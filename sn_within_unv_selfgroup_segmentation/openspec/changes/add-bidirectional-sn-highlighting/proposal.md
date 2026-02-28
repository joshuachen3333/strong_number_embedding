# Proposal: Add Bidirectional SN Highlighting

## Problem Statement

Currently, when users click on Strong's Numbers (SN) in viewer_v2, only a dictionary tooltip appears. There is no visual indication of which SN was clicked or where corresponding SNs appear in other sections. This makes it difficult for users to:

1. Track relationships between SNs across left panel (UNV+SN text) and right panel (Parsed/Raw sections)
2. Understand semantic groupings when the same SN appears multiple times
3. Navigate between different representations of the same verse

The dual_reader_right_editor project successfully implemented bidirectional highlighting with:
- **Deep blue** (#1e88e5) for clicked element (local)
- **Orange** (#ff9800) for corresponding elements (remote)

This UX pattern should be adopted in viewer_v2 to improve usability.

## Proposed Solution

Implement bidirectional SN click highlighting with the following behavior:

### Click Right Parsed Section
- **Right Parsed section** clicked group → Deep blue
- **Right Raw section** corresponding group → Deep blue
- **Left panel** corresponding group → Orange

### Click Right Raw Section
- **Right Raw section** clicked group → Deep blue
- **Right Parsed section** corresponding group → Deep blue
- **Left panel** corresponding group → Orange

### Click Left Panel
- **Left panel** clicked group → Deep blue
- **Right Parsed section** corresponding group → Orange
- **Right Raw section** corresponding group → Orange

## Success Criteria

1. Clicking any SN group highlights it in deep blue and corresponding groups in orange
2. Highlighting persists until another SN is clicked or user clicks elsewhere
3. All three areas (left panel, right Parsed, right Raw) stay synchronized
4. Performance remains smooth with no noticeable lag
5. Existing dictionary tooltip functionality continues to work

## Out of Scope

- Highlighting across different verses (only within current verse)
- Persistent highlighting across page reloads
- Multi-select highlighting
- Customizable highlight colors

## Implementation Approach

1. Add CSS classes `clicked-local` (blue) and `clicked-remote` (orange)
2. Create highlighting manager to handle click events and apply/remove classes
3. Extend SN_CLICK event payload to include source panel information
4. Subscribe to SN_CLICK in all three panels to apply appropriate highlighting
5. Add click handler to Parsed section SN groups (currently only Raw section has handlers)
6. Use existing colorMap to identify corresponding SNs across panels

## Dependencies

- Existing SN_CLICK event system in mediator.js
- Existing colorMap in color_mapper.js
- Current SN tag structure in left_panel.js and right_panel.js

## Risks and Mitigations

**Risk**: Same SN appearing multiple times in verse may cause confusion
- **Mitigation**: Use "first occurrence wins" color strategy already implemented

**Risk**: Click handlers may interfere with existing dictionary tooltip
- **Mitigation**: Use event.stopPropagation() appropriately and test both features together

**Risk**: Highlighting may not clear properly when switching verses
- **Mitigation**: Clear all highlighting on VERSE_SELECTED event
