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

## A2 scoring — two-stage divide-and-conquer (Joshua, 2026-06-25)

> **Scheme correction (supersedes an earlier draft).** An earlier draft made the
> original WLC/SBLGNT the *direct* SN answer key — that over-reached. **FHL's
> 09xxx prefix range is FHL-specific**: standard Strong's tops at H8674 and
> `WLC.tsv` has **zero** 9xxx. Clear Bible *does* tokenize the Hebrew prefixes but
> numbers them in an **augmented standard-range scheme** (Gen 1:1: ב=`H0871a`,
> ה=`H1886a`, ו=`H2050b`), NOT FHL's 09xxx. So **FHL ≠ Clear Bible numbering**;
> WLC-as-answer-key needs a scheme bridge. Since s1/s10 emit **FHL** tags, the
> primary scoring stays **FHL-internal**; Clear Bible is brought in deliberately —
> in Stage 2, as a *source*, not as the answer key.

The KJV/UNV count mismatch (survey5's bottleneck) unfairly penalizes coverage: a
source can't supply SNs its language doesn't express (the 09xxx prefixes, 0853 את,
some 8xxx). On Gen 1:1 the only UNV-only SN was `09002` (the ב prefix). Fix = **two
stages**, each its own divide-and-conquer, escalating rigor.

### Stage 1 — clean baseline (exclude 09xxx; zero scheme bridge)
- **source = KJV+SN, target = UNV-stripped**; score **placement only on
  `UNV-FHL ∩ KJV-FHL`** (the content-word core). The UNV-only 09xxx prefixes are
  **excluded, not scored**.
- Stays **entirely inside FHL's numbering** (what s1/s10 actually emit) → **zero
  bridge, zero extra cost**. The "easy 80%": settle the s1-vs-s10 placement verdict
  on the bulk first.
- `build_exclusion.py` builds it: per verse `shared = UNV-FHL ∩ KJV-FHL`,
  `excluded = UNV-only`; report the excluded-cluster distribution on Gen 1 to
  confirm it is the 09xxx/0853/8xxx families before any paid contest. Plus
  `score_placement(model_output, unv_fhl, shared)`. Cheap (FHL reads, zero model
  cost).

### Stage 2 — harsh full test (include 09xxx) with Clear Bible as the source
The hard tail: can the model place even the **09xxx prefixes**? KJV can't help —
English has no token for ב/ה/ו. **Clear Bible's WLC is the only source that carries
the prefixes explicitly** (Gen 1:1: `בְּ` H0871a `prep`, `הַ` H1886a `art`, `וְ`
H2050b `cj`), so it is the right — and only — input for this test.
- **source = original Hebrew (Clear Bible WLC), bridged to FHL numbering** via a
  small fixed table mapping the handful of inseparable prefixes (בכלמ + ה + ו + ש)
  → FHL 09xxx. Built once, reused everywhere.
- **target = UNV-stripped; score on the FULL set including 09xxx.**
- **Leak-free**: source tokens are Hebrew; the answer is *which Chinese token* —
  not in the Hebrew source. ⚠️ **`WLC.tsv` has a `gloss2` column with Chinese
  glosses** (创造/神/起初/地…); feeding it leaks Chinese hints, so the harsh test
  must feed **Hebrew word + number + morph only, `gloss2` stripped** (or treat
  gloss2 as a separate "with-hint vs no-hint" variable).

| | Stage 1 (baseline) | Stage 2 (harsh) |
|---|---|---|
| scores | content-word core placement | **full placement incl. 09xxx prefixes** |
| source | KJV+SN | **Clear Bible WLC** (explicit prefixes) |
| 09xxx | excluded | **included** (lemma→09xxx bridge) |
| numbering | all FHL, zero bridge | FHL + small fixed prefix bridge |
| role | clean, uncontested verdict | upper-bound stress test |
| cost | lowest (do first) | higher (do after) |

### Clear Bible as a cross-check (supporting role, both stages)
The 10+ aligned languages × translations (each a finished **manual** word-level SN
alignment gold) serve as a **robustness vote** for *why* an SN is excluded: bridge
the FHL 09xxx prefix by **lemma** (ב/ה/ו/את) to the Clear Bible token and confirm
it is either unaligned or aligned only to function words across languages. This
corroborates the Stage-1 exclusion without making Clear Bible the answer key. A
**pure-alignment arena** (project among the aligned languages, score vs their
manual gold — no FHL, no Chinese) remains available for *method* validation, but
is non-Chinese so it does not directly judge the UNV→LCC product.

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
1. build_exclusion.py (Stage 1, CHEAP, FHL-internal, zero model cost — run FIRST):
   - per verse: shared = UNV-FHL ∩ KJV-FHL ; excluded = UNV-only (the 09xxx etc.).
   - kept_set[verse] = shared. Report exclusion-cluster distribution on Gen 1 to
     CONFIRM the 09xxx/0853/8xxx hypothesis before paying for a contest.
   - (optional cross-check) corroborate excluded SNs via Clear Bible alignment by
     lemma bridge — NOT the answer key, just a robustness vote.
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
