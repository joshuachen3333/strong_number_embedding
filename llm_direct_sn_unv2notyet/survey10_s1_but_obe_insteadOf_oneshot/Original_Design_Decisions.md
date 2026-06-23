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

## RE-DECISION — 2026-06-24 (D1→E pivot; Q2/Q3 re-settled)

> **Trigger**: `survey1_prompt_evolving-obe` redesign brief
> ([`20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md`](20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md)),
> per Joshua. Goal: move s10 off the far-*expertise* end of the dial so it can
> **rival s1 for trustworthy gold**, not merely propagate it cheaply.
> **Decided by Joshua** — Q1-E directed by the brief; **Q2/Q3 via `AskUserQuestion`**
> (s10 `prompt.history`, 2026-06-24). *This section supersedes and collapses the two
> earlier draft RE-DECISION blocks (merged 2026-06-24 after survey1-obe review;
> R2.5 escalation re-pinned, Trigger-1 target unified, stale status removed).*

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
| **D2** | **A** — everything stateful; R2 = memory-ful deliberation; Trigger 1/2 "largest code delta" | **C-default + D-escalation** two-tier ladder (see *Q2 locked ladder* below) | Per-verse reset restores blind R1 independence, so **C runs all of s1's machinery untainted**; **D-deliberation is a TERMINAL tier** for the genuine-ambiguity tail — it fires only *after C is exhausted*, not as a mid-pipeline escalation. The original "largest code delta" evaporates. |
| **D3** | **A** — inject raw resolved consensus into all 3 | **Q3-D batched** — extract **distilled conventions per chapter**, regression-gate, version, re-inject | Raw-answer feedback = worst error-propagation (one wrong early consensus contaminates all later verses). Batched distilled conventions learn at the *generalizable* level, are gated before they can poison, and overfit less than per-verse. |

### Where each decision now lives on the dial
The cross-cutting dial (top of this doc) moves **left** (toward trustworthy gold):
`D1-E + (Q2 C-default + D-escalation) + Q3-D-batched` is the **"have-both" middle** —
accumulated expertise *and* preserved independence — at the cost of one new
engineering artifact: the curated, regression-gated `conventions.md` pipeline.

### Q2 locked ladder (C-default + D-escalation) — authoritative
A two-tier escalation ladder — NOT two competing modes, and NOT a mid-R2 escalation:

```
independent R1  (= sealed bids — clean, collected first)
  → C tier: blind R2-convergence stability (Trigger 1/2) + independent R3 voting
      → majority / resolved              → resolved as C   (highest trust)
      → C EXHAUSTED  (R3 unresolved, OR Trigger-1 convention-evolution regression-FAILS)
          → D tier: reuse those same R1s as sealed bids → reveal → deliberate/revise → consensus
              → still deadlocked         → human
```

**Clean division of failure modes (no overlap) — the load-bearing correction:**
- **Trigger 1** = *prompt/convention* bad → **evolve conventions** (feeds the
  scribe / `conventions.md` pipeline — the *same* learning channel as Q3-D, **not** a
  separate prompt `+0.1` bump).
- **Trigger 2** = *weak model* → **model patch** (s1's existing path, kept
  **separate and intact** — a distinct action from D-deliberation; the two must
  never be conflated or co-fired on one verse).
- **D-deliberation** = the *verse itself* is genuinely ambiguous (prompt & models
  fine) → reveal sealed R1 bids → deliberate. Fires **only after C is exhausted**;
  it **replaces s1's terminal "→ human"** with "→ D, then human." Canonical case:
  **Gen 3:11** (Trigger-1 evolution regression-failed → proved irreducible
  verse-ambiguity, not a prompt fix).

**Why it is coherent:** C's R1 *is* D's sealed bid (shared data, zero waste); the
tiers are **sequential** (D fires only after C's independent signals are collected
untainted, never simultaneously); Q1-E's per-verse reset **contains** D's
within-verse statefulness so it never pollutes other verses' C-independence.
`resolved_at` records **two trust tiers** (`c_consensus` vs `d_deliberation`) —
auditable, structurally like s1 already distinguishing round1/2/3/unresolved.

### Q1-E and Q3-D are one mechanism, two faces
`conventions.md` is the spine of all three decisions: it **carries** the expertise
(Q1-E), it **is** the feedback channel (Q3-D), and it keeps R1 **independent** so
C/D can run (Q2). **Trigger-1 evolution and the Q3-D per-chapter digest are the
same regression-gated write-path** into `conventions.md` — one feedback artifact,
one gate, no second ungated channel.

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
edit. Because **Trigger-1 evolution now writes to the *same* `conventions.md`**
(not a separate prompt), **one gate guards every learning write** — there is no
second, ungated feedback channel. "Prompt evolution" → "**convention accumulation**."

### ✅ DECISION SET COMPLETE (2026-06-24)

| Q | Original | **Re-decided** |
|---|---|---|
| **Q1** lifetime/context | A (`/compact`) | **E** — external `conventions.md`, per-verse reset |
| **Q2** statefulness | A (all stateful) | **C default + D hard-verse escalation** (two-tier ladder) |
| **Q3** feedback | A (raw to all 3) | **D** — distilled, gate-audited convention digest |

**The through-line**: `conventions.md` is the spine of all three — it carries the
expertise (Q1-E), it is the feedback channel (Q3-D), and it is what lets R1 stay
independent so C/D can run (Q2). The design sits in the **"have-both" middle**:
accumulated expertise **without** sacrificing the independence that makes gold
trustworthy → **s10 can rival, and on the hard tail surpass, s1 for gold
production.** The single new point of trust (`conventions.md`) is governed by s1's
existing regression-gate discipline.

---

## Source pointers
- s10 `prompt.history` (design-Q&A era + 2026-06-24 re-decision + review-corrections): the `AskUserQuestion` answers + later clarifications.
- [`SURVEY10_DESIGN.md`](SURVEY10_DESIGN.md): the locked decisions + implementation plan + transport validation.
- [`CONVENTIONS_PIPELINE.md`](CONVENTIONS_PIPELINE.md): the extract → regression-gate → version pipeline that populates `conventions.md`; the D-deliberation (post-C) handler; Trigger-1→conventions unification.
- [`S10_VS_S1_GOLD_EXPERIMENT.md`](S10_VS_S1_GOLD_EXPERIMENT.md): the empirical contest vs s1, judged by survey4/5 FHL ground truth.
- [`20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md`](20260624_from_survey1obe_to_survey10obe_redesign_Q1E.md): the redesign brief that triggered this re-decision.