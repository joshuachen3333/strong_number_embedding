# Survey 10 — Original Design Decisions (Q1/Q2/Q3 → D1/D2/D3)

> **Purpose**: capture s10's original design questions, their *full* option spaces
> with consequences, and the option originally chosen (★) — so the decisions can
> be **revisited**.
>
> **Provenance**: the original locked decisions (D1/D2/D3) were made **2026-06-20**
> by the s10 sibling (`survey10_…-obe`) via an **`AskUserQuestion` design Q&A** with
> Joshua (s10 `prompt.history`: *"[S10 design Q&A answers — Joshua, via
> AskUserQuestion]"*). The chosen answers are summarized in
> [`SURVEY10_DESIGN.md`](SURVEY10_DESIGN.md) as D1/D2/D3. The option/consequence
> tables below were authored 2026-06-24 (`survey1_prompt_evolving-obe`) for re-decision.

## Cross-cutting tension (read first)

The three questions sit on **one dial**:

```
   MAX INDEPENDENCE (trustworthy gold)        MAX EXPERTISE/THROUGHPUT (cheap propagation)
   Q2-C, Q3-C  ─────────────────────────────────────────────────  Q2-A ★, Q3-A ★ (current)
                       Q2-D / Q3-B / Q1-E  =  the "have-both" middle (most engineering)
```

Gold-standard trustworthiness rests on **panel independence** (s1 preserves it).
s10's premise (stateful sessions + outcome feedback) trades independence for
**accumulated expertise + throughput**. **Q2 and Q3 are the independence-spenders;
Q1 is about sustainability.** The current picks (Q1-A, Q2-A, Q3-A) sit at the far
*expertise* end — which is why the sibling concluded *"S1 stays the authoritative
gold standard; S10 is a cheap propagation engine."*

---

## Q1 — Session lifetime & context management

*"How long does each model's persistent session live, and how is its context window kept from bloating?"*

| Option | What it means | 厲害後果 (好) | 厲害後果 (壞 / 風險) |
|---|---|---|---|
| **A ★ Continuous + self-compact at 40–50%** | One session per leg across all verses; `/compact` when window ~45% full | Minds stay lean & sharp; bounded cost; accumulated conventions survive | `/compact` is **lossy** (each compaction silently drops detail; a bad compact loses a settled convention); **per-leg thresholds** (opus ~1M vs agy/codex smaller) = complexity; **headless fallback can't `/compact`** → live vs fallback context diverge |
| **B Continuous, never compact** | Run until window fills, then forced reset | Max retention, zero compaction loss | Quality **degrades past ~50–70%** (lost-in-the-middle); pricier every call; eventually **hard-wall → total context loss mid-book** |
| **C Reset per chapter/book** | Fresh session each chapter | Simple, predictable, no compaction; bounded | **Throws away cross-verse learning** at each reset (partly defeats the obe premise); ≈ s1 statelessness at chapter granularity |
| **D Rolling window (keep last N verses)** | Slide context, drop oldest | Bounded, recent-biased continuity | Loses early-established conventions; manual window bookkeeping |
| **E External "conventions" memory (re-injected)** | Raw context stays short; a curated *lessons-learned* doc is maintained & re-injected | **Decouples learning from the window** — most robust to limits; learning explicit & auditable; *also reduces Q3 error-propagation* | Adds a **curation layer** (who writes/updates the digest, when) |

**→ Chosen: D1 = A** (continuous sessions, `/compact` at 40–50% context; per-leg threshold; summarize-and-reseed fallback if `/compact` undriveable).

---

## Q2 — Statefulness vs blind convergence  *(THE crux — largest code delta)*

*"In s1, R2 re-runs the task with **no memory** to measure instability (Level 0–3 → Trigger 1/2). With persistent sessions a model **remembers** → re-asking gives trivial self-agreement. What replaces the blind-convergence premise?"*

