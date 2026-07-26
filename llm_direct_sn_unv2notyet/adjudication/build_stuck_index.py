#!/usr/bin/env python3
"""Build the "stuck verse" adjudication index for s1 + s10.

MVP scope (2026-07-27): ONLY the verses that never settle — the ones whose
design endpoint is a human looking at them. Everything else (all surveyN,
resolved verses, benchmark leaderboards) is out of scope here; see
docs/superpowers/specs/2026-07-25-unified-adjudication-viewer-design.md.

The completion predicate is `trust_tier`, NEVER file existence — s10 has
425/425 files yet 56 unsettled verses, and s1's most-worked verses have no
file at all. Both invisibility modes are handled:

  form=blank_ballot     file exists, trust_tier null, a model returned ""
  form=true_divergence  file exists, trust_tier null, all 3 answered, no consensus
  form=judge_error      file exists, trust_tier null, an R3 judge errored
  form=no_file          no gold file; listed in deferred_ch*/accept_empty_confirmed
  form=corrupt          file exists but does not parse

Reads only; writes one bundle to adjudication/stuck_index.json.

Usage:
    python3 adjudication/build_stuck_index.py
    python3 adjudication/build_stuck_index.py --surveys s1
    python3 adjudication/build_stuck_index.py -o /tmp/probe.json
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LLM_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(LLM_DIR)

SURVEYS = {
    "s1": {
        "dir": os.path.join(LLM_DIR, "survey1_prompt_evolving"),
        "title": "survey1 — prompt evolving",
    },
    "s10": {
        "dir": os.path.join(LLM_DIR, "survey10_s1_but_obe_insteadOf_oneshot"),
        "title": "survey10 — conventions ledger",
    },
}

UNV_DB = os.path.join(REPO_ROOT, "original_text_preparation", "source_sqlite", "bible_little.db")
LCC_DB = os.path.join(REPO_ROOT, "original_text_preparation", "source_sqlite", "bible_lcc.db")

DEFAULT_OUT = os.path.join(HERE, "stuck_index.json")

# Attempt labels come from judge.py:_r2_label — R1, then R2a, R2b, ... We only
# need to *render* them, and the stored `attempts` list is positional, so mirror
# that scheme rather than importing judge.py (which pulls in the CLI stack).
def _attempt_label(i):
    if i == 0:
        return "R1"
    n = i - 1  # 0 -> a
    label = ""
    while True:
        label = chr(ord("a") + (n % 26)) + label
        n = n // 26 - 1
        if n < 0:
            break
    return "R2" + label


def _load_json_safe(path):
    """Returns (data, error). Tolerates missing, 0-byte, truncated, and
    mid-scan deletion — all of which occur in practice (live gold runs +
    sibling cleanup sweeps). Parse failure is the predicate, NOT file size:
    a half-written JSON can be hundreds of bytes and still be garbage."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError:
        return None, "parse_failed"
    except OSError as e:
        return None, f"io_error:{e.__class__.__name__}"


# ── local text mirrors (zero FHL load) ───────────────────────────────────────

def _load_text_table(db_path, table, book):
    """{(chap, sec): txt} for one book, or {} if the mirror is unavailable."""
    if not os.path.exists(db_path):
        return {}
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
        try:
            rows = con.execute(
                f"SELECT chap, sec, txt FROM {table} WHERE engs = ?", (book,)
            ).fetchall()
        finally:
            con.close()
    except sqlite3.Error:
        return {}
    return {(int(c), int(s)): t for c, s, t in rows}


# ── candidate extraction ─────────────────────────────────────────────────────

def _blank(text):
    return not (text or "").strip()


def _candidates_from_round1(round1):
    """round1 dict -> candidate list. Roster is read from the keys, never
    hardcoded: s1 has 8 files on the old gemini/gpt roster, and runs can pass
    --modelsABC."""
    out = []
    for model in sorted((round1 or {}).keys()):
        entry = round1[model] or {}
        sn = entry.get("lcc_sn", "") or ""
        out.append({
            "cid": f"panelist/{model}",
            "role": "panelist",
            "model": model,
            "sn_text": sn,
            "blank": _blank(sn),
            "self_confidence": entry.get("confidence"),
            "opinion": entry.get("opinion"),
            "sn_coverage": entry.get("_sn_coverage"),
            "notes": entry.get("notes"),
        })
    return out


