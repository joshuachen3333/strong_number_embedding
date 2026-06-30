# s10 vs s1 — the gold contest, judged by FHL ground truth

> Settles empirically the open question from s10 `prompt.history`
> (*"作為黃金標準 S1 比較好還是 S10?"*). Companion:
> [`SURVEY10_DESIGN.md`](SURVEY10_DESIGN.md),
> [`CONVENTIONS_PIPELINE.md`](CONVENTIONS_PIPELINE.md).

## s10's identity — founding intent vs current reality (2026-06-30)

Read this before assuming what s10 *is*. The name is now a fossil.

**Founding intent.** `s10 = s1_but_obe_insteadOf_oneshot` — do s1's gold task, but via
**live, injectable CLI sessions** (lala=codex, erha=agy) **instead of** s1's stateless
`oneshot` API calls. The point was that a *live session carries context across verses*,
so the model would **accumulate learned conventions chapter-by-chapter** like a scribe
who gets fluent as it copies. "How lala/erha reuse context" was the whole raison d'être.

**What actually happened — the intent was overturned by its own discovery.** The
**per-call `/clear` blindness** finding (each call must start blank to prevent
answer-leak / cross-verse contamination) collapsed the premise: blind-live ≡ headless
in quality, so there is no quality reason to keep the live session. s10 went **fully
headless** (`cli_caller.LIVE_WINDOWS = {}`). Fully headless = **no session
context-carry at all** — lala/erha have no cross-verse memory.

**So s10's context-reuse mechanism migrated from session-memory → an externalized
file.** Cross-verse learning now lives in [`conventions.md`](conventions.md): a
disk-resident, **regression-gated**, scribe-distilled ledger (one atomic `## C<n>` rule
per heading, gate-PASS provenance) that is **re-injected into every blind call** as a
preamble. Context isn't *carried*; it's *externalized and re-fed*.

**Consequence — s10 and s1 have converged more than the name implies.** Both are now
**blind per-call** and both **externalize accumulated learning to disk and re-feed it**.
The original differentiator (live context-carry) is gone.

**⚠️ Same model count — NOT single-vs-multi.** Both s10 and s1 run the **same 3-model
consensus** (`run_gold_standard.py`: opus / agy / gpt panel; R1 unanimous → R2 debate →
R3 judge; shared `consensus.py`). A natural-but-wrong simplification is to call s10
"single model" — that comes from the **A2 contest probe** (`run_a2_contest.py`,
`run_stage2_harsh.py`), which deliberately runs **one model** (opus, arm B vs B0) to
*isolate the conventions effect*. That single-model setup is the **measurement
instrument**, not s10's gold method. s10's gold production is 3-model, same cost base
as s1.

**The genuine remaining difference is ONE added subsystem — `s10 ⊇ s1`:**

