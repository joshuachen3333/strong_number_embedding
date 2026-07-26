#!/usr/bin/env python3
"""Build gold standard from round results. Track all opinions per round."""

import json
import os
import re
import sys

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
REPO_ROOT = os.path.dirname(PARENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from judge import tally_r2_debate, tally_r3_judgments, tally_r3_buckets
from shared.sn_shell import restore_shells_positional, strip_shell

FHL_DIVERGENCE_LOG = os.path.join(SURVEY_DIR, "FHL_DIVERGENCE_LOG.md")

# Matches existing D-entry headers (mirrors wlc_check.load_divergences' regex) so an
# auto-appended entry is picked up by the Phase-A ledger on the next run.
_D_HEADER_RE = re.compile(
    r"^##\s*D(\d+)\s*—\s*Gen\s*(\d+):(\d+).*?H0*(\d+)\s*\(FHL\)", re.I)
# Permissive D-id scan: matches ANY `## D<n>` header regardless of body shape, so the
# id counter never under-counts a human-added / free-form entry (which would otherwise
# cause a DUPLICATE D-id on the next auto-append). Strict _D_HEADER_RE is used only for
# the (chap, sec, H<fhl>) idempotency key.
_D_ID_RE = re.compile(r"^##\s*D(\d+)\b")


def _eng_to_chi_book(book_eng):
    """Reverse lookup English book name -> Chinese abbrev (for log readability)."""
    try:
        from llm_direct_sn_unv2notyet import CHI_TO_ENG
        for chi, eng in CHI_TO_ENG.items():
            if eng == book_eng:
                return chi
    except Exception:  # noqa: BLE001 — log readability only, never block
        pass
    return book_eng


def append_divergence_entry(book_eng, chap, sec, fhl_num, wlc_num=None,
                            reason="", source_token=None, wlc_lemma=None,
                            path=None):
    """Idempotently append a methodology-divergence D-entry to FHL_DIVERGENCE_LOG.md.

    R-1 Q1 (locked): a >=2/3 methodology_divergence ruling auto-appends a D-entry
    IMMEDIATELY (suppresses re-escalation; human reviews after the fact).

    Idempotent: skips if any existing D-entry already covers the same
    (chap, sec, H<fhl_num>). Auto-increments the D-id from the highest present.
    Matches the existing D-entry markdown format so wlc_check.load_divergences picks
    it up. Returns the D-id written, or None if skipped (already present).

    fhl_num/wlc_num may be like "H0120"/"H120"/"120"; normalized for comparison and
    rendered zero-padded to 4 digits to match the D1 style.
    """
    if path is None:
        path = FHL_DIVERGENCE_LOG

    # Gen-only invariant (Blocker 3): the header is rendered as "Gen C:V" and the
    # idempotency key is book-less (chap, sec, H<fhl>); wlc_check.load_divergences is
    # likewise Gen-anchored. Writing a non-Gen entry would mislabel the header, break
    # upstream re-escalation suppression, and collide the book-less key across books.
    # Until the loader is generalized to capture book, refuse non-Gen rather than
    # silently mislabel. (Current scope — survey1 Gen 1-2, Q4 Gen 1:22-31 — is Gen.)
    _bk = (book_eng or "").strip()
    if _bk.lower() not in ("gen", "genesis") and _bk not in ("創", "创"):
        print(f"  [WLC] D-entry auto-append is Gen-only (loader is Gen-anchored); "
              f"refusing book={book_eng!r} at {chap}:{sec}. Widen wlc_check first.")
        return None

    def _norm(n):
        if n is None:
            return None
        m = re.search(r"(\d+)", str(n))
        return int(m.group(1)) if m else None

    fhl_n = _norm(fhl_num)
    if fhl_n is None:
        return None
    wlc_n = _norm(wlc_num)

    # Scan existing entries: collect ids + idempotency keys.
    max_id = 0
    existing_keys = set()
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for ln in f:
                s = ln.strip()
                mid = _D_ID_RE.match(s)
                if mid:  # permissive: count EVERY D<n> header toward max_id
                    max_id = max(max_id, int(mid.group(1)))
                m = _D_HEADER_RE.match(s)
                if m:    # strict: only full FHL-format headers seed the idempotency key
                    existing_keys.add((int(m.group(2)), int(m.group(3)),
                                       int(m.group(4))))
    if (chap, sec, fhl_n) in existing_keys:
        return None  # already logged — idempotent skip

    new_id = max_id + 1
    fhl_tag = f"H{fhl_n:04d}"
    wlc_tag = f"H{wlc_n:04d}" if wlc_n is not None else "(WLC original-language)"
    book_chi = _eng_to_chi_book(book_eng)

    ev_lines = []
    if source_token:
        ev_lines.append(f"  - WLC source token: `{source_token}`")
    if wlc_lemma:
        ev_lines.append(f"  - WLC lemma: {wlc_lemma}")
    ev_block = ("\n" + "\n".join(ev_lines)) if ev_lines else ""

    entry = (
        f"\n## D{new_id} — Gen {chap}:{sec} — {fhl_tag} (FHL) vs {wlc_tag} (WLC)\n\n"
        f"- **Verse / clause**: {book_chi} {chap}:{sec} — auto-logged methodology "
        f"divergence (Phase B R3 ruling).\n"
        f"- **FHL / current gold**: **{fhl_tag}** (kept — FHL-faithful).\n"
        f"- **WLC original-language alignment**: **{wlc_tag}**.{ev_block}\n"
        f"- **R3 bucket ruling**: methodology_divergence (>=2/3 judges). Reason: "
        f"{reason or '(see R3 round results)'}\n"
        f"- **DECISION (auto, Phase B): KEEP {fhl_tag} — FHL-faithful.** Gold "
        f"unchanged; logged so it never re-escalates. **Pending human review.**\n"
        f"- **Status**: known-divergence · gold unchanged ({fhl_tag}) · "
        f"auto-logged · **FHL-feedback candidate**.\n"
        f"- **Found by**: Phase B R3 WLC-evidence bucket vote (auto-append).\n"
    )

    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)
    return new_id


