# Survey6 Refine Prompt v0.2 — Conservative Placement Correction
# Evolved from v0.1
# Change: Much stricter "when in doubt, don't touch" policy
# v0.1 problem: model moved/deleted tags that were already correct,
# e.g. removed <WAH09002> prefix, merged separate character tags.

## Task — 標注位置微調 (Annotation Placement Fine-tuning)

A previous system inserted Strong's Number (SN) tags into this Chinese
Bible verse. **Most tags are already in the correct position.** Your job
is to fix ONLY the few that are clearly misplaced.

**Default action: DO NOTHING.** Only move a tag if you are highly confident
it is after the wrong Chinese word. When in doubt, leave it where it is.

## ABSOLUTE CONSTRAINTS (violation = failure)

1. **NEVER delete any tag** — every tag string in the draft must appear
   in your output, character-for-character identical. Count them.
2. **NEVER add any tag** — no new tags that weren't in the draft.
3. **NEVER modify a tag** — do not change `<WAH09002>` to `<WH09002>`,
   do not add or remove braces `{}`, do not change any character inside `<>`.
4. **NEVER change Chinese text** — not a single character.
5. **Tag count in = tag count out** — if the draft has N tags, output has N tags.

## Input Format

1. **UNV+SN draft** — Chinese with SN tags (mostly correct, few misplaced)
2. **Original text** — Hebrew/Greek
3. **SN:word dictionary** — SN → original word mapping
4. **KJV+SN** — English with SN tags (cross-reference)

## When to Move a Tag

Move a tag ONLY when ALL of these are true:
- The dictionary clearly shows the SN maps to a specific original word
- That original word clearly corresponds to a DIFFERENT Chinese word than
  where the tag currently sits
- You are confident about the correct Chinese word

**If any doubt → leave the tag in place.**

Keep tag groups together: morphology tags (`<WTH8xxx>`) stay immediately
after their verb SN. Move them as a unit.

## Output

Return ONLY the corrected UNV text with SN tags.
No JSON, no explanation, no markdown.
