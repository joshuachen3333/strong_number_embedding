# Proposal: Fix Viewer Color Grouping and Parsed Output Markers

## Why

The viewer's color grouping system currently produces incorrect visualizations when the same Strong's Number appears in multiple groups (e.g., object marker `{<0853>}` אֵת), making it impossible to see correct group boundaries. Additionally, the parsed output's `:: ::` markers use numeric form instead of WH/WAH prefix form, creating visual inconsistency. These issues directly impact user ability to understand semantic groupings in biblical text.

## Problem Statement

Two related issues in viewer_v2 affect the correctness of Strong's Number grouping visualization:

### Issue 1: Incorrect Color Grouping for Repeated SNs

When the same Strong's Number appears in multiple groups (e.g., object marker `{<0853>}` אֵת), the current "first occurrence wins" color mapping strategy causes all instances to receive the same color, breaking visual group boundaries.

**Example from Gen 1:1:**
```
Raw text: {<WH0853>}天<WH08064>{<WH0853>}地<WH0776>

Expected grouping:
- Group 1: {<WH0853>}天<WH08064> → all pink
- Group 2: {<WH0853>}地<WH0776> → all purple

Actual behavior:
- {<WH0853>} → pink (first occurrence)
- <WH08064> → pink ✓
- {<WH0853>} → pink ✗ (should be purple)
- <WH0776> → purple ✓
```

This creates a misleading visual where three SNs appear grouped (pink) when only two should be.

**Root Cause:**
`ColorMapper.createSNToColorMap()` uses a simple SN-to-color dictionary with "first occurrence wins" strategy:
```javascript
// Line 98-112 in color_mapper.js
function createSNToColorMap(groups) {
  const snToColor = {};
  groups.forEach((group, index) => {
    const color = getColorForGroup(index);
    group.sns.forEach(sn => {
      if (!snToColor[sn]) {  // ← First occurrence wins
        snToColor[sn] = color;
      }
    });
  });
  return snToColor;
}
```

### Issue 2: Incorrect SN Format in Parsed Section Markers

The parsed output's `:: ::` boundary markers use numeric form (`{<0853>}天<08064>`) instead of preserving the original WH/WAH prefix form (`{<WH0853>}天<WH08064>`).

**Example from Gen 1:1 parsed output:**
```
Current:  {<WH0853>}<WH08064> — 冠詞... ::{<0853>}天<08064>::
Expected: {<WH0853>}<WH08064> — 冠詞... ::{<WH0853>}天<WH08064>::
                                            ^^^       ^^^
                                            Missing WH prefix
```

**Root Cause:**
The parser (`parse_verse_v1_8.py`) strips WH/WAH prefixes during normalization and doesn't preserve them for the `:: ::` markers.

## Proposed Solution

### Solution 1: Position-Based Color Mapping

Replace SN-to-color mapping with position-based group coloring:

1. When parsing raw text, track each SN's position and which group it belongs to
2. Color SNs based on their group membership in that specific position, not just the SN code
3. Fall back to SN-based mapping only when position matching fails

**Implementation approach:**
- Modify `applyColorsToRawText()` to iterate through groups sequentially
- Match raw text SNs against group patterns in order
- Assign colors based on group index, not SN code
- Handle edge cases (SNs not in any group, partial matches)

### Solution 2: Preserve WH/WAH Prefixes in Markers

Update parser output to include WH/WAH prefixes in `:: ::` markers:

1. Modify `parse_verse_v1_8.py` to preserve original prefix form
2. Store both normalized (for grouping logic) and original (for output) forms
3. Use original form in the `:: ::` marker generation

**Implementation approach:**
- Add `original_form` field to token data structures
- Preserve WH/WAH/WTH prefixes alongside normalized numeric codes
- Generate `:: ::` markers using original_form instead of normalized codes

## Impact Assessment

**Breaking Changes:** None - these are bug fixes that correct existing incorrect behavior

**User-Visible Changes:**
- Colors in left panel will now correctly reflect group boundaries from parsed output
- Parsed output `:: ::` markers will match the format of the main group display

**Performance Impact:** Minimal - position-based matching adds one sequential scan per verse

## Alternatives Considered

### Alternative 1: Multi-color support for repeated SNs
Allow a single SN to have multiple colors based on group context. **Rejected:** Too complex, breaks the mental model that same SN = same color.

### Alternative 2: Don't color repeated SNs
Leave repeated SNs uncolored to avoid ambiguity. **Rejected:** Loss of visual grouping information.

### Alternative 3: Use different marker format
Change `:: ::` to show groups without SN codes. **Rejected:** Reduces information density and usefulness for cross-referencing.

## Dependencies

- Requires understanding of viewer_v2 color mapping architecture
- Depends on parsed output format from `parse_verse_v1_8.py`
- Must maintain compatibility with existing highlighting and click handlers

## Success Criteria

1. Object marker `{<0853>}` instances in different groups receive different colors
2. All `:: ::` markers use WH/WAH/WTH prefix format matching the main output
3. Clicking an SN in left panel highlights correct group in right panel
4. Color mapping remains consistent within each group
5. No regression in existing Single HL mode or bidirectional highlighting features