def _restore_gold_shells(gold_standard):
    """--naked post-pass: restore original FHL shells onto naked winning text.

    For each gold entry, treat the current ``lcc_sn`` as bare-number (naked)
    text, build a zero-loss lookup from ``unv_sn_reference`` (the shelled
    source), and restore the original tags. The naked text is preserved in
    ``lcc_sn_naked``. Numbers absent from the source stay bare on purpose
    (red flag). This is deterministic format post-processing only — it never
    reads or writes ``resolved_at`` or any other resolution field.

    Returns a list of (verse_key, bare_num) §2.1 same-number-different-shell
    nodes for the human-review list.
    """
    flagged = []
    for verse_key, gold in gold_standard.items():
        naked = gold.get("lcc_sn", "")
        if not naked:
            continue  # e.g. trigger1 verses with no valid output
        ref = gold.get("unv_sn_reference", "")

        # §2.1 detection: same bare number carrying >1 distinct shell in source.
        by_num = {}
        for m in re.finditer(r'\{?<W[ATG]*[HG]\d+[a-z]?>\}?', ref):
            raw = m.group(0)
            num = strip_shell(raw, markers=False).strip("<>")
            by_num.setdefault(num, set()).add(raw)
        for num, shells in by_num.items():
            if len(shells) > 1:
                flagged.append((verse_key, num))

        gold["lcc_sn_naked"] = naked
        gold["lcc_sn"] = restore_shells_positional(naked, ref)
    return flagged


def resolve_winner_text(winner_label, verse_key, convergence_results,
                        corrected_texts):
    """Get the actual SN text for the winning label.

    Uses stable outputs from convergence (not R1 originals).
    """
    models = list(convergence_results.keys())
    label_to_model = {"A": models[0], "B": models[1], "C": models[2]}

    if winner_label == "corrected" and corrected_texts:
        return corrected_texts[0]
    elif winner_label in label_to_model:
        model = label_to_model[winner_label]
        conv = convergence_results[model].get(verse_key, {})
        return conv.get("stable_result", "")
    return ""


