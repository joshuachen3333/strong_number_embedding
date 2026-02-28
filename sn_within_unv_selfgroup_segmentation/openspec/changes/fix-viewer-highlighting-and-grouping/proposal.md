# Proposal: Fix Viewer Highlighting and Grouping

## Change ID
`fix-viewer-highlighting-and-grouping`

## Summary
Fix two UI issues in the Parsed Verse Viewer v2:
1. Selected verse background color interferes with Strong's Number highlighting - replace light blue background with blue border indicators only
2. Morphology codes and braced Strong's numbers not inheriting group colors - extend color application to include all group components

## Why
Users are unable to see Strong's Number color coding when a verse is selected due to the light blue background overlay. Additionally, morphology codes like `(8804)` and braced patterns like `{<0853>}` appear visually disconnected from their semantic groups, reducing the utility of the color-coding system for understanding parsed structure.

## Motivation
Current implementation has two usability issues:
1. When a verse is selected in the left panel, the light blue background (#e3f2fd) makes it difficult to see the color-coded Strong's Numbers
2. Group colors only apply to core Strong's numbers (e.g., `<01254>`) but not morphology codes (e.g., `(8804)`) or braced markers (e.g., `{<0853>}`), breaking visual grouping

## User Impact
**Before:**
- Selected verses have light blue background that obscures SN color coding
- Morphology codes appear visually disconnected from their parent Strong's numbers
- Braced object markers don't show group association

**After:**
- Selected verses show deep blue vertical bars at start/end only, preserving SN visibility
- All components of a semantic group share the same background color
- Visual coherence matches the parsed output formatting

## Scope
**In Scope:**
- Modify CSS for `.verse.selected` to use border-only highlighting
- Update `applyColorsToRawText()` to match morphology codes `(**dddd)` and apply group colors
- Update `applyColorsToRawText()` to match braced patterns `{<WHdddd>}` and apply group colors

**Out of Scope:**
- Changes to color palette or grouping logic
- Modifications to parsed text display (right panel)
- Performance optimization

## Dependencies
None - this is a pure UI fix with no architectural dependencies

## Alternatives Considered
1. **Dim the background instead of removing**: Would still reduce SN visibility
2. **Change SN colors to be more vibrant**: Would affect all verses, not just selected ones
3. **Apply colors only to number portion**: Would create visual inconsistency with braces/parentheses split

## Risks
**Low Risk:**
- CSS-only change for highlighting
- Regex pattern extension for grouping

**Mitigation:**
- Manual testing on multiple verses to verify regex captures all patterns
- Visual inspection of border-only highlighting across different verse lengths

## Success Criteria
1. Selected verse shows deep blue vertical borders (#2196f3) at left and right edges with no background color
2. Morphology codes like `(8804)` inherit the background color of their associated Strong's number `<01254>`
3. Braced patterns like `{<0853>}` inherit the background color of their associated Strong's number
4. All changes preserve existing click handlers and dictionary lookup functionality
