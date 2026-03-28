# Survey5 Prompt v0.4 — Cross-Lingual SN Transfer (KJV → UNV)
# Evolved from: v0.3
# Changes: Shorter prompt (v0.3 was 4471 chars → coverage dropped).
#   Merged redundant rules, kept v0.3 fixes (no backtick, tag after word, NT suffix).

## Task — Cross-Lingual Annotation Projection (跨語言標注投射)

You are TRANSFERRING Strong's Number (SN) tags from KJV (English) to UNV (Chinese 和合本) by semantic alignment. The KJV tags are ground truth — do not second-guess them.

Your job: place each KJV tag after the corresponding Chinese word in UNV.

## Tag Format (copy exactly from KJV)

**OT**: `<WHdddd>` core, `<WAHdddd>` prefix, `<WTH8ddd>` morphology, `{<WHdddd>}` implicit, `<WAH09ddd>` 900x prefix
**NT**: `<WGdddd>` or `<WGdddda>` core (may have letter suffix), `<WTG5ddd>` morphology, `{<WGdddd>}` implicit

## Rules

1. **Every KJV tag must appear** in output. UNV may need MORE (900x prefixes, WAH markers). Missing = failure.

2. **Tag goes AFTER its Chinese word**, never before:
   - CORRECT: 加他`<WH07005>`
   - WRONG: `<WH07005>`加他

3. **Implicit markers**: KJV word has SN but no Chinese equivalent → `{<WH0853>}`

4. **900x prefixes**: Chinese word implies preposition (在=in, 到=to) → add `<WAH09002>` or `<WAH09001>` BEFORE the core SN

5. **Morphology follows verb SN**: 創造`<WH01254><WTH8804>` (not reversed)

6. **Format**: preserve zero-padding, braces, letter suffixes exactly as in KJV

7. **Chinese text untouched**: do not change any Chinese character

## Output

Return ONLY the annotated UNV text. No explanation, no markdown, no backticks.
