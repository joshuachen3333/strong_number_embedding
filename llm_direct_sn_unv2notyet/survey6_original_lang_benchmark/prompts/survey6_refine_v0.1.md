# Survey6 Refine Prompt v0.1 — Placement Correction Pass
# Two-pass pipeline Pass 2: fix tag positions using original-language anchoring
# Input: UNV+SN draft (from Pass 1) + Original text + SN:word dict
# Goal: improve placement WITHOUT removing any tags

## Task Framing — 標注位置校正 (Annotation Placement Correction)

You are correcting the **placement** of Strong's Number (SN) tags in a
Chinese Bible verse (UNV 和合本). A previous system already inserted the
tags, but some may be in the wrong position.

You have the original Hebrew/Greek text and an SN:word dictionary to help
you determine the correct position for each tag.

**Core rules**:
- **Do NOT remove any tags** — every SN tag in the draft must appear in
  your output. You may only MOVE tags, never delete them.
- **Do NOT add new tags** — only reposition existing ones.
- **Do NOT change any Chinese character** — only move SN tags between
  characters.
- **Do NOT change tag format** — copy each tag character-for-character.

## Input Format (4 inputs, all same verse)

1. **UNV+SN draft** — Chinese text with SN tags already inserted (may have
   placement errors)
2. **Original text** — Hebrew (OT) or Greek (NT)
3. **SN:word dictionary** — maps each SN number to its original Hebrew/Greek
   word; use this to determine which Chinese word each tag belongs after
4. **KJV+SN** — English with SN tags (for cross-reference)

## How to Correct Placement

For each SN tag in the draft:
1. Look up the SN in the dictionary → find the original Hebrew/Greek word
2. Identify which Chinese word in UNV corresponds to that original word
3. If the tag is already after the correct Chinese word → leave it
4. If the tag is after the wrong Chinese word → move it to the correct position

**Keep tag groupings intact**: morphology tags (`<WTH8xxx>`, `<WTG5xxx>`)
must stay immediately after their verb's core SN. Move them together.

## Critical Constraints

1. **Tag count must be preserved** — output must have EXACTLY the same
   number of SN tags as the draft input. No more, no less.
2. **Chinese text unchanged** — not a single character added, removed, or
   reordered.
3. **Tag format unchanged** — zero-padding, braces, prefixes all preserved
   exactly as in the draft.

## Output

Return ONLY the corrected UNV text with SN tags.
No JSON, no explanation, no markdown. Just the Chinese text with tags.
