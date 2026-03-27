#!/usr/bin/env python3
"""Survey6: Original-language anchored SN transfer benchmark.

主任務: KJV plain + Original (Heb/Grk) + KJV+SN + SN:word dict + UNV plain → UNV+SN
  Original text and SN:word dict are fetched from FHL qp.php.
  Scored against FHL UNV+SN ground truth.

Usage:
    # Gen 1:1
    python3 run_survey6.py --book 創 --chap 1 --sec 1 --model sonnet

    # Full chapter
    python3 run_survey6.py --book 創 --chap 1 --model sonnet

    # Ollama
    python3 run_survey6.py --book 創 --chap 1 \\
        --model deepseek-v3.1:671b-cloud --ollama-url http://sai.fhl.net:11434

    # Dry run
    python3 run_survey6.py --book 創 --chap 1 --sec 1 --dry-run
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request


class Tee:
    """Write stdout to both terminal and a log file simultaneously."""
    def __init__(self, log_path):
        self._terminal = sys.stdout
        self._log = open(log_path, "w", encoding="utf-8", buffering=1)

    def write(self, msg):
        self._terminal.write(msg)
        self._log.write(msg)

    def flush(self):
        self._terminal.flush()
        self._log.flush()

    def close(self):
        sys.stdout = self._terminal
        self._log.close()


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG, parse_sec_arg as parse_sec_spec

# Reuse from survey4
S4_DIR = os.path.join(PARENT_DIR, "survey4_self_supervised_prompt_tuning")
sys.path.insert(0, S4_DIR)
from auto_score import strip_sn, score_verse
from analyze_test_dimensions import extract_tags
from run_benchmark import (call_ollama, call_claude_cli, call_gemini_cli)

DEFAULT_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey6_v0.1.md")

FHL_QP_API = "https://bible.fhl.net/json/qp.php"

# OT book names (index 0–38 in books.json = Gen … Mal)
_books_data = None

def _load_book_order():
    global _books_data
    if _books_data is None:
        repo_root = os.path.dirname(PARENT_DIR)
        books_json = os.path.join(repo_root, "shared", "data", "books.json")
        with open(books_json, encoding="utf-8") as f:
            _books_data = json.load(f)
    return _books_data


def is_ot_book(book_eng: str) -> bool:
    """Return True if book_eng is an Old Testament book (Gen–Mal)."""
    books = _load_book_order()
    for i, b in enumerate(books):
        if b["eng"] == book_eng:
            return i <= 38
    return True  # default OT if unknown


def normalize_qp_sn(sn_str: str, ot: bool) -> str:
    """Convert qp.php 5-digit sn to FHL tag body (e.g. '00430' → 'WH0430').

    Rule: if sn starts with '00', strip one leading zero.
    Then prepend WH (OT) or WG (NT).
    """
    s = sn_str.strip()
    if s.startswith("00"):
        s = s[1:]           # "00430" → "0430"
    prefix = "WH" if ot else "WG"
    return f"{prefix}{s}"


# Cache for qp verse data: {(book_eng, chap, sec): [{wid, word, sn}, ...]}
_qp_cache = {}


def fetch_qp_verse(book_eng: str, chap: int, sec: int) -> list:
    """Fetch per-word original-language data from qp.php.

    Returns list of dicts with keys: wid, word, sn (normalized tag body).
    wid=0 (verse summary) is skipped.
    """
    key = (book_eng, chap, sec)
    if key in _qp_cache:
        return _qp_cache[key]

    params = urllib.parse.urlencode({
        "engs": book_eng,
        "chap": chap,
        "sec": sec,
    })
    url = f"{FHL_QP_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "StrongNumberEmbedding/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    ot = is_ot_book(book_eng)
    records = []
    for entry in raw.get("record", raw) if isinstance(raw, dict) else raw:
        if entry.get("wid", 0) == 0:
            continue
        word = entry.get("word", "").strip()
        sn_raw = entry.get("sn", "").strip()
        if not word or not sn_raw:
            continue
        sn_tag = normalize_qp_sn(sn_raw, ot)
        records.append({"wid": entry["wid"], "word": word, "sn": sn_tag})

    _qp_cache[key] = records
    return records


def build_sn_word_dict(qp_records: list) -> str:
    """Build the SN:word dictionary string from qp records.

    Format:
        WH07225: בְּרֵאשִׁית
        WH01254: בָּרָא
        WH0430: אֱלֹהִים
    """
    lines = []
    for r in qp_records:
        lines.append(f"{r['sn']}: {r['word']}")
    return "\n".join(lines)


def build_original_text(qp_records: list) -> str:
    """Join word fields from qp records to form the original-language text."""
    return " ".join(r["word"] for r in qp_records)


def load_prompt(path):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def model_short_name(model):
    """Sanitize model name for use in filenames (replace : and / with -)."""
    return re.sub(r'[:/\\]', '-', model)


def prompt_version(prompt_path):
    """Extract version string from prompt filename, e.g. survey6_v0.1.md → v0.1"""
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


def build_survey6_prompt(system_prompt, kjv_plain, orig_text, kjv_sn,
                         sn_word_dict, unv_plain, book_eng, chap, sec):
    """主任務: KJV plain + Original + KJV+SN + SN:word dict + UNV plain → UNV+SN."""
    user = f"""Here is {book_eng} {chap}:{sec} in KJV (plain, no tags):

{kjv_plain}

