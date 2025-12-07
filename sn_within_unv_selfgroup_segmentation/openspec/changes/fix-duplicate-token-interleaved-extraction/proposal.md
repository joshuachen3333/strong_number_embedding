# Proposal: Fix Duplicate Token Interleaved Extraction

## Why

**Problem**: When multiple groups contain identical tokens (e.g., two groups both starting with `{<0853>}`), the `extract_interleaved_text()` function incorrectly extracts text from the FIRST occurrence instead of the occurrence that belongs to the current group.

**Example** (Genesis 1:1):
```
Group 1: {<0853>}<08064> — "天"
  Expected: ::{<0853>}天<08064>::
  Actual: ::{<0853>}天<08064>::  ✓ Correct

Group 2: {<0853>}<0776> — "地"
  Expected: ::{<0853>}地<0776>::
  Actual: ::{<0853>}天<08064>{<0853>}地<0776>::  ✗ Wrong - includes previous group's tokens
```

**Root Cause**: The function uses `str.find()` which always returns the first match. When processing Group 2, it finds the first `{<0853>}` (from Group 1) instead of the second `{<0853>}` (from Group 2).

**Impact**:
- Display issue only - parsing/grouping logic remains correct
- Spec references are correct
- Interleaved text shows expanded context including previous groups' tokens
- Confusing for users reviewing output

## Summary

Fix the `extract_interleaved_text()` function in `parse_verse_v1_8.py` to track which token positions have already been consumed by previous groups, ensuring each group's interleaved text extraction only uses tokens belonging to that specific group.

## Motivation

1. **Correctness**: Each group's interleaved text should show only the tokens from that group, not tokens from previous groups
2. **User Experience**: Current behavior is confusing when reviewing parsed output
3. **Reliability**: Duplicate tokens are common (e.g., multiple `{<0853>}` object markers in a verse)
4. **Maintainability**: The fix should be localized to the extraction function without affecting other parsing logic

## Scope

**In Scope**:
- Modify `extract_interleaved_text()` function to track consumed token positions
- Pass tracking state through the formatting loop in `format_groups_to_text()`
- Handle all token types (prefixes, pre_brace, core, post_brace)
- Test with verses containing duplicate tokens

**Out of Scope**:
- Changes to grouping logic or other parsing rules
- Changes to spec reference determination
- Changes to output formatting (alignment, delimiters)
- Performance optimization beyond the immediate fix

## Constraints

- Must maintain backward compatibility with existing output format
- Should not change the signature of `format_line_with_annotations()`
- Must work with all existing test cases
- Should add minimal complexity to the codebase

## Success Criteria

1. Genesis 1:1 line 6 shows `::{<0853>}地<0776>::` instead of `::{<0853>}天<08064>{<0853>}地<0776>::`
2. All multi-token groups with duplicate tokens extract only their own tokens
3. No regression in existing test cases (Gen 1:2, 1:4, 1:5, 3:5, 4:16)
4. No changes to spec references or other output sections

## Alternatives Considered

### Alternative 1: Use regex with position tracking
- **Pros**: More precise matching
- **Cons**: Adds complexity, regex escaping needed for token strings

### Alternative 2: Build full token→position map upfront
- **Pros**: Could enable other features later
- **Cons**: Over-engineered for current need, breaks encapsulation

### Alternative 3: Accept limitation and document
- **Pros**: No code changes
- **Cons**: Poor user experience, confusing output

**Chosen Approach**: Track consumed positions via mutable set passed through formatting loop (simple, localized, sufficient).

## Dependencies

- Depends on existing `extract_interleaved_text()` implementation from `add-spec-references-to-output` change
- No external dependencies

## Risks

- **Low Risk**: Change is localized to extraction function
- **Mitigation**: Comprehensive testing with verses containing duplicate tokens
- **Rollback**: Easy - revert single function and its call sites