def _annotate_wlc(gold_standard, verse_data, wlc_bucket_overrides=None):
    """WLC Phase-A annotation: attach the original-language identity signal +
    trust_tier to each gold entry. DECOUPLED from resolution (AD-1): reads the wlc
    result collected in verse_data, NEVER reads or writes ``resolved_at``. Makes
    WLC's contribution visible/auditable.

    Phase B: ``wlc_bucket_overrides`` (built in build_gold_standard from the R3 bucket
    vote) may pin trust_tier for verses where the bucket vote fired:
      - collective_error (UNANIMOUS) -> "wlc_corrected"
      - methodology_divergence (>=2/3) -> "c_consensus_over_wlc_divergence" (logged)
    GUARDED: when empty (no WLC-contested R3 verse), behavior is byte-for-byte Phase A.

    trust_tier:
      c_consensus+wlc_corroborated    — consensus AND WLC agree (highest)
      c_consensus_over_wlc_divergence — consensus held on a WLC-contested verse
      c_consensus                     — consensus; WLC silent / no signal
      wlc_corrected                   — gold corrected toward WLC (R3 collective_error)
      None                            — non-C-tier (prompt_evolution / unresolved …)
    """
    _C_TIER = {"round1", "round2", "round3", "r2_model_patch"}
    wlc_bucket_overrides = wlc_bucket_overrides or {}
    for verse_key, gold in gold_standard.items():
        wlc = (verse_data.get(verse_key) or {}).get("wlc")
        status = wlc.get("status") if wlc else None
        gold["wlc_status"] = status            # match | divergence | no_signal | None
        if wlc:
            gold["wlc_divergences"] = wlc.get("divergences", [])

        override = wlc_bucket_overrides.get(verse_key)
        if override and gold.get("resolved_at") in _C_TIER:
            # Phase B R3 bucket ruling pins the tier and records the bucket verdict.
            # Defense-in-depth (AD-1): honor the override ONLY for C-tier entries, so a
            # non-C-tier verse can never receive trust_tier='wlc_corrected' even if an
            # override leaked into the map.
            gold["trust_tier"] = override["tier"]
            gold["wlc_bucket"] = override["bucket"]
            if override.get("reason"):
                gold["wlc_bucket_reason"] = override["reason"]
        elif gold.get("resolved_at") not in _C_TIER:
            gold["trust_tier"] = None
        elif status == "match":
            gold["trust_tier"] = "c_consensus+wlc_corroborated"
        elif status == "divergence":
            gold["trust_tier"] = "c_consensus_over_wlc_divergence"
        else:
            gold["trust_tier"] = "c_consensus"


