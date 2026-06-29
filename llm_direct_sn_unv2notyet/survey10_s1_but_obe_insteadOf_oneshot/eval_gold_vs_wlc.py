#!/usr/bin/env python3
"""eval_gold_vs_wlc.py — validate the current gold's SN inventory against the
original Hebrew (Clear Bible WLC), an INDEPENDENT non-FHL / non-LLM truth.

Why: s1/s10 gold is resolved by LLM consensus and scored only against FHL
(UNV+SN) — a single-source circularity (consensus ≠ truth). WLC is a manual human
alignment of the original Hebrew; comparing the gold's Strong's-number multiset
against WLC catches numbers the gold carries that the source text does NOT contain
= genuine errors, at zero model cost.

COMPLETE coverage (lexical + 09xxx prefix + morph), using BOTH bridges:
  - lexical content / 0853 / 09xxx prefix → survey10 run_stage2_harsh.PREFIX_BRIDGE
  - morph 8xxx codes → survey5 morph_bridge.json (s5's WLC-morph→FHL-8xxx table,
    leave-one-out validated 100%; form_key = WLC morph[:3] for pos==verb). This
    lets us INCLUDE morph instead of dropping it.
Particle dual-numbering canonicalised (same Hebrew word, FHL vs WLC differ):
  מן: FHL 04480 (standalone) == WLC 09006 (prefix מִ);  כ: FHL 09003 == WLC 03509.

Scope: judges the SN *inventory* (which numbers), NOT placement (which Chinese
token) — WLC has no Chinese.

Per verse (number-level multiset):
  gold − WLC = numbers in gold ABSENT from the Hebrew → ERROR signal
  WLC − gold = numbers in Hebrew dropped by gold      → expected (Chinese omits
               prefixes/function words), reported not counted as gold error

Usage:  python3 eval_gold_vs_wlc.py --gold-dir gold_standard --book 創 --chap 1-2 -v
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

_S10 = os.path.dirname(os.path.abspath(__file__))
_S5 = os.path.join(os.path.dirname(_S10), "survey5_bilingual_sn_benchmark")
if _S10 not in sys.path:
    sys.path.insert(0, _S10)

import build_exclusion as BX          # noqa: E402
import run_stage2_harsh as S2         # noqa: E402

CHI_TO_WLC_BOOK = {"創": "01"}

# s5's WLC-morph → FHL-8xxx table (import the data, do not mutate s5's files).
with open(os.path.join(_S5, "morph_bridge.json"), encoding="utf-8") as _f:
    MORPH_BRIDGE = json.load(_f)        # form_key (e.g. "vqp") -> 8804

# Same Hebrew particle, different FHL-vs-WLC numbering → canonicalise both sides.
EQUIV = {"H9006": "H4480", "H3509": "H9003"}


def _canon(c):
    out = Counter()
    for (t, norm), n in c.items():
        out[(t, EQUIV.get(norm, norm))] += n
    return out


def gold_sn_multiset(lcc_sn):
    """Full SN multiset (testament,norm) from a gold lcc_sn — morph INCLUDED."""
    c = Counter()
    for letters, num, suffix in BX._TAG_RE.findall(lcc_sn or ""):
        testament, n_int, _ = BX.classify(letters, num)
        c[(testament, f"{testament}{n_int}{suffix}")] += 1
    return _canon(c)


def wlc_sn_multiset(wlc_book, chap, sec):
    """Full bridged WLC SN multiset: lexical + prefix (PREFIX_BRIDGE) + morph
    (s5 morph_bridge). Reads the raw WLC rows cached by run_stage2_harsh."""
    S2.load_wlc_verse(wlc_book, chap, sec)             # populate cache
    rows = S2._WLC_CACHE.get(wlc_book, {}).get((chap, sec), [])
    c = Counter()
    for row in rows:
        num = S2._bridge_number(row["lemma"], row["strongs"], row["pos"])
        if num:
            c[("H", f"H{int(num)}")] += 1
        if row["pos"] == "verb":
            code = MORPH_BRIDGE.get(row["morph"][:3])
            if code:
                c[("H", f"H{int(code)}")] += 1
    return _canon(c)


def family_of(key):
    n = int(re.match(r"[HG](\d+)", key[1]).group(1))
    if n >= 9000:
        return "prefix_09"
    if 8674 < n < 9000:
        return "morph"
    if n == 853:
        return "obj_marker"
    if n in BX.HEBREW_FUNCTION_WORDS:
        return "core_function"
    return "core_content"


def main():
    ap = argparse.ArgumentParser(description="Validate gold SN inventory vs WLC")
    ap.add_argument("--gold-dir", default="gold_standard")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", default="1-2")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    wlc_book = CHI_TO_WLC_BOOK[args.book]
    book_eng = "Gen"
    n_verses = 0
    gold_only_fam = Counter(); wlc_only_fam = Counter(); gold_only_keys = Counter()
    tot_gold = tot_wlc = tot_shared = 0
    error_verses = []

    for chap in BX.parse_chap_arg(args.chap):
        gdir = os.path.join(args.gold_dir, book_eng, str(chap))
        if not os.path.isdir(gdir):
            continue
        for fn in sorted(os.listdir(gdir), key=lambda x: int(x.split(".")[0])):
            sec = int(fn.split(".")[0])
            gold = json.load(open(os.path.join(gdir, fn)))
            g = gold_sn_multiset(gold.get("lcc_sn", ""))
            w = wlc_sn_multiset(wlc_book, chap, sec)
            gonly, wonly = g - w, w - g
            n_verses += 1
            tot_gold += sum(g.values()); tot_wlc += sum(w.values())
            tot_shared += sum((g & w).values())
            for k, n in gonly.items():
                fam = family_of(k); gold_only_fam[fam] += n
                gold_only_keys[f"{fam}:{k[1]}"] += n
            for k, n in wonly.items():
                wlc_only_fam[family_of(k)] += n
            cc = sum(n for k, n in gonly.items() if family_of(k) == "core_content")
            if cc:
                error_verses.append((f"{chap}:{sec}", cc))
            if args.verbose and sum(gonly.values()):
                ex = ", ".join(f"{k[1]}({family_of(k)})x{n}" for k, n in gonly.items())
                print(f"  {chap}:{sec}  gold-not-in-WLC: {ex}")

    print("\n" + "=" * 64)
    print(f"  Gold SN-inventory vs WLC (lexical+prefix+morph) — {book_eng} {args.chap}"
          f"  ({n_verses} verses)\n  gold-dir: {args.gold_dir}")
    print("=" * 64)
    print(f"  gold SNs : {tot_gold}    WLC SNs : {tot_wlc}    shared : {tot_shared}")
    print("\n  gold − WLC (in gold, NOT in Hebrew) — ERROR signal:")
    for fam in ("core_content", "core_function", "obj_marker", "morph", "prefix_09"):
        if gold_only_fam.get(fam):
            print(f"    {fam:<14}: {gold_only_fam[fam]}")
    print("\n  WLC − gold (in Hebrew, dropped by gold) — expected drops:")
    for fam in ("prefix_09", "obj_marker", "morph", "core_function", "core_content"):
        if wlc_only_fam.get(fam):
            print(f"    {fam:<14}: {wlc_only_fam[fam]}")
    cc_err = gold_only_fam.get("core_content", 0)
    print(f"\n  >>> CONTENT-WORD errors (gold has a content SN the Hebrew lacks): "
          f"{cc_err} across {len(error_verses)} verse(s)")
    if error_verses:
        print("      verses:", ", ".join(f"{v}({c})" for v, c in error_verses))
    else:
        print("      → gold content-word inventory fully consistent with the Hebrew.")
    if gold_only_keys:
        print("\n  top gold-only numbers:")
        for k, n in gold_only_keys.most_common(10):
            print(f"    {k:<20}: {n}")


if __name__ == "__main__":
    main()
