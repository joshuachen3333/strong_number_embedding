#!/usr/bin/env python3
"""run_stage2_harsh.py — A2 Stage-2 harsh test (Clear Bible WLC source → UNV).

The hard tail Stage 1 deliberately excluded: can the model place the **09xxx
inseparable prefixes** (ב/ל/כ/מ/ה) that KJV structurally cannot supply? The only
source that carries them explicitly is the original Hebrew — Clear Bible's WLC.

Pipeline per verse:
  1. Load WLC tokens (Alignments/data/sources/WLC.tsv), grouped by verse id.
  2. Bridge each token's number to FHL numbering:
       - inseparable prefix (pos prep/art/cj, lemma in BRIDGE) → FHL 09xxx by LEMMA
         (WLC's augmented H0871a/H1886a/… are NOT FHL's scheme — bridge by lemma).
       - standard content word Hdddd (≤ H8674) → zero-padded FHL Hdddd.
  3. Build a leak-safe source string: `hebrew<FHLnum>` per morpheme, **gloss2
     (Chinese) DROPPED** so the answer (which Chinese token) isn't handed over.
  4. Ask the model to place the numbers — INCLUDING the 09xxx prefixes — into the
     stripped UNV text.
  5. Score vs UNV+SN FHL truth: full placement (kept_set complement included) and
     the headline **09xxx recall** — of the 09xxx UNV actually tags, how many the
     model placed. Arm B (conventions) vs B0 (none), like Stage 1.

NOTE: UNV-FHL tags 09xxx SPARSELY (only where a Chinese token surfaces), while WLC
carries every Hebrew prefix. So the model must place the *subset* UNV would tag —
that selection is the genuine difficulty, and 09xxx recall measures it directly.

Usage:
  python3 run_stage2_harsh.py --book 創 --chap 1 --sec 1-3 --model opus   # smoke
  python3 run_stage2_harsh.py --book 創 --chap 1-2 --model opus --samples 3
"""

import argparse
import csv
import os
import re
import sys
import time
from collections import defaultdict, Counter

_S10 = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_S10)
for p in (_PARENT, _S10):
    if p not in sys.path:
        sys.path.insert(0, p)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG, parse_sec_arg  # noqa: E402
from cli_caller import call_llm  # noqa: E402
from conventions import build_conventions_preamble  # noqa: E402
import build_exclusion as BX  # noqa: E402
import run_a2_contest as A2  # noqa: E402  (clean_output, SYSTEM_BASE, book map)

WLC_TSV = os.path.join(_PARENT, "Alignments", "data", "sources", "WLC.tsv")

# FHL inseparable-prefix numbering, keyed by the BARE CONSONANT of the WLC lemma
# (authoritative, survey2 FHL_SN_FORMAT_REFERENCE.md §4). WLC lemmas carry niqqud
# (combining points), so we strip points first and match the consonant; WLC's own
# augmented numbers (H0871a for בְּ etc.) are a DIFFERENT scheme — bridge by lemma.
PREFIX_BRIDGE = {
    "ל": "09001", "ב": "09002", "כ": "09003",
    "מ": "09006", "מן": "09006", "ה": "09009",
    # ו (waw "and") has no standard FHL 09xxx and UNV does not tag it → skip.
}
_PREFIX_POS = {"prep", "art", "cj"}
_POINTS = re.compile(r"[֑-ׇ]")  # Hebrew accents + vowel points

# WLC book number (2-digit) for the Chinese abbrevs we run. Genesis = 01.
CHI_TO_WLC_BOOK = {"創": "01"}


def _strip_points(s):
    return _POINTS.sub("", s)


def _bridge_number(lemma, strongs, pos):
    """WLC token → FHL bare number string, or None if not a scorable SN."""
    base = _strip_points(lemma.split("_")[0])  # 'עַל_2'→'על', 'בְּ'→'ב'
    if pos in _PREFIX_POS and base in PREFIX_BRIDGE:
        return PREFIX_BRIDGE[base]
    if pos == "cj" and base == "ו":
        return None    # waw "and": no FHL 09xxx, UNV never tags it — leave untagged
    m = re.match(r"H(\d+)([a-z]?)", strongs or "")
    if not m:
        return None
    n = int(m.group(1))
    if n == 0 or n > 8674:          # 0 = unmarked; >8674 = WLC-augmented non-FHL
        if base in PREFIX_BRIDGE:   # augmented prefix form (H0871a …) → bridge
            return PREFIX_BRIDGE[base]
        return None
    return f"{n:04d}"               # zero-pad to FHL width (e.g. 430 → 0430)


