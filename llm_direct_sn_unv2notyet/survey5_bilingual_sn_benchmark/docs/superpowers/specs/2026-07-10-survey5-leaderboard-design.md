# Survey5 Leaderboard — model × prompt benchmark design

Date: 2026-07-10 · survey5_bilingual_sn_benchmark-obe · Status: **approved, pre-plan · §Third axis amendment: DRAFT**

## Goal

Turn survey5's ground-truth SN-placement task into a **benchmark leaderboard**: measure
which **model** and which **prompt** is best at turning plain UNV into UNV+SN, scored
automatically against FHL UNV+SN gold. One general matrix runner; a full grid, two
sweeps, or a single axis are all just different invocations of it. A third on/off
dimension — **± qp enrichment** (see §Third axis) — measures whether FHL parsing-code
evidence actually helps.

## Why this is cheap to build

survey5 already has most of the parts:

- **`iteration_set_52.json`** — a frozen benchmark set (26 survey4 dims × 2 = 52 verses),
  each verse dimension-labelled. Frozen ⇒ scores are comparable across contestants.
- **`run_iteration_set.py`** — already runs one `(model, prompt)` cell over the 52-set.
- **`prompts/`** — 5 prompt versions (`survey5_v0.1`..`v0.4`, `survey5_reverse_v0.1`).
- **Round-2 scoring** — `scoring.num_score` (format-agnostic), `morph.attach_morph`
  (deterministic morph layer), `gate.morph_recall` / `gate.tier_recall`.
- **`wlc_bridge.py`** — WLC (Hebrew original + SN) source builder.

The expansion is a **matrix runner + leaderboard aggregation** on top of these, plus two
upgrades to the per-cell path (Round-2 scoring; isolated-cwd model calls).

## Core architectural decision — one general matrix runner

Do **not** fork code for "full grid" vs "two sweeps" vs "single axis". Build one
`run_leaderboard.py` that takes a list of models, a list of prompts, and an
enrichment-arm list, and runs the Cartesian product over the fixed verse set. The usage
shapes become argument lists:

| Shape | Invocation |
|---|---|
| Full grid (models × prompts, interaction visible) | `--models a,b,c --prompts p1,p2,p3` |
| Two sweeps (rank models @ fixed prompt, then prompts @ fixed model) | two runs, each fixing one axis |
| Single axis | one list has one element |
| Enrichment A/B (paired cells, ± qp) | `--models a --prompts p1 --enrich off,qp` |

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

### ② v1 scopes to OT (WLC-only)
WLC is the Hebrew OT original; the Round-2-validated production source is WLC-only. The
52-verse set spans OT+NT. v1 therefore runs on the **OT subset** of the 52 verses (filter
by `testament == "OT"`), matching the validated method. NT (Greek source + Greek morph
bridge) is a separate future axis, out of scope here.

## Third axis — ± qp enrichment (amendment 2026-07-10)

Added per [`QP_ENRICHMENT_PLAN.md`](../../../../../parsing/QP_ENRICHMENT_PLAN.md) Item 4.
Conceptual root: [`PARSING_FOUNDATIONS.md`](../../../../../parsing/PARSING_FOUNDATIONS.md)
— FHL parsing (SN + parsing code) is upstream input; our task is alignment. This axis
tests whether feeding that upstream evidence to the model measurably improves alignment.

**The axis.** Same model × same prompt, two arms:

