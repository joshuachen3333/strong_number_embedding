# Survey 10 — S1 task, Obe-style LIVE persistent sessions (not one-shot)

> Status: **design locked, pre-implementation** (2026-06-20, revised after Joshua
> clarification). Inherits all of `../survey1_prompt_evolving/` logic; the change
> is that the 3 panel models are **live, already-open, mutually-bound obe
> sessions driven by osascript injection** — NOT headless one-shot subprocess
> calls. This doc is the s10 analog of s1's `ARCHITECTURE_DECISIONS.md`.

## Mission

Reproduce s1's 3-model consensus gold-standard pipeline (R1 → R2 → R3 + live
prompt evolution + regression gate), but run the panel **obe-style**: the three
models (**opus** / **agy** / **codex**) are **three live interactive CLI sessions
in Terminal tabs**, mutually bound via the `/obe` leash, that the s10
orchestrator drives by **osascript inject + read-back** — the same machinery that
leashes obe/lala/erha. Context accumulates *naturally* because each is a real,
ongoing conversation, not a subprocess re-summoned from scratch.

The three models become three persistent colleagues deliberating verse-by-verse.

## CRUX (Joshua correction, 2026-06-20): live sessions, not headless

> 「s10 就是使用已經開啟, 互相綁定的 3 obe, 而非 headless 一次性地呼叫, 又載入最後
> context (那個可以作為注入失敗時的候補方法)」
> 「s10 should open sibling obes first, or if injection failed, do the headless
> calling of models」

| | PRIMARY path (obe-style) | FALLBACK path (inject fails) |
|---|---|---|
| Mechanism | osascript **inject** task into live tab + **read back** answer | headless `claude -p --resume <id>` / `codex exec resume <id>` / `agy --conversation <id>` |
| Session | the live interactive Terminal session | the **same** on-disk session id, reloaded |
| Context | accumulates live | reloaded from last persisted context |
| Compaction | native `/compact` typed into the live tab (works — interactive!) | headless summarize-and-reseed |

**s10 owns the lifecycle**: it **opens the 3 sibling obe sessions first** (spawns
the 3 panel CLIs in Terminal tabs, each pinned to a known session id), drives them
by inject, and only drops to headless model calls **per-call** when an inject
round fails (focus race, no ack within window, unparseable read-back).

**Shared session id is the linchpin**: each live tab is launched with a known
session id (claude `--session-id <uuid>`, codex session uuid, agy conversation
id). The headless fallback `--resume`s that *same* id, so live-inject and
headless-fallback are two ways to drive one accumulating context — no divergence.

### Read-back caveat → file-based handoff
Per `/obe`, reading answers back from a **Claude Code TUI** tab is unreliable
(continuous redraw). Resolution: inject the task **plus** "write your JSON answer
to `<path>`"; the orchestrator reads the **file**, not the TUI scrollback. Live
obe sessions have tools enabled, so they can write. (codex/agy shell read-back is
reliable, but file-handoff is the uniform, robust choice for all three legs.)

## What is inherited verbatim from s1

- The R1 (unanimous) → R2 (convergence + Trigger 1/2 + debate) → R3 (pick /
  all_wrong) pipeline shape.
- `consensus.py` `build_gold_standard()` remains the **sole authority** for
  `resolved_at`. Main loop only collects.
- Live prompt evolution (Trigger 1 +0.1, Trigger 2 model patch), regression gate,
  gold-standard JSON schema, the prompts/ versioning.
- The 3-leg panel from `cli_caller.py:DEFAULT_MODELS`:
  `opus` (claude) / `agy` (Antigravity, Gemini 3.1 Pro) / `codex`.

## Leg mechanics (live primary + headless fallback share one session id)

| Leg | Live launch (primary) | Headless fallback |
|-----|----------------------|-------------------|
| opus/claude | open tab → `claude --session-id <uuid> [-n opus-s10]` interactive | `claude -p --resume <uuid> --json-schema …` |
| codex | open tab → `codex` (capture session uuid) | `codex exec resume <uuid> -` |
| agy   | open tab → `agy` (capture conversation id) | `agy --conversation <id> -p …` |

Session ids persisted to `.s10_sessions.json` so a resumed run reattaches to the
same three minds. Feasibility verified 2026-06-20 — all three CLIs expose
resume/continue in print mode, so the fallback can always reload the live tab's
accumulated context.

## Locked decisions (Joshua, 2026-06-20, via design Q&A)

### D1 — Session lifetime: continuous, self-compacting at 40–50% context
**Not** a fixed per-chapter/per-book reset. Each session runs continuously, but
when its context window crosses **40–50% full**, it must **compact** before
continuing. Rationale: keep each mind lean enough to stay sharp, never let it
bloat past half its window.

