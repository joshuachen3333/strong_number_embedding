# Survey8 Prompt v0.1 — Simplest SN (bare numbers + original-language dict)

## Task — 標注投射 (Annotation Projection)

This is an Annotation Projection task. You will see:
1. An **example verse** with SN numbers already inserted — learn the placement pattern
2. A **dictionary** mapping each SN number to its original Hebrew/Greek word
3. A **target verse** (plain, no numbers) — insert the numbers from the dictionary

Your job: place each number from the dictionary after the Chinese word that corresponds to that original word.

## Format

Numbers are wrapped in angle brackets: `<7225>`, `<430>`, `<8804>`

Just the number inside angle brackets. Nothing else.

## Rules

1. Place every number from the dictionary in the output
2. Place each number AFTER the Chinese word it corresponds to
3. Format: `<number>` — just angle brackets and the number, no prefix
4. Do not change any Chinese character

## Output

Return ONLY the annotated Chinese text with numbers inserted. No explanation.
