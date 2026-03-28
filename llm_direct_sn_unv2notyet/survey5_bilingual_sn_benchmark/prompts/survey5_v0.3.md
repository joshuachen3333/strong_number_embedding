# Survey5 Prompt v0.3 — Cross-Lingual SN Transfer (KJV → UNV)
# Evolved from: v0.2
# Changes:
#   1. Explicit "no backticks" rule (DeepSeek wraps tags in `` ` `` → breaks scoring)
#   2. Strengthened "tag AFTER Chinese word" rule (model sometimes puts tag before)
#   3. Added WAH prefix coverage guidance (UNV needs WAH tags KJV doesn't have)

## Task Framing — Cross-Lingual Annotation Projection (跨語言標注投射)

This is a **Cross-Lingual Annotation Projection** task. You are NOT
independently analyzing Hebrew/Greek or translating. You are TRANSFERRING
existing annotations from a source text (KJV with SN tags) onto a target
text (UNV Chinese) by semantic alignment.

**The KJV annotations are ground truth — do not second-guess them.**

Key implications:
- **Trust the source**: every SN tag in KJV is correct — your job is
  only WHERE to place each one in UNV
- **Placement, not judgment**: every SN in KJV must appear in your output,
  no exceptions — you decide only the position
- **Align by meaning**: KJV English and UNV Chinese use different word order
  and phrasing — match by semantic correspondence, not by position
- **Preserve groupings**: when multiple SN tags are grouped together in KJV
  (e.g., verb + morphology), keep them grouped in UNV too

## Input Format

You will receive:
1. **KJV (plain)** — English, no tags
2. **KJV+SN** — English with Strong's Number tags
3. **UNV (plain)** — Chinese (和合本), no tags

Your output: the UNV text with SN tags inserted at the correct positions.

## SN Tag Format (FHL standard — reproduce exactly)

### Hebrew (Old Testament)
- `<WHdddd>` / `<WH0dddd>` — Core SN (zero-padded to 4-5 digits)
- `<WAHdddd>` — SN with prefix marker (e.g., `<WAH0905>`)
- `<WTH8ddd>` — Morphology (verbal stems/tenses, 8xxx series)
- `{<WHdddd>}` — Implicit marker (Hebrew word with no Chinese equivalent)
- `<WAH09ddd>` — 900x prefix (inseparable particles: ב=09002, ל=09001, כ=09003)

### Greek (New Testament)
- `<WGdddd>` or `<WGdddda>` — Core SN (may have letter suffix: a, b, c)
- `<WAGdddd>` — SN with prefix marker (rare)
- `<WTG5ddd>` — Morphology (5xxx series)
- `{<WGdddd>}` — Implicit marker

## Critical Rules

### 1. Every KJV SN Must Appear in Output
Count the SN tags in KJV. Your output must have AT LEAST that many.
UNV may need MORE tags (900x prefixes, WAH markers, different implicit markers).
Missing tags = failure.

### 2. Tag Position — ALWAYS After the Chinese Word
Place each SN tag immediately AFTER its corresponding Chinese word:
- CORRECT: 神`<WH0430>`
- WRONG: `<WH0430>`神

This applies to ALL tag types: core SN, morphology, implicit, prefix.

### 3. Implicit Markers — MUST HANDLE
If a KJV word has an SN but UNV has NO corresponding Chinese word,
wrap it as implicit: `{<WH0853>}`.

Common cases:
- `<WH0853>` (את, object marker) → almost always implicit in UNV: `{<WH0853>}`
- KJV "and" → sometimes implicit, sometimes maps to Chinese 和/與

### 4. WAH Prefix Tags — UNV Needs More Than KJV Has
UNV frequently has WAH-prefixed tags that KJV does NOT have:
- `<WAH09ddd>` — 900x prefixes for Hebrew inseparable prepositions (ב, ל, כ)
- `<WAHdddd>` — other prefix-marked SNs (e.g., conjunctive ו, relative ש)

Example: KJV "In the beginning`<WH07225>`" → UNV "起初`<WAH09002><WH07225>`"
The `<WAH09002>` is NOT in KJV but MUST be in UNV.

When a Chinese word implies a preposition, conjunction, or relative pronoun
not explicitly tagged in KJV, add the appropriate WAH tag.

### 5. Morphology Placement
Morphology tags always immediately FOLLOW their verb's core SN:
- CORRECT: 創造`<WH01254><WTH8804>`
- WRONG: 創造`<WTH8804><WH01254>`

### 6. Format Preservation
- Preserve zero-padding exactly: `<WH07225>` not `<WH7225>`
- Preserve braces on implicit markers: `{<WH0853>}` not `<WH0853>`
- Preserve letter suffixes on NT SNs: `<WG3092a>` not `<WG3092>`
- Copy tag content character-for-character from KJV input

### 7. Chinese Text Untouched
Do NOT change, reorder, add, or delete any Chinese character.
Only INSERT SN tags between/after Chinese characters.

## Self-Check

Before outputting, verify:
1. Count SN tags in your output ≥ count in KJV input
2. Every `{<...>}` implicit marker is accounted for
3. Chinese text is completely unchanged from the input
4. Morphology tags follow (not precede) their verb SN
5. Every tag is AFTER a Chinese word, not before

## Output

Return ONLY the annotated UNV text with SN tags inserted.
No JSON, no explanation, no markdown, no backticks. Plain text only.
