#!/usr/bin/env python3
"""s10 conventions pipeline — externalized cross-verse learning (D1-E + D3 + D-tier).

This module holds ALL of s10's new logic so the edits to the s1-inherited
pipeline (`run_gold_standard.py`, `consensus.py`) stay surgical and reviewable.

What it implements (mapped to survey1-obe's code-review gate):
  1. load + PREPEND conventions.md into every leg's prompt   (D1-E, gate #1)
  4. the scribe: per-chapter extract -> dedup -> regression-gate -> version
     + Trigger-1 / R3-all_wrong reroute to the conventions write-path (gate #4)
     `run_convention_regression` reuses s1's `run_prompt_regression` verbatim.
  2. `run_d_deliberation`: the TERMINAL post-C tier (gate #2). It fires ONLY when
     C is exhausted — R3 returns unresolved, OR a Trigger-1 convention-evolution
     attempt regression-FAILS. It is NOT wired to `_stability_level`/Trigger-2,
     and never co-fires with Trigger-2's weak-model patch.

The single feedback artifact is `conventions.md`; the single gate is
`run_convention_regression` (= s1's regression discipline). "Prompt evolution"
becomes "convention accumulation."
"""

import os
import re
import json
from datetime import datetime

from cli_caller import call_llm

S10_DIR = os.path.dirname(os.path.abspath(__file__))
CONVENTIONS_PATH = os.path.join(S10_DIR, "conventions.md")
CONVENTIONS_HISTORY_DIR = os.path.join(S10_DIR, "conventions_history")
CONVENTION_BUDGET = 25  # max active rules — injection-cost + overfit guard

# Marker embedded in every built prompt so the prepend is greppable even when
# conventions.md is empty (seed state) — satisfies gate #1's "grep the built
# prompt, not just the loader".
PREAMBLE_MARKER = "<!-- s10:conventions-preamble -->"


# ── D1-E: load + prepend ──────────────────────────────────────────────────────

