#!/usr/bin/env python3
"""Timed resume: clean-stop any lingering survey10 gold cars, then relaunch a
coverage-driven fleet to FINISH every incomplete chapter in RANGE.

Joshua 2026-07-19 "三小時後繼續": scheduled 3h out via a nohup sleep-timer. By then
the earlier fleet's stragglers (ch9 opus-non-convergence, ch17) will mostly have
finished or NO_PROGRESS-exited; this guarantees a clean, conflict-free resume on
fresh quota that drives ch8-17 to 241/241.

Clean-stop is PID-scoped and cwd-filtered: it kills only THIS survey's wrapper
processes (auto_run_one_chapter / auto_run_chapters_seq) and run_gold_standard
children whose cwd == this survey dir. It NEVER touches survey1's run_gold_standard
(different cwd) — the standing rule against `pkill -f run_gold_standard.py`.

Text is 100% local now (bible_little.db UNV + bible_lcc.db whole-Genesis LCC), so
the relaunched cars make ZERO FHL calls.
"""
import subprocess, sys, os, time, glob, json, signal
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SURVEY_DIR)
GOLD = os.path.join(SURVEY_DIR, "gold_standard", "Gen")
RANGE = list(range(8, 18))            # ch8..ch17 — drive all to full
TARGET = {8: 22, 9: 29, 10: 32, 11: 32, 12: 20,
          13: 18, 14: 24, 15: 21, 16: 16, 17: 27}
LOG = os.path.join(SURVEY_DIR, "run_logs",
                   f"resume_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(msg):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [resume] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _pids_by_name(needle):
    try:
        out = subprocess.check_output(["pgrep", "-f", needle], text=True)
        return [int(p) for p in out.split()]
    except subprocess.CalledProcessError:
        return []


def _cwd_of(pid):
    try:
        out = subprocess.check_output(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
                                      text=True, stderr=subprocess.DEVNULL)
        for ln in out.splitlines():
            if ln.startswith("n"):
                return ln[1:]
    except Exception:
        pass
    return ""


def clean_stop():
    """Kill this survey's wrappers + its own run_gold_standard children (cwd-scoped)."""
    victims = []
    for name in ("auto_run_one_chapter.py", "auto_run_chapters_seq.py"):
        victims += _pids_by_name(name)
    # run_gold_standard: only ones whose cwd is THIS survey dir (never survey1's)
    for pid in _pids_by_name("run_gold_standard.py"):
        cwd = _cwd_of(pid)
        if cwd and os.path.abspath(cwd) == SURVEY_DIR:
            victims.append(pid)
    victims = sorted(set(victims))
    if not victims:
        log("clean-stop: no lingering survey10 gold cars.")
        return
    log(f"clean-stop: killing {victims}")
    for pid in victims:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(3)
    for pid in victims:                # SIGKILL any survivor
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def has_sn(ch, sec):
    f = os.path.join(GOLD, str(ch), f"{sec}.json")
    if not os.path.exists(f):
        return False
    try:
        return bool((json.load(open(f, encoding="utf-8")).get("lcc_sn") or "").strip())
    except Exception:
        return False


def incomplete_chapters():
    out = []
    for ch in RANGE:
        miss = [v for v in range(1, TARGET[ch] + 1) if not has_sn(ch, v)]
        if miss:
            out.append((ch, miss))
    return out


log(f"=== TIMED RESUME START === range={RANGE[0]}-{RANGE[-1]}")
clean_stop()

todo = incomplete_chapters()
if not todo:
    log("all chapters already full — nothing to resume. DONE")
    sys.exit(0)

log(f"incomplete: " + ", ".join(f"ch{c}({len(m)})" for c, m in todo))
for ch, miss in todo:
    out = os.path.join(SURVEY_DIR, "run_logs", f"nohup_resume_ch{ch}.out")
    p = subprocess.Popen(
        [sys.executable, "auto_run_one_chapter.py", "--chap", str(ch)],
        stdout=open(out, "a"), stderr=subprocess.STDOUT,
        start_new_session=True)              # detach — survive this launcher exiting
    log(f"launched resume car ch{ch} (miss={len(miss)}) → PID {p.pid}")
    time.sleep(4)

log("all resume cars launched. Coverage-driven; each finishes its chapter or "
    "NO_PROGRESS-exits on a stuck (opus-non-convergent) verse.")
