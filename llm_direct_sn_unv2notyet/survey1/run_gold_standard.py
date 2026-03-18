#!/usr/bin/env python3
"""
Gold Standard Builder — 3-Model Consensus for SN Embedding

Uses opus, gemini-3-pro-preview, and gpt-5.4 to establish the best possible
Strong's Number embedding via a 3-round consensus process.

Round 1: All 3 models produce output. Only UNANIMOUS agreement passes.
Round 2: Each model judges disagreed verses. 2/3 majority wins.
Round 3: Final arbitration with full history. 2/3 majority wins.
         Remaining → unresolved (human review).

Usage:
    python3 run_gold_standard.py                          # default: Gen 1-2
    python3 run_gold_standard.py --book 創 --chap 1-5
    python3 run_gold_standard.py --book 創 --chap 1 --sec 1-10
    python3 run_gold_standard.py --resume
    python3 run_gold_standard.py --round1-only
    python3 run_gold_standard.py --skip-round1
    python3 run_gold_standard.py --show-summary
    python3 run_gold_standard.py --show-disagreements
    python3 run_gold_standard.py --regression --trigger-verses 1:4,1:16
"""

import argparse
import json
import os
import sys
import time

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
REPO_ROOT = os.path.dirname(PARENT_DIR)

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from llm_direct_sn_unv2notyet import (
    fetch_sec_pair, fetch_chap_cached, build_user_prompt, load_system_prompt,
    verify_sn_coverage, CHI_TO_ENG,
)
from shared.data.book_data_loader import load_books

from cli_caller import call_llm, DEFAULT_MODELS
from comparator import compare_round1, summarize_disagreement
from judge import run_judge_round
from consensus import build_gold_standard, save_gold_standard, print_summary
from regression import (
    load_gold_standard, select_regression_verses, print_regression_plan,
)


def parse_range(s):
    """Parse '1-5' or '1,3,5-7' into list of ints."""
    result = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            result.extend(range(int(a), int(b) + 1))
        else:
            result.append(int(part))
    return result


def get_verse_list(book_chi, chapters, sec_range=None):
    """Get list of (chap, sec) for given chapters, fetching verse counts from API."""
    verses = []
    for chap in chapters:
        chap_data = fetch_chap_cached(book_chi, chap, "unv", strong=0)
        secs = sorted(chap_data.keys())
        if sec_range:
            secs = [s for s in secs if s in sec_range]
        for sec in secs:
            verses.append((chap, sec))
    return verses


def run_round1(verses, book_chi, models, target_version, sn_field,
               system_prompt, resume=False, verbose=False):
    """Run Round 1: each model produces SN output for each verse.

    Returns:
        round1_results: {model_name: {(chap,sec): result_dict}}
        verse_data: {(chap,sec): {"unv_sn", "lcc_original", "book"}}
    """
    round1_dir = os.path.join(SURVEY_DIR, "round1_results")
    round1_results = {m["name"]: {} for m in models}
    verse_data = {}

    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    total = len(verses) * len(models)
    done = 0
    t0 = time.time()

    for chap, sec in verses:
        # Fetch verse pair
        try:
            unv_sn, target_text = fetch_sec_pair(book_chi, chap, sec, target_version)
        except ValueError as e:
            print(f"  SKIP {chap}:{sec} — {e}", flush=True)
            continue

        verse_data[(chap, sec)] = {
            "unv_sn": unv_sn,
            "lcc_original": target_text,
            "book": book_eng,
        }

        user_prompt = build_user_prompt(
            unv_sn, target_text, target_version, book_chi, chap, sec)

        print(f"\n{'─'*50}")
        print(f"  {book_eng} {chap}:{sec}")
        print(f"  UNV: {unv_sn[:100]}...")
        print(f"  LCC: {target_text[:100]}...")

        for model_info in models:
            model_name = model_info["name"]
            brand = model_info["brand"]
            model_id = model_info["model"]

            # Check cache
            result_file = os.path.join(
                round1_dir, model_name, str(chap), f"{sec}.json")

            if resume and os.path.isfile(result_file):
                with open(result_file, "r", encoding="utf-8") as f:
                    round1_results[model_name][(chap, sec)] = json.load(f)
                done += 1
                print(f"  [{model_name}] cached", flush=True)
                continue

            print(f"  [{model_name}] calling...", end=" ", flush=True)

            result = call_llm(
                brand=brand, model=model_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                target_version=target_version,
                verbose=verbose,
            )

            # Add metadata
            result["_model"] = model_name
            result["_brand"] = brand

            # Verify SN coverage
            output_sn = result.get(sn_field, "")
            if output_sn and not result.get("error"):
                coverage = verify_sn_coverage(unv_sn, output_sn)
                result["_sn_coverage"] = coverage
                status = "OK" if coverage["perfect"] else f"MISMATCH (missing={coverage['missing']})"
            else:
                status = "ERROR" if result.get("error") else "empty"

            print(f"conf={result.get('confidence', '?')} {status}", flush=True)

            round1_results[model_name][(chap, sec)] = result

            # Save to disk
            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            done += 1
            elapsed = time.time() - t0
            rate = elapsed / 60 / max(done, 1)
            remaining = (total - done) * rate
            print(f"  [{done}/{total}] {elapsed/60:.1f}m elapsed, "
                  f"~{remaining:.1f}m remaining", flush=True)

    return round1_results, verse_data


