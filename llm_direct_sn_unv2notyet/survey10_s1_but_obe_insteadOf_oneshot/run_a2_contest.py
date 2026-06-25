#!/usr/bin/env python3
"""run_a2_contest.py — A2 Stage-1 contest harness (KJV→UNV, leak-safe).

Implements the S10_VS_S1_GOLD_EXPERIMENT A2 task: source = KJV plain + KJV+SN +
UNV plain (NEVER UNV+SN → no answer leak), target = annotate the UNV text with
Strong's Numbers, scored against the withheld UNV+SN FHL truth.

FIRST CUT — conventions isolation (Arm B vs B0), the cheapest informative number:
the SAME single-pass model annotates each verse twice —
  * Arm B  : with `conventions.md` injected (build_conventions_preamble)
  * Arm B0 : with conventions frozen empty (control)
so the placement/coverage DELTA isolates s10's headline contribution (do the
learned conventions help on the contest task?) at ~2 calls/verse, fully headless.
Full s1-consensus Arm A is a later layer on top of this same task+scorer.

Scoring per verse (both via survey4/auto_score and the Stage-1 kept_set):
  * placement / coverage — auto_score.score_verse vs full UNV+SN truth. The B−B0
    delta is fair even unrestricted (both arms hit identical truth).
  * kept_placement — build_exclusion.score_placement on the kept (KJV-supplyable)
    number set only — the fair, structural-drop-excluded view.

Usage:
  python3 run_a2_contest.py --book 創 --chap 1-2 --model opus
  python3 run_a2_contest.py --book 創 --chap 1 --sec 1-3 --model opus   # smoke
"""

import argparse
import os
import re
import sys
import time

_S10 = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_S10)
_S4 = os.path.join(_PARENT, "survey4_self_supervised_prompt_tuning")
for p in (_PARENT, _S4, _S10):
    if p not in sys.path:
        sys.path.insert(0, p)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG, parse_sec_arg  # noqa: E402
from auto_score import strip_sn, score_verse  # noqa: E402
from cli_caller import call_llm  # noqa: E402  (structured-output headless path)
from conventions import build_conventions_preamble  # noqa: E402
import build_exclusion as BX  # noqa: E402

# Leak-safe KJV→UNV prompt (survey5 main task, inlined to stay self-contained).
SYSTEM_BASE = (
    "You are a Strong's Number alignment expert. You transfer Strong's Number "
    "annotations from an annotated source verse onto a parallel target verse, "
    "placing each number immediately after the target word it belongs to. Keep "
    "the FHL tag format exactly as given in the source.")


def build_main_prompt(kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec):
    return f"""Here is {book_eng} {chap}:{sec} in KJV (plain, no tags):

{kjv_plain}

Here is the same verse in KJV with Strong's Number annotations:

{kjv_sn}

Here is the same verse in UNV (Chinese Union Version), plain, no annotations:

{unv_plain}

Using the KJV annotation pair above as your reference, insert the Strong's Number \
tags into the correct positions in the UNV text. Output ONLY the annotated UNV \
text on a single line, no commentary, no code fences."""


_TAGLINE = re.compile(r"<\s*W?[A-Za-z]*\d{2,5}")
_CJK = re.compile(r"[一-鿿]")


def call_guarded(system, user, model, retries=4):
    """call_llm but RETRY on empty/error output (e.g. token-window exhaustion),
    so a run that outlives its 5-hour quota doesn't silently score empties as 0.
    Returns the cleaned annotated text, or "" if every attempt was empty (caller
    must then DROP the verse, not score it 0)."""
    for attempt in range(retries):
        res = call_llm("claude", model, system, user, target_version="unv", verbose=False)
        out = clean_output(res.get("unv_sn", "") or "") if isinstance(res, dict) else ""
        if out and re.search(r"<\s*W?[A-Za-z]*\d", out):
            return out
        time.sleep(min(30 * (attempt + 1), 120))   # back off: quota may be resetting
    return ""


def clean_output(raw):
    """Pull the annotated UNV line out of a possibly-chatty model reply.

    Among lines that carry an FHL SN tag, pick the one with the MOST CJK
    characters — i.e. the actual annotated Chinese verse. This is robust against
    the conventions-ON model echoing the C1 example line (which also contains FHL
    tags like 創造<WH01254><WTH8799> but only a couple CJK chars); a naive
    first-tag-line heuristic would wrongly grab that echo and score ~0.
    """
    if not raw:
        return ""
    raw = re.sub(r"```[a-zA-Z]*\n?|```", "", raw.strip())
    best, best_cjk = "", -1
    for line in raw.splitlines():
        if _TAGLINE.search(line):
            n = len(_CJK.findall(line))
            if n > best_cjk:
                best, best_cjk = line.strip(), n
    if best:
        return best
    return raw.splitlines()[0].strip() if raw.splitlines() else raw


