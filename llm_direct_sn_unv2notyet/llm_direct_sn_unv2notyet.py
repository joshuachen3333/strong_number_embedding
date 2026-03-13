#!/usr/bin/env python3
"""
LLM-Direct Strong's Number Transfer: UNV → Target Version

Uses Claude CLI (claude -p) to transfer Strong's Number annotations
from UNV (和合本, which has SN from FHL) to a target Bible version (default: LCC).
No API key needed — uses your Claude Code subscription.

Usage:
    python3 llm_direct_sn_unv2notyet.py --book 創 --chap 1 --sec 1
    python3 llm_direct_sn_unv2notyet.py --book 創 --chap 1 --target-version rcuv2010
    python3 llm_direct_sn_unv2notyet.py --set-target-version rcuv2010   # persist default
    python3 llm_direct_sn_unv2notyet.py --book 創 --chap 1 --dry-run
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

import shutil
import subprocess

# Add repo root to path for shared imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from shared.data.book_data_loader import load_books

# ── Duration / time parsing ──────────────────────────────────────────────────

_DURATION_RE = re.compile(
    r'^\s*(\d+(?:\.\d+)?)\s*(h|hr|hrs|hour|hours|m|min|mins|minute|minutes)\s*$',
    re.IGNORECASE
)
_CLOCK_RE = re.compile(r'^\s*(\d{1,2}):(\d{2})\s*$')


def parse_time_spec(s: str, label: str = "--till") -> float:
    """Parse a time specification to a timestamp (seconds since epoch).

    Accepts duration ('30min', '1.5hr') or clock time ('17:50', '21:00').
    Clock times must be in the future; if the time has passed today, it's rejected.
    """
    # Try clock time first (HH:MM)
    cm = _CLOCK_RE.match(s)
    if cm:
        hour, minute = int(cm.group(1)), int(cm.group(2))
        if hour > 23 or minute > 59:
            print(f"Error: Invalid time '{s}' (hour 0-23, minute 0-59)", file=sys.stderr)
            sys.exit(1)
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            print(f"Error: Time '{s}' is in the past (now {now.strftime('%H:%M')})",
                  file=sys.stderr)
            sys.exit(1)
        return target.timestamp()

    # Try duration (30min, 1.5hr, etc.)
    dm = _DURATION_RE.match(s)
    if dm:
        value = float(dm.group(1))
        unit = dm.group(2).lower()
        if unit in ('h', 'hr', 'hrs', 'hour', 'hours'):
            secs = value * 3600
        else:
            secs = value * 60
        if secs <= 0:
            print(f"Error: Duration must be > 0", file=sys.stderr)
            sys.exit(1)
        return time.time() + secs

    print(f"Error: Invalid {label} value '{s}'", file=sys.stderr)
    print(f"Examples: 30min, 1.5hr, 2hours, 45m, 17:50, 21:00", file=sys.stderr)
    sys.exit(1)


def parse_till(s: str) -> float:
    return parse_time_spec(s, "--till")


def _try_parse_time_spec(s: str) -> float | None:
    """Non-fatal version of parse_time_spec for hot-reload. Returns None on error."""
    cm = _CLOCK_RE.match(s)
    if cm:
        hour, minute = int(cm.group(1)), int(cm.group(2))
        if hour > 23 or minute > 59:
            return None
        now = datetime.now()
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            return None
        return target.timestamp()
    dm = _DURATION_RE.match(s)
    if dm:
        value = float(dm.group(1))
        unit = dm.group(2).lower()
        secs = value * 3600 if unit in ('h', 'hr', 'hrs', 'hour', 'hours') else value * 60
        return time.time() + secs if secs > 0 else None
    return None


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


# Chapter cache: {(book_chi, chap, version): {sec: text}}
_chap_cache = {}


def fetch_chap_cached(book_chi: str, chap: int, version: str, strong: int = 0) -> dict:
    """Fetch a chapter, with caching to avoid redundant API calls."""
    key = (book_chi, chap, version)
    if key not in _chap_cache:
        _chap_cache[key] = fetch_chap(book_chi, chap, version, strong)
    return _chap_cache[key]


def fetch_sec_pair(book_chi: str, chap: int, sec: int,
                   target_version: str = "lcc") -> tuple:
    """Fetch both UNV+SN and target version for a single sec.
    Returns (unv_sn, target_text)."""
    unv_chap = fetch_chap_cached(book_chi, chap, "unv", strong=1)
    target_chap = fetch_chap_cached(book_chi, chap, target_version, strong=0)

    unv_sn = unv_chap.get(sec)
    target_text = target_chap.get(sec)

    if not unv_sn:
        raise ValueError(f"UNV {book_chi} {chap}:{sec} not found")
    if not target_text:
        raise ValueError(f"{target_version.upper()} {book_chi} {chap}:{sec} not found")

    return unv_sn, target_text


# ── Prompt Construction ──────────────────────────────────────────────────────

# ── Run config (.run_config.conf) ────────────────────────────────────────────
# Bash-style NAME=value file, hot-reloaded every ~10 seconds during runs.
# Replaces the old .target_version single-value file.

RUN_CONFIG_FILE = os.path.join(SCRIPT_DIR, ".run_config.conf")
_OLD_TARGET_VERSION_FILE = os.path.join(SCRIPT_DIR, ".target_version")

RUN_CONFIG_DEFAULTS = {
    "TARGET_VERSION": "lcc",
    "TILL": "",
    "VERSE_COUNT": "0",
    "PRESERVE_TOKEN_PERCENTAGE": "30",
    "PAUSED": "false",
}


def load_run_config() -> dict:
    """Parse .run_config.conf (NAME=value). Returns dict with string values."""
    config = dict(RUN_CONFIG_DEFAULTS)
    if not os.path.isfile(RUN_CONFIG_FILE):
        return config
    with open(RUN_CONFIG_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            config[key.strip()] = value.strip()
    return config


def save_run_config(config: dict):
    """Write .run_config.conf preserving only known keys with comments."""
    lines = ["# Runtime config — edit while script is running\n"]
    for key in RUN_CONFIG_DEFAULTS:
        val = config.get(key, RUN_CONFIG_DEFAULTS[key])
        lines.append(f"{key} = {val}\n")
    # Preserve any extra keys not in defaults
    for key in config:
        if key not in RUN_CONFIG_DEFAULTS:
            lines.append(f"{key} = {config[key]}\n")
    with open(RUN_CONFIG_FILE, "w") as f:
        f.writelines(lines)


def update_run_config(key: str, value: str):
    """Update a single key in .run_config.conf (creates file if needed)."""
    config = load_run_config()
    config[key] = value
    save_run_config(config)


# Hot-reload state
_config_mtime = 0.0
_config_cache: dict = {}
_last_config_check = 0.0


def maybe_reload_config(force: bool = False) -> dict:
    """Re-read .run_config.conf if file changed. Throttled to every 10s."""
    global _config_mtime, _config_cache, _last_config_check
    now = time.time()
    if not force and now - _last_config_check < 10:
        return _config_cache
    _last_config_check = now
    try:
        mt = os.path.getmtime(RUN_CONFIG_FILE)
    except OSError:
        return _config_cache
    if mt != _config_mtime:
        old = _config_cache.copy()
        _config_cache = load_run_config()
        _config_mtime = mt
        # Log changes (skip on first load)
        if old:
            for k in set(list(_config_cache.keys()) + list(old.keys())):
                if old.get(k) != _config_cache.get(k):
                    print(f"  🔄 Config changed: {k} {old.get(k)!r} → {_config_cache.get(k)!r}")
    return _config_cache


def get_config_int(key: str, default: int = 0) -> int:
    """Get an integer value from the hot config cache."""
    try:
        return int(_config_cache.get(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_config_bool(key: str, default: bool = False) -> bool:
    """Get a boolean value from the hot config cache."""
    val = _config_cache.get(key, str(default)).lower()
    return val in ("true", "1", "yes")


# Backward-compat wrappers (used by --set-target-version and startup)
def load_default_target_version() -> str:
    """Load target version from .run_config.conf (migrates from .target_version)."""
    # Migration: old .target_version → .run_config.conf
    if (os.path.isfile(_OLD_TARGET_VERSION_FILE)
            and not os.path.isfile(RUN_CONFIG_FILE)):
        with open(_OLD_TARGET_VERSION_FILE, "r") as f:
            ver = f.read().strip()
        if ver:
            update_run_config("TARGET_VERSION", ver)
            print(f"Migrated .target_version → .run_config.conf (TARGET_VERSION={ver})")
            return ver
    config = load_run_config()
    return config.get("TARGET_VERSION", "lcc")


def save_default_target_version(version: str):
    """Persist target version to .run_config.conf."""
    update_run_config("TARGET_VERSION", version)
    print(f"Default target version set to: {version}")
    print(f"Saved to: {RUN_CONFIG_FILE}")


def load_system_prompt(target_version: str) -> str:
    """Load system prompt for the target version.

    Tries system_prompt_{version}.md first, falls back to system_prompt_lcc.md
    with version name substituted.
    """
    prompt_file = os.path.join(SCRIPT_DIR, f"system_prompt_{target_version}.md")
    if os.path.isfile(prompt_file):
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()

    # Fallback: load LCC prompt and substitute version name
    lcc_file = os.path.join(SCRIPT_DIR, "system_prompt_lcc.md")
    if os.path.isfile(lcc_file):
        with open(lcc_file, "r", encoding="utf-8") as f:
            prompt = f.read()
        prompt = prompt.replace("LCC", target_version.upper())
        prompt = prompt.replace("lcc", target_version)
        prompt = prompt.replace("呂振中譯本", f"({target_version.upper()} target version)")
        prompt = prompt.replace("Lü Zhènzhōng Translation", f"{target_version.upper()} translation")
        return prompt

    # Hardcoded minimal fallback
    return f"""\
