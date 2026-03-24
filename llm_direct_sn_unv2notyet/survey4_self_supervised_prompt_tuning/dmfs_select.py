#!/usr/bin/env python3
"""Dimension-Matched Few-Shot (DMFS) exemplar selector.

For each test verse, finds the best-matching example verse based on
26-dimension profile similarity (Jaccard). Ensures the few-shot example
demonstrates exactly the SN patterns the test verse needs.

Usage:
    python3 dmfs_select.py --test-set test_set_10pct.json --out dmfs_pairs.json
    python3 dmfs_select.py --test-set test_set_10pct.json --strategy superset
    python3 dmfs_select.py --pct 10 --out dmfs_pairs.json
"""

import argparse
import json
import math
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MAP = os.path.join(SCRIPT_DIR, "dim_verse_map.json")


def jaccard(a, b):
    """Jaccard similarity between two sets."""
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    union = sa | sb
    if not union:
        return 0.0
    return len(sa & sb) / len(union)


def load_map(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def select_pairs(data, test_refs, strategy="jaccard", same_book=False):
    """For each test verse, find the best-matching example.

    Args:
        data: dim_verse_map.json contents
        test_refs: set of refs that are test verses
        strategy: "jaccard" (default), "exact", or "superset"
        same_book: prefer same-book matches as tiebreak

    Returns:
        list of pair dicts
    """
    # Build ref→dims lookup
    ref_dims = {}
    ref_book = {}
    for v in data["verses"]:
        ref_dims[v["ref"]] = set(v["dims"])
        ref_book[v["ref"]] = v["book"]

    # Candidate pool = all verses NOT in test set
    candidates = [ref for ref in ref_dims if ref not in test_refs]

    # Pre-compute candidate dim sets
    cand_dims = {ref: ref_dims[ref] for ref in candidates}

    pairs = []
    stats = {"exact": 0, "superset": 0, "jaccard_sum": 0.0}

    for i, test_ref in enumerate(sorted(test_refs)):
        t_dims = ref_dims[test_ref]
        t_book = ref_book[test_ref]

        best_ref = None
        best_score = -1.0
        best_is_exact = False
        best_is_superset = False

        for c_ref, c_dims in cand_dims.items():
            if strategy == "exact":
                if c_dims == t_dims:
                    score = 1.0
                else:
                    continue
            elif strategy == "superset":
                if c_dims >= t_dims:  # superset
                    score = jaccard(c_dims, t_dims)
                else:
                    continue
            else:  # jaccard (default)
                score = jaccard(c_dims, t_dims)

            # Tiebreak: same book gets +0.001 bonus
            if same_book and ref_book[c_ref] == t_book:
                score += 0.001

            if score > best_score:
                best_score = score
                best_ref = c_ref
                best_is_exact = (c_dims == t_dims)
                best_is_superset = (c_dims >= t_dims)

        if best_ref is None:
            # Fallback: no match found with strict strategy, use jaccard
            for c_ref, c_dims in cand_dims.items():
                score = jaccard(c_dims, t_dims)
                if score > best_score:
                    best_score = score
                    best_ref = c_ref

        e_dims = ref_dims[best_ref] if best_ref else set()
        shared = sorted(t_dims & e_dims)
        test_only = sorted(t_dims - e_dims)
        example_only = sorted(e_dims - t_dims)

        pair = {
            "test": {"ref": test_ref, "dims": sorted(t_dims)},
            "example": {
                "ref": best_ref,
                "dims": sorted(e_dims),
                "jaccard": round(best_score, 4),
                "exact": best_is_exact,
                "superset": best_is_superset,
            },
            "shared_dims": shared,
            "test_only_dims": test_only,
            "example_only_dims": example_only,
        }
        pairs.append(pair)

        if best_is_exact:
            stats["exact"] += 1
        if best_is_superset:
            stats["superset"] += 1
        stats["jaccard_sum"] += best_score

        if (i + 1) % 500 == 0:
            print(f"  ...{i+1}/{len(test_refs)} paired", file=sys.stderr)

    stats["avg_jaccard"] = stats["jaccard_sum"] / len(pairs) if pairs else 0
    return pairs, stats


def main():
    parser = argparse.ArgumentParser(
        description="DMFS: Dimension-Matched Few-Shot exemplar selector")
    parser.add_argument("--test-set", default=None,
                        help="Test set JSON from sample_test_set.py")
    parser.add_argument("--pct", type=float, default=None,
                        help="Auto-generate test set at this %% (alternative to --test-set)")
    parser.add_argument("--testament", choices=["OT", "NT"],
                        help="Filter by testament")
    parser.add_argument("--strategy", choices=["jaccard", "exact", "superset"],
                        default="jaccard",
                        help="Matching strategy (default: jaccard)")
    parser.add_argument("--same-book", action="store_true",
                        help="Prefer same-book matches as tiebreak")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for auto test set (default: 42)")
    parser.add_argument("--map", default=DEFAULT_MAP,
                        help="Path to dim_verse_map.json")
    parser.add_argument("--out", default=None,
                        help="Output JSON file")
    args = parser.parse_args()

    data = load_map(args.map)

    # Get test refs
    if args.test_set:
        with open(args.test_set, encoding="utf-8") as f:
            ts = json.load(f)
        test_refs = set(v["ref"] for v in ts["verses"])
    elif args.pct:
        # Inline sampling (reuse sample_test_set logic)
        from sample_test_set import sample_greedy
        selected, _ = sample_greedy(data, args.pct, args.testament, seed=args.seed)
        test_refs = selected
    else:
        print("Error: provide --test-set or --pct", file=sys.stderr)
        sys.exit(1)

    print(f"Test verses: {len(test_refs)}")
    print(f"Strategy: {args.strategy}"
          f"{' + same-book tiebreak' if args.same_book else ''}")
    print(f"Candidate pool: {len(data['verses']) - len(test_refs)} verses")
    print()

    pairs, stats = select_pairs(
        data, test_refs, args.strategy, args.same_book)

    # Report
    print(f"{'='*60}")
    print(f"  DMFS Pairing Results — {len(pairs)} pairs")
    print(f"{'='*60}")
    print(f"  Avg Jaccard:    {stats['avg_jaccard']:.4f}")
    print(f"  Exact matches:  {stats['exact']:4d} ({stats['exact']/len(pairs)*100:.1f}%)")
    print(f"  Supersets:      {stats['superset']:4d} ({stats['superset']/len(pairs)*100:.1f}%)")

    # Jaccard distribution
    jaccards = [p["example"]["jaccard"] for p in pairs]
    buckets = {"1.0": 0, "≥0.9": 0, "≥0.8": 0, "≥0.7": 0, "≥0.5": 0, "<0.5": 0}
    for j in jaccards:
        if j >= 1.0:
            buckets["1.0"] += 1
        elif j >= 0.9:
            buckets["≥0.9"] += 1
        elif j >= 0.8:
            buckets["≥0.8"] += 1
        elif j >= 0.7:
            buckets["≥0.7"] += 1
        elif j >= 0.5:
            buckets["≥0.5"] += 1
        else:
            buckets["<0.5"] += 1

    print(f"\n  Jaccard distribution:")
    for label, count in buckets.items():
        bar = "█" * (count * 40 // len(pairs)) if pairs else ""
        print(f"    {label:6s} {count:5d} ({count/len(pairs)*100:5.1f}%) {bar}")

    # Worst pairs
    worst = sorted(pairs, key=lambda p: p["example"]["jaccard"])[:5]
    print(f"\n  Worst 5 pairs:")
    for p in worst:
        print(f"    {p['test']['ref']:15s} ↔ {p['example']['ref']:15s} "
              f"J={p['example']['jaccard']:.3f} "
              f"test_only={p['test_only_dims']}")

    # Output
    if args.out:
        output = {
            "meta": {
                "strategy": args.strategy,
                "same_book": args.same_book,
                "test_count": len(pairs),
                "avg_jaccard": round(stats["avg_jaccard"], 4),
                "exact_matches": stats["exact"],
                "supersets": stats["superset"],
            },
            "pairs": pairs,
        }
        out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=1)
        print(f"\n  Saved to {out_path}")


if __name__ == "__main__":
    main()
