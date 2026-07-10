#!/usr/bin/env python3
"""s10 self-opt round 2 — M-tier per-model conventions (D1 + D2 + D2-X + D3).

LOCKED spec: CONVENTIONS_PIPELINE.md §"🔒 LOCKED build spec" + docs/20260630_obe_s10_self_opt_decision.md.

This module is the per-model twin of conventions.py (which holds the GLOBAL C-tier).
It replaces Trigger-2's per-model *prompt patch* with a per-model *conventions file*
(`conventions.{model}.md`, "M-tier"), so s10 becomes fully conventions-based with
ZERO prompt mutation — Trigger-1 already writes global conventions; this closes the
per-model asymmetry.

What lives here:
  D1  load/build/append/version conventions.{model}.md; run_mtier_regression (reuse
      run_gold_standard._run_patch_regression); try_evolve_model_convention (the
      Trigger-2 replacement); check_promotions (an M-rule active in >=k=roster-
      majority models -> promote to a global C via the GLOBAL gate); demotion.
  D2  import_s1_patches_as_inactive: warm-start — s1's per-model patches imported as
      INACTIVE M-candidates that must pass the SAME gate before activation.
  D2-X versioned_resync: a manual prompt re-sync is a first-class versioned event
      (auto-snapshot + baseline bump + provenance-tag gold + re-gate), never a silent copy.
  D3  falsify_model_conventions / falsify_global_conventions: per-convention A/B on
      an objective FHL-truth delta -> automated quarantine of neutral/negative rules.

The trust model is identical to s1's: the gate is s1's regression discipline, just
pointed at a finer artifact. Nothing invents new trust machinery.
"""

import os
import re
import json
import shutil
from datetime import datetime

import conventions as conv_mod
from conventions import (S10_DIR, CONVENTIONS_HISTORY_DIR, CONVENTION_BUDGET,
                         load_conventions, conventions_text, append_convention,
                         run_convention_regression)

# ── M-tier storage ────────────────────────────────────────────────────────────

MTIER_BUDGET = 15          # max active M-rules per model (tighter than global 25)
PROMOTION_K = None         # None -> roster majority computed at call time
PROVENANCE_TAG_KEY = "_baseline_version"   # written into gold files by D2-X


def _mtier_path(model_name):
    return os.path.join(S10_DIR, f"conventions.{model_name}.md")


def _mtier_history_dir(model_name):
    return os.path.join(CONVENTIONS_HISTORY_DIR, model_name)


def _mtier_marker(model_name):
    return f"<!-- s10:mtier-{model_name} -->"


# Heading: "## M3  <title>   [added v0.2 · gate PASS · <prov> · active]"
_MRULE_RE = re.compile(r"^##\s+(M\d+)\b[ \t]*(.*)$", re.MULTILINE)


