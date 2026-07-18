#!/usr/bin/env python3
"""Sequential multi-chapter gold wrapper — ONE car, chapters one at a time.

Joshua 2026-07-18: after the ch8-12 parallel fleet, run ch13-17 SEQUENTIALLY —
a single process that fills one chapter completely, then moves to the next
(循序跑五個 chap,每次一章). Contrast with auto_run_one_chapter.py (one car per
chapter, all parallel).

Because only ONE process runs, there is NO concurrent conventions-write race, so
--skip-scribe is not required for safety here — but the scribe is a slow,
A2-proven-neutral (Δ≈0) 回測, so we still pass --skip-scribe to avoid ~2h of
fruitless work per chapter. --force overwrites any rate-limit-casualty shell.

Carries the ch8-12 fixes:
  - coverage = CONTENT check (non-empty lcc_sn), NOT file existence — an empty
    shell counts as MISSING and is re-run (the first fleet exited DONE with 34
    empty shells because it only checked existence).
  - startup UNV fetch retries transient FHL SSL/read timeouts.
  - Trigger-1 is LOG-ONLY (routine s10 conventions/D path, not a halt).

Stop policy per chapter:
  rate-limit  -> back off 30min, re-run (auto-continue)
  no-progress -> STOP exit 4 (stuck verse; report which)
  all chapters full -> exit 0

Kill PID-scoped. NEVER `pkill -f run_gold_standard.py` (kills survey1's runner).
"""
import argparse, subprocess, sys, os, time, glob, json
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
os.chdir(SURVEY_DIR)
for _p in (SURVEY_DIR, PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from llm_direct_sn_unv2notyet import fetch_chap_cached

MODELS = ["opus", "agy", "gpt"]
BACKOFF_S = 1800
MAX_ITERS = 200


def parse_chaps(spec):
    """'13-17' or '13,15,17' or '13-15,17' -> sorted unique int list."""
    out = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return sorted(out)


def parse_args():
    ap = argparse.ArgumentParser(description="Sequential multi-chapter gold wrapper")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chaps", required=True, help="e.g. 13-17 or 13,15,17")
    return ap.parse_args()


ARGS = parse_args()
BOOK = ARGS.book
CHAPS = parse_chaps(ARGS.chaps)
GOLD = os.path.join(SURVEY_DIR, "gold_standard", "Gen")
LOG = os.path.join(SURVEY_DIR, "run_logs",
                   f"auto_seq_{ARGS.chaps.replace(',', '_')}_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)
_SECS_CACHE = {}


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [seq {ARGS.chaps}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def chapter_secs(ch):
    """Full verse set for a chapter (retries transient FHL faults). Cached."""
    if ch in _SECS_CACHE:
        return _SECS_CACHE[ch]
    for attempt in range(1, 9):
        try:
            secs = sorted(fetch_chap_cached(BOOK, ch, "unv", strong=1))
            _SECS_CACHE[ch] = secs
            return secs
        except Exception as e:
            wait = min(60, 5 * attempt)
            log(f"ch{ch} UNV fetch attempt {attempt} failed ({type(e).__name__}: {e}); "
                f"retry {wait}s")
            time.sleep(wait)
    log(f"ch{ch} UNV fetch failed after 8 attempts — abort.")
    print("WRAPPER_STATUS=FETCH_FAIL"); sys.exit(6)


def real_gold_secs(ch):
    """Verses with non-empty lcc_sn (content check, not file existence)."""
    out = set()
    for f in glob.glob(os.path.join(GOLD, str(ch), "*.json")):
        b = os.path.basename(f)[:-5]
        if not b.isdigit():
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if (d.get("lcc_sn") or "").strip():
            out.add(int(b))
    return out


def missing_first_chapter():
    for ch in CHAPS:
        miss = [v for v in chapter_secs(ch) if v not in real_gold_secs(ch)]
        if miss:
            return ch, miss
    return None, []


def total_done():
    return sum(len(real_gold_secs(ch)) for ch in CHAPS)


def total_target():
    return sum(len(chapter_secs(ch)) for ch in CHAPS)


def run_chapter(it, ch, secs):
    sec_arg = ",".join(map(str, secs))
    log(f"iter {it}: --force --chap {ch} --sec {sec_arg}  ({len(secs)} missing)")
    flags = {"rate_limit": False, "trigger1": False, "unavail": "", "rc": None}
    with open(LOG, "a", encoding="utf-8") as lf:
        p = subprocess.Popen(
            [sys.executable, "run_gold_standard.py", "--book", BOOK,
             "--chap", str(ch), "--sec", sec_arg,
             "--modelsABC", *MODELS, "--skip-scribe", "--force"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in p.stdout:
            lf.write(line); lf.flush()
            sys.stdout.write(line); sys.stdout.flush()
            if "rate-limited" in line:
                flags["rate_limit"] = True
            if "UNAVAILABLE (rate-limited)" in line:
                flags["unavail"] = line.strip()
            if "Auto-evolving prompt (Trigger 1)" in line or "Trigger 1 confirmed" in line:
                flags["trigger1"] = True
        p.wait()
    flags["rc"] = p.returncode
    return flags


log(f"=== SEQUENTIAL Gen {CHAPS} START === target={total_target()} done={total_done()}")

for it in range(1, MAX_ITERS + 1):
    ch, miss = missing_first_chapter()
    if ch is None:
        log(f"ALL chapters {CHAPS} full ({total_done()}/{total_target()}) — DONE")
        print("WRAPPER_STATUS=DONE"); sys.exit(0)

    before = total_done()
    f = run_chapter(it, ch, miss)
    after = total_done()
    log(f"post-iter {it}: done {before}->{after} rc={f['rc']} "
        f"rate_limit={f['rate_limit']} trigger1={f['trigger1']}")

    if f["trigger1"]:
        log("Trigger-1 seen (routine s10 conventions/D path) — not a stop.")

    if missing_first_chapter()[0] is None:
        log(f"ALL chapters full ({total_done()}/{total_target()}) — DONE")
        print("WRAPPER_STATUS=DONE"); sys.exit(0)

    if f["rate_limit"]:
        nxt = datetime.fromtimestamp(time.time() + BACKOFF_S)
        log(f"RATE-LIMITED [{f['unavail'] or 'unspecified'}] — back off "
            f"{BACKOFF_S//60}min; auto-resume ~{nxt:%H:%M}")
        time.sleep(BACKOFF_S)
        continue

    if after == before:
        log(f"NO PROGRESS this iter (rc={f['rc']}), not rate-limit — STOP to avoid "
            f"infinite loop. Likely a stuck verse in ch{ch} (miss={miss}).")
        print("WRAPPER_STATUS=NO_PROGRESS"); sys.exit(4)

log(f"MAX_ITERS {MAX_ITERS} reached — stopping."); print("WRAPPER_STATUS=MAX_ITERS")
sys.exit(5)
