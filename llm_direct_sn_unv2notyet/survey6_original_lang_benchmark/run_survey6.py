#!/usr/bin/env python3
"""Survey6: Original-language anchored SN transfer benchmark.

主任務: KJV plain + Original (Heb/Grk) + KJV+SN + SN:word dict + UNV plain → UNV+SN
  Original text and SN:word dict are fetched from FHL qp.php.
  Scored against FHL UNV+SN ground truth.

Two-pass mode (--two-pass):
  Pass 1: S5-style (KJV plain + KJV+SN + UNV plain → UNV+SN draft) — strong coverage
  Pass 2: Refine (draft + Original + SN:word dict + KJV+SN → UNV+SN) — fix placement

Usage:
    # Gen 1:1
    python3 run_survey6.py --book 創 --chap 1 --sec 1 --model sonnet

    # Full chapter
    python3 run_survey6.py --book 創 --chap 1 --model sonnet

    # Two-pass mode
    python3 run_survey6.py --book 創 --chap 1 --model sonnet --two-pass

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
DEFAULT_REFINE_PROMPT_FILE = os.path.join(SCRIPT_DIR, "prompts", "survey6_refine_v0.4.md")

# S5 prompt for two-pass Pass 1
S5_DIR = os.path.join(PARENT_DIR, "survey5_bilingual_sn_benchmark")
DEFAULT_S5_PROMPT_FILE = os.path.join(S5_DIR, "prompts", "survey5_v0.2.md")

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


def build_tag_inventory(kjv_sn: str) -> str:
    """Extract all SN tags from KJV+SN as a numbered checklist.

    Gives the model an explicit list of every tag that must appear in the output,
    with exact format (braces, prefix, zero-padding) preserved.
    """
    tags = extract_tags(kjv_sn)
    lines = []
    for i, t in enumerate(tags, 1):
        lines.append(f"  {i}. {t['raw']}")
    count = len(tags)
    return (f"Tag inventory ({count} tags — every one MUST appear in your output):\n"
            + "\n".join(lines)
            + f"\n\nTotal: {count} tags. Your output must contain at least {count} SN tags"
            + " (plus any 900x prefixes UNV needs).")


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


def strip_explanation(text):
    """Keep only the first block of annotated text, discard trailing explanation.

    Models (especially sonnet) sometimes append notes/explanations after the
    annotated verse. We take everything up to the first blank line or markdown
    separator (---, **, ##) that follows actual content.
    """
    lines = text.strip().split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        # Stop at blank line or any non-verse content
        if result and (stripped == ""
                       or stripped.startswith("---")
                       or stripped.startswith("**")
                       or stripped.startswith("##")
                       or stripped.startswith("```")
                       or stripped.startswith("Projection")
                       or stripped.startswith("Correction")
                       or stripped.startswith("Note")
                       or stripped.startswith("I ")
                       or stripped.startswith("The ")
                       or stripped.startswith("Here")
                       or stripped.startswith("Tag")
                       or stripped.startswith("Changes")
                       or re.match(r'^[A-Z][a-z]', stripped)):
            break
        result.append(line)
    return "\n".join(result).strip()


def call_model(model, brand, ollama_url, sys_p, user_p):
    if brand == "ollama":
        raw = call_ollama(model, sys_p, user_p, ollama_url)
    elif brand == "claude":
        raw = call_claude_cli(model, sys_p, user_p)
    elif brand == "gemini":
        raw = call_gemini_cli(model, sys_p, user_p)
    else:
        raw = ""
    return strip_explanation(raw)


def build_survey6_prompt(system_prompt, kjv_plain, orig_text, kjv_sn,
                         sn_word_dict, tag_inventory, unv_plain,
                         book_eng, chap, sec):
    """主任務: KJV plain + Original + KJV+SN + SN:word dict + Tag inventory + UNV plain → UNV+SN."""
    user = f"""Here is {book_eng} {chap}:{sec} in KJV (plain, no tags):

{kjv_plain}

Here is the same verse in the original language (Hebrew/Greek):

{orig_text}

Here is the same verse in KJV with Strong's Number annotations:

{kjv_sn}

Strong's Number to original word dictionary (for embedding reference — use this to confirm which UNV word carries each SN tag):

{sn_word_dict}

{tag_inventory}

Here is the same verse in UNV (和合本), plain, no annotations:

{unv_plain}

Using the KJV annotation pair, the SN:word dictionary, and the tag inventory above as your reference, embed every tag from the inventory into the correct positions in the UNV text. Output only the annotated UNV text."""
    return system_prompt, user


def build_pass1_prompt(system_prompt, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec):
    """Pass 1 (S5-style): KJV plain + KJV+SN + UNV plain → UNV+SN draft."""
    user = f"""Here is {book_eng} {chap}:{sec} in KJV (plain, no tags):

{kjv_plain}

Here is the same verse in KJV with Strong's Number annotations:

{kjv_sn}

Here is the same verse in UNV (和合本), plain, no annotations:

{unv_plain}

Using the KJV annotation pair above as your reference, insert the Strong's Number tags into the correct positions in the UNV text. Output only the annotated UNV text."""
    return system_prompt, user


def build_refine_prompt(system_prompt, draft, orig_text, sn_word_dict, kjv_sn,
                        book_eng, chap, sec):
    """Pass 2 (refine): UNV+SN draft + Original + dict + KJV+SN → corrected UNV+SN."""
    user = f"""Here is a draft of {book_eng} {chap}:{sec} in UNV (和合本) with SN tags already inserted (some may be misplaced):

{draft}

Here is the same verse in the original language (Hebrew/Greek):

{orig_text}

Strong's Number to original word dictionary (tells you which original word each SN represents):

{sn_word_dict}

Here is the same verse in KJV with Strong's Number annotations (for cross-reference):

{kjv_sn}

Correct the placement of SN tags in the draft. Move any misplaced tags to their correct positions. Do NOT remove or add any tags — only reposition them. Output only the corrected UNV text with tags."""
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
    parser.add_argument("--single-pass", action="store_true",
                        help="Single-pass mode (S6 v0.1 style). Default is two-pass.")
    parser.add_argument("--match-only", action="store_true",
                        help="Only run verses where KJV SN count = UNV SN count")
    parser.add_argument("--max-diff", type=int, default=None,
                        help="Max SN count diff to include (e.g., 2)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", nargs="?", const="", default=None,
                        help="Save results JSON. No value = auto-generate filename.")
    args = parser.parse_args()
    two_pass = not args.single_pass

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    brand = detect_brand(args.model, args.ollama_url)

    if two_pass:
        # Pass 1: S5 prompt, Pass 2: refine prompt
        s5_prompt_file = args.prompt if args.prompt else DEFAULT_S5_PROMPT_FILE
        if os.path.exists(s5_prompt_file):
            pass1_prompt = load_prompt(s5_prompt_file)
        else:
            pass1_prompt = "Transfer Strong's Number tags from KJV to UNV."
            s5_prompt_file = None

        refine_prompt_file = DEFAULT_REFINE_PROMPT_FILE
        if os.path.exists(refine_prompt_file):
            pass2_prompt = load_prompt(refine_prompt_file)
        else:
            pass2_prompt = "Correct SN tag placement using original language reference."

        pver = "2pass"
        prompt_file = s5_prompt_file  # for header display
        system_prompt = pass1_prompt  # for header display
    else:
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
        json_path = make_out_path("s6-2p" if two_pass else "s6fwd", book_eng, args.chap, args.model, pver, "json") \
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

    mode_label = "Two-pass (S5→Refine)" if two_pass else "Single-pass (S6)"
    print(f"Survey6: {mode_label}")
    print(f"Book: {book_eng} ({book_chi})  OT={'Yes' if is_ot_book(book_eng) else 'No'}")
    print(f"Model: {args.model} ({brand})")
    if two_pass:
        print(f"Pass 1 prompt: {len(pass1_prompt)} chars (S5)")
        print(f"Pass 2 prompt: {len(pass2_prompt)} chars (refine)")
    else:
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
            tag_inventory = build_tag_inventory(kjv_sn)

            if args.dry_run:
                print(f"{'─'*60}")
                print(f"{ref}  KJV={kjv_count} UNV={unv_count} diff={diff}  qp={len(qp_records)} words")
                print(f"  KJV:    {kjv_plain[:80]}...")
                print(f"  Orig:   {orig_text[:80]}...")
                print(f"  KJV+SN: {kjv_sn[:80]}...")
                print(f"  Dict:   {sn_word_dict[:120]}...")
                print(f"  UNV:    {unv_plain[:80]}...")
                if two_pass:
                    print(f"  Mode:   two-pass (S5 → refine)")
                continue

            t_call = time.time()
            try:
                if two_pass:
                    # Pass 1: S5-style (good coverage)
                    sys_p1, user_p1 = build_pass1_prompt(
                        pass1_prompt, kjv_plain, kjv_sn, unv_plain,
                        book_eng, chap, sec)
                    draft = call_model(args.model, brand, args.ollama_url,
                                       sys_p1, user_p1)

                    if not draft or len(draft.strip()) < 10:
                        dt = time.time() - t_call
                        print(f"  {ref:15s} ⚠ Pass 1 empty ({int(dt)}s)")
                        continue

                    p1_score = score_verse(draft, unv_sn)

                    # Pass 2: Refine placement with original text
                    sys_p2, user_p2 = build_refine_prompt(
                        pass2_prompt, draft, orig_text, sn_word_dict,
                        kjv_sn, book_eng, chap, sec)
                    output = call_model(args.model, brand, args.ollama_url,
                                        sys_p2, user_p2)

                    # Fallback: if P2 output is empty or tag count diverges
                    # too much from P1, P2 probably corrupted — use P1
                    p1_tags = len(extract_tags(draft))
                    p2_tags = len(extract_tags(output)) if output else 0
                    if not output or len(output.strip()) < 10 or \
                       (p1_tags > 0 and abs(p2_tags - p1_tags) > p1_tags * 0.5):
                        output = draft

                    dt = time.time() - t_call
                    dt_str = f"{int(dt)//60}m{int(dt)%60:02d}s"

                    score = score_verse(output, unv_sn)

                    # Show both passes
                    print(f"  {ref:15s} "
                          f"P1 c={p1_score['coverage']:.2f}/p={p1_score['placement']:.2f}  "
                          f"P2 c={score['coverage']:.2f}/p={score['placement']:.2f}  "
                          f"fmt={score['format']:.2f}  "
                          f"KJV={kjv_count} UNV={unv_count} diff={diff}  "
                          f"({dt_str})")

                    results.append({
                        "ref": ref,
                        "kjv_sn_count": kjv_count,
                        "unv_sn_count": unv_count,
                        "diff": diff,
                        "qp_word_count": len(qp_records),
                        "pass1_output": draft,
                        "pass1_score": p1_score,
                        "model_output": output,
                        "score": score,
                        "time": round(dt, 1),
                    })
                else:
                    # Single-pass (original S6 v0.1 style)
                    sys_p, user_p = build_survey6_prompt(
                        system_prompt, kjv_plain, orig_text, kjv_sn,
                        sn_word_dict, tag_inventory, unv_plain,
                        book_eng, chap, sec)
                    output = call_model(args.model, brand, args.ollama_url,
                                        sys_p, user_p)
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
                "task": "survey6_two_pass" if two_pass else "survey6_kjv_orig_to_unv",
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