**Mechanism (primary = native `/compact` in the live tab)** — because the panel
is now interactive, the real `/compact` command is available:
1. Track each leg's context usage (the live tab's status line shows context %;
   or estimate from injected+returned bytes).
2. When usage ≥ ~45% of that model's window, **inject `/compact`** into that leg's
   tab (claude `/compact`, codex `/compact`, agy equivalent) and let the live
   session compress itself in place — session id unchanged.
3. Per-leg windows differ (opus ~1M, agy/codex smaller) → threshold is per-leg.
4. **Fallback** (if `/compact` can't be driven): summarize-and-reseed — ask the
   leg for a structured summary, open a fresh session seeded with it.

### D2 — Everything stateful (R2 convergence is no longer blind)
All calls — R1 generation, R2 convergence, R3 judging — share the leg's
persistent session. This **breaks s1's blind-convergence premise**, so the
semantics shift:

- In s1, R2 convergence re-ran the task with **no memory** to *measure
  instability* (Level 0–3 → Trigger 1/2). That measurement assumed amnesia.
- In s10, a model **remembers its R1 answer**, so naive re-asking yields trivial
  self-agreement. The Level 0–3 stability machinery must be **re-interpreted**:
  R2 becomes genuine *deliberation* — each model sees the others' answers (or is
  prompted to reconsider) and decides whether to **hold or revise** with full
  memory. "Convergence" = the panel settling through informed deliberation, not
  through independent amnesiac re-rolls.
- `judge.py` convergence/stability semantics need rework. Trigger 1/2 thresholds
  may need re-derivation (or replacement with a hold-vs-revise signal). **This is
  the largest code delta of s10** — flag for careful design before coding.

### D3 — Feed resolved consensus back into all sessions
After `build_gold_standard()` resolves a verse, inject "the consensus answer was
X (resolved_at=…)" into **all three** sessions. The panel accumulates *corrected*
knowledge, so later verses benefit from settled conventions — the real obe-style
learning loop (not just continuity of each model's own, possibly-wrong, attempts).

## Implementation plan (phased)

1. **Spike the obe transport** — open ONE live panel session in a Terminal tab
   with a known session id, inject a verse task + "write JSON to `<path>`", read
   the file back, confirm round-trip. Then confirm the headless `--resume`
   fallback reloads the *same* session. De-risks the whole transport.
2. **`obe_panel.py`** — NEW module: opens the 3 panel tabs (lifecycle), holds
   their window ids + session ids, exposes `ask(leg, prompt) -> dict` that
   injects + file-reads with **automatic headless fallback** on inject failure,
   tracks per-leg context %, triggers `/compact` at ~45%.
3. **Replace `cli_caller.py`'s role** — `call_llm()` routes through `obe_panel`
   (live inject) with the s1 headless caller as the fallback branch.
4. **Rework `judge.py` R2** under D2 (hold-vs-revise deliberation; re-derive or
   replace Trigger 1/2 — see risk flags).
5. **Wire D3** — inject resolved consensus into all 3 live tabs after each verse.
6. Copy/adapt `consensus.py`, `regression.py`, `run_gold_standard.py`, `prompts/`.
7. Validate on 創 1:1-3 small batch vs s1's gold standard.

## Directory layout (planned, mirrors s1)
```
survey10_.../
├── SURVEY10_DESIGN.md          # this file
├── obe_panel.py                # NEW — open/drive 3 live sessions, inject+file
│                               #   readback, headless fallback, /compact trigger
├── cli_caller.py               # adapted: headless FALLBACK callers (resume)
├── judge.py                    # adapted: D2 deliberation semantics
├── consensus.py / regression.py / run_gold_standard.py  # adapted from s1
├── prompts/                    # versioned (seed from s1 latest)
├── .s10_sessions.json          # per-leg window ids + session ids (gitignored)
└── gold_standard/ round{1,2,3}_results/ run_logs/
```

## Risk flags for Joshua
- **R2 semantics (D2)** is a genuine redesign, not a port. "Convergence" and the
  Trigger 1/2 stability math were built on amnesia; with memory they need new
  definitions. Worth a focused design pass before coding judge.py.
- **Live transport reliability** — inject focus-races + Claude-TUI read-back are
  the known `/obe` landmines. Mitigations baked in: file-based handoff (not TUI
  scrollback), ack/timeout detection, and the headless `--resume` fallback on any
  failed round. The transport spike (step 1) must prove this before scale-up.
- **Panel roster + who opens them** — assumed: s10 spawns opus(claude) /
  codex(lala) / agy(erha) itself in fresh tabs. Confirm whether to reuse any
  already-open sessions instead.