def build_gold_standard(unanimous, disagreed, round1_results,
                        convergence_results, round2_judgments,
                        round3_judgments, verse_data,
                        prompt_version="v1.0", sn_field="lcc_sn",
                        trigger1_verses=None, trigger2_verses=None,
                        naked=False):
    """Build gold standard JSONs from all round results.

    Args:
        unanimous: list of (chap, sec) — passed Round 1 unanimously
        disagreed: list of (chap, sec) — went to Round 2+
        round1_results: {model_name: {(chap,sec): result_dict}}
        convergence_results: {model_name: {(chap,sec): convergence_dict}}
        round2_judgments: {(chap,sec): {judge_key: judgment_dict}}
        round3_judgments: {(chap,sec): {judge_key: judgment_dict}} or None
        verse_data: {(chap,sec): {"unv_sn", "lcc_original", "book"}}
        prompt_version: version string for tracking
        trigger1_verses: list of (verse_key, vdata, conv_data) — R2 all unstable
        trigger2_verses: list of (verse_key, gold_entry) — R2 model patch

    Returns:
        (gold_standard, unresolved, prompt_evolutions)
        gold_standard: {(chap,sec): gold_dict}
        unresolved: list of (chap, sec)
        prompt_evolutions: list of {verse_key, error_descriptions, improvements}
    """
    models = list(round1_results.keys())
    gold_standard = {}
    unresolved = []
    prompt_evolutions = []
    # Phase B (R3-only): per-verse WLC bucket overrides for _annotate_wlc.
    # {verse_key: {"tier": "wlc_corrected" | "c_consensus_over_wlc_divergence",
    #              "bucket": str, "reason": str}}. Empty unless a WLC-contested verse
    # reached R3 and a bucket majority fired — guarded no-op otherwise.
    wlc_bucket_overrides = {}

    # Process unanimous verses
    for verse_key in unanimous:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})

        first_model = models[0]
        result = round1_results[first_model].get(verse_key, {})

        round1_opinions = {}
        for model_name in models:
            r = round1_results[model_name].get(verse_key, {})
            round1_opinions[model_name] = {
                "lcc_sn": r.get(sn_field, ""),
                "confidence": r.get("confidence", 0),
                "opinion": "unanimous",
                # Which model generation actually answered — the panel follows each
                # brand's latest, so this is not derivable from the slot name.
                "model_version": r.get("_resolved_model", ""),
            }

        gold_standard[verse_key] = {
            "book": vdata.get("book", ""),
            "chap": chap,
            "sec": sec,
            "lcc_sn": result.get(sn_field, ""),
            "lcc_original": vdata.get("lcc_original", ""),
            "unv_sn_reference": vdata.get("unv_sn", ""),
            "resolved_at": "round1",
            "prompt_version": prompt_version,
            "round1": round1_opinions,
            "round2": None,
            "round3": None,
        }

    # Process disagreed verses
    for verse_key in disagreed:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})

        # Build Round 1 opinions
        round1_opinions = {}
        for model_name in models:
            r = round1_results[model_name].get(verse_key, {})
            round1_opinions[model_name] = {
                "lcc_sn": r.get(sn_field, ""),
                "confidence": r.get("confidence", 0),
                "opinion": "disagree",
                "model_version": r.get("_resolved_model", ""),
            }

        # Build convergence info
        convergence_info = {}
        for model_name in models:
            conv = convergence_results.get(model_name, {}).get(verse_key, {})
            convergence_info[model_name] = {
                "stable_result": conv.get("stable_result", ""),
                "converged": conv.get("converged", False),
                "stable_at": conv.get("stable_at", "?"),
                "attempt_count": len(conv.get("attempts", [])),
                # >1 entry = the CLI upgraded mid-convergence (see judge.py)
                "model_versions": conv.get("model_versions", []),
            }

        # Try Round 2 debate
        r2 = round2_judgments.get(verse_key, {})
        resolved_at = None
        winning_text = ""
        round2_with_opinions = None
        round3_with_opinions = None

        if r2:
            winner_label, opinion_map = tally_r2_debate(
                r2, convergence_results, sn_field)

            corrected_texts = [
                j.get("corrected") for j in r2.values()
                if j.get("corrected")
            ]

            round2_with_opinions = {}
            for judge_key, judgment in r2.items():
                round2_with_opinions[judge_key] = {
                    **judgment,
                    "opinion": opinion_map.get(judge_key, "?"),
                }

            if winner_label is not None:
                resolved_at = "round2"
                winning_text = resolve_winner_text(
                    winner_label, verse_key, convergence_results,
                    corrected_texts)

                # Update R1 opinions
                label_to_model = {"A": models[0], "B": models[1], "C": models[2]}
                winner_model = label_to_model.get(winner_label)
                for model_name in models:
                    if winner_label == "corrected":
                        round1_opinions[model_name]["opinion"] = "superseded"
                    elif model_name == winner_model:
                        round1_opinions[model_name]["opinion"] = "majority"
                    else:
                        round1_opinions[model_name]["opinion"] = "minority"

        # Try Round 3 if needed
        if resolved_at is None and round3_judgments:
            r3 = round3_judgments.get(verse_key, {})
            if r3:
                outcome, details = tally_r3_judgments(r3, convergence_results)

                round3_with_opinions = {}
                for judge_key, judgment in r3.items():
                    round3_with_opinions[judge_key] = {**judgment}

                if outcome == "resolved":
                    winner_label, opinion_map = details
                    resolved_at = "round3"

                    corrected_texts = [
                        j.get("corrected") for j in r3.values()
                        if j.get("corrected")
                    ]
                    winning_text = resolve_winner_text(
                        winner_label, verse_key, convergence_results,
                        corrected_texts)

                    # Update opinions
                    for judge_key in round3_with_opinions:
                        round3_with_opinions[judge_key]["opinion"] = opinion_map.get(judge_key, "?")

                    label_to_model = {"A": models[0], "B": models[1], "C": models[2]}
                    winner_model = label_to_model.get(winner_label)
                    for model_name in models:
                        if winner_label == "corrected":
                            round1_opinions[model_name]["opinion"] = "superseded"
                        elif model_name == winner_model:
                            round1_opinions[model_name]["opinion"] = "majority"
                        else:
                            round1_opinions[model_name]["opinion"] = "minority"

                elif outcome == "prompt_evolution":
                    resolved_at = "prompt_evolution"
                    prompt_evolutions.append({
                        "verse_key": verse_key,
                        "error_descriptions": details["error_descriptions"],
                        "improvements": details["improvements"],
                        "aligned": details["aligned"],
                    })
                    # Use first model's stable output as placeholder
                    winning_text = convergence_results[models[0]].get(
                        verse_key, {}).get("stable_result", "")

                    for judge_key in round3_with_opinions:
                        round3_with_opinions[judge_key]["opinion"] = "all_wrong"

                else:  # unresolved
                    for judge_key in round3_with_opinions:
                        round3_with_opinions[judge_key]["opinion"] = details.get(judge_key, "minority")

                # ── Phase B (R3-only): WLC bucket resolution ──
                # GUARDED: only fires when this verse REACHED A C-TIER RESOLUTION
                # (outcome == "resolved" → resolved_at == "round3") AND is WLC-contested
                # AND R3 judges supplied bucket verdicts. The C-tier gate is load-bearing
                # for AD-1: without it the block runs for prompt_evolution/unresolved
                # outcomes too, leaking WLC-corrected text into the gold of a verse the
                # panel could NOT resolve and pinning trust_tier on a non-C-tier entry.
                _wlc = (verse_data.get(verse_key) or {}).get("wlc")
                if (outcome == "resolved"
                        and _wlc and _wlc.get("status") == "divergence"):
                    bucket, b_details = tally_r3_buckets(r3)
                    if bucket == "collective_error":
                        # Q3 UNANIMOUS already enforced in tally_r3_buckets.
                        # Gold corrected toward WLC: prefer a judge's corrected text
                        # if any judge supplied one, else keep consensus text (the
                        # identity fix is recorded in the tier + log; text correction
                        # requires an explicit corrected output).
                        _corr = next((j.get("corrected") for j in r3.values()
                                      if j.get("corrected")), None)
                        if _corr:
                            winning_text = _corr
                        wlc_bucket_overrides[verse_key] = {
                            "tier": "wlc_corrected",
                            "bucket": bucket,
                            "reason": "; ".join(
                                b_details.get("reasons", {}).get(
                                    "collective_error", [])),
                        }
                    elif bucket == "methodology_divergence":
                        # Keep FHL consensus; auto-append idempotent D-entry (Q1).
                        reason = "; ".join(
                            b_details.get("reasons", {}).get(
                                "methodology_divergence", []))
                        for d in _wlc.get("divergences", []):
                            if (d.get("side") == "fhl_only"
                                    and d.get("kind") == "unresolved"):
                                try:
                                    append_divergence_entry(
                                        book_eng=vdata.get("book", ""),
                                        chap=chap, sec=sec,
                                        fhl_num=d.get("bare_num"),
                                        wlc_num=d.get("wlc_strong"),
                                        reason=reason,
                                        source_token=d.get("source_token"),
                                        wlc_lemma=d.get("wlc_lemma"),
                                    )
                                except Exception as _le:  # noqa: BLE001
                                    print(f"  [WLC] D-entry append failed for "
                                          f"{chap}:{sec} {d.get('bare_num')}: {_le}")
                        wlc_bucket_overrides[verse_key] = {
                            "tier": "c_consensus_over_wlc_divergence",
                            "bucket": bucket,
                            "reason": reason,
                        }
                    # placement_or_silent / no majority -> no override (normal
                    # consensus; WLC abstains — existing behavior).

        if resolved_at is None:
            resolved_at = "unresolved"
            unresolved.append(verse_key)
            winning_text = convergence_results.get(models[0], {}).get(
                verse_key, {}).get("stable_result",
                round1_results[models[0]].get(verse_key, {}).get(sn_field, ""))

        gold_standard[verse_key] = {
            "book": vdata.get("book", ""),
            "chap": chap,
            "sec": sec,
            "lcc_sn": winning_text,
            "lcc_original": vdata.get("lcc_original", ""),
            "unv_sn_reference": vdata.get("unv_sn", ""),
            "resolved_at": resolved_at,
            "prompt_version": prompt_version,
            "round1": round1_opinions,
            "round2": round2_with_opinions,
            "round2_convergence": convergence_info,
            "round3": round3_with_opinions,
        }

    # Process Trigger 1 verses (all 3 unstable → early prompt evolution)
    if trigger1_verses:
        for verse_key, vdata, conv_data in trigger1_verses:
            chap, sec = verse_key
            models_in_conv = list(conv_data.keys())
            gold_standard[verse_key] = {
                "book": vdata.get("book", ""),
                "chap": chap,
                "sec": sec,
                "lcc_sn": "",  # no valid output
                "lcc_original": vdata.get("lcc_original", ""),
                "unv_sn_reference": vdata.get("unv_sn", ""),
                "resolved_at": "r2_early_evolution",
                "prompt_version": prompt_version,
                "round1": {m: {
                    "lcc_sn": round1_results.get(m, {}).get(verse_key, {}).get(sn_field, ""),
                    "confidence": round1_results.get(m, {}).get(verse_key, {}).get("confidence", 0),
                    "opinion": "unstable",
                } for m in models_in_conv},
                "round2_convergence": {m: {
                    "stable_result": conv_data.get(m, {}).get("stable_result", ""),
                    "converged": conv_data.get(m, {}).get("converged", False),
                    "stable_at": conv_data.get(m, {}).get("stable_at", "?"),
                    "attempt_count": len(conv_data.get(m, {}).get("attempts", [])),
                } for m in models_in_conv},
                "round2": None,
                "round3": None,
            }
            prompt_evolutions.append({
                "verse_key": verse_key,
                "error_descriptions": ["All 3 models unstable in R2 convergence"],
                "improvements": ["Prompt may be ambiguous — review verse structure"],
                "aligned": True,
                "trigger": "r2_all_unstable",
            })

    # Process Trigger 2 verses (2 easy + agree, 1 unstable → model patch)
    if trigger2_verses:
        for verse_key, gold_entry in trigger2_verses:
            gold_standard[verse_key] = gold_entry

    # --naked post-pass (存檔還殼): restore FHL shells onto naked winning text.
    # Deterministic format step, decoupled from all resolved_at logic above.
    if naked:
        flagged = _restore_gold_shells(gold_standard)
        if flagged:
            nodes = ", ".join(f"{c}:{s}#{num}" for (c, s), num in flagged)
            print(f"\n  §2.1 same-number-different-shell positionally restored "
                  f"({len(flagged)} nodes; occurrence order assumed = source — "
                  f"spot-check if uncertain): {nodes}")

    # WLC Phase-A annotation: trust_tier + wlc_status/divergences on every entry.
    # Decoupled from resolution (AD-1) — reads verse_data['wlc'], never resolved_at.
    # Phase B: pass R3 bucket overrides (guarded — empty unless a WLC-contested verse
    # reached R3 and a bucket majority fired).
    _annotate_wlc(gold_standard, verse_data, wlc_bucket_overrides)

    return gold_standard, unresolved, prompt_evolutions


