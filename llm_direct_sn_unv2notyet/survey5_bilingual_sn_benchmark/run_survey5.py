#!/usr/bin/env python3
"""Survey5: KJV+SN → UNV+SN cross-lingual benchmark.

Given KJV+SN (English with tags) and plain UNV (Chinese without tags),
model transfers SN tags to UNV. Scored against FHL's UNV+SN ground truth.

Usage:
    # Quick proof-of-concept: Gen 1:1
    python3 run_survey5.py --book 創 --chap 1 --sec 1 --model sonnet

    # Run a chapter
    python3 run_survey5.py --book 約 --chap 1 --model sonnet

    # Only matched verses (KJV SN count = UNV SN count)
    python3 run_survey5.py --book 約 --chap 1 --model sonnet --match-only

    # Ollama
    python3 run_survey5.py --book 約 --chap 1 \
        --model qwen3:32b --ollama-url http://sai.fhl.net:11434

    # Dry run
    python3 run_survey5.py --book 創 --chap 1 --sec 1 --dry-run
"""

import argparse
import json
import os
import re
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG

# Reuse from survey4
S4_DIR = os.path.join(PARENT_DIR, "survey4_self_supervised_prompt_tuning")
sys.path.insert(0, S4_DIR)
from auto_score import strip_sn, score_verse
from analyze_test_dimensions import extract_tags
from run_benchmark import (call_ollama, call_claude_cli, call_gemini_cli,
                           parse_ref)

DEFAULT_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey5_v0.1.md")


