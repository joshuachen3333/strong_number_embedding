#!/usr/bin/env python3
"""Survey9: S1 production task + S8 stripped architecture.

UNV+SN (stripped) → LLM places bare numbers in LCC → script restores shells.

Usage:
    # Single verse
    python3 run_survey9.py --book 創 --chap 1 --sec 1 \
        --model deepseek-v3.1:671b-cloud --ollama-url http://<ollama-host>:11434

    # Full chapter with output
    python3 run_survey9.py --book 創 --chap 1 \
        --model deepseek-v3.1:671b-cloud --ollama-url http://<ollama-host>:11434 --out

    # Dry run
    python3 run_survey9.py --book 創 --chap 1 --sec 1 --dry-run

    # Target version (default: lcc)
    python3 run_survey9.py --book 創 --chap 1 --version rcuv2010 --model ...
"""

import argparse
import json
import os
import re
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(PARENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG, parse_sec_arg as parse_sec_spec
from shared.sn_shell import strip_shell, restore_shell, fix_placement, fix_pipeline, extract_bare_numbers

# Reuse from survey4
S4_DIR = os.path.join(PARENT_DIR, "survey4_self_supervised_prompt_tuning")
sys.path.insert(0, S4_DIR)
from auto_score import strip_sn
from analyze_test_dimensions import extract_tags
from run_benchmark import call_ollama, call_claude_cli, call_gemini_cli

# Reuse qp.php from survey6
S6_DIR = os.path.join(PARENT_DIR, "survey6_original_lang_benchmark")
sys.path.insert(0, S6_DIR)
from run_survey6 import fetch_qp_verse, build_original_text, is_ot_book

DEFAULT_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey9_v0.1.md")


class Tee:
    def __init__(self, log_path, mode="w"):
        self._terminal = sys.stdout
        self._log = open(log_path, mode, encoding="utf-8", buffering=1)

    def write(self, msg):
        self._terminal.write(msg)
        self._log.write(msg)

    def flush(self):
        self._terminal.flush()
        self._log.flush()

    def close(self):
        sys.stdout = self._terminal
        self._log.close()


def load_prompt(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def model_short_name(model):
    return re.sub(r'[:/\\]', '-', model)


def prompt_version(path):
    m = re.search(r'(v\d+\.\d+)', os.path.basename(path))
    return m.group(1) if m else "vunk"


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
    """Strip backticks and trailing explanation."""
    text = text.replace("`", "")
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


def build_shell_lookup(unv_sn_text):
    """Build a lookup table: bare number → original FHL tag string.

    From UNV+SN, extract every tag and map its stripped number to the
    full original tag. Used for zero-loss shell restoration.

    Returns dict: {'07225': '<WH07225>', '09002': '<WAH09002>',
                   '0853': '{<WH0853>}', '8804': '<WTH8804>', ...}
    """
    tags = extract_tags(unv_sn_text)
    lookup = {}
    for t in tags:
        raw = t["raw"]  # e.g. '<WH07225>' or '{<WH0853>}'
        # Strip to get bare number
        stripped = strip_shell(raw, markers=False)
        num = stripped.strip("<>")
        # Store first occurrence (if same number appears multiple times,
        # they should have the same shell format)
        if num not in lookup:
            lookup[num] = raw
    return lookup


def restore_shell_lookup(stripped_text, lookup):
    """Restore shells using lookup table (zero loss).

    Replaces <number> with the original FHL tag from UNV+SN.
    """
    def _replace(m):
        num = m.group(1)
        if num in lookup:
            return lookup[num]
        return m.group(0)  # keep as-is if not found

    return re.sub(r'<(\d+[a-z]?)>', _replace, stripped_text)


def trim_extra_tags(text, input_tags):
    """Remove tags from output that don't exist in input.

    If LLM added tags not present in UNV+SN, remove them.
    Preserves correct tags, only strips extras.
    """
    from collections import Counter
    input_counter = Counter(input_tags)
    output_tags = extract_bare_numbers(text)

    # Track how many of each tag we've seen
    seen = Counter()
    result = text

    # Process tags from left to right, remove extras
    tag_pattern = re.compile(r'<(\d+[a-z]?)>')
    parts = []
    last_end = 0
    for m in tag_pattern.finditer(result):
        num = m.group(1)
        seen[num] += 1
        if seen[num] <= input_counter.get(num, 0):
            # Keep this tag
            parts.append(result[last_end:m.end()])
        else:
            # Extra tag — remove it (keep text before, skip the tag)
            parts.append(result[last_end:m.start()])
        last_end = m.end()
    parts.append(result[last_end:])
    return "".join(parts)


def build_sn_dict_stripped(qp_records):
    """Build SN:word dictionary using stripped (bare) numbers."""
    lines = []
    for r in qp_records:
        bare = strip_shell(f"<{r['sn']}>", markers=False)
        num = bare.strip("<>")
        lines.append(f"{num}: {r['word']}")
    return "\n".join(lines)


def build_survey9_prompt(system_prompt, unv_stripped, unv_plain,
                         target_plain, orig_text, sn_dict,
                         book_eng, chap, sec, target_version):
    """Build prompt: UNV+SN stripped + UNV plain + target plain + original + dict."""
    user = f"""Here is {book_eng} {chap}:{sec} in UNV (和合本) with SN numbers:

{unv_stripped}

Here is the same verse in UNV without annotations:

{unv_plain}

Here is the same verse in {target_version.upper()}:

{target_plain}

Original language text:

{orig_text}

SN number to original word dictionary:

{sn_dict}

Move every SN number from the UNV annotated text to the correct position in the {target_version.upper()} text. Output only the annotated {target_version.upper()} text."""
    return system_prompt, user


def main():
    parser = argparse.ArgumentParser(
        description="Survey9: S1 + S8 — UNV+SN stripped → target version + SN")
    parser.add_argument("--book", default="創")
    parser.add_argument("--chap", default="1")
    parser.add_argument("--sec", nargs="+", default=None)
    parser.add_argument("--version", default="lcc",
                        help="Target Bible version (default: lcc)")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--prompt", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", nargs="?", const="", default=None)
    parser.add_argument("--resume", default=None)
    args = parser.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    brand = detect_brand(args.model, args.ollama_url)
    ot = is_ot_book(book_eng)
    testament = "OT" if ot else "NT"
    target_ver = args.version

    prompt_file = args.prompt if args.prompt else DEFAULT_PROMPT_FILE
    system_prompt = load_prompt(prompt_file) if os.path.exists(prompt_file) else \
        "Move SN numbers from UNV to the target version text."
    pver = prompt_version(prompt_file) if os.path.exists(prompt_file) else "vunk"

    # Resume
    done_refs = set()
    results = []
    resume_path = None
    if args.resume:
        resume_path = os.path.join(SCRIPT_DIR, args.resume) if not os.path.isabs(args.resume) else args.resume
        if os.path.exists(resume_path):
            with open(resume_path, encoding="utf-8") as f:
                prev = json.load(f)
            results = prev.get("verses", [])
            done_refs = {r["ref"] for r in results}
            if args.out is None:
                args.out = resume_path

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

    # Output path
    _out_path = None
    if resume_path:
        _out_path = resume_path
    elif args.out is not None:
        if args.out == "":
            mshort = model_short_name(args.model)
            ts = time.strftime("%Y%m%d_%H%M%S")
            scope = f"{book_eng.lower()}{args.chap.replace('-', '_')}"
            fname = f"s9_{target_ver}_{scope}_{mshort}_{pver}_{ts}.json"
            _out_path = os.path.join(SCRIPT_DIR, "run_logs", fname)
        else:
            _out_path = os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out
    if _out_path:
        os.makedirs(os.path.dirname(_out_path), exist_ok=True)

    # Tee logging
    tee = None
    if _out_path:
        log_path = re.sub(r'\.json$', '.log', _out_path)
        tee_mode = "a" if resume_path else "w"
        tee = Tee(log_path, mode=tee_mode)
        sys.stdout = tee

    print(f"Survey9: S1+S8 — UNV+SN → {target_ver.upper()}+SN (去殼)")
    print(f"Book: {book_eng} ({book_chi})  {testament}")
    print(f"Target: {target_ver.upper()}")
    print(f"Model: {args.model} ({brand})")
    print(f"Prompt: {pver} ({len(system_prompt)} chars)")
    if done_refs:
        print(f"Resume: {len(done_refs)} verses already done")
    print()

    t0 = time.time()

    for chap in chapters:
        try:
            unv_data = fetch_chap_cached(book_chi, chap, "unv", strong=1)
            target_data = fetch_chap_cached(book_chi, chap, target_ver, strong=0)
        except Exception as e:
            print(f"  Fetch error {book_eng} {chap}: {e}")
            continue

        secs = sorted(set(unv_data.keys()) & set(target_data.keys()))
        if args.sec:
            wanted = set(parse_sec_spec(args.sec))
            secs = [s for s in secs if s in wanted]

        for sec in secs:
            ref = f"{book_eng} {chap}:{sec}"
            if ref in done_refs:
                continue

            unv_sn = unv_data[sec]
            unv_plain = strip_sn(unv_sn)
            unv_stripped = strip_shell(unv_sn, markers=False)
            target_plain = target_data[sec]

            # Build shell lookup table from UNV+SN
            shell_lookup = build_shell_lookup(unv_sn)

            # Count input tags
            input_tags = extract_bare_numbers(unv_stripped)
            input_count = len(input_tags)

            # Skip verses with no SN tags (FHL data missing)
            if input_count == 0:
                continue

            # Fetch qp.php
            try:
                qp_records = fetch_qp_verse(book_eng, chap, sec)
            except Exception as e:
                print(f"  {ref:15s} qp.php ERROR: {e}")
                continue

            orig_text = build_original_text(qp_records)
            sn_dict = build_sn_dict_stripped(qp_records)

            if args.dry_run:
                print(f"{'─'*60}")
                print(f"{ref}  UNV tags={input_count}  qp={len(qp_records)}")
                print(f"  UNV+SN:  {unv_stripped[:80]}...")
                print(f"  UNV:     {unv_plain[:80]}...")
                print(f"  {target_ver.upper()}:     {target_plain[:80]}...")
                print(f"  Orig:    {orig_text[:60]}...")
                print(f"  Dict:    {sn_dict[:80]}...")
                continue

            sys_p, user_p = build_survey9_prompt(
                system_prompt, unv_stripped, unv_plain,
                target_plain, orig_text, sn_dict,
                book_eng, chap, sec, target_ver)

            t_call = time.time()
            try:
                raw = call_model(args.model, brand, args.ollama_url, sys_p, user_p)
                output = clean_output(raw) if raw else ""
                dt = time.time() - t_call
                dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

                if dt < 5 and (not output or len(output.strip()) < 10):
                    print(f"  {ref:15s} ⚠ RATE LIMITED ({dt_str})")
                    continue

                # Build core_sns for fix_placement
                core_sns = set()
                for r in qp_records:
                    sn_clean = r['sn'].lstrip('WH').lstrip('WG').lstrip('0') or '0'
                    try:
                        core_sns.add(int(sn_clean.rstrip('abcdefghijklmnopqrstuvwxyz')))
                    except ValueError:
                        pass

                # Pipeline: trim extras → fix_coverage+fix_placement → restore_shell
                trimmed = trim_extra_tags(output, input_tags)
                fixed, fix_rounds = fix_pipeline(trimmed, input_tags, core_sns)
                shelled = restore_shell_lookup(fixed, shell_lookup)

                # Coverage check: count output tags vs input tags
                output_tags = extract_bare_numbers(fixed)
                output_count = len(output_tags)
                cov_rate = output_count / input_count if input_count > 0 else 0

                print(f"  {ref:15s} "
                      f"tags={input_count}→{output_count} "
                      f"cov={cov_rate:.0%}  "
                      f"({dt_str})")

                results.append({
                    "ref": ref,
                    "input_tag_count": input_count,
                    "output_tag_count": output_count,
                    "coverage_rate": round(cov_rate, 4),
                    "model_output": output,
                    "output_fixed": fixed,
                    "output_shelled": shelled,
                    "time": round(dt, 1),
                })

                # Incremental save
                if _out_path:
                    _save(results, _out_path, book_eng, args, brand, pver, target_ver)

            except Exception as e:
                print(f"  {ref:15s} ERROR: {e}")

    if args.dry_run:
        if tee:
            tee.close()
        return

    # Summary
    scored = [r for r in results if "coverage_rate" in r]
    if scored:
        print(f"\n{'='*60}")
        print(f"  Survey9 S1+S8 — {book_eng} → {target_ver.upper()}, {args.model}")
        print(f"{'='*60}")
        print(f"  Verses: {len(scored)}")
        avg_cov = sum(r["coverage_rate"] for r in scored) / len(scored)
        full_cov = sum(1 for r in scored if r["output_tag_count"] >= r["input_tag_count"])
        print(f"  Avg tag coverage: {avg_cov:.1%}")
        print(f"  Full coverage: {full_cov}/{len(scored)} ({full_cov/len(scored)*100:.1f}%)")
        print(f"  Time: {(time.time()-t0)/60:.1f} minutes")

    if _out_path:
        _save(results, _out_path, book_eng, args, brand, pver, target_ver)
        print(f"\n  Saved to {_out_path}")

    if tee:
        tee.close()


def _save(results, out_path, book_eng, args, brand, pver, target_ver):
    scored = [r for r in results if "coverage_rate" in r]
    out_data = {
        "meta": {
            "task": "survey9_s1_plus_s8",
            "book": book_eng,
            "target_version": target_ver,
            "model": args.model,
            "brand": brand,
            "prompt_version": pver,
            "total_scored": len(scored),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "verses": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