def load_model_conventions(model_name, active_only=False):
    """Parse conventions.{model}.md → list of {id,title,body,active,promoted}.

    `active` is False for D2 warm-start candidates that have not yet passed the
    gate (heading carries `· inactive`). `promoted` marks M-rules already lifted to
    a global C (so promotion doesn't re-fire).
    """
    path = _mtier_path(model_name)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    out = []
    matches = list(_MRULE_RE.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        heading_line = text[m.start():start]
        body = text[start:end].strip()
        active = "· inactive" not in heading_line
        promoted = "· promoted" in heading_line
        rule = {"id": m.group(1), "title": m.group(2).strip(), "body": body,
                "active": active, "promoted": promoted}
        if active_only and not active:
            continue
        out.append(rule)
    return out


def model_conventions_text(model_name, active_only=True):
    rules = load_model_conventions(model_name, active_only=active_only)
    if not rules:
        return ""
    lines = []
    for r in rules:
        lines.append(f"- {r['id']} {r['title']}".rstrip())
        for bl in (r["body"] or "").splitlines():
            bl = bl.strip()
            if bl and not bl.startswith("<!--") and not bl.startswith("["):
                lines.append(f"    {bl}")
    return "\n".join(lines)


def build_model_conventions_preamble(model_name, target_version="lcc"):
    """The per-model block appended to that model's leg prompt — the D1 replacement
    for the Trigger-2 `model_patch` append at run_gold_standard.py:~814.

    Always emits the greppable marker so the wiring is verifiable in the empty
    (no-M-rule) state, mirroring the global preamble's PREAMBLE_MARKER contract.
    """
    marker = _mtier_marker(model_name)
    body = model_conventions_text(model_name, active_only=True)
    if not body.strip():
        return f"\n## Per-model conventions ({model_name}) — none yet\n{marker}\n"
    return (
        f"\n## Per-model conventions ({model_name}) — APPLY THESE\n"
        "Regression-gated placement rules specific to your own past instability. "
        "Apply unless the current verse clearly contradicts them:\n\n"
        f"{body}\n{marker}\n"
    )


# ── versioning (per model) ────────────────────────────────────────────────────

def _current_mtier_version(model_name):
    path = _mtier_path(model_name)
    if not os.path.isfile(path):
        return "v0.0"
    with open(path, "r", encoding="utf-8") as f:
        head = f.read(400)
    m = re.search(r"#\s*conventions\.\w+\.md\s*—\s*v(\d+)\.(\d+)", head)
    return f"v{m.group(1)}.{m.group(2)}" if m else "v0.0"


def _next_mtier_version(model_name):
    cur = _current_mtier_version(model_name)
    m = re.match(r"v(\d+)\.(\d+)", cur)
    return f"v{m.group(1)}.{int(m.group(2)) + 1}" if m else "v0.1"


def _snapshot_mtier(model_name, version):
    hist = _mtier_history_dir(model_name)
    os.makedirs(hist, exist_ok=True)
    with open(_mtier_path(model_name), "r", encoding="utf-8") as f:
        snap = f.read()
    with open(os.path.join(hist, f"{version}.md"), "w", encoding="utf-8") as f:
        f.write(snap)


def append_model_convention(model_name, candidate_rule, provenance, active=True):
    """Append an M-rule to conventions.{model}.md; bump version; snapshot.

    active=False stages a D2 warm-start candidate that must be activated by a later
    gate pass (activate_model_convention)."""
    path = _mtier_path(model_name)
    rules = load_model_conventions(model_name)
    new_id = f"M{len(rules) + 1}"
    new_ver = _next_mtier_version(model_name)
    title, _, rest = candidate_rule.strip().partition("\n")
    state = "active" if active else "inactive"
    block = (
        f"\n## {new_id}  {title.strip()}"
        f"   [added {new_ver} · gate {'PASS' if active else 'STAGED'} · {provenance} · {state}]\n"
        f"{rest.strip()}\n"
    )
    if not os.path.isfile(path):
        header = (
            f"# conventions.{model_name}.md — {new_ver}   (s10 M-tier: {model_name})\n\n"
            "Regression-gated, versioned per-model placement rules — the Trigger-2 "
            "replacement (no prompt patch). One `## M<n>` per atomic rule.\n"
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(header + block)
    else:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        text = re.sub(r"(#\s*conventions\.\w+\.md\s*—\s*)v\d+\.\d+",
                      rf"\g<1>{new_ver}", text, count=1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n" + block)
    _snapshot_mtier(model_name, new_ver)
    return new_id, new_ver


def _rewrite_rule_heading(model_name, rule_id, transform):
    """Apply `transform(heading_line)->heading_line` to one M-rule heading in place."""
    path = _mtier_path(model_name)
    if not os.path.isfile(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    changed = False
    for i, ln in enumerate(lines):
        m = re.match(rf"^##\s+{re.escape(rule_id)}\b", ln)
        if m:
            new = transform(ln.rstrip("\n"))
            if new != ln.rstrip("\n"):
                lines[i] = new + "\n"
                changed = True
            break
    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    return changed


def activate_model_convention(model_name, rule_id):
    return _rewrite_rule_heading(
        model_name, rule_id,
        lambda h: h.replace("· inactive", "· active").replace("gate STAGED", "gate PASS"))


def demote_model_convention(model_name, rule_id, reason):
    """Mark an M-rule inactive (D3 falsification / demotion). Kept in the file as an
    audit trail rather than deleted."""
    ok = _rewrite_rule_heading(
        model_name, rule_id,
        lambda h: (h.replace("· active", "· inactive")
                   + f"  (demoted {datetime.now():%Y-%m-%d}: {reason})"
                   if "demoted" not in h else h))
    if ok:
        print(f"  [M-tier] {model_name}:{rule_id} DEMOTED — {reason}", flush=True)
    return ok


def _mark_promoted(model_name, rule_id, global_id):
    return _rewrite_rule_heading(
        model_name, rule_id,
        lambda h: h if "· promoted" in h else h + f" · promoted→{global_id}")


# ── D1 gate: reuse s1's per-model 回測 ─────────────────────────────────────────

def run_mtier_regression(model_name, candidate_rule, base_prompt, convergence_results,
                         verse_data, models, target_version, sn_field,
                         instability_level="mild", naked=False, verbose=False):
    """Gate an M-candidate by REUSING the existing per-model minor 回測
    (`_run_patch_regression`): the candidate rule is handed in as the patch text, so
    the same solo-re-run-on-past-verses discipline applies. Returns bool ok."""
    from run_gold_standard import _run_patch_regression
    # The rule is injected the same way the preamble injects it (as an appended block).
    patch_text = build_model_conventions_preamble_trial(model_name, candidate_rule)
    return _run_patch_regression(
        model_name=model_name, prompt_version="mtier",
        base_prompt=base_prompt, patch_text=patch_text,
        convergence_results=convergence_results, verse_data=verse_data,
        models=models, target_version=target_version, sn_field=sn_field,
        verbose=verbose, instability_level=instability_level, naked=naked)


def build_model_conventions_preamble_trial(model_name, candidate_rule):
    """Preamble as it WOULD look with one extra candidate M-rule — used by the gate
    before the rule is written."""
    body = model_conventions_text(model_name, active_only=True)
    merged = (body + "\n- CANDIDATE " + candidate_rule.strip()).strip()
    return (
        f"\n## Per-model conventions ({model_name}) — APPLY THESE\n\n"
        f"{merged}\n{_mtier_marker(model_name)}\n"
    )


def try_evolve_model_convention(model_name, candidate_rule, base_prompt,
                                convergence_results, verse_data, models,
                                target_version, sn_field, provenance,
                                instability_level="mild", naked=False, verbose=False):
    """The Trigger-2 replacement: gate an M-candidate; on PASS append it ACTIVE.
    Returns (accepted: bool). A FAIL leaves the model unpatched (the verse's own
    C-tier / D-tier handling still applies)."""
    active = load_model_conventions(model_name, active_only=True)
    if len(active) >= MTIER_BUDGET:
        print(f"  [M-tier] {model_name} budget ({MTIER_BUDGET}) reached — "
              f"skip candidate (merge/demote first)", flush=True)
        return False
    ok = run_mtier_regression(
        model_name, candidate_rule, base_prompt, convergence_results, verse_data,
        models, target_version, sn_field, instability_level, naked, verbose)
    if ok:
        mid, ver = append_model_convention(model_name, candidate_rule, provenance,
                                           active=True)
        print(f"  [M-tier] {model_name}:{mid} ACCEPTED ({ver}) ← {provenance}",
              flush=True)
        return True
    print(f"  [M-tier] {model_name} candidate REGRESSION-FAILED ← {provenance}",
          flush=True)
    return False


# ── D1 promotion: M-rule in >=k models -> global C ────────────────────────────

def _stem(w):
    """Light singular/participle stemming so 'binds'/'bind', 'nouns'/'noun' cluster."""
    for suf in ("ing", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)]
    return w


def _rule_key_tokens(text):
    return {_stem(w) for w in re.findall(r"\w+", text.lower()) if len(w) > 3}


def _rules_match(a, b, thresh=0.5):
    """Fuzzy same-rule test for cross-model promotion clustering. Deliberately
    permissive (Jaccard ≥ 0.5 OR a shared Strong's-number token) — promotion has TWO
    further safety layers (k-majority requirement + the global regression gate), so
    surfacing a candidate cheaply and letting the gate reject bad ones is correct."""
    ta, tb = _rule_key_tokens(a), _rule_key_tokens(b)
    if not ta or not tb:
        return False
    # A shared Strong's-number token (e.g. 0853) is a strong same-topic signal.
    nums_a = {w for w in ta if w.isdigit() and len(w) >= 3}
    if nums_a & tb:
        return True
    overlap = len(ta & tb) / max(len(ta | tb), 1)
    return overlap >= thresh


def check_promotions(models, base_prompt, book_chi, book_eng, target_version,
                     sn_field, verbose=False):
    """D1 cross-model promotion. An ACTIVE, not-yet-promoted M-rule that appears
    (fuzzy-match) ACTIVE in >= k = roster majority models is promoted to a global
    C<n> — but ONLY if it passes the GLOBAL regression gate (no regression on the
    non-promoting model). Returns list of promoted (global_id, title)."""
    k = PROMOTION_K or (len(models) // 2 + 1)
    names = [m["name"] for m in models]
    per_model = {n: load_model_conventions(n, active_only=True) for n in names}

    promoted = []
    # Cluster equivalent rules across models.
    seen = set()
    for n in names:
        for rule in per_model[n]:
            if rule["promoted"] or (n, rule["id"]) in seen:
                continue
            cluster = [(n, rule)]
            for other in names:
                if other == n:
                    continue
                for orule in per_model[other]:
                    if orule["promoted"]:
                        continue
                    if _rules_match(rule["title"] + " " + rule["body"],
                                    orule["title"] + " " + orule["body"]):
                        cluster.append((other, orule))
                        break
            distinct_models = {mn for mn, _ in cluster}
            if len(distinct_models) >= k:
                # Candidate global rule = the representative rule text.
                rule_text = (rule["title"] + "\n" + rule["body"]).strip()
                ok, _ = run_convention_regression(
                    rule_text, base_prompt, (0, 0), book_chi, book_eng, models,
                    target_version, sn_field, verbose=verbose)
                if ok:
                    prov = f"promoted k={len(distinct_models)}/{len(models)} " \
                           f"({'+'.join(sorted(distinct_models))})"
                    gid, gver = append_convention(rule_text, prov)
                    for mn, r in cluster:
                        _mark_promoted(mn, r["id"], gid)
                        seen.add((mn, r["id"]))
                    promoted.append((gid, rule["title"]))
                    print(f"  [promote] {gid} ← {prov} ({gver})", flush=True)
                else:
                    print(f"  [promote] cluster '{rule['title'][:40]}' FAILED "
                          f"global gate — not promoted", flush=True)
            seen.add((n, rule["id"]))
    return promoted


# ── D2 warm-start: import s1 patches as INACTIVE M-candidates ─────────────────

def import_s1_patches_as_inactive(models, prompt_version="v1.2", verbose=False):
    """D2 reconciled warm-start. Read s1's per-model prompt patches and stage each as
    an INACTIVE M-candidate (must pass the standard gate via activate path before it
    influences a run). Head-start WITHOUT pre-enabled inheritance. Idempotent: skips
    a patch already imported (title match)."""
    s1_prompts = os.path.join(os.path.dirname(S10_DIR),
                              "survey1_prompt_evolving", "prompts")
    if not os.path.isdir(s1_prompts):
        print(f"  [warm-start] no s1 prompts dir — skipping", flush=True)
        return {}
    staged = {}
    for m in models:
        name = m["name"]
        existing_titles = {r["title"] for r in load_model_conventions(name)}
        for fname in sorted(os.listdir(s1_prompts)):
            # Lenient family match: s1 patches carry model-family names
            # (gpt-5.4-patch, opus-patch, codex-patch) that may differ from the s10
            # panel label (gpt, opus, agy). Match `.<name>` + `-patch-` so a family
            # prefix (gpt → gpt-5.4) still imports. Inactive-staged, so a loose match
            # is safe — the gate decides activation.
            if f".{name}" not in fname or "-patch-" not in fname \
                    or not fname.endswith(".md"):
                continue
            with open(os.path.join(s1_prompts, fname), "r", encoding="utf-8") as f:
                patch = f.read().strip()
            # Reduce a whole patch file to one atomic candidate line (its first
            # substantive directive) — the gate later decides if it earns activation.
            line = _first_directive(patch)
            if not line or line in existing_titles:
                continue
            append_model_convention(
                name, line, provenance=f"s1-warmstart {fname}", active=False)
            staged.setdefault(name, []).append(line[:60])
            existing_titles.add(line)
    if verbose:
        for n, ls in staged.items():
            print(f"  [warm-start] {n}: staged {len(ls)} inactive M-candidate(s)")
    return staged


def _first_directive(patch_text):
    for ln in patch_text.splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#") and not ln.startswith("<!--") \
                and not ln.startswith(">") and len(ln) > 20:
            return ln
    return ""


# ── D2-X: versioned re-sync (manual prompt re-sync = first-class event) ────────

def versioned_resync(new_baseline_version, models, base_prompt, book_chi, book_eng,
                     target_version, sn_field, gold_dir=None, verbose=False):
    """A manual prompt re-sync is NEVER a silent copy. Atomically:
      1. auto-snapshot gold + conventions*.md + baseline version (frozen contest arm),
      2. bump baseline version + provenance-tag every gold file,
      3. re-run the full convention regression against the new prompt →
         auto-quarantine any convention that no longer passes.
    Returns a report dict. `base_prompt` is the NEW (re-synced) prompt.
    """
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    gold_dir = gold_dir or os.path.join(S10_DIR, "gold_standard")
    snap_root = os.path.join(S10_DIR, "resync_snapshots", f"{stamp}_pre_{new_baseline_version}")
    os.makedirs(snap_root, exist_ok=True)

    # 1. snapshot gold + all conventions*.md
    if os.path.isdir(gold_dir):
        shutil.copytree(gold_dir, os.path.join(snap_root, "gold_standard"),
                        dirs_exist_ok=True)
    for f in os.listdir(S10_DIR):
        if f.startswith("conventions") and f.endswith(".md"):
            shutil.copy2(os.path.join(S10_DIR, f), os.path.join(snap_root, f))
    report = {"snapshot": snap_root, "new_baseline": new_baseline_version,
              "provenance_tagged": 0, "quarantined": []}

    # 2. provenance-tag every gold file with the baseline that produced it.
    for root, _dirs, files in os.walk(gold_dir):
        for fn in files:
            if not fn.endswith(".json"):
                continue
            fp = os.path.join(root, fn)
            try:
                d = json.load(open(fp, encoding="utf-8"))
            except Exception:
                continue
            if PROVENANCE_TAG_KEY not in d:
                d[PROVENANCE_TAG_KEY] = "pre-resync"   # produced under the old baseline
            d["_resynced_to"] = new_baseline_version
            json.dump(d, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            report["provenance_tagged"] += 1

    # 3. re-gate every active convention (global + per-model) against the NEW prompt.
    for rule in load_conventions():
        rule_text = (rule["title"] + "\n" + rule["body"]).strip()
        ok, _ = run_convention_regression(
            rule_text, base_prompt, (0, 0), book_chi, book_eng, models,
            target_version, sn_field, verbose=verbose)
        if not ok:
            report["quarantined"].append(("global", rule["id"]))
    for m in models:
        name = m["name"]
        for rule in load_model_conventions(name, active_only=True):
            rule_text = (rule["title"] + "\n" + rule["body"]).strip()
            ok = run_mtier_regression(
                name, rule_text, base_prompt, {}, {}, models, target_version,
                sn_field, verbose=verbose)
            if not ok:
                demote_model_convention(name, rule["id"],
                                        f"re-gate fail @ {new_baseline_version}")
                report["quarantined"].append((name, rule["id"]))

    with open(os.path.join(snap_root, "resync_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  [D2-X] re-sync → {new_baseline_version}: "
          f"{report['provenance_tagged']} gold tagged, "
          f"{len(report['quarantined'])} convention(s) quarantined; "
          f"snapshot {snap_root}", flush=True)
    return report


# ── D3: falsification loop (objective FHL-truth delta) ────────────────────────

def falsify_conventions(models, target_version, sn_field, sample_book="創",
                        sample_chaps=(1,), verbose=False, dry_run=False):
    """D3 falsification. For each active convention (global C + per-model M), measure
    an OBJECTIVE FHL-truth delta by re-annotating UNV verses (which carry REAL FHL
    Strong's tags) WITH vs WITHOUT the rule, scoring each against the FHL ground
    truth. A rule whose delta is neutral/negative is quarantined (global) / demoted
    (M) — automated; manual override only for documented theological exceptions.

    Returns a report dict. `dry_run=True` computes deltas without demoting.
    """
    from fhl_truth_delta import convention_fhl_delta   # thin objective scorer
    report = {"evaluated": 0, "quarantined": [], "kept": []}
    lead = models[0]

    def _eval(scope, rule_id, rule_text, demote_fn):
        try:
            delta = convention_fhl_delta(
                rule_text, lead, target_version, sample_book, sample_chaps,
                verbose=verbose)
        except Exception as e:
            print(f"  [D3] {scope}:{rule_id} scorer error ({e}) — skipped", flush=True)
            return
        report["evaluated"] += 1
        if delta <= 0.0:
            report["quarantined"].append((scope, rule_id, round(delta, 4)))
            if not dry_run:
                demote_fn()
            print(f"  [D3] {scope}:{rule_id} delta={delta:+.4f} → QUARANTINE"
                  f"{' (dry-run)' if dry_run else ''}", flush=True)
        else:
            report["kept"].append((scope, rule_id, round(delta, 4)))
            print(f"  [D3] {scope}:{rule_id} delta={delta:+.4f} → keep", flush=True)

    for rule in load_conventions():
        rule_text = (rule["title"] + "\n" + rule["body"]).strip()
        _eval("global", rule["id"], rule_text,
              lambda rid=rule["id"]: _quarantine_global(rid))
    for m in models:
        name = m["name"]
        for rule in load_model_conventions(name, active_only=True):
            rule_text = (rule["title"] + "\n" + rule["body"]).strip()
            _eval(name, rule["id"], rule_text,
                  lambda n=name, rid=rule["id"]: demote_model_convention(
                      n, rid, "D3 FHL-truth delta ≤ 0"))
    return report


def _quarantine_global(rule_id):
    """Mark a global C-rule quarantined in conventions.md (audit-preserving)."""
    path = conv_mod.CONVENTIONS_PATH
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    for i, ln in enumerate(lines):
        if re.match(rf"^##\s+{re.escape(rule_id)}\b", ln) and "QUARANTINED" not in ln:
            lines[i] = ln.rstrip("\n") + "  (QUARANTINED: D3 FHL-truth delta ≤ 0)\n"
            break
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"  [D3] global:{rule_id} QUARANTINED", flush=True)
