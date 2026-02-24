#!/usr/bin/env python3
"""
LLM-Direct Strong's Number Transfer: UNV → LCC

Uses Claude CLI (claude -p) to transfer Strong's Number annotations
from UNV (和合本, which has SN from FHL) to LCC (呂振中譯本, which has none).
No API key needed — uses your Claude Code subscription.

Usage:
    python llm_direct_sn_unv2lcc.py --book 創 --chap 1 --sec 1
    python llm_direct_sn_unv2lcc.py --book 創 --chap 1              # whole chapter
    python llm_direct_sn_unv2lcc.py --book 創 --chap 1 --dry-run    # preview only
    python llm_direct_sn_unv2lcc.py --book 創 --chap 1 --model opus # use opus
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import shutil
import subprocess

# Add repo root to path for shared imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from shared.data.book_data_loader import load_books

# ── FHL API ──────────────────────────────────────────────────────────────────

FHL_API = "https://bible.fhl.net/json/qb.php"

# Book data from shared/data/books.json
_books = load_books()
CHI_TO_ENG = _books["CHI_TO_ENG"]


def fetch_chap(book_chi: str, chap: int, version: str, strong: int = 0) -> dict:
    """Fetch a chapter from FHL API. Returns {sec: bible_text}."""
    params = urllib.parse.urlencode({
        "version": version,
        "chineses": book_chi,
        "chap": chap,
        "strong": strong
    })
    url = f"{FHL_API}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": "StrongNumberEmbedding/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    secs = {}
    for record in data.get("record", []):
        secs[record["sec"]] = record["bible_text"]
    return secs


def fetch_sec_pair(book_chi: str, chap: int, sec: int) -> tuple:
    """Fetch both UNV+SN and LCC for a single sec. Returns (unv_sn, lcc)."""
    unv_chap = fetch_chap(book_chi, chap, "unv", strong=1)
    lcc_chap = fetch_chap(book_chi, chap, "lcc", strong=0)

    unv_sn = unv_chap.get(sec)
    lcc = lcc_chap.get(sec)

    if not unv_sn:
        raise ValueError(f"UNV {book_chi} {chap}:{sec} not found")
    if not lcc:
        raise ValueError(f"LCC {book_chi} {chap}:{sec} not found")

    return unv_sn, lcc


# ── Prompt Construction ──────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a biblical Hebrew and Chinese translation expert. Your task is to transfer \
Strong's Number (SN) annotations from the Chinese Union Version (UNV/和合本) to the \
Lü Zhènzhōng Translation (LCC/呂振中譯本).

UNV already has SN tags from FHL (bible.fhl.net). LCC has none. You must insert the \
same SN tags into LCC text at the semantically correct positions.

## SN Tag Format (preserve exactly)

- `<WHdddd>` or `<WGdddd>` — Core Strong's number (H=Hebrew, G=Greek)
- `<WAHdddd>` — Strong's with prefix marker
- `<WTHdddd>` — Morphology code (8xxx series = verbal stems/tenses)
- `{<WHdddd>}` — Implicit marker (Hebrew word with no explicit Chinese translation)

## Rules

1. For each SN in UNV, find the semantically corresponding word/phrase in LCC and \
insert the SN tag immediately AFTER that word.
2. Morphology codes (`<WTH8xxx>`) always attach to the verb they describe.
3. If UNV has `{<...>}` (implicit) but LCC has an EXPLICIT word for it, drop the \
braces and attach as normal: `word<WHdddd>`.
4. If LCC has no explicit word for an implicit marker, keep the braces: `{<WHdddd>}`.
5. Words in LCC with no Hebrew/Greek equivalent (e.g., Chinese aspect particle 了) \
→ leave unannotated.
6. If one LCC phrase covers multiple Hebrew words, attach all their SNs to that phrase.
7. Preserve LCC's original text, punctuation, and word order exactly. Only INSERT tags.

## Response Format

Return ONLY a JSON object (no markdown fences):
{
  "lcc_sn": "the LCC text with SN tags inserted",
  "confidence": 0.95,
  "notes": ["brief note about any non-trivial alignment decisions"]
}

confidence: 0.0 to 1.0. Lower if word boundaries are ambiguous or LCC rephrases heavily."""


def build_user_prompt(unv_sn: str, lcc: str, book_chi: str, chap: int, sec: int) -> str:
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    return f"""\
Transfer Strong's Numbers from UNV to LCC for {book_eng} {chap}:{sec}.

UNV+SN: {unv_sn}
LCC:    {lcc}

Return the JSON with lcc_sn, confidence, and notes."""


