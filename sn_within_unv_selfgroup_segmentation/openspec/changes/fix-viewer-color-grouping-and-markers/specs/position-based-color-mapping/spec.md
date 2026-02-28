# Spec: Position-Based Color Mapping

## Overview

Replace the current SN-to-color dictionary mapping with position-based group coloring to correctly handle cases where the same Strong's Number appears in multiple groups.

## MODIFIED Requirements

### Requirement: Color Mapping Must Respect Group Boundaries
The color mapping system SHALL assign colors based on group membership in the parsed output, not just Strong's Number codes. When the same SN appears in multiple groups, each occurrence MUST receive the color of its respective group.

#### Scenario: Object Marker in Multiple Groups

**Given** a verse with object marker `{<0853>}` appearing in two different groups:
```
Parsed output:
- Group 0 (pink): {<WH0853>}<WH08064> — 冠詞...
- Group 1 (purple): {<WH0853>}<WH0776> — 冠詞...

Raw text: {<WH0853>}天<WH08064>{<WH0853>}地<WH0776>
```

**When** `ColorMapper.applyColorsToRawText()` processes the raw text

**Then**:
- First `{<WH0853>}` must be colored pink (matching group 0)
- `<WH08064>` must be colored pink (same group)
- Second `{<WH0853>}` must be colored purple (matching group 1)
- `<WH0776>` must be colored purple (same group)

**And** the visual grouping must clearly show two separate groups, not three

#### Scenario: Same Word Appearing Twice (Non-Repeated SN)

**Given** a verse where different words share no SNs:
```
Parsed output:
- Group 0 (blue): <WH0216> — 名詞「光」
- Group 1 (green): <WH0216> — 名詞「光」

Raw text: 光<WH0216>...光<WH0216>
```

**When** `ColorMapper.applyColorsToRawText()` processes the raw text

**Then**:
- First `<WH0216>` must be colored blue (group 0)
- Second `<WH0216>` must be colored green (group 1)

**Note:** This scenario represents the current "first occurrence wins" issue affecting repeated words like "light" in Gen 1:4.

---

### Requirement: Sequential Group Pattern Matching
The color mapping SHALL process groups sequentially in the order they appear in the parsed output, matching group patterns against raw text from left to right.

#### Scenario: Sequential Matching Preserves Order

**Given** parsed output with groups in specific order:
```
Group 0: <WAH09002><WH07225>
Group 1: <WH0430>
Group 2: {<WH0853>}<WH08064>
Group 3: {<WH0853>}<WH0776>
```

**When** applying colors to raw text

**Then**:
- Process groups in index order (0, 1, 2, 3)
- Match each group's SN pattern in the raw text
- Color the matched span with the group's color
- Track colored regions to prevent overlap

#### Scenario: Overlapping Matches Use First-Match Priority

**Given** two groups whose patterns could match the same text span

**When** both patterns match overlapping positions

**Then**:
- The first group (lower index) wins
- The overlapped region is marked as colored
- The second group's pattern skips this region

---

### Requirement: Fallback to SN-Based Coloring
When position-based pattern matching fails to color an SN, the system SHALL fall back to SN-based color mapping as a safety net.

#### Scenario: Unmatched SN Gets Fallback Color

**Given** an SN in raw text that doesn't match any group pattern

**When** all group patterns have been processed

**Then**:
- System checks if this SN has an entry in the SN-to-color map
- If yes, applies that color
- If no, leaves the SN uncolored (no background)

**And** logs a warning to console for debugging

#### Scenario: Pattern Match Failure Due to Format Divergence

**Given** raw text format differs slightly from parsed output (e.g., extra whitespace)

**When** group pattern fails to match

**Then**:
- Individual SNs within that group fall back to SN-based coloring
- Console warning indicates pattern mismatch
- User still sees colored SNs (though possibly not perfectly grouped)

---

## ADDED Requirements

### Requirement: Build Group Regex Patterns
The system SHALL generate regex patterns from parsed groups that MUST match the corresponding SN sequences in raw text.

#### Scenario: Simple Group Pattern

**Given** a group with SNs `['09002', '07225']`

**When** `buildRegexPattern(sns)` is called

**Then** it must return a regex like:
```javascript
/\{?<W[ATH]*H?09002>\}?.*?\{?<W[ATH]*H?07225>\}?/g
```

**That matches:**
- `<WAH09002><WH07225>`
- `{<WAH09002>}{<WH07225>}` (implicit forms)
- With optional Chinese characters between SNs

#### Scenario: Group with Morphology

**Given** a group with SNs `['01254', '8804']` (verb + morphology)

**When** pattern is generated

**Then** it must match:
```
<WH01254><WTH8804>
<WH01254>(**8804)
{<WH01254>}(8804)
```

#### Scenario: Group with Brace-Wrapped SN

**Given** a group with SNs `['0853', '08064']` (object marker + noun)

**When** pattern is generated

**Then** it must match:
```
{<WH0853>}<WH08064>
{<WH0853>}天<WH08064>  (with Chinese between)
```

---

### Requirement: API Changes
The `applyColorsToRawText()` function signature SHALL change to accept group information.

#### Scenario: Updated Function Signature

**Given** the current signature:
```javascript
function applyColorsToRawText(text, snToColorMap)
```

**When** implementing position-based coloring

**Then** the signature must become:
```javascript
function applyColorsToRawText(text, snToColorMap, groups)
```

**Where:**
- `text` - raw UNV+SN text
- `snToColorMap` - SN-to-color dictionary (for fallback)
- `groups` - array of `{groupIndex, sns, text}` from `parseGroups()`

#### Scenario: Backward Compatibility

**Given** existing call sites may not pass `groups` parameter

**When** `groups` is undefined or null

**Then**:
- Function falls back to original SN-based mapping
- No errors thrown
- Console warning logged about missing groups parameter

---

## Implementation Notes

### Regex Pattern Construction

The pattern must handle:
1. Optional braces: `\{?` and `\}?`
2. Variable prefixes: `W`, `WH`, `WAH`, `WTH`
3. Optional morphology: `(**\d+)` or `(\d+)`
4. Chinese text between SNs: `.*?` (non-greedy)

### Performance Considerations

- Verses are typically <50 SNs, so sequential matching is O(n*m) where n=groups, m=text_length
- Regex compilation should be cached per group
- Early termination when all groups matched

### Edge Cases

1. **Empty groups:** Skip pattern matching
2. **Single-SN groups:** Pattern matches just that SN
3. **Non-contiguous groups:** Pattern must allow arbitrary text between SNs
4. **Duplicate groups:** First occurrence wins

## Related Capabilities

- `preserve-wh-prefixes-in-markers` - Marker format must match colored output
- Single HL mode - Must still respect verse boundaries when coloring
- Bidirectional highlighting - Click handlers use SN codes, unaffected by color changes

## Migration Path

### Phase 1: Implement with Feature Flag

```javascript
const USE_POSITION_BASED_COLORING = true;  // Toggle for rollback

function applyColorsToRawText(text, snToColorMap, groups) {
  if (!USE_POSITION_BASED_COLORING || !groups) {
    return applyColorsToRawTextLegacy(text, snToColorMap);
  }
  // New implementation
}
```

### Phase 2: Remove Feature Flag

After 1 week of successful operation, remove legacy code path and feature flag.

## Success Metrics

1. **Correctness:** Gen 1:1 shows `{<0853>}` in two different colors
2. **Performance:** Color application <10ms per verse
3. **Robustness:** No uncolored SNs in any verse
4. **Compatibility:** No regressions in highlighting features
