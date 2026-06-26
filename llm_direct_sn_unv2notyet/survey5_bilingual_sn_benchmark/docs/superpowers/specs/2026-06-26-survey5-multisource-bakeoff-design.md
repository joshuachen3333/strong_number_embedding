# Survey5 v2 — Multi-source SN-transfer bake-off (design)

Date: 2026-06-26 · Author: survey5_bilingual_sn_benchmark-obe
Status: **draft, pending Joshua review**

## 1. Context & purpose

Survey5 tests cross-lingual SN placement: give a model a source text **already tagged
with Strong's Numbers**, have it place those tags onto plain **UNV** Chinese, and
auto-score the result against FHL's **UNV+SN** (ground truth).

Original survey5 used **KJV+SN** (English, FHL) as the only source. s10-obe proved KJV
is **lossy**: on Gen 1, ~31% of UNV's gold tags cannot be supplied from KJV — English
grammar structurally drops the Hebrew function words (היה existential, כל, the 2nd את)
and **every 09xxx inseparable prefix** (ל ב כ מ ה). So KJV→UNV is unfairly
coverage-capped.

The Clear Bible handover (`../CLEAR_BIBLE_HANDOVER_from_s10obe.md`) gives us new
sources that carry those missing tags. This spec defines a **bake-off**: rather than
guess which source mix is best, run controlled configs on a fixed verse set with a
fixed model and let the gold scores decide.

## 2. Source inventory (OT only — WLC/BSB are Hebrew-anchored)

| Source | Language | Carries which SN | Acquisition cost |
|---|---|---|---|
| **WLC** | Hebrew (original) | **all**, incl. 09xxx + dropped function words | ready — import s10 loader |
| **KJV+SN** | English | content words; drops 09xxx + some function words | ready (FHL) |
| **BSB+SN** | English | derived via alignment; expected cleaner than KJV | **must build** (join `WLCM-BSB-manual.json`) |
| YLT+SN | English (literal) | same mechanism; word order closer to Hebrew | must build (deferred) |
| **UNV+SN** | Chinese | — | **answer** (FHL gold) |

WLC's unique, irreplaceable value is narrow but real: it is the **only** source that
carries the 09xxx prefixes and the function words English drops. For content words it
is redundant with any English bridge (and a strong model reads English more fluently
than Hebrew). NT (Greek SBLGNT) is out of scope here.

## 3. Architecture — two stages + a deterministic gate

### Stage 0 — consistency gate (deterministic, no LLM, **answer-blind**)

For each verse, extract each source's SN tags and partition into **09xxx**
(integer value ≥ 9000; note `0922` etc. are NOT 09xxx) vs **non-09xxx**. Build the
**non-09xxx SN multiset** per source. The SN number is the language-agnostic common
key, so we compare **numbers only — not positions** (positions are not comparable
across Hebrew/English/Chinese; resolved as design choice "b-1").

Cross-source comparison yields a per-tag **graded trust tier** (not binary 全等):

| Tier | Condition | Meaning |
|---|---|---|
| 🟢 rock | WLC = KJV (= BSB) all carry it | content word, multi-witness |
| 🟡 orig+bridge | WLC (= BSB) carry, KJV drops | WLC corroborated by BSB; KJV merely incomplete |
| 🔵 orig-only | only WLC carries (09xxx + functions even BSB drops) | WLC is sole source |

This replaces "exclude verses that aren't 全等" — KJV's dropped tags (the 31%) are
**reclassified as WLC/BSB-supplied**, not discarded. The gate is a *labeller*, not a
filter; no verse is dropped from the exam by default.

### Stage 1 — exam (what the model sees)

Feed a chosen source configuration + plain UNV → model answers UNV+SN.

| Config | Source(s) fed to model | Build cost |
|---|---|---|
| **A** | WLC + WLC+SN (Hebrew spine, complete) | none (s10-proven) |
| **B** | WLC + WLC+SN  **and**  KJV plain + KJV+SN | none |
| **C** | WLC + WLC+SN  **and**  BSB plain + BSB+SN | build BSB+SN first |

(YLT and KJV+BSB-together configs deferred unless R1/R2 motivate them.)

### Stage 2 — scoring (existing `auto_score.score_verse`, split reporting)

Score vs FHL UNV+SN gold, reported on **two axes**:
1. **09xxx vs non-09xxx** — does the config recover the 09xxx that the KJV-only
   baseline structurally misses?
2. **By trust tier** — do 🟢 tags score higher against gold than 🔵? This is the
   direct empirical test of Joshua's hypothesis "agreement → trust WLC."

Plus the standard overall cov / place / fmt for continuity with existing survey5.

## 4. Round plan (staged to avoid building BSB before it's justified)

- **Round 1 — A vs B** (both zero-build). Question: *does an English bridge help at
  all, and does WLC alone already recover the 09xxx?* If B ≈ A, an English bridge adds
  little and BSB may not be worth building.
- **Round 2 — add C** (build BSB+SN). Only if R1 shows the English bridge helps.
  Question: *does the cleaner BSB beat KJV as the bridge?*
- Scope both rounds on **Gen 1** (gold exists; survey5 already runs there). Extend if
  signal is noisy.

## 5. Reused components (import, do **not** mutate s10 files)

- s10 `run_stage2_harsh.py`: `load_wlc_verse`, `build_wlc_source`, `PREFIX_BRIDGE`,
  `_strip_points`, `CHI_TO_WLC_BOOK` — the WLC loader + lemma→FHL-09xxx bridge.
- s10 `build_exclusion.py`: `tag_multiset`, the 09xxx detector, kept-set logic.
- survey4 `auto_score.score_verse` (already used by survey5) + `strip_sn`.
- survey5 `fetch_chap_cached` for KJV/UNV; `make_out_path` conventions.

New code lives in survey5 (e.g. `run_bakeoff.py` + a `gate.py`), importing the above.
gloss2 (Chinese gloss in WLC.tsv) **must be stripped** — feeding it leaks the answer.

## 6. Model & params

Hold the model constant across configs (the variable under test is the **source**, not
the model). Default **opus** (matches s10's WLC validation); `--model` overridable
(sonnet for cheaper runs). Same verse set, same prompt scaffold, same scorer.

## 7. Success criteria

- **Coverage recovery**: A and/or B/C lift 09xxx recall well above the KJV-only
  baseline (target: approach s10's smoke 100% on Gen 1:1–5, measured across Gen 1).
- **Bridge value**: a clear, consistent cov/place delta between A and B (either
  direction) that tells us whether to feed an English bridge.
- **Trust hypothesis**: 🟢-tier tags score measurably higher vs gold than 🔵-tier,
  validating the gate as a confidence signal transferable to production (survey1/9,
  where there is no gold).

## 8. Open decisions (for Joshua at review)

1. **Round 1 = A vs B only (defer BSB build)?** — assumed yes above.
2. **Model = opus** for the bake-off? — assumed yes.
3. **Gate compares numbers only (no position), b-1** — assumed yes (positions aren't
   cross-language comparable).
4. Gate is a **labeller, not a filter** (no verse dropped) — assumed yes.
