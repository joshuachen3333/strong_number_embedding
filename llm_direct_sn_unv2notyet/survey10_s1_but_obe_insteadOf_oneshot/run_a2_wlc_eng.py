#!/usr/bin/env python3
"""A2 contest — WLC + <English> source → UNV, scored vs UNV's real FHL tags.

Base source config (survey11) = **WLC + BSB** (Joshua 2026-07-11, revised from WLC+YLT).
The readable-English bridge is swappable via --eng-source (BSB default, YLT available)
through english_bridge.py — WLC always supplies the SN inventory incl. 09xxx; the
English disambiguates which Chinese word each tag belongs to. Target UNV carries the
REAL FHL tags (answer key, never shown) so scoring escapes consensus circularity.

Arms (each isolates one factor via a PAIRED delta on shared verses):
  B      : conventions ON,  WLC+<eng>   — headline s10 arm
  B0     : conventions OFF, WLC+<eng>   — conventions control   → Δ(B−B0)     = conventions
  B_noeng: conventions ON,  WLC-only    — English control       → Δ(B−B_noeng) = the English bridge
"""

import argparse
import os
import sys
import time

_S10 = os.path.dirname(os.path.abspath(__file__))
if _S10 not in sys.path:
    sys.path.insert(0, _S10)

import build_exclusion as BX
import run_a2_contest as A2
from conventions import build_conventions_preamble
from auto_score import strip_sn
from run_stage2_harsh import (nines_recall, CHI_TO_WLC_BOOK, build_wlc_source,
                              build_harsh_prompt)
from english_bridge import load_wlc_verse_with_ids, build_wlc_eng_source, verse_text
from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG, parse_sec_arg

# (conventions_on, eng_on) per arm. Deltas isolate each factor.
ARMS = {
    "B":       (True,  True),    # WLC+eng, conventions ON   (headline)
    "B0":      (False, True),    # WLC+eng, conventions OFF  (conventions control)
    "B_noeng": (True,  False),   # WLC-only, conventions ON  (English control — s5 lesson)
}


def build_wlc_eng_prompt(source_block, unv_plain, book_eng, chap, sec, eng_name):
    return f"""Here is {book_eng} {chap}:{sec}.

{source_block}

Here is the same verse in UNV (Chinese Union Version), plain, no annotations:

{unv_plain}

Insert the Strong's Number tags into the correct positions in the UNV text, \
INCLUDING the 09xxx inseparable-prefix tags where the Chinese expresses them. Use the \
WLC Hebrew for the authoritative tag set and the {eng_name} English to disambiguate \
which Chinese word each tag belongs to. Output ONLY the annotated UNV text on a single \
line, no commentary, no code fences."""


def run_arm(label, conv_on, eng_on, eng_name, verses, model, verbose, samples):
    preamble = build_conventions_preamble("unv") if conv_on else ""
    system = (preamble + A2.SYSTEM_BASE) if preamble else A2.SYSTEM_BASE
    rows = []
    for (book_chi, book_eng, wlc_book, chap, sec, unv_sn) in verses:
        unv_plain = strip_sn(unv_sn)
        toks = load_wlc_verse_with_ids(wlc_book, chap, sec, source=eng_name)
        if not toks:
            if verbose:
                print(f"  [{label}] {chap}:{sec}  (no WLC — skip)", flush=True)
            continue
        if eng_on:
            source_block = build_wlc_eng_source(eng_name, toks, wlc_book, chap, sec)
            user = build_wlc_eng_prompt(source_block, unv_plain, book_eng, chap, sec,
                                        eng_name)
        else:
            wlc_line = build_wlc_source([(t, n) for _mid, t, n in toks])  # WLC-only
            user = build_harsh_prompt(wlc_line, unv_plain, book_eng, chap, sec)
        shared = BX.tag_multiset(unv_sn)[0]
        t0 = time.time()
        fp, n9p, n9t = [], 0, 0
        for _ in range(samples):
            out = A2.call_guarded(system, user, model)
            if not out:
                continue                       # quota-empty — DROP, never score 0
            fp.append(BX.score_placement(out, shared)["fraction"])
            p9, t9 = nines_recall(out, unv_sn)
            n9p += p9; n9t += t9
        if not fp:
            if verbose:
                print(f"  [{label}] {chap}:{sec}  DROPPED (all samples empty)", flush=True)
            continue
        rows.append({"chap": chap, "sec": sec, "full_frac": sum(fp) / len(fp),
                     "n9_placed": n9p, "n9_total": n9t, "eng_used": eng_on})
        if verbose:
            r9 = f"{n9p}/{n9t}" if n9t else "—"
            print(f"  [{label}] {chap}:{sec}  full={rows[-1]['full_frac']:.3f}  "
                  f"09xxx={r9}  {'+'+eng_name if eng_on else 'WLConly'}  "
                  f"{time.time()-t0:.0f}s", flush=True)
    return rows


