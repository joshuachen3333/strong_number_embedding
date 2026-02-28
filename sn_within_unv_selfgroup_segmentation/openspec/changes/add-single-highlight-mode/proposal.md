# Proposal: Add Single Highlight Mode

## Problem Statement

Currently in viewer_v2, when users click on Strong's Numbers (SNs), the system always clears previous highlighting before applying new highlighting. This "single highlight" behavior is hardcoded and cannot be toggled. Users may want to compare multiple SN groups simultaneously by highlighting them together, which is not currently possible.

## Proposed Solution

Add a "Single HL" (Single Highlight) checkbox control to the left panel header, similar to the existing feature in dual_reader_right_editor. This checkbox will allow users to toggle between:

- **Single HL ON (checked, default)**: Clicking a new SN clears previous highlighting (current behavior)
- **Single HL OFF (unchecked)**: Multiple SN groups can be highlighted simultaneously for comparison

## User Impact

**Positive:**
- Users can compare multiple semantic groups side-by-side
- Maintains current default behavior (single highlight)
- Consistent with dual_reader_right_editor UX patterns
- Enables advanced study workflows (e.g., comparing different prepositions across a verse)

**Negative:**
- None (purely additive feature with backwards-compatible default)

## Technical Approach

1. **UI Addition**: Add checkbox to left panel header with label "Single HL" (default checked)
2. **State Management**: Track single highlight mode state in left_panel.js
3. **Highlighting Logic**: Modify `handleSNClickForHighlighting()` to conditionally skip `clearHighlighting()` when Single HL is OFF
4. **Styling**: Style checkbox consistently with existing toggle buttons in header-right

## Success Criteria

- Checkbox appears in left panel header
- Default state is checked (single highlight mode ON)
- When checked: clicking new SN clears previous highlighting (current behavior)
- When unchecked: multiple SN groups can be highlighted simultaneously
- Click-away still clears all highlights regardless of mode
- Verse navigation still clears all highlights regardless of mode

## Risks and Mitigations

**Risk**: Users might accumulate too many highlights and get confused
**Mitigation**: Click-away and verse navigation always clear highlights, providing easy reset

**Risk**: Multi-highlight mode might visually clash with color grouping
**Mitigation**: Existing blue/orange scheme is distinct enough to differentiate multiple groups

## Alternatives Considered

1. **Always allow multi-highlight**: Would break current single-select UX that users expect
2. **Add "Clear All" button instead**: Doesn't address the core use case of comparing multiple groups
3. **Use Ctrl+Click for multi-select**: More complex interaction, less discoverable

## Dependencies

- Builds on completed `add-bidirectional-sn-highlighting` change
- No external dependencies

## Timeline Estimate

- Implementation: ~30 minutes (small HTML/JS change)
- Testing: ~15 minutes (verify both modes work correctly)
