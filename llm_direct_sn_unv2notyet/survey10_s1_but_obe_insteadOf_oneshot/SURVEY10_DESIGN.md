# Survey 10 — S1 task, Obe-style persistent sessions (not one-shot)

> Status: **design locked, pre-implementation** (2026-06-20). Inherits all of
> `../survey1_prompt_evolving/` logic; the ONLY conceptual change is that the 3
> panel models hold persistent **cumulative sessions** instead of stateless
> one-shot subprocess calls. This doc is the s10 analog of s1's
> `ARCHITECTURE_DECISIONS.md` — read it before touching session/round logic.

## Mission

Reproduce s1's 3-model consensus gold-standard pipeline (R1 → R2 → R3 + live
prompt evolution + regression gate), but run the panel **obe-style**: each model
(**opus** / **agy** / **codex**) keeps its *own* accumulating CLI session that
remembers everything it has done, instead of s1's "temp one-shot per verse."

The three models become three persistent colleagues deliberating verse-by-verse,
not three stateless oracles re-summoned from scratch each call.

## What is inherited verbatim from s1

- The R1 (unanimous) → R2 (convergence + Trigger 1/2 + debate) → R3 (pick /
  all_wrong) pipeline shape.
- `consensus.py` `build_gold_standard()` remains the **sole authority** for
  `resolved_at`. Main loop only collects.
- Live prompt evolution (Trigger 1 +0.1, Trigger 2 model patch), regression gate,
  gold-standard JSON schema, the prompts/ versioning.
- The 3-leg panel from `cli_caller.py:DEFAULT_MODELS`:
  `opus` (claude) / `agy` (Antigravity, Gemini 3.1 Pro) / `codex`.

## The one crux that changes: stateless → stateful (`cli_caller.py`)

s1 calls are explicitly memoryless:

| Leg | s1 (one-shot) | s10 (cumulative) |
|-----|---------------|------------------|
| claude | `claude -p … --no-session-persistence` | pin `--session-id <uuid>` per leg, drop `--no-session-persistence`, `--resume` each call |
| codex  | fresh `codex exec … -` | `codex exec resume <session_id> [prompt]` |
| agy    | fresh `agy -p …` | `agy --conversation <id> -p …` (or `-c`) |

Each leg gets ONE long-lived session id, persisted to disk (e.g.
`.s10_sessions.json`) so a resumed run reattaches to the same three minds.
Feasibility verified 2026-06-20 — all three CLIs expose resume/continue in print
mode.

## Locked decisions (Joshua, 2026-06-20, via design Q&A)

### D1 — Session lifetime: continuous, self-compacting at 40–50% context
**Not** a fixed per-chapter/per-book reset. Each session runs continuously, but
when its context window crosses **40–50% full**, it must **compact** before
continuing. Rationale: keep each mind lean enough to stay sharp, never let it
bloat past half its window.

**Mechanism (CLI-agnostic summarize-and-reseed)** — because headless `-p`/`exec`
mode has no reliable interactive `/compact`:
1. Track each leg's cumulative context usage (token counts from the CLI's
   usage/result events, or estimated from prompt+response bytes).
2. When usage ≥ ~45% of that model's window, issue a **compaction turn**:
   ask the model to emit a structured summary of the learned patterns / standing
   conventions it has accumulated so far.
3. Start a **fresh session** for that leg, seeded with the summary as its opening
   context. Persist the new session id.
4. Per-leg windows differ (opus ~1M, agy/codex smaller) → threshold is per-leg,
   not global.

> OPEN ITEM: confirm each CLI's cleanest way to read live context %. If a native
> headless compaction exists (e.g. claude auto-compact), prefer it; else use the
> summarize-and-reseed loop above. Spike this first.

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

1. **Spike D1 compaction** — determine per-CLI context-usage readout + the
   cleanest compaction path (native vs summarize-reseed). De-risks everything.
2. **Session manager** — new module (`session_manager.py`?) owning per-leg
   session ids, resume flags, usage tracking, compaction trigger, reseed.
3. **Refactor `cli_caller.py`** — stateful variants of `_call_claude/_call_codex/
   _call_agy` that resume + report usage; keep one-shot path for judge-only calls
   if any survive D2.
4. **Rework `judge.py` R2** under D2 (hold-vs-revise deliberation; re-derive or
   replace Trigger 1/2).
5. **Wire D3** — consensus-feedback inject after each verse resolves.
6. Copy/adapt `run_gold_standard.py`, `consensus.py`, `regression.py`, `prompts/`.
7. Validate on 創 1:1-3 small batch vs s1's gold standard.

## Directory layout (planned, mirrors s1)
```
survey10_.../
├── SURVEY10_DESIGN.md          # this file
├── session_manager.py          # NEW — persistent session + compaction
├── cli_caller.py               # adapted: stateful callers
├── judge.py                    # adapted: D2 deliberation semantics
├── consensus.py / regression.py / run_gold_standard.py  # adapted from s1
├── prompts/                    # versioned (seed from s1 latest)
├── .s10_sessions.json          # per-leg session ids (gitignored)
└── gold_standard/ round{1,2,3}_results/ run_logs/
```

## Risk flags for Joshua
- **R2 semantics (D2)** is a genuine redesign, not a port. "Convergence" and the
  Trigger 1/2 stability math were built on amnesia; with memory they need new
  definitions. Worth a focused design pass before coding judge.py.
- **Headless compaction (D1)** has no turnkey `/compact` in `-p` mode; the
  summarize-and-reseed loop is the fallback and needs a spike to confirm cost +
  fidelity.