def save_gold_standard(gold_standard, output_dir=None):
    """Save gold standard JSONs to disk."""
    if output_dir is None:
        output_dir = os.path.join(SURVEY_DIR, "gold_standard")

    for verse_key, gold in gold_standard.items():
        chap, sec = verse_key
        book = gold.get("book", "")
        book_dir = os.path.join(output_dir, book, str(chap))
        os.makedirs(book_dir, exist_ok=True)
        filepath = os.path.join(book_dir, f"{sec}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(gold, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved {len(gold_standard)} gold standard verses to {output_dir}")


def print_summary(gold_standard, unresolved, prompt_evolutions=None):
    """Print a summary of the gold standard."""
    total = len(gold_standard)
    r1 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round1")
    r2 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round2")
    r2_patch = sum(1 for g in gold_standard.values() if g["resolved_at"] == "r2_model_patch")
    r2_evo = sum(1 for g in gold_standard.values() if g["resolved_at"] == "r2_early_evolution")
    r3 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round3")
    pe = sum(1 for g in gold_standard.values() if g["resolved_at"] == "prompt_evolution")
    ur = len(unresolved)

    print(f"\n{'='*60}")
    print(f"  Gold Standard Summary")
    print(f"{'='*60}")
    print(f"  Total verses:          {total}")
    print(f"  Round 1 (unanimous):   {r1}")
    print(f"  Round 2 (2/3 debate):  {r2}")
    print(f"  R2 Trigger 2 (patch):  {r2_patch}")
    print(f"  R2 Trigger 1 (+0.1):   {r2_evo}")
    print(f"  Round 3 (2/3 final):   {r3}")
    print(f"  R3 prompt evolution:   {pe}")
    print(f"  Unresolved:            {ur}")
    if unresolved:
        print(f"  Unresolved verses: {', '.join(f'{c}:{s}' for c, s in unresolved)}")

    if prompt_evolutions:
        print(f"\n  {'─'*50}")
        print(f"  PROMPT EVOLUTION TRIGGERED ({len(prompt_evolutions)} verses)")
        print(f"  {'─'*50}")
        for pe_info in prompt_evolutions:
            vk = pe_info["verse_key"]
            print(f"\n  Verse {vk[0]}:{vk[1]}:")
            print(f"    Aligned: {pe_info['aligned']}")
            for i, (err, imp) in enumerate(zip(
                    pe_info["error_descriptions"], pe_info["improvements"])):
                print(f"    Judge {i+1} error: {err[:120]}")
                print(f"    Judge {i+1} fix:   {imp[:120]}")

    print(f"{'='*60}")