# ── Claude CLI ───────────────────────────────────────────────────────────────

JSON_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "lcc_sn": {"type": "string", "description": "LCC text with SN tags inserted"},
        "confidence": {"type": "number", "description": "Confidence score 0.0-1.0"},
        "notes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Notes about non-trivial alignment decisions"
        }
    },
    "required": ["lcc_sn", "confidence", "notes"]
})


def call_claude(model: str, unv_sn: str, lcc: str,
                book_chi: str, chap: int, sec: int,
                verbose: bool = True) -> dict:
    """Call claude CLI to insert SNs into LCC. Returns parsed JSON response."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        raise RuntimeError("'claude' CLI not found in PATH")

    prompt = SYSTEM_PROMPT + "\n\n" + build_user_prompt(unv_sn, lcc, book_chi, chap, sec)

    if verbose:
        print(f"  ── prompt ──")
        print(f"  {prompt}")
        print(f"  ── /prompt ──")

    cmd = [
        claude_bin, "-p",
        "--output-format", "json",
        "--json-schema", JSON_SCHEMA,
        "--model", model,
        "--no-session-persistence",
        "--disallowed-tools", "Bash,Edit,Write,Read,Glob,Grep,Task",
    ]

    if verbose:
        print(f"  [claude {model}] calling... (timeout 300s)", flush=True)

    # Clear CLAUDECODE env var to allow running from within a Claude Code session
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    result_proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=300, env=env,
        input=prompt
    )

    if result_proc.returncode != 0:
        stderr = result_proc.stderr.strip()
        return {
            "lcc_sn": "",
            "confidence": 0.0,
            "notes": [f"claude CLI error: {stderr[:300]}"],
            "error": True
        }

    raw = result_proc.stdout.strip()

    try:
        outer = json.loads(raw)

        # claude --output-format json returns an array of message objects
        # Find the last assistant message with type "result"
        if isinstance(outer, list):
            for msg in reversed(outer):
                if msg.get("type") == "result":
                    inner = msg.get("result", "")
                    if isinstance(inner, str):
                        return json.loads(inner)
                    elif isinstance(inner, dict):
                        return inner
            # Fallback: try to find lcc_sn in any text content
            for msg in reversed(outer):
                if msg.get("type") == "assistant":
                    text = ""
                    for block in msg.get("message", {}).get("content", []):
                        if block.get("type") == "text":
                            text = block.get("text", "")
                    if text:
                        return json.loads(text)

        elif isinstance(outer, dict):
            if "result" in outer:
                inner = outer["result"]
                if isinstance(inner, str):
                    return json.loads(inner)
                return inner
            if "lcc_sn" in outer:
                return outer

    except (json.JSONDecodeError, KeyError, TypeError):
        pass

    # Last resort: regex extract
    match = re.search(r'\{[^{}]*"lcc_sn"\s*:', raw, re.DOTALL)
    if match:
        # Find the matching closing brace
        start = match.start()
        depth = 0
        for i, c in enumerate(raw[start:], start):
            if c == '{': depth += 1
            elif c == '}': depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start:i+1])
                except json.JSONDecodeError:
                    break

    return {
        "lcc_sn": "",
        "confidence": 0.0,
        "notes": [f"Failed to parse response: {raw[:300]}"],
        "error": True
    }


# ── Output ───────────────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")


def save_result(result: dict, book_chi: str, book_eng: str,
                chap: int, sec: int, model: str,
                unv_sn: str, lcc: str) -> str:
    """Save result to output/{Book}/{chap}/{sec}.json. Returns file path."""
    sec_dir = os.path.join(OUTPUT_DIR, book_eng, str(chap))
    os.makedirs(sec_dir, exist_ok=True)

    output = {
        "book": book_eng,
        "book_chi": book_chi,
        "chap": chap,
        "sec": sec,
        "lcc_sn": result.get("lcc_sn", ""),
        "lcc_original": lcc,
        "unv_sn_reference": unv_sn,
        "confidence": result.get("confidence", 0.0),
        "notes": result.get("notes", []),
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    file_path = os.path.join(sec_dir, f"{sec}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return file_path


# ── Verification ─────────────────────────────────────────────────────────────

def count_sns(text: str) -> list:
    """Extract all SN codes from text (both explicit and implicit)."""
    # Match all SN patterns: <WHdddd>, <WAHdddd>, <WTHdddd>, {<WHdddd>}, etc.
    pattern = r'(?:\{)?<W[ATH]*([HG]?\d+)>(?:\})?'
    return re.findall(pattern, text)


def verify_sn_coverage(unv_sn: str, lcc_sn: str) -> dict:
    """Check that all SNs from UNV appear in LCC+SN output."""
    unv_sns = sorted(count_sns(unv_sn))
    lcc_sns = sorted(count_sns(lcc_sn))

    missing = []
    extra = []

    unv_counts = {}
    for sn in unv_sns:
        unv_counts[sn] = unv_counts.get(sn, 0) + 1

    lcc_counts = {}
    for sn in lcc_sns:
        lcc_counts[sn] = lcc_counts.get(sn, 0) + 1

    for sn, count in unv_counts.items():
        lcc_count = lcc_counts.get(sn, 0)
        if lcc_count < count:
            missing.extend([sn] * (count - lcc_count))

    for sn, count in lcc_counts.items():
        unv_count = unv_counts.get(sn, 0)
        if count > unv_count:
            extra.extend([sn] * (count - unv_count))

    return {
        "unv_count": len(unv_sns),
        "lcc_count": len(lcc_sns),
        "missing": missing,
        "extra": extra,
        "perfect": len(missing) == 0 and len(extra) == 0
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def process_sec(model: str, book_chi: str,
                chap: int, sec: int, dry_run: bool = False,
                verbose: bool = True) -> dict:
    """Process a single sec. Returns the result dict."""
    book_eng = CHI_TO_ENG.get(book_chi)
    if not book_eng:
        print(f"  ✗ Unknown book: {book_chi}", file=sys.stderr)
        return None

    try:
        unv_sn, lcc = fetch_sec_pair(book_chi, chap, sec)
    except ValueError as e:
        print(f"  ✗ {e}", file=sys.stderr)
        return None

    print(f"  UNV+SN: {unv_sn}")
    print(f"  LCC:    {lcc}")

    if dry_run:
        print("  [dry-run] Skipping claude call")
        return {"lcc_sn": "", "confidence": 0.0, "notes": ["dry-run"]}

    try:
        result = call_claude(model, unv_sn, lcc, book_chi, chap, sec,
                             verbose=verbose)
    except subprocess.TimeoutExpired:
        print(f"  ✗ Timed out (300s)")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

    # Verify SN coverage
    if result.get("lcc_sn"):
        verify = verify_sn_coverage(unv_sn, result["lcc_sn"])
        if not verify["perfect"]:
            if verify["missing"]:
                result.setdefault("notes", []).append(
                    f"Missing SNs: {', '.join(verify['missing'])}"
                )
            if verify["extra"]:
                result.setdefault("notes", []).append(
                    f"Extra SNs: {', '.join(verify['extra'])}"
                )
            print(f"  ⚠ SN mismatch: {verify['unv_count']} UNV → {verify['lcc_count']} LCC"
                  f" (missing: {verify['missing']}, extra: {verify['extra']})")

    print(f"  LCC+SN: {result.get('lcc_sn', '(empty)')}")
    print(f"  Conf:   {result.get('confidence', 0.0)}")
    if result.get("notes"):
        for note in result["notes"]:
            print(f"  Note:   {note}")

    # Save
    file_path = save_result(result, book_chi, book_eng, chap, sec,
                            model, unv_sn, lcc)
    print(f"  Saved:  {file_path}")

    return result


def parse_chap_arg(chap_str: str, book_chi: str) -> list:
    """Parse --chap argument into list of chapter numbers.

    Supports: "5" (single), "1-10" (range), "all" (all chapters from books.json).
    """
    if chap_str.lower() == "all":
        chapters_count = _books["CHAPTERS"].get(CHI_TO_ENG.get(book_chi, ""), 0)
        if chapters_count == 0:
            print(f"Error: Cannot determine chapter count for '{book_chi}'", file=sys.stderr)
            sys.exit(1)
        return list(range(1, chapters_count + 1))

    if "-" in chap_str:
        parts = chap_str.split("-", 1)
        try:
            start, end = int(parts[0]), int(parts[1])
        except ValueError:
            print(f"Error: Invalid chapter range '{chap_str}'", file=sys.stderr)
            sys.exit(1)
        if start < 1 or end < start:
            print(f"Error: Invalid range {start}-{end}", file=sys.stderr)
            sys.exit(1)
        return list(range(start, end + 1))

    try:
        return [int(chap_str)]
    except ValueError:
        print(f"Error: Invalid chapter '{chap_str}'", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="LLM-Direct Strong's Number Transfer: UNV → LCC"
    )
    parser.add_argument("--chineses", "--book", required=False, dest="chineses",
                        help="Chinese book abbreviation (e.g., 創, 出, 詩)")
    parser.add_argument("--chap", required=False, type=str,
                        help="Chapter: single (1), range (1-10), or 'all'")
    parser.add_argument("--list-books", action="store_true",
                        help="List all 66 book abbreviations and exit")
    parser.add_argument("--sec", type=int, default=None,
                        help="Section/verse number (omit for whole chapter)")
    parser.add_argument("--model", default="opus",
                        help="Claude model (default: opus; alternatives: sonnet, haiku)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch data but skip claude calls")
    parser.add_argument("--force", action="store_true",
                        help="Reprocess all verses, overwrite existing files")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress prompt and claude command details")
    args = parser.parse_args()

    if args.list_books:
        books = load_books()["ALL"]
        print("Book abbreviations (66 books):\n")
        print("  ── Old Testament (39) ──")
        for i, b in enumerate(books[:39]):
            print(f"  {b['chi']:>3}  {b['eng']:<6} {b['chiLong']} ({b['engLong']}, {b['chapters']} ch)")
        print("\n  ── New Testament (27) ──")
        for b in books[39:]:
            print(f"  {b['chi']:>3}  {b['eng']:<6} {b['chiLong']} ({b['engLong']}, {b['chapters']} ch)")
        sys.exit(0)

    if not args.chineses or not args.chap:
        parser.error("--chineses and --chap are required (or use --list-books)")

    book_chi = args.chineses
    book_eng = CHI_TO_ENG.get(book_chi)
    if not book_eng:
        print(f"Error: Unknown book abbreviation '{book_chi}'", file=sys.stderr)
        print(f"Valid: {', '.join(sorted(CHI_TO_ENG.keys()))}", file=sys.stderr)
        sys.exit(1)

    chapters = parse_chap_arg(args.chap, book_chi)
    chap_label = f"{chapters[0]}-{chapters[-1]}" if len(chapters) > 1 else str(chapters[0])

    print(f"═══ LLM-Direct SN Transfer: {book_eng} ({book_chi}) Chap {chap_label} ═══")
    print(f"Model: {args.model}")
    if not args.force:
        print(f"Skip existing: ON (use --force to reprocess)")

    if not args.dry_run:
        if not shutil.which("claude"):
            print("Error: 'claude' CLI not found in PATH.", file=sys.stderr)
            sys.exit(1)

    start_time = time.time()
    total_processed = 0
    total_skipped = 0
    total_failed = 0

    for chap in chapters:
        if args.sec and len(chapters) == 1:
            # Single verse mode
            secs = [args.sec]
        else:
            # Whole chapter — fetch UNV to get sec list
            print(f"\nFetching verse list for {book_eng} {chap}...")
            try:
                unv_data = fetch_chap(book_chi, chap, "unv", strong=1)
                secs = sorted(unv_data.keys())
            except Exception as e:
                print(f"  Error fetching chapter {chap}: {e}")
                continue
            if not secs:
                print(f"  No verses found for chapter {chap}, skipping")
                continue
            print(f"── {book_eng} {chap} ({len(secs)} verses) ──")

        chap_processed = 0
        chap_skipped = 0
        chap_failed = 0

        for i, s in enumerate(secs):
            # Skip existing files unless --force
            if not args.force:
                out_path = os.path.join(OUTPUT_DIR, book_eng, str(chap), f"{s}.json")
                if os.path.isfile(out_path):
                    chap_skipped += 1
                    total_skipped += 1
                    if len(secs) <= 5 or (i + 1) == len(secs):
                        print(f"  {chap}:{s} skipped (exists)")
                    elif chap_skipped == 1:
                        print(f"  {chap}:{s} skipped (exists)...", end="", flush=True)
                    continue

            print(f"\n  ── {book_eng} {chap}:{s} ({i+1}/{len(secs)}) ──")
            result = process_sec(args.model, book_chi, chap, s,
                                 dry_run=args.dry_run,
                                 verbose=not args.quiet)
            if result and result.get("lcc_sn"):
                chap_processed += 1
                total_processed += 1
            else:
                chap_failed += 1
                total_failed += 1

            # Rate limiting between API calls
            if not args.dry_run and i < len(secs) - 1:
                time.sleep(0.5)

        if len(chapters) > 1 or len(secs) > 1:
            print(f"\n  Chapter {chap}: {chap_processed} processed, "
                  f"{chap_skipped} skipped, {chap_failed} failed")

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    total = total_processed + total_skipped + total_failed
    print(f"\n═══ Done: {total_processed}/{total} processed, "
          f"{total_skipped} skipped, {total_failed} failed "
          f"({minutes}m {seconds}s) ═══")


if __name__ == "__main__":
    main()
