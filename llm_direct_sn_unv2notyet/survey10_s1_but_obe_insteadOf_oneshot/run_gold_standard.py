#!/usr/bin/env python3
"""
Gold Standard Builder — 3-Model Consensus for SN Embedding

Uses opus, gemini-3-flash-preview, and gpt-5.4 to establish the best possible
Strong's Number embedding via a 3-round consensus process.

Round 1: All 3 models produce output. Only UNANIMOUS agreement passes.
Round 2: Convergence (blind re-do until stable) + Debate (judge stable outputs).
         2/3 majority wins.
Round 3: Dual-capability final arbitration (pick winner OR identify collective
         error → prompt evolution). 2/3 majority wins.
         Remaining → unresolved (human review).

Usage:
    python3 run_gold_standard.py                          # default: Gen 1-2
    python3 run_gold_standard.py --book 創 --chap 1-5
    python3 run_gold_standard.py --book 創 --chap 1 --sec 1-10
    python3 run_gold_standard.py --prompt-file prompts/v1.1.md --prompt-version v1.1
    python3 run_gold_standard.py --max-r2-retries 2
    python3 run_gold_standard.py --force                           # re-run cached
    python3 run_gold_standard.py --round1-only
    python3 run_gold_standard.py --skip-round1
    python3 run_gold_standard.py --show-summary
    python3 run_gold_standard.py --show-disagreements
    python3 run_gold_standard.py --regression --trigger-verses 1:4,1:16
"""

import argparse
import atexit
import json
import os
import signal
import sys
import time
from datetime import datetime


def ts():
    """Return current timestamp string for progress logging."""
    return datetime.now().strftime("%H:%M:%S")


class _TeeWriter:
    """Write to both stdout and a log file."""
    def __init__(self, log_path, original_stdout):
        self._log = open(log_path, "a", encoding="utf-8")
        self._stdout = original_stdout

    def write(self, text):
        self._stdout.write(text)
        self._log.write(text)
        self._log.flush()

    def flush(self):
        self._stdout.flush()
        self._log.flush()


def _setup_tee(log_path):
    """Redirect stdout to both console and log file."""
    sys.stdout = _TeeWriter(log_path, sys.stdout)


# ── Log file rename tracking ────────────────────────────────────────────────

_log_rename_state = {
    "log_file": None,
    "book_eng": None,
    "first_chap": None,
    "first_sec": None,
    "last_book_eng": None,
    "last_chap": None,
    "last_sec": None,
}


def _update_last_verse(book_eng, chap, sec):
    """Track the last processed verse for log rename."""
    _log_rename_state["last_book_eng"] = book_eng
    _log_rename_state["last_chap"] = chap
    _log_rename_state["last_sec"] = sec


def _rename_log_on_exit():
    """Rename log file to include ending verse. Called via atexit/signal."""
    s = _log_rename_state
    if not s["log_file"] or not s["last_chap"]:
        return
    # Build end part
    if s["last_book_eng"] and s["last_book_eng"] != s["book_eng"]:
        # Crossed books
        end_part = f"{s['last_book_eng']}_{s['last_chap']}_{s['last_sec']}"
    else:
        end_part = f"{s['last_chap']}_{s['last_sec']}"

    start_part = f"{s['book_eng']}_{s['first_chap']}_{s['first_sec']}"
    old_path = s["log_file"]
    new_path = old_path.replace(f"{start_part}-.", f"{start_part}-{end_part}.")
    if old_path != new_path:
        try:
            os.rename(old_path, new_path)
        except OSError:
            pass


def _signal_handler(signum, frame):
    """Handle Ctrl-C: rename log then exit."""
    _rename_log_on_exit()
    sys.exit(0)


# ── Stability helpers (AD-2: Unified 4-Level Scale) ─────────────────────────

STABILITY_ORDER = {"R1": 0, "R2a": 1, "R2b": 2, "R2c": 3, "R2d": 4, "unstable": 5}

# Trigger thresholds
TRIGGER2_MIN_DISTANCE = 2.0
TRIGGER1_MIN_AVG = 2.0


def get_stability_level(conv_data):
    """Get unified stability level (0-3) for a model's convergence data.

    Level -1: Unavailable — bailed out (all errors, rate-limited)
    Level 0: Easy     — stable at R1 or R2a (≤2 unique outputs)
    Level 1: Mild     — stable at R2b (3 unique outputs)
    Level 2: Moderate — stable at R2c-R2d (4 unique outputs)
    Level 3: Strong   — stable at R2e+ or never converged (5+ unique outputs)
    """
    if conv_data.get("bailed_out", False):
        return -1  # unavailable, not unstable
    from judge import _count_unique_attempts, _stability_level
    attempts = conv_data.get("attempts", [])
    converged = conv_data.get("converged", False)
    unique = _count_unique_attempts(attempts)
    _, level = _stability_level(unique, converged)
    return level


def is_easy_convergence(conv_data):
    """Check if a model converged easily (Level 0)."""
    return get_stability_level(conv_data) == 0


def load_model_patch(model_name, prompt_version):
    """Load latest model-specific prompt patch if it exists.

    Filename format: v1.1_Gen_1_1.{model}-patch-{ver}_{Book}_{chap}_{sec}.md
    Matches on prompt_version prefix (e.g., "v1.1") and model name.

    Returns (patch_text, patch_version_str) or ("", "") if no patch.
    """
    import re as _re
    prompts_dir = os.path.join(SURVEY_DIR, "prompts")
    if not os.path.isdir(prompts_dir):
        return "", ""
    patches = []
    for fname in os.listdir(prompts_dir):
        m = _re.match(
            rf'^{_re.escape(prompt_version)}_\w+_\d+_\d+\.{_re.escape(model_name)}-patch-(\d+\.\d+)_\w+_\d+_\d+\.md$',
            fname)
        if m:
            ver_str = m.group(1)
            ver = tuple(int(x) for x in ver_str.split('.'))
            patches.append((ver, ver_str, fname))
    if not patches:
        return "", ""
    patches.sort()
    _, ver_str, latest = patches[-1]
    with open(os.path.join(prompts_dir, latest), "r", encoding="utf-8") as f:
        return f.read().strip(), ver_str


def next_patch_version(model_name, prompt_version):
    """Find the next patch version number for a model."""
    import re as _re
    prompts_dir = os.path.join(SURVEY_DIR, "prompts")
    if not os.path.isdir(prompts_dir):
        return "0.1"
    max_minor = 0
    for fname in os.listdir(prompts_dir):
        m = _re.match(
            rf'^{_re.escape(prompt_version)}_\w+_\d+_\d+\.{_re.escape(model_name)}-patch-(\d+)\.(\d+)_',
            fname)
        if m:
            minor = int(m.group(1)) * 10 + int(m.group(2))
            max_minor = max(max_minor, minor)
    if max_minor == 0:
        return "0.1"
    major = (max_minor + 1) // 10
    minor = (max_minor + 1) % 10
    return f"{major}.{minor}"

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
REPO_ROOT = os.path.dirname(PARENT_DIR)

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from llm_direct_sn_unv2notyet import (
    fetch_sec_pair, fetch_chap_cached, build_user_prompt, build_naked_user_prompt,
    load_system_prompt, verify_sn_coverage, CHI_TO_ENG,
)
from shared.sn_shell import strip_shell, build_shell_lookup, restore_shell_lookup
from shared.data.book_data_loader import load_books


