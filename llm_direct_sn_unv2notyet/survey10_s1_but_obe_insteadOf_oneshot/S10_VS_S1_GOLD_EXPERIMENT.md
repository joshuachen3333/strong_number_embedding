# s10 vs s1 — the gold contest, judged by FHL ground truth

> Settles empirically the open question from s10 `prompt.history`
> (*"作為黃金標準 S1 比較好還是 S10?"*). Companion:
> [`SURVEY10_DESIGN.md`](SURVEY10_DESIGN.md),
> [`CONVENTIONS_PIPELINE.md`](CONVENTIONS_PIPELINE.md).

## The measurement problem (and the trick)

The production gold task is **UNV → LCC**, but **LCC has no FHL Strong's truth**,
so a UNV→LCC gold can only be judged by *consensus*, not against an answer key —
which is circular for comparing two consensus methods.

**Trick (borrowed from survey5):** run the contest on a task where ground truth
**does** exist — project onto **UNV** (which has FHL tags) **from a different
annotated source** so the answer is never shown:
1. **Source = KJV+SN** (KJV carries its own FHL Strong's; it is *not* the answer).
2. **Target = UNV stripped** of its SN (`strip_shell`).
3. Have each method (**s1** and **s10-E**) project the Strong's numbers
   cross-lingually KJV→UNV.
4. Score each method's UNV output against UNV's **original FHL tags** with
   `survey4/auto_score.py:score_verse` → objective `{exact, coverage, placement,
   format}` per verse.

The method whose UNV output matches FHL truth more often is the better gold
producer — no consensus circularity, and (critically) **no answer leak**: the
projection source is KJV, not the UNV answer. See **A2** below for the leak trap
this avoids (a naive "strip UNV → re-place onto UNV" hands the model its own
answer via the projection source + the system-prompt worked examples).

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

### A2 — objective contest (HAS FHL truth) ★

> ⚠️ **ANSWER-LEAK TRAP (Joshua, 2026-06-25) — read first.** s1/s10 are
> **projection** engines: `_user_prompt(unv_sn, target, …)` feeds an annotated
> **source** (text *with* SN) to project *from*, and the system prompt embeds
> **UNV+SN worked examples**. So the *naive* "strip UNV, ask to re-place onto
> UNV" leaks: if the target is UNV, the projection source (UNV+SN) and the
> system-prompt examples literally **contain the answer** → the model just copies
> the reference. A2 MUST NOT hand the model an annotated copy of the test text.

- **Leak-free design (survey5 framing — source ≠ answer):**
  - **Source = KJV+SN** (KJV carries its *own* FHL Strong's, English) — *not* the
    answer being scored.
  - **Target = UNV stripped** (SN removed).
  - Both s1 and s10 **project KJV's SN cross-lingually onto UNV**.
  - **Score the projected UNV-SN against UNV's original FHL tags** with
    `survey4/auto_score.py:score_verse`. The answer never enters the prompt.
- **Worked-example audit (second leak vector):** the prompt's
  *"Worked examples"* must contain **no verse in the test set** (use held-out
  examples, or strip the examples for the contest). Verify before running.
- **Answers**: *who is more accurate vs ground truth* — mean placement/coverage
  per arm (H1), whether each accepted convention (e.g. C1) **raises** held-out
  placement accuracy (H5, per-convention A/B), false-disagreement reduction (H2).
- **Honest caveat**: KJV→UNV is **cross-lingual** (English→Chinese), *harder*
  than production's same-language UNV→LCC. Unavoidable: only UNV/CUV carry FHL SN
  in Chinese, so two independent *Chinese* annotated texts don't exist — KJV is
  the only leak-free annotated source. `survey5` already runs this exact setup.
  The contest is still fair (s1 and s10 face the identical KJV→UNV task).
- **Key**: a **separate run** — task is KJV→UNV, NOT the UNV→LCC gold we already
  produced; the Gen 1 LCC gold does **not** feed A2.
- **Cost**: higher (fresh s10 live run + s1 run on KJV→UNV), but the **only**
  path that can claim "s10 is as accurate as / beats s1 vs truth."
- **Use as**: the authoritative credibility verdict (H1–H5 below).

**One line**: *A1 measures likeness (cheap, "do they look the same?"); A2
measures correctness (heavier, "who is closer to FHL truth?"). Only A2 uses
`auto_score` against ground truth.* The Arms / Metrics / Hypotheses sections
below describe **A2** (the real contest); A1 is the optional warm-up diff.

## A2 scoring — original-language answer key + alignment-derived exclusion (Joshua, 2026-06-25)

The KJV/UNV Strong's-**count mismatch** (survey5's bottleneck) unfairly penalizes
coverage: projecting from a source can never supply SNs that source's language
doesn't express — Hebrew inseparable prefixes (09xxx), the object marker 0853 את,
some morphology 8xxx. **Empirically confirmed on Gen 1:1**: the only UNV-only SN
was `09002` (the ב prefix). Fix = score **placement only on the SNs both sides
genuinely have**, with a *principled, multi-language* exclusion instead of a
single-translation diff. Two upgrades over the naive `UNV-FHL ∩ KJV-FHL`:

### 1. Canonical SN answer key = the ORIGINAL Hebrew/Greek
`Alignments/data/sources/` holds the source token tables — **WLC / WLCM** (Hebrew
OT) and **SBLGNT / BGNT** (Greek NT) — each token carrying its `strongs` + `lemma`
+ `morph`. This is the **authoritative "which SNs this verse has"**, not a derived
translation. So:
- **SN *set* answer key** = the original (WLC/SBLGNT) per verse.
- **Placement answer key** for the Chinese target = UNV-FHL (where each SN sits on
  Chinese tokens). The original defines *what*; UNV-FHL defines *where*.

### 2. Exclusion list = alignment-derived projectability (not a single-lang diff)
`Alignments/` (Clear Bible / BiblioNexus, **manual** word-level alignments) maps
each original source token to target words across **10+ languages × multiple
translations** (eng `BSB`/`YLT`, fra, spa, por, rus, arb, hin, ben, asm, hau).
**Each (language, translation) pair is itself a finished "translation + word-level
SN alignment" gold** — the same *kind* of artifact as FHL's UNV+SN/KJV+SN, just in
relational Burrito form (target word → alignment record → source token → `strongs`)
rather than inline `詞<SN>`.

For each source SN token, count how many aligned pairs map a target word to it:
- **High coverage** (content words: 神 0430, 創造 1254) → **projectable → keep & score**.
- **Low / zero coverage** (09xxx prefixes, 0853 את, some 8xxx morphology) →
  **language-specific → exclude** (no translation can project them).

10+ languages **vote**, so the exclusion is far more robust than a KJV-only diff
(one translation's idiosyncrasy can't bias it).

### Two contest arenas this unlocks
- **(a) Chinese arena (production-relevant)** — source-with-SN → UNV-stripped,
  score **placement vs UNV-FHL on the kept (projectable) ∩ UNV set**; excluded SNs
  reported separately, not scored. `Alignments/` has **no Chinese**, so UNV's
  placement truth still comes from FHL; the alignment corpus is the *exclusion
  authority*, not a Chinese gold. Source is **no longer limited to KJV** — any
  manually-aligned translation (e.g. BSB) is a candidate, cleaner SN source.
- **(b) Pure-alignment arena (methodology validation, no FHL/Chinese)** — project
  the original source SN onto **any one of the 10+ aligned languages** and score
  against *that language's manual alignment gold*. Fully leak-free, human gold,
  many language pairs — but tests non-Chinese, so it validates the **method**, not
  the UNV→LCC product directly.

### `build_exclusion.py` (planned scaffold)
Join `sources/*.tsv` (SN per original token) + each language's `alignments/*.json`
→ per-SN cross-lingual expression rate → exclusion list; intersect with UNV-FHL
per verse → the fair scoring set. Plus `score_placement(model_output, unv_fhl,
kept_set)`. **Cheap** (local alignment files + FHL UNV, zero model cost) — run on
Gen 1 first to confirm the exclusion clusters as 09xxx/0853/8xxx before any paid
contest.

## Arms

| Arm | Method | Cross-verse learning |
|---|---|---|
| **A — s1** | `../survey1_prompt_evolving` consensus, unchanged | prompt evolution (`+0.1`, gated) |
| **B — s10-E** | this dir: per-verse `/clear`, blind R1/R2 (C tier), gated D-deliberation (post-C), conventions.md | `conventions.md` (gated, versioned) |
| **B0 — s10 ablation** (optional) | s10 with `conventions.md` **frozen empty** | none (isolates the conventions contribution) |

A and B see the **same KJV→UNV corpus** (source KJV+SN, target UNV-stripped, score
vs UNV FHL truth) and the **same panel roster**
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
1. build_exclusion.py (CHEAP, zero model cost — run FIRST):
   - SN set answer key = original WLC/SBLGNT (Alignments/data/sources/*.tsv).
   - per-SN cross-lingual expression rate over the 10+ aligned languages → exclusion
     (low-coverage 09xxx/0853/8xxx morphology+particles).
   - kept_set[verse] = projectable ∩ UNV-FHL. Report exclusion-cluster distribution
     on Gen 1 to CONFIRM the 09xxx/0853/8xxx hypothesis before paying for a contest.
2. Build the contest corpus: source = KJV+SN (or a manually-aligned translation),
   target = UNV stripped (strip_shell, Gen 1–5); UNV-FHL = placement answer key.
   Audit prompt worked-examples to exclude any tested verse (no answer leak).
3. Arm A: run s1 consensus over the corpus → gold_A/{book}/{ch}/{sec}.json
4. Arm B: run s10-E (this dir), scribe active per-chapter → gold_B/... + conventions
   history. (B0 ablation: same but conventions.md frozen empty.)
5. Score: score_placement(gold_X, unv_fhl, kept_set[verse]) per verse, both arms —
   placement only on the kept set; excluded SNs reported separately, not scored.
6. Aggregate: placement/coverage/exact per arm + the secondary metrics.
7. Per-convention A/B on the test split → annotate conventions.md deltas; demote ≤0.
8. Verdict table (below).
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
