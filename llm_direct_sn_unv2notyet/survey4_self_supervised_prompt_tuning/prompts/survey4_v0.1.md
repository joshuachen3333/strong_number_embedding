# Survey4 Prompt v0.1 — UNV Self-Annotation Test
# Task: Given plain UNV text, re-insert Strong's Number annotations
# Ground truth: FHL's existing UNV+SN (bible.fhl.net)
# Derived from: survey1 v1.2 format rules, adapted for same-language task

## Task Framing — Annotation Re-insertion (標注回插)

This is an **Annotation Re-insertion** task. You are given a Chinese Bible verse
(UNV 和合本) with all Strong's Number tags removed. Your job is to re-insert
the correct SN tags at the correct positions.

This is NOT translation. The Chinese text is identical to the original — you are
restoring annotations that were stripped away.

Key implications:
- **Every Chinese word that had an SN originally must get it back**
- **Placement precision**: tags must appear immediately AFTER the Chinese word they annotate
- **Format exactness**: reproduce the exact FHL tag format (zero-padding, prefixes, braces)
- **No modifications**: do not change, reorder, or add/remove any Chinese characters

## SN Tag Format (FHL standard — reproduce exactly)

### Old Testament (Hebrew)
- `<WHdddd>` or `<WH0dddd>` — Core Strong's number (zero-padded to 4-5 digits)
- `<WAHdddd>` — Strong's with prefix marker (inseparable prepositions, etc.)
- `<WTH8ddd>` — Morphology code (8xxx series = verbal stems/tenses)
- `{<WHdddd>}` — Implicit marker (Hebrew word with no Chinese equivalent)
- `<WAH09ddd>` — 900x prefix (inseparable particles: ב=09002, ל=09001, כ=09003)

### New Testament (Greek)
- `<WGdddd>` — Core Strong's number
- `<WAGdddd>` — Strong's with prefix marker (rare)
- `<WTG5ddd>` — Morphology code (5xxx series)
- `{<WGdddd>}` — Implicit marker

## Critical Rules

### Implicit Markers — MUST PRESERVE
Tags in braces like `{<WH0853>}` represent Hebrew/Greek words with no Chinese
equivalent. They appear between Chinese words, not attached to any word.
You MUST include them. Missing implicit markers is the #1 error.

### Morphology Placement
Morphology tags (`<WTH8xxx>` or `<WTG5xxx>`) always appear immediately AFTER
the core SN of the verb they describe:
- CORRECT: 創造`<WH01254><WTH8804>`
- WRONG: 創造`<WTH8804><WH01254>`

### 900x Prefix Placement (OT only)
900x prefix tags appear BEFORE the core SN they modify:
- CORRECT: 起初`<WAH09002><WH07225>`
- WRONG: 起初`<WH07225><WAH09002>`

### Zero-Padding
Preserve leading zeros exactly. `<WH07225>` not `<WH7225>`.

### Consecutive Tags
Multiple tags can appear in sequence with no Chinese between them.
This is normal — do not insert extra characters between them.

## Self-Check

Before outputting, verify:
1. Count your SN tags — it should match the example's density for similar verses
2. Every `{<...>}` implicit marker from similar patterns should be present
3. Chinese text is completely unchanged

## Output Format

Return ONLY the annotated verse text. No JSON, no explanation, no markdown.
Just the Chinese text with SN tags inserted.
