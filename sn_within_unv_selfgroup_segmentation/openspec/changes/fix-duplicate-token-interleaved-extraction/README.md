# Fix Duplicate Token Interleaved Extraction

## Overview

This change fixes the bug where `extract_interleaved_text()` extracts text from the first occurrence of duplicate tokens instead of the occurrence belonging to the current group.

## Problem

When a verse contains multiple groups with identical tokens (e.g., two `{<0853>}` object markers), the extraction function uses `str.find()` which always returns the first match. This causes later groups to incorrectly include tokens from earlier groups.

**Example (Genesis 1:1):**
```
Group 1: {<0853>}<08064> — "天"
  Current: ::{<0853>}天<08064>:: ✓

Group 2: {<0853>}<0776> — "地"
  Current: ::{<0853>}天<08064>{<0853>}地<0776>:: ✗ (includes Group 1's tokens)
  Expected: ::{<0853>}地<0776>:: ✓
```

## Solution

Implement position tracking to mark which character ranges in the raw text have been consumed by previous groups. When searching for tokens, skip any matches that overlap with consumed ranges.

**Key Changes:**
1. Add `consumed_positions` set to track used ranges
2. Modify token search to skip consumed positions
3. Mark successfully extracted ranges as consumed
4. Thread tracking state through formatting loop

## Files Modified

- `parse_verse_v1_8.py`:
  - Add `_is_position_consumed()` helper (~line 690)
  - Add `_find_next_unused_position()` helper (~line 695)
  - Modify `extract_interleaved_text()` signature and logic (~line 700)
  - Initialize `consumed_positions` in `format_groups_to_text()` (~line 874)
  - Pass `consumed_positions` to extraction calls (~lines 954, 1017)

## Testing

**Primary Test:** Genesis 1:1
- Line 6 should show `::{<0853>}地<0776>::` (not including 天)

**Additional Tests:**
- Genesis 1:4 (multiple object markers)
- Genesis 1:2, 1:5, 3:5, 4:16 (regression - no duplicate tokens)

## Status

📋 **Proposal Complete** - Ready for implementation via `/openspec:apply`

## Related Changes

- Depends on: `add-spec-references-to-output` (provides `extract_interleaved_text()` function)
