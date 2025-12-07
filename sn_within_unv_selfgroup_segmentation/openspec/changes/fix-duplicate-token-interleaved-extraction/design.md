# Design: Fix Duplicate Token Interleaved Extraction

## Problem Analysis

### Current Behavior

The `extract_interleaved_text()` function searches for tokens using `str.find()`:

```python
for token in tokens_to_find:
    if token.startswith('{<'):
        for prefix_variant in ['{<WH', '{<WAH', '{<WTH']:
            search_token = token.replace('{<', prefix_variant)
            pos = bible_text_raw.find(search_token)  # ← Always returns FIRST match
            if pos != -1:
                positions.append((pos, search_token))
                break
```

**Issue**: When processing Group 2 with `{<0853>}`, `find()` returns position of Group 1's `{<0853>}`.

### Token Position Lifecycle

```
Raw text: {<WH0853>}天<WH08064>{<WH0853>}地<WH0776>
          ↑ pos=0           ↑ pos=20

Group 1: {<0853>}<08064>
  - Searches for {<WH0853>} → finds pos=0 ✓
  - Searches for <WH08064> → finds pos=11 ✓
  - Extracts [0:20] → ::{<0853>}天<08064>:: ✓

Group 2: {<0853>}<0776>
  - Searches for {<WH0853>} → finds pos=0 ✗ WRONG (should find pos=20)
  - Searches for <WH0776> → finds pos=30 ✓
  - Extracts [0:39] → ::{<0853>}天<08064>{<0853>}地<0776>:: ✗
```

## Solution Design

### Strategy: Consumed Position Tracking

Track which character positions in `bible_text_raw` have already been consumed by previous groups. When searching for a token, skip any matches that fall within consumed ranges.

### Implementation Approach

1. **State Container**: Use a set of consumed position ranges
   ```python
   consumed_positions = set()  # Set of (start, end) tuples
   ```

2. **Modified Search**: Add `start_pos` parameter to skip consumed positions
   ```python
   def find_next_unused(text, search_token, consumed_positions, start_from=0):
       """Find next occurrence not in consumed_positions."""
       pos = start_from
       while True:
           pos = text.find(search_token, pos)
           if pos == -1:
               return -1
           end_pos = pos + len(search_token)
           # Check if this position overlaps with any consumed range
           if not any(start <= pos < end or start < end_pos <= end
                      for start, end in consumed_positions):
               return pos
           pos = end_pos  # Try next occurrence
   ```

3. **Mark Consumed**: After successful extraction, mark the range as consumed
   ```python
   consumed_positions.add((first_pos, snippet_end))
   ```

4. **Thread Through Call Chain**:
   ```python
   # In format_groups_to_text()
   consumed_positions = set()
   for group in groups:
       # ...
       interleaved = extract_interleaved_text(group, bible_text_raw, consumed_positions)
       # consumed_positions is mutated in-place
   ```

### Alternative Approach: Occurrence Counter

Instead of position tracking, count which occurrence of each token to use:

```python
token_occurrence_map = {}  # {token: next_occurrence_index}

def find_nth_occurrence(text, search_token, n):
    """Find the nth occurrence (0-indexed)."""
    pos = -1
    for i in range(n + 1):
        pos = text.find(search_token, pos + 1)
        if pos == -1:
            return -1
    return pos
```

**Pros**: Simpler logic
**Cons**: Doesn't handle interleaved tokens correctly (e.g., if tokens appear out of order)

**Decision**: Use position tracking (more robust).

## Data Structures

### ConsumedPositions Set

```python
consumed_positions: Set[Tuple[int, int]]
```

- Each tuple represents a closed interval `[start, end)` of consumed characters
- Mutable set passed through the formatting loop
- Groups mutate it by adding their extracted ranges

### Position Check Logic

```python
def is_position_consumed(pos, length, consumed_positions):
    """Check if position range overlaps any consumed range."""
    end_pos = pos + length
    for consumed_start, consumed_end in consumed_positions:
        # Check overlap: [pos, end_pos) overlaps [consumed_start, consumed_end)
        if pos < consumed_end and end_pos > consumed_start:
            return True
    return False
```