| Option | What it means | 厲害後果 (好) | 厲害後果 (壞 / 風險) |
|---|---|---|---|
| **A ★ Everything stateful** | All calls (R1/R2/R3) share the persistent session; R2 = genuine *deliberation* (hold-vs-revise w/ memory) | **Can resolve genuine ambiguity** (the 3:11-class oscillation amnesia can't); models reason about each other's answers; accumulated expertise | **Independence lost → anchoring/groupthink** (a confident-wrong model drags the others; consensus stops being N independent witnesses); **Trigger 1/2 stability math must be fully redesigned**; **gold-standard trustworthiness weakened** |
| **B Hybrid: stateful R1, blind R2** | Keep R1 stateful (expertise) but fork a *clean* context for R2 to preserve instability measurement | Keeps s1's instability-detection AND R1 expertise | **Hard/unreliable** — you can't truly make a stateful model "forget" for R2 (telling it to ignore the convo is leaky); only partial independence |
| **C Fully independent (= s1, just live transport)** | No memory accumulation; s10 = s1 with fancier inject transport | Preserves consensus independence + all s1 machinery unchanged; trustworthy | **Defeats the point of s10** — no expertise gain, **3:11 oscillation NOT solved**; obe transport spent for ~no quality gain |
| **D Stateful + independence safeguard (sealed-bid)** | Stateful memory, but each model **commits its answer privately before seeing others**, then deliberates | Accumulated expertise **and** mitigated anchoring (first answer uninfluenced) | Highest **orchestration complexity** (enforce commit-before-reveal across 3 live tabs); deliberation can still drift after reveal |

**→ Chosen: D2 = A** (everything stateful; R2 becomes hold-vs-revise deliberation; Trigger 1/2 semantics flagged for redesign — *the largest code delta of s10*).

---

## Q3 — Outcome feedback

*"After a verse resolves, do we inject 'the consensus answer was X' back into the sessions?"*

| Option | What it means | 厲害後果 (好) | 厲害後果 (壞 / 風險) |
|---|---|---|---|
| **A ★ Feed resolved consensus to all 3** | Inject the settled answer into every session | **Fastest learning loop** — later verses inherit settled conventions; the real obe payoff | **Worst error-propagation** — a *wrong* early consensus injected as truth **contaminates all future verses systematically**; maximal groupthink; ambiguity over which form to feed (shelled/naked/reasoning) |
| **B Feed back only to the wrong/minority** | Correct only dissenters; winners keep their own path | Some diversity preserved; lighter correction | Per-model bookkeeping; minority "corrected" toward a possibly-wrong majority |
| **C No feedback** | Each session keeps only its own (maybe-wrong) memory | Preserves diversity/independence longest | **No correction** — a model repeating the same mistake never learns; continuity without improvement |
| **D Periodic distilled-convention digest** | Inject a curated *"conventions we've settled"* summary every N verses, not raw per-verse answers | Learning at the **generalizable convention level** (not memorizing answers); bounded; less per-verse overfitting | Needs the digest curated (engineering); slower to propagate than A |

**→ Chosen: D3 = A** (feed resolved consensus back into all 3 sessions — the obe-style learning loop).

---

## Synthesis — the decision actually hiding inside Q2 + Q3

> **Do you want s10's output to BE a trustworthy gold standard, or to be a fast
> propagation engine seeded by s1's trustworthy gold?**

- **Far-right (current: Q2-A, Q3-A)** → propagation engine: cheap, fast, accumulates
  expertise, but **not independently trustworthy** as a gold standard.
- **Move left (Q2-D sealed-bid, Q3-B/D, Q1-E external memory)** → recover independence
  / limit error-propagation, at higher engineering cost.
- **Q1 is mostly orthogonal** (sustainability), **except option E** (external memory),
  which *also* mitigates Q3's error-propagation (curated conventions are reviewable
  before they can poison the panel).

---

## Later clarifications (after the original Q&A — for completeness)

These were pinned in subsequent prompts, not the original AskUserQuestion:

- **CRUX**: PRIMARY = live `osascript` inject + **file-handoff** read-back into the 3
  already-open mutually-bound obe sessions; **FALLBACK** = headless `--resume`/
  `--conversation` of the *same* session id, per-call, when an inject round fails.
- **Lifecycle**: the s10 orchestrator **opens the 3 panel sessions itself** first.
- **Panel roster**: `s10-obe` (opus leg **+** orchestrator — no separate s10-opus) /
  `s10-lala` (codex) / `s10-erha` (agy).
- **Fallback contract**: inject failure (no ack/file within timeout, unparseable
  read-back, session errored) → call s1's stateless `cli_caller.call_llm()` one-shot.
- **Open methodological question** (s10 `prompt.history`): *"Which is the gold standard
  — S1 or S10?"* → sibling's lean: **S1 authoritative (independent); S10 = cheap
  propagation**, to be settled empirically against survey4/5 ground truth.

---

## RE-DECISION — 2026-06-24 (D1→E pivot, Q2/Q3 re-settled)

> **Trigger**: `survey1_prompt_evolving-obe` redesign brief
> ([`20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md`](20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md)),
> per Joshua. Goal: move s10 off the far-*expertise* end of the dial so it can
> **rival s1 for trustworthy gold**, not merely propagate s1's gold cheaply.
> **Decided by Joshua via `AskUserQuestion`** (s10 `prompt.history`,
> 2026-06-24): Q2 = **Hybrid**, Q3 = **D-batched**. D1 = **E** was directed by
> the brief.

