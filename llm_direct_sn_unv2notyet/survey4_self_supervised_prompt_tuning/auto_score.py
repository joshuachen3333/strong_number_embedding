#!/usr/bin/env python3
"""Auto-score model output against FHL ground truth.

Compares model-generated UNV+SN against FHL's authoritative UNV+SN
using 4 metrics: exact match, SN coverage, placement accuracy, format compliance.

Usage:
    # Score a single verse
    python3 auto_score.py --book 創 --chap 1 --sec 1 --model-output "起初<WAH09002>..."

    # Score from file (one verse per line or JSON)
    python3 auto_score.py --input model_results.json

    # Self-test: FHL vs FHL should be 100%
    python3 auto_score.py --self-test --book 創 --chap 1
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

# Reuse tag extraction from analyze_test_dimensions
sys.path.insert(0, SCRIPT_DIR)
from analyze_test_dimensions import extract_tags


def strip_sn(text):
    """Remove all SN tags from UNV+SN text, returning plain UNV."""
    # Remove {<...>} (implicit markers — entire tag disappears)
    text = re.sub(r'\{<[^>]+>\}', '', text)
    # Remove <...> (regular tags)
    text = re.sub(r'<[^>]+>', '', text)
    return text


def extract_sn_sequence(text):
    """Extract ordered list of (position, raw_tag, content) from text.

    Position = character index in the stripped (plain) text where the tag appears.
    """
    result = []
    plain_pos = 0
    i = 0
    while i < len(text):
        if text[i] == '{' and i + 1 < len(text) and text[i + 1] == '<':
            # Implicit marker {<...>}
            end = text.find('>', i)
            if end != -1 and end + 1 < len(text) and text[end + 1] == '}':
                raw = text[i:end + 2]
                content = text[i + 2:end]
                result.append((plain_pos, raw, content, True))
                i = end + 2
                continue
        if text[i] == '<':
            end = text.find('>', i)
            if end != -1:
                raw = text[i:end + 1]
                content = text[i + 1:end]
                result.append((plain_pos, raw, content, False))
                i = end + 1
                continue
        plain_pos += 1
        i += 1
    return result


def score_verse(model_output, ground_truth):
    """Score a single verse against ground truth.

    Returns dict with 4 metrics + details.
    """
    # 1. Exact match
    exact = (model_output.strip() == ground_truth.strip())

    # Extract tag sequences
    model_tags = extract_tags(model_output)
    truth_tags = extract_tags(ground_truth)

    model_raws = [t["raw"] for t in model_tags]
    truth_raws = [t["raw"] for t in truth_tags]

    model_contents = [t["content"] for t in model_tags]
    truth_contents = [t["content"] for t in truth_tags]

    # 2. SN coverage — missing + extra tags
    model_set = set(model_raws)
    truth_set = set(truth_raws)

    # Use multiset (count duplicates)
    from collections import Counter
    model_counter = Counter(model_raws)
    truth_counter = Counter(model_raws)  # intentional: compare counts
    truth_counter = Counter(truth_raws)

    missing = []  # in truth but not in model
    extra = []    # in model but not in truth

    all_tags = set(model_raws) | set(truth_raws)
    for tag in all_tags:
        mc = model_counter.get(tag, 0)
        tc = truth_counter.get(tag, 0)
        if tc > mc:
            missing.extend([tag] * (tc - mc))
        elif mc > tc:
            extra.extend([tag] * (mc - tc))

    total_truth = len(truth_raws)
    coverage = 1.0 - (len(missing) + len(extra)) / total_truth if total_truth > 0 else 1.0
    coverage = max(0.0, coverage)

    # 3. Placement accuracy — tags present in both but at different positions
    # Compare by looking at the sequence of tags relative to surrounding Chinese text
    model_seq = extract_sn_sequence(model_output)
    truth_seq = extract_sn_sequence(ground_truth)

    # Build position→tag maps
    model_pos_tags = [(pos, raw) for pos, raw, content, braced in model_seq]
    truth_pos_tags = [(pos, raw) for pos, raw, content, braced in truth_seq]

    # Count tags that exist in both but are at different character positions
    misplaced = 0
    matched_truth = set()
    for m_pos, m_raw in model_pos_tags:
        found = False
        for j, (t_pos, t_raw) in enumerate(truth_pos_tags):
            if j not in matched_truth and m_raw == t_raw:
                if m_pos == t_pos:
                    matched_truth.add(j)
                    found = True
                    break
        if not found:
            # Check if tag exists at different position
            for j, (t_pos, t_raw) in enumerate(truth_pos_tags):
                if j not in matched_truth and m_raw == t_raw:
                    matched_truth.add(j)
                    misplaced += 1
                    break

    placement = 1.0 - misplaced / total_truth if total_truth > 0 else 1.0

    # 4. Format compliance — check specific format rules
    format_issues = []

    for t in model_tags:
        num = t["number"]
        prefix = t["prefix"]
        # Check zero-padding preserved
        if prefix and prefix.endswith("H") and num and num[0].isdigit():
            # OT: should maintain original zero-padding
            pass  # Hard to check without knowing expected length

        # Check braces consistency
        if t["braced"]:
            if not t["raw"].startswith("{<") or not t["raw"].endswith(">}"):
                format_issues.append(f"Bad brace format: {t['raw']}")

    # Compare braced status between model and truth
    model_braced = set(t["content"] for t in model_tags if t["braced"])
    truth_braced = set(t["content"] for t in truth_tags if t["braced"])
    brace_mismatch = (model_braced ^ truth_braced)

    format_score = 1.0
    if total_truth > 0:
        format_issues_count = len(format_issues) + len(brace_mismatch)
        format_score = max(0.0, 1.0 - format_issues_count / total_truth)

    return {
        "exact_match": exact,
        "coverage": round(coverage, 4),
        "placement": round(placement, 4),
        "format": round(format_score, 4),
        "details": {
            "total_truth_tags": total_truth,
            "total_model_tags": len(model_raws),
            "missing": missing[:10],  # cap for readability
            "extra": extra[:10],
            "misplaced": misplaced,
            "format_issues": format_issues[:5],
            "brace_mismatches": list(brace_mismatch)[:5],
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Auto-score model UNV+SN output against FHL ground truth")
    parser.add_argument("--book", default="創",
                        help="Chinese book abbreviation")
    parser.add_argument("--chap", type=int, default=1)
    parser.add_argument("--sec", type=int, default=None,
                        help="Single verse to score")
    parser.add_argument("--model-output", default=None,
                        help="Model output string to score")
    parser.add_argument("--self-test", action="store_true",
                        help="Self-test: score FHL ground truth against itself")
    parser.add_argument("--input", default=None,
                        help="JSON file with model results")
    args = parser.parse_args()

    if args.self_test:
        # Score FHL against itself — should be 100% on all metrics
        chap_data = fetch_chap_cached(args.book, args.chap, "unv", strong=1)
        book_eng = CHI_TO_ENG.get(args.book, args.book)

        secs = [args.sec] if args.sec else sorted(chap_data.keys())
        total = {"exact": 0, "coverage": 0.0, "placement": 0.0, "format": 0.0}
        count = 0

        for sec in secs:
            gt = chap_data[sec]
            result = score_verse(gt, gt)
            total["exact"] += int(result["exact_match"])
            total["coverage"] += result["coverage"]
            total["placement"] += result["placement"]
            total["format"] += result["format"]
            count += 1

            if not result["exact_match"]:
                print(f"  FAIL: {book_eng} {args.chap}:{sec}")

        print(f"\nSelf-test: {book_eng} chap {args.chap} ({count} verses)")
        print(f"  Exact:     {total['exact']}/{count} ({total['exact']/count*100:.1f}%)")
        print(f"  Coverage:  {total['coverage']/count:.4f}")
        print(f"  Placement: {total['placement']/count:.4f}")
        print(f"  Format:    {total['format']/count:.4f}")

    elif args.model_output and args.sec:
        gt = fetch_chap_cached(args.book, args.chap, "unv", strong=1)[args.sec]
        result = score_verse(args.model_output, gt)
        book_eng = CHI_TO_ENG.get(args.book, args.book)
        print(f"{book_eng} {args.chap}:{args.sec}")
        print(f"  Exact:     {result['exact_match']}")
        print(f"  Coverage:  {result['coverage']}")
        print(f"  Placement: {result['placement']}")
        print(f"  Format:    {result['format']}")
        if result["details"]["missing"]:
            print(f"  Missing:   {result['details']['missing']}")
        if result["details"]["extra"]:
            print(f"  Extra:     {result['details']['extra']}")

    elif args.input:
        with open(args.input, encoding="utf-8") as f:
            results = json.load(f)
        # Expect: {"verses": [{"ref": "Gen 1:1", "model_output": "..."}]}
        total = {"exact": 0, "coverage": 0.0, "placement": 0.0, "format": 0.0}
        count = 0
        for v in results["verses"]:
            ref = v["ref"]
            # Parse ref to fetch ground truth
            parts = ref.split()
            book_eng = parts[0]
            chap_sec = parts[1].split(":")
            # Reverse lookup book_chi
            chi_map = {v2: k for k, v2 in CHI_TO_ENG.items()}
            book_chi = chi_map.get(book_eng, book_eng)
            chap, sec = int(chap_sec[0]), int(chap_sec[1])
            gt = fetch_chap_cached(book_chi, chap, "unv", strong=1)[sec]
            result = score_verse(v["model_output"], gt)
            total["exact"] += int(result["exact_match"])
            total["coverage"] += result["coverage"]
            total["placement"] += result["placement"]
            total["format"] += result["format"]
            count += 1

        print(f"Scored {count} verses from {args.input}")
        print(f"  Exact:     {total['exact']}/{count} ({total['exact']/count*100:.1f}%)")
        print(f"  Avg Coverage:  {total['coverage']/count:.4f}")
        print(f"  Avg Placement: {total['placement']/count:.4f}")
        print(f"  Avg Format:    {total['format']/count:.4f}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
