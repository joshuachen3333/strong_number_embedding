#!/usr/bin/env python3
"""Re-run the 17 empty-SN gold shells (rate-limit casualties from the Gen 5-7 run).

CONTEXT (task #8): the Gen 5-7 wrapper (auto_run_gen5_7.py) marked chapters DONE on
FILE EXISTENCE only — it never checked content. 17 verses landed on disk as
`unresolved` shells with an EMPTY `lcc_sn` because all three models were rate-limited
at R2 that pass. This wrapper fixes exactly those, and ONLY those.

DIFFERENCE vs auto_run_gen5_7.py:
  - Coverage = CONTENT check (non-empty lcc_sn), not file existence. A shell counts as
    "missing" until it has real SN.
  - Runs with --force (the shell file already exists; without --force the runner would
    skip it as cached).
  - Target list is the fixed 17-verse set, grouped per chapter.

Everything else mirrors auto_run_gen5_7.py: fail-fast runner wrapped in an outer
retry loop; rate-limit -> log which model, back off 30min, re-probe (auto-continue);
Trigger-1 is a ROUTINE s10 conventions/D-deliberation write-path -> LOG only, never a
stop (copying s1's trigger1->exit3 caused a false stop last run).

Concurrency: survey1 runs its own gold on the SAME opus/agy/gpt accounts -> frequent
rate limits; the backoff loop absorbs them. Kill PID-scoped, NEVER
`pkill -f run_gold_standard.py` (also kills survey1's runner).
"""
import subprocess, sys, os, time, json, glob
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SURVEY_DIR)
GOLD = os.path.join(SURVEY_DIR, "gold_standard", "Gen")
MODELS = ["opus", "agy", "gpt"]
BACKOFF_S = 1800
MAX_ITERS = 80

# The fixed empty-shell set (task #8), grouped by chapter.
TARGET = {
    1: [30],
    2: [23],
    6: [4, 13, 14, 17, 18, 19, 20, 21, 22],
    7: [1, 7, 8, 21, 22, 23],
}

# DEFER: verses on which opus is pathologically non-convergent (endless R2a..R2h
# cycles + D-deliberation that never writes SN). 6:17 ate ~1h50m across TWO full R2
# cycles at iter 6 with zero output. Deferring it to the ABSOLUTE END unblocks the
# other 11 verses; when only deferred verses remain we give each ONE bounded --force
# attempt, then leave it as a documented accept-empty for Joshua rather than looping.
DEFER = {(6, 17)}

LOG = os.path.join(SURVEY_DIR, "run_logs",
                   f"rerun_empty_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [rerun] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def has_sn(ch, sec):
    """True iff the gold file exists AND carries a non-empty lcc_sn."""
    f = os.path.join(GOLD, str(ch), f"{sec}.json")
    if not os.path.exists(f):
        return False
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        return False
    return bool((d.get("lcc_sn") or "").strip())


def missing_first_chapter():
    # Phase 1: all non-deferred verses first.
    for ch in sorted(TARGET):
        miss = [v for v in TARGET[ch] if not has_sn(ch, v) and (ch, v) not in DEFER]
        if miss:
            return ch, miss
    # Phase 2: only deferred verses remain — attempt them (one bounded pass each).
    for ch in sorted(TARGET):
        miss = [v for v in TARGET[ch] if not has_sn(ch, v)]
        if miss:
            return ch, miss
    return None, []


def total_done():
    return sum(1 for ch in TARGET for v in TARGET[ch] if has_sn(ch, v))


TOTAL = sum(len(v) for v in TARGET.values())


def run_chapter(it, ch, secs):
    sec_arg = ",".join(map(str, secs))
    log(f"iteration {it}: --force --chap {ch} --sec {sec_arg}  ({len(secs)} empty shells)")
    flags = {"rate_limit": False, "trigger1": False, "unavail": "", "rc": None}
    with open(LOG, "a", encoding="utf-8") as lf:
        p = subprocess.Popen(
            [sys.executable, "run_gold_standard.py", "--book", "創",
             "--chap", str(ch), "--sec", sec_arg, "--modelsABC", *MODELS, "--force"],
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


log(f"=== RE-RUN 17 EMPTY SHELLS START === target={TARGET}")
log(f"start total_done={total_done()} / {TOTAL}")

for it in range(1, MAX_ITERS + 1):
    ch, miss = missing_first_chapter()
    if ch is None:
        log("ALL 17 shells now carry SN — DONE"); print("RERUN_STATUS=DONE"); sys.exit(0)

    before = total_done()
    f = run_chapter(it, ch, miss)
    after = total_done()
    log(f"post-iter {it}: total_done {before}->{after} rc={f['rc']} "
        f"rate_limit={f['rate_limit']} trigger1={f['trigger1']}")

    # s10 Trigger-1 is a ROUTINE conventions/D-deliberation write-path, NOT a stop.
    if f["trigger1"]:
        log("Trigger-1 seen (s10 routine path) — not a stop; continuing.")

    if missing_first_chapter()[0] is None:
        log("ALL 17 shells filled after iter — DONE"); print("RERUN_STATUS=DONE"); sys.exit(0)

    if f["rate_limit"]:
        nxt = datetime.fromtimestamp(time.time() + BACKOFF_S)
        log(f"RATE-LIMITED [{f['unavail'] or 'unspecified'}] — back off "
            f"{BACKOFF_S//60}min; auto-resume ~{nxt:%H:%M}")
        time.sleep(BACKOFF_S)
        continue

    if after == before:
        log(f"NO PROGRESS this iter (rc={f['rc']}), not rate-limit — STOP to avoid "
            f"infinite loop. Likely a genuinely stuck verse in Gen {ch}.")
        print("RERUN_STATUS=NO_PROGRESS"); sys.exit(4)

log(f"MAX_ITERS {MAX_ITERS} reached — stopping."); print("RERUN_STATUS=MAX_ITERS"); sys.exit(5)
