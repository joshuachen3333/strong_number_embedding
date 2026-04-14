#!/usr/bin/env python3
"""Round-robin tournament within each dim's exemplar candidates.

Each candidate takes turns being the example (v1) while others are
tested (v2). Produces dual rankings: best example + hardest test.

Usage:
    # Run dim #1 only (quick test)
    python3 round_robin.py --dim 1 --model qwen3:32b \
        --ollama-url http://<ollama-host>:11434

    # Run all dims
    python3 round_robin.py --model qwen3:32b \
        --ollama-url http://<ollama-host>:11434

    # Limit opponents per round (faster)
    python3 round_robin.py --dim 1 --max-opponents 5

    # Use Claude
    python3 round_robin.py --dim 1 --model sonnet

    # Dry run
    python3 round_robin.py --dim 1 --dry-run
"""

import argparse
import json
import os
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG
from auto_score import strip_sn, score_verse
from run_benchmark import (call_ollama, call_claude_cli, call_gemini_cli,
                           build_task_prompt, parse_ref)

DEFAULT_LIBRARY = os.path.join(SCRIPT_DIR, "exemplar_library.json")
DEFAULT_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey4_v0.1.md")


def load_prompt(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def call_model(model, brand, ollama_url, system_prompt, user_prompt):
    """Call model, return raw output text."""
    if brand == "ollama":
        return call_ollama(model, system_prompt, user_prompt, ollama_url)
    elif brand == "claude":
        return call_claude_cli(model, system_prompt, user_prompt)
    elif brand == "gemini":
        return call_gemini_cli(model, system_prompt, user_prompt)
    return ""


def run_dim_tournament(dim, candidates, system_prompt, model, brand,
                       ollama_url, max_opponents=None, dry_run=False):
    """Run round-robin for one dim's candidates.

    Returns dict with example_scores and test_scores.
    """
    n = len(candidates)
    if n < 2:
        print(f"    Dim #{dim}: only {n} candidate(s), skipping tournament")
        return None

    # Fetch all verse texts
    verse_texts = {}  # ref → (annotated, plain)
    for v in candidates:
        book_chi, chap, sec = parse_ref(v["ref"])
        text = fetch_chap_cached(book_chi, chap, "unv", strong=1)[sec]
        verse_texts[v["ref"]] = (text, strip_sn(text))

    # example_scores[ref] = list of scores when this ref is the example
    # test_scores[ref] = list of scores when this ref is the test
    example_scores = {v["ref"]: [] for v in candidates}
    test_scores = {v["ref"]: [] for v in candidates}
    skipped_pairs = []  # (example_ref, opp_ref) pairs skipped due to rate limit

    total_rounds = n
    t0 = time.time()
    call_count = 0
    consecutive_rl = 0  # rate-limit streak counter

    for i, example_v in enumerate(candidates):
        ex_ref = example_v["ref"]
        ex_annotated, ex_plain = verse_texts[ex_ref]

        # Opponents = all other candidates
        opponents = [v for v in candidates if v["ref"] != ex_ref]
        if max_opponents and len(opponents) > max_opponents:
            import random
            random.seed(42 + i)
            opponents = random.sample(opponents, max_opponents)

        elapsed = (time.time() - t0) / 60
        print(f"    Round {i+1}/{total_rounds}: {ex_ref} as example "
              f"→ {len(opponents)} opponents [{elapsed:.1f}m]")

        for opp_v in opponents:
            opp_ref = opp_v["ref"]
            opp_annotated, opp_plain = verse_texts[opp_ref]

            sys_p, user_p = build_task_prompt(
                system_prompt, ex_annotated, ex_plain, opp_plain)

            if dry_run:
                continue

            try:
                t_call = time.time()
                output = call_model(model, brand, ollama_url, sys_p, user_p)
                dt = time.time() - t_call
                dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

                # Rate-limit detection: <5s response + empty/useless output
                if dt < 5 and (not output or len(output.strip()) < 10):
                    consecutive_rl += 1
                    skipped_pairs.append((ex_ref, opp_ref))
                    print(f"      ⚠ SKIPPED (rate limited {dt_str}) "
                          f"{ex_ref} → {opp_ref}  streak={consecutive_rl}")
                    if consecutive_rl >= 3:
                        wait = min(60 * consecutive_rl, 600)
                        print(f"      ⏸ Pausing {wait}s before continuing...")
                        time.sleep(wait)
                    continue  # skip to next opponent

                consecutive_rl = 0  # reset on normal response

                score = score_verse(output, opp_annotated)
                example_scores[ex_ref].append(score["coverage"])
                test_scores[opp_ref].append(score["coverage"])
                call_count += 1

                print(f"      {ex_ref:15s} → {opp_ref:15s}  "
                      f"cov={score['coverage']:.2f} place={score['placement']:.2f} "
                      f"fmt={score['format']:.2f} exact={score['exact_match']}  "
                      f"({dt_str})")

            except Exception as e:
                print(f"      ERROR: {ex_ref}→{opp_ref}: {e}")

    if dry_run:
        return None

    # Retry skipped pairs
    if skipped_pairs:
        print(f"\n    ── Retrying {len(skipped_pairs)} skipped pairs ──")
        retry_ok = 0
        retry_fail = 0
        for ex_ref, opp_ref in skipped_pairs:
            ex_annotated, ex_plain = verse_texts[ex_ref]
            opp_annotated, opp_plain = verse_texts[opp_ref]
            sys_p, user_p = build_task_prompt(
                system_prompt, ex_annotated, ex_plain, opp_plain)
            try:
                t_call = time.time()
                output = call_model(model, brand, ollama_url, sys_p, user_p)
                dt = time.time() - t_call
                dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

                if dt < 5 and (not output or len(output.strip()) < 10):
                    print(f"      ⚠ STILL LIMITED {ex_ref} → {opp_ref} ({dt_str})")
                    retry_fail += 1
                    # Pause longer on continued rate limit
                    time.sleep(min(180, 60 * (retry_fail + 2)))
                    continue

                score = score_verse(output, opp_annotated)
                example_scores[ex_ref].append(score["coverage"])
                test_scores[opp_ref].append(score["coverage"])
                call_count += 1
                retry_ok += 1

                print(f"      {ex_ref:15s} → {opp_ref:15s}  "
                      f"cov={score['coverage']:.2f} place={score['placement']:.2f} "
                      f"fmt={score['format']:.2f} exact={score['exact_match']}  "
                      f"({dt_str}) [RETRY OK]")

            except Exception as e:
                print(f"      ERROR retry: {ex_ref}→{opp_ref}: {e}")
                retry_fail += 1

        print(f"    Retry results: {retry_ok} OK, {retry_fail} still failed")
        skipped_pairs = [(ex, opp) for ex, opp in skipped_pairs
                         if not any(s == opp for s in test_scores[opp]
                                   if test_scores[opp])]

    # Compute averages (only from real scores, skipped pairs excluded)
    def avg(lst):
        return sum(lst) / len(lst) if lst else 0.0

    example_ranking = sorted(
        [(ref, avg(scores), len(scores))
         for ref, scores in example_scores.items() if scores],
        key=lambda x: -x[1])

    test_ranking = sorted(
        [(ref, avg(scores), len(scores))
         for ref, scores in test_scores.items() if scores],
        key=lambda x: x[1])  # hardest first (lowest score)

    # Count still-skipped
    final_skipped = [p for p in skipped_pairs
                     if not example_scores[p[0]] or not test_scores[p[1]]]

    return {
        "dim": dim,
        "candidates": n,
        "total_calls": call_count,
        "skipped_count": len(skipped_pairs),
        "time_minutes": round((time.time() - t0) / 60, 1),
        "example_ranking": [
            {"ref": ref, "avg_cov": round(score, 4), "rounds": count}
            for ref, score, count in example_ranking
        ],
        "test_ranking": [
            {"ref": ref, "avg_cov": round(score, 4), "rounds": count}
            for ref, score, count in test_ranking
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Round-robin tournament for Exemplar Library candidates")
    parser.add_argument("--dim", type=int, default=None,
                        help="Run only this dim (default: all)")
    parser.add_argument("--model", default="qwen3:32b")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--brand", choices=["ollama", "claude", "gemini"])
    parser.add_argument("--prompt", default=DEFAULT_PROMPT_FILE)
    parser.add_argument("--library", default=DEFAULT_LIBRARY)
    parser.add_argument("--max-opponents", type=int, default=None,
                        help="Limit opponents per round (default: all)")
    parser.add_argument("--till", default=None,
                        help="Stop before this time (e.g., 7:50)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    # Load
    with open(args.library, encoding="utf-8") as f:
        lib = json.load(f)
    system_prompt = load_prompt(args.prompt)

    # Detect brand
    brand = args.brand
    if not brand:
        if args.ollama_url:
            brand = "ollama"
        elif args.model in ("haiku", "sonnet", "opus"):
            brand = "claude"
        elif "gemini" in args.model:
            brand = "gemini"
        else:
            brand = "ollama"

    # Parse deadline
    deadline = None
    if args.till:
        import datetime
        hm = args.till.split(":")
        now = datetime.datetime.now()
        deadline = now.replace(hour=int(hm[0]), minute=int(hm[1]), second=0)
        if deadline <= now:
            deadline += datetime.timedelta(days=1)
        print(f"Deadline: {deadline.strftime('%H:%M')}")

    # Select dims to run
    dims = [args.dim] if args.dim else sorted(int(d) for d in lib["library"].keys())

    print(f"Model: {args.model} ({brand})")
    print(f"Prompt: {args.prompt} ({len(system_prompt)} chars)")
    print(f"Dims to run: {dims}")
    print()

    results = {}
    t_global = time.time()

    for dim in dims:
        if deadline:
            import datetime
            if datetime.datetime.now() >= deadline:
                print(f"\n⏰ Deadline reached. Stopping.")
                break

        dim_key = str(dim)
        if dim_key not in lib["library"]:
            continue

        dim_info = lib["library"][dim_key]
        candidates = dim_info["verses"]
        print(f"  Dim #{dim} — {dim_info['label']} ({len(candidates)} candidates)")

        result = run_dim_tournament(
            dim, candidates, system_prompt, args.model, brand,
            args.ollama_url, args.max_opponents, args.dry_run)

        if result:
            results[dim_key] = result

            # Print top 3 example + hardest 3
            print(f"    Best examples:")
            for r in result["example_ranking"][:3]:
                print(f"      {r['ref']:15s} avg_cov={r['avg_cov']:.3f}")
            print(f"    Hardest tests:")
            for r in result["test_ranking"][:3]:
                print(f"      {r['ref']:15s} avg_cov={r['avg_cov']:.3f}")
            print()

    # Save
    if args.out and results:
        output = {
            "meta": {
                "model": args.model,
                "brand": brand,
                "prompt": os.path.basename(args.prompt),
                "max_opponents": args.max_opponents,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_time_minutes": round((time.time() - t_global) / 60, 1),
            },
            "results": results,
        }
        out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=1)
        print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
