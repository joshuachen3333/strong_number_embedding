# Survey8 Prompt v0.2 — Simplest SN
# Changes from v0.1:
#   1. Clarify: place each dict entry ONCE at ONE position (no duplicates)
#   2. Clarify: if same number appears multiple times in dict, place it that many times
#   3. Better example showing the pattern

## Task — 標注投射 (Annotation Projection)

You are inserting Strong's Number annotations into a Chinese Bible verse.

You receive:
1. An **example** — a verse already annotated, showing the pattern
2. A **dictionary** — each number maps to a Hebrew/Greek word
3. A **target verse** — plain Chinese text to annotate

Your job: for each dictionary entry, find which Chinese word translates
that Hebrew/Greek word, and place the number after it.

## Format

`<number>` — angle brackets around the number. Example: `<7225>`, `<430>`

## Rules

1. **One dict entry = one placement.** If the dictionary lists a number
   twice (same word appears twice), place it twice at two different positions.
   If listed once, place it once.
2. Place each number AFTER the Chinese word it corresponds to
3. Do not add numbers that are not in the dictionary
4. Do not change any Chinese character

## Output

Return ONLY the annotated text. No explanation.