def mean(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return sum(vals) / len(vals) if vals else 0.0


def _nines_recall_agg(rows):
    p = sum(r["n9_placed"] for r in rows)
    t = sum(r["n9_total"] for r in rows)
    return (p / t) if t else None, p, t


def main():
    ap = argparse.ArgumentParser(description="A2 contest — WLC+English source → UNV")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", default="1")
    ap.add_argument("--sec", default=None, help="verse range, e.g. 1-5")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--eng-source", default="BSB", choices=["BSB", "YLT"],
                    help="readable-English bridge (default BSB — survey11 base)")
    ap.add_argument("--arms", default="B,B0,B_noeng",
                    help="comma list of B / B0 / B_noeng")
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("-v", "--verbose", action="store_true", default=True)
    args = ap.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    wlc_book = CHI_TO_WLC_BOOK.get(book_chi)
    if not wlc_book:
        sys.exit(f"No WLC book number for {book_chi}; add to CHI_TO_WLC_BOOK.")
    eng_name = args.eng_source

    verses = []
    for chap in BX.parse_chap_arg(args.chap):
        unv = fetch_chap_cached(book_chi, chap, "unv", strong=1)
        secs = sorted(unv)
        if args.sec:
            want = set(parse_sec_arg([args.sec]))
            secs = [s for s in secs if s in want]
        for sec in secs:
            verses.append((book_chi, book_eng, wlc_book, chap, sec, unv[sec]))

    print(f"\n{'='*60}\n  A2 CONTEST (WLC+{eng_name} → UNV) — {book_eng} {args.chap}  "
          f"model={args.model}  verses={len(verses)}  arms={args.arms}  "
          f"samples={args.samples}\n{'='*60}")

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    results = {}
    for arm in arms:
        conv_on, eng_on = ARMS.get(arm, (arm == "B", True))
        print(f"\n  ── Arm {arm} (conventions {'ON' if conv_on else 'OFF'}, "
              f"source {'WLC+'+eng_name if eng_on else 'WLC-only'}) ──")
        results[arm] = run_arm(arm, conv_on, eng_on, eng_name, verses, args.model,
                               args.verbose, args.samples)

    print(f"\n{'='*60}\n  RESULTS ({eng_name})\n{'='*60}")
    for arm in arms:
        rows = results[arm]
        r9, p9, t9 = _nines_recall_agg(rows)
        r9s = f"{r9:.3f} ({p9}/{t9})" if r9 is not None else "—"
        print(f"  Arm {arm:8s}: n={len(rows)}  full_frac={mean(rows,'full_frac'):.3f}  "
              f"09xxx_recall={r9s}")

    def _delta(a, b, factor):
        # PAIRED delta: only verses BOTH arms scored (quota drops leave different
        # subsets; mean-of-different-sets would bias it).
        if not (a in results and b in results):
            return
        fa = {(r["chap"], r["sec"]): r["full_frac"] for r in results[a]}
        fb = {(r["chap"], r["sec"]): r["full_frac"] for r in results[b]}
        common = sorted(set(fa) & set(fb))
        if not common:
            print(f"  Δ({a} − {b}): no paired verses — cannot measure {factor}")
            return
        ma = sum(fa[k] for k in common) / len(common)
        mb = sum(fb[k] for k in common) / len(common)
        d = ma - mb
        verdict = "helps" if d > 0 else ("neutral" if d == 0 else "hurts")
        warn = "  ⚠ SMALL SAMPLE" if len(common) < 10 else ""
        print(f"  Δ({a} − {b}) full_frac = {d:+.4f}  (paired n={len(common)}: "
              f"{a}={ma:.3f} {b}={mb:.3f})  → {factor} {verdict}{warn}")

    print()
    _delta("B", "B0", "s10 conventions")           # conventions value (eng held ON)
    _delta("B", "B_noeng", f"{eng_name} bridge")   # English value (conventions held ON)


if __name__ == "__main__":
    main()
