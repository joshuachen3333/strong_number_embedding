# Survey6 Prompt v0.2 — Original Language Anchored SN Transfer
# Evolved from: v0.1
# Change: Added Tag Inventory checklist to recover coverage
# v0.1 evidence: placement +7pp vs survey5 but coverage -10pp;
# root cause = model emits fewer tags when overwhelmed by 5 inputs.
# Tag inventory gives explicit checklist of every tag that must appear.

## Task Framing — 跨語言標注投射 (Cross-Lingual Annotation Projection)

This is a **Cross-Lingual Annotation Projection** task across three languages:
Original (Hebrew/Greek) → English (KJV) → Chinese (UNV 和合本).

You are NOT translating or analyzing. You are **EMBEDDING** Strong's Number (SN)
tags into the UNV Chinese text by aligning it with the KJV+SN source.

The SN:word dictionary tells you exactly which original Hebrew/Greek word each SN
number represents. **Use it to confirm your placement** — each SN tag must be
embedded after the Chinese word that corresponds to that original word.

**Core principle**: trust the source. Every SN in KJV+SN is correct. Your only
job is WHERE to embed each one in UNV.

## Input Format (6 inputs, all same verse)

You will receive:

1. **KJV (plain)** — English, no tags
2. **Original text** — Hebrew (OT) or Greek (NT), no tags
3. **KJV+SN** — English with Strong's Number tags embedded
4. **SN:word dictionary** — maps each SN number to its original Hebrew/Greek word;
   these are for **embedding reference only** — use them to confirm which UNV
   word should carry each SN tag
5. **Tag inventory** — numbered list of EVERY tag extracted from KJV+SN;
   **your output MUST contain ALL of these tags** — this is your checklist
6. **UNV (plain)** — Chinese (和合本), no tags ← **this is what you annotate**

Your output: the UNV text with SN tags embedded at the correct positions.

## How to Use the SN:word Dictionary

Alignment chain for each SN:
1. Find the SN in KJV+SN → identify the KJV English word it tags
2. Cross-check with dictionary: SN → original Hebrew/Greek word
3. Align KJV word + original word → find the corresponding UNV Chinese word
4. **Embed** the SN tag immediately after that Chinese word

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

### 1. EVERY Tag in the Inventory Must Appear — NO EXCEPTIONS
The tag inventory lists every SN tag from KJV+SN. **ALL of them must appear
in your output.** Copy each tag character-for-character from the inventory.
If you output fewer tags than the inventory count, you have FAILED.

UNV may also need EXTRA tags not in the inventory (900x prefixes, different
implicit markers). Add those too.

### 2. Implicit Markers
If a KJV word has an SN but UNV has NO corresponding Chinese word, embed it
as implicit: `{<WH0853>}`.
Common: `<WH0853>` (את, object marker) → almost always implicit in UNV.

### 3. 900x Prefixes — UNV May Need Extra Tags
UNV often needs 900x prefix tags that KJV does NOT have.
Example: KJV `In the beginning<WH07225>` → UNV `起初<WAH09002><WH07225>`
The `<WAH09002>` (ב = "in") is NOT in KJV but must be embedded in UNV.

### 4. Morphology Placement
Morphology tags always FOLLOW their verb's core SN immediately:
- CORRECT: 創造`<WH01254><WTH8804>`
- WRONG: 創造`<WTH8804><WH01254>`

### 5. Format Preservation
- Preserve zero-padding exactly: `<WH07225>` not `<WH7225>`
- Preserve braces: `{<WH0853>}` not `<WH0853>`
- Copy tags character-for-character from KJV+SN input and inventory

### 6. Chinese Text Untouched
Do NOT change, reorder, add, or delete any Chinese character.
Only INSERT/EMBED SN tags.

## Self-Check

Before outputting, verify:
1. **Count your SN tags ≥ inventory count** — if fewer, go back and add missing ones
2. Every `{<...>}` implicit marker is present
3. Chinese text is completely unchanged
4. Morphology tags follow (not precede) their verb SN

## Output

Return ONLY the annotated UNV text with SN tags embedded.
No JSON, no explanation, no markdown. Just the Chinese text with tags.
