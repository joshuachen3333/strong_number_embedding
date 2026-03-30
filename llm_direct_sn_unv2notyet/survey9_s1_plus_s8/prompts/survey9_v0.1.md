# Survey9 Prompt v0.1 — S1+S8: UNV+SN → Target Version+SN (stripped)

## Task — 標注投射 (Annotation Projection)

You are transferring Strong's Number annotations from UNV (和合本) to
another Chinese Bible version by semantic alignment.

You receive:
1. **UNV with numbers** — source verse, already annotated with `<number>` tags
2. **UNV plain** — same verse without tags (for reference)
3. **Target verse** — plain text to annotate
4. **Original language text** — Hebrew/Greek (for reference)
5. **SN dictionary** — number to original word mapping (for reference)

Your job: move every `<number>` from the UNV text to the correct
position in the target text, by matching Chinese words with the same meaning.

## Rules

1. Every number in the UNV must appear in your output — same count, same numbers
2. Place each number AFTER the corresponding word in the target text
3. Format: `<number>` — just angle brackets and the number
4. Do not change any character in the target text
5. UNV and target are both Chinese — match words by meaning, not position

## Output

Return ONLY the annotated target text. No explanation.
