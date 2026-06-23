# Survey 10 — S1's gold task, obe-style live panel, with externalized conventions

> Status: **design locked v2** (2026-06-24, the Q1-E re-decision). Supersedes the
> 2026-06-20 v1 (continuous-session + `/compact`). Inherits all of
> `../survey1_prompt_evolving/` logic. This doc is the s10 analog of s1's
> `ARCHITECTURE_DECISIONS.md`. Companion docs:
> [`Original_Design_Decisions.md`](Original_Design_Decisions.md) (option/consequence
> tables + the 06-24 re-decision), [`CONVENTIONS_PIPELINE.md`](CONVENTIONS_PIPELINE.md),
> [`S10_VS_S1_GOLD_EXPERIMENT.md`](S10_VS_S1_GOLD_EXPERIMENT.md).

## Mission

Reproduce s1's 3-model consensus gold-standard pipeline (R1 → R2 → R3 + live
quality evolution + regression gate), run **obe-style** — the three models
(**opus** / **agy** / **codex**) are **three live, mutually-bound CLI sessions in
Terminal tabs**, driven by osascript inject + file-handoff — but with the
cross-verse learning **externalized into a curated `conventions.md`** instead of
accumulating (and bloating, and being lossily `/compact`ed) inside each session.

**The target is not "cheaper s1." The target is "s1-grade or better gold."**
s10 earns that by removing s1's two structural weaknesses:
1. **False disagreement** — many s1 panel splits are *format/convention noise*
   (implicit-marker placement, same-number rebinding), not real placement
   ambiguity. s10 pre-injects the settled `conventions.md` so those evaporate →
   the disagreements that remain are *genuine* placement questions.
2. **No memory of hard cases** — s1 is amnesiac, so a genuine-ambiguity verse
   (3:11-class oscillation) can only be *flagged*, never *resolved*. s10's gated
   the gated D-deliberation tier lets the panel actually settle them.

## The central idea — decouple expertise from independence

The original s10 was downgraded to "cheap propagation engine, unfit to be gold
authority" for **one** reason:

> accumulate expertise (s10's selling point) → only via stateful session →
> sacrifice panel independence → consensus is no longer N independent witnesses →
> not trustworthy.

"Accumulate expertise" and "lose independence" were **welded together**.
**Q1-E breaks the weld**: expertise accumulates in an external, reviewable
`conventions.md`; it does **not** accumulate in session context. Therefore each
session can be **reset (`/clear`) per verse → R1 is blind-independent again, just
like s1**. R1 independence is the bedrock of gold trustworthiness, and E gives it
back while *still* getting smarter verse-over-verse.

## Locked decisions (2026-06-24)

### D1 = E — External conventions memory + per-verse reset
- Each panel session's live context stays **short**: only the current verse task
  + the re-injected `conventions.md`.
- `conventions.md` holds **distilled, regression-gated, versioned** reusable rules
  (e.g. "implicit `<...0853>` 受詞記號 binds to the *following* noun's group, not
  standalone"; "a repeated Strong's number rebinds per occurrence, not once").
  These are **principles distilled from resolved verses**, never raw per-verse
  answers.
- Before each verse, `conventions.md` is **prepended** to the prompt.
- **No `/compact`, no per-leg window thresholds, no context-bloat decay.** (Last
  run's agy coverage-decay and `/compact` loss were both context-bloat artifacts;
  E removes the cause.)

### D2 = C-default + D-escalation (two-tier ladder)
Within a verse (sessions freshly `/clear`'d, so genuinely amnesiac), a **sequential
two-tier ladder** — **not** a mid-R2 escalation, and D is **not** Trigger-2:

```
independent R1  (= sealed bids — clean, collected first)
  → C tier: blind R2-convergence stability (Trigger 1/2) + independent R3 voting
      → majority / resolved              → resolved as C   (highest trust)
      → C EXHAUSTED  (R3 unresolved, OR Trigger-1 convention-evolution regression-FAILS)
          → D tier: reuse those same R1s as sealed bids → reveal → deliberate/revise → consensus
              → still deadlocked         → human
```

- **R1** — blind independent, each leg sees only `conventions.md` + the verse, not
  the others. *(= s1 R1 + conventions preamble.)* These are the **sealed bids**.
- **C tier (R2 + R3)** — **exactly s1**: blind amnesiac R2 re-roll measures
  stability (Level 0–3 → Trigger 1/2), independent R3 voting resolves. **s1's
  stability machinery is preserved verbatim.** Most verses resolve here (highest
  trust, `resolved_at = c_consensus`).
- **D tier (deliberation) — terminal, gated** — fires **only after C is
  exhausted**: i.e. **R3 returns unresolved**, OR a **Trigger-1
  convention-evolution attempt regression-FAILS** (the verse can't be fixed by a
  prompt/convention → it is genuinely ambiguous). It **replaces s1's terminal
  "→ human"** with "→ D, then human." The orchestrator reveals the three sealed R1
  bids and asks each leg **hold-or-revise with reasons** (`resolved_at =
  d_deliberation`). Canonical case: **Gen 3:11**. This is the deliberation amnesia
  cannot do.

**Three distinct failure modes — never conflated:**
- **Trigger 1** (prompt/convention bad) → **evolve conventions** (scribe pipeline).
- **Trigger 2** (weak model) → **model patch** (s1's existing path, kept
  **separate and intact** — *not* D-deliberation; the two must never co-fire).
- **D** (the verse itself is irreducibly ambiguous) → **deliberate** (the tier above).

Net: s1's trust math runs untainted on every verse; deliberation is the **last
resort for the genuine-ambiguity tail only**, never a broad mid-pipeline trigger.
See `judge.py` change scope in
[`CONVENTIONS_PIPELINE.md`](CONVENTIONS_PIPELINE.md) §D-deliberation.

### D3 = Q3-D batched — distilled conventions, not raw answers
- **No raw resolved-answer injection** (that was the worst error-propagation
  path). Feedback flows **only** through `conventions.md`.
- **Cadence: batched per chapter** (configurable N). After a chapter's verses
  resolve, a **scribe** step extracts candidate conventions from that chapter's
  gold, each candidate is **regression-gated** against prior gold, survivors are
  **versioned** into `conventions.md`. Detail: [`CONVENTIONS_PIPELINE.md`](CONVENTIONS_PIPELINE.md).

## Reconciling E with the "live obe sessions" CRUX (Joshua, 2026-06-20)

> 「s10 就是使用已經開啟, 互相綁定的 3 obe, 而非 headless 一次性地呼叫」

Per-verse reset does **not** demote the panel to headless one-shots. The
distinction is **process vs context**:

| Property | Lifetime | Satisfies |
|---|---|---|
| The 3 Terminal tabs / CLI processes | **persistent** — alive & leashed for the whole run, driven by inject | Joshua's "3 mutually-bound live obe" requirement |
| Each session's **conversational context** | **per-verse** — `/clear`'d between verses | Q1-E independence (fresh, blind R1) |
| Cross-verse **learning** | **externalized** — `conventions.md`, re-injected each verse | Q1-E + Q3-D (auditable, gated, generalizable) |

So: **persistent processes, per-verse-fresh contexts, externalized learning.**
The panel is still three bound colleagues; they just consult a shared, reviewed
notebook (`conventions.md`) instead of relying on each one's lossy memory.

### Per-leg reset command
| Leg | Reset between verses | Notes |
|---|---|---|
| opus / claude | `/clear` in the live tab | orchestrator also IS this leg |
| codex (lala) | `/clear` (or `/new`) in the live tab | confirm codex clear verb at spike |
| agy (erha)  | clear / new-conversation in the live tab | confirm agy clear verb at spike |

Fallback if a leg's clear verb can't be driven by inject: **headless one-shot**
(`cli_caller.call_llm`, no `--resume`) is *already* per-call amnesiac, so the
fallback path trivially satisfies per-verse reset.

## What is inherited verbatim from s1

- The R1 (unanimous) → R2 (blind convergence + Trigger 1/2) → R3 (pick /
  all_wrong) pipeline shape — **now intact again** because per-verse reset
  restores blindness (v1's "largest code delta" is mostly gone).
- `consensus.py` `build_gold_standard()` remains the **sole authority** for
  `resolved_at`. Main loop only collects.
- The regression gate — **reused** to gate `conventions.md` edits (this is the
  key reuse; cf. s1 v1.3 REGRESSION_FAILED).
- Gold-standard JSON schema; the 3-leg panel from `cli_caller.py:DEFAULT_MODELS`:
  `opus` (claude) / `agy` (Antigravity, Gemini 3.1 Pro) / `codex`.

### What is new in s10 (the deltas)
1. `conventions.md` + its prepend-into-prompt wiring (D1-E).
2. The **scribe**: convention extraction + regression-gate + versioning (D3).
3. **D-deliberation tier** — sealed-bid round, gated to fire **only after C is
   exhausted** (R3 unresolved / Trigger-1 convention-evolution regression-fail),
   replacing s1's terminal "→ human"; **distinct from** Trigger-2's model patch (D2).
4. Per-verse `/clear` driver in the live transport.

## Transport (unchanged from v1 — validated 2026-06-20)

PRIMARY = osascript **inject** task into live tab + **file-handoff** read-back
(orchestrator writes prompt to a task file, injects a short "read it, write JSON
to answer file" command, polls the answer file — never reads TUI scrollback).
FALLBACK = headless `cli_caller.call_llm` one-shot per leg on any inject failure
(no ack/file within timeout, unparseable answer). Both paths proven for all three
legs (see "Transport validation" below). The s10 `cli_caller.py` already
implements this routing.

## Implementation plan (phased, revised for v2)

1. **Conventions scaffold** — `conventions.md` schema + loader that prepends it to
   the prompt; seed it empty (or from s1's latest prompt distillation). Wire
   `run_gold_standard.py` to pass it through.
2. **Per-verse `/clear` driver** — extend the live transport to `/clear` each leg
   between verses; confirm codex/agy clear verbs at a spike.
3. **D-deliberation tier** — add to `judge.py` as a **post-C terminal handler**:
   when C is exhausted (R3 unresolved / Trigger-1 evolution regression-fails),
   reveal the sealed R1 bids → hold-or-revise. Keep C (blind R2 stability + R3) and
   Trigger-2's model-patch path **unchanged and separate**.
4. **The scribe** — per-chapter convention extraction + regression-gate +
   versioning (`CONVENTIONS_PIPELINE.md`).
5. **Validate** on 創 1:1-3 vs s1 gold, then run the **s10-vs-s1 contest**
   (`S10_VS_S1_GOLD_EXPERIMENT.md`) on a ground-truth corpus.

## Directory layout (planned)
```
survey10_.../
├── SURVEY10_DESIGN.md             # this file (locked decisions + architecture)
├── Original_Design_Decisions.md   # Q1/Q2/Q3 option tables + 06-24 re-decision log
├── CONVENTIONS_PIPELINE.md        # scribe: extract → regression-gate → version
├── S10_VS_S1_GOLD_EXPERIMENT.md   # empirical contest vs s1 (survey4/5 truth)
├── conventions.md                 # THE externalized learning (versioned)
├── cli_caller.py                  # live inject + file-handoff, headless fallback (+/clear driver)
├── judge.py                       # adapted: + D-deliberation (post-C terminal tier)
├── consensus.py / regression.py / run_gold_standard.py  # from s1 (+conventions prepend)
├── prompts/                       # versioned (seed from s1 latest)
├── .s10_sessions.json             # per-leg window ids + session ids (gitignored)
└── gold_standard/ round{1,2,3}_results/ run_logs/
```

## Transport validation (2026-06-20) — both paths proven

Live panel opened in-cwd: **s10-obe** (5544, opus+orchestrator), **s10-lala**
(5555, codex gpt-5.5), **s10-erha** (5557, agy).

| Test | Leg | Result |
|------|-----|--------|
| Canary inject + read-back | lala, erha | PASS |
| **Primary**: inject "write JSON to file" → read file | lala (codex) | PASS ~3s |
| **Primary**: inject "write JSON to file" → read file | erha (agy) | PASS ~9s |
| **Fallback**: headless `cli_caller.call_llm` | opus / codex / agy | PASS 5–7s |

Open config item: erha live tab on Flash → switch to **Gemini 3.1 Pro (High)**
before the real run (headless Pro already confirmed).

## Risk flags
- **`conventions.md` = new single trust-point.** A wrong rule propagates to every
  verse. Mitigation: the **same regression gate** that blocked s1's v1.3; plus
  per-line granularity (finer than whole-prompt +0.1) so a bad rule is revertible
  without losing the whole notebook. The contest (`S10_VS_S1_GOLD_EXPERIMENT.md`)
  scores **each convention** against FHL truth so poison is caught empirically.
- **D-escalation criterion** must be pinned to **"C exhausted"** (R3 unresolved OR
  Trigger-1 convention-evolution regression-fails), **not** to a stability/Trigger-2
  condition. Wrong pinning either over-deliberates (cost/anchoring, fires on stable
  verses) or conflates D with Trigger-2's model patch. Keep Trigger-2 (weak-model
  patch) a separate path that never co-fires with D.
- **Scribe over-extraction** — too many narrow conventions = overfit + injection
  bloat. Batched-per-chapter + regression gate + a convention budget cap mitigate.
- **Live transport landmines** (inject focus-race, Claude-TUI read-back) — already
  mitigated by file-handoff + headless fallback; re-verify the new `/clear` driver
  at the spike.
