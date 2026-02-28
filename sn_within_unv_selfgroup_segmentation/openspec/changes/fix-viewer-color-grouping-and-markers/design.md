# Design: Fix Viewer Color Grouping and Parsed Output Markers

## Architecture Overview

This change fixes two interconnected issues in the viewer's Strong's Number visualization system:

1. **Color mapping architecture** (viewer_v2/js/color_mapper.js)
2. **Parser output formatting** (parse_verse_v1_8.py)

## Component 1: Position-Based Color Mapping

### Current Architecture

```
Parsed Output → parseGroups() → [{groupIndex, sns: ['0853', '08064']}, ...]
                                         ↓
                                createSNToColorMap()
                                         ↓
                               {'0853': pink, '08064': pink, ...}
                                         ↓
Raw Text → applyColorsToRawText() → Colored HTML
```

**Problem:** `createSNToColorMap()` creates a flat SN-to-color dictionary. When `0853` appears in multiple groups, only the first group's color is stored.

### Proposed Architecture

```
Parsed Output → parseGroups() → [{groupIndex, sns, pattern}, ...]
                                         ↓
Raw Text → applyColorsToRawText() → Match groups sequentially
                                         ↓
                    Color based on group membership, not SN code
                                         ↓
                                    Colored HTML
```

**Key Changes:**
1. `applyColorsToRawText()` iterates through groups in order
2. For each group, find its position in raw text
3. Color all SNs in that text span with the group's color
4. Track which text positions have been colored to avoid conflicts

### Implementation Details

#### Step 1: Build Group Pattern Matcher

```javascript
function buildGroupPatterns(groups) {
  return groups.map((group, index) => ({
    groupIndex: index,
    sns: group.sns,
    pattern: buildRegexPattern(group.sns),  // NEW
    color: getColorForGroup(index)
  }));
}

function buildRegexPattern(sns) {
  // Build regex to match this exact sequence of SNs in raw text
  // Example: ['0853', '08064'] → /\{?<W[ATH]*H?0853>\}?.*?<W[ATH]*H?08064>/
  const snPatterns = sns.map(sn =>
    `\\{?<W[ATH]*H?${sn}>\\}?`
  ).join('.*?');  // Allow Chinese text between SNs
  return new RegExp(snPatterns, 'g');
}
```

#### Step 2: Apply Colors Sequentially

```javascript
function applyColorsToRawText(text, colorMap, groups) {  // Add groups param
  let result = text;
  const coloredRanges = [];  // Track what's been colored

  const groupPatterns = buildGroupPatterns(groups);

  // Process each group in order
  groupPatterns.forEach(({pattern, color, sns}) => {
    let match;
    while ((match = pattern.exec(result)) !== null) {
      // Check if this range overlaps with already-colored text
      if (overlapsColoredRange(match.index, match[0].length, coloredRanges)) {
        continue;
      }

      // Color all SNs in this match
      const colored = colorSNsInText(match[0], sns, color);
      result = replaceRange(result, match.index, match[0].length, colored);

      coloredRanges.push({start: match.index, end: match.index + colored.length});
    }
  });

  return result;
}
```

#### Step 3: Handle Edge Cases

1. **SNs not in any group:** Use fallback color or leave uncolored
2. **Overlapping matches:** First group wins (maintain left-to-right precedence)
3. **Partial matches:** If group pattern doesn't match, fall back to individual SN coloring

### Trade-offs

**Pros:**
- Correctly handles repeated SNs in different groups
- Maintains group-based coloring semantics
- Compatible with existing click handlers

**Cons:**
- More complex than simple dictionary lookup
- Requires sequential processing (but verses are short, so negligible perf impact)
- Pattern matching may fail if raw text format diverges from parsed output

## Component 2: Preserve WH/WAH Prefixes in Markers

### Current Flow

```python
# parse_verse_v1_8.py
raw_text: "{<WH0853>}天<WH08064>"
    ↓
normalize(): Remove WH prefix
    ↓
tokens: [{'sn': '0853', ...}, {'sn': '08064', ...}]
    ↓
format_output(): Generate markers
    ↓
output: "::{<0853>}天<08064>::"  # Missing WH prefix
```

### Proposed Flow