You are a biblical Hebrew and Chinese translation expert. Your task is to transfer \
Strong's Number (SN) annotations from the Chinese Union Version (UNV/和合本) to the \
{target_version.upper()} translation.

UNV already has SN tags from FHL (bible.fhl.net). The target has none. You must insert \
the same SN tags at the semantically correct positions.

Return ONLY a JSON object:
{{
  "{target_version}_sn": "the target text with SN tags inserted",
  "confidence": 0.95,
  "notes": ["brief note about any non-trivial alignment decisions"]
}}"""


def build_json_schema(target_version: str) -> str:
    """Build JSON schema string with version-specific field name."""
    sn_field = f"{target_version}_sn"
    return json.dumps({
        "type": "object",
        "properties": {
            sn_field: {"type": "string",
                       "description": f"{target_version.upper()} text with SN tags inserted"},
            "confidence": {"type": "number", "description": "Confidence score 0.0-1.0"},
            "notes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Notes about non-trivial alignment decisions"
            }
        },
        "required": [sn_field, "confidence", "notes"]
    })


def build_user_prompt(unv_sn: str, target_text: str, target_version: str,
                      book_chi: str, chap: int, sec: int) -> str:
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    ver = target_version.upper()
    sn_field = f"{target_version}_sn"
    return f"""\
Transfer Strong's Numbers from UNV to {ver} for {book_eng} {chap}:{sec}.

UNV+SN: {unv_sn}
{ver}:    {target_text}

