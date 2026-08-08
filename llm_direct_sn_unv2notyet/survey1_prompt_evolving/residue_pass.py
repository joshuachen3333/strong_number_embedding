#!/usr/bin/env python3
"""Another clean pass over whatever Gen 1-20 verses still have no gold.

Usage:  residue_pass.py <car:A|B|C> <pass_n>   (launch nohup-detached, one per car)

Generalizes second_pass_17.py, which hard-coded its worklist. Rationale for
running the same verses again rather than declaring them unsolvable:

  Pass 2 (2026-07-30) resolved 4 of 17 -- including 8:21, which had already been
  declared accept-empty after two clean fresh-quota runs. Combined with the
  earlier 9:16 and 17:25 reversals, that is three verses now recovered *after*
  being written off. So "failed N times" is not a verdict; each clean pass
  converts a slice of the residue and the slice is not empty yet.

  Pass 2 also refuted the model-upgrade hypothesis: the verses that resolved and
  the ones that did not ran on the SAME generations (claude-opus-5 / gpt-5.6-sol),
  so the variation is stochastic within fixed models, not a generational effect.

The worklist is computed from disk, so a verse resolved by any other run (or by
a sibling survey) is skipped automatically. Chapters are partitioned across cars
so no two cars share a chapter's caches. Scripture comes from local SQLite; no
FHL. Cloud CLIs only; NO ollama.
"""
import subprocess, sys, os, time, signal, json
from datetime import datetime

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SURVEY_DIR)

# The full Gen 1-20 residue as of pass 2; anything since resolved is filtered out.
RESIDUE = [(1, 30), (7, 13), (8, 1), (8, 21), (9, 2), (9, 5), (17, 23),
           (18, 19), (18, 25), (19, 2), (19, 8), (19, 14), (19, 15),
           (20, 3), (20, 7), (20, 16), (20, 18)]
CARS = ("A", "B", "C")
PER_VERSE_TIMEOUT = 2400   # 40 min
BACKOFF_S = 1800

CAR = sys.argv[1].upper()
PASS_N = sys.argv[2] if len(sys.argv) > 2 else "3"
REPORT = os.path.join(SURVEY_DIR, "run_logs", f"residue_pass{PASS_N}_car{CAR}.jsonl")
LOG = os.path.join(SURVEY_DIR, "run_logs",
                   f"residue_pass{PASS_N}_car{CAR}_{datetime.now():%Y%m%d_%H%M%S}.log")
os.makedirs(os.path.dirname(LOG), exist_ok=True)


def log(m):
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [p{PASS_N}car{CAR}] {m}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def gold_path(ch, sec):
    return os.path.join(SURVEY_DIR, "gold_standard", "Gen", str(ch), f"{sec}.json")


_DONE_RESOLUTIONS = {"round1", "round2", "round3", "r2_model_patch"}


def has_gold(ch, sec):
    """Is this verse actually FINISHED?

    File existence is not the predicate (s10obe, 2026-08-08): a run that ends in
    `resolved_at: "unresolved"` still writes a gold file, usually with an EMPTY
    `lcc_sn`. Scanning for the file counted 508/514 in this tree when only 436
    verses carried a trust_tier -- 50 of the rest were empty shells. A whole batch
    lost to a codex usage-limit looks identical to a finished chapter.

    trust_tier alone is too strict the other way: 16 verses predate the field
    (v1.1/v1.2) yet have real text and a real resolution, and re-running them
    would burn quota to replace good gold. So: tiered, OR resolved with content.

    Parse-fail (not file size) remains the poison test -- a write killed partway
    can leave hundreds of bytes that still will not parse (s10obe, 2026-07-27).
    """
    p = gold_path(ch, sec)
    if not os.path.isfile(p) or os.path.getsize(p) == 0:
        return False
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
    except (json.JSONDecodeError, ValueError, OSError):
        return False
    if d.get("trust_tier"):
        return True
    return bool((d.get("lcc_sn") or "").strip()
                and d.get("resolved_at") in _DONE_RESOLUTIONS)


def assign_chapters():
    """Partition the still-missing verses across cars by CHAPTER (never split a
    chapter), largest chapter first onto the currently lightest car — keeps the
    cars balanced while guaranteeing they never touch the same chapter's caches."""
    pending = [v for v in RESIDUE if not has_gold(*v)]
    by_chap = {}
    for ch, sec in pending:
        by_chap.setdefault(ch, []).append((ch, sec))
    loads = {c: [] for c in CARS}
    for ch in sorted(by_chap, key=lambda c: (-len(by_chap[c]), c)):
        lightest = min(CARS, key=lambda c: (len(loads[c]), c))
        loads[lightest].extend(sorted(by_chap[ch]))
    return loads


def sweep_poison():
    """Any SIGKILL can truncate a JSON mid-write; a corrupt convergence cache then
    crashes the NEXT run of that verse and looks like pathology."""
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
    try:
        with open(gold_path(ch, sec), encoding="utf-8") as f:
            d = json.load(f)
    except Exception:  # noqa: BLE001 — reporting only, never block the run
        return {}
    return {m: v.get("resolved_model", "")
            for m, v in (d.get("round1") or {}).items() if isinstance(v, dict)}


def record(ch, sec, outcome, extra=None):
    row = {"chap": ch, "sec": sec, "outcome": outcome, "pass": PASS_N,
           "at": f"{datetime.now():%Y-%m-%d %H:%M}"}
    if extra:
        row.update(extra)
    with open(REPORT, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_verse(ch, sec, timeout):
    log(f"verse Gen {ch}:{sec} (timeout {timeout}s)")
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


WORKLIST = assign_chapters()[CAR]
log(f"=== PASS {PASS_N} car{CAR} START === {len(WORKLIST)} verses: "
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
        log(f"RESOLVED Gen {ch}:{sec}  models={prov}")
        record(ch, sec, "resolved", {"resolved_model": prov})
    elif f["timeout"]:
        log(f"STILL NON-CONVERGENT Gen {ch}:{sec} (timeout)")
        record(ch, sec, "still_non_convergent")
    else:
        log(f"NO GOLD Gen {ch}:{sec} (clean run, no timeout)")
        record(ch, sec, "no_gold_clean_run")
    i += 1

left = [v for v in WORKLIST if not has_gold(*v)]
log(f"=== pass{PASS_N} car{CAR} DONE === resolved {len(WORKLIST)-len(left)}/{len(WORKLIST)}; "
    f"remaining: {['%d:%d' % v for v in left]}")
print(f"PASS{PASS_N}_CAR{CAR}_STATUS=DONE")