def _user_prompt(unv_sn, target_text, target_version, book_chi, chap, sec,
                 naked=False):
    """Build the per-verse placement prompt; naked mode strips the source
    shell so the model places bare numbers only (sole graded job)."""
    if naked:
        return build_naked_user_prompt(
            strip_shell(unv_sn, markers=False), target_text,
            target_version, book_chi, chap, sec)
    return build_user_prompt(unv_sn, target_text, target_version,
                             book_chi, chap, sec)


def _coverage(unv_sn, output_sn, naked=False):
    """SN-coverage check that is correct in both modes. In naked mode the model
    output is bare numbers, which count_sns() (prefix-required) cannot see, so
    we restore the output first and verify against the shelled source — the
    same basis as the final gold-standard coverage check."""
    if naked:
        output_sn = restore_shell_lookup(output_sn, build_shell_lookup(unv_sn))
    return verify_sn_coverage(unv_sn, output_sn)

from cli_caller import call_llm, DEFAULT_MODELS, MODEL_ALIASES, build_panel
from cli_caller import reset_live_panel
from comparator import compare_round1, summarize_disagreement
from judge import run_r2_convergence, run_r2_debate, run_round3, tally_r2_debate
from consensus import build_gold_standard, save_gold_standard, print_summary
from regression import (
    load_gold_standard, select_regression_verses, print_regression_plan,
)
# s10 v2 deltas: externalized conventions (D1-E), the scribe (D3), D-deliberation.
import conventions as conv_mod
from conventions import build_conventions_preamble, load_conventions


def parse_range(s):
    """Parse '1-5' or '1,3,5-7' into list of ints."""
    result = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            result.extend(range(int(a), int(b) + 1))
        else:
            result.append(int(part))
    return result


def get_verse_list(book_chi, chapters, sec_range=None):
    """Get list of (chap, sec) for given chapters, fetching verse counts from API."""
    verses = []
    for chap in chapters:
        chap_data = fetch_chap_cached(book_chi, chap, "unv", strong=0)
        secs = sorted(chap_data.keys())
        if sec_range:
            secs = [s for s in secs if s in sec_range]
        for sec in secs:
            verses.append((chap, sec))
    return verses


def _run_patch_regression(model_name, prompt_version, base_prompt, patch_text,
                          convergence_results, verse_data, models,
                          target_version, sn_field, verbose,
                          instability_level="mild", naked=False):
    """Minor 回測: re-run patched model solo on past verses.

    Sampling rate scales with instability level:
      - mild:     10% of past verses
      - moderate: 20% of past verses
      - strong:   30% + all past trigger2 verses for this model

    Compares new stability to model's own previous stability.
    Returns True if patch is OK, False if regression detected.
    """
    import random
    from llm_direct_sn_unv2notyet import build_user_prompt
    from comparator import texts_match
    from judge import _eng_to_chi

    # Sampling rate by instability level
    sample_rates = {"mild": 0.10, "moderate": 0.20, "strong": 0.30}
    sample_rate = sample_rates.get(instability_level, 0.10)

    # Collect past verses with convergence data for this model
    past_verses = []
    model_conv = convergence_results.get(model_name, {})
    for vk, cv in model_conv.items():
        if cv.get("stable_at") and cv.get("stable_at") != "unstable":
            past_verses.append(vk)

    if not past_verses:
        print(f"    Patch 回測: no past data for {model_name}, skipping")
        return True

    # Sample by level rate, minimum 1
    sample_size = max(1, int(len(past_verses) * sample_rate))
    sampled = random.sample(past_verses, min(sample_size, len(past_verses)))

    print(f"    Patch 回測: testing {len(sampled)}/{len(past_verses)} past verses for {model_name}")

    patched_prompt = base_prompt + "\n\n" + patch_text

    # Find model info
    model_info = None
    for m in models:
        if m["name"] == model_name:
            model_info = m
            break
    if not model_info:
        return True

    for vk in sampled:
        old_conv = model_conv[vk]
        old_stable = old_conv.get("stable_at", "unstable")
        vdata = verse_data.get(vk)
        if not vdata:
            continue

        book_chi = _eng_to_chi(vdata.get("book", ""))
        chap, sec = vk

        # Do one blind call with patched prompt
        user_prompt = _user_prompt(
            vdata["unv_sn"], vdata["lcc_original"],
            target_version, book_chi, chap, sec, naked=naked)

        result = call_llm(
            brand=model_info["brand"], model=model_info["model"],
            system_prompt=patched_prompt,
            user_prompt=user_prompt,
            target_version=target_version,
            verbose=verbose,
        )

        new_text = result.get(sn_field, "")
        r1_text = old_conv.get("attempts", [""])[0]  # R1 output

        # Check: does new output match R1? (best case = stable at R1)
        if new_text and r1_text and texts_match(new_text, r1_text):
            new_stable = "R1"
        elif new_text:
            new_stable = "R2a"  # produced something different but non-empty
        else:
            new_stable = "unstable"

        old_rank = STABILITY_ORDER.get(old_stable, 5)
        new_rank = STABILITY_ORDER.get(new_stable, 5)

        if new_rank > old_rank:
            print(f"    REGRESSION on {chap}:{sec}: was {old_stable}, now {new_stable}")
            return False
        else:
            print(f"    {chap}:{sec}: was {old_stable}, now {new_stable} ✓")

    return True


def _get_base_prompt_trigger(prompt_version):
    """Extract the trigger suffix from the base prompt filename.

    e.g., v1.1_Gen_1_1.md → "_Gen_1_1"
          v1.2_joshua.md → "_joshua"
          v1.0.md → "" (baseline, no trigger)
    """
    import re as _re
    prompts_dir = os.path.join(SURVEY_DIR, "prompts")
    if not os.path.isdir(prompts_dir):
        return ""
    for fname in os.listdir(prompts_dir):
        if "-patch-" in fname or "-exp" in fname or "REGRESSION_FAILED" in fname:
            continue
        m = _re.match(rf'^{_re.escape(prompt_version)}(_[\w]+(?:_\d+_\d+)?)?\.md$', fname)
        if m and m.group(1):
            return m.group(1)  # e.g., "_Gen_1_1" or "_joshua"
    return ""


def strip_prompt_comments(text):
    """Strip leading # comment lines from prompt text.

    Removes lines starting with '# ' or bare '#' at the top of the file.
    Preserves '##' markdown headers that are part of the actual prompt.
    Applied to both main prompt and model patches.
    """
    lines = text.split('\n')
    start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith('# ') and stripped != '#':
            start = i
            break
    return '\n'.join(lines[start:]).strip()


def load_prompt_file(prompt_file):
    """Load system prompt from a file (relative to survey1_prompt_evolving/ or absolute)."""
    if not os.path.isabs(prompt_file):
        prompt_file = os.path.join(SURVEY_DIR, prompt_file)
    with open(prompt_file, "r", encoding="utf-8") as f:
        return f.read().strip()