def load_conventions():
    """Parse conventions.md → list of {'id','title','body'} active rules.

    A rule is a level-2 heading (``## C<n>  <title>``) followed by its body up to
    the next heading. Returns [] if the file is missing or has no rules (seed).
    """
    if not os.path.isfile(CONVENTIONS_PATH):
        return []
    with open(CONVENTIONS_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    rules = []
    # Split on level-2 headings that look like convention ids (C1, C2, ...).
    pattern = re.compile(r"^##\s+(C\d+)\b[ \t]*(.*)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        rules.append({"id": m.group(1), "title": m.group(2).strip(), "body": body})
    return rules


def conventions_text():
    """Active conventions rendered as a compact rules block ("" if none)."""
    rules = load_conventions()
    if not rules:
        return ""
    lines = []
    for r in rules:
        head = f"- {r['id']} {r['title']}".rstrip()
        lines.append(head)
        if r["body"]:
            for bl in r["body"].splitlines():
                bl = bl.strip()
                if bl and not bl.startswith("<!--"):
                    lines.append(f"    {bl}")
    return "\n".join(lines)


def build_conventions_preamble(target_version="lcc"):
    """The block prepended to every leg's system_prompt (R1/R2/R3).

    Always returns the greppable PREAMBLE_MARKER so the wiring is verifiable even
    in the empty-seed state; when rules exist, their text is included so it lands
    verbatim in the built prompt.
    """
    rules = conventions_text()
    if not rules.strip():
        return (
            "## Settled conventions (s10 conventions.md) — none yet (empty seed)\n"
            f"{PREAMBLE_MARKER}\n\n"
        )
    return (
        "## Settled conventions (s10 conventions.md) — APPLY THESE\n"
        "Regression-gated placement rules distilled from resolved gold verses. "
        "Apply unless the current verse clearly contradicts them:\n\n"
        f"{rules}\n"
        f"{PREAMBLE_MARKER}\n\n"
    )


def _preamble_with_candidate(candidate_rule):
    """Preamble as it WOULD look with one extra candidate rule appended — used by
    the regression gate to test a candidate before it is written."""
    base = conventions_text()
    merged = (base + "\n- CANDIDATE " + candidate_rule.strip()).strip()
    return (
        "## Settled conventions (s10 conventions.md) — APPLY THESE\n\n"
        f"{merged}\n"
        f"{PREAMBLE_MARKER}\n\n"
    )


# ── Versioning ────────────────────────────────────────────────────────────────

def _current_version():
    rules = load_conventions()
    if not os.path.isfile(CONVENTIONS_PATH):
        return "v0.0"
    with open(CONVENTIONS_PATH, "r", encoding="utf-8") as f:
        head = f.read(400)
    m = re.search(r"#\s*conventions\.md\s*—\s*v(\d+)\.(\d+)", head)
    return f"v{m.group(1)}.{m.group(2)}" if m else f"v0.{len(rules)}"


def _next_version():
    cur = _current_version()
    m = re.match(r"v(\d+)\.(\d+)", cur)
    return f"v{m.group(1)}.{int(m.group(2)) + 1}" if m else "v0.1"


def append_convention(candidate_rule, provenance):
    """Append a gate-PASSED candidate as a new ``## C<n>`` rule; bump version;
    snapshot to conventions_history/. ``provenance`` is a short string
    (e.g. "Gen 3:14 Trigger-1")."""
    rules = load_conventions()
    new_id = f"C{len(rules) + 1}"
    new_ver = _next_version()
    title, _, rest = candidate_rule.strip().partition("\n")
    block = (
        f"\n## {new_id}  {title.strip()}"
        f"   [added {new_ver} · gate PASS · {provenance}]\n"
        f"{rest.strip()}\n"
    )
    if not os.path.isfile(CONVENTIONS_PATH):
        header = (
            f"# conventions.md — {new_ver}   (s10 externalized learning)\n\n"
            "Regression-gated, versioned placement rules distilled from resolved "
            "gold. One `## C<n>` per atomic rule.\n"
        )
        with open(CONVENTIONS_PATH, "w", encoding="utf-8") as f:
            f.write(header + block)
    else:
        with open(CONVENTIONS_PATH, "r", encoding="utf-8") as f:
            text = f.read()
        text = re.sub(r"(#\s*conventions\.md\s*—\s*)v\d+\.\d+",
                      rf"\g<1>{new_ver}", text, count=1)
        with open(CONVENTIONS_PATH, "w", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n" + block)
    os.makedirs(CONVENTIONS_HISTORY_DIR, exist_ok=True)
    with open(CONVENTIONS_PATH, "r", encoding="utf-8") as f:
        snap = f.read()
    with open(os.path.join(CONVENTIONS_HISTORY_DIR, f"{new_ver}.md"), "w",
              encoding="utf-8") as f:
        f.write(snap)
    return new_id, new_ver


# ── Convention regression gate (gate #4) — reuse s1's run_prompt_regression ────

def run_convention_regression(candidate_rule, system_prompt, trigger_verse,
                              book_chi, book_eng, models, target_version,
                              sn_field, verbose=False):
    """Gate a candidate convention by REUSING s1's regression machinery.

    The "new prompt" handed to ``run_prompt_regression`` is the system prompt with
    the candidate convention prepended; the gate re-runs sampled prior gold and
    FAILS if any already-settled verse changes. Returns ``(ok, results)``.
    """
    from regression import run_prompt_regression
    trial_prompt = _preamble_with_candidate(candidate_rule) + system_prompt
    return run_prompt_regression(
        new_prompt=trial_prompt,
        new_version=f"conv-trial-{book_eng}-{trigger_verse[0]}-{trigger_verse[1]}",
        trigger_verse=trigger_verse,
        book_chi=book_chi, book_eng=book_eng,
        models=models, target_version=target_version, sn_field=sn_field,
        verbose=verbose,
    )


# ── The scribe: extract candidate conventions (D3 + Trigger-1 reroute) ─────────

_SCRIBE_SYS = (
    "You are the s10 conventions scribe. You distill GENERALIZABLE placement "
    "rules for projecting Strong's-number tags onto Chinese text. You output only "
    "rules that transfer to OTHER verses — never verse-specific facts."
)


def extract_candidate_conventions(context_text, existing_conventions,
                                  models, target_version="lcc", verbose=False):
    """Ask the lead model to propose 0–2 NEW generalizable conventions given some
    resolved-verse context. Returns a list of candidate rule strings (possibly
    empty). Verse-specific 'rules' are explicitly penalized.
    """
    lead = models[0]
    prompt = (
        "Existing settled conventions (do NOT restate these):\n"
        f"{existing_conventions or '(none yet)'}\n\n"
        "Newly resolved gold context:\n"
        f"{context_text}\n\n"
        "Task: state at most TWO NEW, GENERALIZABLE placement conventions this "
        "context teaches that are not already covered. Each must be one atomic "
        "rule that applies to OTHER verses (cite the trigger verse as an example "
        "only). If nothing generalizable, reply exactly: NONE.\n\n"
        "Format: one rule per line, prefixed 'RULE: '. No commentary."
    )
    res = call_llm(
        brand=lead["brand"], model=lead["model"],
        system_prompt=_SCRIBE_SYS, user_prompt=prompt,
        target_version=target_version, verbose=verbose, mode="freeform",
    )
    raw = (res or {}).get("text", "") if isinstance(res, dict) else ""
    candidates = []
    for line in raw.splitlines():
        line = line.strip()
        if line.upper() == "NONE":
            return []
        m = re.match(r"RULE:\s*(.+)", line, re.IGNORECASE)
        if m and len(m.group(1).strip()) > 8:
            candidates.append(m.group(1).strip())
    return candidates[:2]


def _dedup(candidates, existing_conventions):
    """Drop candidates that restate an existing rule (cheap token-overlap)."""
    existing = existing_conventions.lower()
    fresh = []
    for c in candidates:
        words = [w for w in re.findall(r"\w+", c.lower()) if len(w) > 3]
        if not words:
            continue
        overlap = sum(1 for w in set(words) if w in existing)
        if overlap / max(len(set(words)), 1) < 0.6:
            fresh.append(c)
    return fresh


def try_evolve_convention(candidate_rule, system_prompt, trigger_verse,
                          book_chi, book_eng, models, target_version, sn_field,
                          provenance, verbose=False):
    """Run one candidate through the gate; on PASS append it. Returns
    ``(accepted: bool, results)``. A FAIL is the signal that the verse is not a
    convention problem → the caller escalates to D-deliberation."""
    if len(load_conventions()) >= CONVENTION_BUDGET:
        print(f"  [scribe] convention budget ({CONVENTION_BUDGET}) reached — "
              f"skipping candidate (consider merging rules)", flush=True)
        return False, {"budget_full": True}
    ok, results = run_convention_regression(
        candidate_rule, system_prompt, trigger_verse,
        book_chi, book_eng, models, target_version, sn_field, verbose=verbose)
    if ok:
        cid, ver = append_convention(candidate_rule, provenance)
        print(f"  [scribe] convention {cid} ACCEPTED ({ver}) ← {provenance}",
              flush=True)
        return True, results
    print(f"  [scribe] candidate REGRESSION-FAILED ← {provenance} "
          f"(verse is not a convention problem → D-deliberation)", flush=True)
    return False, results


def handle_collective_error(verse_key, reason, error_descriptions,
                            convergence_context, system_prompt, book_chi,
                            book_eng, models, target_version, sn_field,
                            round1_results, verse_data, naked=False,
                            verbose=False):
    """Trigger-1 / R3-all_wrong reroute (gate #4 + #2) — replaces s1's prompt +0.1.

    A collective error means the *prompt/convention* may be wrong. So:
      1. Distill a candidate convention from the error + convergence context.
      2. Gate it via run_convention_regression (= s1's regression discipline).
         PASS → append to conventions.md (no prompt bump); return
         ("convention_added", None) — the trigger verse stays a hard verse but the
         convention now helps future verses; the run CONTINUES.
      3. If NO candidate passes the gate, the verse is not a convention problem →
         it is genuinely ambiguous → D-deliberation (the terminal tier). Return
         ("deliberation", gold_entry_or_None).
    """
    existing = conventions_text()
    ctx = ("Collective error: " + "; ".join(d for d in error_descriptions[:3] if d)
           + "\n" + (convergence_context or ""))
    candidates = _dedup(
        extract_candidate_conventions(ctx, existing, models, target_version, verbose),
        existing)
    for cand in candidates:
        accepted, _ = try_evolve_convention(
            cand, system_prompt, verse_key, book_chi, book_eng, models,
            target_version, sn_field,
            provenance=f"{book_eng} {verse_key[0]}:{verse_key[1]} {reason}",
            verbose=verbose)
        if accepted:
            return ("convention_added", None)
    # No convention fixed it → genuine ambiguity → terminal D-deliberation.
    gold_entry = run_d_deliberation(
        verse_key, round1_results, verse_data, models, target_version, sn_field,
        reason=f"{reason}: convention-evolution regression-fail/none",
        naked=naked, verbose=verbose, book_chi=book_chi,
        gate_ctx={"system_prompt": system_prompt, "book_eng": book_eng})
    return ("deliberation", gold_entry)


def run_scribe_for_chapter(chap, book_chi, book_eng, gold_standard, models,
                           target_version, sn_field, verbose=False):
    """Per-chapter (D3-batched): distill this chapter's resolved gold into new
    conventions, dedup, gate each, version the survivors. Returns the list of
    accepted convention ids."""
    chapter_gold = [g for (c, s), g in sorted(gold_standard.items())
                    if c == chap and g.get("resolved_at") in
                    ("round1", "round2", "round3", "r2_model_patch",
                     "d_deliberation")]
    if not chapter_gold:
        return []
    ctx = []
    for g in chapter_gold[:40]:
        ctx.append(f"{g['chap']}:{g['sec']} [{g['resolved_at']}]  "
                   f"UNV={g['unv_sn_reference'][:120]}  →  GOLD={g['lcc_sn'][:120]}")
    existing = conventions_text()
    candidates = _dedup(
        extract_candidate_conventions("\n".join(ctx), existing, models,
                                      target_version, verbose),
        existing)
    accepted = []
    for cand in candidates:
        ok, _ = try_evolve_convention(
            cand, _scribe_system_prompt_for_gate(), (chap, chapter_gold[0]['sec']),
            book_chi, book_eng, models, target_version, sn_field,
            provenance=f"{book_eng} ch{chap} scribe", verbose=verbose)
        if ok:
            accepted.append(cand)
    return accepted


def _scribe_system_prompt_for_gate():
    """Best-effort system prompt for the gate's re-run; the actual run threads the
    real prompt, but the chapter scribe may not have it — use the latest prompt."""
    try:
        from run_gold_standard import detect_latest_prompt, load_prompt_file
        path, _ = detect_latest_prompt()
        if path:
            return load_prompt_file(path)
    except Exception:
        pass
    return ""


# ── D-deliberation: the TERMINAL post-C tier (gate #2) ────────────────────────
# Fires ONLY when C is exhausted: R3 unresolved OR Trigger-1 convention-evolution
# regression-FAILS. NEVER pinned to _stability_level / Trigger-2.

_D_DELIB_SYS = (
    "You are one of three independent experts re-examining a verse whose Strong's "
    "tag placement could NOT be resolved by independent voting, and which could "
    "NOT be fixed by evolving a shared convention — so the verse itself is "
    "genuinely ambiguous. Now you MAY see the others' independent first answers."
)


def _wlc_evidence_block(book_chi, chap, sec, fhl_sn):
    """D5: independent WLC (Clear Bible Hebrew alignment) identity evidence for the
    verse — NOT an override. Returns a short evidence string ("" if unavailable or
    book_chi unknown). Real WLC/FHL tensions are surfaced (routed to FHL_DIVERGENCE_LOG
    by wlc_check itself), never used to override the FHL-faithful default."""
    if not book_chi:
        return ""
    try:
        from wlc_check import wlc_check
        r = wlc_check(book_chi, chap, sec, fhl_sn)
    except Exception:
        return ""
    status = r.get("status")
    if status == "no_signal":
        return ""
    if status == "match":
        return ("WLC identity evidence: the Hebrew lemma/SN inventory MATCHES the FHL "
                f"reference (coverage {r.get('coverage', 0):.2f}). No identity tension — "
                "decide placement on the Chinese text alone.")
    divs = r.get("divergences", [])[:3]
    lines = [f"    · {d.get('side')} {d.get('bare_num')} ({d.get('kind')}): "
             f"WLC={d.get('wlc_lemma')}/{d.get('wlc_strong')} vs FHL token "
             f"{d.get('source_token')}" for d in divs]
    return ("WLC identity evidence (independent, NOT an override — keep the FHL "
            "reference authoritative; this only flags where the Hebrew source and FHL "
            "differ on lemma identity):\n" + "\n".join(lines))


def run_d_deliberation(verse_key, round1_results, verse_data, models,
                       target_version, sn_field, reason, naked=False,
                       verbose=False, book_chi=None, gate_ctx=None):
    """Reveal the sealed R1 bids and ask each leg to hold or revise, then tally.

    Returns a ``gold_entry`` dict (resolved_at='d_deliberation', trust_tier=
    'd_deliberation') when ≥2 legs converge, else ``None`` (→ human / unresolved).
    The sealed R1 bids are reused verbatim — no new independent round is run, so
    independence was already spent untainted before this tier.

    D5: ``book_chi`` enables WLC identity evidence in each leg's prompt.
    D4: ``gate_ctx`` (dict with ``system_prompt``, ``book_eng``) enables the
        D-deliberation → convention closed loop — on resolution, a reusable rule is
        distilled from the D outcome and pushed through the SAME scribe gate.
    """
    chap, sec = verse_key
    vdata = verse_data.get(verse_key, {})
    unv_ref = vdata.get("unv_sn", "")
    fhl_sn_for_wlc = unv_ref
    if naked:
        try:
            from shared.sn_shell import strip_shell
            unv_ref = strip_shell(unv_ref, markers=False)
        except Exception:
            pass

    wlc_evidence = _wlc_evidence_block(book_chi, chap, sec, fhl_sn_for_wlc)  # D5

    bids = {}
    for mi in models:
        name = mi["name"]
        bids[name] = round1_results.get(name, {}).get(verse_key, {}).get(sn_field, "")

    bid_block = "\n".join(f"  [{n}] {t}" for n, t in bids.items())
    print(f"\n  ── D-DELIBERATION [{reason}] {chap}:{sec} ──", flush=True)
    if wlc_evidence and verbose:
        print(f"    [D5 WLC] {wlc_evidence.splitlines()[0]}", flush=True)

    revised = {}
    for mi in models:
        name, brand, model_id = mi["name"], mi["brand"], mi["model"]
        prompt = (
            f"Verse {chap}:{sec}.\n"
            f"UNV+SN reference:\n{unv_ref}\n\n"
            f"Target ({target_version}) original:\n{vdata.get('lcc_original','')}\n\n"
            f"The three INDEPENDENT first answers (sealed bids) were:\n{bid_block}\n\n"
            + (f"{wlc_evidence}\n\n" if wlc_evidence else "")
            + "This verse is genuinely ambiguous (voting failed; no convention fixes "
            "it). Considering the three answers, give your FINAL placement and the "
            "single rule that decides it. Output ONLY the final annotated target "
            "text (same tag format as the bids)."
        )
        res = call_llm(brand=brand, model=model_id, system_prompt=_D_DELIB_SYS,
                       user_prompt=prompt, target_version=target_version,
                       verbose=verbose, mode="production")
        revised[name] = (res or {}).get(sn_field, "") if isinstance(res, dict) else ""
        print(f"    [{name}] revised → {revised[name][:80]}", flush=True)

    # Tally: ≥2 matching revised answers → resolved.
    from comparator import texts_match
    names = list(revised.keys())
    winner_text = None
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = revised[names[i]], revised[names[j]]
            if a and b and texts_match(a, b):
                winner_text = a
                break
        if winner_text:
            break

    if not winner_text:
        print(f"  → D-DELIBERATION DEADLOCK {chap}:{sec} → human", flush=True)
        return None

    print(f"  → D-DELIBERATION RESOLVED {chap}:{sec}", flush=True)

    # D4: D-deliberation → convention closed loop. Only a REUSABLE rule earns a
    # candidate; it must pass the SAME scribe gate; the D case is its provenance.
    if gate_ctx:
        try:
            _d_to_convention(verse_key, winner_text, unv_ref, reason, models,
                             target_version, sn_field, book_chi, gate_ctx, naked,
                             verbose)
        except Exception as e:
            print(f"  [D4] convention extraction skipped ({e})", flush=True)

    return {
        "book": vdata.get("book", ""), "chap": chap, "sec": sec,
        "lcc_sn": winner_text,
        "lcc_original": vdata.get("lcc_original", ""),
        "unv_sn_reference": vdata.get("unv_sn", ""),
        "resolved_at": "d_deliberation",
        "trust_tier": "d_deliberation",
        "d_reason": reason,
        "wlc_evidence": wlc_evidence or None,
        "round1": {n: {"lcc_sn": bids.get(n, ""), "opinion": "sealed_bid"}
                   for n in bids},
        "d_deliberation": {n: revised.get(n, "") for n in revised},
        "round2": None, "round3": None,
    }


def _d_to_convention(verse_key, winner_text, unv_ref, reason, models,
                     target_version, sn_field, book_chi, gate_ctx, naked, verbose):
    """D4 closed loop: distill a reusable convention from a resolved D outcome and
    push it through the standard scribe gate. No-op unless a generalizable rule is
    found; verse-specific facts are penalized by the scribe prompt."""
    ctx = (f"A previously-ambiguous verse {verse_key[0]}:{verse_key[1]} was resolved "
           f"by D-deliberation ({reason}).\n"
           f"UNV+SN reference: {unv_ref[:160]}\n"
           f"Resolved placement (GOLD): {winner_text[:160]}\n"
           "What GENERALIZABLE placement rule does this resolution expose?")
    existing = conventions_text()
    candidates = _dedup(
        extract_candidate_conventions(ctx, existing, models, target_version, verbose),
        existing)
    book_eng = gate_ctx.get("book_eng", "")
    system_prompt = gate_ctx.get("system_prompt", "")
    for cand in candidates:
        accepted, _ = try_evolve_convention(
            cand, system_prompt, verse_key, book_chi or "", book_eng, models,
            target_version, sn_field,
            provenance=f"{book_eng} {verse_key[0]}:{verse_key[1]} D4-deliberation",
            verbose=verbose)
        if accepted:
            print(f"  [D4] convention distilled from D-deliberation "
                  f"{verse_key[0]}:{verse_key[1]}", flush=True)
            return True
    return False
