#!/usr/bin/env python3
"""Model Shootout — compare multiple models on the same small set of pairs.

Runs N pairs from a dim across multiple models, outputs comparison table.
Use this to pick the best model before committing to a full round-robin.

Usage:
    # Compare ollama models on sai
    python3 model_shootout.py --ollama-url http://sai.fhl.net:11434 \
        --models qwen3:8b qwen3:32b deepseek-v3.1:671b-cloud \
        --dim 1 --pairs 5

    # Compare Claude models
    python3 model_shootout.py --models haiku sonnet --dim 1 --pairs 5

    # Mix ollama + claude
    python3 model_shootout.py \
        --models sonnet qwen3:32b deepseek-v3.1:671b-cloud \
        --ollama-url http://sai.fhl.net:11434 \
        --dim 1 --pairs 5

    # Auto-discover ollama models
    python3 model_shootout.py --ollama-url http://sai.fhl.net:11434 \
        --auto-discover --dim 1 --pairs 3
"""

import argparse
import json
import os
import sys
import time
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG
from auto_score import strip_sn, score_verse
from run_benchmark import (call_ollama, call_claude_cli, call_gemini_cli,
                           build_task_prompt, parse_ref)

DEFAULT_LIBRARY = os.path.join(SCRIPT_DIR, "exemplar_library.json")
DEFAULT_PROMPT = os.path.join(SCRIPT_DIR, "prompts", "survey4_v0.1.md")

CLAUDE_MODELS = {"haiku", "sonnet", "opus"}
GEMINI_MODELS = {"gemini-2.0-flash", "gemini-2.5-flash-preview", "gemini-2.5-pro-preview"}


def detect_brand(model, ollama_url):
    if model in CLAUDE_MODELS or "claude" in model:
        return "claude"
    if model in GEMINI_MODELS or "gemini" in model:
        return "gemini"
    if ollama_url:
        return "ollama"
    return "claude"  # fallback


