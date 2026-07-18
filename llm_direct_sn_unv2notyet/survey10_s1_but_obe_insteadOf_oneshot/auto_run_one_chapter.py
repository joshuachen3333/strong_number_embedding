#!/usr/bin/env python3
"""Single-chapter auto-resume gold wrapper — one car, one chapter.

Distilled from auto_run_gen5_7.py (coverage-driven, quota-aware) for the
"parallel fleet, one chapter per car" run (Joshua 2026-07-18): launch this once
per chapter (8, 9, 10, 11, 12 …) so N independent cars burn the token window in
parallel, each owning exactly one Genesis chapter.

Why one-chapter-per-car (vs one wrapper walking many chapters):
  - disjoint gold_standard/Gen/{chap}/ dirs → zero file contention between cars
  - each car's rate-limit backoff is independent — a stalled account on car A
    does not hold up car B
  - max token burn toward the 3-account (opus/agy/gpt) rate-limit ceiling

CONCURRENCY SAFETY — MANDATORY --skip-scribe:
  run_gold_standard's per-chapter scribe + M-rule promotion write SHARED
  conventions.{model}.md files. With ≥2 cars live those writes race. This
  wrapper always passes --skip-scribe so gold building (disjoint per-chapter
  files) is the only thing that runs. Conventions learning is A2-proven Δ≈0
  neutral, so skipping it costs nothing and removes the only shared-write path.

Coverage-driven: each iteration re-derives the MISSING verses for this chapter
(from the actual UNV verse set) and runs only those. The runner skip-caches
already-computed per-model calls, so re-entry after a backoff is near-instant on
the done verses.

Stop policy (same as auto_run_gen5_7):
  rate-limit      -> log model, back off 30min, re-run (auto-continue)
  Trigger-1       -> LOG ONLY (routine s10 conventions path, not a halt)
  no-progress     -> STOP exit 4 (stuck verse; avoid infinite loop)
  all present     -> exit 0

Kill PID-scoped. NEVER `pkill -f run_gold_standard.py` (kills survey1's runner too).
"""
import argparse, subprocess, sys, os, time, glob, json
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)          # llm_direct_sn_unv2notyet/ holds the driver
os.chdir(SURVEY_DIR)
for _p in (SURVEY_DIR, PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from llm_direct_sn_unv2notyet import fetch_chap_cached  # UNV verse set (no hardcode)

MODELS = ["opus", "agy", "gpt"]          # explicit panel (avoids codex-alias error)
BACKOFF_S = 1800
MAX_ITERS = 80


def parse_args():
    ap = argparse.ArgumentParser(description="Single-chapter auto-resume gold wrapper")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", type=int, required=True)
    return ap.parse_args()


ARGS = parse_args()
BOOK = ARGS.book
CHAP = ARGS.chap
GOLD_CH = os.path.join(SURVEY_DIR, "gold_standard", "Gen", str(CHAP))
LOG = os.path.join(SURVEY_DIR, "run_logs",
                   f"auto_ch{CHAP}_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [car ch{CHAP}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def chapter_secs():
    """Full verse set for this chapter, from the live UNV response (authoritative).

    Retries transient FHL network faults (SSL/read timeouts happen when all cars
    hammer qb.php at once) — an unguarded fetch here previously killed cars at
    startup before they ran a single verse.
    """
    for attempt in range(1, 9):
        try:
            return sorted(fetch_chap_cached(BOOK, CHAP, "unv", strong=1))
        except Exception as e:
            wait = min(60, 5 * attempt)
            log(f"UNV fetch attempt {attempt} failed ({type(e).__name__}: {e}); "
                f"retry in {wait}s")
            time.sleep(wait)
    log("UNV fetch failed after 8 attempts — abort car.")
    print("WRAPPER_STATUS=FETCH_FAIL"); sys.exit(6)


def present_secs():
    """Verses with REAL gold — file exists AND carries a non-empty lcc_sn.

    CONTENT check, not file existence: a rate-limit casualty writes an
    `unresolved`/empty-lcc_sn shell file that mere existence would wrongly count
    as done (this bug let the first pass exit DONE with 34 empty shells). A shell
    counts as MISSING so the next pass re-runs it (with --force, since the file
    is already there).
    """
    out = set()
    for f in glob.glob(os.path.join(GOLD_CH, "*.json")):
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


def run_pass(it, secs):
    sec_arg = ",".join(map(str, secs))
    log(f"iter {it}: run --chap {CHAP} --sec {sec_arg}  ({len(secs)} missing)")
    flags = {"rate_limit": False, "trigger1": False, "unavail": "", "rc": None}
    with open(LOG, "a", encoding="utf-8") as lf:
        p = subprocess.Popen(
            [sys.executable, "run_gold_standard.py", "--book", BOOK,
             "--chap", str(CHAP), "--sec", sec_arg,
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


ALL_SECS = chapter_secs()
log(f"=== CAR ch{CHAP} START === total verses={len(ALL_SECS)} "
    f"present={len(present_secs())}")

for it in range(1, MAX_ITERS + 1):
    miss = [v for v in ALL_SECS if v not in present_secs()]
    if not miss:
        log(f"ch{CHAP} ALL {len(ALL_SECS)} verses present — DONE")
        print("WRAPPER_STATUS=DONE"); sys.exit(0)

    before = len(present_secs())
    f = run_pass(it, miss)
    after = len(present_secs())
    log(f"post-iter {it}: present {before}->{after} rc={f['rc']} "
        f"rate_limit={f['rate_limit']} trigger1={f['trigger1']}")

    if f["trigger1"]:
        log("Trigger-1 seen (routine s10 conventions/D path) — not a stop.")

    if not [v for v in ALL_SECS if v not in present_secs()]:
        log(f"ch{CHAP} all present after iter — DONE")
        print("WRAPPER_STATUS=DONE"); sys.exit(0)

    if f["rate_limit"]:
        nxt = datetime.fromtimestamp(time.time() + BACKOFF_S)
        log(f"RATE-LIMITED [{f['unavail'] or 'unspecified'}] — back off "
            f"{BACKOFF_S//60}min; auto-resume ~{nxt:%H:%M}")
        time.sleep(BACKOFF_S)
        continue

    if after == before:
        log(f"NO PROGRESS this iter (rc={f['rc']}), not rate-limit — STOP to avoid "
            f"infinite loop. Likely a stuck verse in ch{CHAP}.")
        print("WRAPPER_STATUS=NO_PROGRESS"); sys.exit(4)

log(f"MAX_ITERS {MAX_ITERS} reached — stopping."); print("WRAPPER_STATUS=MAX_ITERS")
sys.exit(5)
