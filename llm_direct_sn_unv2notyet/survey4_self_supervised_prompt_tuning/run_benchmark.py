#!/usr/bin/env python3
"""Run survey4 benchmark: cheap model annotates UNV with Strong's Numbers.

Uses DMFS pairs (dimension-matched few-shot) to test a model's ability
to reproduce FHL's UNV+SN annotations. Results scored by auto_score.py.

Usage:
    # Generate pairs + run in one shot
    python3 run_benchmark.py --pct 1 --model qwen3:32b \
        --ollama-url http://sai.fhl.net:11434 --out results.json

    # Use pre-built pairs
    python3 run_benchmark.py --pairs dmfs_pairs.json --model qwen3:32b \
        --ollama-url http://sai.fhl.net:11434 --out results.json

    # With custom prompt
    python3 run_benchmark.py --pct 1 --model qwen3:32b \
        --prompt my_prompt.md --ollama-url http://sai.fhl.net:11434

    # Use Claude CLI
    python3 run_benchmark.py --pct 1 --model haiku --out results.json

    # Dry run (just show prompt, don't call model)
    python3 run_benchmark.py --pct 1 --dry-run --verse-pair-count 3
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG
from auto_score import strip_sn, score_verse

# Reverse map: English book → Chinese book
ENG_TO_CHI = {v: k for k, v in CHI_TO_ENG.items()}

DEFAULT_PROMPT = """You are an expert at Biblical Hebrew and Greek Strong's Number annotation.

Given a Chinese Bible verse (UNV 和合本) without annotations, insert the correct
Strong's Number tags in FHL format. Preserve the exact Chinese text — only add SN tags.

FHL tag format rules:
- Hebrew core: <WHnnnn> or <WH0nnnn> (zero-padded to 4-5 digits)
- Hebrew morph: <WTHnnnn> (4-digit, 8xxx series)
- Hebrew prefix: <WAHnnnnn> (includes 900x inseparable prepositions)
- Greek core: <WGnnnn>
- Greek morph: <WTGnnnn> (5xxx series)
- Implicit markers: {<WHnnnn>} or {<WGnnnn>} (in braces)
- Tags follow the Chinese word they annotate
- Morphology tags follow the verb SN they describe
- 900x prefix tags precede the core SN they modify

Output ONLY the annotated verse text. No explanation, no JSON wrapping."""


def load_prompt(path):
    """Load custom prompt from file."""
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def build_task_prompt(system_prompt, example_annotated, example_plain, test_plain):
    """Build the full prompt for one DMFS pair.

    Args:
        system_prompt: system instructions
        example_annotated: UNV+SN of v1 (ground truth with tags)
        example_plain: UNV of v1 (same verse, tags stripped)
        test_plain: UNV of v2 (test verse, no tags)

    Returns:
        (system, user) prompt tuple
    """
    user = f"""Here is an example of UNV text annotated with Strong's Numbers:

Input (plain UNV):
{example_plain}

Output (annotated UNV+SN):
{example_annotated}

Now annotate the following verse in the same format:

Input (plain UNV):
{test_plain}

