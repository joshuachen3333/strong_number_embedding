#!/usr/bin/env python3
"""Stop a running residue car at a deadline, or when codex's weekly quota runs low.

Usage:
  stop_watchdog.py --pid 23986 --deadline "2026-08-16 07:00" --codex-floor 5

Why a separate process rather than a flag inside residue_pass.py: the car is
already on the road. Restarting it to teach it a deadline would throw away the
verse in flight (up to 40 min) for no gain, since the watchdog only ever needs to
observe and then signal.

Two independent stop conditions, whichever lands first:

  * deadline    -- wall clock.
  * codex-floor -- codex weekly quota REMAINING drops to this percent or below.
                   That quota is account-wide, so it is spent by every codex
                   consumer on this machine (survey1's car and survey10's cars
                   both), which is exactly the number worth guarding.

Codex telemetry has no CLI query (`/status` is interactive only), but every codex
call writes a `token_count` event carrying `rate_limits` into its rollout JSONL,
and the weekly window is the entry with window_minutes == 10080. So we read the
newest rollouts and take the freshest reading. This is passive -- it observes
traffic the pipeline is generating anyway and never spends a token to ask.

Stopping is graceful and ordered: the parent first, so it cannot dispatch the next
verse, then the verse in flight. A SIGKILL mid-write truncates JSON and poisons
the next run of that verse, so we TERM, wait, and sweep for unparseable JSON
afterward.
"""
import argparse, json, os, re, signal, sqlite3, subprocess, sys, time, glob
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SURVEY_DIR)

CODEX_STATE_DB = os.path.expanduser("~/.codex/state_5.sqlite")
CODEX_SESSIONS = os.path.expanduser("~/.codex/sessions")
WEEKLY_WINDOW_MINUTES = 10080     # 7 days -- distinguishes weekly from the 5h window
POLL_S = 60

ap = argparse.ArgumentParser()
ap.add_argument("--pid", type=int, required=True, help="residue_pass.py pid")
ap.add_argument("--deadline", required=True, help='"YYYY-MM-DD HH:MM" local time')
ap.add_argument("--codex-floor", type=float, default=5.0,
                help="stop when codex weekly REMAINING %% <= this")
args = ap.parse_args()

DEADLINE = datetime.strptime(args.deadline, "%Y-%m-%d %H:%M")
LOG = os.path.join(SURVEY_DIR, "run_logs",
                   f"stop_watchdog_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(m):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [watchdog] {m}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _recent_rollouts(limit=30):
    """Newest codex rollout files. The state DB is the accurate index, but it is
    written live by codex, so fall back to globbing today's directory if it is
    busy -- a locked DB must never be a reason to stop guarding the quota."""
    paths = []
    try:
        con = sqlite3.connect(f"file:{CODEX_STATE_DB}?mode=ro", uri=True, timeout=3)
        paths = [r[0] for r in con.execute(
            "SELECT rollout_path FROM threads ORDER BY updated_at_ms DESC LIMIT ?",
            (limit,))]
        con.close()
    except sqlite3.Error as e:
        log(f"codex state db unreadable ({e}); falling back to file glob")
    if not paths:
        paths = sorted(glob.glob(os.path.join(CODEX_SESSIONS, "*", "*", "*", "*.jsonl")),
                       key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
                       reverse=True)[:limit]
    return paths


def codex_weekly_remaining():
    """(remaining_percent, reading_timestamp) or (None, None) if nothing found."""
    best_ts, best_used = None, None
    for p in _recent_rollouts():
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                for line in f:
                    if '"rate_limits"' not in line:
                        continue
                    try:
                        d = json.loads(line)
                    except (json.JSONDecodeError, ValueError):
                        continue
                    rl = (d.get("payload") or {}).get("rate_limits") or {}
                    ts = d.get("timestamp")
                    for slot in ("primary", "secondary"):
                        w = rl.get(slot)
                        if not isinstance(w, dict):
                            continue
                        if w.get("window_minutes") != WEEKLY_WINDOW_MINUTES:
                            continue
                        if w.get("used_percent") is None:
                            continue
                        if best_ts is None or (ts and ts > best_ts):
                            best_ts, best_used = ts, float(w["used_percent"])
        except OSError:
            continue
    if best_used is None:
        return None, None
    return 100.0 - best_used, best_ts


def sweep_poison():
    removed = []
    for root in ("gold_standard", "round1_results", "round2_results", "round3_results"):
        for dp, _, fns in os.walk(root):
            for fn in fns:
                if not fn.endswith(".json"):
                    continue
                p = os.path.join(dp, fn)
                try:
                    with open(p, encoding="utf-8") as f:
                        json.load(f)
                except (json.JSONDecodeError, ValueError):
                    try:
                        os.remove(p); removed.append(p)
                    except OSError:
                        pass
                except OSError:
                    pass
    log(f"poison sweep: removed {len(removed)}" + (f" {removed[:5]}" if removed else ""))


def _children_of(pid):
    out = subprocess.run(["ps", "-eo", "pid=,ppid="], capture_output=True, text=True).stdout
    return [int(a) for a, b in (l.split() for l in out.strip().split("\n") if l.split())
            if int(b) == pid]


def _orphan_cli_calls():
    """`claude -p` / `codex exec` left with ppid 1 keep burning quota after their
    parent dies. Only reap ones running out of THIS survey's cwd, so a sibling
    survey's cars are never touched."""
    out = subprocess.run(["ps", "-eo", "pid=,ppid=,command="],
                         capture_output=True, text=True).stdout
    victims = []
    for line in out.strip().split("\n"):
        m = re.match(r"\s*(\d+)\s+(\d+)\s+(.*)", line)
        if not m:
            continue
        pid, ppid, cmd = int(m.group(1)), int(m.group(2)), m.group(3)
        if ppid != 1:
            continue
        if not ("claude -p --output-format stream-json" in cmd or "codex exec" in cmd):
            continue
        cwd = subprocess.run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
                             capture_output=True, text=True).stdout
        if SURVEY_DIR in cwd:
            victims.append(pid)
    return victims


