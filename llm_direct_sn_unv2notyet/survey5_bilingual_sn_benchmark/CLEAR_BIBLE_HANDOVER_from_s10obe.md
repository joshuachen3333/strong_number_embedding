# Clear Bible → survey5 handover (from survey10-obe, 2026-06-26)

Welcome. I'm `survey10_s1_but_obe_insteadOf_oneshot-obe` (window 5544). Joshua asked
me to hand you the Clear Bible data so survey5 stops being "嗷嗷待哺 on KJV only".
**Reply back to me by osascript-injecting Terminal window 5544** (fenced, see /obe).
Joshua will be working this thread with you directly.

## Why this matters for survey5

survey5's main task is cross-lingual SN transfer: `KJV plain + KJV+SN + UNV plain →
UNV+SN`. KJV is your ONLY source today. I just proved (Stage-1 of the s10-vs-s1
contest) that **KJV is a lossy source**: on Gen 1, 31% of UNV's SN tags cannot be
supplied from KJV+SN — English structurally drops Hebrew function words (היה
existential, כל, the 2nd את, every 09xxx prefix). So KJV→UNV is unfairly
coverage-capped. Clear Bible fixes this.

## What Clear Bible gives you — `…/llm_direct_sn_unv2notyet/Alignments/data/`

| Source | Path | Carries SN via |
|---|---|---|
| **WLC** (original Hebrew) | `sources/WLC.tsv` | tokens carry Strong's directly, incl. 09xxx prefixes |
| eng: **BSB, YLT** | `eng/targets/{BSB,YLT}/ot_*.tsv` | aligned to WLC via `eng/alignments/{TRANS}/WLCM-{TRANS}-manual.json` |
| **9 more langs** (fra por rus spa arb hin ben asm hau) | `{lang}/targets/…` | same manual word-alignment to WLC/SBLGNT source tokens |

Mechanism: each target word → (alignment JSON) → source Hebrew/Greek token →
(that token's Strong's). So any aligned translation becomes an SN-annotated source.

`WLC.tsv` columns: `id altId text strongs gloss gloss2 lemma pos morph`.
⚠️ **`gloss2` is a Chinese gloss** (起初/创造/神/地…) — feeding it to a UNV task
**leaks the answer**. Strip gloss2 for any UNV-target test.

## Two tiers (I recommend Tier 1 first)

### Tier 1 — WLC (original Hebrew) as a survey5 source  [cheapest, highest value]
Add a `--source wlc` path. I already built & validated the loader + the
**lemma→FHL-09xxx bridge** — **reuse it directly** from
`…/survey10_s1_but_obe_insteadOf_oneshot/run_stage2_harsh.py`:
- `load_wlc_verse(wlc_book, chap, sec)` → `[(hebrew_text, fhl_num|None), …]`
- `build_wlc_source(tokens)` → `hebrew<FHLnum>…` source string (gloss2 already dropped)
- `PREFIX_BRIDGE` (authoritative, from survey2 FHL ref): `ל→09001 ב→09002 כ→09003
  מ→09006 ה→09009` (ו waw → no FHL 09xxx, untagged). Keyed on the **bare
  consonant after stripping niqqud** (`_strip_points`) — WLC lemmas carry vowel
  points, a plain-string match misses them (bug I already hit and fixed).
- content words: `Hdddd (≤8674)` → zero-padded FHL `dddd`.
WLC book number map so far: Genesis `01` (`CHI_TO_WLC_BOOK`). Add others as needed.

Smoke result (Stage-2 harsh, opus, Gen 1:1–5): **09xxx recall 100%** (1:1 1/1,
1:5 2/2) — the model CAN place the inseparable prefixes from a Hebrew source. So
WLC→UNV unlocks exactly the tags KJV→UNV structurally cannot.

### Tier 2 — alignment-derived multi-language sources  [bigger build]
Write a parser for `{lang}/alignments/{TRANS}/WLCM-{TRANS}-manual.json` (records:
`{"source":[wlc_ids…], "target":[tgt_ids…]}`). Join target tokens (`{lang}/targets/
{TRANS}/ot_{TRANS}.tsv`) to source WLC Strong's → an SN-annotated version of BSB /
YLT / fra / por / … as a survey5 source. BSB's manual alignment is likely
**cleaner than FHL's KJV tagging** (which had the count-mismatch above), so BSB+SN
may beat KJV+SN as a source.

## Reusable scorers (mine, in the s10 dir)
- `build_exclusion.py`: `tag_multiset`, `verse_split` (kept = UNV∩source), and the
  09xxx detector pattern (number int-value ≥ 9000; note 0922 is NOT a 09xxx).
- survey4 `auto_score.score_verse` you already use; restrict to a kept-set for fair
  scoring if you adopt a lossy source.

## Coordination
- I'm continuing the s10-vs-s1 contest + 创 3/4 in my own dir; Clear Bible↔survey5
  is **yours** now.
- Don't edit my s10 files; copy/import the WLC loader rather than mutating it
  (it's load-bearing for my Stage-2 contest arm).
- Reply via fenced inject to **window 5544**, or write me a `docs/` letter and
  ping a 1-liner.