Return the JSON with {sn_field}, confidence, and notes."""


# ── Claude CLI ───────────────────────────────────────────────────────────────


def parse_stream_json(raw: str, sn_field: str = "lcc_sn") -> tuple:
    """Parse stream-json output from claude CLI.

    Returns (result_dict, rate_limit_info).
    rate_limit_info is the rate_limit_event.rate_limit_info dict, or None.
    result_dict includes '_cost_usd' extracted from the result event.

    stream-json is newline-delimited JSON. Each line has a top-level "type" field.
    With --json-schema, the structured output appears in:
      1. result event → structured_output field (most reliable)
      2. assistant event → tool_use "StructuredOutput" → input field
    """
    result = None
    rate_limit_info = None
    cost_usd = 0.0

    # First pass: collect structured result, rate_limit_info, and cost
    for line in raw.strip().split('\n'):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Extract rate limit info
        if obj.get("type") == "rate_limit_event":
            rate_limit_info = obj.get("rate_limit_info")

        # Best: result event with structured_output
        if obj.get("type") == "result":
            cost_usd = obj.get("total_cost_usd", 0)
            if result is None:
                if "structured_output" in obj and obj["structured_output"]:
                    result = obj["structured_output"]
                else:
                    result_text = obj.get("result", "")
                    if isinstance(result_text, dict):
                        result = result_text
                    elif isinstance(result_text, str) and result_text.strip():
                        try:
                            result = json.loads(result_text)
                        except json.JSONDecodeError:
                            pass

        # Also check: assistant tool_use with StructuredOutput
        if obj.get("type") == "assistant" and result is None:
            for block in obj.get("message", {}).get("content", []):
                if (block.get("type") == "tool_use"
                        and block.get("name") == "StructuredOutput"):
                    inp = block.get("input", {})
                    if inp and sn_field in inp:
                        result = inp

    if result is not None:
        result["_cost_usd"] = cost_usd
        return result, rate_limit_info

    # Last resort: concatenate all text_delta content and try parsing
    text_parts = []
    for line in raw.strip().split('\n'):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        event = obj.get("event", obj)
        if event.get("type") == "content_block_delta":
            delta = event.get("delta", {})
            if delta.get("type") == "text_delta":
                text_parts.append(delta.get("text", ""))
    if text_parts:
        full_text = ''.join(text_parts)
        try:
            parsed = json.loads(full_text)
            parsed["_cost_usd"] = cost_usd
            return parsed, rate_limit_info
        except json.JSONDecodeError:
            pass
        # Regex fallback
        match = re.search(r'\{[^{}]*"' + re.escape(sn_field) + r'"\s*:', full_text, re.DOTALL)
        if match:
            start = match.start()
            depth = 0
            for i, c in enumerate(full_text[start:], start):
                if c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                if depth == 0:
                    try:
                        parsed = json.loads(full_text[start:i + 1])
                        parsed["_cost_usd"] = cost_usd
                        return parsed, rate_limit_info
                    except json.JSONDecodeError:
                        break

    return {
        sn_field: "",
        "confidence": 0.0,
        "notes": [f"Failed to parse stream-json response: {raw[:300]}"],
        "error": True,
        "_cost_usd": cost_usd
    }, rate_limit_info


BUDGET_FILE = os.path.join(SCRIPT_DIR, ".window_budget.json")


def load_window_budget(model: str) -> float:
    """Load learned cost budget for model's rate-limit window. Returns 0 if unknown."""
    try:
        with open(BUDGET_FILE) as f:
            data = json.load(f)
        return data.get(model, {}).get("budget_cost", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def save_window_budget(model: str, budget_cost: float):
    """Save learned cost budget for model."""
    try:
        with open(BUDGET_FILE) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data[model] = {
        "budget_cost": round(budget_cost, 4),
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    with open(BUDGET_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def call_claude(model: str, unv_sn: str, target_text: str,
                target_version: str,
                book_chi: str, chap: int, sec: int,
                verbose: bool = False,
                progress: tuple = None,
                paused_acc: list = None) -> tuple:
    """Call claude CLI to insert SNs into target version text.

    Returns (result_dict, rate_limit_info).
    rate_limit_info is the rate_limit_event dict from stream-json, or None.
    progress: optional (total_processed, start_time) for progress display.
    paused_acc: optional mutable [float] to accumulate pause/wait seconds.
    """
    sn_field = f"{target_version}_sn"

    claude_bin = shutil.which("claude")
    if not claude_bin:
        raise RuntimeError("'claude' CLI not found in PATH")

    system_prompt = load_system_prompt(target_version)
    json_schema = build_json_schema(target_version)
    prompt = system_prompt + "\n\n" + build_user_prompt(
        unv_sn, target_text, target_version, book_chi, chap, sec)

    if verbose:
        print(f"  ── prompt ──")
        print(f"  {prompt}")
        print(f"  ── /prompt ──")

    cmd = [
        claude_bin, "-p",
        "--output-format", "stream-json",
        "--json-schema", json_schema,
        "--model", model,
        "--no-session-persistence",
        "--disallowed-tools", "Bash,Edit,Write,Read,Glob,Grep,Task",
    ]

    if verbose:
        print(f"  [claude {model}] calling... (timeout 300s)", flush=True)

    # Clear CLAUDECODE env var to allow running from within a Claude Code session
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    # Retry loop for rate-limit / token exhaustion errors
    DEFAULT_TIMEOUT = 300     # 5 min — normal verses
    RETRY_TIMEOUT = 600       # 10 min — generous for retries (complex verses)
    IMMEDIATE_RETRIES = 2     # retry twice (no output) before assuming rate limit
    RETRY_INTERVAL = 30 * 60  # 30 minutes
    MAX_RETRIES = 48          # 48 x 30min = 24 hours max
    RATE_LIMIT_PATTERNS = [
        "rate limit", "rate_limit", "token limit", "too many requests",
        "overloaded", "capacity", "quota", "throttl", "429",
    ]

    for attempt in range(MAX_RETRIES + 1):
        timeout = DEFAULT_TIMEOUT if attempt == 0 else RETRY_TIMEOUT
        try:
            result_proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, env=env,
                input=prompt
            )
        except subprocess.TimeoutExpired as e:
            now_str = datetime.now().strftime("%H:%M:%S")
            partial = (e.stdout or "").strip()
            # Count events beyond the initial system/init line
            event_lines = [l for l in partial.split('\n') if l.strip()]
            model_active = len(event_lines) > 1

            if model_active:
                # Model was actively generating — slow verse, not rate limit
                print(f"  ⏳ [{now_str}] Timed out ({timeout}s) but model was "
                      f"generating ({len(event_lines)} events, "
                      f"{len(partial)} chars). Slow verse.", flush=True)
                # Try to salvage partial output
                result, rl_info = parse_stream_json(partial, sn_field)
                if result.get(sn_field):
                    print(f"  ✓ Salvaged partial result", flush=True)
                    return result, rl_info
                # Can't salvage — skip this verse
                return {
                    sn_field: "",
                    "confidence": 0.0,
                    "notes": [f"Timeout ({timeout}s): verse too complex, "
                              f"model was generating ({len(event_lines)} events)"],
                    "error": True
                }, rl_info

            # No model output — likely rate limit or waiting for capacity
            if attempt < IMMEDIATE_RETRIES:
                next_timeout = RETRY_TIMEOUT
                print(f"  ⏳ [{now_str}] Timed out ({timeout}s, no output, "
                      f"attempt {attempt + 1}/{IMMEDIATE_RETRIES + 1}). "
                      f"Retrying immediately (timeout {next_timeout}s)...",
                      flush=True)
                continue

            # Exhausted immediate retries — enter rate-limit wait loop
            next_try = datetime.now(timezone.utc).timestamp() + RETRY_INTERVAL
            next_str = datetime.fromtimestamp(next_try).strftime("%H:%M:%S")
            print(f"  ⏸ [{now_str}] Timed out (attempt {attempt + 1}, likely "
                  f"rate limit). Waiting 30 min, next retry at "
                  f"{next_str}...", flush=True)

            if attempt >= MAX_RETRIES:
                return {
                    sn_field: "",
                    "confidence": 0.0,
                    "notes": [f"Timeout: gave up after {MAX_RETRIES} retries"],
                    "error": True
                }, None

            _pause_start = time.time()
            time.sleep(RETRY_INTERVAL)
            if paused_acc is not None:
                paused_acc[0] += time.time() - _pause_start
            continue

        if result_proc.returncode == 0:
            break

        stderr = result_proc.stderr.strip().lower()
        is_rate_limit = any(pat in stderr for pat in RATE_LIMIT_PATTERNS)

        if not is_rate_limit:
            # Non-rate-limit error — return immediately
            return {
                sn_field: "",
                "confidence": 0.0,
                "notes": [f"claude CLI error: {result_proc.stderr.strip()[:300]}"],
                "error": True
            }, None

        # Rate limit hit — wait and retry
        now_str = datetime.now().strftime("%H:%M:%S")
        next_try = datetime.now(timezone.utc).timestamp() + RETRY_INTERVAL
        next_str = datetime.fromtimestamp(next_try).strftime("%H:%M:%S")
        print(f"  ⏸ [{now_str}] Rate limit hit (attempt {attempt + 1}). "
              f"Waiting 30 min, next retry at {next_str}...", flush=True)

        if attempt >= MAX_RETRIES:
            return {
                sn_field: "",
                "confidence": 0.0,
                "notes": [f"Rate limit: gave up after {MAX_RETRIES} retries"],
                "error": True
            }, None

        _pause_start = time.time()
        time.sleep(RETRY_INTERVAL)
        if paused_acc is not None:
            paused_acc[0] += time.time() - _pause_start

    return parse_stream_json(result_proc.stdout, sn_field)


# ── Output ───────────────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(REPO_ROOT, "output")

MODEL_BRAND_MAP = {
    "sonnet": "claude", "opus": "claude", "haiku": "claude",
    "gemini-3-pro": "gemini", "gemini-3-flash": "gemini",
    "gemini-2.5-pro": "gemini", "gemini-2.5-flash": "gemini",
    "codex-5.4": "codex", "codex-5.3": "codex", "codex-5.2": "codex",
}

KNOWN_BRANDS = sorted(set(MODEL_BRAND_MAP.values()))


def save_result(result: dict, book_chi: str, book_eng: str,
                chap: int, sec: int, model: str, brand: str,
                target_version: str,
                unv_sn: str, target_text: str) -> str:
    """Save result to output/{version}/{brand}/{Book}/{chap}/{sec}.json."""
    sec_dir = os.path.join(OUTPUT_DIR, target_version, brand, book_eng, str(chap))
    os.makedirs(sec_dir, exist_ok=True)

    sn_field = f"{target_version}_sn"
    orig_field = f"{target_version}_original"

    output = {
        "book": book_eng,
        "book_chi": book_chi,
        "chap": chap,
        "sec": sec,
        "target_version": target_version,
        sn_field: result.get(sn_field, result.get("lcc_sn", "")),
        orig_field: target_text,
        "unv_sn_reference": unv_sn,
        "confidence": result.get("confidence", 0.0),
        "notes": result.get("notes", []),
        "brand": brand,
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


def verify_sn_coverage(unv_sn: str, target_sn: str) -> dict:
    """Check that all SNs from UNV appear in target+SN output."""
    unv_sns = sorted(count_sns(unv_sn))
    lcc_sns = sorted(count_sns(target_sn))

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

def process_sec(model: str, brand: str, target_version: str, book_chi: str,
                chap: int, sec: int, dry_run: bool = False,
                verbose: bool = False,
                progress: tuple = None,
                paused_acc: list = None) -> tuple:
    """Process a single sec. Returns (result_dict, rate_limit_info).

    progress: optional (total_processed, start_time, total_paused) for display.
    paused_acc: optional mutable [float] to accumulate pause/wait seconds.
    """
    verse_t0 = time.time()
    ver = target_version.upper()
    sn_field = f"{target_version}_sn"
    book_eng = CHI_TO_ENG.get(book_chi)
    if not book_eng:
        print(f"  ✗ Unknown book: {book_chi}", file=sys.stderr)
        return None, None

    try:
        unv_sn, target_text = fetch_sec_pair(book_chi, chap, sec, target_version)
    except ValueError as e:
        print(f"  ✗ {e}", file=sys.stderr)
        return None, None

    print(f"\n  UNV+SN: {unv_sn}")
    print(f"\n  {ver}:    {target_text}")

    if dry_run:
        print("  [dry-run] Skipping claude call")
        return {sn_field: "", "confidence": 0.0, "notes": ["dry-run"]}, None

    try:
        result, rate_limit_info = call_claude(model, unv_sn, target_text,
                                              target_version, book_chi,
                                              chap, sec, verbose=verbose,
                                              progress=progress,
                                              paused_acc=paused_acc)
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None, None

    # Normalize notes to list (model may return a string despite schema)
    if "notes" in result and isinstance(result["notes"], str):
        result["notes"] = [result["notes"]] if result["notes"] else []

    # Verify SN coverage
    target_sn = result.get(sn_field, "")
    if target_sn:
        verify = verify_sn_coverage(unv_sn, target_sn)
        if not verify["perfect"]:
            if verify["missing"]:
                result.setdefault("notes", []).append(
                    f"Missing SNs: {', '.join(verify['missing'])}"
                )
            if verify["extra"]:
                result.setdefault("notes", []).append(
                    f"Extra SNs: {', '.join(verify['extra'])}"
                )
            print(f"  ⚠ SN mismatch: {verify['unv_count']} UNV → {verify['lcc_count']} {ver}"
                  f" (missing: {verify['missing']}, extra: {verify['extra']})")

    print(f"\n  {ver}+SN: {result.get(sn_field, '(empty)')}")
    print(f"\n  Conf:   {result.get('confidence', 0.0)}")
    if result.get("notes"):
        for note in result["notes"]:
            print(f"  Note:   {note}")

    # Save
    file_path = save_result(result, book_chi, book_eng, chap, sec,
                            model, brand, target_version, unv_sn, target_text)
    verse_secs = time.time() - verse_t0
    if verse_secs >= 60:
        verse_time_str = f"{verse_secs / 60:.1f}min"
    else:
        verse_time_str = f"{verse_secs:.0f}s"
    print(f"  Saved:  {file_path}")
    print(f"  ⏱ Verse time: {verse_time_str}")

    # Show progress summary after saving
    if progress:
        done, t0, paused_so_far = progress
        # +1 to include this verse we just processed
        done_now = done + 1
        wall = time.time() - t0
        working = wall - (paused_acc[0] if paused_acc else paused_so_far)
        if done_now > 0:
            rate = working / done_now / 60  # minutes per verse (working time only)
            working_m = working / 60
            print(f"\n  📊 {done_now} verses done, {working_m:.0f}min working, "
                  f"{rate:.1f} min/verse", flush=True)

    return result, rate_limit_info


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
        description="LLM-Direct Strong's Number Transfer: UNV → Target Version"
    )
    parser.add_argument("--target-version", "--tv", dest="target_version", default=None,
                        help=f"Target Bible version code (default: from .target_version or lcc). "
                             f"e.g., lcc, rcuv2010, tcv, esv, nasb")
    parser.add_argument("--set-target-version", dest="set_target_version", default=None,
                        metavar="VERSION",
                        help="Set and persist default target version, then exit")
    parser.add_argument("--chineses", "--book", required=False, dest="chineses",
                        nargs='+',
                        help="Chinese book abbreviation(s) (e.g., 創 出 詩)")
    parser.add_argument("--chap", required=False, type=str,
                        help="Chapter: single (1), range (1-10), or 'all'")
    parser.add_argument("--list-books", "--book-list", action="store_true",
                        help="List all 66 book abbreviations and exit")
    parser.add_argument("--sec", type=int, default=None,
                        help="Section/verse number (omit for whole chapter)")
    parser.add_argument("--model", default="sonnet",
                        help="LLM model (default: sonnet). Claude: sonnet, opus, haiku. "
                             "Gemini: gemini-3-pro, gemini-3-flash, gemini-2.5-pro, gemini-2.5-flash. "
                             "Codex: codex-5.4, codex-5.3, codex-5.2")
    parser.add_argument("--brand", default=None, choices=KNOWN_BRANDS,
                        help="Override brand (auto-derived from --model if omitted)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch data but skip claude calls")
    parser.add_argument("--force", action="store_true",
                        help="Reprocess all verses, overwrite existing files")
    parser.add_argument("--verse-count", type=int, nargs="?", const=10, default=0,
                        help="Process at most N verses then quit (omit N for 10, omit flag for unlimited)")
    parser.add_argument("--till", "--until", dest="till", nargs='+', default=None,
                        help="Quit after duration or at clock time (e.g., 30min, '3 hrs', 2hours, 17:50, 21:00)")
    parser.add_argument("--start-at", "--since", "--start-from", dest="start_at", nargs='+', default=None,
                        help="Wait and start at clock time or after duration (e.g., 23:00, '3 hrs', 30min)")
    parser.add_argument("--reprocess-low-confidence", action="store_true",
                        help="Reprocess verses with confidence < 0.85 using opus (or --model)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show full prompt and claude command details")
    parser.add_argument("--no-work-hours-stop", action="store_true",
                        help="Disable automatic pause before work hours")
    parser.add_argument("--work-hours-start", default="06:50",
                        help="Pause time in HH:MM format (default: 06:50)")
    parser.add_argument("--midnight-resume-at", default="01:00",
                        help="Resume time in HH:MM format (default: 01:00)")
    parser.add_argument("--quit-at-work-hours", action="store_true",
                        help="Quit instead of pausing when work hours reached")
    parser.add_argument("--immediately-restrict-first-session", action="store_true",
                        help="Enforce pause window immediately (default: always run on first start)")
    parser.add_argument("--preserve-token-percentage-4-colleagues", type=int,
                        default=30, metavar="N",
                        help="Preserve N%% of token budget for colleagues; "
                             "pause at (100-N)%% usage (default: 30)")
    args = parser.parse_args()

    # Handle --set-target-version (persist and exit)
    if args.set_target_version:
        save_default_target_version(args.set_target_version)
        sys.exit(0)

    # ── Initialize .run_config.conf: merge CLI args into config file ──
    # Migrate from old .target_version if needed
    if (os.path.isfile(_OLD_TARGET_VERSION_FILE)
            and not os.path.isfile(RUN_CONFIG_FILE)):
        with open(_OLD_TARGET_VERSION_FILE, "r") as f:
            _migrated_ver = f.read().strip()
        if _migrated_ver:
            _mig_config = dict(RUN_CONFIG_DEFAULTS)
            _mig_config["TARGET_VERSION"] = _migrated_ver
            save_run_config(_mig_config)
            print(f"Migrated .target_version → .run_config.conf "
                  f"(TARGET_VERSION={_migrated_ver})")
    # Load existing config (or defaults)
    _startup_config = load_run_config()

    # Detect which CLI args were explicitly provided (vs defaults)
    _explicit_cli = set()
    for action in parser._actions:
        for opt in action.option_strings:
            if opt in sys.argv:
                _explicit_cli.update(action.option_strings)
                break

    # Overlay explicitly-provided CLI args into config
    if any(o in _explicit_cli for o in ('--target-version', '--tv')):
        _startup_config["TARGET_VERSION"] = args.target_version
    if any(o in _explicit_cli for o in ('--till', '--until')):
        _startup_config["TILL"] = ' '.join(args.till) if args.till else ""
    if '--verse-count' in _explicit_cli:
        _startup_config["VERSE_COUNT"] = str(args.verse_count)
    if '--preserve-token-percentage-4-colleagues' in _explicit_cli:
        _startup_config["PRESERVE_TOKEN_PERCENTAGE"] = str(
            args.preserve_token_percentage_4_colleagues)

    # Write merged config to file
    save_run_config(_startup_config)

    # Initialize hot-reload cache
    maybe_reload_config(force=True)

    # Resolve target version from config (file is now the source of truth)
    target_version = _config_cache.get("TARGET_VERSION", "lcc")

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

    # Normalize: support both "利 民" and "利, 民" and "利,民"
    args.chineses = [b.strip() for raw in args.chineses for b in raw.split(',') if b.strip()]

    # Validate --verse-count
    if args.verse_count < 0:
        parser.error("--verse-count must be >= 0 (0=unlimited)")

    # --reprocess-low-confidence defaults to opus unless --model was explicitly set
    if args.reprocess_low_confidence and '--model' not in sys.argv:
        args.model = 'opus'

    # Derive brand from model (or use explicit --brand override)
    if args.brand:
        brand = args.brand
    elif args.model in MODEL_BRAND_MAP:
        brand = MODEL_BRAND_MAP[args.model]
    else:
        print(f"Error: Unknown model '{args.model}'. Known models: "
              f"{', '.join(sorted(MODEL_BRAND_MAP.keys()))}", file=sys.stderr)
        print(f"Use --brand to specify brand explicitly.", file=sys.stderr)
        sys.exit(1)

    # Validate all books upfront
    book_list = []  # [(book_chi, book_eng, chapters), ...]
    for bchi in args.chineses:
        beng = CHI_TO_ENG.get(bchi)
        if not beng:
            print(f"Error: Unknown book abbreviation '{bchi}'", file=sys.stderr)
            print(f"Valid: {', '.join(sorted(CHI_TO_ENG.keys()))}", file=sys.stderr)
            sys.exit(1)
        bchaps = parse_chap_arg(args.chap, bchi)
        book_list.append((bchi, beng, bchaps))

    # For banner: summarize books
    if len(book_list) == 1:
        book_chi, book_eng, chapters = book_list[0]
        chap_label = f"{chapters[0]}-{chapters[-1]}" if len(chapters) > 1 else str(chapters[0])
        banner_books = f"{book_eng} ({book_chi}) Chap {chap_label}"
    else:
        banner_books = ', '.join(f"{beng}({bchi})" for bchi, beng, _ in book_list)

    # Validate work-hours times
    stop_hour, stop_minute = 6, 50
    resume_hour, resume_minute = 1, 0
    if not args.no_work_hours_stop:
        try:
            t = datetime.strptime(args.work_hours_start, "%H:%M")
            stop_hour, stop_minute = t.hour, t.minute
        except ValueError:
            print(f"Error: Invalid --work-hours-start '{args.work_hours_start}' "
                  f"(expected HH:MM)", file=sys.stderr)
            sys.exit(1)
        try:
            t = datetime.strptime(args.midnight_resume_at, "%H:%M")
            resume_hour, resume_minute = t.hour, t.minute
        except ValueError:
            print(f"Error: Invalid --midnight-resume-at '{args.midnight_resume_at}' "
                  f"(expected HH:MM)", file=sys.stderr)
            sys.exit(1)

    print(f"═══ LLM-Direct SN Transfer: {banner_books} ═══")
    print(f"Target: {target_version}  Brand: {brand}  Model: {args.model}")
    if args.reprocess_low_confidence:
        print(f"Mode: reprocess low confidence (<0.85)")
    elif not args.force:
        print(f"Skip existing: ON (use --force to reprocess)")
    _vc = get_config_int("VERSE_COUNT")
    print(f"Verse count: {_vc if _vc > 0 else 'unlimited'}")
    print(f"Config: {RUN_CONFIG_FILE} (hot-reloaded every ~10s)")
    # Parse --start-at (wait before starting)
    start_at_ts = None
    start_at_str = None
    if args.start_at:
        start_at_str = ' '.join(args.start_at)
        start_at_ts = parse_time_spec(start_at_str, "--start-at")
        start_at_fmt = datetime.fromtimestamp(start_at_ts).strftime("%H:%M")
        print(f"Start at: {start_at_str} (begin at {start_at_fmt})")

    # Parse --till and compute deadline
    # When used with --start-at, --till is relative to the start time, not now
    deadline = None
    till_str = None
    _till_raw = _config_cache.get("TILL", "").strip()
    if _till_raw:
        till_str = _till_raw
        if start_at_ts:
            # --till is a run duration when combined with --start-at
            # Re-parse as duration from start_at_ts instead of from now
            dm = _DURATION_RE.match(till_str)
            cm = _CLOCK_RE.match(till_str)
            if dm:
                value = float(dm.group(1))
                unit = dm.group(2).lower()
                secs = value * 3600 if unit in ('h', 'hr', 'hrs', 'hour', 'hours') else value * 60
                deadline = start_at_ts + secs
            elif cm:
                deadline = parse_till(till_str)
            else:
                deadline = parse_till(till_str)
        else:
            deadline = parse_till(till_str)
        quit_at = datetime.fromtimestamp(deadline).strftime("%H:%M")
        print(f"Till: {till_str} (quit at {quit_at})")
    _prev_till_str = till_str  # Track for hot-reload change detection
    if not args.no_work_hours_stop:
        print(f"Work hours: pause at {args.work_hours_start}, "
              f"resume at {args.midnight_resume_at}"
              f" (--quit-at-work-hours to exit instead)"
              if not args.quit_at_work_hours else
              f"Work hours: quit at {args.work_hours_start}")

    preserve_pct = get_config_int("PRESERVE_TOKEN_PERCENTAGE", 30)
    window_budget = load_window_budget(args.model)
    if preserve_pct > 0:
        budget_str = f", learned budget: ${window_budget:.2f}" if window_budget > 0 else ", budget: learning..."
        print(f"Preserve: {preserve_pct}% for colleagues "
              f"(pause at {100 - preserve_pct}%{budget_str})")

    if not args.dry_run:
        if not shutil.which("claude"):
            print("Error: 'claude' CLI not found in PATH.", file=sys.stderr)
            sys.exit(1)

    # --start-at: wait until the specified time
    if start_at_ts:
        wait_secs = start_at_ts - time.time()
        if wait_secs > 0:
            start_at_fmt = datetime.fromtimestamp(start_at_ts).strftime("%Y-%m-%d %H:%M")
            wait_h = wait_secs / 3600
            if wait_h >= 1:
                print(f"\n⏸ Waiting {wait_h:.1f} hours until {start_at_fmt}...")
            else:
                print(f"\n⏸ Waiting {wait_secs / 60:.0f} minutes until {start_at_fmt}...")
            try:
                time.sleep(wait_secs)
            except KeyboardInterrupt:
                print("\n⏹ Cancelled during --start-at wait.")
                print(f"\n═══ Session Report ═══")
                print(f"No verses processed (cancelled before start).")
                print(f"═══════════════════════")
                sys.exit(0)
            print(f"⏵ {datetime.now().strftime('%H:%M')} — starting now.", flush=True)

    # Work-hours pause window helper
    def in_pause_window(now):
        now_mins = now.hour * 60 + now.minute
        stop_mins = stop_hour * 60 + stop_minute
        resume_mins = resume_hour * 60 + resume_minute
        if stop_mins < resume_mins:
            return stop_mins <= now_mins < resume_mins
        else:
            # Crosses midnight: e.g., stop=06:50, resume=01:00
            return now_mins >= stop_mins or now_mins < resume_mins

    start_time = time.time()
    start_wall = datetime.now()
    total_paused = 0.0  # seconds spent in pauses (work-hours, rate-limit)
    total_processed = 0
    total_skipped = 0
    total_failed = 0
    work_hours_stop = False
    limit_reached = False
    time_limit_reached = False
    enforce_work_hours = args.immediately_restrict_first_session
    chapter_stats = []  # [(book_eng, chap, first_sec, last_sec, processed, skipped, failed)]
    user_interrupted = False
    # Token-budget tracking per rate-limit window
    current_window_resets_at = 0
    window_cost = 0.0

    # Flatten all books' chapters into one sequential list for the main loop
    _chap_jobs = []  # [(book_chi, book_eng, chap), ...]
    for _bchi, _beng, _bchaps in book_list:
        for _ch in _bchaps:
            _chap_jobs.append((_bchi, _beng, _ch))

    _prev_book_eng = None
    for _job_book_chi, _job_book_eng, chap in _chap_jobs:
        book_chi = _job_book_chi
        book_eng = _job_book_eng

        # Print book header when switching to a new book
        if book_eng != _prev_book_eng:
            if len(book_list) > 1 and _prev_book_eng is not None:
                print(f"\n{'─' * 40}")
            if len(book_list) > 1:
                print(f"\n── Book: {book_eng} ({book_chi}) ──")
            _prev_book_eng = book_eng

        if args.sec and len(_chap_jobs) == 1:
            # Single verse mode
            secs = [args.sec]
        else:
            # Whole chapter — fetch UNV to get sec list (also warms cache)
            print(f"\nFetching verse list for {book_eng} {chap}...")
            try:
                unv_data = fetch_chap_cached(book_chi, chap, "unv", strong=1)
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
        chap_first_sec = None
        chap_last_sec = None

        for i, s in enumerate(secs):
            # ── Hot-reload config + PAUSED check ──
            cfg = maybe_reload_config()
            # Update live values from config
            target_version = cfg.get("TARGET_VERSION", target_version)
            preserve_pct = get_config_int("PRESERVE_TOKEN_PERCENTAGE", 30)
            # Re-check TILL if changed
            _new_till = cfg.get("TILL", "").strip()
            if _new_till != _prev_till_str:
                _prev_till_str = _new_till
                if _new_till:
                    _new_deadline = _try_parse_time_spec(_new_till)
                    if _new_deadline is not None:
                        deadline = _new_deadline
                else:
                    deadline = None
            # PAUSED check
            if get_config_bool("PAUSED"):
                print(f"\n  ⏸ Paused via .run_config.conf — set PAUSED=false to resume",
                      flush=True)
                while get_config_bool("PAUSED"):
                    try:
                        time.sleep(5)
                    except KeyboardInterrupt:
                        print(f"\n⏹ Interrupted during pause.")
                        user_interrupted = True
                        break
                    maybe_reload_config(force=True)
                if user_interrupted:
                    break
                pause_resume_time = datetime.now().strftime("%H:%M")
                print(f"  ⏵ Resumed at {pause_resume_time}.", flush=True)

            out_path = os.path.join(OUTPUT_DIR, target_version, brand, book_eng, str(chap), f"{s}.json")

            # Skip logic: --force skips nothing, --reprocess-low-confidence only reprocesses low conf
            if not args.force and os.path.isfile(out_path):
                if args.reprocess_low_confidence:
                    # Check confidence — skip if >= 0.85
                    try:
                        with open(out_path, 'r', encoding='utf-8') as f:
                            existing = json.load(f)
                        conf = existing.get('confidence', 0.0)
                        if conf >= 0.85:
                            chap_skipped += 1
                            total_skipped += 1
                            if len(secs) <= 5 or (i + 1) == len(secs):
                                print(f"  {chap}:{s} skipped (conf {conf:.2f})")
                            elif chap_skipped == 1:
                                print(f"  {chap}:{s} skipped (conf {conf:.2f})...", end="", flush=True)
                            continue
                        # Low confidence — will reprocess below
                        print(f"\n\n\n\n\n  ── {book_eng} {chap}:{s} ({i+1}/{len(secs)}) ── [reprocess: conf {conf:.2f}]")
                    except (json.JSONDecodeError, IOError):
                        print(f"\n\n\n\n\n  ── {book_eng} {chap}:{s} ({i+1}/{len(secs)}) ── [reprocess: unreadable]")
                else:
                    chap_skipped += 1
                    total_skipped += 1
                    if len(secs) <= 5 or (i + 1) == len(secs):
                        print(f"  {chap}:{s} skipped (exists)")
                    elif chap_skipped == 1:
                        print(f"  {chap}:{s} skipped (exists)...", end="", flush=True)
                    continue
            else:
                print(f"\n\n\n\n\n  ── {book_eng} {chap}:{s} ({i+1}/{len(secs)}) ──")

            # --till time limit check
            if deadline and time.time() >= deadline:
                print(f"\n⏹ Time limit reached (--till {till_str}).")
                time_limit_reached = True
                break

            # Work-hours pause/quit check
            if not args.no_work_hours_stop and not args.dry_run:
                now = datetime.now()
                currently_in_window = in_pause_window(now)
                if currently_in_window and enforce_work_hours:
                    if args.quit_at_work_hours:
                        print(f"\n⏹ Work hours ({now.strftime('%H:%M')}). Quitting.")
                        work_hours_stop = True
                        break
                    else:
                        resume = now.replace(hour=resume_hour, minute=resume_minute, second=0)
                        if resume <= now:
                            resume += timedelta(days=1)
                        wait_secs = (resume - now).total_seconds()
                        wait_hours = wait_secs / 3600
                        print(f"\n⏸ Work hours ({now.strftime('%H:%M')}). "
                              f"Pausing until {args.midnight_resume_at} "
                              f"({wait_hours:.1f}h)...", flush=True)
                        pause_start = time.time()
                        try:
                            time.sleep(wait_secs)
                        except KeyboardInterrupt:
                            pause_duration = time.time() - pause_start
                            total_paused += pause_duration
                            if deadline:
                                deadline += pause_duration
                            print(f"\n⏹ Cancelled during work-hours pause.")
                            work_hours_stop = True
                            break
                        pause_duration = time.time() - pause_start
                        total_paused += pause_duration
                        if deadline:
                            deadline += pause_duration
                        print(f"⏵ {args.midnight_resume_at} reached, resuming.",
                              flush=True)
                elif not currently_in_window:
                    enforce_work_hours = True

            try:
                paused_acc = [total_paused]
                result, rate_limit_info = process_sec(
                    args.model, brand, target_version, book_chi, chap, s,
                    dry_run=args.dry_run, verbose=args.verbose,
                    progress=(total_processed, start_time, total_paused),
                    paused_acc=paused_acc)
                total_paused = paused_acc[0]
            except KeyboardInterrupt:
                print(f"\n⏹ Interrupted by user.")
                user_interrupted = True
                break
            sn_field = f"{target_version}_sn"
            if result and result.get(sn_field):
                chap_processed += 1
                total_processed += 1
                if chap_first_sec is None:
                    chap_first_sec = s
                chap_last_sec = s
            else:
                chap_failed += 1
                total_failed += 1

            # Track cost per rate-limit window
            verse_cost = result.get("_cost_usd", 0) if result else 0
            if rate_limit_info:
                resets_at = rate_limit_info.get("resetsAt", 0)
                if resets_at != current_window_resets_at:
                    # New window — reset cost tracker
                    current_window_resets_at = resets_at
                    window_cost = 0.0
            window_cost += verse_cost

            # Preserve-token check: pause at (100-N)% of learned budget
            should_pause_preserve = False
            if (preserve_pct > 0 and window_budget > 0
                    and window_cost >= window_budget * (1 - preserve_pct / 100)):
                should_pause_preserve = True

            # Proactive rate-limit detection from stream-json event
            if rate_limit_info and rate_limit_info.get("status") != "allowed":
                resets_at = rate_limit_info.get("resetsAt", 0)
                now_ts = time.time()
                # Learn/update budget: API triggers at ~90%, so budget ≈ cost / 0.9
                if window_cost > 0:
                    estimated_budget = window_cost / 0.9
                    save_window_budget(args.model, estimated_budget)
                    window_budget = estimated_budget
                    print(f"  📝 Learned window budget: ${estimated_budget:.2f} "
                          f"(from ${window_cost:.2f} at API limit)", flush=True)
                if resets_at > now_ts:
                    wait_secs = resets_at - now_ts
                    wait_min = wait_secs / 60
                    resume_str = datetime.fromtimestamp(resets_at).strftime("%H:%M")
                    print(f"\n  ⏸ Rate limit hit "
                          f"(status: {rate_limit_info.get('status')}). "
                          f"Waiting {wait_min:.0f} min until {resume_str}...",
                          flush=True)
                    pause_start = time.time()
                    try:
                        time.sleep(wait_secs)
                    except KeyboardInterrupt:
                        pause_duration = time.time() - pause_start
                        total_paused += pause_duration
                        if deadline:
                            deadline += pause_duration
                        print(f"\n⏹ Cancelled during rate-limit wait.")
                        limit_reached = True
                        break
                    pause_duration = time.time() - pause_start
                    total_paused += pause_duration
                    if deadline:
                        deadline += pause_duration
                    window_cost = 0.0  # new window after wait
                    print(f"  ⏵ Resuming.", flush=True)

            elif should_pause_preserve:
                # Budget-based early pause to preserve tokens for colleagues
                resets_at = current_window_resets_at
                now_ts = time.time()
                if resets_at > now_ts:
                    wait_secs = resets_at - now_ts
                    wait_min = wait_secs / 60
                    resume_str = datetime.fromtimestamp(resets_at).strftime("%H:%M")
                    print(f"\n  ⏸ {100 - preserve_pct}% budget used "
                          f"(${window_cost:.2f}/${window_budget:.2f}). "
                          f"Preserving {preserve_pct}% for colleagues. "
                          f"Waiting {wait_min:.0f} min until {resume_str}...",
                          flush=True)
                    pause_start = time.time()
                    try:
                        time.sleep(wait_secs)
                    except KeyboardInterrupt:
                        pause_duration = time.time() - pause_start
                        total_paused += pause_duration
                        if deadline:
                            deadline += pause_duration
                        print(f"\n⏹ Cancelled during preserve-token wait.")
                        limit_reached = True
                        break
                    pause_duration = time.time() - pause_start
                    total_paused += pause_duration
                    if deadline:
                        deadline += pause_duration
                    window_cost = 0.0  # new window after wait
                    print(f"  ⏵ Resuming (new window).", flush=True)

            # --verse-count check (hot-reloadable from config)
            _vc_limit = get_config_int("VERSE_COUNT")
            if _vc_limit > 0 and total_processed >= _vc_limit:
                print(f"\n⏹ Verse count reached ({_vc_limit}).")
                limit_reached = True
                break

            # Brief pause between API calls (server courtesy)
            if not args.dry_run and i < len(secs) - 1:
                try:
                    time.sleep(0.1)
                except KeyboardInterrupt:
                    print(f"\n⏹ Interrupted by user.")
                    user_interrupted = True
                    break

        # Record chapter stats (only if work was done)
        if chap_processed > 0 or chap_failed > 0:
            chapter_stats.append((book_eng, chap, chap_first_sec, chap_last_sec,
                                  chap_processed, chap_failed))

        if len(_chap_jobs) > 1 or len(secs) > 1:
            print(f"\n  Chapter {chap}: {chap_processed} processed, "
                  f"{chap_skipped} skipped, {chap_failed} failed")

        if work_hours_stop or limit_reached or time_limit_reached:
            break
        if user_interrupted:
            break

    # ── Session Report ───────────────────────────────────────────────────────
    end_wall = datetime.now()
    elapsed = time.time() - start_time
    working = elapsed - total_paused
    working_min = working / 60
    rate = f"~{working_min / total_processed:.1f} min/verse" if total_processed > 0 else "n/a"

    stop_reason = ""
    if user_interrupted:
        stop_reason = " (interrupted by user)"
    elif work_hours_stop:
        stop_reason = " (stopped for work hours)"
    elif limit_reached:
        stop_reason = " (verse count reached)"
    elif time_limit_reached:
        stop_reason = " (time limit reached)"

    print(f"\n═══ Session Report ({target_version}/{brand}/{args.model}) ═══")
    paused_str = ""
    if total_paused >= 60:
        paused_str = f", paused {total_paused / 60:.0f}min"
    print(f"Started: {start_wall.strftime('%H:%M')}  "
          f"Ended: {end_wall.strftime('%H:%M')}  "
          f"(working {int(working_min)}m {int(working % 60)}s{paused_str}, {rate})")
    for (bk, ch, first, last, proc, fail) in chapter_stats:
        parts = []
        if proc > 0:
            verse_range = f"{ch}:{first}–{ch}:{last}" if first != last else f"{ch}:{first}"
            parts.append(f"{verse_range} ({proc} verses)")
        if fail > 0:
            parts.append(f"{fail} failed")
        print(f"  {bk} {ch}:  {', '.join(parts)}")
    print(f"Total: {total_processed} processed, {total_failed} failed{stop_reason}")
    print(f"═══════════════════════")


if __name__ == "__main__":
    main()
