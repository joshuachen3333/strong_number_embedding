#!/usr/bin/env python3
"""A2 contest — WLC + YLT source → UNV, scored vs UNV's real FHL tags.

Source config = **WLC + YLT** (Joshua 2026-07-11, survey11 open decision; replaces the
structurally-crippled KJV of the original run_a2_contest). WLC gives the complete
Hebrew SN inventory incl. 09xxx inseparable prefixes; YLT (Young's Literal) glues
literal English to Hebrew word order so the model can map each Hebrew<SN> morpheme to
meaning without a Chinese crutch. The target UNV carries the REAL FHL tags — the answer
key, never shown — so scoring escapes consensus circularity (no answer leak).

Arms (isolate s10's headline contribution — the conventions):
  B  : conventions.md injected  (build_conventions_preamble)  — s10 ON
  B0 : conventions frozen empty (control)                     — s10 OFF
The placement/coverage DELTA (B − B0) is s10's measured value on this KJV-free source.
Full s1-consensus Arm A layers on top of the SAME task+scorer (documented; a later run).

Scoring reuses the validated Stage-2 harsh objective metrics:
  full_frac   = BX.score_placement  (kept number-level set coverage vs FHL truth)
  09xxx_recall= nines_recall        (inseparable-prefix placement — WLC's edge over KJV)
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
from ylt_bridge import load_wlc_verse_with_ids, build_wlc_ylt_source, ylt_verse_text
from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG, parse_sec_arg

# Arm definitions: (conventions_on, ylt_on). Deltas isolate each factor —
#   Δ(B − B0)      = s10 conventions' value  (YLT held ON)
#   Δ(B − B_noylt) = YLT's value             (conventions held ON)
ARMS = {
    "B":       (True,  True),    # WLC+YLT, conventions ON   (headline s10 arm)
    "B0":      (False, True),    # WLC+YLT, conventions OFF  (conventions control)
    "B_noylt": (True,  False),   # WLC-only, conventions ON  (YLT control — s5 lesson)
}


def build_wlc_ylt_prompt(source_block, unv_plain, book_eng, chap, sec):
    return f"""Here is {book_eng} {chap}:{sec}.

{source_block}

Here is the same verse in UNV (Chinese Union Version), plain, no annotations:

{unv_plain}

Insert the Strong's Number tags into the correct positions in the UNV text, \
INCLUDING the 09xxx inseparable-prefix tags where the Chinese expresses them. Use the \
WLC Hebrew for the authoritative tag set and the YLT English to disambiguate which \
Chinese word each tag belongs to. Output ONLY the annotated UNV text on a single \
line, no commentary, no code fences."""


def run_arm(label, conv_on, ylt_on, verses, model, verbose, samples):
    preamble = build_conventions_preamble("unv") if conv_on else ""
    system = (preamble + A2.SYSTEM_BASE) if preamble else A2.SYSTEM_BASE
    rows = []
    for (book_chi, book_eng, wlc_book, chap, sec, unv_sn) in verses:
        unv_plain = strip_sn(unv_sn)
        toks = load_wlc_verse_with_ids(wlc_book, chap, sec)
        if not toks:
            if verbose:
                print(f"  [{label}] {chap}:{sec}  (no WLC — skip)", flush=True)
            continue
        if ylt_on:
            source_block = build_wlc_ylt_source(toks, wlc_book, chap, sec)
            user = build_wlc_ylt_prompt(source_block, unv_plain, book_eng, chap, sec)
        else:
            # WLC-only control (no YLT gloss/sentence) — the s5 "WLC-only" comparison.
            wlc_line = build_wlc_source([(t, n) for _mid, t, n in toks])
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
        row = {"chap": chap, "sec": sec, "full_frac": sum(fp) / len(fp),
               "n9_placed": n9p, "n9_total": n9t,
               "ylt_used": ylt_on,                       # this ARM's source, not data avail
               "ylt_available": bool(ylt_verse_text(wlc_book, chap, sec))}
        rows.append(row)
        if verbose:
            r9 = f"{n9p}/{n9t}" if n9t else "—"
            print(f"  [{label}] {chap}:{sec}  full={row['full_frac']:.3f}  "
                  f"09xxx={r9}  {'+ylt' if ylt_on else 'WLConly'}  "
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
    ap = argparse.ArgumentParser(description="A2 contest — WLC+YLT source → UNV")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", default="1")
    ap.add_argument("--sec", default=None, help="verse range, e.g. 1-5")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--arms", default="B,B0,B_noylt",
                    help="comma list of B / B0 / B_noylt")
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("-v", "--verbose", action="store_true", default=True)
    args = ap.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    wlc_book = CHI_TO_WLC_BOOK.get(book_chi)
    if not wlc_book:
        sys.exit(f"No WLC book number for {book_chi}; add to CHI_TO_WLC_BOOK.")

    verses = []
    for chap in BX.parse_chap_arg(args.chap):
        unv = fetch_chap_cached(book_chi, chap, "unv", strong=1)
        secs = sorted(unv)
        if args.sec:
            want = set(parse_sec_arg([args.sec]))
            secs = [s for s in secs if s in want]
        for sec in secs:
            verses.append((book_chi, book_eng, wlc_book, chap, sec, unv[sec]))

    print(f"\n{'='*60}\n  A2 CONTEST (WLC+YLT → UNV) — {book_eng} {args.chap}  "
          f"model={args.model}  verses={len(verses)}  arms={args.arms}  "
          f"samples={args.samples}\n{'='*60}")

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    results = {}
    for arm in arms:
        conv_on, ylt_on = ARMS.get(arm, (arm == "B", True))
        print(f"\n  ── Arm {arm} (conventions {'ON' if conv_on else 'OFF'}, "
              f"source {'WLC+YLT' if ylt_on else 'WLC-only'}) ──")
        results[arm] = run_arm(arm, conv_on, ylt_on, verses, args.model,
                               args.verbose, args.samples)

    print(f"\n{'='*60}\n  RESULTS\n{'='*60}")
    for arm in arms:
        rows = results[arm]
        r9, p9, t9 = _nines_recall_agg(rows)
        r9s = f"{r9:.3f} ({p9}/{t9})" if r9 is not None else "—"
        print(f"  Arm {arm:8s}: n={len(rows)}  full_frac={mean(rows,'full_frac'):.3f}  "
              f"09xxx_recall={r9s}")

    def _delta(a, b, factor):
        # PAIRED delta: compare only verses BOTH arms scored (quota drops leave arms
        # with different verse subsets; mean-of-different-sets would bias the result).
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
    _delta("B", "B0", "s10 conventions")        # conventions value (YLT held ON)
    _delta("B", "B_noylt", "YLT")               # YLT value (conventions held ON) — s5 check


if __name__ == "__main__":
    main()