def _judge_candidates(gold):
    """Judge `corrected` strings are real answers a human may pick, so they
    become candidates too. Judge verdict/reasoning stays in `judges`."""
    cands, judges = [], []
    for rnd in ("round2", "round3"):
        block = gold.get(rnd) or {}
        for key in sorted(block.keys()):
            entry = block[key] or {}
            model = key.replace("_as_judge", "")
            errored = bool(entry.get("error")) or entry.get("verdict") == "unknown"
            judges.append({
                "round": rnd,
                "model": model,
                "verdict": entry.get("verdict"),
                "best": entry.get("best"),
                "reasoning": entry.get("reasoning"),
                "sn_counts": entry.get("sn_counts"),
                "sn_count_unv": entry.get("sn_count_unv"),
                "errored": errored,
            })
            corrected = entry.get("corrected")
            if corrected and not _blank(corrected):
                cands.append({
                    "cid": f"judge_corrected/{rnd}/{model}",
                    "role": "judge_corrected",
                    "model": model,
                    "round": rnd,
                    "sn_text": corrected,
                    "blank": False,
                    "self_confidence": None,
                })
    return cands, judges


def _read_traces(survey_dir, book, chap, sec):
    """R2 convergence traces, deduped with multiplicity.

    Attempts are EVIDENCE, not candidates: Gen 6:17 has 31 attempts over ~9
    distinct texts, so promoting each to a pickable row would drown the UI.
    The ordered list is kept for replay; `distinct` is what the UI shows."""
    r2_dir = os.path.join(survey_dir, "round2_results")
    if not os.path.isdir(r2_dir):
        return []
    traces = []
    for model in sorted(os.listdir(r2_dir)):
        path = os.path.join(r2_dir, model, book, f"{chap}_{sec}_convergence.json")
        if not os.path.exists(path):
            continue
        data, err = _load_json_safe(path)
        if err:
            traces.append({"model": model, "damaged": err, "attempts": [],
                           "distinct": [], "n_attempts": 0, "n_distinct": 0})
            continue
        raw = data.get("attempts") or []
        attempts = [{"label": _attempt_label(i), "text": t} for i, t in enumerate(raw)]
        groups = defaultdict(list)
        for a in attempts:
            groups[a["text"]].append(a["label"])
        stable = data.get("stable_result")
        distinct = sorted(
            ({"text": t, "labels": labs, "count": len(labs),
              "is_stable": bool(stable) and t.strip() == (stable or "").strip()}
             for t, labs in groups.items()),
            key=lambda g: (-g["count"], g["labels"][0]),
        )
        traces.append({
            "model": model,
            "damaged": None,
            "converged": data.get("converged"),
            "stable_at": data.get("stable_at"),
            "bailed_out": data.get("bailed_out"),
            "stable_result": stable,
            "attempts": attempts,
            "distinct": distinct,
            "n_attempts": len(attempts),
            "n_distinct": len(distinct),
        })
    return traces


def _read_round1_dir(survey_dir, book, chap, sec):
    """For no-file verses: round1_results/{model}/{Book}/{chap}/{sec}.json.
    NOTE the naming differs from round2's {chap}_{sec} — a real trap."""
    r1_dir = os.path.join(survey_dir, "round1_results")
    if not os.path.isdir(r1_dir):
        return {}
    out = {}
    for model in sorted(os.listdir(r1_dir)):
        path = os.path.join(r1_dir, model, book, str(chap), f"{sec}.json")
        if not os.path.exists(path):
            continue
        data, err = _load_json_safe(path)
        if err or not isinstance(data, dict):
            continue
        out[model] = data
    return out


# ── deferred / accept-empty lists (the authority for no-file verses) ─────────