## Function Signatures

### Modified extract_interleaved_text()

```python
def extract_interleaved_text(group, bible_text_raw, consumed_positions=None):
    """
    Extract original text showing SN-Chinese-SN arrangement when tokens are
    interleaved with Chinese characters.

    Args:
        group: Group dict
        bible_text_raw: Raw UNV+SN source text
        consumed_positions: Set of (start, end) tuples marking already-used positions.
                           Modified in-place when extraction succeeds.

    Returns:
        str: Interleaved snippet like "{<0853>}天<08064>" or None if not interleaved
    """
    if consumed_positions is None:
        consumed_positions = set()

    # ... existing logic with modified search ...

    # Mark range as consumed on successful extraction
    consumed_positions.add((first_pos, snippet_end))

    return cleaned
```

### Call Site in format_groups_to_text()

```python
def format_groups_to_text(groups, bible_text_raw):
    """..."""
    output_lines = ["Parsed and Formatted Text Section (SPECIFICATION_v1.8):"]

    consumed_positions = set()  # Track consumed positions across all groups

    for group in groups:
        # ... existing logic ...

        spec_rule = determine_spec_rule(group)
        interleaved = extract_interleaved_text(group, bible_text_raw, consumed_positions)
        formatted_line = format_line_with_annotations(formatted_line, interleaved, spec_rule)

        # ... rest of logic ...
```

## Edge Cases

### Case 1: Three Identical Tokens
```
{<0853>}A<1111>{<0853>}B<2222>{<0853>}C<3333>
```
- Group 1 consumes [0, 15)
- Group 2 searches from 0, skips [0, 15), finds position 15, consumes [15, 30)
- Group 3 searches from 0, skips [0, 15) and [15, 30), finds position 30, consumes [30, 45)

### Case 2: Tokens in Different Order
```
{<0853>}A<1111>B<2222>{<0853>}C<3333>
```
- If Group 1 is `<2222>{<0853>}` (left-to-right in source, but appears second in text)
- Position tracking ensures we find the correct `{<0853>}` at position 20, not position 0

### Case 3: No Duplicate Tokens
```
{<0853>}A<1111>
```
- consumed_positions remains empty or has only one entry
- Behavior identical to current implementation

### Case 4: Failed Extraction
```
Group has {<0853>}<0776> but both already consumed by previous groups
```
- Search returns -1 for all attempts
- Function returns None (same as current behavior)
- No positions added to consumed_positions

## Testing Strategy

### Test Cases

1. **Genesis 1:1** - Two `{<0853>}` groups (天 and 地)
   - Expected: Line 5 shows `::{<0853>}天<08064>::`
   - Expected: Line 6 shows `::{<0853>}地<0776>::`

2. **Genesis 1:4** - Multiple `{<0853>}` object markers
   - Verify each group extracts only its own tokens

3. **Genesis 1:2** - No duplicate tokens
   - Verify no regression in existing behavior

4. **Constructed Test** - Three identical prefix groups
   - Mock verse with `<09002><1111> <09002><2222> <09002><3333>`
   - Verify each extracts correctly

### Validation

```bash
# Parse test verses
python run_parser_temp.py 1 1
python run_parser_temp.py 1 2
python run_parser_temp.py 1 4

# Verify Gen 1:1 line 6
grep "地<0776>" output/Gen/1/1 | grep -v "天<08064>"

# Verify no "uncertain" files
ls output/Gen/1/ | grep uncertain
```

## Rollback Plan

If issues arise:
1. Revert `extract_interleaved_text()` to remove `consumed_positions` parameter
2. Revert call sites in `format_groups_to_text()` to remove position tracking
3. Re-test with Genesis 1:1 to confirm rollback success

## Performance Considerations

**Current**: O(n) per group, where n = length of bible_text_raw
**New**: O(n × m) per group, where m = number of consumed ranges

**Analysis**:
- Typical verse has 5-10 groups
- Typical consumed_positions has 5-10 entries
- String search still dominates (O(n))
- Position overlap check is O(m) but m is small
- Overall impact: negligible

**Optimization not needed** for current use case.
