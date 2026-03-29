#!/usr/bin/env python3
"""Survey8: Simplest SN benchmark — bare numbers + original-language dict.

LLM only inserts bare numbers (<7225>, <430>). Script handles format shells.
Dual scoring: Score 1 (stripped comparison) + Score 2 (shelled comparison).

Usage:
    python3 run_survey8.py --book 創 --chap 1 --sec 1 --model sonnet
    python3 run_survey8.py --book 創 --chap 1 --model deepseek-v3.1:671b-cloud \
        --ollama-url http://sai.fhl.net:11434 --out
    python3 run_survey8.py --book 創 --chap 1 --sec 1 --dry-run
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(PARENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG, parse_sec_arg as parse_sec_spec
from shared.sn_shell import strip_shell, restore_shell, extract_bare_numbers

# Reuse from survey4
S4_DIR = os.path.join(PARENT_DIR, "survey4_self_supervised_prompt_tuning")
sys.path.insert(0, S4_DIR)
from auto_score import strip_sn, score_verse
from analyze_test_dimensions import extract_tags
from run_benchmark import call_ollama, call_claude_cli, call_gemini_cli

# Reuse qp.php from survey6
S6_DIR = os.path.join(PARENT_DIR, "survey6_original_lang_benchmark")
sys.path.insert(0, S6_DIR)
from run_survey6 import fetch_qp_verse, build_original_text, is_ot_book

DEFAULT_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey8_v0.1.md")


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


def build_sn_dict_stripped(qp_records, testament):
    """Build SN:word dictionary using stripped (bare) numbers.

    Format:
        7225: בְּרֵאשִׁית
        1254: בָּרָא
        430: אֱלֹהִים
    """
    lines = []
    for r in qp_records:
        # Strip the SN tag to bare number format
        bare = strip_shell(f"<{r['sn']}>")  # e.g. <WH07225> → <7225>
        # Remove angle brackets for dictionary display
        num = bare.strip("<>")
        lines.append(f"{num}: {r['word']}")
    return "\n".join(lines)


def build_example_stripped(example_text, testament):
    """Strip an example verse's SN tags to bare number format."""
    return strip_shell(example_text)


def build_survey8_prompt(system_prompt, example_stripped, sn_dict_stripped,
                         unv_plain, book_eng, chap, sec):
    """Build prompt: example + dict + target."""
    user = f"""Example — this verse already has SN numbers inserted:

{example_stripped}

SN number to original word dictionary for {book_eng} {chap}:{sec}:

{sn_dict_stripped}

Now insert the numbers from the dictionary into the correct positions in this verse:

{unv_plain}

Output only the annotated text."""
    return system_prompt, user