def main():
    parser = argparse.ArgumentParser(
        description="Gold Standard Builder — 3-Model Consensus")
    parser.add_argument("--book", default="創",
                        help="Chinese book abbreviation (default: 創)")
    parser.add_argument("--chap", default="1-2",
                        help="Chapter range: '1-2' or '1,3,5' (default: 1-2)")
    parser.add_argument("--sec", default=None,
                        help="Verse range: '1-10' or '1,3,5-7' (optional)")
    parser.add_argument("--target-version", default="lcc",
                        help="Target Bible version (default: lcc)")
    parser.add_argument("--prompt-version", default="v1.0",
                        help="Prompt version label (default: v1.0)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already-completed verses")
    parser.add_argument("--round1-only", action="store_true",
                        help="Run Round 1 only (no judging)")
    parser.add_argument("--skip-round1", action="store_true",
                        help="Skip Round 1, start from comparison")
    parser.add_argument("--show-summary", action="store_true",
                        help="Show gold standard summary and exit")
    parser.add_argument("--show-disagreements", action="store_true",
                        help="Show disagreement details and exit")
    parser.add_argument("--regression", action="store_true",
                        help="Run regression testing")
    parser.add_argument("--trigger-verses", default=None,
                        help="Verses that triggered prompt change: '1:4,1:16'")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi)
    if not book_eng:
        print(f"Unknown book: {book_chi}", file=sys.stderr)
        sys.exit(1)

    target_version = args.target_version
    sn_field = f"{target_version}_sn"

    # Show summary
    if args.show_summary:
        gold = load_gold_standard()
        unresolved = [(k[0], k[1]) for k, v in gold.items()
                      if v.get("resolved_at") == "unresolved"]
        print_summary(gold, unresolved)
        return

    # Show disagreements
    if args.show_disagreements:
        gold = load_gold_standard()
        for verse_key, g in sorted(gold.items()):
            if g.get("resolved_at") != "round1":
                print(f"\n  {g['chap']}:{g['sec']} — resolved at {g['resolved_at']}")
                if g.get("round1"):
                    for model, info in g["round1"].items():
                        print(f"    [{model}] opinion={info.get('opinion')} "
                              f"conf={info.get('confidence')}")
                        print(f"      {info.get('lcc_sn', '')[:120]}")
                if g.get("round2"):
                    print("    Round 2 judgments:")
                    for judge, info in g["round2"].items():
                        print(f"      [{judge}] best={info.get('best')} "
                              f"opinion={info.get('opinion')}")
                        if info.get("reasoning"):
                            print(f"        {info['reasoning'][:150]}")
        return

    # Regression testing
    if args.regression:
        gold = load_gold_standard()
        trigger = []
        if args.trigger_verses:
            for v in args.trigger_verses.split(","):
                c, s = v.split(":")
                trigger.append((int(c), int(s)))
        selected = select_regression_verses(gold, trigger)
        print_regression_plan(selected, gold, trigger)
        # TODO: actually run regression (reuse run_round1 + judge on selected)
        print("\n  Regression execution not yet implemented — plan only.")
        return

    # Parse chapters and verses
    chapters = parse_range(args.chap)
    sec_range = set(parse_range(args.sec)) if args.sec else None

    print(f"\n{'='*60}")
    print(f"  Gold Standard: {book_eng} chapters {args.chap}")
    print(f"  Target: {target_version.upper()}")
    print(f"  Models: {', '.join(m['name'] for m in DEFAULT_MODELS)}")
    print(f"  Prompt version: {args.prompt_version}")
    print(f"{'='*60}")

    # Get verse list
    verses = get_verse_list(book_chi, chapters, sec_range)
    print(f"\n  {len(verses)} verses to process")

    # Load system prompt
    system_prompt = load_system_prompt(target_version)

    # Round 1
    if not args.skip_round1:
        print(f"\n{'='*60}")
        print(f"  ROUND 1 — Production Run")
        print(f"{'='*60}")

        round1_results, verse_data = run_round1(
            verses, book_chi, DEFAULT_MODELS, target_version, sn_field,
            system_prompt, resume=args.resume, verbose=args.verbose)
    else:
        # Load from disk
        print(f"\n  Loading Round 1 results from disk...")
        round1_results = {m["name"]: {} for m in DEFAULT_MODELS}
        verse_data = {}
        round1_dir = os.path.join(SURVEY_DIR, "round1_results")

        for model_info in DEFAULT_MODELS:
            model_name = model_info["name"]
            for chap, sec in verses:
                result_file = os.path.join(
                    round1_dir, model_name, str(chap), f"{sec}.json")
                if os.path.isfile(result_file):
                    with open(result_file, "r", encoding="utf-8") as f:
                        round1_results[model_name][(chap, sec)] = json.load(f)

                # Fetch verse data
                if (chap, sec) not in verse_data:
                    try:
                        unv_sn, target_text = fetch_sec_pair(
                            book_chi, chap, sec, target_version)
                        verse_data[(chap, sec)] = {
                            "unv_sn": unv_sn,
                            "lcc_original": target_text,
                            "book": CHI_TO_ENG.get(book_chi, book_chi),
                        }
                    except ValueError:
                        pass

    if args.round1_only:
        print(f"\n  Round 1 complete. Use --skip-round1 to continue with judging.")
        return

    # Compare
    print(f"\n{'='*60}")
    print(f"  COMPARISON — Strict Unanimous Check")
    print(f"{'='*60}")

    unanimous, disagreed = compare_round1(round1_results, sn_field)
    print(f"\n  Unanimous: {len(unanimous)}")
    print(f"  Disagreed: {len(disagreed)}")

    if args.verbose or len(disagreed) <= 20:
        for v in disagreed:
            print(summarize_disagreement(v, round1_results, sn_field))

    # Round 2
    round2_judgments = {}
    if disagreed:
        print(f"\n{'='*60}")
        print(f"  ROUND 2 — Judge Reviews ({len(disagreed)} verses)")
        print(f"{'='*60}")

        round2_judgments = run_judge_round(
            round_num=2,
            disagreed_verses=disagreed,
            round1_results=round1_results,
            verse_data=verse_data,
            models=DEFAULT_MODELS,
            target_version=target_version,
            sn_field=sn_field,
            verbose=args.verbose,
        )

    # Check which verses are still unresolved after Round 2
    from judge import tally_judgments
    still_disagreed = []
    for verse_key in disagreed:
        r2 = round2_judgments.get(verse_key, {})
        if r2:
            winner, _ = tally_judgments(r2, round1_results, sn_field)
            if winner is None:
                still_disagreed.append(verse_key)
        else:
            still_disagreed.append(verse_key)

    # Round 3
    round3_judgments = {}
    if still_disagreed:
        print(f"\n{'='*60}")
        print(f"  ROUND 3 — Final Arbitration ({len(still_disagreed)} verses)")
        print(f"{'='*60}")

        round3_judgments = run_judge_round(
            round_num=3,
            disagreed_verses=still_disagreed,
            round1_results=round1_results,
            verse_data=verse_data,
            models=DEFAULT_MODELS,
            round2_judgments=round2_judgments,
            target_version=target_version,
            sn_field=sn_field,
            verbose=args.verbose,
        )

    # Build gold standard
    print(f"\n{'='*60}")
    print(f"  BUILDING GOLD STANDARD")
    print(f"{'='*60}")

    gold_standard, unresolved = build_gold_standard(
        unanimous=unanimous,
        disagreed=disagreed,
        round1_results=round1_results,
        round2_judgments=round2_judgments,
        round3_judgments=round3_judgments if round3_judgments else None,
        verse_data=verse_data,
        prompt_version=args.prompt_version,
        sn_field=sn_field,
    )

    save_gold_standard(gold_standard)
    print_summary(gold_standard, unresolved)

    # Verify SN coverage on gold standard
    print(f"\n  Verifying SN coverage on gold standard...")
    bad_coverage = 0
    for verse_key, gold in gold_standard.items():
        if gold["resolved_at"] == "unresolved":
            continue
        coverage = verify_sn_coverage(gold["unv_sn_reference"], gold["lcc_sn"])
        if not coverage["perfect"]:
            bad_coverage += 1
            print(f"  WARNING: {gold['chap']}:{gold['sec']} — "
                  f"missing={coverage['missing']} extra={coverage['extra']}")

    if bad_coverage == 0:
        print(f"  All resolved verses have perfect SN coverage.")
    else:
        print(f"  {bad_coverage} verses with imperfect SN coverage.")


if __name__ == "__main__":
    main()