def _read_deferred(survey_dir, book="Gen"):
    """{(chap, sec): reason}. Two formats, both verified on disk:
        deferred_ch{N}.txt        "<sec>  <reason>  <timestamp>"
        accept_empty_confirmed    "<chap>:<sec>  <reason>  <timestamp>"
    """
    out = {}
    logs = os.path.join(survey_dir, "run_logs")
    if not os.path.isdir(logs):
        return out

    for fn in sorted(os.listdir(logs)):
        m = re.match(r"deferred_ch(\d+)\.txt$", fn)
        if not m:
            continue
        chap = int(m.group(1))
        try:
            lines = open(os.path.join(logs, fn), encoding="utf-8").read().splitlines()
        except OSError:
            continue
        for line in lines:
            parts = line.strip().split(None, 1)
            if not parts or not parts[0].isdigit():
                continue
            out[(chap, int(parts[0]))] = (parts[1].strip() if len(parts) > 1 else "deferred")

    ae = os.path.join(logs, "accept_empty_confirmed.txt")
    if os.path.exists(ae):
        try:
            lines = open(ae, encoding="utf-8").read().splitlines()
        except OSError:
            lines = []
        for line in lines:
            parts = line.strip().split(None, 1)
            if not parts or ":" not in parts[0]:
                continue
            c, _, s = parts[0].partition(":")
            if not (c.isdigit() and s.isdigit()):
                continue
            out[(int(c), int(s))] = (parts[1].strip() if len(parts) > 1 else "accept-empty")

    return out


# ── classification ───────────────────────────────────────────────────────────

def _classify(gold, candidates):
    """Which human-intervention shape is this? Order matters: a blank ballot
    means R1 could never agree, so it dominates."""
    panelists = [c for c in candidates if c["role"] == "panelist"]
    if any(c["blank"] for c in panelists):
        return "blank_ballot"
    r3 = gold.get("round3") or {}
    for entry in r3.values():
        entry = entry or {}
        if entry.get("error") or entry.get("verdict") == "unknown":
            return "judge_error"
    return "true_divergence"


