# Survey5 Leaderboard — model × prompt benchmark design

Date: 2026-07-10 (amended 2026-07-18) · survey5_bilingual_sn_benchmark-obe ·
Status: **approved — v1 scope locked; ±qp deferred to v1.1**

## Goal

Turn survey5's ground-truth SN-placement task into a **benchmark leaderboard**: measure
which **model** and which **prompt** is best at turning plain UNV into UNV+SN, scored
automatically against FHL UNV+SN gold. One general matrix runner; a full grid, two
sweeps, or a single axis are all just different invocations of it.

**v1** ships two things: the **model × prompt** leaderboard, and a **one-off bridge
ablation** (`wlc` vs `wlc+bsb` vs `wlc+ylt`, see §Bridge ablation) that settles — with a
same-run, no-baseline-drift comparison — whether an English bridge helps. The bridge
ablation is **load-bearing**: its YLT verdict feeds survey10's A2 source decision.

**v1.1** adds the **± qp enrichment** dimension (see §Deferred to v1.1) — whether feeding
FHL parsing-code evidence measurably improves alignment.

## Why this is cheap to build

survey5 already has most of the parts:

- **`iteration_set_52.json`** — a frozen benchmark set (26 survey4 dims × 2 = 52 verses),
  each verse dimension-labelled. Frozen ⇒ scores are comparable across contestants.
- **`run_iteration_set.py`** — already runs one `(model, prompt)` cell over the 52-set.
- **`prompts/`** — 5 prompt versions (`survey5_v0.1`..`v0.4`, `survey5_reverse_v0.1`).
  ⚠️ These are **KJV→UNV** specific (KJV tags as ground truth). v1 chose option **B**:
  **author a fresh WLC-ready prompt set** (`prompts/survey5_wlc_*.md`); the KJV prompts
  are not used as-is.
- **Round-2 scoring** — `scoring.num_score` (format-agnostic), `morph.attach_morph`
  (deterministic morph layer), `gate.morph_recall` / `gate.tier_recall`.
- **`wlc_bridge.py`** — WLC (Hebrew original + SN) source builder.
- **Clear Bible alignment data** (`Alignments/data/eng/`) — `alignments/YLT/WLC-YLT-manual.json`
  (437k WLC-morpheme→YLT-word records), `targets/YLT/ot_YLT.tsv`, and the BSB equivalents.
  ⚠️ Correction (2026-07-18): survey10's `ylt_bridge.py` referenced in an earlier draft
  **does not exist on disk** — the bridge gloss builder (`bridge_gloss.py`) is authored
  locally in v1 from this alignment data.

The expansion is a **matrix runner + leaderboard aggregation** on top of these, plus two
upgrades to the per-cell path (Round-2 scoring; isolated-cwd model calls).

## Core architectural decision — one general matrix runner

Do **not** fork code for "full grid" vs "two sweeps" vs "single axis" vs "bridge ablation"
vs "±qp". Build one `run_leaderboard.py` that takes a list of models, a list of prompts,
and a list of **arms**, and runs the Cartesian product over the fixed verse set. An **arm**
is a prompt-composition recipe — *what extra material rides in the prompt beyond WLC+SN*.
Everything is one mechanism:

| Shape | Invocation |
|---|---|
| Full grid (models × prompts, interaction visible) | `--models a,b,c --prompts p1,p2,p3` |
| Two sweeps (rank models @ fixed prompt, then prompts @ fixed model) | two runs, each fixing one axis |
| Single axis | one list has one element |
| **Bridge ablation (v1, paired)** | `--models a --prompts p1 --arms wlc,wlc+bsb,wlc+ylt` |
| **± qp enrichment (v1.1, paired)** | `--models a --prompts p1 --arms wlc,wlc+qp` |

Default `--arms wlc` (the locked production source). Every non-`wlc` arm is opt-in and
paired against `wlc` in the delta table.

## Two locked decisions

### ① Ranking metric excludes the deterministic morph layer
`attach_morph()` is deterministic post-processing — the **same free points for every
contestant**. Including morph in the ranking metric inflates all cells equally and dilutes
the discriminating signal. So:

- **Headline / ranking metric = what the model actually controls**: lexical + 09xxx
  placement, i.e. `coverage` and `placement` from `scoring.num_score` computed on the
  model's **raw output, before `attach_morph()`** — so the free morph tags are physically
  absent from the headline number.
- **Morph recall is a separate column**, computed via `gate.morph_recall` on the output
  **after `attach_morph()`**, a near-constant across cells — reported for completeness,
  never a ranking input.

### ② v1 scopes to OT (WLC-only default source)
WLC is the Hebrew OT original; the Round-2-validated production source is WLC-only. The
52-verse set spans OT+NT. v1 therefore runs on the **OT subset** of the 52 verses (filter
by `testament == "OT"`), matching the validated method. NT (Greek source + Greek morph
bridge) is a separate future axis, out of scope here. (The bridge ablation adds *optional*
English glosses on top of the WLC source; it does not change the default, which stays
WLC-only.)

## Bridge ablation — v1, one-off, feeds survey10

**Why.** survey10's A2 Gen1 test found WLC-only strongest (full 0.797 / 09xxx 0.984), BSB
bridge harmful (Δ−0.023), but **YLT undetermined** — YLT looked +0.039 in its own run,
against a drifted baseline, so WLC-only-vs-YLT is not settled. survey5 can settle it: the
frozen 52-set + a single run + FHL ground truth gives a **same-run, no-baseline-drift**
comparison that survey10's single-run setup cannot. survey10 accepted (2026-07-18); if
same-run YLT still beats WLC-only, survey10 reconsiders switching A2's bridge back to YLT.

**The arms** (same model × same prompt, paired cells over the OT subset):

| Arm | Prompt content |
|---|---|
| `wlc` (default) | WLC+SN source + UNV plain — the locked production source |
| `wlc+bsb` | + BSB English gloss bridge (readable, natural word order) |
| `wlc+ylt` | + YLT literal English gloss bridge (tracks Hebrew morphology closely) |

**Data.** A local `bridge_gloss.py` (authored in v1) builds per-Hebrew-word English
glosses from the Clear Bible alignment: for each WLC token id, look up its aligned target
word-ids in `WLC-YLT-manual.json` (`records`: `source`=WLC ids, `target`=YLT ids) and join
the text from `ot_YLT.tsv`. YLT aligns directly to our `WLC.tsv` ids (clean); BSB uses
WLCM source ids in `WLCM-BSB-manual.json`, needing a WLC↔WLCM id reconciliation (secondary,
since BSB is the expected-harmful arm and YLT is the load-bearing question). Glosses are
frozen to `bridge_snapshot_52.json`; benchmark runs never read the alignment live.

**Scoring.** Identical to the leaderboard headline — `scoring.num_score` cov/place on raw
output (pre-`attach_morph`), morph column separate. A **paired-delta table** reports, per
`(model, prompt)`: Δcov / Δplace of `wlc+bsb − wlc` and `wlc+ylt − wlc`, plus per-dimension
deltas.

**Prior & burden of proof.** Round-2 (WLC-only > WLC+KJV) and survey10's A2 both lean
WLC-only. So `wlc` is the default and the burden is on the bridge; BSB is expected harmful,
YLT is the open question this ablation exists to close.

**Reading → report back to survey10.**

| YLT result (same-run, vs `wlc`) | Action |
|---|---|
| Δ ≤ 0 | WLC-only confirmed universally; English bridge stays retired everywhere |
| Δ > 0 (robust across cells) | report to survey10 → they reconsider A2 bridge = YLT |

**Scope.** This is a **one-off ablation, not a permanent source axis.** After the verdict,
the production default stays WLC-only and the English bridge stays retired. Run it on a
shortlist (headline models × best prompt), never the full grid.

## Deferred to v1.1 — ± qp enrichment

*(Content below is retained from the 2026-07-10 amendment; re-scoped from v1 to v1.1 on
2026-07-18. The `off`/`qp` arms map onto the unified `--arms wlc` / `wlc+qp`.)*