Here is the same verse in the original language (Hebrew/Greek):

{orig_text}

Here is the same verse in KJV with Strong's Number annotations:

{kjv_sn}

Strong's Number to original word dictionary (for embedding reference — use this to confirm which UNV word carries each SN tag):

{sn_word_dict}

Here is the same verse in UNV (和合本), plain, no annotations:

{unv_plain}

Using the KJV annotation pair and the SN:word dictionary above as your reference, insert the Strong's Number tags into the correct positions in the UNV text. Output only the annotated UNV text."""
    return system_prompt, user


def print_summary(results, book_eng, model, t0):
    scored = [r for r in results if "score" in r]
    if not scored:
        return
    print(f"\n{'='*60}")
    print(f"  Survey6 KJV+Orig→UNV — {book_eng}, {model}")
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
        description="Survey6: Original-language anchored KJV→UNV SN benchmark")
    parser.add_argument("--book", default="創")
    parser.add_argument("--chap", default="1")
    parser.add_argument("--sec", nargs="+", default=None,
                        help="Verse(s) to run, e.g. 1 or 1-5 or 1,3,5-8")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--ollama-url", default=None)
    parser.add_argument("--prompt", default=None,
                        help="Override system prompt file")
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

    prompt_file = args.prompt if args.prompt else DEFAULT_PROMPT_FILE
    if os.path.exists(prompt_file):
        system_prompt = load_prompt(prompt_file)
    else:
        system_prompt = "Transfer Strong's Number tags from KJV to UNV using the original language dictionary."
        prompt_file = None

    pver = prompt_version(prompt_file) if prompt_file else "vunk"

    # Start tee logging if --out requested
    tee = None
    json_path = None
    if args.out is not None and not args.dry_run:
        json_path = make_out_path("s6fwd", book_eng, args.chap, args.model, pver, "json") \
            if args.out == "" else \
            (os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out)
        log_path = re.sub(r'\.json$', '.log', json_path)
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        tee = Tee(log_path)
        sys.stdout = tee
        print(f"Log: {log_path}")

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

    print(f"Survey6: KJV+Orig+Dict → UNV (主任務)")
    print(f"Book: {book_eng} ({book_chi})  OT={'Yes' if is_ot_book(book_eng) else 'No'}")
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
            wanted = set(parse_sec_spec(args.sec))
            secs = [s for s in secs if s in wanted]

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

            # Fetch qp.php data for this verse
            try:
                qp_records = fetch_qp_verse(book_eng, chap, sec)
            except Exception as e:
                print(f"  {ref:15s} qp.php ERROR: {e}")
                continue

            orig_text = build_original_text(qp_records)
            sn_word_dict = build_sn_word_dict(qp_records)

            if args.dry_run:
                print(f"{'─'*60}")
                print(f"{ref}  KJV={kjv_count} UNV={unv_count} diff={diff}  qp={len(qp_records)} words")
                print(f"  KJV:    {kjv_plain[:80]}...")
                print(f"  Orig:   {orig_text[:80]}...")
                print(f"  KJV+SN: {kjv_sn[:80]}...")
                print(f"  Dict:   {sn_word_dict[:120]}...")
                print(f"  UNV:    {unv_plain[:80]}...")
                continue

            sys_p, user_p = build_survey6_prompt(
                system_prompt, kjv_plain, orig_text, kjv_sn,
                sn_word_dict, unv_plain, book_eng, chap, sec)

            t_call = time.time()
            try:
                output = call_model(args.model, brand, args.ollama_url, sys_p, user_p)
                dt = time.time() - t_call
                dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

                if dt < 5 and (not output or len(output.strip()) < 10):
                    print(f"  {ref:15s} ⚠ RATE LIMITED ({dt_str})")
                    continue

                score = score_verse(output, unv_sn)

                print(f"  {ref:15s} cov={score['coverage']:.2f} "
                      f"place={score['placement']:.2f} "
                      f"fmt={score['format']:.2f} "
                      f"exact={score['exact_match']}  "
                      f"KJV={kjv_count} UNV={unv_count} diff={diff}  "
                      f"({dt_str})")

                results.append({
                    "ref": ref,
                    "kjv_sn_count": kjv_count,
                    "unv_sn_count": unv_count,
                    "diff": diff,
                    "qp_word_count": len(qp_records),
                    "model_output": output,
                    "score": score,
                    "time": round(dt, 1),
                })

            except Exception as e:
                print(f"  {ref:15s} ERROR: {e}")

    if args.dry_run:
        return

    print_summary(results, book_eng, args.model, t0)

    # Save
    if args.out is not None:
        if json_path is None:
            json_path = make_out_path("s6fwd", book_eng, args.chap,
                                     args.model, pver, "json") \
                if args.out == "" else \
                (os.path.join(SCRIPT_DIR, args.out) if not os.path.isabs(args.out) else args.out)
            os.makedirs(os.path.dirname(json_path), exist_ok=True)

        scored = [r for r in results if "score" in r]
        out_data = {
            "meta": {
                "task": "survey6_kjv_orig_to_unv",
                "book": book_eng,
                "model": args.model,
                "brand": brand,
                "prompt_version": pver,
                "match_only": args.match_only,
                "max_diff": args.max_diff,
                "total_scored": len(scored),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "verses": results,
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False, indent=1)
        print(f"\n  Saved to {json_path}")

    if tee:
        tee.close()


if __name__ == "__main__":
    main()
