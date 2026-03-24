#!/usr/bin/env python3
"""Sample a minimal test set from dim_verse_map.json using greedy coverage.

Strategy B: pick verses that maximize multi-dim coverage so that each
dimension reaches ≥ N% coverage. Rare dims (≤ ceil threshold) are auto
selected in full.

Usage:
    python3 sample_test_set.py --pct 10
    python3 sample_test_set.py --pct 5 --seed 42
    python3 sample_test_set.py --pct 10 --testament OT
    python3 sample_test_set.py --pct 10 --out test_set_10pct.json
"""

import argparse
import json
import math
import os
import random
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MAP = os.path.join(SCRIPT_DIR, "dim_verse_map.json")


def load_map(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sample_greedy(data, pct, testament=None, rare_threshold=20, seed=None):
    """Greedy coverage sampling.

    Args:
        data: dim_verse_map.json contents
        pct: target percentage (e.g. 10 = 10%)
        testament: "OT", "NT", or None (both)
        rare_threshold: dims with ≤ this many verses are selected in full
        seed: random seed for reproducibility

    Returns:
        (selected_refs: set, report: list of dicts)
    """
    if seed is not None:
        random.seed(seed)

    # Build verse→dims lookup, filtered by testament
    verse_dims = {}  # ref → set of dims
    for v in data["verses"]:
        if testament and v["testament"] != testament:
            continue
        verse_dims[v["ref"]] = set(v["dims"])

    # Build dim→verses lookup (filtered)
    dim_verses = {}
    for d_str, info in data["by_dimension"].items():
        d = int(d_str)
        verses_in_dim = [ref for ref in info["verses"] if ref in verse_dims]
        if verses_in_dim:
            dim_verses[d] = set(verses_in_dim)

    # Calculate targets per dim
    targets = {}
    for d, vs in dim_verses.items():
        total = len(vs)
        if total <= rare_threshold:
            # Rare dim: select all
            targets[d] = total
        else:
            targets[d] = math.ceil(total * pct / 100)

    # Track coverage progress
    coverage = {d: 0 for d in dim_verses}
    selected = set()

    # Phase 1: force-select all rare dim verses
    for d, vs in dim_verses.items():
        if len(vs) <= rare_threshold:
            for ref in vs:
                if ref not in selected:
                    selected.add(ref)
                    # Update coverage for all dims this verse touches
                    for d2 in verse_dims[ref]:
                        if d2 in coverage:
                            coverage[d2] += 1

    # Phase 2: greedy selection until all dims reach target
    # Build candidate pool (exclude already selected)
    candidates = set(verse_dims.keys()) - selected

    while True:
        # Check which dims still need more
        unmet = {d: targets[d] - coverage[d]
                 for d in targets if coverage[d] < targets[d]}
        if not unmet:
            break
        if not candidates:
            break

        # Score each candidate: how many unmet-dim slots does it fill?
        best_ref = None
        best_score = -1

        # Sample a batch for efficiency (don't score all 26k every iteration)
        pool = list(candidates)
        if len(pool) > 5000:
            random.shuffle(pool)
            pool = pool[:5000]

        for ref in pool:
            score = 0
            for d in verse_dims[ref]:
                if d in unmet and unmet[d] > 0:
                    score += 1
            # Tiebreak: prefer verses with more dims (higher value)
            if score > best_score or (score == best_score and best_ref
                                      and len(verse_dims[ref]) > len(verse_dims[best_ref])):
                best_score = score
                best_ref = ref

        if best_score <= 0:
            # No candidate helps any unmet dim — shouldn't happen, but safety
            break

        selected.add(best_ref)
        candidates.discard(best_ref)
        for d in verse_dims[best_ref]:
            if d in coverage:
                coverage[d] += 1

    # Build report
    report = []
    for d in sorted(dim_verses.keys()):
        total = len(dim_verses[d])
        target = targets[d]
        actual = coverage[d]
        report.append({
            "dim": d,
            "label": data["by_dimension"][str(d)]["label"],
            "total": total,
            "target": target,
            "selected": actual,
            "pct": actual / total * 100 if total > 0 else 0,
            "met": actual >= target,
        })

    return selected, report


def main():
    parser = argparse.ArgumentParser(
        description="Sample minimal test set with greedy dim coverage")
    parser.add_argument("--pct", type=float, default=10,
                        help="Target coverage %% per dimension (default: 10)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--testament", choices=["OT", "NT"],
                        help="Filter by testament (default: both)")
    parser.add_argument("--rare-threshold", type=int, default=20,
                        help="Dims with ≤ N verses are selected in full (default: 20)")
    parser.add_argument("--map", default=DEFAULT_MAP,
                        help="Path to dim_verse_map.json")
    parser.add_argument("--out", default=None,
                        help="Output JSON file (default: print summary only)")
    args = parser.parse_args()

    data = load_map(args.map)
    total_verses = len([v for v in data["verses"]
                        if not args.testament or v["testament"] == args.testament])

    print(f"Source: {total_verses} verses"
          f"{f' ({args.testament} only)' if args.testament else ''}")
    print(f"Target: ≥{args.pct}% per dim, rare≤{args.rare_threshold} → full select")
    print(f"Seed: {args.seed}")
    print()

    selected, report = sample_greedy(
        data, args.pct, args.testament, args.rare_threshold, args.seed)

    # Print report
    print(f"{'='*75}")
    print(f"  Selected: {len(selected)} verses "
          f"({len(selected)/total_verses*100:.1f}% of {total_verses})")
    print(f"{'='*75}")

    all_met = True
    for r in report:
        mark = "✓" if r["met"] else "✗"
        rare = " [RARE→ALL]" if r["total"] <= args.rare_threshold else ""
        print(f"  #{r['dim']:2d} {r['label']:45s} "
              f"{r['selected']:4d}/{r['total']:5d} "
              f"({r['pct']:5.1f}%) target={r['target']:4d} {mark}{rare}")
        if not r["met"]:
            all_met = False

    print()
    if all_met:
        print(f"  All dimensions met target ≥{args.pct}%.")
    else:
        unmet = [r for r in report if not r["met"]]
        print(f"  WARNING: {len(unmet)} dimensions below target!")

    # Output JSON
    if args.out:
        # Enrich selected verses with their dim info
        selected_verses = [v for v in data["verses"] if v["ref"] in selected]
        output = {
            "meta": {
                "pct": args.pct,
                "seed": args.seed,
                "testament": args.testament,
                "rare_threshold": args.rare_threshold,
                "total_source": total_verses,
                "total_selected": len(selected),
                "generated": "2026-03-24",
            },
            "coverage": report,
            "verses": selected_verses,
        }
        out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=1)
        print(f"\n  Saved to {out_path}")


if __name__ == "__main__":
    main()