def build(surveys, out_path):
    unv_cache, lcc_cache = {}, {}
    verses, stats = [], Counter()

    for sid in surveys:
        meta = SURVEYS[sid]
        sdir = meta["dir"]
        gold_root = os.path.join(sdir, "gold_standard")
        deferred = _read_deferred(sdir)
        seen = set()

        # ── pass 1: files that exist ────────────────────────────────────────
        if os.path.isdir(gold_root):
            for book in sorted(os.listdir(gold_root)):
                book_dir = os.path.join(gold_root, book)
                if not os.path.isdir(book_dir):
                    continue
                if book not in unv_cache:
                    unv_cache[book] = _load_text_table(UNV_DB, "unv", book)
                    lcc_cache[book] = _load_text_table(LCC_DB, "lcc", book)

                chaps = sorted((d for d in os.listdir(book_dir) if d.isdigit()), key=int)
                for chap_s in chaps:
                    chap = int(chap_s)
                    cdir = os.path.join(book_dir, chap_s)
                    if not os.path.isdir(cdir):
                        continue
                    for fn in sorted((f for f in os.listdir(cdir) if f.endswith(".json")),
                                     key=lambda f: int(f[:-5]) if f[:-5].isdigit() else 0):
                        sec_s = fn[:-5]
                        if not sec_s.isdigit():
                            continue
                        sec = int(sec_s)
                        seen.add((chap, sec))
                        gold, err = _load_json_safe(os.path.join(cdir, fn))

                        if err == "missing":
                            continue  # deleted mid-scan; pass 2 may pick it up
                        if err:
                            stats[f"{sid}:corrupt"] += 1
                            verses.append({
                                "survey": sid, "book": book, "chap": chap, "sec": sec,
                                "form": "corrupt", "damaged": err,
                                "unv_sn_reference": unv_cache[book].get((chap, sec)),
                                "lcc_original": lcc_cache[book].get((chap, sec)),
                                "candidates": [], "judges": [], "traces": [],
                            })
                            continue

                        if gold.get("trust_tier") is not None:
                            stats[f"{sid}:resolved"] += 1
                            continue

                        cands = _candidates_from_round1(gold.get("round1"))
                        jcands, judges = _judge_candidates(gold)
                        cands += jcands
                        form = _classify(gold, cands)
                        stats[f"{sid}:{form}"] += 1
                        verses.append({
                            "survey": sid, "book": book, "chap": chap, "sec": sec,
                            "form": form, "damaged": None,
                            "resolved_at": gold.get("resolved_at"),
                            "trust_tier": gold.get("trust_tier"),
                            "prompt_version": gold.get("prompt_version"),
                            "unv_sn_reference": gold.get("unv_sn_reference")
                                                or unv_cache[book].get((chap, sec)),
                            "lcc_original": gold.get("lcc_original")
                                            or lcc_cache[book].get((chap, sec)),
                            "current_lcc_sn": gold.get("lcc_sn"),
                            "current_lcc_sn_naked": gold.get("lcc_sn_naked"),
                            "candidates": cands,
                            "judges": judges,
                            "traces": _read_traces(sdir, book, chap, sec),
                        })

        # ── pass 2: verses with NO gold file (structurally invisible above) ─
        book = "Gen"  # the deferred logs are Genesis-only today
        if book not in unv_cache:
            unv_cache[book] = _load_text_table(UNV_DB, "unv", book)
            lcc_cache[book] = _load_text_table(LCC_DB, "lcc", book)
        for (chap, sec), reason in sorted(deferred.items()):
            if (chap, sec) in seen:
                continue  # a file appeared since the log was written
            r1 = _read_round1_dir(sdir, book, chap, sec)
            cands = _candidates_from_round1(r1)
            stats[f"{sid}:no_file"] += 1
            verses.append({
                "survey": sid, "book": book, "chap": chap, "sec": sec,
                "form": "no_file", "damaged": None,
                "deferred_reason": reason,
                "resolved_at": None, "trust_tier": None,
                "unv_sn_reference": unv_cache[book].get((chap, sec)),
                "lcc_original": lcc_cache[book].get((chap, sec)),
                "current_lcc_sn": None, "current_lcc_sn_naked": None,
                "candidates": cands,
                "judges": [],
                "traces": _read_traces(sdir, book, chap, sec),
            })

    verses.sort(key=lambda v: (v["survey"], v["book"], v["chap"], v["sec"]))

    bundle = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "scope": "stuck verses only (trust_tier is null, or no gold file)",
            "surveys": {s: SURVEYS[s]["title"] for s in surveys},
            "predicate": "trust_tier — NEVER file existence",
            "counts": dict(sorted(stats.items())),
            "total_stuck": len(verses),
        },
        "verses": verses,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, separators=(",", ":"))

    return bundle, out_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--surveys", default="s1,s10",
                    help="comma list of survey ids (default: s1,s10)")
    ap.add_argument("-o", "--output", default=DEFAULT_OUT)
    args = ap.parse_args()

    ids = [s.strip() for s in args.surveys.split(",") if s.strip()]
    unknown = [s for s in ids if s not in SURVEYS]
    if unknown:
        ap.error(f"unknown survey id(s): {', '.join(unknown)} "
                 f"(known: {', '.join(SURVEYS)})")

    bundle, path = build(ids, args.output)
    m = bundle["meta"]

    print(f"-> {path}  ({os.path.getsize(path)/1024:.0f} KB)")
    print(f"   stuck verses: {m['total_stuck']}")
    for k, v in m["counts"].items():
        print(f"     {k:28s} {v}")

    tr = [t for v in bundle["verses"] for t in v["traces"]]
    if tr:
        print(f"   traces: {len(tr)}  "
              f"(damaged {sum(1 for t in tr if t['damaged'])}, "
              f"max attempts {max(t['n_attempts'] for t in tr)})")
    missing_unv = sum(1 for v in bundle["verses"] if not v.get("unv_sn_reference"))
    if missing_unv:
        print(f"   WARNING: {missing_unv} verses have no UNV reference text")
    empty = sum(1 for v in bundle["verses"] if not v["candidates"])
    if empty:
        print(f"   WARNING: {empty} verses have zero candidates (nothing to pick)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