| | s1 | s10 |
|---|---|---|
| **Model panel** | 3-model consensus (R1→R2→R3) | **same** 3-model consensus (R1→R2→R3) |
| **Externalized learning** | mutate the **instruction prompt** (`v1.1→v1.2` + model-specific patches) | **same prompt mechanism, PLUS** an added **conventions subsystem** |
| **s10-only machinery** | — | `conventions.md` **C/D ledger** (atomic gate-PASS rules, prepended to every leg's R1/R2/R3 prompt) + the **scribe** (distils resolved gold → conventions) + **regression gate** (Trigger-1 write-path) + **D-deliberation** (escalation for genuinely ambiguous verses) |

Infrastructure/truth-source layer is shared bidirectionally (WLC tooling
[`wlc_check.py`](wlc_check.py)/`eval_gold_vs_wlc.py` + `FHL_DIVERGENCE_LOG` + trust
tiers + buckets flowed s10→s1; s10 reads s1's gold as baseline). What still
distinguishes s10 is therefore **purely the added conventions subsystem** — same panel,
same per-call blindness, same cost base. s10's bet (Q2): does that extra scribe+ledger+
gate machinery produce **better gold** and/or **fewer escalations over time** (H4
"cheaper over time"), earning its keep? Still only answered by a B-vs-B0 proxy — the
head-on **A-vs-B** contest below is unrun. That contest is the final exam for s10's
reason to exist.

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

#### ✅ Stage-1 empirical result (`build_exclusion.py`, 2026-06-25 — run BEFORE any paid contest)

Built and run; **the kept set is fair, confirmed.** Key design correction made
during the build: intersection must be on the **bare Strong's NUMBER**
(family-agnostic), NOT on (number+role) — in naked mode the model transfers a
bare number, so an `'A'`-augmented attached form `WAH1961` and a plain `WH1961`
are the *same* supplyable number. Keying identity on role falsely excluded ~74
shared numbers; fixed → number-level multiset `shared = min(unv, kjv)`.

| corpus | UNV tags | kept (shared) | excluded (UNV-only) | excl % | content-lemma excess |
|---|---|---|---|---|---|
| **Gen 1** | 592 | 409 | 183 | 30.9% | **0** |
| **Gen 2** | 443 | 323 | 120 | 27.1% | 2 (H5117 rest, H120 man) |
| **Gen 1–5** | 2438 | 1819 | 619 | 25.4% | 7 (1.1%) |

The family profile is **stable across chapters** (ch1: prefix_09 62 / obj 23 / morph 24
/ core_func 74; ch2: prefix_09 36 / obj 13 / morph 5 / core_func 64) — same four
structural classes dominate, so the kept-set methodology generalises verse-to-verse.

Excluded-family distribution (Gen 1): `prefix_09` 62 · `obj_marker` (את 853) 23 ·
`morph` (UNV-only 8xxx codes) 24 · `core_function` 74 · **`core_content` 0**.

**Finding — the exclusion is broader than "just 09xxx", and that is the point.**
FHL's KJV annotation is *sparser* than UNV's because English structurally drops
Hebrew function words. Verified by hand: 1:3 UNV tags היה(1961) twice
(要有/就有了) but KJV tags "Let there be" once and leaves "and there was light"
**untagged**; 1:13 "有晚上有早晨"=1961×2 vs KJV "were" tagged **zero** (its own
footnote admits "Heb. …was, …was"); 1:31 一切=כל(3605) vs KJV "every thing"
untagged. So the excluded set = `{09xxx prefixes} ∪ {את} ∪ {UNV-only morph} ∪
{English-dropped function words: היה/כל/על/בין/אשר/הנה/מן/כן/כי/מה/שם/…}`.

**Fairness is by construction**: `shared = min(unv, kjv)` per number ⇒ every
KJV-supplyable instance is kept; `excluded` is strictly UNV's *excess*, which the
KJV source genuinely lacks (whether a function word or one extra count of a
content lemma like a repeated 神/上帝 where English used a pronoun). Gen 1 has
**zero** content-lemma excess; Gen 1–5 has 7 (LORD/God/Adam/man/rest/lift, all
count-mismatch). → **kept_set is a fair placement answer key for the contest.**

Artifacts: `kept_set_gen1-5.json` (per-verse kept + excluded-by-family for the
138-verse corpus); `score_placement(model_output, shared)` scores number presence
on the kept set (true *positional* placement defers to `survey4/auto_score.py`).

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

#### 🟢 Stage-2 feasibility CONFIRMED (data inspected 2026-06-25 — NOT yet built)

`Alignments/data/sources/WLC.tsv` exists and carries every column the harsh test
needs: `id · altId · text · strongs · gloss · gloss2 · lemma · pos · morph`. Gen
1:1 verified row-by-row:
- Inseparable prefixes are **separate tokens** with augmented numbering —
  `בְּ`=`H0871a`(prep), `הַ`=`H1886a`(art), `וְ`=`H2050b`(cj) — and **empty
  `gloss2`** (no Chinese gloss, since they aren't standalone Chinese words). So the
  bridge is **by lemma** (בְּ/הַ/וְ/כְּ/לְ/מִן/שֶׁ → FHL 09xxx), NOT by number —
  confirms the scheme-correction above.
- `אֵת`=`H0853` matches FHL `0853` directly (no bridge).
- `gloss2` leak is real (起初/创造/神/诸天/与/地) → **strip `gloss2`** for the
  no-hint test; `pos`/`morph` are safe non-leaking signal to keep.

Remaining build (when greenlit — this is the **paid** arm, do AFTER ch2/contest):
1. derive the FHL-09xxx ↔ prefix-lemma map empirically (cross-ref UNV 09xxx
   positions against WLC lemmas) — a ~7-entry fixed table;
2. WLC source loader (Hebrew text + strongs→FHL-normalized + pos + morph, gloss2
   dropped); 3. score on the FULL set incl. 09xxx via the kept_set's complement.

### ⚖️ WLC answer key — methodology-divergence rule (s1 gold ruling, 2026-06-29)

When WLC is used to validate/score gold (`eval_gold_vs_wlc.py`), some FHL-faithful
tags legitimately differ from WLC original-language morphology — these are
**methodology divergences, NOT gold errors**, and the WLC key must NOT penalise
them (else it wrongly punishes FHL-faithful gold and skews the s1-vs-s10 contest).

- **Canonical list**: `../survey1_prompt_evolving/FHL_DIVERGENCE_LOG.md` (s1 is the
  gold authority; the gold is FHL-faithful — it *transfers* FHL's SN, it does not
  *correct* FHL with WLC). `eval_gold_vs_wlc.py` reads this log and buckets matches
  as `methodology_divergence`, excluded from the error count.
- **Ruled example — D1 / Gen 2:20** 2nd אדם: gold `H0120` ("the man", matches 那人)
  vs WLC `H0121` ("Adam"). Article-less `וּלְאָדָם` + KJV/ESV/NIV "Adam" make WLC's
  reading sound, but the Chinese 那人 anchors H0120 → **keep H0120**, log as
  divergence + FHL-feedback candidate.
- **Whole-gold WLC check (Gen 1–2, 56 verses)**: 982/986 SN-inventory-consistent
  (lexical + 09xxx prefix + s5 morph bridge); after excluding the 1 ruled
  divergence, residual gold-only = an FHL `<WH00>` artifact + a verb-doubling
  count + an את-companion 854/853 nuance — **zero hallucinated content words**.

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

## ▶ First contest result — B vs B0 (conventions isolation), Gen 1–2, opus (2026-06-26)

Ran `run_a2_contest.py` (the first cut: same single-pass opus annotates each verse
twice, conventions ON vs OFF; full Arm A = s1 consensus is a later layer). Harness
validated; two bugs fixed first — raw `claude -p` inherits this repo's CLAUDE.md
and drifts into project-assistant meta-chatter ("Recorded to prompt.history…") →
routed through `cli_caller.call_llm` **structured output** (forces clean `{unv_sn}`);
and `clean_output` now picks the tag-bearing line with the most CJK chars (avoids
grabbing an echoed C1-example line).

| arm | placement* | coverage* | **kept_place** |
|---|---|---|---|
| **B** (conv ON) | 0.7274 | 0.6524 | **0.9971** |
| **B0** (conv OFF) | 0.7284 | 0.6555 | **0.9914** |
| **Δ (B − B0)** | −0.0011 | −0.0031 | **+0.0058** |

\* `auto_score.placement`/`coverage` are noisy here (position-shift artifacts from
KJV-unsupplyable prefixes shifting char offsets); **`kept_place`** (Stage-1 kept-set
number coverage) is the trustworthy metric.

**Aggregate is tiny but directionally positive; the signal lives in the hard
verses.** 50/56 verses are at the kept-place ceiling (~1.0) for BOTH arms — opus
already nails the KJV-supplyable numbers, so conventions have nothing to fix there.
On the **6 verses where B0 actually erred**, B helped 5:1 — full fixes on 1:6
(9/10→10/10), 1:17 (7/8→8/8), 1:24 (13/14→14/14), 2:5 (20/21→21/21); partial on
1:11 (18/20→19/20); tie on 1:28; one regression (1:4). Net +4 kept tags.

**Honest caveats / what this dictates next:**
1. **Ceiling**: opus on easy Genesis can't discriminate. Use a **weaker model**
   (more headroom) or **focus on hard verses** to see convention value.
2. **Sampling noise**: 1 sample/arm/verse + a stochastic model means the 5:1 fix
   ratio is confounded (a fresh re-run of 1:17 fixed a *different* tag, 0430, not
   the C1 morph pattern). A rigorous number needs **N samples/verse/arm** (or
   low-temp) to separate convention-effect from sampling variance.
3. **One narrow rule**: with only C1 in `conventions.md`, the achievable Δ is
   small by construction. Effect should compound as the scribe adds gated rules.

→ **Verdict so far: H5 directionally supported (conventions help where the model
errs, ~zero cost where it doesn't), not yet significant.** The B-vs-B0 design is
sound but ceiling+noise-limited on opus/Genesis; harden with multi-sample or a
weaker model before treating the number as decisive.

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
