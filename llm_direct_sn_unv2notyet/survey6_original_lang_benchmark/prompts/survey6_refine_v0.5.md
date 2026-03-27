# Survey6 Refine Prompt v0.5 — High-Confidence-Only Correction
# Evolved from v0.4
# Problem: v0.4 moves tags that were already correct (P1 place=1.00 → P2 drops).
# Fix: only move tags where placement is CLEARLY wrong.

## Task — 標注位置微調 (Fine-tune Tag Positions)

A previous system inserted Strong's Number (SN) tags into this Chinese Bible
verse. Most tags are already correctly placed. You may fine-tune positions
using the original-language dictionary — but **only move a tag when it is
CLEARLY after the wrong Chinese word**.

## ABSOLUTE CONSTRAINTS

1. **NEVER delete any tag** — every tag in the draft appears in output.
2. **NEVER add any tag**.
3. **NEVER modify any tag** — copy character-for-character.
4. **NEVER change Chinese text**.
5. **Tag count in = tag count out**.

## Decision Rule — Move Only When Clearly Wrong

For each tag, check the dictionary:
- SN → dictionary → original word → which Chinese word does it translate?
- Is the tag currently after a Chinese word that COULD translate the original? → **LEAVE IT**
- Is the tag clearly after an UNRELATED Chinese word? → **MOVE IT**

**"Could translate" is broad** — if there is any reasonable connection
between the Chinese word and the original word, leave the tag.

Example of LEAVING a tag (correct or plausibly correct):
- `神<WH0430>` — WH0430 = אֱלֹהִים (God), 神 = God → correct, leave it
- `看<WH07200>` — WH07200 = רָאָה (to see), 看 = see → correct, leave it

Example of MOVING a tag (clearly wrong):
- `天<WH0776>地` — WH0776 = אֶרֶץ (earth), but 天 = heaven, not earth
  → move to `天地<WH0776>` (地 = earth)

**When in doubt, leave the tag where it is.**

## Tag Group Rule

Morphology tags (`<WTH8xxx>`, `<WTG5xxx>`) must stay immediately after
their verb's core SN. Always move them together as one unit.

## Output

Return ONLY the text with SN tags. No explanation, no markdown.
