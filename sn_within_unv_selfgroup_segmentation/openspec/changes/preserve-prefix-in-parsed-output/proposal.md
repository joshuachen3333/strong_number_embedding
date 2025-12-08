# Change: Preserve Strong's Number Prefixes in Parsed Output

## Why

Currently, the parser outputs Strong's numbers in two different formats:
- **Parsed section**: `{<05921>}<06440>` (bare numbers without prefixes)
- **Raw section**: `{<WAH05921>}<WH06440>` (complete tags with WAH/WH/WTH prefixes)

This inconsistency causes:
1. **Visual mismatch** between left (Raw) and right (Parsed) displays in the viewer
2. **Complex color mapping** requiring normalization logic to strip/add prefixes
3. **Information loss** as the prefixes encode morphological information (W=waw, A=article, H=definite article, T=tense)
4. **Maintenance burden** maintaining two different parsing patterns in viewer code

The user has requested that Parsed section preserve the complete Strong's number tags (e.g., `<WAH05921>`) to match the Raw section format, making the output consistent and easier to work with.

## What Changes

- Parser output format: Change Parsed section to use complete Strong's number tags with prefixes (`<WAH05921>` instead of `<05921>`)
- Viewer color mapping: Simplify regex patterns to handle only one format (with prefixes)
- Output consistency: Both Parsed and Raw sections will use identical Strong's number representations

Example transformation:
```
BEFORE:
Parsed: {<05921>}<06440> — 名詞「面、臉面」
Raw:    {<WAH05921>}<WH06440>

AFTER:
Parsed: {<WAH05921>}<WH06440> — 名詞「面、臉面」
Raw:    {<WAH05921>}<WH06440>
```

## Impact

- **Affected code:**
  - `parse_verse_v1_8.py`: Modify `format_groups_to_text()` to preserve prefixes from original bible_text_raw
  - `viewer_v2/js/color_mapper.js`: Simplify `extractSNsFromLine()` and `applyColorsToParsedText()` to handle prefixed format

- **Output files:** All newly parsed verses will have the new format. Existing output files remain unchanged (no migration needed as they are regenerable)

- **Breaking change:** Yes, changes parser output format. Viewer must be updated simultaneously.

- **User impact:** Visual consistency improvement - no functional changes to user workflow