### The pivot in one sentence
**Q1-E decouples "accumulated expertise" from "lost independence."** Cross-verse
learning moves out of each model's session context and into an external,
**reviewable** `conventions.md`. Because the learning is externalized, each panel
session can **`/clear` (reset) per verse** → R1 independence is restored to
s1-grade *for free*. The two things that were welded together in the original
design (expertise ⊥ independence) come apart.

### New decisions

| | Original (2026-06-20) | **Re-decided (2026-06-24)** | Why the change |
|---|---|---|---|
| **D1** | **A** — continuous session, `/compact` at 40–50% | **E** — external `conventions.md` + **per-verse `/clear`** | A's `/compact` is lossy + per-leg-threshold complex + diverges from headless fallback; E makes learning explicit/auditable, never bloats context, and *enables* independent R1. Empirically: last run's agy coverage-decay (context overflow) and `/compact` loss both **vanish** under E. |
| **D2** | **A** — everything stateful; R2 = memory-ful deliberation; Trigger 1/2 "largest code delta" | **Hybrid (Q2-D-gated)** — R1 blind-independent; **blind R2 measures stability (s1 machinery intact)**; escalate to **sealed-bid R2.5 deliberation only when blind R2 flags instability** | Per-verse reset already restores blind independence, so the original "largest code delta" mostly evaporates. Hybrid keeps s1's Trigger 1/2 trust math AND adds deliberation exactly on the genuine-ambiguity (3:11-class) verses amnesia can only flag. |
| **D3** | **A** — inject raw resolved consensus into all 3 | **Q3-D batched** — extract **distilled conventions per chapter**, regression-gate, version, re-inject | Raw-answer feedback = worst error-propagation (one wrong early consensus contaminates all later verses). Batched distilled conventions learn at the *generalizable* level, are gated before they can poison, and overfit less than per-verse. |

### Where each decision now lives on the dial
The cross-cutting dial (top of this doc) moves **left** (toward trustworthy gold):
`D1-E + Q2-hybrid + Q3-D-batched` is the **"have-both" middle** — accumulated
expertise *and* preserved independence — at the cost of one new engineering
artifact: the curated, regression-gated `conventions.md` pipeline.