def discover_ollama_models(ollama_url):
    """Fetch available models from ollama server."""
    try:
        resp = urllib.request.urlopen(f"{ollama_url}/api/tags", timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        print(f"  Failed to discover models: {e}")
        return []


def call_model(model, brand, ollama_url, system_prompt, user_prompt):
    if brand == "ollama":
        return call_ollama(model, system_prompt, user_prompt, ollama_url)
    elif brand == "claude":
        return call_claude_cli(model, system_prompt, user_prompt)
    elif brand == "gemini":
        return call_gemini_cli(model, system_prompt, user_prompt)
    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Compare multiple models on the same pairs")
    parser.add_argument("--models", nargs="+", default=None,
                        help="Model names to compare")
    parser.add_argument("--auto-discover", action="store_true",
                        help="Auto-discover all ollama models")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--dim", type=int, default=1,
                        help="Which dim to sample pairs from (default: 1)")
    parser.add_argument("--pairs", type=int, default=5,
                        help="Number of example→test pairs to run (default: 5)")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--library", default=DEFAULT_LIBRARY)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    # Load
    with open(args.library, encoding="utf-8") as f:
        lib = json.load(f)
    with open(args.prompt, encoding="utf-8") as f:
        system_prompt = f.read().strip()

    # Get models
    models = args.models or []
    if args.auto_discover and args.ollama_url:
        discovered = discover_ollama_models(args.ollama_url)
        print(f"  Discovered ollama models: {discovered}")
        models = list(set(models + discovered))

    if not models:
        print("Error: provide --models or --auto-discover with --ollama-url")
        sys.exit(1)

    # Build pairs from dim's candidates
    dim_key = str(args.dim)
    candidates = lib["library"][dim_key]["verses"]
    if len(candidates) < 2:
        print(f"Dim #{args.dim} has < 2 candidates, cannot build pairs")
        sys.exit(1)

    import random
    random.seed(args.seed)

    # Pick N pairs: each pair = (example, test)
    pairs = []
    indices = list(range(len(candidates)))
    random.shuffle(indices)
    for i in range(min(args.pairs, len(candidates) - 1)):
        ex_idx = indices[i]
        # Pick a different candidate as test
        test_idx = indices[(i + 1) % len(candidates)]
        pairs.append((candidates[ex_idx], candidates[test_idx]))

    print(f"Shootout: {len(models)} models × {len(pairs)} pairs = "
          f"{len(models) * len(pairs)} calls")
    print(f"Dim #{args.dim}: {lib['library'][dim_key]['label']}")
    print(f"Prompt: {os.path.basename(args.prompt)} ({len(system_prompt)} chars)")
    print()

    # Prepare verse texts
    pair_data = []
    for ex_v, test_v in pairs:
        ex_chi, ex_chap, ex_sec = parse_ref(ex_v["ref"])
        t_chi, t_chap, t_sec = parse_ref(test_v["ref"])
        ex_annotated = fetch_chap_cached(ex_chi, ex_chap, "unv", strong=1)[ex_sec]
        test_annotated = fetch_chap_cached(t_chi, t_chap, "unv", strong=1)[t_sec]
        pair_data.append({
            "ex_ref": ex_v["ref"],
            "test_ref": test_v["ref"],
            "ex_annotated": ex_annotated,
            "ex_plain": strip_sn(ex_annotated),
            "test_annotated": test_annotated,
            "test_plain": strip_sn(test_annotated),
        })

    # Run each model
    results = {}  # model → list of scores

    for model in models:
        brand = detect_brand(model, args.ollama_url)
        print(f"  ── {model} ({brand}) ──")
        results[model] = {
            "brand": brand,
            "scores": [],
            "errors": 0,
            "total_time": 0,
        }

        for j, pd in enumerate(pair_data):
            sys_p, user_p = build_task_prompt(
                system_prompt, pd["ex_annotated"], pd["ex_plain"],
                pd["test_plain"])

            try:
                t0 = time.time()
                output = call_model(model, brand, args.ollama_url, sys_p, user_p)
                dt = time.time() - t0
                dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"
                results[model]["total_time"] += dt

                # Rate limit check
                if dt < 5 and (not output or len(output.strip()) < 10):
                    print(f"    [{j+1}] {pd['ex_ref']:12s}→{pd['test_ref']:12s}  "
                          f"⚠ RATE LIMITED ({dt_str})")
                    results[model]["errors"] += 1
                    continue

                score = score_verse(output, pd["test_annotated"])
                results[model]["scores"].append({
                    "pair": f"{pd['ex_ref']}→{pd['test_ref']}",
                    "cov": score["coverage"],
                    "place": score["placement"],
                    "fmt": score["format"],
                    "exact": score["exact_match"],
                    "time": round(dt, 1),
                })
                print(f"    [{j+1}] {pd['ex_ref']:12s}→{pd['test_ref']:12s}  "
                      f"cov={score['coverage']:.2f} place={score['placement']:.2f} "
                      f"fmt={score['format']:.2f} exact={score['exact_match']}  "
                      f"({dt_str})")

            except Exception as e:
                print(f"    [{j+1}] {pd['ex_ref']:12s}→{pd['test_ref']:12s}  "
                      f"ERROR: {e}")
                results[model]["errors"] += 1

        print()

    # Comparison table
    print(f"{'='*80}")
    print(f"  MODEL SHOOTOUT — Dim #{args.dim}, {len(pairs)} pairs")
    print(f"{'='*80}")
    print(f"  {'Model':<35s} {'Cov':>6s} {'Place':>6s} {'Fmt':>6s} "
          f"{'Exact':>6s} {'Time':>8s} {'Err':>4s}")
    print(f"  {'─'*35} {'─'*6} {'─'*6} {'─'*6} {'─'*6} {'─'*8} {'─'*4}")

    ranking = []
    for model in models:
        r = results[model]
        scores = r["scores"]
        if scores:
            avg_cov = sum(s["cov"] for s in scores) / len(scores)
            avg_place = sum(s["place"] for s in scores) / len(scores)
            avg_fmt = sum(s["fmt"] for s in scores) / len(scores)
            exact_pct = sum(1 for s in scores if s["exact"]) / len(scores)
            avg_time = r["total_time"] / (len(scores) + r["errors"])
            time_str = f"{int(avg_time)//60}m{int(avg_time)%60:02d}s"
        else:
            avg_cov = avg_place = avg_fmt = exact_pct = 0
            time_str = "N/A"

        print(f"  {model:<35s} {avg_cov:6.3f} {avg_place:6.3f} {avg_fmt:6.3f} "
              f"{exact_pct:5.0%}  {time_str:>8s} {r['errors']:4d}")
        ranking.append((model, avg_cov, avg_place, avg_fmt, exact_pct))

    # Winner
    ranking.sort(key=lambda x: (-x[1], -x[4], -x[2]))
    print(f"\n  🏆 Best coverage: {ranking[0][0]} (avg_cov={ranking[0][1]:.3f})")

    # Save
    if args.out:
        output = {
            "meta": {
                "dim": args.dim,
                "pairs": len(pairs),
                "prompt": os.path.basename(args.prompt),
                "seed": args.seed,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "pair_refs": [f"{p['ex_ref']}→{p['test_ref']}" for p in pair_data],
            "results": {m: results[m] for m in models},
        }
        out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=1)
        print(f"\n  Saved to {out_path}")


if __name__ == "__main__":
    main()
