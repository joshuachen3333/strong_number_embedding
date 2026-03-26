#!/usr/bin/env python3
"""Survey5: cross-lingual SN transfer benchmark (KJV ↔ UNV).

主任務 (default): KJV plain + KJV+SN + UNV plain → UNV+SN
  Scored against FHL UNV+SN ground truth.

輔助任務 (--reverse): UNV plain + UNV+SN + KJV plain → KJV+SN
  Scored against FHL KJV+SN ground truth.

Usage:
    # Main task: Gen 1:1
    python3 run_survey5.py --book 創 --chap 1 --sec 1 --model sonnet

    # Main task: full chapter
    python3 run_survey5.py --book 創 --chap 1 --model sonnet

    # Reverse task: UNV+SN → KJV+SN
    python3 run_survey5.py --book 創 --chap 1 --model sonnet --reverse

    # Only matched verses (KJV SN count = UNV SN count)
    python3 run_survey5.py --book 創 --chap 1 --model sonnet --match-only

    # Ollama
    python3 run_survey5.py --book 創 --chap 1 \\
        --model deepseek-v3.1:671b-cloud --ollama-url http://sai.fhl.net:11434

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
DEFAULT_REVERSE_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey5_reverse_v0.1.md")


def load_prompt(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def model_short_name(model):
    """Convert full model name to short filename-safe identifier."""
    m = model.lower()
    if "671b" in m or "v3.1" in m:
        return "ds671b"
    if "deepseek-r1:70b" in m:
        return "dsr1_70b"
    if "deepseek-r1:32b" in m:
        return "dsr1_32b"
    if "qwen3:32b" in m:
        return "qwen32b"
    if "opus" in m:
        return "opus"
    if "sonnet" in m:
        return "sonnet"
    if "haiku" in m:
        return "haiku"
    if "gemini" in m:
        return re.sub(r'[^a-z0-9]', '', m)[:12]
    return re.sub(r'[^a-z0-9]', '', m)[:12]


def prompt_version(prompt_path):
    """Extract version string from prompt filename, e.g. survey5_v0.2.md → v0.2"""
    m = re.search(r'(v\d+\.\d+)', os.path.basename(prompt_path))
    return m.group(1) if m else "vunk"


def make_out_path(task, book_eng, chap_str, model, pversion, ext):
    """Generate filename: {task}_{scope}_{model}_{prompt}_{YYYYMMDD_HHMMSS}.{ext}"""
    scope = f"{book_eng.lower()}{chap_str.replace('-', '_')}"
    mshort = model_short_name(model)
    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{task}_{scope}_{mshort}_{pversion}_{ts}.{ext}"
    return os.path.join(SCRIPT_DIR, "run_logs", fname)


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


def build_main_prompt(system_prompt, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec):
    """主任務: KJV plain + KJV+SN + UNV plain → UNV+SN."""
    user = f"""Here is {book_eng} {chap}:{sec} in KJV (plain, no tags):

{kjv_plain}

Here is the same verse in KJV with Strong's Number annotations:

{kjv_sn}

Here is the same verse in UNV (和合本), plain, no annotations:

{unv_plain}

Using the KJV annotation pair above as your reference, insert the Strong's Number tags into the correct positions in the UNV text. Output only the annotated UNV text."""
    return system_prompt, user


def build_reverse_prompt(system_prompt, unv_plain, unv_sn, kjv_plain, book_eng, chap, sec):
    """輔助任務: UNV plain + UNV+SN + KJV plain → KJV+SN."""
    user = f"""Here is {book_eng} {chap}:{sec} in UNV (和合本), plain, no tags:

{unv_plain}

Here is the same verse in UNV with Strong's Number annotations:

{unv_sn}

Here is the same verse in KJV (King James Version), plain, no annotations:

{kjv_plain}

Using the UNV annotation pair above as your reference, insert the Strong's Number tags into the correct positions in the KJV text. Output only the annotated KJV text."""
    return system_prompt, user


def print_summary(results, book_eng, model, t0, task_label):
    scored = [r for r in results if "score" in r]
    if not scored:
        return
    print(f"\n{'='*60}")
    print(f"  Survey5 {task_label} — {book_eng}, {model}")
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