def main():
    parser = argparse.ArgumentParser(
        description="Survey8: Simplest SN benchmark")
    parser.add_argument("--book", default="創")
    parser.add_argument("--chap", default="1")
    parser.add_argument("--sec", nargs="+", default=None)
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

    prompt_file = args.prompt if args.prompt else DEFAULT_PROMPT_FILE
    system_prompt = load_prompt(prompt_file) if os.path.exists(prompt_file) else \
        "Insert SN numbers from the dictionary into the Chinese text."
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
            fname = f"s8_{scope}_{mshort}_{pver}_{ts}.json"
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

    print(f"Survey8: Simplest SN (去殼)")
    print(f"Book: {book_eng} ({book_chi})  {testament}")
    print(f"Model: {args.model} ({brand})")
    print(f"Prompt: {pver} ({len(system_prompt)} chars)")
    if done_refs:
        print(f"Resume: {len(done_refs)} verses already done")
    print()

    t0 = time.time()

    for chap in chapters:
        try:
            unv_data = fetch_chap_cached(book_chi, chap, "unv", strong=1)
        except Exception as e:
            print(f"  Fetch error {book_eng} {chap}: {e}")
            continue

        secs = sorted(unv_data.keys())
        if args.sec:
            wanted = set(parse_sec_spec(args.sec))
            secs = [s for s in secs if s in wanted]

        for sec in secs:
            ref = f"{book_eng} {chap}:{sec}"
            if ref in done_refs:
                continue

            unv_sn = unv_data[sec]          # ground truth (full format)
            unv_plain = strip_sn(unv_sn)    # plain text (no tags)
            gt_stripped = strip_shell(unv_sn)  # ground truth stripped

            # Fetch qp.php dictionary
            try:
                qp_records = fetch_qp_verse(book_eng, chap, sec)
            except Exception as e:
                print(f"  {ref:15s} qp.php ERROR: {e}")
                continue

            sn_dict = build_sn_dict_stripped(qp_records, testament)

            # Use previous verse as example (or first verse of chapter)
            example_sec = sec - 1 if sec > 1 and (sec - 1) in unv_data else secs[0]
            if example_sec == sec and len(secs) > 1:
                example_sec = secs[1] if secs[0] == sec else secs[0]
            example_stripped = strip_shell(unv_data.get(example_sec, unv_sn))

            if args.dry_run:
                print(f"{'─'*60}")
                print(f"{ref}  tags={len(extract_tags(unv_sn))}  qp={len(qp_records)}")
                print(f"  Example: {example_stripped[:80]}...")
                print(f"  Dict:    {sn_dict[:100]}...")
                print(f"  UNV:     {unv_plain[:80]}...")
                print(f"  GT strip:{gt_stripped[:80]}...")
                continue

            sys_p, user_p = build_survey8_prompt(
                system_prompt, example_stripped, sn_dict,
                unv_plain, book_eng, chap, sec)

            t_call = time.time()
            try:
                raw = call_model(args.model, brand, args.ollama_url, sys_p, user_p)
                output = clean_output(raw) if raw else ""
                dt = time.time() - t_call
                dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

                if dt < 5 and (not output or len(output.strip()) < 10):
                    print(f"  {ref:15s} ⚠ RATE LIMITED ({dt_str})")
                    continue

                # Score 1: stripped comparison (LLM placement)
                score1 = score_verse(output, gt_stripped)

                # Score 2: restore shell then compare with original GT
                output_shelled = restore_shell(output, testament)
                score2 = score_verse(output_shelled, unv_sn)

                print(f"  {ref:15s} "
                      f"S1 c={score1['coverage']:.2f}/p={score1['placement']:.2f}  "
                      f"S2 c={score2['coverage']:.2f}/p={score2['placement']:.2f}  "
                      f"fmt={score2['format']:.2f}  "
                      f"({dt_str})")

                results.append({
                    "ref": ref,
                    "unv_sn_count": len(extract_tags(unv_sn)),
                    "qp_word_count": len(qp_records),
                    "model_output": output,
                    "output_shelled": output_shelled,
                    "score1_stripped": score1,
                    "score2_shelled": score2,
                    "time": round(dt, 1),
                })

                # Incremental save
                if _out_path:
                    _save(results, _out_path, book_eng, args, brand, pver)

            except Exception as e:
                print(f"  {ref:15s} ERROR: {e}")

    if args.dry_run:
        if tee:
            tee.close()
        return

    # Summary
    scored = [r for r in results if "score1_stripped" in r]
    if scored:
        print(f"\n{'='*60}")
        print(f"  Survey8 Simplest SN — {book_eng}, {args.model}")
        print(f"{'='*60}")
        print(f"  Verses scored: {len(scored)}")
        for label, key in [("Score 1 (stripped)", "score1_stripped"),
                           ("Score 2 (shelled)", "score2_shelled")]:
            avg_c = sum(r[key]["coverage"] for r in scored) / len(scored)
            avg_p = sum(r[key]["placement"] for r in scored) / len(scored)
            exact = sum(1 for r in scored if r[key]["exact_match"])
            print(f"  {label}:")
            print(f"    cov={avg_c:.4f}  place={avg_p:.4f}  exact={exact}/{len(scored)}")
        print(f"  Time: {(time.time()-t0)/60:.1f} minutes")

    if _out_path:
        _save(results, _out_path, book_eng, args, brand, pver)
        print(f"\n  Saved to {_out_path}")

    if tee:
        tee.close()


def _save(results, out_path, book_eng, args, brand, pver):
    scored = [r for r in results if "score1_stripped" in r]
    out_data = {
        "meta": {
            "task": "survey8_simplest_sn",
            "book": book_eng,
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
