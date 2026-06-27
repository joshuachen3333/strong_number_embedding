#!/usr/bin/env python3
"""learn_morph_bridge.py — one-time whole-OT sweep that learns the WLC-morph -> FHL
8xxx code table by aligning FHL UNV+SN gold against WLC verbs. NO LLM is used.

Mechanism (see docs/.../2026-06-26-survey5-morph-mechanism-design.md):
  - Parse FHL UNV+SN gold into ordered (lexical_SN, morph_code) pairs (a <WTH8xxx>
    morph tag binds to the lexical tag immediately before it).
  - Load WLC verb tokens (pos==verb) with their (lexical_SN, form_key), form_key =
    stem+form prefix of the ETCBC morph string (e.g. vqp3ms -> vqp).
  - Pair by lexical SN in order; tally form_key -> {fhl_code: count}.
  - Consistency: every form_key must map to ONE code; conflicts are reported.
Emits morph_bridge.json {form_key: code} + a coverage/conflict report.

Run:  python3 learn_morph_bridge.py            # whole OT
      python3 learn_morph_bridge.py --books 1  # just Genesis (smoke)
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict, deque, Counter

from run_survey5 import fetch_chap_cached  # puts parent dir on sys.path

_HERE = os.path.dirname(os.path.abspath(__file__))
_BOOKS_JSON = os.path.abspath(os.path.join(_HERE, "..", "..", "shared", "data", "books.json"))


def load_ot_books():
    """First 39 entries of books.json (OT, canonical order matching WLC 01-39)."""
    with open(_BOOKS_JSON, encoding="utf-8") as f:
        return json.load(f)[:39]

WLC_TSV = os.path.abspath(os.path.join(_HERE, "..", "Alignments", "data", "sources", "WLC.tsv"))
_GOLD_TAG = re.compile(r"<W([A-Z]*?)H(\d{4,5})>")


def gold_pairs(txt):
    """FHL UNV+SN -> ordered [(lexical_int, morph_code), ...]."""
    pairs = []
    last_lex = None
    for m in _GOLD_TAG.finditer(txt):
        markers, num = m.group(1), int(m.group(2))
        if "T" in markers and 8600 <= num <= 8900:      # morphology tag
            if last_lex is not None:
                pairs.append((last_lex, num))
        else:
            last_lex = num                               # lexical tag
    return pairs


def load_wlc_verbs():
    """Read WLC.tsv once -> {(booknum2, chap, sec): [(lexical_int, form_key), ...]}."""
    idx = defaultdict(list)
    with open(WLC_TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["pos"] != "verb":
                continue
            i = row["id"]                                 # o BB CCC VVV
            book, chap, sec = i[1:3], int(i[3:6]), int(i[6:9])
            mm = re.match(r"H(\d+)", row["strongs"] or "")
            if not mm:
                continue
            lex = int(mm.group(1))
            form_key = row["morph"][:3]                   # v + stem + form
            idx[(book, chap, sec)].append((lex, form_key))
    return idx


def main():
    ap = argparse.ArgumentParser(description="Learn WLC-morph -> FHL code table (no LLM)")
    ap.add_argument("--books", default="1-39", help="OT book numbers, e.g. 1-39 or 1 or 1,2,5")
    ap.add_argument("--out", default="morph_bridge.json")
    args = ap.parse_args()

    # parse book selection
    want = set()
    for part in args.books.split(","):
        if "-" in part:
            a, b = part.split("-"); want.update(range(int(a), int(b) + 1))
        else:
            want.add(int(part))

    books = load_ot_books()                               # OT only, canonical order
    wlc = load_wlc_verbs()

    learned = defaultdict(Counter)                        # form_key -> {code: count}
    verbs_aligned = 0
    covered, failed = [], []

    for n in sorted(want):
        meta = books[n - 1]
        chi, nchap = meta["chi"], meta["chapters"]
        booknum = f"{n:02d}"
        got_any = False
        for chap in range(1, nchap + 1):
            try:
                unv = fetch_chap_cached(chi, chap, "unv", strong=1)
            except Exception as e:
                continue
            if not unv:
                continue
            for sec, txt in unv.items():
                gp = gold_pairs(txt)
                if not gp:
                    continue
                by_lex = defaultdict(deque)
                for lex, key in wlc.get((booknum, chap, sec), []):
                    by_lex[lex].append(key)
                for lex, code in gp:
                    if by_lex[lex]:
                        key = by_lex[lex].popleft()
                        learned[key][code] += 1
                        verbs_aligned += 1
                got_any = True
        (covered if got_any else failed).append(f"{n:02d}{chi}")
        print(f"  swept {n:02d} {chi} ({'ok' if got_any else 'NO DATA'})", flush=True)

    # freeze: majority code per form_key; report purity (majority share)
    bridge, impure = {}, []
    for key, codes in sorted(learned.items()):
        total = sum(codes.values())
        top, topn = codes.most_common(1)[0]
        bridge[key] = top
        purity = topn / total
        if len(codes) > 1:
            impure.append((purity, key, top, total, dict(codes)))

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(bridge, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"\n{'='*60}\n  MORPH BRIDGE LEARNED\n{'='*60}")
    print(f"  form_keys: {len(bridge)}   verbs aligned: {verbs_aligned}")
    print(f"  books covered: {len(covered)}   no-data: {failed or '—'}")
    print(f"  keys with a minority tail: {len(impure)} (majority-vote resolves; "
          f"low purity = check)")
    for purity, key, top, total, codes in sorted(impure):
        flag = "  <-- LOW" if purity < 0.9 else ""
        print(f"    {key} -> {top}  purity={purity:.3f} (n={total})  {codes}{flag}")
    print(f"  wrote {args.out}")


if __name__ == "__main__":
    main()
