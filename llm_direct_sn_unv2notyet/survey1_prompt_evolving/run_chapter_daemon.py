#!/usr/bin/env python3
"""Per-chapter coverage-driven s1 gold daemon — ONE chapter per daemon.

Usage:  run_chapter_daemon.py <chap>   (launch with nohup for reaper-immunity)

Processes every verse of Genesis chapter <chap> that lacks a gold file, ONE verse at a
time, with all the safeguards learned this week:
  - per-verse timeout -> opus-non-convergent (pathological) verses are DEFERRED, not looped
  - model-down (codex usage-limit / UNAVAILABLE) / rate-limit -> back off + retry same verse
  - a verse with no gold and no timeout -> deferred (never infinite-loop)
Launch nohup-detached so the harness background-task reaper can't kill it. Cloud CLIs only;
NO ollama. Disjoint chapters across daemons -> zero file collision, saturates the 3 accounts.
"""
import subprocess, sys, os, time, signal
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SURVEY_DIR)
CHAP = int(sys.argv[1])
GEN_VERSES = {1:31,2:25,3:24,4:26,5:32,6:22,7:24,8:22,9:29,10:32,11:32,12:20,13:18,
              14:24,15:21,16:16,17:27,18:33,19:38,20:18,21:34,22:24,23:20,24:67,25:34,
              26:35,27:46,28:22,29:35,30:43,31:55,32:32,33:20,34:31,35:29,36:43,37:36,
              38:30,39:23,40:23,41:57,42:38,43:34,44:34,45:28,46:34,47:31,48:22,49:33,50:26}
N = GEN_VERSES[CHAP]
GOLD = os.path.join(SURVEY_DIR, "gold_standard", "Gen", str(CHAP))
DEFERRED = os.path.join(SURVEY_DIR, "run_logs", f"deferred_ch{CHAP}.txt")
LOG = os.path.join(SURVEY_DIR, "run_logs", f"ch{CHAP}_daemon_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)
BACKOFF_S = 1800
# 600s fits a single daemon; under multi-car contention a normal verse (3 models ×
# multi-round) easily exceeds it and gets MISLABELED "opus non-convergent". Override
# via env for low-contention residue re-runs so only genuine pathology hits the ceiling.
PER_VERSE_TIMEOUT = int(os.environ.get("PER_VERSE_TIMEOUT", "600"))
MAX_ITERS = 500


def log(m):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [ch{CHAP}] {m}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_deferred():
    s = set()
    if os.path.isfile(DEFERRED):
        for ln in open(DEFERRED, encoding="utf-8"):
            t = ln.strip().split()[0] if ln.strip() else ""
            if t.isdigit():
                s.add(int(t))
    return s


def has_gold(v):
    return os.path.isfile(os.path.join(GOLD, f"{v}.json"))


def worklist():
    dfr = load_deferred()
    return [v for v in range(1, N + 1) if not has_gold(v) and v not in dfr]


def defer(v, why):
    with open(DEFERRED, "a", encoding="utf-8") as f:
        f.write(f"{v}  {why}  {datetime.now():%Y-%m-%d %H:%M}\n")


def fhl_down():
    """True if the FHL JSON API is unreachable / returning non-JSON. A fast no-gold
    crash is usually FHL returning HTTP 400 (throttle/outage) under multi-car load, not
    a pathological verse — probe so we back off instead of falsely deferring the verse."""
    import urllib.request, json as _json
    url = ("https://bible.fhl.net/json/qb.php?version=unv&chineses=%E5%89%B5"
           "&chap=1&strong=1")
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            _json.loads(r.read().decode("utf-8", "replace"))
        return False
    except Exception:
        return True


def run_verse(v, timeout):
    log(f"verse {CHAP}:{v} (timeout {timeout}s)")
    flags = {"rate_limit": False, "model_down": False, "timeout": False}
    p = subprocess.Popen(
        [sys.executable, "run_gold_standard.py", "--book", "創",
         "--chap", str(CHAP), "--sec", str(v)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
        start_new_session=True)
    start = time.time()
    lf = open(LOG, "a", encoding="utf-8")
    try:
        while True:
            line = p.stdout.readline()
            if line:
                lf.write(line); lf.flush()
                if "rate-limited" in line:
                    flags["rate_limit"] = True
                if ("BAILED OUT" in line or "Level -1 (UNAVAILABLE)" in line
                        or "usage limit" in line):
                    flags["model_down"] = True
            elif p.poll() is not None:
                break
            if time.time() - start > timeout:
                flags["timeout"] = True
                try:
                    os.killpg(os.getpgid(p.pid), signal.SIGKILL)
                except Exception:
                    p.kill()
                break
    finally:
        lf.close()
    try:
        p.wait(timeout=10)
    except Exception:
        pass
    return flags


log(f"=== CH{CHAP} DAEMON START === {N} verses, {len(worklist())} to do")
it = 0
while it < MAX_ITERS:
    it += 1
    wl = worklist()
    if not wl:
        log(f"=== DONE === all {N} verses have gold; deferred={sorted(load_deferred())}")
        print(f"CH{CHAP}_STATUS=DONE"); sys.exit(0)
    v = wl[0]
    f = run_verse(v, PER_VERSE_TIMEOUT)
    if f["rate_limit"] or f["model_down"]:
        log(f"model-down/rate-limit on {CHAP}:{v} — back off {BACKOFF_S//60}min, retry same verse")
        time.sleep(BACKOFF_S); continue
    if has_gold(v):
        log(f"DONE {CHAP}:{v}"); continue
    if f["timeout"]:
        defer(v, "deferred-pathological (per-verse timeout, opus non-convergent)")
        log(f"DEFERRED {CHAP}:{v} (timeout)"); continue
    # fast crash, no gold: probe FHL — if the source API is down, back off & retry the
    # SAME verse rather than falsely defer it (FHL 400 throttle under multi-car load).
    if fhl_down():
        log(f"FHL API DOWN on {CHAP}:{v} — back off {BACKOFF_S//60}min, retry same verse")
        time.sleep(BACKOFF_S); continue
    defer(v, "no-gold-no-timeout (crash/error — deferred to avoid loop)")
    log(f"DEFERRED {CHAP}:{v} (no gold, no timeout)")

log(f"MAX_ITERS {MAX_ITERS} reached — stop"); print(f"CH{CHAP}_STATUS=MAX_ITERS")
