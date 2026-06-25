#!/usr/bin/env python3
"""S10 cli_caller — OBE-style live-session transport with headless fallback.

Drop-in replacement for survey1's cli_caller. The pipeline (run_gold_standard /
judge / regression) imports `call_llm, DEFAULT_MODELS, MODEL_ALIASES, build_panel`
from here; we re-export the s1 versions and OVERRIDE `call_llm` so that the two
injectable legs run against LIVE obe sessions (Terminal tabs) via osascript
inject + file-handoff, and fall back to s1's stateless headless caller on any
failure.

Leg routing (by brand):
  codex -> s10-lala  (live Terminal window)   | fallback: headless codex exec
  agy   -> s10-erha  (live Terminal window)   | fallback: headless agy -p
  claude-> headless opus (no live tab; the orchestrator IS the obe)

The live transport never reads the TUI scrollback (unreliable for some CLIs):
the orchestrator writes the full prompt to a task file, injects a SHORT command
telling the leg to read it and write its answer to an answer file, then polls the
answer file. Inject failures (focus race, timeout, unparseable) degrade to the
headless path so the run always completes.
"""

import importlib.util
import os
import subprocess
import sys
import time

S10_DIR = os.path.dirname(os.path.abspath(__file__))
S1_DIR = os.path.join(os.path.dirname(S10_DIR), "survey1_prompt_evolving")
PARENT_DIR = os.path.dirname(S10_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Load survey1's cli_caller by file path under a distinct name (our own module is
# also called 'cli_caller' and shadows it on sys.path).
_spec = importlib.util.spec_from_file_location(
    "s1_cli_caller", os.path.join(S1_DIR, "cli_caller.py"))
_s1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_s1)

# Re-export the symbols the pipeline imports.
DEFAULT_MODELS = _s1.DEFAULT_MODELS
MODEL_ALIASES = _s1.MODEL_ALIASES
build_panel = _s1.build_panel
resolve_model = _s1.resolve_model
DEFAULT_TIMEOUT = _s1.DEFAULT_TIMEOUT

build_json_schema = _s1.build_json_schema
_extract_json = _s1._extract_json

# Live obe leg -> Terminal window id (see .s10_sessions.json).
# Fix (d): agy relaunched on a fresh window pinned to "Gemini 3.1 Pro (High)"
# (was 5557 on Flash). codex relaunched fresh (9082) after its 5555 session ended
# during the quota-capped run.
# 2026-06-25: codex live leg dropped — its osascript inject stopped landing in
# the codex TUI input box (31 consecutive fails on Gen ch2), so every codex call
# burned the full LIVE_TIMEOUT (150s) before falling back to headless. Under the
# per-call /clear blind design, headless ≡ blind-live (both start blank), so
# routing codex straight to headless costs zero quality and saves the 150s/call.
# agy live (w8214) remains reliable (70 ok / 1 fail on the same run). Restore
# codex here (window id) once its inject path is fixed.
LIVE_WINDOWS = {"agy": 8214}

# Cap the live-inject attempt so a hung session falls back to headless quickly
# instead of burning the full call timeout. The headless fallback then gets the
# full timeout. Live legs normally answer in 15-60s.
LIVE_TIMEOUT = 150

# Fix (b) — pacing between consecutive LIVE legs. Sequential osascript injects
# fight for Terminal frontmost focus; too fast and the Return lands in the wrong
# window or never fires. After one leg's interaction commits, wait >= this before
# the next leg's inject. Enforced globally across every live call (R1/R2/R3).
LEG_PACING_SEC = 15.0
_LAST_LIVE_TS = {"t": 0.0}


def _pace_between_legs(verbose=False):
    """Block until >= LEG_PACING_SEC has elapsed since the previous live leg."""
    gap = LEG_PACING_SEC - (time.time() - _LAST_LIVE_TS["t"])
    if gap > 0:
        if verbose:
            print(f"  [pace] {gap:.0f}s before next live leg", flush=True)
        time.sleep(gap)


def _mark_live_inject():
    """Record that a live leg just finished (resets the pacing clock)."""
    _LAST_LIVE_TS["t"] = time.time()


def _osascript_inject(window_id, text):
    """Focus the target tab and submit a command into it.

    Fix (a) — DOUBLE-ENTER v2 (/obe-codified, Joshua-observed): a single Return
    does not reliably commit into a CLI TUI's bracketed-paste input box (Joshua
    watched /clear fail to submit). Send TWO `key code 36` with a ~5s gap so the
    TUI finishes ingesting the paste before the second Return submits it.
    """
    esc = text.replace("\\", "\\\\").replace('"', '\\"')
    script = f'''
tell application "System Events"
  set frontmost of process "Terminal" to true
end tell
delay 0.5
tell application "Terminal"
  activate
  set t to tab 1 of window id {window_id}
  set selected tab of window id {window_id} to t
  set frontmost of window id {window_id} to true
end tell
delay 1.0
tell application "Terminal"
  do script "{esc}" in tab 1 of window id {window_id}
end tell
delay 0.7
tell application "System Events" to key code 36
delay 5.0
tell application "System Events" to key code 36
'''
    subprocess.run(["osascript", "-e", script], capture_output=True, text=True)


