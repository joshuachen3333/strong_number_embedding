#!/usr/bin/env python3
"""run_bakeoff.py — Survey5 v2 multi-source bake-off (Round 1: A vs B).

A = WLC-only (Hebrew original -> UNV).
B = WLC + KJV (Hebrew original + English bridge -> UNV).
Scores vs FHL UNV+SN gold: overall (auto_score) + 09xxx recall + per trust-tier recall.
Spec: docs/superpowers/specs/2026-06-26-survey5-multisource-bakeoff-design.md
"""
import argparse
import json
import os
import sys
import time

import wlc_bridge as W
import gate as G
# Importing run_survey5 puts the parent dir and survey4 dir on sys.path, so the
# following imports resolve afterwards.
from run_survey5 import call_model, detect_brand, fetch_chap_cached  # noqa: E402
from auto_score import score_verse, strip_sn  # noqa: E402
from llm_direct_sn_unv2notyet import CHI_TO_ENG, parse_sec_arg  # noqa: E402

SYSTEM = (
    "You are an expert in Strong's Number annotation of biblical texts. "
    "Given a source text already tagged with Strong's Numbers, place those tags "
    "onto the correct positions of the plain Chinese (UNV) text. "
    "Output ONLY the annotated UNV text on a single line, no commentary."
)


def build_a_prompt(wlc_source, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec):
    """Config A: WLC (Hebrew+SN) -> UNV. Reuses s10's harsh prompt; ignores KJV."""
    return W.build_harsh_prompt(wlc_source, unv_plain, book_eng, chap, sec)


def build_b_prompt(wlc_source, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec):
    """Config B: WLC (Hebrew+SN) + KJV (plain & +SN) -> UNV."""
    return f"""Here is {book_eng} {chap}:{sec} in the original Hebrew (WLC), each \
morpheme tagged with its FHL Strong's Number (inseparable prefixes use the 09xxx \
codes: 09001=לְ to/for, 09002=בְּ in, 09003=כְּ as, 09006=מִ from, 09009=הַ the):

{wlc_source}

Here is the same verse in KJV (plain, no tags):

{kjv_plain}

Here is the same verse in KJV with Strong's Number annotations:

{kjv_sn}

Here is the same verse in UNV (和合本), plain, no annotations:

{unv_plain}

Using the Hebrew and the KJV annotation pair above as your references, insert the \
Strong's Number tags into the correct positions in the UNV text, INCLUDING the \
09xxx inseparable-prefix tags where the Chinese expresses them. Output ONLY the \
annotated UNV text on a single line, no commentary."""


BUILDERS = {"A": build_a_prompt, "B": build_b_prompt}


def run_config(label, build_user, verses, book_eng, model, brand):
    rows = []
    for (chap, sec, unv_sn, wlc_source, kjv_plain, kjv_sn) in verses:
        unv_plain = strip_sn(unv_sn)
        user = build_user(wlc_source, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec)
        t0 = time.time()
        out = call_model(model, brand, None, SYSTEM, user)
        if not out:
            print(f"  [{label}] {chap}:{sec}  EMPTY (skip)", flush=True)
            continue
        sc = score_verse(out, unv_sn)
        n9p, n9t = W.nines_recall(out, unv_sn)
        tiers = G.tier_recall(out, unv_sn, wlc_source, kjv_sn)
        rows.append({"chap": chap, "sec": sec, "score": sc,
                     "n9_placed": n9p, "n9_total": n9t, "tiers": tiers,
                     "output": out})
        r9 = f"{n9p}/{n9t}" if n9t else "—"
        print(f"  [{label}] {chap}:{sec}  cov={sc['coverage']:.3f} "
              f"place={sc['placement']:.3f} 09xxx={r9} {time.time()-t0:.0f}s",
              flush=True)
    return rows


def print_summary(results):
    print(f"\n{'='*72}\n  SUMMARY\n{'='*72}")
    print(f"  {'cfg':<5}{'cov':>8}{'place':>8}{'fmt':>8}"
          f"{'09xxx':>12}{'rock':>9}{'wlc_only':>10}{'kjv_only':>10}")
    for cfg, rows in results.items():
        if not rows:
            continue
        n = len(rows)
        cov = sum(r["score"]["coverage"] for r in rows) / n
        place = sum(r["score"]["placement"] for r in rows) / n
        fmt = sum(r["score"]["format"] for r in rows) / n
        n9p = sum(r["n9_placed"] for r in rows)
        n9t = sum(r["n9_total"] for r in rows)
        n9 = f"{n9p}/{n9t} ({100*n9p/n9t:.0f}%)" if n9t else "n/a"

        def tier_frac(tier):
            p = sum(r["tiers"].get(tier, {}).get("placed", 0) for r in rows)
            t = sum(r["tiers"].get(tier, {}).get("total", 0) for r in rows)
            return f"{100*p/t:.0f}%" if t else "—"

        print(f"  {cfg:<5}{cov:>8.3f}{place:>8.3f}{fmt:>8.3f}{n9:>12}"
              f"{tier_frac('rock'):>9}{tier_frac('wlc_only'):>10}"
              f"{tier_frac('kjv_only'):>10}")


def main():
    ap = argparse.ArgumentParser(description="Survey5 multi-source bake-off (A vs B)")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", type=int, default=1)
    ap.add_argument("--sec", default=None, help="e.g. 1 or 1-5 or 1,3,5")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--configs", default="A,B")
    ap.add_argument("--out", nargs="?", const="", default=None)
    args = ap.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    wlc_book = W.CHI_TO_WLC_BOOK.get(book_chi)
    if not wlc_book:
        sys.exit(f"No WLC book number for {book_chi}; add to s10 CHI_TO_WLC_BOOK.")
    brand = detect_brand(args.model, None)

    unv = fetch_chap_cached(book_chi, args.chap, "unv", strong=1)
    kjv = fetch_chap_cached(book_chi, args.chap, "kjv", strong=1)
    secs = sorted(set(unv) & set(kjv))
    if args.sec:
        want = set(parse_sec_arg([args.sec]))
        secs = [s for s in secs if s in want]

    verses = []
    for sec in secs:
        wlc_source = W.build_wlc_source(W.load_wlc_verse(wlc_book, args.chap, sec))
        if not wlc_source:
            continue
        verses.append((args.chap, sec, unv[sec], wlc_source,
                       strip_sn(kjv[sec]), kjv[sec]))

    print(f"\n{'='*72}\n  Survey5 BAKE-OFF — {book_eng} {args.chap} "
          f"({len(verses)} verses)  model={args.model}  configs={args.configs}\n{'='*72}")

    results = {}
    for cfg in [c.strip() for c in args.configs.split(",") if c.strip()]:
        if cfg not in BUILDERS:
            print(f"  (config {cfg} not implemented — skip)")
            continue
        print(f"\n── Config {cfg} ──", flush=True)
        results[cfg] = run_config(cfg, BUILDERS[cfg], verses, book_eng,
                                  args.model, brand)

    print_summary(results)

    if args.out is not None:
        out_path = args.out or os.path.join(
            "run_logs", f"bakeoff_{book_chi}{args.chap}_{args.model.replace(':', '_')}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"book": book_chi, "chap": args.chap, "model": args.model,
                       "configs": args.configs, "results": results},
                      f, ensure_ascii=False, indent=2)
        print(f"\n  wrote {out_path}")


if __name__ == "__main__":
    main()
