#!/usr/bin/env python3
"""Auto-resume wrapper: survey10 gold standard Gen 5 -> Gen 7, quota-aware.

Adapted from survey1_prompt_evolving/auto_run_gen3_7.py (s1-obe, 2026-07-04) for
survey10's chapters + explicit model panel. Same rationale:

COVERAGE-DRIVEN: each iteration finds the first chapter with MISSING gold verses and
runs ONLY those verses (--chap N --sec <missing>). Never re-derives done verses; the
runner skip-caches already-computed per-model R1/R2 calls, so re-running a chapter that
is mostly cached is near-instant. Gold is written per completed chapter-pass, so
progress persists incrementally (unlike a single --chap 5-7 pass that writes 0 gold if
interrupted).

Why a wrapper at all: this survey runner has NO built-in auto-resume — cli_caller is
fail-fast and run_gold_standard STOPS on rate-limit ("...rate-limited"). The 30-min
backoff lives in the MAIN driver (llm_direct_sn_unv2notyet.py), not here. This wrapper
supplies the outer retry loop so a codex/agy/opus quota cap auto-continues.

Stop policy:
  rate-limit -> log which model, back off 30min, re-probe by re-running (auto-continue).
  Trigger-1 (prompt evolution) -> STOP exit 3 (human attention; do NOT blind-continue).
  no-progress / crash -> STOP exit 4 (avoid infinite loop).
  all Gen 5-7 verses present -> exit 0.

Concurrency note: survey1 runs its own gold in parallel to ch7 on the SAME
opus/agy/codex accounts (Joshua 2026-07-04, both-concurrent) -> more frequent rate
limits here; the backoff loop absorbs them. Kill this run PID-scoped, NEVER
`pkill -f run_gold_standard.py` (that also kills survey1's runner).
"""
import subprocess, sys, os, time, glob
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SURVEY_DIR)
GOLD = os.path.join(SURVEY_DIR, "gold_standard", "Gen")
TARGET = {5: 32, 6: 22, 7: 24}                 # Genesis verse counts, chapters 5-7
MODELS = ["opus", "agy", "gpt"]                # explicit panel (avoids codex-alias error)
BACKOFF_S = 1800
MAX_ITERS = 80
LOG = os.path.join(SURVEY_DIR, "run_logs",
                   f"auto_gen5_7_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [wrapper] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def present_secs(ch):
    out = set()
    for f in glob.glob(os.path.join(GOLD, str(ch), "*.json")):
        b = os.path.basename(f)[:-5]
        if b.isdigit():
            out.add(int(b))
    return out


def missing_first_chapter():
    for ch in sorted(TARGET):
        miss = [v for v in range(1, TARGET[ch] + 1) if v not in present_secs(ch)]
        if miss:
            return ch, miss
    return None, []


def total_done():
    return sum(len(present_secs(ch)) for ch in TARGET)


def run_chapter(it, ch, secs):
    sec_arg = ",".join(map(str, secs))
    log(f"iteration {it}: run --chap {ch} --sec {sec_arg}  ({len(secs)} missing verses)")
    flags = {"rate_limit": False, "trigger1": False, "unavail": "", "rc": None}
    with open(LOG, "a", encoding="utf-8") as lf:
        p = subprocess.Popen(
            [sys.executable, "run_gold_standard.py", "--book", "創",
             "--chap", str(ch), "--sec", sec_arg, "--modelsABC", *MODELS],
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


log(f"=== AUTO-RUN Gen 5 -> Gen 7 (coverage-driven) START === target={TARGET}")
log(f"start total_done={total_done()} / {sum(TARGET.values())}")

for it in range(1, MAX_ITERS + 1):
    ch, miss = missing_first_chapter()
    if ch is None:
        log("ALL Gen 5-7 verses present — DONE"); print("WRAPPER_STATUS=DONE"); sys.exit(0)

    before = total_done()
    f = run_chapter(it, ch, miss)
    after = total_done()
    log(f"post-iter {it}: total_done {before}->{after} rc={f['rc']} "
        f"rate_limit={f['rate_limit']} trigger1={f['trigger1']}")

    # NOTE (s10 fix): survey1's wrapper stops on Trigger-1 because there it means
    # prompt-evolution needing human review. In survey10, "Trigger 1 confirmed" is a
    # ROUTINE convention/D-deliberation write-path (it does NOT halt the run or need a
    # human). Copying s1's trigger1->exit3 caused a FALSE stop at Gen 6:14 whose real
    # cause was an opus rate-limit. So here we only LOG trigger1 and fall through to the
    # rate-limit backoff / no-progress checks below.
    if f["trigger1"]:
        log("Trigger-1 seen (s10 routine conventions/D-deliberation path) — not a stop; "
            "continuing to rate-limit/progress checks.")

    if missing_first_chapter()[0] is None:
        log("ALL verses present after iter — DONE"); print("WRAPPER_STATUS=DONE"); sys.exit(0)

    if f["rate_limit"]:
        nxt = datetime.fromtimestamp(time.time() + BACKOFF_S)
        log(f"RATE-LIMITED [{f['unavail'] or 'unspecified'}] — back off "
            f"{BACKOFF_S//60}min; auto-resume ~{nxt:%H:%M}")
        time.sleep(BACKOFF_S)
        continue

    if after == before:
        log(f"NO PROGRESS this iter (rc={f['rc']}), not rate-limit/trigger — STOP to "
            f"avoid infinite loop. Likely a stuck verse in Gen {ch}.")
        print("WRAPPER_STATUS=NO_PROGRESS"); sys.exit(4)

log(f"MAX_ITERS {MAX_ITERS} reached — stopping."); print("WRAPPER_STATUS=MAX_ITERS"); sys.exit(5)