def load_prompt(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def detect_brand(model, ollama_url):
    if model in ("haiku", "sonnet", "opus") or "claude" in model:
        return "claude"
    if "gemini" in model or "flash" in model:
        return "gemini"
    if ollama_url:
        return "ollama"
    return "claude"


def call_model(model, brand, ollama_url, sys_p, user_p):
    if brand == "ollama":
        return call_ollama(model, sys_p, user_p, ollama_url)
    elif brand == "claude":
        return call_claude_cli(model, sys_p, user_p)
    elif brand == "gemini":
        return call_gemini_cli(model, sys_p, user_p)
    return ""


def build_survey5_prompt(system_prompt, kjv_sn, unv_plain, book_eng, chap, sec):
    """Build prompt for KJV→UNV transfer."""
    user = f"""Here is the KJV text with Strong's Number annotations for {book_eng} {chap}:{sec}:

{kjv_sn}

Here is the corresponding UNV (和合本) text without annotations:

{unv_plain}

Please insert the Strong's Number tags from the KJV into the correct positions in the UNV text. Output only the annotated UNV text."""

    return system_prompt, user


def main():
    parser = argparse.ArgumentParser(
        description="Survey5: KJV+SN → UNV+SN cross-lingual benchmark")
    parser.add_argument("--book", default="創")
    parser.add_argument("--chap", default="1")
    parser.add_argument("--sec", type=int, default=None,
                        help="Single verse (default: all in chapter)")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--match-only", action="store_true",
                        help="Only run verses where KJV SN count = UNV SN count")
    parser.add_argument("--max-diff", type=int, default=None,
                        help="Max SN count diff to include (e.g., 2)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    brand = detect_brand(args.model, args.ollama_url)

    # Load prompt
    if args.prompt:
        system_prompt = load_prompt(args.prompt)
    elif os.path.exists(DEFAULT_PROMPT_FILE):
        system_prompt = load_prompt(DEFAULT_PROMPT_FILE)
    else:
        system_prompt = "Transfer Strong's Number tags from KJV to UNV."

    # Parse chapters
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
    elif "-" in args.chap:
        a, b = args.chap.split("-")
        chapters = list(range(int(a), int(b) + 1))
    else:
        chapters = [int(args.chap)]

    print(f"Survey5: KJV+SN → UNV+SN")
    print(f"Book: {book_eng} ({book_chi})")
    print(f"Model: {args.model} ({brand})")
    print(f"Prompt: {len(system_prompt)} chars")
    print()

    results = []
    t0 = time.time()

    for chap in chapters:
        try:
            kjv_data = fetch_chap_cached(book_chi, chap, "kjv", strong=1)
            unv_data = fetch_chap_cached(book_chi, chap, "unv", strong=1)
        except Exception as e:
            print(f"  Fetch error {book_eng} {chap}: {e}")
            continue

        secs = sorted(set(kjv_data.keys()) & set(unv_data.keys()))
        if args.sec:
            secs = [args.sec] if args.sec in secs else []

        for sec in secs:
            kjv_sn = kjv_data[sec]
            unv_sn = unv_data[sec]  # ground truth
            unv_plain = strip_sn(unv_sn)

            # SN count filter
            kjv_count = len(extract_tags(kjv_sn))
            unv_count = len(extract_tags(unv_sn))
            diff = abs(kjv_count - unv_count)

            if args.match_only and diff != 0:
                continue
            if args.max_diff is not None and diff > args.max_diff:
                continue

            ref = f"{book_eng} {chap}:{sec}"

            if args.dry_run:
                sys_p, user_p = build_survey5_prompt(
                    system_prompt, kjv_sn, unv_plain, book_eng, chap, sec)
                print(f"{'─'*60}")
                print(f"{ref}  KJV={kjv_count} UNV={unv_count} diff={diff}")
                print(f"  KJV+SN: {kjv_sn[:100]}...")
                print(f"  UNV:    {unv_plain[:100]}...")
                continue

            # Call model
            sys_p, user_p = build_survey5_prompt(
                system_prompt, kjv_sn, unv_plain, book_eng, chap, sec)

            t_call = time.time()
            try:
                output = call_model(args.model, brand, args.ollama_url,
                                    sys_p, user_p)
                dt = time.time() - t_call
                dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

                # Rate limit check
                if dt < 5 and (not output or len(output.strip()) < 10):
                    print(f"  {ref:15s} ⚠ RATE LIMITED ({dt_str})")
                    continue

                score = score_verse(output, unv_sn)

                print(f"  {ref:15s} cov={score['coverage']:.2f} "
                      f"place={score['placement']:.2f} "
                      f"fmt={score['format']:.2f} "
                      f"exact={score['exact_match']}  "
                      f"KJV={kjv_count} UNV={unv_count} diff={diff}  "
                      f"({dt_str})")

                results.append({
                    "ref": ref,
                    "kjv_sn_count": kjv_count,
                    "unv_sn_count": unv_count,
                    "diff": diff,
                    "model_output": output,
                    "score": score,
                    "time": round(dt, 1),
                })

            except Exception as e:
                print(f"  {ref:15s} ERROR: {e}")

    if args.dry_run:
        return

    # Summary
    scored = [r for r in results if "score" in r]
    if scored:
        print(f"\n{'='*60}")
        print(f"  Survey5 Results — {book_eng}, {args.model}")
        print(f"{'='*60}")
        print(f"  Verses scored: {len(scored)}")
        avg_cov = sum(r["score"]["coverage"] for r in scored) / len(scored)
        avg_place = sum(r["score"]["placement"] for r in scored) / len(scored)
        avg_fmt = sum(r["score"]["format"] for r in scored) / len(scored)
        exact_count = sum(1 for r in scored if r["score"]["exact_match"])
        print(f"  Exact match: {exact_count}/{len(scored)} ({exact_count/len(scored)*100:.1f}%)")
        print(f"  Avg coverage:  {avg_cov:.4f}")
        print(f"  Avg placement: {avg_place:.4f}")
        print(f"  Avg format:    {avg_fmt:.4f}")
        print(f"  Time: {(time.time()-t0)/60:.1f} minutes")

    # Save
    if args.out:
        output = {
            "meta": {
                "task": "survey5_kjv_to_unv",
                "book": book_eng,
                "model": args.model,
                "brand": brand,
                "match_only": args.match_only,
                "max_diff": args.max_diff,
                "total_scored": len(scored),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "verses": results,
        }
        out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=1)
        print(f"\n  Saved to {out_path}")


if __name__ == "__main__":
    main()
