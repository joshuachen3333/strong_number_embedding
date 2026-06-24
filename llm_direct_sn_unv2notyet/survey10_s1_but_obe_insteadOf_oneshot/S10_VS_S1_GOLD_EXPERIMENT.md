# s10 vs s1 — the gold contest, judged by FHL ground truth

> Settles empirically the open question from s10 `prompt.history`
> (*"作為黃金標準 S1 比較好還是 S10?"*). Companion:
> [`SURVEY10_DESIGN.md`](SURVEY10_DESIGN.md),
> [`CONVENTIONS_PIPELINE.md`](CONVENTIONS_PIPELINE.md).

## The measurement problem (and the trick)

The production gold task is **UNV → LCC**, but **LCC has no FHL Strong's truth**,
so a UNV→LCC gold can only be judged by *consensus*, not against an answer key —
which is circular for comparing two consensus methods.

**Trick (borrowed from survey4/5):** run the contest on a task where ground truth
**does** exist — **re-annotate UNV against its own FHL tags**:
1. Take UNV+SN (which carries authoritative FHL tags).
2. **Strip** the SN (survey4 `auto_score.strip_sn` / naked-mode `strip_shell`).
3. Have each method (**s1** and **s10-E**) re-place the Strong's numbers from
   scratch, exactly as if UNV were an unannotated target.
4. Score each method's output against the **original FHL tags** with
   `survey4/auto_score.py:score_verse` → objective `{exact, coverage, placement,
   format}` per verse.

The method whose gold matches FHL truth more often is, by definition, the better
gold producer — no consensus circularity.

## Two comparison flavors — A1 vs A2 (read before running any contest)

"Run s1 on the same verses and compare" can mean two very different things. They
answer different questions and only one yields an objective score, because the
production gold we already have (Gen 1) is **UNV→LCC and LCC has no FHL truth**.

### A1 — direct method diff (same UNV→LCC verses, NO objective truth)
- **What**: run `../survey1_prompt_evolving/run_gold_standard.py` on the *same*
  UNV→LCC verses we already did in s10, producing **s1's gold**; then **diff
  s1-gold vs s10-gold** verse by verse.
- **Answers**: *where* the two methods place differently — e.g. did s10's
  convention C1 make it agree/disagree with s1 on verb-morphology verses.
- **Cannot answer**: *who is right.* LCC has no FHL answer key, so this is
  similarity-only ("do they match?"), not accuracy.
- **Cost**: low-ish. s1 is headless one-shot (faster per call than s10's live
  panel) but still runs full R1→R2→R3 consensus over 31 verses on 3 accounts.
- **Use as**: a cheap warm-up / sanity diff, NOT a credibility verdict.

### A2 — objective contest (strip-UNV self-re-annotation, HAS FHL truth) ★
- **What**: the strip-UNV trick above.題目 = **UNV+SN with its SN stripped**
  (`strip_shell`); both s1 and s10 re-place the numbers onto UNV; score each
  against the **original FHL tags** with `survey4/auto_score.py:score_verse`.
- **Answers**: *who is more accurate vs ground truth* — mean placement/coverage
  per arm (H1), whether each accepted convention (e.g. C1) actually **raises**
  held-out placement accuracy (H5, the per-convention A/B), false-disagreement
  reduction (H2), etc.
- **Key**: this is a **separate run** — its task is stripped-UNV, NOT the
  UNV→LCC gold we already produced. The Gen 1 LCC gold does **not** feed A2
  directly; A2 needs s10 (and s1) re-run on the stripped-UNV corpus.
- **Cost**: higher (a fresh s10 live run on stripped-UNV + an s1 run), but it is
  the **only** path that can claim "s10 is as accurate as / beats s1 vs truth."
- **Use as**: the authoritative credibility verdict (the H1–H5 tests below).

**One line**: *A1 measures likeness (cheap, "do they look the same?"); A2
measures correctness (heavier, "who is closer to FHL truth?"). Only A2 uses
`auto_score` against ground truth.* The Arms / Metrics / Hypotheses sections
below describe **A2** (the real contest); A1 is the optional warm-up diff.

## Arms

| Arm | Method | Cross-verse learning |
|---|---|---|
| **A — s1** | `../survey1_prompt_evolving` consensus, unchanged | prompt evolution (`+0.1`, gated) |
| **B — s10-E** | this dir: per-verse `/clear`, blind R1/R2 (C tier), gated D-deliberation (post-C), conventions.md | `conventions.md` (gated, versioned) |
| **B0 — s10 ablation** (optional) | s10 with `conventions.md` **frozen empty** | none (isolates the conventions contribution) |