def reset_live_panel(verbose=False):
    """One-shot hygiene clear of every live leg (e.g. at run start) — drops any
    stale pre-run context. Uses double-Enter (fix a, via _osascript_inject) and
    >=15s pacing BETWEEN legs (fix b) so the sequential /clear injects don't fight
    for focus.

    NOTE: per-call blindness is enforced inside `_live_call` (it /clears before
    EVERY model call), so this function is NOT needed per-verse — it is a coarse
    run-start hygiene step only. Headless legs are already per-call amnesiac.

    Returns a dict {brand: "cleared"|"error"} for logging.
    """
    status = {}
    for brand, window_id in LIVE_WINDOWS.items():
        try:
            _pace_between_legs(verbose=verbose)  # >=15s between legs (fix b)
            _osascript_inject(window_id, "/clear")  # double-Enter (fix a)
            _mark_live_inject()
            status[brand] = "cleared"
            if verbose:
                print(f"  [reset] {brand} w{window_id} /clear", flush=True)
        except Exception as e:  # noqa: BLE001 — best-effort, headless covers failures
            status[brand] = "error"
            if verbose:
                print(f"  [reset] {brand} w{window_id} FAILED ({e}) "
                      f"-> headless fallback is amnesiac anyway", flush=True)
    return status


def _live_call(brand, window_id, system_prompt, user_prompt,
               target_version, sn_field, mode, timeout, verbose):
    """Inject the task into a live obe session; read its answer from a file.

    Fix (b)+(c) — per-call blindness with leg pacing. EVERY live call (R1, each R2
    re-roll, R3 vote) starts blank: pace >=15s since the previous leg, COMMIT a
    `/clear` (double-Enter) so this leg has no memory of the prior verse/round,
    let it settle, THEN inject the task. This restores within-verse R1/R2
    independence on the live path. D-deliberation passes the sealed R1 bids
    explicitly in its prompt, so clearing before a D call loses nothing.
    """
    task_file = f"/tmp/s10_task_{brand}.txt"
    ans_file = f"/tmp/s10_ans_{brand}.json"

    body = system_prompt + "\n\n" + user_prompt
    if mode == "production":
        body += ("\n\nRespond with ONLY valid JSON matching this schema:\n" +
                 build_json_schema(target_version))
    with open(task_file, "w", encoding="utf-8") as f:
        f.write(body)
    try:
        os.remove(ans_file)
    except OSError:
        pass

    # Pace, then commit /clear (per-call blindness), then let it settle.
    _pace_between_legs(verbose=verbose)
    if verbose:
        print(f"  [live {brand}] /clear (blind) then inject", flush=True)
    _osascript_inject(window_id, "/clear")
    time.sleep(3)  # let /clear process before the task lands

    inject_cmd = (
        f"Read the full task in {task_file} and complete it. "
        f"Write ONLY your answer to {ans_file} (overwrite it, raw JSON, no "
        f"markdown fences, no commentary). Then reply with just: done. "
        f"Do not print the answer in chat.")
    _osascript_inject(window_id, inject_cmd)

    result = {"error": True, "notes": [f"live inject timeout ({timeout}s) on {brand}"]}
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.isfile(ans_file):
            time.sleep(0.6)  # let the write settle
            try:
                with open(ans_file, "r", encoding="utf-8") as f:
                    raw = f.read().strip()
            except OSError:
                raw = ""
            if raw:
                if mode == "freeform":
                    result = {"text": raw}
                else:
                    key = sn_field if mode == "production" else "best"
                    result = _extract_json(raw, key)
                break
        time.sleep(2)

    _mark_live_inject()  # start the >=15s pacing clock for the NEXT leg
    return result


def call_llm(brand, model, system_prompt, user_prompt,
             target_version="lcc", timeout=DEFAULT_TIMEOUT,
             verbose=False, mode="production"):
    """Route to a live obe session when one exists; else headless."""
    sn_field = f"{target_version}_sn"

    if brand in LIVE_WINDOWS:
        live_timeout = min(timeout, LIVE_TIMEOUT)
        if verbose:
            print(f"  [live {brand} w{LIVE_WINDOWS[brand]}] inject ({mode}, "
                  f"≤{live_timeout}s)...", flush=True)
        res = _live_call(brand, LIVE_WINDOWS[brand], system_prompt, user_prompt,
                         target_version, sn_field, mode, live_timeout, verbose)
        if isinstance(res, dict) and not res.get("error"):
            res.setdefault("_transport", "live")
            return res
        if verbose:
            print(f"  [live {brand}] failed -> headless fallback", flush=True)

    res = _s1.call_llm(brand, model, system_prompt, user_prompt,
                       target_version, timeout, verbose, mode)
    if isinstance(res, dict):
        res.setdefault("_transport", "headless")
    return res