| Arm | Prompt content |
|---|---|
| `off` (default — today's path) | WLC+SN source + UNV plain, byte-identical to the current prompt |
| `qp` | + a per-verse **qp word-table**: one line per original word — `word / orig` (lemma) `/ sn / wform` (parsing code) `/ exp` (gloss) |

Recommended block format (extends survey6's enriched-dict format with `orig`):

```
qp word-table (original word order; annotation only — copy no tags from here):
  wid 1  בְּרֵאשִׁית  orig=רֵאשִׁית  WH07225  介系詞 בְּ + 名詞，陰性單數  起初、開始
  wid 2  בָּרָא      orig=בָּרָא    WH01254  動詞，Qal 完成式 3 單陽     Qal 創造…
```

This turns "does the parsing code actually help SN placement?" into a measurable
proposition, and **feeds Item 3's go/no-go**: the survey1 gold-pipeline qp A/B
([`survey1_prompt_evolving/QP_AB_DESIGN.md`](../../../../survey1_prompt_evolving/QP_AB_DESIGN.md),
created in the same change set) is expensive (3-model consensus, no ground truth);
this axis is the cheap, ground-truth-scored measurement that should run first.

### Prior: survey6 `--enrich-dict` (the hypothesis to retest)

survey6 already appended `exp`+`wform` to its SN:word dict
(`run_survey6.py --enrich-dict`). Verdict: single-pass 5-input **information overload —
placement +7pp but coverage −10pp**. Why a retest is justified:
- source is now **WLC-only** (no KJV competing channel — the main overload suspect);
- frozen 52-set + paired cells ⇒ controlled comparison, not anecdote;
- Round-2 scoring path with the morph guard below, not the survey6 scorer.
The prior is negative-leaning, so the arm defaults `off` and the burden of proof is on `qp`.

### Locked sub-decisions

1. **Enrichment is a cell dimension, not a new runner.** The matrix becomes
   `models × prompts × enrich`; `--enrich off,qp`, default `off`.
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
4. **One fixed enrichment format in v1** (the five-field block above). Which-fields
   ablations are out of scope.

### Reading the axis

The leaderboard gains an `enrich` column, plus a **paired-delta table**: for every
`(model, prompt)` present in both arms — Δcov, Δplace (headline), per-dimension deltas.

| Δcov | Δplace | Read as |
|---|---|---|
| ≥ 0 | > 0 | enrichment helps → Item 3's A/B qualified to proceed |
| > 0 | ≤ 0 | mixed signal (coverage up, placement not) → stays `off` pending investigation |
| < 0 | > 0 | survey6's overload pattern reproduced → stays `off` |
| ≈ 0 | ≈ 0 | parsing-code evidence redundant given WLC+SN → stays `off` |

Any outcome not matching the "helps" row defaults to staying `off`.

## Components

| File | Role | New / reuse |
|---|---|---|
| `run_leaderboard.py` | Matrix driver: loop `(model, prompt)` cells over the fixed OT set; per-cell disk cache + resume; emit leaderboard | **new** |
| `run_iteration_set.py` | Per-cell executor (one model × one prompt × verse set) | reuse, upgraded |
| `iteration_set_52.json` | Frozen benchmark set (OT subset selected at runtime) | reuse |
| `prompts/*.md` | Prompt contestants | reuse |
| `scoring.py` / `gate.py` / `morph.py` | Round-2 scoring + deterministic morph attach | reuse |
| `wlc_bridge.py` | WLC source builder | reuse |
| `build_qp_snapshot.py` | One-time qp word-table snapshot builder (qp.php + `bible_parsing.db` fallback for numbered books) | **new** (±enrich axis) |
| `qp_snapshot_52.json` | Frozen per-verse qp word-tables (wid/word/orig/pro/sn/wform/exp) for the OT subset | **new** (±enrich axis) |
| leaderboard aggregation (a function inside `run_leaderboard.py`) | Aggregate per-cell scores → ranked table (sort by headline metric) + per-dimension breakdown → JSON + markdown. Kept in the runner for v1 (YAGNI a separate file) | **new** |

### Per-cell upgrades to `run_iteration_set.py`
1. **Scoring**: replace bare `score_verse(output, unv_sn)` with the Round-2 path —
   `scoring.num_score` for headline cov/place, plus `attach_morph` + `gate.morph_recall`
   for the separate morph column.
2. **Isolated cwd**: model-under-test must run in an empty temp cwd
   (`call_claude_isolated` pattern) so it does not inherit this repo's `CLAUDE.md` +
   `/ph` `/logoutput` skills + hooks (the Round-2 contamination bug). Any subprocess LLM
   call from this repo dir must use an isolated cwd.
3. **`--enrich` flag** (default `off`): with `qp`, the prompt builder appends the
   verse's qp word-table block from `qp_snapshot_52.json`; with `off`, the prompt is
   byte-identical to today's. See §Third axis.

## Data flow

```
models × prompts × enrich matrix
  └ per cell (model, prompt, enrich):
      for each verse in OT subset of iteration_set_52:
          build prompt (source = WLC+SN [+ qp word-table if enrich=qp])
          ->  call model (ISOLATED cwd)
          -> strip morph-range tags from raw output (headline guard, both arms)
          -> attach_morph() (deterministic constant)
          -> score vs FHL UNV+SN gold  (num_score cov/place ; morph_recall separate)
      aggregate cell: mean cov, mean place (headline) ; morph% (separate) ; per-dim
  -> leaderboard: sort cells by headline metric
     + per-dimension breakdown (which cell wins which of the 26 dims)
     + paired ±enrich delta table (Δcov/Δplace per (model, prompt) pair)
  -> write JSON + markdown report under run_logs/
```

## Cost / quota

A grid is `models × prompts × verses` calls. Mitigations:
- **Per-cell disk cache + resume** — a completed cell is never re-run; re-ranking is free.
- **Start small** — a short models list × the 5 prompts × OT subset (~fewer than 52).
- **Local models are free** — ollama (qwen / deepseek) for wide sweeps; reserve cloud
  (opus/sonnet/gemini) for the headline comparison.
- **Cloud pausing** — reuse the existing colleague-token-reservation / quota-pause logic
  for cloud models on shared accounts.
- **Enrichment arm is opt-in** — `--enrich` defaults to `off`; the `qp` arm doubles
  only explicitly requested cells. Run it on a shortlist (headline models × best
  prompt), never the full grid.

## Error handling

- **Empty / failed model output** — skip the verse in that cell (as `run_bakeoff` does),
  log it; a cell with too many empties is flagged, not silently averaged.
- **Isolated cwd** — mandatory for subprocess LLM calls (see per-cell upgrade #2).
- **NT verse in set** — filtered out at load (v1 OT-only); no WLC lookup attempted.
- **Cache invalidation** — cell cache keyed by
  `(model, prompt-file-hash, iter-set-hash, enrich, qp-snapshot-hash)` — where
  `qp-snapshot-hash` participates only when `enrich=qp` (constant empty string for
  `enrich=off`) — so editing a prompt, the verse set, or the qp snapshot invalidates
  only affected cells (regenerating the snapshot never invalidates `off` cells).
- **Verse missing from qp snapshot (`qp` arm)** — skip + log (same policy as empty
  model output); never silently fall back to the un-enriched prompt inside a `qp` cell.
- **qp snapshot build failure** — `build_qp_snapshot.py` fails loudly at build time;
  benchmark runs never fetch qp.php live.

## Testing

- **Unit** — leaderboard aggregation/ranking on synthetic per-cell scores (deterministic,
  no LLM): correct sort order, per-dimension winner selection, morph-excluded-from-rank,
  paired ±enrich delta computation. Prompt builder: `enrich=off` byte-identical to the
  current prompt; `enrich=qp` contains the verse's qp block. Morph guard: a raw output
  containing `<WTH8804>` scores identically to the same output without it.
- **Smoke** — one tiny cell (1 model × 1 prompt × 2 OT verses) end-to-end, asserting a
  score row and a cache file are produced.

## Out of scope (v1)

- **NT / Greek** — SBLGNT source + Greek morph bridge (`WTG` 5xxx). Separate build.
- **Multi-model consensus / debate** — survey5 has ground truth; the leaderboard ranks,
  it does not arbitrate. (Consensus is survey1's job.)
- **Input-source axis** — WLC-only is locked (Round-2). Source is fixed, not a contestant.
- **Enrichment field ablations** — which qp fields carry the signal (orig-only /
  exp-only / wform-only) is follow-up work; v1 ships one fixed five-field format.

## Status

Design approved 2026-07-10. Next: implementation plan (writing-plans).

Amended 2026-07-10: third axis **± qp enrichment** added per
[`QP_ENRICHMENT_PLAN.md`](../../../../../parsing/QP_ENRICHMENT_PLAN.md) Item 4 —
spec only, no runner changes yet. Amendment status: DRAFT, pending design review.
