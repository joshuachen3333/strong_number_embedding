#!/usr/bin/env python3
"""Second pass over the 17 Gen 1-20 verses that never produced gold.

Usage:  second_pass_17.py <car:A|B|C>   (launch nohup-detached, one per car)

Joshua 2026-07-30 "yes, run these 17". Two things make this pass different from
the earlier sweeps, and both are the point:

  1. Provenance. Every verse now records `resolved_model` per model leg
     (commit a221e44/604ebf1), so for the first time we can ask WHY a verse that
     failed before succeeds now — a different model generation is a candidate
     answer, and until now we simply could not see it.
  2. A real precedent. 9:16 and 17:25 were both declared pathological and both
     resolved on a later clean run. So "already failed twice" is evidence, not a
     verdict; five of these 17 carry that label and still deserve one honest
     attempt under the current models.

Cars own DISJOINT chapters so no two cars touch the same chapter's caches.
Scripture is served from local SQLite (UNV bible_little.db / LCC bible_lcc.db);
no FHL. Cloud CLIs only; NO ollama.

A verse that times out here is left alone — recorded, not retried forever.
"""
import subprocess, sys, os, time, signal, json
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SURVEY_DIR)

# Disjoint chapters per car → zero cross-car cache collision.
CARS = {
    "A": [(19, 2), (19, 8), (19, 14), (19, 15), (1, 30), (7, 13)],
    "B": [(20, 3), (20, 7), (20, 16), (20, 18), (8, 1), (8, 21)],
    "C": [(9, 2), (9, 5), (18, 19), (18, 25), (17, 23)],
}
# Verses already declared accept-empty after two clean fresh-quota runs. Tracked
# only so the report can say whether a *third* attempt changed anything.
TWICE_FAILED = {(8, 1), (8, 21), (9, 2), (9, 5), (17, 23)}

CAR = sys.argv[1].upper()
WORKLIST = CARS[CAR]
PER_VERSE_TIMEOUT = 2400   # 40 min — generous; pathology hits this, normal verses don't
BACKOFF_S = 1800
REPORT = os.path.join(SURVEY_DIR, "run_logs", f"second_pass_17_car{CAR}.jsonl")
LOG = os.path.join(SURVEY_DIR, "run_logs",
                   f"second_pass_car{CAR}_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(m):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [car{CAR}] {m}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def gold_path(ch, sec):
    return os.path.join(SURVEY_DIR, "gold_standard", "Gen", str(ch), f"{sec}.json")


def has_gold(ch, sec):
    p = gold_path(ch, sec)
    # Non-empty is not enough: a truncated write parses as garbage. Parse-fail is
    # the correct poison test (s10obe, 2026-07-27) — a size check misses a JSON
    # that got several hundred bytes in before the kill.
    if not os.path.isfile(p) or os.path.getsize(p) == 0:
        return False
    try:
        with open(p, encoding="utf-8") as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, ValueError, OSError):
        return False


def sweep_poison():
    """Any SIGKILL can truncate a JSON mid-write; a corrupt convergence cache then
    crashes the NEXT run of that verse and looks like pathology. Sweep after every
    kill, by parse-fail (not size)."""
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
    if removed:
        log(f"swept {len(removed)} corrupt JSON: {removed[:5]}")
    return removed


def provenance(ch, sec):
    """Which model generation answered — the whole reason this pass is worth running."""
    try:
        with open(gold_path(ch, sec), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:  # noqa: BLE001 — reporting only, never block the run
        return {}
    out = {}
    for model, v in (d.get("round1") or {}).items():
        if isinstance(v, dict):
            out[model] = v.get("resolved_model", "")
    return out


def record(ch, sec, outcome, extra=None):
    row = {"chap": ch, "sec": sec, "outcome": outcome,
           "twice_failed_before": [ch, sec] in [list(t) for t in TWICE_FAILED],
           "at": f"{datetime.now():%Y-%m-%d %H:%M}"}
    if extra:
        row.update(extra)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_verse(ch, sec, timeout):
    log(f"verse Gen {ch}:{sec} (timeout {timeout}s"
        f"{', 3rd attempt' if (ch, sec) in TWICE_FAILED else ''})")
    flags = {"rate_limit": False, "model_down": False, "timeout": False}
    p = subprocess.Popen(
        [sys.executable, "run_gold_standard.py", "--force", "--book", "創",
         "--chap", str(ch), "--sec", str(sec)],
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
                except Exception:  # noqa: BLE001
                    p.kill()
                break
    finally:
        lf.close()
    try:
        p.wait(timeout=10)
    except Exception:  # noqa: BLE001
        pass
    if flags["timeout"]:
        sweep_poison()
    return flags


log(f"=== SECOND PASS car{CAR} START === {len(WORKLIST)} verses: "
    f"{['%d:%d' % v for v in WORKLIST]}")
i = 0
while i < len(WORKLIST):
    ch, sec = WORKLIST[i]
    if has_gold(ch, sec):
        log(f"already resolved Gen {ch}:{sec} — skip"); i += 1; continue
    f = run_verse(ch, sec, PER_VERSE_TIMEOUT)
    if f["rate_limit"] or f["model_down"]:
        log(f"model-down/rate-limit on Gen {ch}:{sec} — back off {BACKOFF_S//60}min, "
            f"retry same verse")
        time.sleep(BACKOFF_S); continue
    if has_gold(ch, sec):
        prov = provenance(ch, sec)
        tag = "RESOLVED (was 2x-failed)" if (ch, sec) in TWICE_FAILED else "RESOLVED"
        log(f"{tag} Gen {ch}:{sec}  models={prov}")
        record(ch, sec, "resolved", {"resolved_model": prov})
    elif f["timeout"]:
        log(f"STILL NON-CONVERGENT Gen {ch}:{sec} (timeout)")
        record(ch, sec, "still_non_convergent")
    else:
        log(f"NO GOLD Gen {ch}:{sec} (clean run, no timeout)")
        record(ch, sec, "no_gold_clean_run")
    i += 1

left = [v for v in WORKLIST if not has_gold(*v)]
log(f"=== car{CAR} DONE === resolved {len(WORKLIST)-len(left)}/{len(WORKLIST)}; "
    f"remaining: {['%d:%d' % v for v in left]}")
print(f"CAR{CAR}_STATUS=DONE")
