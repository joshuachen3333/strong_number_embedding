#!/usr/bin/env python3
"""Run S5 benchmark on the 52-verse iteration set (from survey4 dims).

Usage:
    python3 run_iteration_set.py --model sonnet
    python3 run_iteration_set.py --model deepseek-v3.1:671b-cloud --ollama-url http://sai.fhl.net:11434
    python3 run_iteration_set.py --prompt prompts/survey5_v0.3.md --model deepseek-v3.1:671b-cloud --ollama-url http://sai.fhl.net:11434 --out
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

S4_DIR = os.path.join(PARENT_DIR, "survey4_self_supervised_prompt_tuning")
sys.path.insert(0, S4_DIR)
from auto_score import strip_sn, score_verse
from analyze_test_dimensions import extract_tags
from run_benchmark import call_ollama, call_claude_cli, call_gemini_cli

DEFAULT_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey5_v0.2.md")
DEFAULT_ITER_SET = os.path.join(SCRIPT_DIR, "iteration_set_52.json")


def load_prompt(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def prompt_version(path):
    m = re.search(r'(v\d+\.\d+)', os.path.basename(path))
    return m.group(1) if m else "vunk"


def model_short_name(model):
    return re.sub(r'[:/\\]', '-', model)


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


def clean_output(text):
    """Strip backticks and trailing explanation from model output."""
    # Remove backticks (DeepSeek sometimes wraps tags in `)
    text = text.replace("`", "")
    # Strip trailing explanation (stop at first blank line after content)
    lines = text.strip().split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if result and (stripped == "" or re.match(r'^[A-Z][a-z]', stripped)
                       or stripped.startswith("---") or stripped.startswith("**")
                       or stripped.startswith("Note") or stripped.startswith("##")):
            break
        result.append(line)
    return "\n".join(result).strip()


def build_prompt(system_prompt, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec):
    user = f"""Here is {book_eng} {chap}:{sec} in KJV (plain, no tags):

{kjv_plain}

Here is the same verse in KJV with Strong's Number annotations:

{kjv_sn}

Here is the same verse in UNV (和合本), plain, no annotations:

{unv_plain}

Using the KJV annotation pair above as your reference, insert the Strong's Number tags into the correct positions in the UNV text. Output only the annotated UNV text."""
    return system_prompt, user


def main():
    parser = argparse.ArgumentParser(
        description="Run S5 on the 52-verse iteration set")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--iter-set", default=DEFAULT_ITER_SET)
    parser.add_argument("--out", nargs="?", const="", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    brand = detect_brand(args.model, args.ollama_url)
    prompt_file = args.prompt if args.prompt else DEFAULT_PROMPT_FILE
    if os.path.exists(prompt_file):
        system_prompt = load_prompt(prompt_file)
    else:
        system_prompt = "Transfer Strong's Number tags from KJV to UNV."
        prompt_file = None
    pver = prompt_version(prompt_file) if prompt_file else "vunk"

    with open(args.iter_set, encoding="utf-8") as f:
        iter_data = json.load(f)
    verses = iter_data["verses"]

    print(f"S5 Iteration Set Benchmark")
    print(f"Model: {args.model} ({brand})")
    print(f"Prompt: {pver} ({len(system_prompt)} chars)")
    print(f"Verses: {len(verses)}")
    print()

    results = []
    t0 = time.time()

    # Cache fetched chapters: (book_chi, chap) → {sec: text}
    _kjv_cache = {}
    _unv_cache = {}

    for v in verses:
        book_chi = v["book_chi"]
        book_eng = v["book"]
        chap = v["chap"]
        sec = v["sec"]
        ref = v["ref"]
        dim = v["dim"]

        # Fetch chapter data (cached)
        kkey = (book_chi, chap)
        if kkey not in _kjv_cache:
            try:
                _kjv_cache[kkey] = fetch_chap_cached(book_chi, chap, "kjv", strong=1)
                _unv_cache[kkey] = fetch_chap_cached(book_chi, chap, "unv", strong=1)
            except Exception as e:
                print(f"  {ref:15s} FETCH ERROR: {e}")
                continue

        kjv_data = _kjv_cache[kkey]
        unv_data = _unv_cache[kkey]

        if sec not in kjv_data or sec not in unv_data:
            print(f"  {ref:15s} MISSING in KJV/UNV data")
            continue

        kjv_sn = kjv_data[sec]
        kjv_plain = strip_sn(kjv_sn)
        unv_sn = unv_data[sec]
        unv_plain = strip_sn(unv_sn)

        kjv_count = len(extract_tags(kjv_sn))
        unv_count = len(extract_tags(unv_sn))
        diff = abs(kjv_count - unv_count)

        if args.dry_run:
            print(f"  Dim {dim:>2} {ref:15s} KJV={kjv_count} UNV={unv_count} diff={diff}")
            continue

        sys_p, user_p = build_prompt(
            system_prompt, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec)

        t_call = time.time()
        try:
            raw_output = call_model(args.model, brand, args.ollama_url, sys_p, user_p)
            output = clean_output(raw_output) if raw_output else ""
            dt = time.time() - t_call
            dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

            if dt < 5 and (not output or len(output.strip()) < 10):
                print(f"  {ref:15s} ⚠ RATE LIMITED ({dt_str})")
                continue

            score = score_verse(output, unv_sn)

            print(f"  Dim {dim:>2} {ref:15s} cov={score['coverage']:.2f} "
                  f"place={score['placement']:.2f} "
                  f"fmt={score['format']:.2f} "
                  f"exact={score['exact_match']}  "
                  f"KJV={kjv_count} UNV={unv_count} diff={diff}  "
                  f"({dt_str})")

            results.append({
                "ref": ref,
                "dim": dim,
                "dim_label": v["label"],
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
        print(f"  S5 Iteration Set — {args.model}, {pver}")
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

        # Per-dim summary
        from collections import defaultdict
        dim_scores = defaultdict(list)
        for r in scored:
            dim_scores[r["dim"]].append(r["score"])
        print(f"\n  Per-dim averages:")
        for dim in sorted(dim_scores):
            ss = dim_scores[dim]
            dc = sum(s["coverage"] for s in ss) / len(ss)
            dp = sum(s["placement"] for s in ss) / len(ss)
            print(f"    Dim {dim:>2}: cov={dc:.2f} place={dp:.2f}  (n={len(ss)})")

    # Save
    if args.out is not None:
        mshort = model_short_name(args.model)
        ts = time.strftime("%Y%m%d_%H%M%S")
        if args.out == "":
            fname = f"iter52_{mshort}_{pver}_{ts}.json"
            out_path = os.path.join(SCRIPT_DIR, "run_logs", fname)
        else:
            out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        out_data = {
            "meta": {
                "task": "s5_iteration_set",
                "model": args.model,
                "brand": brand,
                "prompt_version": pver,
                "iter_set": os.path.basename(args.iter_set),
                "total_scored": len(scored),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "verses": results,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=1)
        print(f"\n  Saved to {out_path}")


if __name__ == "__main__":
    main()
