# Survey5 Leaderboard — model × prompt benchmark design

Date: 2026-07-10 · survey5_bilingual_sn_benchmark-obe · Status: **approved, pre-plan**

## Goal

Turn survey5's ground-truth SN-placement task into a **benchmark leaderboard**: measure
which **model** and which **prompt** is best at turning plain UNV into UNV+SN, scored
automatically against FHL UNV+SN gold. One general matrix runner; a full grid, two
sweeps, or a single axis are all just different invocations of it.

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
`run_leaderboard.py` that takes a list of models and a list of prompts and runs the
Cartesian product over the fixed verse set. The three usage shapes become argument lists:

| Shape | Invocation |
|---|---|
| Full grid (models × prompts, interaction visible) | `--models a,b,c --prompts p1,p2,p3` |
| Two sweeps (rank models @ fixed prompt, then prompts @ fixed model) | two runs, each fixing one axis |
| Single axis | one list has one element |

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

## Components

| File | Role | New / reuse |
|---|---|---|
| `run_leaderboard.py` | Matrix driver: loop `(model, prompt)` cells over the fixed OT set; per-cell disk cache + resume; emit leaderboard | **new** |
| `run_iteration_set.py` | Per-cell executor (one model × one prompt × verse set) | reuse, upgraded |
| `iteration_set_52.json` | Frozen benchmark set (OT subset selected at runtime) | reuse |
| `prompts/*.md` | Prompt contestants | reuse |
| `scoring.py` / `gate.py` / `morph.py` | Round-2 scoring + deterministic morph attach | reuse |
| `wlc_bridge.py` | WLC source builder | reuse |
| leaderboard aggregation (a function inside `run_leaderboard.py`) | Aggregate per-cell scores → ranked table (sort by headline metric) + per-dimension breakdown → JSON + markdown. Kept in the runner for v1 (YAGNI a separate file) | **new** |

### Per-cell upgrades to `run_iteration_set.py`
1. **Scoring**: replace bare `score_verse(output, unv_sn)` with the Round-2 path —
   `scoring.num_score` for headline cov/place, plus `attach_morph` + `gate.morph_recall`
   for the separate morph column.
2. **Isolated cwd**: model-under-test must run in an empty temp cwd
   (`call_claude_isolated` pattern) so it does not inherit this repo's `CLAUDE.md` +
   `/ph` `/logoutput` skills + hooks (the Round-2 contamination bug). Any subprocess LLM
   call from this repo dir must use an isolated cwd.

## Data flow

```
models × prompts matrix
  └ per cell (model, prompt):
      for each verse in OT subset of iteration_set_52:
          build prompt (source = WLC+SN)  ->  call model (ISOLATED cwd)
          -> attach_morph() (deterministic constant)
          -> score vs FHL UNV+SN gold  (num_score cov/place ; morph_recall separate)
      aggregate cell: mean cov, mean place (headline) ; morph% (separate) ; per-dim
  -> leaderboard: sort cells by headline metric
     + per-dimension breakdown (which cell wins which of the 26 dims)
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

## Error handling

- **Empty / failed model output** — skip the verse in that cell (as `run_bakeoff` does),
  log it; a cell with too many empties is flagged, not silently averaged.
- **Isolated cwd** — mandatory for subprocess LLM calls (see per-cell upgrade #2).
- **NT verse in set** — filtered out at load (v1 OT-only); no WLC lookup attempted.
- **Cache invalidation** — cell cache keyed by `(model, prompt-file-hash, iter-set-hash)`
  so editing a prompt or the verse set invalidates only affected cells.

## Testing

- **Unit** — leaderboard aggregation/ranking on synthetic per-cell scores (deterministic,
  no LLM): correct sort order, per-dimension winner selection, morph-excluded-from-rank.
- **Smoke** — one tiny cell (1 model × 1 prompt × 2 OT verses) end-to-end, asserting a
  score row and a cache file are produced.

## Out of scope (v1)

- **NT / Greek** — SBLGNT source + Greek morph bridge (`WTG` 5xxx). Separate build.
- **Multi-model consensus / debate** — survey5 has ground truth; the leaderboard ranks,
  it does not arbitrate. (Consensus is survey1's job.)
- **Input-source axis** — WLC-only is locked (Round-2). Source is fixed, not a contestant.

## Status

Design approved 2026-07-10. Next: implementation plan (writing-plans).