Output (annotated UNV+SN):"""

    return system_prompt, user


def call_ollama(model, system_prompt, user_prompt, ollama_url, timeout=600):
    """Call Ollama API. Returns raw response text."""
    payload = {
        "model": model,
        "prompt": user_prompt,
        "system": system_prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_ctx": 8192},
    }
    req = urllib.request.Request(
        f"{ollama_url}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=timeout)
    body = json.loads(resp.read().decode("utf-8"))
    return body.get("response", "").strip()


def call_claude_cli(model, system_prompt, user_prompt, timeout=300):
    """Call Claude via CLI. Returns raw response text."""
    model_map = {"haiku": "haiku", "sonnet": "sonnet", "opus": "opus"}
    cli_model = model_map.get(model, model)
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    result = subprocess.run(
        ["claude", "--model", cli_model, "-p", full_prompt],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout.strip()


def call_gemini_cli(model, system_prompt, user_prompt, timeout=120):
    """Call Gemini via CLI. Returns raw response text."""
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    result = subprocess.run(
        ["gemini", "--model", model, "-p", full_prompt],
        capture_output=True, text=True, timeout=timeout,
    )
    return result.stdout.strip()


def parse_ref(ref):
    """Parse 'Gen 1:1' into (book_chi, chap, sec)."""
    parts = ref.split()
    book_eng = parts[0]
    chap_sec = parts[1].split(":")
    book_chi = ENG_TO_CHI.get(book_eng, book_eng)
    return book_chi, int(chap_sec[0]), int(chap_sec[1])


def main():
    parser = argparse.ArgumentParser(
        description="Run survey4 benchmark: model annotates UNV with SN")
    # Input
    parser.add_argument("--pairs", default=None,
                        help="Pre-built DMFS pairs JSON")
    parser.add_argument("--pct", type=float, default=None,
                        help="Auto-generate test set + pairs at this %%")
    parser.add_argument("--testament", choices=["OT", "NT"],
                        help="Filter by testament")
    parser.add_argument("--seed", type=int, default=42)
    # Model
    parser.add_argument("--model", default="qwen3:32b",
                        help="Model name (default: qwen3:32b)")
    parser.add_argument("--ollama-url", default=None,
                        help="Ollama server URL (e.g., http://sai.fhl.net:11434)")
    parser.add_argument("--brand", choices=["ollama", "claude", "gemini"],
                        default=None,
                        help="Force brand (auto-detected from model name if omitted)")
    # Prompt
    parser.add_argument("--prompt", default=None,
                        help="Custom prompt file (default: built-in)")
    # Output
    parser.add_argument("--out", default=None,
                        help="Output JSON file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without calling model")
    parser.add_argument("--verse-pair-count", type=int, default=None,
                        help="Only run first N pairs")
    parser.add_argument("--till", default=None,
                        help="Stop before this time (e.g., 7:50, 08:00)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    # Parse --till into a deadline
    deadline = None
    if args.till:
        import datetime
        hm = args.till.split(":")
        now = datetime.datetime.now()
        deadline = now.replace(hour=int(hm[0]), minute=int(hm[1]), second=0, microsecond=0)
        if deadline <= now:
            deadline += datetime.timedelta(days=1)
        print(f"Deadline: stop before {deadline.strftime('%H:%M')}")

    # Load or generate pairs
    if args.pairs:
        with open(args.pairs, encoding="utf-8") as f:
            pairs_data = json.load(f)
        pairs = pairs_data["pairs"]
    elif args.pct:
        from sample_test_set import sample_greedy, load_map
        from dmfs_select import select_pairs
        data = load_map(os.path.join(SCRIPT_DIR, "dim_verse_map.json"))
        selected, _ = sample_greedy(data, args.pct, args.testament, seed=args.seed)
        pairs, _ = select_pairs(data, selected)
        print(f"Generated {len(pairs)} DMFS pairs at {args.pct}%")
    else:
        print("Error: provide --pairs or --pct", file=sys.stderr)
        sys.exit(1)

    if args.verse_pair_count:
        pairs = pairs[:args.verse_pair_count]

    # Load prompt
    system_prompt = DEFAULT_PROMPT
    if args.prompt:
        system_prompt = load_prompt(args.prompt)

    # Detect brand
    brand = args.brand
    if not brand:
        if args.ollama_url:
            brand = "ollama"
        elif args.model in ("haiku", "sonnet", "opus") or "claude" in args.model:
            brand = "claude"
        elif "gemini" in args.model or "flash" in args.model:
            brand = "gemini"
        else:
            brand = "ollama"

    print(f"Model: {args.model} ({brand})")
    print(f"Pairs: {len(pairs)}")
    print(f"Prompt: {'custom' if args.prompt else 'built-in'} ({len(system_prompt)} chars)")
    print()

    # Run
    results = []
    t0 = time.time()

    for i, pair in enumerate(pairs):
        # Check deadline
        if deadline:
            import datetime
            if datetime.datetime.now() >= deadline:
                print(f"\n  ⏰ Deadline reached ({args.till}). Stopping with {i}/{len(pairs)} done.")
                break

        test_ref = pair["test"]["ref"]
        example_ref = pair["example"]["ref"]

        # Fetch ground truth
        t_chi, t_chap, t_sec = parse_ref(test_ref)
        e_chi, e_chap, e_sec = parse_ref(example_ref)

        example_annotated = fetch_chap_cached(e_chi, e_chap, "unv", strong=1)[e_sec]
        example_plain = strip_sn(example_annotated)
        test_annotated = fetch_chap_cached(t_chi, t_chap, "unv", strong=1)[t_sec]
        test_plain = strip_sn(test_annotated)

        sys_p, user_p = build_task_prompt(
            system_prompt, example_annotated, example_plain, test_plain)

        if args.dry_run:
            print(f"{'─'*60}")
            print(f"[{i+1}/{len(pairs)}] {test_ref} (example: {example_ref})")
            print(f"  Example plain: {example_plain[:80]}...")
            print(f"  Test plain:    {test_plain[:80]}...")
            if args.verbose:
                print(f"  User prompt:\n{user_p}")
            continue

        # Call model
        elapsed_str = f"{(time.time()-t0)/60:.1f}m"
        print(f"  [{i+1}/{len(pairs)}] {test_ref} (ex: {example_ref}) [{elapsed_str}]",
              end="", flush=True)

        try:
            if brand == "ollama":
                model_output = call_ollama(
                    args.model, sys_p, user_p, args.ollama_url)
            elif brand == "claude":
                model_output = call_claude_cli(args.model, sys_p, user_p)
            elif brand == "gemini":
                model_output = call_gemini_cli(args.model, sys_p, user_p)
            else:
                model_output = ""

            # Score immediately
            score = score_verse(model_output, test_annotated)
            print(f" → exact={score['exact_match']} cov={score['coverage']:.2f}"
                  f" place={score['placement']:.2f} fmt={score['format']:.2f}")

            results.append({
                "ref": test_ref,
                "example_ref": example_ref,
                "dims": pair["test"]["dims"],
                "jaccard": pair["example"]["jaccard"],
                "model_output": model_output,
                "ground_truth": test_annotated,
                "score": score,
            })

        except Exception as e:
            print(f" → ERROR: {e}")
            results.append({
                "ref": test_ref,
                "example_ref": example_ref,
                "dims": pair["test"]["dims"],
                "error": str(e),
            })

    if args.dry_run:
        return

    # Summary
    scored = [r for r in results if "score" in r]
    errors = [r for r in results if "error" in r]

    print(f"\n{'='*60}")
    print(f"  Benchmark Summary — {args.model}")
    print(f"{'='*60}")
    print(f"  Total:   {len(results)}")
    print(f"  Scored:  {len(scored)}")
    print(f"  Errors:  {len(errors)}")

    if scored:
        avg = {
            "exact": sum(1 for r in scored if r["score"]["exact_match"]) / len(scored),
            "coverage": sum(r["score"]["coverage"] for r in scored) / len(scored),
            "placement": sum(r["score"]["placement"] for r in scored) / len(scored),
            "format": sum(r["score"]["format"] for r in scored) / len(scored),
        }
        print(f"  Exact match: {avg['exact']*100:.1f}%")
        print(f"  Avg coverage:  {avg['coverage']:.4f}")
        print(f"  Avg placement: {avg['placement']:.4f}")
        print(f"  Avg format:    {avg['format']:.4f}")
        print(f"  Time: {(time.time()-t0)/60:.1f} minutes")

    # Save
    if args.out:
        output = {
            "meta": {
                "model": args.model,
                "brand": brand,
                "prompt": "custom" if args.prompt else "built-in",
                "prompt_file": args.prompt,
                "total": len(results),
                "scored": len(scored),
                "errors": len(errors),
                "avg_scores": avg if scored else None,
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
