# Survey6 Refine Prompt v0.3 — Balanced Placement Correction
# Evolved from v0.2
# Change: v0.2 was too conservative (9/10 verses unchanged).
# Added positive guidance: explicit alignment examples showing WHEN to move.

## Task — 標注位置校正 (Annotation Placement Correction)

A previous system inserted Strong's Number (SN) tags into this Chinese
Bible verse. **Most tags are correctly placed**, but some may be after
the wrong Chinese word. Your job: move misplaced tags to the right position.

## ABSOLUTE CONSTRAINTS (violation = failure)

1. **NEVER delete any tag** — every tag in the draft must appear in output.
2. **NEVER add any tag** — no new tags.
3. **NEVER modify a tag** — copy character-for-character. Do not change
   `<WAH09002>` to `<WH09002>`, do not add/remove braces `{}`.
4. **NEVER change Chinese text** — not a single character.
5. **Tag count in = tag count out**.

## Input Format

1. **UNV+SN draft** — Chinese with SN tags (mostly correct)
2. **Original text** — Hebrew/Greek
3. **SN:word dictionary** — SN → original word mapping
4. **KJV+SN** — English with SN tags (cross-reference)

## How to Decide: Move or Leave?

For each tag in the draft, use the dictionary to verify its position:

1. Look up the SN in the dictionary → get the original word
2. Think: which Chinese word in UNV translates that original word?
3. Check: is the tag already after that Chinese word?
   - **YES** → leave it (most tags will be correct)
   - **NO** → move it to after the correct Chinese word

Example — tag correctly placed (leave it):
```
Draft: 神<WH0430>    Dict: WH0430 = אֱלֹהִים (God)    → 神 = God ✓ leave
```

Example — tag misplaced (move it):
```
Draft: 創造天<WH08064>地    Dict: WH08064 = הַשָּׁמַיִם (heaven)
→ <WH08064> should be after 天 (heaven), not before 地
→ Fix: 創造天<WH08064>地
Actually it's already correct in this case. Only move when genuinely wrong.
```

**Keep tag groups together**: morphology tags (`<WTH8xxx>`) stay immediately
after their verb SN. Move them as a unit.

## Output

Return ONLY the corrected UNV text with SN tags.
No JSON, no explanation, no markdown.
