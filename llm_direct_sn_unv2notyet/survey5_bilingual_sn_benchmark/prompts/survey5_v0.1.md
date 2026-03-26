# Survey5 Prompt v0.1 — Cross-Lingual SN Transfer (KJV → UNV)
# Task: Given KJV+SN (English) and plain UNV (Chinese), transfer SN tags to UNV
# Ground truth: FHL's existing UNV+SN

## Task — Cross-Lingual Annotation Transfer (跨語言標注搬運)

You are transferring Strong's Number (SN) annotations from an English Bible
verse (KJV) to the corresponding Chinese Bible verse (UNV 和合本).

The KJV text already has SN tags. Your job is to place those same SNs at the
correct positions in the Chinese UNV text by semantic alignment.

**Key rules:**
- **Every SN in KJV should appear in your UNV output** (unless there is no
  Chinese equivalent — then use implicit markers `{<...>}`)
- **Placement by meaning**: match English words to their Chinese equivalents,
  then place the SN tag after the Chinese word
- **Do NOT change, reorder, or delete any Chinese characters** — only INSERT tags
- **UNV may need additional tags** not in KJV (e.g., 900x prefixes `<WAH09001>`,
  `<WAH09002>` for Hebrew inseparable prepositions). Include them if the
  Chinese text implies them.

## SN Tag Format (FHL standard)

### Hebrew (Old Testament)
- `<WHdddd>` / `<WH0dddd>` — Core SN (zero-padded)
- `<WAHdddd>` — SN with prefix marker
- `<WTH8ddd>` — Morphology (verbal stems, 8xxx series)
- `{<WHdddd>}` — Implicit marker (no Chinese equivalent)
- `<WAH09ddd>` — 900x prefix (inseparable particles: ב=09002, ל=09001, כ=09003)

### Greek (New Testament)
- `<WGdddd>` — Core SN
- `<WAGdddd>` — SN with prefix marker (rare)
- `<WTG5ddd>` — Morphology (5xxx series)
- `{<WGdddd>}` — Implicit marker

## Important Notes

### Implicit Markers
If a KJV word has an SN but the UNV has NO corresponding Chinese word,
wrap it as implicit: `{<WH0853>}`. This is common for:
- Hebrew את (object marker, SN 0853)
- Greek articles and particles

### 900x Prefixes (OT only)
UNV often has 900x prefix tags that KJV does not. These represent Hebrew
inseparable prepositions (ב, ל, כ) that are part of the Chinese word.
Add them when the Chinese context implies a preposition.

### Morphology Tags
Copy morphology tags (`<WTH8xxx>` or `<WTG5xxx>`) together with their
verb SN. Place them immediately after the core SN:
- CORRECT: 創造`<WH01254><WTH8804>`
- WRONG: 創造`<WTH8804><WH01254>`

### Format Preservation
- Preserve zero-padding: `<WH07225>` not `<WH7225>`
- Preserve braces on implicit markers
- KJV may use `<WH0853>` without braces; if UNV needs it implicit, add `{}`

## Output

Return ONLY the annotated UNV text with SN tags inserted.
No JSON, no explanation, no markdown. Just the Chinese text with tags.
