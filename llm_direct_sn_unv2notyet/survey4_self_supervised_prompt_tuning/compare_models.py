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
        --ollama-url http://<ollama-host>:11434

    # Pre-built pairs
    python3 compare_models.py --pairs dmfs_pairs.json --verse-pair-count 10 \
        --models qwen3:8b qwen3:32b \
        --ollama-url http://localhost:11434

    # Merge results from different days (same --dim --seed --verse-pair-count)
    python3 compare_models.py --merge day1.json day2.json --out merged.json

    # Tournament mode: multi-round auto-elimination
    python3 compare_models.py --tournament --auto-discover \
        --ollama-url http://localhost:11434 --dim 1 \
        --out tournament_result.json
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

# Size tier grouping for tournament mode
SIZE_TIERS = {
    "1-2B": ["llama3.2:1b", "smollm2:1.7b"],
    "3-4B": ["llama3.2:3b", "phi4-mini:3.8b", "ministral-3:3b", "qwen3:4b", "gemma3:4b"],
    "7-8B": ["mistral:7b", "deepseek-r1:7b", "aya:8b", "llama3.1:8b", "qwen3:8b", "ministral-3:8b"],
    "12-14B": ["mistral-nemo:12b", "gemma3:12b", "ministral-3:14b", "phi4:14b", "deepseek-r1:14b", "qwen3:14b"],
    "30-35B": ["qwen3:30b", "qwen3:32b", "aya:35b"],
    "70B+": ["llama3.3:70b", "qwen2.5:72b"],
    "cloud": ["deepseek-v3.1:671b-cloud", "devstral-2:123b-cloud"],
}


def get_tier(model):
    """Get size tier for a model."""
    for tier, models in SIZE_TIERS.items():
        if model in models:
            return tier
    # Guess by name
    for tier, models in SIZE_TIERS.items():
        for m in models:
            if model.split(":")[0] == m.split(":")[0]:
                return tier
    return "unknown"


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