A and B see the **same stripped-UNV corpus** and the **same panel roster**
(opus/agy/codex). Only the method differs. B0 isolates how much the conventions
pipeline itself contributes vs the transport.

## Corpus

- **Primary**: Genesis 1–5 (138 verses) — the corpus already partially run; UNV
  has full FHL truth across it. 68 verses already produced clean last session
  provide a warm cache for arm A baselining.
- **Held-out for convention scoring**: split each chapter into *train* (scribe may
  extract conventions from these resolved verses) and *test* (never extracted
  from; used only to measure whether a convention generalizes).
- Extendable to a second book (e.g. a NT chapter) to test convention transfer
  across Testaments.

## Metrics (all from `survey4/auto_score.py`)

Per verse, against FHL truth:
- **placement** (primary) — fraction of truth tags placed on the right token.
- **coverage** — fraction of truth tags present (no missing/extra).
- **exact** — whole-verse exact match (strict).
- **format** — FHL-format compliance.

Aggregated per arm: mean placement/coverage, exact-match rate, and the
**disagreement profile** below.

### Secondary / mechanism metrics
- **Cost**: total LLM calls + tokens per arm (s10 should fall over time as
  conventions settle and re-rolls drop).
- **Genuine-ambiguity resolution**: # verses where blind R2 flagged instability,
  split by *resolved by D-deliberation* (s10 only) vs *left flagged* (s1).
- **False-disagreement removed**: # R1 panel splits in arm A that **do not occur**
  in arm B because a convention pre-aligned them. This is s10's headline claim —
  measure it directly.
- **Per-convention delta**: for each rule in `conventions.md`, placement accuracy
  on the *test* split **with vs without** that rule. Positive = real; ≤0 = demote
  (closes the `CONVENTIONS_PIPELINE.md` step-5 loop).

## Hypotheses (falsifiable)

- **H1 (parity-or-better)**: mean placement(B) ≥ placement(A). *Refuted if s10 is
  worse → s10 stays a propagation engine, s1 remains gold authority.*
- **H2 (false-disagreement)**: B has materially fewer R1 panel splits than A on
  convention-covered phenomena (implicit markers, rebinding, 神/上帝).
- **H3 (resolves the hard ones)**: among R2-flagged unstable verses, B resolves a
  higher fraction via D-deliberation than A leaves flagged.
- **H4 (cheaper over time)**: B's per-verse cost trends **down** across chapters
  as conventions settle; A's stays flat.
- **H5 (conventions are real)**: most accepted conventions show **positive**
  held-out placement delta (H5 fails → the scribe is overfitting; tighten the
  gate / budget).

## Procedure

```
0. Freeze panel roster (opus/agy/codex); erha → Gemini 3.1 Pro (High).
1. Build stripped-UNV corpus (strip_sn over Gen 1–5); keep FHL truth as key.
2. Arm A: run s1 consensus over the corpus → gold_A/{book}/{ch}/{sec}.json
3. Arm B: run s10-E (this dir) over the SAME corpus, with the scribe active
   per-chapter → gold_B/... + conventions.md history.
   (B0 ablation: same but conventions.md frozen empty.)
4. Score: auto_score.score_verse(gold_X, fhl_truth) for every verse, both arms.
5. Aggregate: placement/coverage/exact per arm + the secondary metrics.
6. Per-convention A/B on the test split → annotate conventions.md deltas; demote ≤0.
7. Verdict table (below).
```

## Verdict table (to fill)

| Metric | Arm A (s1) | Arm B (s10-E) | B0 (no conv) | Winner |
|---|---|---|---|---|
| mean placement | | | | |
| mean coverage | | | | |
| exact-match rate | | | | |
| false-disagreements (R1 splits) | | | | |
| genuine-ambiguity verses resolved (D-deliberation) | n/a | | n/a | |
| total cost (calls / tokens) | | | | |
| conventions w/ positive delta | n/a | / | n/a | |

## Decision rule

- **B ≥ A on placement AND H5 holds** → s10-E is a **co-equal or superior** gold
  producer; promote it from "propagation engine" to gold authority (or run both
  and reconcile). This is the brief's stretch goal ("甚至超越").
- **B ≈ A but cheaper (H4) and removes false-disagreements (H2)** → s10-E is the
  **preferred production** path (same trust, less cost, cleaner residual
  disagreements), with s1 retained as an audit cross-check.
- **B < A** → s1 stays the authoritative gold; s10 reverts to cheap propagation,
  and the conventions pipeline is re-examined (likely H5 failure = overfit).

## Why this is a fair test
- Same panel, same corpus, same objective scorer — only the *method* varies.
- Ground truth is FHL's own tags, not either method's consensus → no circularity.
- The B0 ablation isolates the conventions contribution from the transport, so a
  win can be **attributed**, not just observed.