def detect_latest_prompt():
    """Find the latest versioned base prompt file in prompts/ directory.

    Matches: v{ver}.md, v{ver}_{trigger}.md (e.g., v1.1_Gen_1_1.md, v1.2_joshua.md)
    Excludes patch files (contain '-patch-') and experiment files (contain '-exp').
    Returns (prompt_path, version_string) or (None, None) if none found.
    """
    import re
    prompts_dir = os.path.join(SURVEY_DIR, "prompts")
    if not os.path.isdir(prompts_dir):
        return None, None

    version_files = []
    for fname in os.listdir(prompts_dir):
        if "-patch-" in fname or "-exp" in fname or "REGRESSION_FAILED" in fname:
            continue  # skip model patches and experiments
        m = re.match(r'^v(\d+(?:\.\d+)*)(?:_[\w]+(?:_\d+_\d+)?)?\.md$', fname)
        if m:
            ver_str = m.group(1)
            ver_tuple = tuple(int(x) for x in ver_str.split('.'))
            version_files.append((ver_tuple, ver_str, fname))

    if not version_files:
        return None, None

    version_files.sort()
    _, ver_str, fname = version_files[-1]
    return os.path.join(prompts_dir, fname), f"v{ver_str}"


def run_round1(verses, book_chi, book_eng, models, target_version, sn_field,
               system_prompt, force=False, verbose=False):
    """Run Round 1: each model produces SN output for each verse.

    Returns:
        round1_results: {model_name: {(chap,sec): result_dict}}
        verse_data: {(chap,sec): {"unv_sn", "lcc_original", "book"}}
    """
    round1_dir = os.path.join(SURVEY_DIR, "round1_results")
    round1_results = {m["name"]: {} for m in models}
    verse_data = {}
    total = len(verses) * len(models)
    done = 0
    t0 = time.time()

    for chap, sec in verses:
        # Fetch verse pair
        try:
            unv_sn, target_text = fetch_sec_pair(book_chi, chap, sec, target_version)
        except ValueError as e:
            print(f"  SKIP {chap}:{sec} — {e}", flush=True)
            continue

        verse_data[(chap, sec)] = {
            "unv_sn": unv_sn,
            "lcc_original": target_text,
            "book": book_eng,
        }

        user_prompt = build_user_prompt(
            unv_sn, target_text, target_version, book_chi, chap, sec)

        print(f"\n{'─'*50}")
        print(f"  {book_eng} {chap}:{sec}")
        print(f"  UNV: {unv_sn[:100]}...")
        print(f"  LCC: {target_text[:100]}...")

        for model_info in models:
            model_name = model_info["name"]
            brand = model_info["brand"]
            model_id = model_info["model"]

            # Check cache
            result_file = os.path.join(
                round1_dir, model_name, book_eng, str(chap), f"{sec}.json")

            if not force and os.path.isfile(result_file):
                with open(result_file, "r", encoding="utf-8") as f:
                    round1_results[model_name][(chap, sec)] = json.load(f)
                done += 1
                print(f"  [ {model_name} ] cached", flush=True)
                continue

            print(f"  [ {model_name} ] calling...", end=" ", flush=True)

            result = call_llm(
                brand=brand, model=model_id,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                target_version=target_version,
                verbose=verbose,
            )

            # Add metadata
            result["_model"] = model_name
            result["_brand"] = brand

            # Verify SN coverage
            output_sn = result.get(sn_field, "")
            if output_sn and not result.get("error"):
                coverage = verify_sn_coverage(unv_sn, output_sn)
                result["_sn_coverage"] = coverage
                status = "OK" if coverage["perfect"] else f"MISMATCH (missing={coverage['missing']})"
            else:
                status = "ERROR" if result.get("error") else "empty"

            print(f"conf={result.get('confidence', '?')} {status}", flush=True)

            round1_results[model_name][(chap, sec)] = result

            # Save to disk
            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            done += 1
            elapsed = time.time() - t0
            rate = elapsed / 60 / max(done, 1)
            remaining = (total - done) * rate
            print(f"  [{done}/{total}] {elapsed/60:.1f}m elapsed, "
                  f"~{remaining:.1f}m remaining", flush=True)

    return round1_results, verse_data


