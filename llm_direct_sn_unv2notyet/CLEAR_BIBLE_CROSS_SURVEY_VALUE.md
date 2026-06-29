# Clear Bible — cross-survey value (s1 / s9 / s10)

> Origin: survey5-obe onboarded the **Clear Bible** alignment data (2026-06-26,
> `survey5_bilingual_sn_benchmark/CLEAR_BIBLE_HANDOVER_from_s10obe.md`). This doc
> records *why it matters beyond survey5* — its leverage on s1 (consensus gold),
> s9 (production naked), and s10 (conventions + C/D contest). Authored by
> survey10-obe; survey5-obe owns the survey5 integration itself.

## What Clear Bible is (the data)

`…/llm_direct_sn_unv2notyet/Alignments/data/` (Scripture Burrito format):
- `sources/WLC.tsv` — original Hebrew, every morpheme carrying its Strong's
  (incl. the 09xxx inseparable prefixes); `sources/SBLGNT*` for Greek NT.
- `{lang}/targets/{TRANS}/…` + `{lang}/alignments/{TRANS}/WLCM-{TRANS}-manual.json`
  — **manual** word-level alignment of 10+ languages (arb asm ben eng fra hau hin
  por rus spa) × multiple translations to the Hebrew/Greek source tokens. **No
  Chinese.**

## The three things it brings that nothing else does

1. **Independent human ground truth.** It is *manual* word-by-word alignment —
   not FHL, not any LLM. Today s1/s9/s10 all validate against the *single* FHL
   source (UNV+SN), which is a circularity risk (LLM consensus ≠ truth). Clear
   Bible is a **second, independent truth that can validate the validators.**
2. **A complete original-language source.** WLC carries **every** SN, including
   the ones KJV/English structurally drop — the 09xxx prefixes, the 2nd את,
   Hebrew function words. (Stage-1 measured KJV missing **31%** of UNV's tags on
   Gen 1.)
3. **10+ languages.** Enables cross-language / cross-Testament (OT↔NT)
   generalisation tests — no longer a Chinese-only single line.

## Per-survey leverage

### S1 (consensus gold)
- **Break the circularity — a non-LLM "4th judge."** When s1's 3 models split at
  R2/R3, only LLMs vote. Clear Bible's manual alignment is an **non-LLM arbiter**:
  where the original Hebrew word actually binds, the human gold decides —
  strengthening R3's "pick winner / declare collective error."
- **Validate whether s1's gold is actually right.** Diff s1's produced gold
  against Clear Bible alignment → quantify "does consensus = truth?" — the
  external sanity check s1 has always lacked.
- ⚠️ **survey6 caution**: feeding WLC as an *extra one-shot* may overload the
  prompt (survey6 died of info overload: +7pp placement, −10pp coverage). Test,
  don't assume.

### S10 (conventions + C/D) — biggest winner
- **A fairer/stronger contest source.** The A2 contest used KJV (drops 31% →
  unfair). Swapping in **WLC/BSB as source** removes the count-mismatch → a
  cleaner s1-vs-s10 comparison. **Stage-2 already uses WLC** (`run_stage2_harsh.py`,
  09xxx recall validated).
- **Evidence for D-deliberation.** When s10 routes a genuinely ambiguous verse to
  D-deliberation, Clear Bible's manual alignment is the **objective evidence** of
  how the original binds — so D isn't just LLMs arguing again.
- **External convention validation.** A scribe-distilled convention can be
  back-checked against "how do 10 languages align this same phenomenon" — if a
  convention is cross-lingually consistent its credibility jumps; if it only holds
  in Chinese, that's an overfitting signal (feeds `CONVENTIONS_PIPELINE.md` step-5).

### S9 (production naked)
- **An independent quality ceiling.** s9's output is currently only scored for
  FHL self-consistency. Clear Bible gives an external truth → "s9 reached not just
  FHL-consistent but human-original-alignment-consistent."
- **Extra reference for hard verses.** Where UNV+SN itself is ambiguous, WLC can
  be a supplementary reference in the naked pipeline, helping `fix_pipeline`
  confirm which 09xxx are real.
- **Multi-language extrapolation.** The naked (去殼) method is language-agnostic;
  Clear Bible's 10 languages give ground truth to validate "same method, non-Chinese
  target."

## One line + honest limits

**Common value to all three = one independent human truth + one complete
original-language source — it breaks the "everyone validates against the single
FHL source" circularity, and makes KJV-sourced experiments (especially the s10
contest) fair.**

**Limit: Clear Bible has NO Chinese** (the 10 languages exclude Chinese), so it
**cannot be a direct UNV/LCC answer key** — its power is on the **source side
(original / other languages) and as cross-validation**, not as the Chinese-target
truth. `gloss2` does carry Chinese word-glosses but they **leak the answer**, so
they're usable only as a controlled variable, never as input to a UNV-target test.

**Ranking:** biggest winner **S10** (contest eats WLC directly), then **S1** (a
non-LLM judge that breaks the circularity), then **S9** (gains an external quality
ceiling).

## Reusable artifacts (already built)
- `survey10_…/run_stage2_harsh.py` — WLC loader (`load_wlc_verse`,
  `build_wlc_source`) + authoritative lemma→FHL-09xxx bridge (`PREFIX_BRIDGE`,
  niqqud-stripped consonant match). gloss2 dropped by construction.
- `survey10_…/build_exclusion.py` — kept-set (UNV∩source) + 09xxx detector
  (number int-value ≥ 9000).
- `survey5_…/CLEAR_BIBLE_HANDOVER_from_s10obe.md` — the data inventory + Tier-1
  (WLC source) / Tier-2 (alignment-derived multi-language) build plan.
