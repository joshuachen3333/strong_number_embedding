#!/usr/bin/env python3
"""Compare multiple models on the survey4 SN annotation benchmark.

Runs the same test pairs through each model and prints a ranked comparison.
All models share the same pairs so results are directly comparable.

Pair sources (pick one):
  --dim N          → sample from exemplar library dim N
  --pct N          → sample N% from dim_verse_map.json (DMFS)
  --pairs FILE     → pre-built pairs JSON

Usage:
    # Quick: 5 pairs from dim #1, compare ollama models on sai
    python3 compare_models.py --dim 1 --verse-pair-count 5 \
        --models qwen3:8b qwen3:32b deepseek-v3.1:671b-cloud \
        --ollama-url http://localhost:11434

    # Auto-discover all ollama models on server
    python3 compare_models.py --dim 1 --verse-pair-count 5 \
        --auto-discover --ollama-url http://localhost:11434

    # 1% DMFS test set
    python3 compare_models.py --pct 1 --verse-pair-count 20 \
        --models qwen3:8b qwen3:32b \
        --ollama-url http://localhost:11434

    # Mix ollama + claude
    python3 compare_models.py --dim 1 --verse-pair-count 5 \
        --models qwen3:32b sonnet haiku \
        --ollama-url http://sai.fhl.net:11434

    # Pre-built pairs
    python3 compare_models.py --pairs dmfs_pairs.json --verse-pair-count 10 \
        --models qwen3:8b qwen3:32b \
        --ollama-url http://localhost:11434
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG
from auto_score import strip_sn, score_verse
from run_benchmark import (
    call_ollama, call_claude_cli, call_gemini_cli,
    build_task_prompt, parse_ref, DEFAULT_PROMPT, load_prompt,
)

DEFAULT_LIBRARY = os.path.join(SCRIPT_DIR, "exemplar_library.json")
DEFAULT_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey4_v0.1.md")

CLAUDE_MODELS = {"haiku", "sonnet", "opus"}


def detect_brand(model, ollama_url):
    if model in CLAUDE_MODELS or "claude" in model:
        return "claude"
    if "gemini" in model or "flash" in model:
        return "gemini"
    if ollama_url:
        return "ollama"
    return "claude"


def discover_ollama_models(ollama_url):
    """Fetch available models from ollama server."""
    try:
        resp = urllib.request.urlopen(f"{ollama_url}/api/tags", timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        models = [m["name"] for m in data.get("models", [])]
        # Filter out translation-specific models
        models = [m for m in models if "translategemma" not in m]
        return models
    except Exception as e:
        print(f"  Failed to discover models: {e}")
        return []


def call_model(model, brand, ollama_url, sys_p, user_p):
    if brand == "ollama":
        return call_ollama(model, sys_p, user_p, ollama_url)
    elif brand == "claude":
        return call_claude_cli(model, sys_p, user_p)
    elif brand == "gemini":
        return call_gemini_cli(model, sys_p, user_p)
    return ""


def build_verse_cache(pairs):
    """Pre-fetch all verse texts needed. Shared across all models."""
    refs = set()
    for p in pairs:
        refs.add(p["test"]["ref"] if isinstance(p["test"], dict) else p["test_ref"])
        refs.add(p["example"]["ref"] if isinstance(p["example"], dict) else p["ex_ref"])

    print(f"  Pre-fetching {len(refs)} verses...")
    cache = {}
    for ref in sorted(refs):
        book_chi, chap, sec = parse_ref(ref)
        annotated = fetch_chap_cached(book_chi, chap, "unv", strong=1)[sec]
        cache[ref] = (annotated, strip_sn(annotated))
    return cache


def build_pairs_from_dim(dim, library_path, n_pairs, seed):
    """Build pairs from exemplar library for a specific dim."""
    with open(library_path, encoding="utf-8") as f:
        lib = json.load(f)

    dim_key = str(dim)
    if dim_key not in lib["library"]:
        print(f"Dim #{dim} not in library")
        sys.exit(1)

    candidates = lib["library"][dim_key]["verses"]
    if len(candidates) < 2:
        print(f"Dim #{dim} has < 2 candidates")
        sys.exit(1)

    random.seed(seed)
    indices = list(range(len(candidates)))
    random.shuffle(indices)

    pairs = []
    for i in range(min(n_pairs, len(candidates) - 1)):
        ex = candidates[indices[i]]
        test = candidates[indices[(i + 1) % len(candidates)]]
        pairs.append({
            "test": {"ref": test["ref"], "dims": test["dims"]},
            "example": {"ref": ex["ref"], "dims": ex["dims"]},
        })

    label = lib["library"][dim_key]["label"]
    return pairs, f"Dim #{dim}: {label}"


def run_one_model(model, brand, ollama_url, pairs, verse_cache,
                  system_prompt, error_budget):
    """Run all pairs for one model. Returns result dict or None."""
    scores = []
    errors = 0
    rate_limited = 0
    t0 = time.time()

    print(f"\n  {'─'*60}")
    print(f"  Model: {model} ({brand})")
    print(f"  {'─'*60}")

    for i, pair in enumerate(pairs):
        test_ref = pair["test"]["ref"] if isinstance(pair["test"], dict) else pair["test_ref"]
        ex_ref = pair["example"]["ref"] if isinstance(pair["example"], dict) else pair["ex_ref"]

        ex_annotated, ex_plain = verse_cache[ex_ref]
        test_annotated, test_plain = verse_cache[test_ref]

        sys_p, user_p = build_task_prompt(
            system_prompt, ex_annotated, ex_plain, test_plain)

        t_call = time.time()
        try:
            output = call_model(model, brand, ollama_url, sys_p, user_p)
            dt = time.time() - t_call
            dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

            # Rate-limit detection
            if dt < 5 and (not output or len(output.strip()) < 10):
                rate_limited += 1
                print(f"    [{i+1:3d}/{len(pairs)}] {test_ref:<15} "
                      f"⚠ RATE LIMITED ({dt_str})")
                if rate_limited >= 3:
                    wait = min(60 * rate_limited, 600)
                    print(f"    ⏸ Pausing {wait}s...")
                    time.sleep(wait)
                continue

            rate_limited = 0  # reset on success
            score = score_verse(output, test_annotated)
            scores.append(score)

            print(f"    [{i+1:3d}/{len(pairs)}] {test_ref:<15} "
                  f"cov={score['coverage']:.2f} "
                  f"place={score['placement']:.2f} "
                  f"fmt={score['format']:.2f} "
                  f"exact={str(score['exact_match']):<5}  ({dt_str})")

        except Exception as e:
            errors += 1
            print(f"    [{i+1:3d}/{len(pairs)}] {test_ref:<15} ERROR: {e}")
            if errors >= error_budget:
                print(f"  !! Error budget ({error_budget}) exhausted — skipping {model}")
                return None

    if not scores:
        print(f"  !! No valid scores for {model}")
        return None

    total_time = time.time() - t0
    result = {
        "model": model,
        "brand": brand,
        "n": len(scores),
        "errors": errors,
        "rate_limited": rate_limited,
        "exact": sum(1 for s in scores if s["exact_match"]) / len(scores),
        "coverage": sum(s["coverage"] for s in scores) / len(scores),
        "placement": sum(s["placement"] for s in scores) / len(scores),
        "format": sum(s["format"] for s in scores) / len(scores),
        "time_minutes": round(total_time / 60, 1),
        "sec_per_verse": round(total_time / len(scores), 1),
    }

    print(f"  → exact={result['exact']*100:.1f}%  "
          f"cov={result['coverage']:.3f}  "
          f"place={result['placement']:.3f}  "
          f"fmt={result['format']:.3f}  "
          f"[{result['time_minutes']}m, {result['sec_per_verse']}s/v]")
    return result


def print_comparison_table(results, source_label, n_pairs):
    """Print ranked comparison table."""
    if not results:
        return

    ranked = sorted(results, key=lambda r: (-r["coverage"], -r["exact"]))

    print(f"\n{'='*80}")
    print(f"  MODEL COMPARISON — {source_label} ({n_pairs} pairs)")
    print(f"{'='*80}")
    print(f"  {'Model':<30} {'Brand':<8} {'Exact':>6} {'Cov':>6} "
          f"{'Place':>6} {'Fmt':>6} {'s/v':>5} {'n':>4} {'Err':>4}")
    print(f"  {'─'*30} {'─'*8} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*5} {'─'*4} {'─'*4}")

    for r in ranked:
        print(f"  {r['model']:<30} {r['brand']:<8} "
              f"{r['exact']*100:5.1f}% "
              f"{r['coverage']:6.3f} "
              f"{r['placement']:6.3f} "
              f"{r['format']:6.3f} "
              f"{r['sec_per_verse']:5.1f} "
              f"{r['n']:4d} "
              f"{r['errors']:4d}")

    print(f"{'='*80}")
    best = ranked[0]
    print(f"  Winner: {best['model']}  "
          f"(cov={best['coverage']:.3f}, exact={best['exact']*100:.1f}%)")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Compare multiple models on the survey4 SN annotation benchmark")
    # Models
    parser.add_argument("--models", nargs="+", default=None,
                        help="Models to compare")
    parser.add_argument("--auto-discover", action="store_true",
                        help="Auto-discover ollama models on server")
    parser.add_argument("--ollama-url", default=None,
                        help="Ollama server URL")
    # Pair source (pick one)
    parser.add_argument("--dim", type=int, default=None,
                        help="Sample pairs from exemplar library dim N")
    parser.add_argument("--pct", type=float, default=None,
                        help="Sample N%% DMFS pairs from dim_verse_map.json")
    parser.add_argument("--pairs", default=None,
                        help="Pre-built pairs JSON file")
    # Limits
    parser.add_argument("--verse-pair-count", type=int, default=None,
                        help="Max pairs to use")
    parser.add_argument("--seed", type=int, default=42)
    # Prompt
    parser.add_argument("--prompt", default=None,
                        help="Custom prompt file")
    # Behaviour
    parser.add_argument("--error-budget", type=int, default=5,
                        help="Max errors before skipping a model (default: 5)")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    # Get models
    models = args.models or []
    if args.auto_discover and args.ollama_url:
        discovered = discover_ollama_models(args.ollama_url)
        print(f"  Discovered: {discovered}")
        models = list(dict.fromkeys(models + discovered))  # preserve order, dedup

    if not models:
        print("Error: provide --models or --auto-discover with --ollama-url")
        sys.exit(1)

    # Build pairs
    if args.dim is not None:
        limit = args.verse_pair_count or 10
        pairs, source_label = build_pairs_from_dim(
            args.dim, DEFAULT_LIBRARY, limit, args.seed)
    elif args.pct:
        from sample_test_set import sample_greedy, load_map
        from dmfs_select import select_pairs
        data = load_map(os.path.join(SCRIPT_DIR, "dim_verse_map.json"))
        selected, _ = sample_greedy(data, args.pct, seed=args.seed)
        pairs, _ = select_pairs(data, selected)
        source_label = f"DMFS {args.pct}%"
    elif args.pairs:
        with open(args.pairs, encoding="utf-8") as f:
            pairs = json.load(f)["pairs"]
        source_label = os.path.basename(args.pairs)
    else:
        print("Error: provide --dim, --pct, or --pairs")
        sys.exit(1)

    if args.verse_pair_count and len(pairs) > args.verse_pair_count:
        pairs = pairs[:args.verse_pair_count]

    # Load prompt
    if args.prompt:
        system_prompt = load_prompt(args.prompt)
        prompt_name = os.path.basename(args.prompt)
    elif os.path.exists(DEFAULT_PROMPT_FILE):
        system_prompt = load_prompt(DEFAULT_PROMPT_FILE)
        prompt_name = os.path.basename(DEFAULT_PROMPT_FILE)
    else:
        system_prompt = DEFAULT_PROMPT
        prompt_name = "built-in"

    print(f"Models:  {models}")
    print(f"Source:  {source_label}")
    print(f"Pairs:   {len(pairs)}")
    print(f"Prompt:  {prompt_name} ({len(system_prompt)} chars)")
    print(f"Calls:   {len(models)} models × {len(pairs)} pairs = "
          f"{len(models) * len(pairs)}")

    # Pre-fetch verses once
    verse_cache = build_verse_cache(pairs)

    # Run each model
    all_results = []
    t_global = time.time()

    for model in models:
        brand = detect_brand(model, args.ollama_url)
        result = run_one_model(
            model, brand, args.ollama_url,
            pairs, verse_cache, system_prompt,
            args.error_budget)
        if result:
            all_results.append(result)

    # Comparison table
    print_comparison_table(all_results, source_label, len(pairs))
    print(f"Total time: {(time.time()-t_global)/60:.1f} minutes")

    # Save
    if args.out:
        output = {
            "meta": {
                "models": models,
                "source": source_label,
                "pairs": len(pairs),
                "prompt": prompt_name,
                "seed": args.seed,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_time_minutes": round((time.time()-t_global)/60, 1),
            },
            "results": all_results,
        }
        out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=1)
        print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
