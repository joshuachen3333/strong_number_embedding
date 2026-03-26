# Survey5 Reverse Prompt v0.1 — Cross-Lingual SN Transfer (UNV → KJV)
# 輔助任務: Given UNV plain + UNV+SN + KJV plain → KJV+SN
# Ground truth: FHL's existing KJV+SN

## Task Framing — Cross-Lingual Annotation Projection (跨語言標注投射)

This is a **Cross-Lingual Annotation Projection** task. You are NOT
independently analyzing Hebrew/Greek or translating. You are TRANSFERRING
existing annotations from a source text (UNV with SN tags) onto a target
text (KJV English) by semantic alignment.

**The UNV annotations are ground truth — do not second-guess them.**

Key implications:
- **Trust the source**: every SN tag in UNV is correct — your job is
  only WHERE to place each one in KJV
- **Placement, not judgment**: every SN in UNV must appear in your output,
  no exceptions — you decide only the position
- **Align by meaning**: UNV Chinese and KJV English use different word order
  and phrasing — match by semantic correspondence, not by position
- **Preserve groupings**: when multiple SN tags are grouped together in UNV
  (e.g., verb + morphology), keep them grouped in KJV too

## Input Format

You will receive:
1. **UNV (plain)** — Chinese Bible verse (和合本) without any tags
2. **UNV+SN** — same verse with Strong's Number tags already inserted
3. **KJV (plain)** — English Bible verse (King James Version) without any tags

Your output: the KJV text with SN tags inserted at the correct positions.

## SN Tag Format (FHL standard — reproduce exactly)

### Hebrew (Old Testament)
- `<WHdddd>` / `<WH0dddd>` — Core SN (zero-padded to 4-5 digits)
- `<WAHdddd>` — SN with prefix marker
- `<WTH8ddd>` — Morphology (verbal stems/tenses, 8xxx series)
- `{<WHdddd>}` — Implicit marker (Hebrew word with no English equivalent)
- `<WAH09ddd>` — 900x prefix (inseparable particles: ב=09002, ל=09001, כ=09003)

### Greek (New Testament)
- `<WGdddd>` — Core SN
- `<WAGdddd>` — SN with prefix marker (rare)
- `<WTG5ddd>` — Morphology (5xxx series)
- `{<WGdddd>}` — Implicit marker

## Critical Rules

### 1. Every UNV SN Must Appear in Output
Count the SN tags in UNV. Your output must have AT LEAST that many.
Missing tags = failure.

### 2. Implicit Markers
If a UNV word has an SN but KJV has NO corresponding English word,
wrap it as implicit: `{<WH0853>}`.

### 3. 900x Prefixes
UNV may have 900x prefix tags (e.g., `<WAH09002>`) that represent Hebrew
inseparable prepositions. KJV may express these as separate English words
("in", "to", "like") or not at all. Place them as implicit if KJV has no
corresponding word.

### 4. Morphology Placement
Morphology tags always immediately FOLLOW their verb's core SN:
- CORRECT: created`<WH01254><WTH8804>`
- WRONG: created`<WTH8804><WH01254>`

### 5. Format Preservation
- Preserve zero-padding exactly: `<WH07225>` not `<WH7225>`
- Preserve braces on implicit markers: `{<WH0853>}` not `<WH0853>`
- Copy tag content character-for-character from UNV input

### 6. English Text Untouched
Do NOT change, reorder, add, or delete any English word.
Only INSERT SN tags between/after English words.

## Self-Check

Before outputting, verify:
1. Count SN tags in your output ≥ count in UNV input
2. Every `{<...>}` implicit marker is accounted for
3. English text is completely unchanged from the input
4. Morphology tags follow (not precede) their verb SN

## Output

Return ONLY the annotated KJV text with SN tags inserted.
No JSON, no explanation, no markdown. Just the English text with tags.