def run_tournament(models, ollama_url, dim, system_prompt, seed,
                   initial_pairs=3, error_budget=5, max_pairs=50):
    """Multi-round tournament with condition-driven elimination.

    Returns (survivors, eliminated, all_round_results).
    """
    # Group models by tier
    tier_models = {}
    for model in models:
        tier = get_tier(model)
        tier_models.setdefault(tier, []).append(model)

    print(f"\n{'='*70}")
    print(f"  TOURNAMENT — {len(models)} models in {len(tier_models)} tiers")
    print(f"{'='*70}")
    for tier in sorted(tier_models.keys()):
        print(f"  {tier}: {tier_models[tier]}")
    print()

    active_models = list(models)
    eliminated = []  # (model, tier, round, reason, best_cov)
    all_round_results = []
    n_pairs = initial_pairs
    round_num = 0
    prev_scores = {}

    while active_models and n_pairs <= max_pairs:
        round_num += 1
        print(f"\n{'─'*70}")
        print(f"  ROUND {round_num}: {len(active_models)} models × {n_pairs} pairs")
        print(f"{'─'*70}")

        # Build pairs
        pairs, source_label = build_pairs_from_dim(dim, DEFAULT_LIBRARY, n_pairs, seed)
        verse_cache = build_verse_cache(pairs)

        # Run all active models
        round_results = {}
        for model in active_models:
            brand = detect_brand(model, ollama_url)
            result = run_one_model(
                model, brand, ollama_url,
                pairs, verse_cache, system_prompt, error_budget)
            if result:
                round_results[model] = result
            else:
                tier = get_tier(model)
                eliminated.append((model, tier, round_num, "no valid scores", 0))

        all_round_results.append({
            "round": round_num,
            "pairs": n_pairs,
            "results": list(round_results.values()),
        })

        # Elimination within each tier
        new_active = []
        all_decided = True

        for tier in sorted(tier_models.keys()):
            tier_active = [m for m in tier_models[tier] if m in round_results]
            if not tier_active:
                continue

            tier_scores = [(m, round_results[m]["coverage"]) for m in tier_active]
            tier_scores.sort(key=lambda x: -x[1])
            best_model, best_cov = tier_scores[0]

            print(f"\n  Tier {tier}:")
            for m, cov in tier_scores:
                print(f"    {m:<30s} cov={cov:.3f}")

            # Rule: entire tier too weak
            if best_cov < 0.05:
                print(f"    → TIER ELIMINATED (best cov={best_cov:.3f} < 0.05)")
                for m, cov in tier_scores:
                    eliminated.append((m, tier, round_num, "tier too weak", cov))
                continue

            # Rule: eliminate bottom (> 50% behind tier best)
            for m, cov in tier_scores:
                if best_cov > 0 and cov < best_cov * 0.5:
                    print(f"    → {m} ELIMINATED (cov={cov:.3f} < 50% of best)")
                    eliminated.append((m, tier, round_num, "bottom 50%", cov))
                else:
                    new_active.append(m)

            # Check if tier is decided
            tier_survivors = [m for m in new_active if get_tier(m) == tier]
            if len(tier_survivors) > 1:
                top_cov = max(round_results[m]["coverage"] for m in tier_survivors)
                second_cov = sorted(
                    [round_results[m]["coverage"] for m in tier_survivors],
                    reverse=True)[1]
                gap = (top_cov - second_cov) / top_cov if top_cov > 0 else 0

                if gap > 0.10:
                    print(f"    → Gap {gap:.0%} > 10%: tier DECIDED")
                else:
                    print(f"    → Gap {gap:.0%} ≤ 10%: need more pairs")
                    all_decided = False

                # Check stability (compare with previous round)
                if round_num > 1:
                    stable = True
                    for m in tier_survivors:
                        if m in prev_scores:
                            change = abs(round_results[m]["coverage"] - prev_scores[m])
                            if change > 0.02:
                                stable = False
                    if stable:
                        print(f"    → Scores stable (change < 2%): tier DECIDED")

        active_models = new_active
        prev_scores = {m: round_results[m]["coverage"] for m in round_results}

        # Check global stop
        if all_decided:
            print(f"\n  All tiers decided. Tournament complete.")
            break

        # Double pairs for next round
        n_pairs = min(n_pairs * 2, max_pairs)
        if n_pairs >= max_pairs:
            print(f"\n  Max pairs ({max_pairs}) reached. Tournament complete.")
            break

    # Final summary
    survivors = []
    if active_models and round_results:
        for model in active_models:
            if model in round_results:
                r = round_results[model]
                r["tier"] = get_tier(model)
                survivors.append(r)

    print(f"\n{'='*70}")
    print(f"  TOURNAMENT RESULTS")
    print(f"{'='*70}")

    if survivors:
        survivors.sort(key=lambda r: (-r["coverage"], r["sec_per_verse"]))
        print(f"\n  SURVIVORS ({len(survivors)}):")
        print(f"  {'Model':<30} {'Tier':<8} {'Cov':>6} {'Exact':>6} {'s/v':>5}")
        print(f"  {'─'*30} {'─'*8} {'─'*6} {'─'*6} {'─'*5}")
        for r in survivors:
            print(f"  {r['model']:<30} {r['tier']:<8} "
                  f"{r['coverage']:6.3f} {r['exact']*100:5.1f}% "
                  f"{r['sec_per_verse']:5.1f}")

    if eliminated:
        print(f"\n  ELIMINATED ({len(eliminated)}):")
        for m, tier, rnd, reason, cov in eliminated:
            print(f"    R{rnd} {m:<30} {tier:<8} cov={cov:.3f}  ({reason})")

    return survivors, eliminated, all_round_results


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
    parser.add_argument("--tournament", action="store_true",
                        help="Multi-round tournament with auto-elimination")
    parser.add_argument("--out", default=None)
    # Merge mode
    parser.add_argument("--merge", nargs="+", default=None,
                        help="Merge multiple result JSONs and print combined table")
    args = parser.parse_args()

    # ── Merge mode ──
    if args.merge:
        all_results = []
        seen_models = set()
        source_label = None
        n_pairs = 0
        for path in args.merge:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if source_label is None:
                source_label = data["meta"].get("source", "merged")
                n_pairs = data["meta"].get("pairs", 0)
            for r in data["results"]:
                if r["model"] not in seen_models:
                    all_results.append(r)
                    seen_models.add(r["model"])
                else:
                    print(f"  ⚠ Duplicate model {r['model']} in {path}, skipped")

        print_comparison_table(all_results, f"{source_label} (merged)", n_pairs)

        if args.out:
            output = {
                "meta": {
                    "merged_from": args.merge,
                    "source": source_label,
                    "pairs": n_pairs,
                    "models": [r["model"] for r in all_results],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                "results": all_results,
            }
            out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=1)
            print(f"Saved merged to {out_path}")
        return

    # Get models
    models = args.models or []
    if args.auto_discover and args.ollama_url:
        discovered = discover_ollama_models(args.ollama_url)
        print(f"  Discovered: {discovered}")
        models = list(dict.fromkeys(models + discovered))  # preserve order, dedup

    if not models:
        print("Error: provide --models or --auto-discover with --ollama-url")
        sys.exit(1)

    # ── Tournament mode ──
    if args.tournament:
        if args.dim is None:
            args.dim = 1  # default dim for tournament
        # Load prompt
        if args.prompt:
            system_prompt = load_prompt(args.prompt)
        elif os.path.exists(DEFAULT_PROMPT_FILE):
            system_prompt = load_prompt(DEFAULT_PROMPT_FILE)
        else:
            system_prompt = DEFAULT_PROMPT

        initial = args.verse_pair_count or 3
        survivors, elim, rounds = run_tournament(
            models, args.ollama_url, args.dim, system_prompt,
            args.seed, initial_pairs=initial, error_budget=args.error_budget)

        if args.out:
            output = {
                "meta": {
                    "mode": "tournament",
                    "dim": args.dim,
                    "seed": args.seed,
                    "initial_pairs": initial,
                    "total_rounds": len(rounds),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                "survivors": survivors,
                "eliminated": [
                    {"model": m, "tier": t, "round": r, "reason": reason, "cov": cov}
                    for m, t, r, reason, cov in elim
                ],
                "rounds": rounds,
            }
            out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=1)
            print(f"\nSaved to {out_path}")
        return

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