def main():
    parser = argparse.ArgumentParser(
        description="Survey5: KJV↔UNV cross-lingual SN benchmark")
    parser.add_argument("--book", default="創")
    parser.add_argument("--chap", default="1")
    parser.add_argument("--sec", type=int, default=None,
                        help="Single verse (default: all in chapter)")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--prompt", default=None,
                        help="Override system prompt file")
    parser.add_argument("--reverse", action="store_true",
                        help="輔助任務: UNV plain + UNV+SN + KJV plain → KJV+SN")
    parser.add_argument("--match-only", action="store_true",
                        help="Only run verses where KJV SN count = UNV SN count")
    parser.add_argument("--max-diff", type=int, default=None,
                        help="Max SN count diff to include (e.g., 2)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", nargs="?", const="", default=None,
                        help="Save results JSON. No value = auto-generate filename.")
    args = parser.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    brand = detect_brand(args.model, args.ollama_url)

    # Load prompt
    if args.prompt:
        prompt_file = args.prompt
    elif args.reverse:
        prompt_file = DEFAULT_REVERSE_PROMPT_FILE
    else:
        prompt_file = DEFAULT_PROMPT_FILE

    if os.path.exists(prompt_file):
        system_prompt = load_prompt(prompt_file)
    else:
        system_prompt = "Transfer Strong's Number tags from UNV to KJV." if args.reverse \
            else "Transfer Strong's Number tags from KJV to UNV."
        prompt_file = None

    pver = prompt_version(prompt_file) if prompt_file else "vunk"

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

    task_label = "輔助任務 UNV→KJV" if args.reverse else "主任務 KJV→UNV"
    print(f"Survey5: {task_label}")
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
            kjv_plain = strip_sn(kjv_sn)
            unv_sn = unv_data[sec]
            unv_plain = strip_sn(unv_sn)

            kjv_count = len(extract_tags(kjv_sn))
            unv_count = len(extract_tags(unv_sn))
            diff = abs(kjv_count - unv_count)

            if args.match_only and diff != 0:
                continue
            if args.max_diff is not None and diff > args.max_diff:
                continue

            ref = f"{book_eng} {chap}:{sec}"

            if args.reverse:
                ground_truth = kjv_sn
                sys_p, user_p = build_reverse_prompt(
                    system_prompt, unv_plain, unv_sn, kjv_plain, book_eng, chap, sec)
                src_count, tgt_count = unv_count, kjv_count
                src_label, tgt_label = "UNV", "KJV"
            else:
                ground_truth = unv_sn
                sys_p, user_p = build_main_prompt(
                    system_prompt, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec)
                src_count, tgt_count = kjv_count, unv_count
                src_label, tgt_label = "KJV", "UNV"

            if args.dry_run:
                print(f"{'─'*60}")
                print(f"{ref}  {src_label}={src_count} {tgt_label}={tgt_count} diff={diff}")
                if args.reverse:
                    print(f"  UNV:    {unv_plain[:100]}...")
                    print(f"  UNV+SN: {unv_sn[:100]}...")
                    print(f"  KJV:    {kjv_plain[:100]}...")
                else:
                    print(f"  KJV:    {kjv_plain[:100]}...")
                    print(f"  KJV+SN: {kjv_sn[:100]}...")
                    print(f"  UNV:    {unv_plain[:100]}...")
                continue

            t_call = time.time()
            try:
                output = call_model(args.model, brand, args.ollama_url,
                                    sys_p, user_p)
                dt = time.time() - t_call
                dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

                if dt < 5 and (not output or len(output.strip()) < 10):
                    print(f"  {ref:15s} ⚠ RATE LIMITED ({dt_str})")
                    continue

                score = score_verse(output, ground_truth)

                print(f"  {ref:15s} cov={score['coverage']:.2f} "
                      f"place={score['placement']:.2f} "
                      f"fmt={score['format']:.2f} "
                      f"exact={score['exact_match']}  "
                      f"{src_label}={src_count} {tgt_label}={tgt_count} diff={diff}  "
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

    print_summary(results, book_eng, args.model, t0, task_label)

    # Save
    if args.out is not None:
        task_short = "rev" if args.reverse else "fwd"
        if args.out == "":
            # auto-generate filename
            out_path = make_out_path(task_short, book_eng, args.chap,
                                     args.model, pver, "json")
        else:
            out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out

        scored = [r for r in results if "score" in r]
        out_data = {
            "meta": {
                "task": "survey5_unv_to_kjv" if args.reverse else "survey5_kjv_to_unv",
                "book": book_eng,
                "model": args.model,
                "brand": brand,
                "prompt_version": pver,
                "reverse": args.reverse,
                "match_only": args.match_only,
                "max_diff": args.max_diff,
                "total_scored": len(scored),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "verses": results,
        }
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=1)
        print(f"\n  Saved to {out_path}")


if __name__ == "__main__":
    main()