def main():
    parser = argparse.ArgumentParser(
        description="Gold Standard Builder — 3-Model Consensus")
    parser.add_argument("--book", default="創",
                        help="Chinese book abbreviation (default: 創)")
    parser.add_argument("--chap", default="1-2",
                        help="Chapter range: '1-2' or '1,3,5' (default: 1-2)")
    parser.add_argument("--sec", default=None,
                        help="Verse range: '1-10' or '1,3,5-7' (optional)")
    parser.add_argument("--target-version", default="lcc",
                        help="Target Bible version (default: lcc)")
    parser.add_argument("--prompt-version", default=None,
                        help="Prompt version label (default: auto-detected from latest prompt)")
    parser.add_argument("--prompt-file", default=None,
                        help="Override prompt file (default: latest in prompts/)")
    parser.add_argument("--max-r2-retries", type=int, default=0,
                        help="Max R2 convergence retries after R2a (default: 0 = unlimited, hard cap 26)")
    parser.add_argument("--verse-count", type=int, default=None,
                        help="Process only N verses (from the start of the range)")
    aliases_help = ", ".join(f"{k}={v['model']}" for k, v in MODEL_ALIASES.items() if len(k) <= 10)
    parser.add_argument("--modelsABC", nargs="*", default=None,
                        help=f"3 model slots (comma/space separated). "
                             f"Aliases: {aliases_help}. "
                             f"Example: --modelsABC opus opus opus")
    parser.add_argument("--gold-dir", default=None,
                        help="output dir for gold_standard JSONs "
                             "(default: survey dir's gold_standard/). Use a "
                             "scratch dir to avoid touching the canonical set.")
    parser.add_argument("--naked", action=argparse.BooleanOptionalAction,
                        default=True,
                        help="consensus-on-naked: models place bare numbers; "
                             "shells restored zero-loss by lookup at save time. "
                             "DEFAULT ON (2026-06-14, Joshua). Use --no-naked for "
                             "the legacy shelled path.")
    parser.add_argument("--strip-prompt-comment", action="store_true",
                        help="Strip # comment headers from prompt before feeding to models (survey3 experiment)")
    parser.add_argument("--force", action="store_true",
                        help="Re-run even if cached results exist (default: skip cached)")
    parser.add_argument("--round1-only", action="store_true",
                        help="Run Round 1 only (no judging)")
    parser.add_argument("--skip-round1", action="store_true",
                        help="Skip Round 1, start from comparison")
    parser.add_argument("--show-summary", action="store_true",
                        help="Show gold standard summary and exit")
    parser.add_argument("--show-disagreements", action="store_true",
                        help="Show disagreement details and exit")
    parser.add_argument("--regression", action="store_true",
                        help="Run regression testing")
    parser.add_argument("--trigger-verses", default=None,
                        help="Verses that triggered prompt change: '1:4,1:16'")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi)
    if not book_eng:
        print(f"Unknown book: {book_chi}", file=sys.stderr)
        sys.exit(1)

    target_version = args.target_version
    sn_field = f"{target_version}_sn"

    # Resolve model trio
    if args.modelsABC:
        model_trio = build_panel(args.modelsABC)
    else:
        model_trio = DEFAULT_MODELS

    # Show summary
    if args.show_summary:
        gold = load_gold_standard()
        unresolved = [(k[0], k[1]) for k, v in gold.items()
                      if v.get("resolved_at") == "unresolved"]
        print_summary(gold, unresolved)
        return

    # Show disagreements
    if args.show_disagreements:
        gold = load_gold_standard()
        for verse_key, g in sorted(gold.items()):
            if g.get("resolved_at") != "round1":
                print(f"\n  {g['chap']}:{g['sec']} — resolved at {g['resolved_at']}")
                if g.get("round1"):
                    for model, info in g["round1"].items():
                        print(f"    [{model}] opinion={info.get('opinion')} "
                              f"conf={info.get('confidence')}")
                        print(f"      {info.get('lcc_sn', '')[:120]}")
                if g.get("round2_convergence"):
                    print("    R2 convergence:")
                    for model, info in g["round2_convergence"].items():
                        print(f"      [{model}] stable_at={info.get('stable_at')} "
                              f"converged={info.get('converged')} "
                              f"attempts={info.get('attempt_count')}")
                if g.get("round2"):
                    print("    R2 debate:")
                    for judge, info in g["round2"].items():
                        print(f"      [{judge}] best={info.get('best')} "
                              f"opinion={info.get('opinion')}")
                        if info.get("reasoning"):
                            print(f"        {info['reasoning'][:150]}")
                if g.get("round3"):
                    print("    R3 judgments:")
                    for judge, info in g["round3"].items():
                        verdict = info.get("verdict", "?")
                        if verdict == "all_wrong":
                            print(f"      [{judge}] ALL_WRONG: {info.get('error_identified', '')[:100]}")
                        else:
                            print(f"      [{judge}] PICK best={info.get('best')} "
                                  f"opinion={info.get('opinion')}")
        return

    # Regression testing
    if args.regression:
        gold = load_gold_standard()
        trigger = []
        if args.trigger_verses:
            for v in args.trigger_verses.split(","):
                c, s = v.split(":")
                trigger.append((int(c), int(s)))
        selected = select_regression_verses(gold, trigger)
        print_regression_plan(selected, gold, trigger)
        # TODO: actually run regression (reuse run_round1 + judge on selected)
        print("\n  Regression execution not yet implemented — plan only.")
        return

    # Parse chapters and verses
    chapters = parse_range(args.chap)
    sec_range = set(parse_range(args.sec)) if args.sec else None

    # Load system prompt (before header so version is known)
    if args.prompt_file:
        system_prompt = load_prompt_file(args.prompt_file)
        if args.prompt_version is None:
            import re
            m = re.search(r'v(\d+(?:\.\d+)*)', args.prompt_file)
            args.prompt_version = f"v{m.group(1)}" if m else "unknown"
    else:
        latest_path, latest_ver = detect_latest_prompt()
        if latest_path:
            system_prompt = load_prompt_file(latest_path)
            if args.prompt_version is None:
                args.prompt_version = latest_ver
        else:
            system_prompt = load_system_prompt(target_version)
            if args.prompt_version is None:
                args.prompt_version = "unknown"

    # Strip prompt comments if requested (survey3 experiment)
    if args.strip_prompt_comment:
        system_prompt = strip_prompt_comments(system_prompt)
        print(f"  [--strip-prompt-comment] # comments stripped from prompt")

    # ── s10 D1-E (gate #1): PREPEND externalized conventions.md into the system
    # prompt so every leg's R1/R2/R3 built prompt carries the settled conventions.
    # Empty seed still injects a greppable marker so the wiring is verifiable.
    system_prompt = build_conventions_preamble(target_version) + system_prompt
    print(f"  [conventions] {len(load_conventions())} active rule(s) prepended "
          f"into every leg's prompt")

    # Get verse list
    verses = get_verse_list(book_chi, chapters, sec_range)
    if args.verse_count is not None:
        verses = verses[:args.verse_count]

    # ── Set up run log with verse info ──
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = os.path.join(SURVEY_DIR, "run_logs")
    os.makedirs(logs_dir, exist_ok=True)
    first_chap, first_sec = verses[0] if verses else (0, 0)
    log_start = f"{book_eng}_{first_chap}_{first_sec}"
    log_file = os.path.join(logs_dir, f"run_{run_timestamp}_{log_start}-.log")
    _setup_tee(log_file)

    # Register rename on exit (normal or Ctrl-C)
    _log_rename_state["log_file"] = log_file
    _log_rename_state["book_eng"] = book_eng
    _log_rename_state["first_chap"] = first_chap
    _log_rename_state["first_sec"] = first_sec
    atexit.register(_rename_log_on_exit)
    signal.signal(signal.SIGINT, _signal_handler)

    print(f"\n{'='*60}")
    print(f"  Gold Standard: {book_eng} chapters {args.chap}")
    print(f"  Target: {target_version.upper()}")
    print(f"  Models: {', '.join(m['name'] for m in model_trio)}")
    print(f"  Prompt: {args.prompt_version}")
    if args.prompt_file:
        print(f"  Prompt file: {args.prompt_file}")
    print(f"  Max R2 retries: {args.max_r2_retries}")
    if args.verse_count is not None:
        print(f"  Verse count:  {args.verse_count}")
    print(f"  Verses: {len(verses)}")
    print(f"  Log: {log_file}")
    print(f"{'='*60}")

    # ── Per-verse pipeline ─────────────────────────────────────────────
    # Each verse goes through R1 → compare → R2 → R3 → gold standard
    # before moving to the next. If R3 triggers prompt evolution, we stop.

    round1_dir = os.path.join(SURVEY_DIR, "round1_results")
    round1_results = {m["name"]: {} for m in model_trio}
    verse_data = {}
    convergence_results = {}
    round2_judgments = {}
    round3_judgments = {}
    all_unanimous = []
    all_disagreed = []
    all_trigger1 = []   # (verse_key, verse_data_entry, convergence_for_verse)
    all_trigger2 = []   # (verse_key, gold_entry)
    all_deliberation = []  # s10 D-tier: (verse_key, gold_entry|None) — terminal post-C

    for verse_idx, (chap, sec) in enumerate(verses):
        verse_key = (chap, sec)
        _update_last_verse(book_eng, chap, sec)

        # ── s10 D1-E (gate #3): per-verse reset — /clear each LIVE leg so this
        # verse starts blind/independent (R1 amnesia restored). Headless legs are
        # already per-call amnesiac, so a failed /clear degrades safely.
        reset_live_panel(verbose=args.verbose)

        if verse_idx > 0:
            print("\n\n\n\n\n")
        print(f"{'='*60}")
        print(f"  [{ts()}] [{verse_idx+1}/{len(verses)}] {book_eng} {chap}:{sec} main prompt {args.prompt_version}")
        print(f"{'='*60}")

        # ── Fetch verse data ──
        try:
            unv_sn, target_text = fetch_sec_pair(book_chi, chap, sec, target_version)
        except ValueError as e:
            print(f"  SKIP {chap}:{sec} — {e}", flush=True)
            continue

        verse_data[verse_key] = {
            "unv_sn": unv_sn,
            "lcc_original": target_text,
            "book": book_eng,
        }

        print(f"  UNV: {unv_sn[:100]}...")
        print(f"  LCC: {target_text[:100]}...")

        # ── R1: All 3 models produce output ──
        print(f"\n  ── R1 [{ts()}] ──")
        user_prompt = _user_prompt(
            unv_sn, target_text, target_version, book_chi, chap, sec,
            naked=args.naked)

        for model_info in model_trio:
            model_name = model_info["name"]
            brand = model_info["brand"]
            model_id = model_info["model"]

            result_file = os.path.join(
                round1_dir, model_name, book_eng, str(chap), f"{sec}.json")

            # Load model-specific patch info (for display, even when cached)
            model_patch, patch_ver = load_model_patch(model_name, args.prompt_version)
            if model_patch and args.strip_prompt_comment:
                model_patch = strip_prompt_comments(model_patch)
            model_label = f"{model_name} (patch {patch_ver})" if model_patch else model_name

            if not args.force and os.path.isfile(result_file):
                with open(result_file, "r", encoding="utf-8") as f:
                    round1_results[model_name][verse_key] = json.load(f)
                print(f"  [ {model_label} ] cached", flush=True)
                continue
            model_prompt = system_prompt + ("\n\n" + model_patch if model_patch else "")
            print(f"  [ {model_label} ] calling...", end=" ", flush=True)

            t_start = time.time()
            result = call_llm(
                brand=brand, model=model_id,
                system_prompt=model_prompt,
                user_prompt=user_prompt,
                target_version=target_version,
                verbose=args.verbose,
            )
            elapsed_s = int(time.time() - t_start)

            result["_model"] = model_name
            result["_brand"] = brand

            output_sn = result.get(sn_field, "")
            if output_sn and not result.get("error"):
                coverage = _coverage(unv_sn, output_sn, naked=args.naked)
                result["_sn_coverage"] = coverage
                status = "OK" if coverage["perfect"] else f"MISMATCH (missing={coverage['missing']})"
            else:
                status = "ERROR" if result.get("error") else "empty"

            print(f"conf={result.get('confidence', '?')} {status} {elapsed_s}s", flush=True)

            round1_results[model_name][verse_key] = result

            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        if args.round1_only:
            continue

        # ── Compare: unanimous? ──
        unanimous_v, disagreed_v = compare_round1(round1_results, sn_field,
                                                   verse_keys=[verse_key])
        if unanimous_v:
            print(f"  → UNANIMOUS [{ts()}]", flush=True)
            all_unanimous.append(verse_key)
            continue

        print(f"  → DISAGREED", flush=True)
        all_disagreed.append(verse_key)

        # ── R2 Phase 1: Convergence ──
        print(f"\n  ── R2 Convergence [{ts()}] (max_retries={args.max_r2_retries}) ──")
        conv = run_r2_convergence(
            verses=[verse_key],
            round1_results=round1_results,
            verse_data=verse_data,
            models=model_trio,
            system_prompt=system_prompt,
            naked=args.naked,
            target_version=target_version,
            sn_field=sn_field,
            max_retries=args.max_r2_retries,
            verbose=args.verbose,
            force=args.force,
        )
        for m in conv:
            convergence_results.setdefault(m, {}).update(conv[m])

        # ── R2 Phase 1.5: Convergence Analysis (AD-2: Level + Distance) ──
        models_list = [m["name"] for m in model_trio]
        model_levels = {}
        for m in models_list:
            conv_data = convergence_results.get(m, {}).get(verse_key, {})
            model_levels[m] = get_stability_level(conv_data)

        level_names = {-1: "UNAVAILABLE", 0: "Easy", 1: "Mild", 2: "Moderate", 3: "Strong"}

        # Separate available from unavailable models
        available_models = [m for m in models_list if model_levels[m] >= 0]
        unavailable_models = [m for m in models_list if model_levels[m] == -1]

        print(f"\n  ── R2 Convergence Analysis [{ts()}] ──")
        for m in models_list:
            print(f"    [{m}] Level {model_levels[m]} ({level_names.get(model_levels[m], '?')})")

        if unavailable_models:
            print(f"\n    ⚠ UNAVAILABLE (rate-limited): {unavailable_models}")
            print(f"    STOPPING — one or more models rate-limited. Fix and retry.")
            print(f"    (Use --modelsABC to exclude the unavailable model, or wait for rate limit reset)")
            break

        # Compute avg only over available models
        avg_level = sum(model_levels[m] for m in available_models) / len(available_models)
        print(f"    Average (available only): {avg_level:.1f}")

        # For trigger checks — only available models
        easy_models = [m for m in available_models if model_levels[m] == 0]
        hard_models = [m for m in available_models if model_levels[m] > 0]

        # TRIGGER 1: avg ≥ 2 → all struggling → early prompt evolution
        # AD-3: confirmation run — re-run convergence once to filter random noise
        # Only fires if ALL available models are struggling (not due to unavailability)
        if len(unavailable_models) == 0 and avg_level >= TRIGGER1_MIN_AVG:
            print(f"\n  {'*'*60}")
            print(f"  [{ts()}] TRIGGER 1 CANDIDATE: ALL STRUGGLING (avg={avg_level:.1f} ≥ {TRIGGER1_MIN_AVG})")
            print(f"  AD-3: Running confirmation re-run to filter random noise...")
            print(f"  {'*'*60}")

            # Confirmation run: re-do R2 convergence for all models on same verse
            # Delete cached convergence for this verse first
            for m_name in models_list:
                conv_file = os.path.join(SURVEY_DIR, "round2_results",
                                        m_name, book_eng, f"{chap}_{sec}_convergence.json")
                if os.path.isfile(conv_file):
                    os.remove(conv_file)

            print(f"\n  ── Confirmation R2 Convergence [{ts()}] ──")
            conv2 = run_r2_convergence(
                verses=[verse_key],
                round1_results=round1_results,
                verse_data=verse_data,
                models=model_trio,
                system_prompt=system_prompt,
                naked=args.naked,
                target_version=target_version,
                sn_field=sn_field,
                max_retries=args.max_r2_retries,
                verbose=args.verbose,
                force=True,
            )
            for m in conv2:
                convergence_results.setdefault(m, {}).update(conv2[m])

            # Re-classify levels after confirmation run
            confirm_levels = {}
            for m in models_list:
                conv_data = convergence_results.get(m, {}).get(verse_key, {})
                confirm_levels[m] = get_stability_level(conv_data)

            confirm_available = [m for m in models_list if confirm_levels[m] >= 0]
            if confirm_available:
                confirm_avg = sum(confirm_levels[m] for m in confirm_available) / len(confirm_available)
            else:
                confirm_avg = 0

            print(f"\n  ── Confirmation Analysis [{ts()}] ──")
            for m in models_list:
                print(f"    [{m}] Level {confirm_levels[m]} ({level_names.get(confirm_levels[m], '?')})")
            print(f"    Confirmation avg: {confirm_avg:.1f}")

            if confirm_avg >= TRIGGER1_MIN_AVG:
                print(f"\n  ✅ CONFIRMED: still all struggling (avg={confirm_avg:.1f})")
                print(f"  Trigger 1 confirmed — proceeding with prompt evolution.")
            else:
                print(f"\n  ❌ NOT CONFIRMED: avg dropped to {confirm_avg:.1f} (was {avg_level:.1f})")
                print(f"  Random noise — skipping Trigger 1. Proceeding to normal debate.")
                # Update model_levels with confirmation results
                model_levels = confirm_levels
                avg_level = confirm_avg
                easy_models = [m for m in confirm_available if confirm_levels[m] == 0]
                hard_models = [m for m in confirm_available if confirm_levels[m] > 0]
                # Fall through to Trigger 2 check / debate
                pass  # don't enter the evolution block below

        if len(unavailable_models) == 0 and avg_level >= TRIGGER1_MIN_AVG:
            # Trigger 1 confirmed (or first detection that survived confirmation)
            for m in models_list:
                c = convergence_results.get(m, {}).get(verse_key, {})
                print(f"    [{m}] stable_at={c.get('stable_at','?')} "
                      f"attempts={len(c.get('attempts', []))}")
            # Save evolution record
            evo_record = {
                "verse": f"{chap}:{sec}",
                "book": book_eng,
                "trigger": "r2_all_unstable",
                "prompt_from": args.prompt_version,
                "prompt_to": None,
                "convergence": {m: {
                    "stable_at": convergence_results.get(m, {}).get(verse_key, {}).get("stable_at", "?"),
                    "attempts": convergence_results.get(m, {}).get(verse_key, {}).get("attempts", []),
                } for m in models_list},
                "timestamp": datetime.now().isoformat(),
            }
            evo_dir = os.path.join(SURVEY_DIR, "round2_results",
                                   "prompt_evolution", book_eng)
            os.makedirs(evo_dir, exist_ok=True)
            evo_path = os.path.join(evo_dir, f"{chap}_{sec}_evolution_record.json")
            with open(evo_path, "w", encoding="utf-8") as f:
                json.dump(evo_record, f, indent=2, ensure_ascii=False)
            print(f"  Evolution record saved: {evo_path}")

            # ── s10 (gate #4): Trigger-1 = prompt/convention bad → evolve a
            # CONVENTION (NOT a prompt +0.1 bump). If no candidate passes the
            # regression gate, the verse is genuinely ambiguous → D-deliberation
            # (gate #2). The run CONTINUES — conventions accumulate live; there is
            # no break / human prompt-fix. Trigger-2's model-patch path is untouched.
            print(f"\n  Trigger 1 → conventions write-path (s10)...")
            conv_ctx = "; ".join(
                f"{m} stable_at={convergence_results.get(m, {}).get(verse_key, {}).get('stable_at','?')}"
                for m in models_list)
            outcome, d_entry = conv_mod.handle_collective_error(
                verse_key, reason="Trigger-1",
                error_descriptions=["All 3 models unstable in R2 convergence — "
                                    "prompt/convention may be ambiguous"],
                convergence_context=conv_ctx,
                system_prompt=system_prompt, book_chi=book_chi, book_eng=book_eng,
                models=model_trio, target_version=target_version, sn_field=sn_field,
                round1_results=round1_results, verse_data=verse_data,
                naked=args.naked, verbose=args.verbose)
            evo_record["resolution"] = outcome
            with open(evo_path, "w", encoding="utf-8") as f:
                json.dump(evo_record, f, indent=2, ensure_ascii=False)
            if outcome == "deliberation":
                all_deliberation.append((verse_key, d_entry))

            # Collect the trigger verse for gold (r2_early_evolution unless D
            # resolved it — D entries override in build_gold_standard). AD-1: don't
            # save directly.
            conv_for_verse = {m: convergence_results.get(m, {}).get(verse_key, {})
                              for m in models_list}
            all_trigger1.append((verse_key, verse_data[verse_key], conv_for_verse))
            all_disagreed.remove(verse_key)  # was added at DISAGREED, now handled
            # s10: do NOT break — conventions are live; continue the run.
            continue

        # TRIGGER 2: distance-based (AD-2)
        # Find all pairs of agreeing AVAILABLE models, check distance to the third
        trigger2_fired = False
        from comparator import texts_match
        for i, m1 in enumerate(available_models):
            for m2 in available_models[i+1:]:
                others = [m for m in available_models if m != m1 and m != m2]
                if not others:
                    continue  # only 2 available models, no third to check
                m3 = others[0]
                t1 = convergence_results[m1].get(verse_key, {}).get("stable_result", "")
                t2 = convergence_results[m2].get(verse_key, {}).get("stable_result", "")
                if t1 and t2 and texts_match(t1, t2):
                    agreed_avg = (model_levels[m1] + model_levels[m2]) / 2.0
                    weak_level = model_levels[m3]
                    distance = weak_level - agreed_avg
                    if distance >= TRIGGER2_MIN_DISTANCE:
                        easy_models = [m1, m2]
                        unstable_model = m3
                        trigger2_fired = True
                        print(f"\n  {'*'*60}")
                        print(f"  [{ts()}] TRIGGER 2: {unstable_model} (L{weak_level}) unstable, "
                              f"{easy_models} (avg L{agreed_avg:.1f}) agree "
                              f"[distance={distance:.1f} ≥ {TRIGGER2_MIN_DISTANCE}]")
                        print(f"  Auto-resolving with 2/3 output. Generating model patch.")
                        print(f"  {'*'*60}")
                        break
            if trigger2_fired:
                break

        if trigger2_fired:
            # Distance-based validation (AD-2 / TRIGGER2_DESIGN_REVIEW)
            # distance = 2.0 → ask weak model to validate
            # distance ≥ 3.0 → skip validation, direct auto-resolve
            if distance < 3.0:
                from judge import validate_trigger2
                print(f"\n  Distance={distance:.1f} < 3.0 — asking {unstable_model} to validate...")
                agrees, val_reasoning = validate_trigger2(
                    unstable_model=unstable_model,
                    stable_output=t1,
                    unv_sn=verse_data[verse_key]["unv_sn"],
                    lcc_original=verse_data[verse_key]["lcc_original"],
                    models=model_trio,
                    target_version=target_version,
                    verbose=args.verbose,
                    naked=args.naked,
                )
                if not agrees:
                    print(f"  {unstable_model} DISAGREES — routing to normal R2 debate.")
                    print(f"  (Patch still generated for future verses)")
                    # Generate patch but don't auto-resolve — fall through to debate
                    from judge import generate_model_patch
                    unstable_conv = convergence_results[unstable_model][verse_key]
                    current_patch, current_patch_ver = load_model_patch(
                        unstable_model, args.prompt_version)
                    patch_text, patch_record = generate_model_patch(
                        unstable_model=unstable_model,
                        unstable_attempts=unstable_conv.get("attempts", []),
                        stable_output=t1,
                        unv_sn=verse_data[verse_key]["unv_sn"],
                        stable_models=easy_models,
                        models=model_trio,
                        target_version=target_version,
                        verse_key=verse_key,
                        book_eng=book_eng,
                        existing_patch=current_patch,
                        verbose=args.verbose,
                        converged=unstable_conv.get("converged", True),
                        naked=args.naked,
                    )
                    if patch_text:
                        patch_ver = next_patch_version(unstable_model, args.prompt_version)
                        base_trigger = _get_base_prompt_trigger(args.prompt_version)
                        patch_trigger = f"{book_eng}_{chap}_{sec}"
                        patch_fname = f"{args.prompt_version}{base_trigger}.{unstable_model}-patch-{patch_ver}_{patch_trigger}.md"
                        patch_path = os.path.join(SURVEY_DIR, "prompts", patch_fname)
                        with open(patch_path, "w", encoding="utf-8") as f:
                            f.write(patch_text)
                        print(f"  Patch saved: {patch_fname} (for future verses)")
                    # Don't auto-resolve — fall through to normal debate
                    trigger2_fired = False
                else:
                    print(f"  {unstable_model} agrees — proceeding with auto-resolve (3/3 with reasoning)")
            else:
                print(f"\n  Distance={distance:.1f} ≥ 3.0 — direct auto-resolve (skip validation)")

        if trigger2_fired:

                # Generate model patch
                from judge import generate_model_patch
                unstable_conv = convergence_results[unstable_model][verse_key]
                # Load existing patch so the model can incorporate it
                current_patch, current_patch_ver = load_model_patch(
                    unstable_model, args.prompt_version)
                if current_patch:
                    print(f"  Existing patch {current_patch_ver} will be fed to {unstable_model} for evolution")

                # Collect past trigger2 verse keys for this model
                past_t2_verses = []
                t2_patches_dir = os.path.join(
                    SURVEY_DIR, "round2_results", unstable_model,
                    book_eng, "trigger2_patches")
                if os.path.isdir(t2_patches_dir):
                    for fname in os.listdir(t2_patches_dir):
                        if fname.endswith("_patch_record.json"):
                            parts = fname.replace("_patch_record.json", "").split("_")
                            if len(parts) == 2:
                                past_t2_verses.append(f"{parts[0]}:{parts[1]}")

                patch_text, patch_record = generate_model_patch(
                    unstable_model=unstable_model,
                    unstable_attempts=unstable_conv.get("attempts", []),
                    stable_output=t1,
                    unv_sn=verse_data[verse_key]["unv_sn"],
                    stable_models=easy_models,
                    models=model_trio,
                    target_version=target_version,
                    verse_key=verse_key,
                    book_eng=book_eng,
                    existing_patch=current_patch,
                    verbose=args.verbose,
                    converged=unstable_conv.get("converged", True),
                    past_trigger2_verses=past_t2_verses if past_t2_verses else None,
                    naked=args.naked,
                )

                if patch_text:
                    # Save patch — filename includes base prompt trigger + patch trigger
                    patch_ver = next_patch_version(unstable_model, args.prompt_version)
                    base_trigger = _get_base_prompt_trigger(args.prompt_version)
                    patch_trigger = f"{book_eng}_{chap}_{sec}"
                    patch_fname = f"{args.prompt_version}{base_trigger}.{unstable_model}-patch-{patch_ver}_{patch_trigger}.md"
                    patch_path = os.path.join(SURVEY_DIR, "prompts", patch_fname)

                    # Build self-documenting header with full context
                    unstable_conv = convergence_results[unstable_model][verse_key]
                    attempt_summary = []
                    a_labels = ["R1", "R2a", "R2b", "R2c", "R2d", "R2e", "R2f"]
                    for ai, att in enumerate(unstable_conv.get("attempts", [])):
                        lbl = a_labels[ai] if ai < len(a_labels) else f"attempt_{ai}"
                        attempt_summary.append(f"#   {lbl}: {att[:120]}{'...' if len(att) > 120 else ''}")
                    feedback_summary = []
                    for fb_model, fb_text in patch_record.get("feedbacks", {}).items():
                        feedback_summary.append(f"# [{fb_model}] feedback:")
                        for line in fb_text.split('\n')[:5]:
                            feedback_summary.append(f"#   {line[:120]}")
                        if len(fb_text.split('\n')) > 5:
                            feedback_summary.append(f"#   ... ({len(fb_text)} chars total)")

                    patch_level = patch_record.get("instability_level", "mild")
                    patch_score = patch_record.get("instability_score", "?")
                    patch_unique = patch_record.get("unique_output_count", "?")
                    header_lines = [
                        f"# Patch {patch_ver} for {unstable_model}",
                        f"# Triggered by: {book_eng} {chap}:{sec}",
                        f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        f"# Base prompt: {args.prompt_version}",
                        f"# Stable models: {', '.join(easy_models)}",
                        f"# Instability: {patch_level} (score={patch_score}, unique_outputs={patch_unique})",
                        f"#",
                        f"# --- Convergence story ---",
                        f"# {unstable_model} failed to converge easily "
                        f"(stable_at={unstable_conv.get('stable_at', '?')}, "
                        f"{len(unstable_conv.get('attempts', []))} attempts)",
                        f"# while {', '.join(easy_models)} agreed on the same output.",
                        f"#",
                        f"# {unstable_model}'s attempts:",
                        *attempt_summary,
                        f"#",
                        f"# --- Feedback from stable models ---",
                        *feedback_summary,
                        f"#",
                        f"# --- Self-patch (written by {unstable_model}) ---",
                        f"",
                    ]
                    header = '\n'.join(header_lines) + '\n'

                    with open(patch_path, "w", encoding="utf-8") as f:
                        f.write(header + patch_text)
                    print(f"  Patch saved: {patch_fname}")

                    # Minor 回測: solo self-comparison (sampling scales with instability)
                    patch_level = patch_record.get("instability_level", "mild")
                    patch_ok = _run_patch_regression(
                        unstable_model, args.prompt_version,
                        system_prompt, patch_text,
                        convergence_results, verse_data,
                        model_trio, target_version, sn_field,
                        args.verbose,
                        instability_level=patch_level, naked=args.naked)

                    if not patch_ok:
                        print(f"  PATCH REVERTED — made {unstable_model} less stable")
                        os.remove(patch_path)
                    else:
                        print(f"  Patch REGRESSION TEST PASSED for {unstable_model}")

                # Use the 2 agreeing models' output as gold standard
                # Mark as r2_model_patch resolved
                gold_entry = {
                    "book": book_eng, "chap": chap, "sec": sec,
                    "lcc_sn": t1,
                    "lcc_original": verse_data[verse_key]["lcc_original"],
                    "unv_sn_reference": verse_data[verse_key]["unv_sn"],
                    "resolved_at": "r2_model_patch",
                    "prompt_version": args.prompt_version,
                    "round1": {m: {
                        "lcc_sn": round1_results[m].get(verse_key, {}).get(sn_field, ""),
                        "confidence": round1_results[m].get(verse_key, {}).get("confidence", 0),
                        "opinion": "majority" if m in easy_models else "unstable",
                    } for m in models_list},
                    "round2_convergence": {m: {
                        "stable_result": convergence_results.get(m, {}).get(verse_key, {}).get("stable_result", ""),
                        "converged": convergence_results.get(m, {}).get(verse_key, {}).get("converged", False),
                        "stable_at": convergence_results.get(m, {}).get(verse_key, {}).get("stable_at", "?"),
                        "attempt_count": len(convergence_results.get(m, {}).get(verse_key, {}).get("attempts", [])),
                    } for m in models_list},
                    "round2": None,
                    "round3": None,
                    "trigger2_model": unstable_model,
                    "trigger2_instability": {
                        "level": patch_record.get("instability_level", "mild"),
                        "score": patch_record.get("instability_score", 0),
                        "unique_outputs": patch_record.get("unique_output_count", 0),
                    },
                }
                # Collect for build_gold_standard() — don't save directly (AD-1)
                all_trigger2.append((verse_key, gold_entry))
                all_disagreed.remove(verse_key)  # was added at DISAGREED, now resolved
                print(f"  → R2 TRIGGER 2 RESOLVED [{ts()}] (2/3 agree, patch for {unstable_model})")
                continue

        # ── R2 Phase 2: Debate ──
        print(f"\n  ── R2 Debate [{ts()}] ──")
        r2j = run_r2_debate(
            verses=[verse_key],
            convergence_results=convergence_results,
            verse_data=verse_data,
            models=model_trio,
            target_version=target_version,
            sn_field=sn_field,
            verbose=args.verbose,
            force=args.force,
            naked=args.naked,
        )
        round2_judgments.update(r2j)

        # Check R2 result
        r2 = round2_judgments.get(verse_key, {})
        if r2:
            winner, _ = tally_r2_debate(r2, convergence_results, sn_field)
            if winner is not None:
                votes_str = ",".join(
                    j.get("best", "?") for j in r2.values())
                print(f"  → R2 RESOLVED [{ts()}] (winner={winner} {votes_str})", flush=True)
                continue

        # ── R3: Dual-capability ──
        print(f"\n  ── R3 Final Arbitration [{ts()}] ──")
        r3j = run_round3(
            verses=[verse_key],
            convergence_results=convergence_results,
            round2_judgments=round2_judgments,
            verse_data=verse_data,
            models=model_trio,
            target_version=target_version,
            sn_field=sn_field,
            verbose=args.verbose,
            force=args.force,
            naked=args.naked,
        )
        round3_judgments.update(r3j)

        # Check R3 result — did it trigger prompt evolution?
        from judge import tally_r3_judgments
        r3 = round3_judgments.get(verse_key, {})
        if r3:
            outcome, details = tally_r3_judgments(r3, convergence_results)
            if outcome == "resolved":
                winner_label, _ = details
                r3_votes_str = ",".join(
                    j.get("best", j.get("verdict", "?")) for j in r3.values())
                print(f"  → R3 RESOLVED [{ts()}] (winner={winner_label} {r3_votes_str})", flush=True)
            elif outcome == "prompt_evolution":
                print(f"\n  {'*'*60}")
                print(f"  PROMPT EVOLUTION TRIGGERED at {chap}:{sec}")
                print(f"  {'*'*60}")
                evo_record = {
                    "verse": f"{chap}:{sec}",
                    "book": book_eng,
                    "trigger": "r3_all_wrong",
                    "prompt_from": args.prompt_version,
                    "prompt_to": None,  # filled when new prompt is drafted
                    "judges": {},
                    "aligned": details["aligned"],
                    "timestamp": datetime.now().isoformat(),
                }
                # Collect each judge's full opinion
                for judge_key, judgment in r3.items():
                    evo_record["judges"][judge_key] = {
                        k: judgment.get(k) for k in
                        ["verdict", "error_identified", "prompt_improvement", "reasoning"]
                    }
                # Save evolution record
                evo_dir = os.path.join(SURVEY_DIR, "round3_results",
                                       "prompt_evolution", book_eng)
                os.makedirs(evo_dir, exist_ok=True)
                evo_path = os.path.join(evo_dir, f"{chap}_{sec}_evolution_record.json")
                with open(evo_path, "w", encoding="utf-8") as f:
                    json.dump(evo_record, f, indent=2, ensure_ascii=False)
                print(f"  Evolution record saved: {evo_path}")

                # Don't collect here — build_gold_standard() handles it (AD-1)
                for i, (err, imp) in enumerate(zip(
                        details["error_descriptions"], details["improvements"])):
                    print(f"    Judge {i+1} error: {err[:150]}")
                    print(f"    Judge {i+1} fix:   {imp[:150]}")

                # ── s10 (gate #4): R3 collective error = prompt/convention bad →
                # evolve a CONVENTION (NOT a prompt +0.1 bump). If no candidate
                # passes the regression gate, the verse is genuinely ambiguous →
                # D-deliberation (gate #2). The run CONTINUES — conventions are
                # live. The verse stays in `disagreed`, so build_gold_standard marks
                # it prompt_evolution unless a D entry overrides it.
                print(f"\n  R3 all_wrong → conventions write-path (s10)...")
                outcome, d_entry = conv_mod.handle_collective_error(
                    verse_key, reason="R3-all_wrong",
                    error_descriptions=details["error_descriptions"],
                    convergence_context="; ".join(
                        i for i in details.get("improvements", []) if i),
                    system_prompt=system_prompt, book_chi=book_chi, book_eng=book_eng,
                    models=model_trio, target_version=target_version, sn_field=sn_field,
                    round1_results=round1_results, verse_data=verse_data,
                    naked=args.naked, verbose=args.verbose)
                evo_record["resolution"] = outcome
                with open(evo_path, "w", encoding="utf-8") as f:
                    json.dump(evo_record, f, indent=2, ensure_ascii=False)
                if outcome == "deliberation":
                    all_deliberation.append((verse_key, d_entry))
                # s10: do NOT break — conventions are live; continue the run.
                continue
            else:
                # ── s10 D-tier (gate #2): C is exhausted (R3 returned unresolved).
                # Fire D-deliberation — the TERMINAL tier replacing s1's "→ human".
                # This is the corrected trigger (C-exhausted), NOT _stability_level.
                print(f"  → R3 UNRESOLVED [{ts()}] → D-deliberation (C exhausted)",
                      flush=True)
                d_entry = conv_mod.run_d_deliberation(
                    verse_key, round1_results, verse_data, model_trio,
                    target_version, sn_field, reason="R3-unresolved",
                    naked=args.naked, verbose=args.verbose)
                all_deliberation.append((verse_key, d_entry))
                continue

    if args.round1_only:
        print(f"\n  Round 1 complete for {len(verses)} verses.")
        return

    # ── Build gold standard for all processed verses ──
    print(f"\n{'='*60}")
    print(f"  BUILDING GOLD STANDARD")
    print(f"{'='*60}")

    gold_standard, unresolved, prompt_evolutions = build_gold_standard(
        unanimous=all_unanimous,
        disagreed=all_disagreed,
        round1_results=round1_results,
        convergence_results=convergence_results,
        round2_judgments=round2_judgments,
        round3_judgments=round3_judgments if round3_judgments else None,
        verse_data=verse_data,
        prompt_version=args.prompt_version,
        sn_field=sn_field,
        trigger1_verses=all_trigger1,
        trigger2_verses=all_trigger2,
        deliberation_verses=all_deliberation,  # s10 D-tier (terminal post-C)
        naked=args.naked,
    )

    save_gold_standard(gold_standard, output_dir=args.gold_dir)
    print_summary(gold_standard, unresolved, prompt_evolutions)

    # ── s10 D3 (gate #4): per-chapter scribe — distill this run's resolved gold
    # into new regression-gated conventions for FUTURE verses. Runs AFTER gold is
    # built (verses must be settled before learning from them).
    scribe_chaps = sorted({c for (c, _s) in gold_standard.keys()})
    for _c in scribe_chaps:
        accepted = conv_mod.run_scribe_for_chapter(
            _c, book_chi, book_eng, gold_standard, model_trio,
            target_version, sn_field, verbose=args.verbose)
        if accepted:
            print(f"  [scribe] ch{_c}: {len(accepted)} new convention(s) accepted")

    # Verify SN coverage on gold standard
    print(f"\n  Verifying SN coverage on gold standard...")
    bad_coverage = 0
    for verse_key, gold in gold_standard.items():
        if gold["resolved_at"] in ("unresolved", "prompt_evolution", "r2_early_evolution"):
            continue
        coverage = verify_sn_coverage(gold["unv_sn_reference"], gold["lcc_sn"])
        if not coverage["perfect"]:
            bad_coverage += 1
            print(f"  WARNING: {gold['chap']}:{gold['sec']} — "
                  f"missing={coverage['missing']} extra={coverage['extra']}")

    if bad_coverage == 0:
        print(f"  All resolved verses have perfect SN coverage.")
    else:
        print(f"  {bad_coverage} verses with imperfect SN coverage.")


if __name__ == "__main__":
    main()
