# Survey5 Prompt v0.2 — Cross-Lingual SN Transfer (KJV → UNV)
# Evolved from: v0.1
# Change: Added Annotation Projection framing (proven in survey1 v1.2)
# v1.2 evidence: dramatically improved convergence on hard verses,
# eliminated need for model-specific patches in most cases.

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
1. **KJV+SN** — English Bible verse with Strong's Number tags already inserted
2. **UNV (plain)** — Chinese Bible verse (和合本) without any tags

Your output: the UNV text with SN tags inserted at the correct positions.

## SN Tag Format (FHL standard — reproduce exactly)

### Hebrew (Old Testament)
- `<WHdddd>` / `<WH0dddd>` — Core SN (zero-padded to 4-5 digits)
- `<WAHdddd>` — SN with prefix marker
- `<WTH8ddd>` — Morphology (verbal stems/tenses, 8xxx series)
- `{<WHdddd>}` — Implicit marker (Hebrew word with no Chinese equivalent)
- `<WAH09ddd>` — 900x prefix (inseparable particles: ב=09002, ל=09001, כ=09003)

### Greek (New Testament)
- `<WGdddd>` — Core SN
- `<WAGdddd>` — SN with prefix marker (rare)
- `<WTG5ddd>` — Morphology (5xxx series)
- `{<WGdddd>}` — Implicit marker

## Critical Rules

### 1. Every KJV SN Must Appear in Output
Count the SN tags in KJV. Your output must have AT LEAST that many.
UNV may need MORE tags (900x prefixes, different implicit markers).
Missing tags = failure.

### 2. Implicit Markers — MUST HANDLE
If a KJV word has an SN but UNV has NO corresponding Chinese word,
wrap it as implicit: `{<WH0853>}`.

Common cases:
- `<WH0853>` (את, object marker) → almost always implicit in UNV: `{<WH0853>}`
- KJV "and" `<WH0853>` → sometimes implicit, sometimes maps to Chinese 和/與

### 3. 900x Prefixes — UNV May Need Extra Tags
UNV often has 900x prefix tags that KJV does NOT have. These represent
Hebrew inseparable prepositions (ב, ל, כ) that are absorbed into the
Chinese word's meaning.

Example: KJV "In the beginning`<WH07225>`" → UNV "起初`<WAH09002><WH07225>`"
The `<WAH09002>` (prefix ב = "in") is NOT in KJV but must be in UNV.

When you see a Chinese word that implies a preposition ("in", "to", "like"),
add the appropriate 900x prefix BEFORE the core SN.

### 4. Morphology Placement
Morphology tags always immediately FOLLOW their verb's core SN:
- CORRECT: 創造`<WH01254><WTH8804>`
- WRONG: 創造`<WTH8804><WH01254>`

### 5. Format Preservation
- Preserve zero-padding exactly: `<WH07225>` not `<WH7225>`
- Preserve braces on implicit markers: `{<WH0853>}` not `<WH0853>`
- Copy tag content character-for-character from KJV input

### 6. Chinese Text Untouched
Do NOT change, reorder, add, or delete any Chinese character.
Only INSERT SN tags between/after Chinese characters.

## Self-Check

Before outputting, verify:
1. Count SN tags in your output ≥ count in KJV input
2. Every `{<...>}` implicit marker is accounted for
3. Chinese text is completely unchanged from the input
4. Morphology tags follow (not precede) their verb SN

## Output

Return ONLY the annotated UNV text with SN tags inserted.
No JSON, no explanation, no markdown. Just the Chinese text with tags.
