#!/usr/bin/env python3
"""Scan KJV+SN vs UNV+SN tag count mismatches per verse.

Classifies each verse into: matched (same count), close (diff ≤ 2),
or mismatched (diff > 2). Outputs stats and detailed JSON.

Usage:
    python3 scan_sn_mismatch.py --book 創 --chap 1
    python3 scan_sn_mismatch.py --book 創 --chap 1-50
    python3 scan_sn_mismatch.py --book 創 --chap all --summary
    python3 scan_sn_mismatch.py --book 創 --chap all --out gen_mismatch.json
"""

import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG

# Reuse tag extraction
sys.path.insert(0, os.path.join(PARENT_DIR, "survey4_self_supervised_prompt_tuning"))
from analyze_test_dimensions import extract_tags


def count_sn_tags(text):
    """Count SN tags in a verse. Returns (total, core, morph, implicit)."""
    tags = extract_tags(text)
    total = len(tags)
    morph = sum(1 for t in tags if t["is_morph"])
    implicit = sum(1 for t in tags if t["braced"])
    core = total - morph - implicit
    return total, core, morph, implicit


def parse_range(s):
    result = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            result.extend(range(int(a), int(b) + 1))
        else:
            result.append(int(part))
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Scan KJV vs UNV SN tag count mismatches")
    parser.add_argument("--book", default="創",
                        help="Chinese book abbreviation")
    parser.add_argument("--chap", default="1",
                        help="Chapter: single, range, or 'all'")
    parser.add_argument("--summary", action="store_true",
                        help="Show summary only")
    parser.add_argument("--out", default=None,
                        help="Output JSON file")
    args = parser.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)

    if args.chap.lower() == "all":
        chapters = []
        for c in range(1, 151):
            try:
                d = fetch_chap_cached(book_chi, c, "unv", strong=1)
                if d:
                    chapters.append(c)
                else:
                    break
            except:
                break
    else:
        chapters = parse_range(args.chap)

    # Stats
    matched = []    # diff == 0
    close = []      # diff 1-2
    mismatched = [] # diff > 2
    errors = []
    total_verses = 0

    for chap in chapters:
        try:
            unv_data = fetch_chap_cached(book_chi, chap, "unv", strong=1)
            kjv_data = fetch_chap_cached(book_chi, chap, "kjv", strong=1)
        except Exception as e:
            errors.append(f"{book_eng} {chap}: fetch error {e}")
            continue

        secs = sorted(set(unv_data.keys()) & set(kjv_data.keys()))

        for sec in secs:
            total_verses += 1
            unv_text = unv_data[sec]
            kjv_text = kjv_data[sec]

            u_total, u_core, u_morph, u_impl = count_sn_tags(unv_text)
            k_total, k_core, k_morph, k_impl = count_sn_tags(kjv_text)

            diff = abs(u_total - k_total)
            ref = f"{book_eng} {chap}:{sec}"

            record = {
                "ref": ref,
                "chap": chap,
                "sec": sec,
                "unv_total": u_total,
                "kjv_total": k_total,
                "diff": diff,
                "unv_detail": {"core": u_core, "morph": u_morph, "implicit": u_impl},
                "kjv_detail": {"core": k_core, "morph": k_morph, "implicit": k_impl},
            }

            if diff == 0:
                matched.append(record)
            elif diff <= 2:
                close.append(record)
            else:
                mismatched.append(record)

            if not args.summary:
                tag = "=" if diff == 0 else ("~" if diff <= 2 else "✗")
                print(f"  {ref:15s} UNV={u_total:3d} KJV={k_total:3d} "
                      f"diff={diff:2d} {tag}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  {book_eng} — KJV vs UNV SN Count Comparison ({total_verses} verses)")
    print(f"{'='*60}")
    print(f"  Matched (diff=0):   {len(matched):5d} ({len(matched)/total_verses*100:5.1f}%)")
    print(f"  Close (diff 1-2):   {len(close):5d} ({len(close)/total_verses*100:5.1f}%)")
    print(f"  Mismatched (diff>2):{len(mismatched):5d} ({len(mismatched)/total_verses*100:5.1f}%)")

    if mismatched and not args.summary:
        print(f"\n  Worst mismatches:")
        worst = sorted(mismatched, key=lambda r: -r["diff"])[:10]
        for r in worst:
            print(f"    {r['ref']:15s} UNV={r['unv_total']} KJV={r['kjv_total']} "
                  f"diff={r['diff']}")

    # Breakdown by diff
    from collections import Counter
    diff_dist = Counter()
    for r in matched:
        diff_dist[0] += 1
    for r in close:
        diff_dist[r["diff"]] += 1
    for r in mismatched:
        diff_dist[r["diff"]] += 1

    print(f"\n  Diff distribution:")
    for d in sorted(diff_dist.keys()):
        bar = "█" * (diff_dist[d] * 40 // total_verses) if total_verses else ""
        print(f"    diff={d:2d}: {diff_dist[d]:5d} ({diff_dist[d]/total_verses*100:5.1f}%) {bar}")

    if errors:
        print(f"\n  Errors: {errors}")

    # Save
    if args.out:
        output = {
            "meta": {
                "book": book_eng,
                "book_chi": book_chi,
                "total_verses": total_verses,
                "matched": len(matched),
                "close": len(close),
                "mismatched": len(mismatched),
            },
            "matched": matched,
            "close": close,
            "mismatched": mismatched,
        }
        out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=1)
        print(f"\n  Saved to {out_path}")


if __name__ == "__main__":
    main()