Added per [`QP_ENRICHMENT_PLAN.md`](../../../../../parsing/QP_ENRICHMENT_PLAN.md) Item 4.
Conceptual root: [`PARSING_FOUNDATIONS.md`](../../../../../parsing/PARSING_FOUNDATIONS.md)
— FHL parsing (SN + parsing code) is upstream input; our task is alignment. This axis
tests whether feeding that upstream evidence to the model measurably improves alignment.

**The axis.** Same model × same prompt, two arms:

| Arm | Prompt content |
|---|---|
| `wlc` (default — today's path) | WLC+SN source + UNV plain, byte-identical to the current prompt |
| `wlc+qp` | + a per-verse **qp word-table**: one line per original word — `word / orig` (lemma) `/ sn / wform` (parsing code) `/ exp` (gloss) |

Recommended block format (extends survey6's enriched-dict format with `orig`):

```
qp word-table (original word order; annotation only — copy no tags from here):
  wid 1  בְּרֵאשִׁית  orig=רֵאשִׁית  WH07225  介系詞 בְּ + 名詞，陰性單數  起初、開始
  wid 2  בָּרָא      orig=בָּרָא    WH01254  動詞，Qal 完成式 3 單陽     Qal 創造…
```

This turns "does the parsing code actually help SN placement?" into a measurable
proposition, and **feeds Item 3's go/no-go**: the survey1 gold-pipeline qp A/B
([`survey1_prompt_evolving/QP_AB_DESIGN.md`](../../../../survey1_prompt_evolving/QP_AB_DESIGN.md))
is expensive (3-model consensus, no ground truth); this axis is the cheap,
ground-truth-scored measurement that should run first.

### Prior: survey6 `--enrich-dict` (the hypothesis to retest)

survey6 already appended `exp`+`wform` to its SN:word dict
(`run_survey6.py --enrich-dict`). Verdict: single-pass 5-input **information overload —
placement +7pp but coverage −10pp**. Why a retest is justified:
- source is now **WLC-only** (no KJV competing channel — the main overload suspect);
- frozen 52-set + paired cells ⇒ controlled comparison, not anecdote;
- Round-2 scoring path with the morph guard below, not the survey6 scorer.
The prior is negative-leaning, so the arm defaults to `wlc` and the burden of proof is on `wlc+qp`.

### Locked sub-decisions (v1.1)

1. **Enrichment is an arm, not a new runner.** `--arms wlc,wlc+qp`; default `wlc`.
2. **Headline metric unchanged; morph guard added (decision ① stays intact).** The qp
   table leaks `wform`, so an enriched model may start emitting morph tags itself. To
   keep arms comparable, the headline scorer **strips morph-range tags (canonical
   H8675–H8999, i.e. `WTH*` after `normalize_tags` drops the `T`) from the model's raw
   output in BOTH arms** before `num_score`. `attach_morph()` then runs on the stripped
   output, so the morph column remains the deterministic constant of decision ①.
   (Implementation-plan note: stripping the same range from the gold side of
   `num_score` would make headline absolutes cleaner too — optional; it affects neither
   deltas nor rankings.)
3. **qp data is frozen, like the verse set.** A one-time `build_qp_snapshot.py` writes
   `qp_snapshot_52.json` for the OT subset — via `qp.php` (skip `wid=0`,
   `normalize_qp_sn`; survey6's `fetch_qp_verse` pattern, extended to also preserve
   `orig`/`pro`), with the local `bible_parsing.db` (`lparsing` table) fallback for the
   numbered books qp.php cannot serve (the OT subset contains 2Sam ×4, 1Chr ×3,
   2Chr ×3). The local table carries all five fields
   (`word/sn/pro/wform/orig/exp` — verified), so there is no field asymmetry.
   Benchmark runs never fetch qp live.
4. **One fixed enrichment format in v1.1** (the five-field block above). Which-fields
   ablations are out of scope.

### Reading the axis

The leaderboard gains a `wlc+qp` arm, plus a **paired-delta table**: for every
`(model, prompt)` present in both arms — Δcov, Δplace (headline), per-dimension deltas.

| Δcov | Δplace | Read as |
|---|---|---|
| ≥ 0 | > 0 | enrichment helps → Item 3's A/B qualified to proceed |
| > 0 | ≤ 0 | mixed signal (coverage up, placement not) → stays `wlc` pending investigation |
| < 0 | > 0 | survey6's overload pattern reproduced → stays `wlc` |
| ≈ 0 | ≈ 0 | parsing-code evidence redundant given WLC+SN → stays `wlc` |

Any outcome not matching the "helps" row defaults to staying `wlc`.

## Components

| File | Role | New / reuse |
|---|---|---|
| `run_leaderboard.py` | Matrix driver: loop `(model, prompt, arm)` cells over the fixed OT set; per-cell disk cache + resume; emit leaderboard + paired-delta tables | **new** |
| `run_iteration_set.py` | Per-cell executor (one model × one prompt × arm × verse set) | reuse, upgraded |
| `iteration_set_52.json` | Frozen benchmark set (OT subset selected at runtime) | reuse |
| `prompts/*.md` | Prompt contestants | reuse |
| `scoring.py` / `gate.py` / `morph.py` | Round-2 scoring + deterministic morph attach | reuse |
| `wlc_bridge.py` | WLC source builder | reuse |
| `bridge_gloss.py` | YLT (and BSB) English gloss builder from Clear Bible alignment data | **new (v1, bridge ablation)** |
| `prompts/survey5_wlc_*.md` | WLC-ready prompt contestants (authored in v1 — option B) | **new (v1, prompt axis)** |
| `bridge_snapshot_52.json` | Frozen per-verse BSB/YLT glosses for the OT subset (if freezing is needed) | **new (v1, bridge ablation)** |
| `build_qp_snapshot.py` | One-time qp word-table snapshot builder | **new (v1.1, ±qp)** |
| `qp_snapshot_52.json` | Frozen per-verse qp word-tables | **new (v1.1, ±qp)** |
| leaderboard aggregation (a function inside `run_leaderboard.py`) | Aggregate per-cell scores → ranked table + per-dimension breakdown + paired-delta tables → JSON + markdown. Kept in the runner for v1 (YAGNI a separate file) | **new** |

### Per-cell upgrades to `run_iteration_set.py`
1. **Scoring**: replace bare `score_verse(output, unv_sn)` with the Round-2 path —
   `scoring.num_score` for headline cov/place, plus `attach_morph` + `gate.morph_recall`
   for the separate morph column.
2. **Isolated cwd**: model-under-test must run in an empty temp cwd
   (`call_claude_isolated` pattern) so it does not inherit this repo's `CLAUDE.md` +
   `/ph` `/logoutput` skills + hooks (the Round-2 contamination bug). Any subprocess LLM
   call from this repo dir must use an isolated cwd.
3. **`--arms` flag** (default `wlc`): the prompt builder composes the arm's extra material
   — `wlc` = WLC+SN only (byte-identical to today); `wlc+bsb`/`wlc+ylt` = append the
   English gloss bridge (v1); `wlc+qp` = append the qp word-table (v1.1).

## Data flow

```
models × prompts × arms matrix
  └ per cell (model, prompt, arm):
      for each verse in OT subset of iteration_set_52:
          build prompt (WLC+SN [+ BSB/YLT gloss if arm=wlc+bsb/wlc+ylt]
                                [+ qp word-table if arm=wlc+qp])
          ->  call model (ISOLATED cwd)
          -> strip morph-range tags from raw output (headline guard, all arms)
          -> attach_morph() (deterministic constant)
          -> score vs FHL UNV+SN gold  (num_score cov/place ; morph_recall separate)
      aggregate cell: mean cov, mean place (headline) ; morph% (separate) ; per-dim
  -> leaderboard: sort cells by headline metric
     + per-dimension breakdown (which cell wins which of the 26 dims)
     + paired-arm delta tables (Δcov/Δplace of each non-wlc arm vs wlc, per (model,prompt))
  -> write JSON + markdown report under run_logs/
```

## Cost / quota

A grid is `models × prompts × arms × verses` calls. Mitigations:
- **Per-cell disk cache + resume** — a completed cell is never re-run; re-ranking is free.
- **Start small** — a short models list × the 5 prompts × OT subset (~fewer than 52).
- **Local models are free** — ollama (qwen / deepseek) for wide sweeps; reserve cloud
  (opus/sonnet/gemini) for the headline comparison.
- **Cloud pausing** — reuse the existing colleague-token-reservation / quota-pause logic.
- **Non-`wlc` arms are opt-in** — the bridge ablation (and later ±qp) doubles/triples only
  explicitly requested cells; run on a shortlist (headline models × best prompt), never
  the full grid.

## Error handling

- **Empty / failed model output** — skip the verse in that cell (as `run_bakeoff` does),
  log it; a cell with too many empties is flagged, not silently averaged.
- **Isolated cwd** — mandatory for subprocess LLM calls (see per-cell upgrade #2).
- **NT verse in set** — filtered out at load (v1 OT-only); no WLC lookup attempted.
- **Cache invalidation** — cell cache keyed by
  `(model, prompt-file-hash, iter-set-hash, arm, arm-data-hash)` — where `arm-data-hash`
  is the bridge/qp snapshot hash for non-`wlc` arms (constant empty string for `wlc`) —
  so editing a prompt, the verse set, or an arm's snapshot invalidates only affected cells
  (regenerating a snapshot never invalidates `wlc` cells).
- **Verse missing from an arm's snapshot** — skip + log (same policy as empty model
  output); never silently fall back to the `wlc` prompt inside a non-`wlc` cell.
- **Snapshot build failure** — snapshot builders fail loudly at build time; benchmark runs
  never fetch bridge/qp data live.

## Testing

- **Unit** — leaderboard aggregation/ranking on synthetic per-cell scores (deterministic,
  no LLM): correct sort order, per-dimension winner selection, morph-excluded-from-rank,
  paired-arm delta computation. Prompt builder: `wlc` byte-identical to the current prompt;
  `wlc+ylt`/`wlc+bsb` contain the verse's gloss; (`wlc+qp` in v1.1) contains the qp block.
  Morph guard: a raw output containing `<WTH8804>` scores identically to the same output
  without it.
- **Smoke** — one tiny cell (1 model × 1 prompt × 2 OT verses) end-to-end, asserting a
  score row and a cache file are produced; one paired bridge-ablation cell produces a
  delta row.

## Out of scope

- **NT / Greek** — SBLGNT source + Greek morph bridge (`WTG` 5xxx). Separate build.
- **Multi-model consensus / debate** — survey5 has ground truth; the leaderboard ranks,
  it does not arbitrate. (Consensus is survey1's job.)
- **Permanent English-bridge source axis** — the bridge ablation is a **one-off** to settle
  survey10's YLT question; production default stays WLC-only, bridge stays retired.
- **± qp enrichment** — deferred to **v1.1** (not out of scope, just later).
- **Enrichment field ablations** — which qp fields carry the signal (orig-only / exp-only /
  wform-only) is follow-up work; v1.1 ships one fixed five-field format.

## Status

- **v1 scope locked 2026-07-18**: model × prompt leaderboard + one-off bridge ablation
  (`wlc`/`wlc+bsb`/`wlc+ylt`, feeds survey10's A2 YLT decision).
- **v1.1**: ± qp enrichment (`wlc+qp`).
- Next: implementation plan (writing-plans) for v1.

### Amendment log
- 2026-07-10: third axis ± qp enrichment added (per QP_ENRICHMENT_PLAN Item 4).
- 2026-07-18: v1 scope locked to model×prompt + bridge ablation; ± qp deferred to v1.1;
  `off`/`qp` unified under `--arms wlc`/`wlc+qp`; bridge ablation added as load-bearing
  one-off feeding survey10 (accepted by survey10-obe via inject 2026-07-18).