### Reconciling E with Joshua's "live obe sessions" CRUX
Per-verse reset does **not** abandon the live mutually-bound panel. The 3 obe
tabs stay **alive and leashed** for the whole run (persistent *processes*,
driven by osascript inject — Joshua's hard requirement); only their
conversational *context* is `/clear`'d between verses. So: **persistent
processes, per-verse-fresh contexts, externalized learning.** The "3 bound
colleagues" property is preserved; the "amnesiac independence" property is
regained; the `conventions.md` carries what used to (lossily) accumulate in
each head.

### Honest residual risk
`conventions.md` becomes a **new single trust-point** — a wrong rule is
inherited by every verse. This is just **s1's prompt in a new form**, guarded by
**the same regression gate** (cf. s1's v1.3 REGRESSION_FAILED block). The
upgrade: conventions are **per-line addable/removable**, so the gate is finer
than s1's whole-prompt +0.1 bump and far less likely to regress 8 verses on one
edit. "Prompt evolution" → "**convention accumulation**."

---

## Source pointers
- s10 `prompt.history` (design-Q&A era + 2026-06-24 re-decision): the `AskUserQuestion` answers + later clarifications.
- [`SURVEY10_DESIGN.md`](SURVEY10_DESIGN.md): the locked decisions + implementation plan + transport validation.
- [`CONVENTIONS_PIPELINE.md`](CONVENTIONS_PIPELINE.md): the extract → regression-gate → version pipeline that populates `conventions.md`.
- [`S10_VS_S1_GOLD_EXPERIMENT.md`](S10_VS_S1_GOLD_EXPERIMENT.md): the empirical contest vs s1, judged by survey4/5 FHL ground truth.
- [`20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md`](20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md): the redesign brief that triggered this re-decision.

---

# RE-DECISION (2026-06-24) — Joshua + `survey1_prompt_evolving-obe`

> The original D1/D2/D3 (all = option A) put s10 at the *cheap-propagation* end.
> Joshua is re-deciding toward the *gold-competitive* combination. **Status: Q1 & Q2
> locked; Q3 still under discussion — do NOT implement until Q3 is settled.**

## Q1 → **E** (External conventions memory) — *was A*
- Each leg's session stays **short and resets per verse**; cross-verse expertise lives
  in a curated, auditable **`conventions.md`** that is re-injected each verse, and
  updated (through a **regression gate**) only when a verse reveals a new convention.
- **Why**: decouples "accumulate expertise" from "consume context window" → no `/compact`,
  no per-leg window juggling, no lossy compaction; learning is **explicit & reviewable**;
  it *also* defuses Q3's error-propagation (a wrong convention is catchable before it spreads).
- **Knock-on**: this is the linchpin that lets Q2 keep R1 independent (per-verse reset
  restores s1's amnesia premise *within* a verse) — i.e. **E is what makes s10 able to
  rival/surpass s1 for gold** (see `20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md`).

## Q2 → **C (default) + D (hard-verse escalation)** — *was A; hybrid, not either/or*
A two-tier escalation ladder, NOT two competing modes:

```
independent R1 (= sealed bids — clean, collected first)
  → C tier: blind R2-convergence stability + independent voting (all independent)
      → majority reached → resolved as C  (highest trust)
      → C exhausted (no majority / Trigger-1 evolution fails regression / R3 unresolved)
          → D tier: reuse those same R1s as sealed bids → reveal → deliberate/revise → consensus
              → still deadlocked → human
```

**Why it is coherent (no contradiction):**
1. **C's R1 *is* D's sealed bid** — same independent first move; they share data, zero waste.
2. **Sequential tiers, not simultaneous** — D fires only *after* C's independent signals are
   collected untainted; C's measurements are never polluted.
3. **Q1=E contains D's statefulness within the verse** — the deliberation memory is wiped by
   the per-verse reset, so it never pollutes other verses' C-independence.
4. It is the **natural completion of s1's ladder**: s1 ended at "→ human"; this replaces that
   terminal tier with "→ try D deliberation, *then* human."
5. **Clean division of failure modes** (no overlap): Trigger 1 = *prompt/convention* bad →
   evolve conventions; Trigger 2 = *weak model* → patch; **D = the verse itself is genuinely
   ambiguous** (prompt & models fine) → deliberate. 3:11 is the canonical D case (Trigger-1
   evolution regression-failed → proves it's irreducible verse-ambiguity, not a prompt fix).

**Design carefully (not contradictions, just must-dos):**
- Record **two trust tiers** in `resolved_at` (`c_consensus` vs `d_deliberation`) — a feature
  (auditable), structurally identical to s1 already distinguishing round1/2/3/unresolved.
- **Pin the handoff** = "C marks unresolved / Trigger-1 evolution fails regression."
- **Anchor D's trust on the sealed first answers**; deliberation output must stay auditable.

**Feasibility**: C tier = low (reuse s1, E restores its premises); handoff = low (one conditional
at s1's existing unresolved point); D tier = medium, **contained** (an escalation handler for a
few hard verses — do NOT make the whole pipeline stateful).

## Q3 / D3 → **D** (periodic distilled, audited convention digest) — *was A*
- **Not** raw per-verse answers injected into sessions. Instead, settled rules are
  **distilled into `conventions.md`** and re-injected — i.e. **the feedback channel
  *is* updating `conventions.md`** (the same artifact Q1-E maintains; Q3-D and Q1-E
  are two faces of one mechanism).
- **Why**: learning at the **generalizable convention level** (not memorizing specific
  answers → less per-verse overfitting); and a wrong "lesson" must pass the
  **regression gate** before it can spread → **defuses A's systematic error-propagation**.

---

## ✅ DECISION SET COMPLETE (2026-06-24)

| Q | Original | **Re-decided** |
|---|---|---|
| **Q1** lifetime/context | A (`/compact`) | **E** — external `conventions.md`, per-verse reset |
| **Q2** statefulness | A (all stateful) | **C default + D hard-verse escalation** (two-tier ladder) |
| **Q3** feedback | A (raw to all 3) | **D** — distilled, gate-audited convention digest |

**The through-line**: `conventions.md` is the spine of all three — it carries the
expertise (Q1-E), it is the feedback channel (Q3-D), and it is what lets R1 stay
independent so C/D can run (Q2). The whole design now sits in the **"have-both"
middle**: accumulated expertise **without** sacrificing the independence that makes
gold trustworthy → **s10 can rival, and on the hard tail surpass, s1 for gold
production.** The single new point of trust (`conventions.md`) is governed by s1's
existing regression-gate discipline.

**Next**: re-decisions are locked; the s10 sibling is already mid-redo with
`Q1-E + independent-R1 + Q3-D` (per its START flare) but does NOT yet have the
**refined Q2 hybrid (C-default + D-escalation)** — that needs relaying before/at its
next checkpoint.