def load_wlc_verse(wlc_book, chap, sec):
    """Return list of (hebrew_text, fhl_num_or_None) morphemes for one verse."""
    rows = _WLC_CACHE.get(wlc_book)
    if rows is None:
        rows = defaultdict(list)
        with open(WLC_TSV, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                i = row["id"]
                if not i.startswith("o" + wlc_book):
                    continue
                rows[(int(i[3:6]), int(i[6:9]))].append(row)
        _WLC_CACHE[wlc_book] = rows
    out = []
    for row in rows.get((chap, sec), []):
        num = _bridge_number(row["lemma"], row["strongs"], row["pos"])
        out.append((row["text"], num))
    return out


_WLC_CACHE = {}


def build_wlc_source(tokens):
    """Render the WLC source line: hebrew<num> per morpheme, gloss2 dropped."""
    parts = []
    for text, num in tokens:
        parts.append(f"{text}<{num}>" if num else text)
    return "".join(parts)


def build_harsh_prompt(wlc_source, unv_plain, book_eng, chap, sec):
    return f"""Here is {book_eng} {chap}:{sec} in the original Hebrew (WLC), each \
morpheme tagged with its FHL Strong's Number (inseparable prefixes use the 09xxx \
codes: 09001=לְ to/for, 09002=בְּ in, 09003=כְּ as, 09006=מִ from, 09009=הַ the):

{wlc_source}

Here is the same verse in UNV (Chinese Union Version), plain, no annotations:

{unv_plain}

Insert the Strong's Number tags into the correct positions in the UNV text, \
INCLUDING the 09xxx inseparable-prefix tags where the Chinese expresses them. \
Output ONLY the annotated UNV text on a single line, no commentary."""


def _nines(tagset):
    """Counter of keys whose number is a 09xxx prefix (int value >= 9000).

    build_exclusion normalises 09002 -> int 9002; real Strong's tops at 8674, so
    any normalised value >= 9000 is a 5-digit 09xxx prefix. (0922 -> 922, content
    word, correctly excluded — fixes the earlier 'H9'-prefix false positive.)
    """
    c = Counter()
    for k, n in tagset.items():
        m = re.match(r"[HG](\d+)", k[1])
        if m and int(m.group(1)) >= 9000:
            c[k] += n
    return c


def nines_recall(model_output, unv_sn):
    """09xxx recall: of UNV's 09xxx tags, how many the model placed (number-level)."""
    truth, _ = BX.tag_multiset(unv_sn)
    truth9 = _nines(truth)
    out, _ = BX.tag_multiset(model_output)
    placed = total = 0
    for k, need in truth9.items():
        total += need
        placed += min(need, out.get(k, 0))
    return placed, total


def run_arm(label, conv_on, verses, model, verbose, samples):
    preamble = build_conventions_preamble("unv") if conv_on else ""
    system = (preamble + A2.SYSTEM_BASE) if preamble else A2.SYSTEM_BASE
    rows = []
    for (book_chi, book_eng, wlc_book, chap, sec, unv_sn) in verses:
        from auto_score import strip_sn
        unv_plain = strip_sn(unv_sn)
        tokens = load_wlc_verse(wlc_book, chap, sec)
        if not tokens:
            if verbose:
                print(f"  [{label}] {chap}:{sec}  (no WLC data — skip)", flush=True)
            continue
        wlc_source = build_wlc_source(tokens)
        user = build_harsh_prompt(wlc_source, unv_plain, book_eng, chap, sec)
        t0 = time.time()
        fp, n9p, n9t = [], 0, 0
        for _ in range(samples):
            res = call_llm("claude", model, system, user, target_version="unv", verbose=False)
            out = A2.clean_output(res.get("unv_sn", "") or "")
            full = BX.score_placement(out, BX.tag_multiset(unv_sn)[0])
            p9, t9 = nines_recall(out, unv_sn)
            fp.append(full["fraction"]); n9p += p9; n9t += t9
        row = {"chap": chap, "sec": sec, "full_frac": sum(fp) / len(fp),
               "n9_placed": n9p, "n9_total": n9t}
        rows.append(row)
        if verbose:
            r9 = f"{n9p}/{n9t}" if n9t else "—"
            print(f"  [{label}] {chap}:{sec}  full={row['full_frac']:.3f}  "
                  f"09xxx_recall={r9}  {time.time()-t0:.0f}s", flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser(description="A2 Stage-2 harsh test (WLC→UNV)")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", default="1")
    ap.add_argument("--sec", default=None)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--arms", default="B,B0")
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("-v", "--verbose", action="store_true", default=True)
    args = ap.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    wlc_book = CHI_TO_WLC_BOOK.get(book_chi)
    if not wlc_book:
        sys.exit(f"No WLC book number mapped for {book_chi}; add to CHI_TO_WLC_BOOK.")

    verses = []
    for chap in BX.parse_chap_arg(args.chap):
        unv = fetch_chap_cached(book_chi, chap, "unv", strong=1)
        secs = sorted(unv)
        if args.sec:
            want = set(parse_sec_arg([args.sec]))
            secs = [s for s in secs if s in want]
        for sec in secs:
            verses.append((book_chi, book_eng, wlc_book, chap, sec, unv[sec]))

    print(f"\n{'='*60}\n  A2 Stage-2 HARSH (WLC→UNV) — {book_eng} {args.chap}"
          f"{('  v'+args.sec) if args.sec else ''}\n"
          f"  model={args.model}  verses={len(verses)}  arms={args.arms}"
          f"  samples={args.samples}\n{'='*60}")

    results = {}
    for arm in [a.strip() for a in args.arms.split(",") if a.strip()]:
        print(f"\n── Arm {arm} (conventions {'ON' if arm=='B' else 'OFF'}) ──", flush=True)
        results[arm] = run_arm(arm, arm == "B", verses, args.model, args.verbose, args.samples)

    print(f"\n{'='*60}\n  SUMMARY ({args.model}, samples={args.samples})\n{'='*60}")
    print(f"  {'arm':<6}{'full_place':>12}{'09xxx_recall':>16}")
    for arm, rows in results.items():
        if not rows:
            continue
        full = sum(r["full_frac"] for r in rows) / len(rows)
        p9 = sum(r["n9_placed"] for r in rows)
        t9 = sum(r["n9_total"] for r in rows)
        rec = f"{p9}/{t9} ({100*p9/t9:.1f}%)" if t9 else "n/a"
        print(f"  {arm:<6}{full:>12.4f}{rec:>16}")


if __name__ == "__main__":
    main()
