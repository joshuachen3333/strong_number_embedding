# Survey8 Prompt v0.1 — Simplest SN (bare numbers + original-language dict)

## Task — 標注投射 (Annotation Projection)

This is an Annotation Projection task. You will see:
1. An **example verse** with SN numbers already inserted — learn the placement pattern
2. A **dictionary** mapping each SN number to its original Hebrew/Greek word
3. A **target verse** (plain, no numbers) — insert the numbers from the dictionary

Your job: place each number from the dictionary after the Chinese word that corresponds to that original word.

## Format

Numbers are wrapped in angle brackets: `<7225>`, `<430>`, `<8804>`

Markers before the number indicate special types:
- `<M8804>` — morphology (verb form), always follows its verb's core number
- `<P9002>` — prefix (preposition like "in", "to")
- `<I853>` — implicit (original word has no Chinese equivalent)
- `<A430>` — prefix-attached variant
- No marker — core SN number

## Rules

1. Place every number from the dictionary in the output
2. Place each number AFTER the Chinese word it corresponds to
3. Copy numbers exactly as given in the dictionary
4. Do not change any Chinese character

## Output

Return ONLY the annotated Chinese text with numbers inserted. No explanation.
