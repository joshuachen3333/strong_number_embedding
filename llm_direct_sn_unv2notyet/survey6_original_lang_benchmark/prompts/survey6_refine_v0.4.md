# Survey6 Refine Prompt v0.4 — Re-align Tags Using Dictionary
# Evolved from v0.3
# Change: Instead of "decide move or leave", give a concrete procedure:
# extract all tags from draft, then re-insert each one using the dictionary.

## Task — 重新對齊標注 (Re-align Annotations)

You have a Chinese Bible verse (UNV) with SN tags already inserted.
You also have an SN:word dictionary mapping each tag to its original
Hebrew/Greek word. **Re-align every tag** to the correct Chinese word
using the dictionary.

## Procedure

1. **Extract**: list every SN tag from the draft, in order
2. **For each tag**: use the dictionary to find which original word it
   represents, then find the Chinese word in UNV that translates it
3. **Re-insert**: place the tag immediately after that Chinese word
4. **Verify**: your output must have the EXACT same tags as the draft
   (same count, same format, same content — character-for-character)

## HARD RULES

- **Same tags, same count** — if the draft has N tags, output has N tags.
  Do not add or remove any. Copy tag strings exactly.
- **Chinese text unchanged** — every Chinese character in exactly the
  same order. Only tag positions may differ.
- **Tag groups stay together** — morphology tags (`<WTH8xxx>`, `<WTG5xxx>`)
  must immediately follow their verb's core SN.
- **Implicit markers** (`{<...>}`) — if a tag is wrapped in braces in
  the draft, keep it wrapped in braces in the output.

## Input Format

1. **UNV+SN draft** — Chinese with SN tags
2. **Original text** — Hebrew/Greek
3. **SN:word dictionary** — SN → original word
4. **KJV+SN** — English with SN tags (cross-reference)

## Output

Return ONLY the re-aligned UNV text with SN tags.
No JSON, no explanation, no markdown.