def kept_placement(model_output, unv_sn, kjv_sn):
    """build_exclusion kept-set number-coverage for one verse."""
    shared, _, _, _ = BX.verse_split(unv_sn, kjv_sn)
    return BX.score_placement(model_output, shared)


def run_arm(label, conventions_on, verses, model, verbose, samples=1):
    preamble = build_conventions_preamble("unv") if conventions_on else ""
    system = (preamble + SYSTEM_BASE) if preamble else SYSTEM_BASE
    rows = []
    for (book_chi, book_eng, chap, sec, kjv_sn, unv_sn) in verses:
        kjv_plain, unv_plain = strip_sn(kjv_sn), strip_sn(unv_sn)
        user = build_main_prompt(kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec)
        t0 = time.time()
        # N samples/verse to separate convention-effect from the model's sampling
        # noise (opus is stochastic). Per-verse metric = mean over samples.
        sk = []
        for _ in range(samples):
            out = call_guarded(system, user, model)
            if not out:
                continue   # all retries empty (quota) — DROP, don't score 0
            sc = score_verse(out, unv_sn)
            kp = kept_placement(out, unv_sn, kjv_sn)
            sk.append({"placement": sc["placement"], "coverage": sc["coverage"],
                       "exact": sc["exact_match"], "kept_frac": kp["fraction"],
                       "kept_n": kp["total"]})
        if not sk:
            if verbose:
                print(f"  [{label}] {chap}:{sec}  DROPPED (all samples empty)", flush=True)
            continue
        avg = {k: (sum(s[k] for s in sk) / len(sk)) for k in
               ("placement", "coverage", "kept_frac")}
        avg["exact"] = sum(1 for s in sk if s["exact"]) / len(sk)
        avg["chap"], avg["sec"], avg["kept_n"] = chap, sec, sk[0]["kept_n"]
        rows.append(avg)
        if verbose:
            spread = (max(s["kept_frac"] for s in sk) - min(s["kept_frac"] for s in sk)
                      ) if samples > 1 else 0.0
            print(f"  [{label}] {chap}:{sec}  kept={avg['kept_frac']:.3f}"
                  f"{f' (±{spread:.3f} over {samples})' if samples>1 else ''}  "
                  f"cov={avg['coverage']:.3f}  {time.time()-t0:.0f}s", flush=True)
    return rows


def mean(rows, key):
    return sum(r[key] for r in rows) / len(rows) if rows else 0.0


def main():
    ap = argparse.ArgumentParser(description="A2 Stage-1 contest (KJV→UNV)")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", default="1")
    ap.add_argument("--sec", default=None, help="verse range, e.g. 1-3")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--arms", default="B,B0", help="comma list of B / B0")
    ap.add_argument("--samples", type=int, default=1, help="N samples/verse/arm (mean)")
    ap.add_argument("-v", "--verbose", action="store_true", default=True)
    args = ap.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    chaps = BX.parse_chap_arg(args.chap)

    verses = []
    for chap in chaps:
        unv = fetch_chap_cached(book_chi, chap, "unv", strong=1)
        kjv = fetch_chap_cached(book_chi, chap, "kjv", strong=1)
        secs = sorted(set(unv) & set(kjv))
        if args.sec:
            want = set(parse_sec_arg([args.sec]))
            secs = [s for s in secs if s in want]
        for sec in secs:
            verses.append((book_chi, book_eng, chap, sec, kjv[sec], unv[sec]))

    print(f"\n{'='*60}\n  A2 Stage-1 contest — {book_eng} {args.chap}"
          f"{('  v'+args.sec) if args.sec else ''}\n"
          f"  model={args.model}  verses={len(verses)}  arms={args.arms}"
          f"  samples={args.samples}\n{'='*60}")

    results = {}
    for arm in [a.strip() for a in args.arms.split(",") if a.strip()]:
        conv_on = (arm == "B")
        print(f"\n── Arm {arm} (conventions {'ON' if conv_on else 'OFF'}) ──", flush=True)
        results[arm] = run_arm(arm, conv_on, verses, args.model, args.verbose, args.samples)

    print(f"\n{'='*60}\n  SUMMARY ({len(verses)} verses, {args.model})\n{'='*60}")
    print(f"  {'arm':<6}{'placement':>11}{'coverage':>11}{'kept_place':>12}{'exact':>8}")
    for arm, rows in results.items():
        exact = sum(1 for r in rows if r["exact"])
        print(f"  {arm:<6}{mean(rows,'placement'):>11.4f}{mean(rows,'coverage'):>11.4f}"
              f"{mean(rows,'kept_frac'):>12.4f}{exact:>6}/{len(rows)}")
    if "B" in results and "B0" in results:
        dp = mean(results["B"], "placement") - mean(results["B0"], "placement")
        dk = mean(results["B"], "kept_frac") - mean(results["B0"], "kept_frac")
        print(f"\n  Δ(B − B0): placement {dp:+.4f}   kept_placement {dk:+.4f}")
        print("  (positive = conventions help on the contest task)")


if __name__ == "__main__":
    main()
