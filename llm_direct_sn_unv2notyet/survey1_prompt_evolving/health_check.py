#!/usr/bin/env python3
"""Health check: poll all 3 models until they're available, then optionally resume.

Usage:
    python3 health_check.py                    # check once
    python3 health_check.py --poll             # poll every 5 min until all ready
    python3 health_check.py --poll --resume    # poll, then auto-resume when ready
    python3 health_check.py --interval 10      # poll every 10 min
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS = [
    {"name": "opus",                 "brand": "claude", "model": "opus"},
    {"name": "gemini-3-pro-preview", "brand": "gemini", "model": "gemini-3-pro-preview"},
    {"name": "gpt-5.4",             "brand": "codex",  "model": "gpt-5.4"},
]


def check_claude(model: str, timeout: int = 30) -> tuple:
    """Returns (ok: bool, message: str)."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return False, "CLI not found"
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    try:
        result = subprocess.run(
            [claude_bin, "-p", "--output-format", "stream-json",
             "--model", model, "--no-session-persistence",
             "--disallowed-tools", "Bash,Edit,Write,Read,Glob,Grep,Task"],
            capture_output=True, text=True, timeout=timeout, env=env,
            input="say ok"
        )
        if result.returncode == 0:
            # Check for rate limit in output
            for line in result.stdout.split('\n'):
                try:
                    obj = json.loads(line)
                    if obj.get("type") == "result":
                        return True, "OK"
                except json.JSONDecodeError:
                    continue
            return True, "OK (response received)"
        stderr = result.stderr.lower()
        if any(p in stderr for p in ["rate limit", "429", "overloaded", "quota"]):
            return False, "rate limited"
        return False, f"error: {result.stderr[:100]}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:100]


def check_gemini(model: str, timeout: int = 30) -> tuple:
    """Returns (ok: bool, message: str)."""
    gemini_bin = shutil.which("gemini")
    if not gemini_bin:
        return False, "CLI not found"
    try:
        result = subprocess.run(
            [gemini_bin, "-p", "say ok", "-y",
             "--output-format", "stream-json", "--model", model],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            return True, "OK"
        stderr = result.stderr.lower()
        if any(p in stderr for p in ["rate limit", "429", "overloaded", "quota"]):
            return False, "rate limited"
        return False, f"error: {result.stderr[:100]}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:100]


def check_codex(model: str, timeout: int = 30) -> tuple:
    """Returns (ok: bool, message: str)."""
    codex_bin = shutil.which("codex")
    if not codex_bin:
        return False, "CLI not found"
    try:
        result = subprocess.run(
            [codex_bin, "exec", "--sandbox", "read-only", "--model", model, "-"],
            capture_output=True, text=True, timeout=timeout,
            input="say ok"
        )
        if result.returncode == 0:
            return True, "OK"
        all_output = (result.stderr + result.stdout).lower()
        if any(p in all_output for p in ["rate limit", "429", "overloaded", "quota"]):
            return False, "rate limited"
        return False, f"error: {(result.stderr + result.stdout)[:100]}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:100]


def check_all():
    """Check all 3 models. Returns (all_ok, results_dict)."""
    results = {}
    checkers = {
        "claude": check_claude,
        "gemini": check_gemini,
        "codex": check_codex,
    }

    now = datetime.now().strftime("%H:%M:%S")
    print(f"\n  [{now}] Health check:", flush=True)

    all_ok = True
    for model_info in MODELS:
        name = model_info["name"]
        brand = model_info["brand"]
        model_id = model_info["model"]

        ok, msg = checkers[brand](model_id)
        status = "✓" if ok else "✗"
        print(f"    {status} {name}: {msg}", flush=True)
        results[name] = {"ok": ok, "message": msg}
        if not ok:
            all_ok = False

    if all_ok:
        print(f"  All models ready!", flush=True)
    else:
        failed = [n for n, r in results.items() if not r["ok"]]
        print(f"  Waiting on: {', '.join(failed)}", flush=True)

    return all_ok, results


def main():
    parser = argparse.ArgumentParser(description="Health check for survey1_prompt_evolving models")
    parser.add_argument("--poll", action="store_true",
                        help="Poll until all models are ready")
    parser.add_argument("--interval", type=int, default=5,
                        help="Poll interval in minutes (default: 5)")
    parser.add_argument("--resume", action="store_true",
                        help="Auto-resume gold standard run when all ready")
    parser.add_argument("--book", default="創")
    parser.add_argument("--chap", default="1-3")
    args = parser.parse_args()

    all_ok, _ = check_all()

    if not args.poll:
        sys.exit(0 if all_ok else 1)

    # Poll loop
    while not all_ok:
        next_check = datetime.now().strftime("%H:%M:%S")
        print(f"\n  Next check in {args.interval} min...", flush=True)
        time.sleep(args.interval * 60)
        all_ok, _ = check_all()

    if args.resume:
        print(f"\n{'='*60}")
        print(f"  All models ready — resuming gold standard run")
        print(f"{'='*60}\n", flush=True)
        os.execvp(sys.executable, [
            sys.executable, os.path.join(SURVEY_DIR, "run_gold_standard.py"),
            "--book", args.book, "--chap", args.chap, "--resume"
        ])
    else:
        print(f"\n  All models ready. Run manually:")
        print(f"  python3 run_gold_standard.py --book {args.book} --chap {args.chap} --resume")


if __name__ == "__main__":
    main()
