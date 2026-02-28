# Proposal: Fix Viewer Greedy Morphology Pattern

## Problem Statement

In Gen 1:6, the parsed output shows `<WAH09001><WH04325>` as ONE group containing two SNs: ['09001', '04325']. However, in the raw text, they appear as two separate braced tokens: `{<WAH09001>}{<WH04325>}`.

**Current Behavior:**
- Clicking `{<WAH09001>}` on left panel → right panel's `<WAH09001><WH04325>` highlights correctly ✅
- Clicking `{<WH04325>}` on left panel → right panel's `<WAH09001><WH04325>` does NOT highlight ❌
- Instead, other single instances of `<WH04325>` highlight

**Root Cause:**
The morphology code pattern `\{?<W[AT]*H?\d+>\}?` is too greedy. When processing `{<WAH09001>}{<WH04325>}`, the pattern for the first SN (09001) consumes BOTH tokens:
- `{<WAH09001>}` matches as the core SN
- `{<WH04325>}` is incorrectly matched as a "morphology code" (because `\d+` matches any digits)

This leaves nothing for the second SN pattern to match, causing the two tokens to be colored with different groups instead of the same group color.

## Proposed Solution

Make the morphology code pattern more specific to only match actual morphology codes, which are:
1. **WTH-prefixed tags**: `<WTH8xxx>` - always 4 digits starting with 8
2. **Parenthesized codes**: `(8xxx)` or `(**8xxx)` - always 4 digits starting with 8

**Pattern Change:**
- **Current**: `(\{?<W[AT]*H?\d+>\}?|\(\*?\*?\d+\))?`
- **Proposed**: `(\{?<WTH8\d{3}>\}?|\(\*?\*?8\d{3}\))?`

This ensures:
- ✅ Matches `{<WTH8799>}`, `<WTH8799>` (braced/unbraced morphology)
- ✅ Matches `(8799)`, `(**8799)` (parenthesized morphology)
- ❌ Does NOT match `{<WH04325>}` (core SN)
- ❌ Does NOT match `{<WAH09001>}` (prefixed core SN)

## Expected Outcome

After the fix, clicking `{<WH04325>}` on the left panel will correctly:
1. Identify it belongs to the group ['09001', '04325']
2. Highlight the right panel's `<WAH09001><WH04325>` in orange
3. Highlight both `{<WAH09001>}` and `{<WH04325>}` on the left in blue (as they share the same group color)

## Affected Files

- `viewer_v2/js/color_mapper.js` - 4 functions need pattern updates

## Dependencies

None - this is a self-contained bug fix.

## Risks

Low risk. The change makes the pattern more restrictive, which could only:
- Fix the current bug (intended)
- Potentially not match some edge case morphology format (but WTH8xxx and (8xxx) are the only formats used in the data)