```python
# parse_verse_v1_8.py
raw_text: "{<WH0853>}天<WH08064>"
    ↓
normalize(): Remove WH AND store original
    ↓
tokens: [{'sn': '0853', 'original': '{<WH0853>}', ...},
         {'sn': '08064', 'original': '<WH08064>', ...}]
    ↓
format_output(): Use original form in markers
    ↓
output: "::{<WH0853>}天<WH08064>::"  # Preserves WH prefix
```

### Implementation Details

#### Step 1: Extend Token Data Structure

```python
# In parse_verse_v1_8.py
class Token:
    def __init__(self, raw_text, sn_code, token_type):
        self.sn = sn_code              # Normalized: '0853'
        self.original = raw_text        # Original: '{<WH0853>}'
        self.type = token_type
```

#### Step 2: Preserve Original During Normalization

```python
def normalize_token(raw_token):
    # Current: Extract numeric only
    # Proposed: Extract both normalized and original

    match = re.match(r'\{?<(W[ATH]*H?)(\d+)>\}?', raw_token)
    if match:
        prefix = match.group(1)  # 'WH', 'WAH', 'WTH'
        code = match.group(2)     # '0853'
        return {
            'sn': code,           # Normalized for logic
            'original': raw_token  # Original for display
        }
```

#### Step 3: Update Marker Generation

```python
def format_group_marker(group):
    # Build marker from original forms
    marker_parts = []
    for token in group['tokens']:
        if 'original' in token:
            marker_parts.append(token['original'])
        else:
            # Fallback: reconstruct from normalized
            marker_parts.append(f"<{token['sn']}>")

    return ''.join(marker_parts)

# Usage in output formatting
marker = f"::{format_group_marker(group)}::"
```

### Trade-offs

**Pros:**
- Maintains visual consistency between parsed output and markers
- No loss of information
- Easy to implement (just preserve what's already there)

**Cons:**
- Increases memory footprint slightly (storing both forms)
- Must ensure original form is preserved through entire parsing pipeline

## Integration Points

### Viewer ↔ Parser

The viewer relies on the `:: ::` markers to understand group boundaries. Changing the marker format requires:

1. **Parser update:** Generate markers with WH/WAH prefixes
2. **Viewer update:** Parse markers correctly (should be transparent if we only add prefixes)
3. **Validation:** Ensure marker extraction regex handles prefixed form

**Current marker extraction** (in color_mapper.js):
```javascript
// Extract from: ::{<0853>}天<08064>::
const markerPattern = /::(.*?)::/g;
```

**After change:**
```javascript
// Extract from: ::{<WH0853>}天<WH08064>::
// Same pattern works! No change needed.
```

### Color Mapping ↔ Highlighting

The new position-based coloring must work with existing highlight features:

1. **Single HL mode:** Still clears highlights correctly
2. **Bidirectional highlighting:** Click handlers use SN codes, not colors - no impact
3. **SN tooltips:** Use SN codes, not colors - no impact

**Validation needed:**
- Test clicking SNs in groups with repeated SNs
- Verify group boundaries are respected in all highlight modes

## Rollback Strategy

If position-based coloring causes issues:

1. **Fallback flag:** Add `USE_POSITION_BASED_COLORING` flag in color_mapper.js
2. **Hybrid approach:** Use position-based only for SNs that appear in >1 group
3. **Logging:** Add debug logging to identify pattern matching failures

## Testing Strategy

### Unit Tests

1. **Color mapping:**
   - Single SN in one group → color matches group
   - Same SN in two groups → each gets different color
   - Three groups with overlapping SNs → all colored correctly

2. **Marker generation:**
   - Implicit SN `{<WH0853>}` → marker includes braces and WH prefix
   - Explicit SN `<WH08064>` → marker includes WH prefix
   - Morphology `<WH01254>(8804)` → marker includes both parts with WH prefix

### Integration Tests

1. Load Gen 1:1 → verify `{<WH0853>}` appears in two different colors
2. Click first `{<WH0853>}` → only first group highlights
3. Click second `{<WH0853>}` → only second group highlights
4. Check parsed output markers → all use WH/WAH format

### Visual Regression Tests

1. Screenshot Gen 1:1 before/after
2. Verify color boundaries match group boundaries in parsed output
3. Check that `:: ::` markers are visually consistent with main output