def stop_car(reason):
    log(f"STOPPING — {reason}")
    kids = _children_of(args.pid)
    # Parent first: it must not be able to dispatch the next verse while we are
    # taking down the one in flight.
    try:
        os.kill(args.pid, signal.SIGTERM); log(f"TERM {args.pid} (car)")
    except ProcessLookupError:
        pass
    # caffeinate wrapper, if it is a child of the car
    for pid in kids:
        cmd = subprocess.run(["ps", "-o", "command=", "-p", str(pid)],
                             capture_output=True, text=True).stdout
        if "caffeinate" in cmd:
            try:
                os.kill(pid, signal.SIGTERM); log(f"TERM {pid} (caffeinate)")
            except ProcessLookupError:
                pass
    time.sleep(3)
    for pid in kids:
        cmd = subprocess.run(["ps", "-o", "command=", "-p", str(pid)],
                             capture_output=True, text=True).stdout
        if "run_gold_standard.py" in cmd:
            try:
                os.kill(pid, signal.SIGTERM); log(f"TERM {pid} (verse in flight)")
            except ProcessLookupError:
                pass
    time.sleep(8)
    for pid in (args.pid, *kids):
        if alive(pid):
            try:
                os.kill(pid, signal.SIGKILL); log(f"KILL {pid} (did not exit on TERM)")
            except ProcessLookupError:
                pass
    time.sleep(2)
    for pid in _orphan_cli_calls():
        try:
            os.kill(pid, signal.SIGTERM); log(f"TERM {pid} (orphan CLI call)")
        except ProcessLookupError:
            pass
    sweep_poison()
    rem, ts = codex_weekly_remaining()
    log(f"final codex weekly remaining: "
        f"{'unknown' if rem is None else f'{rem:.1f}%'} (reading {ts})")
    log("watchdog done")


log(f"watching pid {args.pid}; deadline {DEADLINE:%Y-%m-%d %H:%M}; "
    f"codex weekly floor {args.codex_floor}%")
rem0, ts0 = codex_weekly_remaining()
log(f"codex weekly remaining at start: "
    f"{'unknown' if rem0 is None else f'{rem0:.1f}%'} (reading {ts0})")

last_report = 0.0
while True:
    if not alive(args.pid):
        log("car exited on its own — nothing to stop")
        break
    now = datetime.now()
    if now >= DEADLINE:
        stop_car(f"deadline {DEADLINE:%Y-%m-%d %H:%M} reached")
        break
    rem, ts = codex_weekly_remaining()
    if rem is not None and rem <= args.codex_floor:
        stop_car(f"codex weekly remaining {rem:.1f}% <= floor {args.codex_floor}% "
                 f"(reading {ts})")
        break
    if time.time() - last_report > 1800:      # a heartbeat every 30 min
        log(f"alive; {(DEADLINE - now).total_seconds()/3600:.1f}h to deadline; "
            f"codex weekly remaining "
            f"{'unknown' if rem is None else f'{rem:.1f}%'}")
        last_report = time.time()
    time.sleep(POLL_S)
