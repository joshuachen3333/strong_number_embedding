## Context
The viewer_v2 application displays parsed UNV+SN biblical text with bidirectional highlighting between left (source text) and right (parsed output) panels. Currently, there is a single global SN Dict toggle that affects tooltip display for both panels. Users want independent control per panel.

## Goals / Non-Goals
- Goals:
  - Independent SN Dict control for each panel
  - Hover-style floating tooltips (consistent with Spec tooltip)
  - Automatic cleanup of highlights and tooltips after 10 seconds
  - Synchronized cleanup order for better UX

- Non-Goals:
  - Different tooltip content per panel (both use same dictionary)
  - Customizable timeout duration (hardcoded 10s)
  - Different tooltip styles per panel

## Decisions

### Decision 1: Panel-specific SN Dict State
- Store two separate boolean states: `leftSnDictEnabled` and `rightSnDictEnabled`
- Each panel's checkbox controls only its own tooltip display
- Both panels can be enabled/disabled independently

### Decision 2: Hover-style Tooltip Implementation
- Reuse the `spec-tooltip-container` CSS class styling pattern
- Create new `sn-dict-tooltip-container` class with similar positioning logic
- Position tooltip near the highlighted element (not as popup modal)
- Tooltip follows the highlighted element's position

### Decision 3: Unified Timeout Manager
- Create a single timeout manager in a shared location (mediator or app.js)
- Timer ID stored globally, cleared and reset on each new highlight
- Timeout callback triggers synchronized cleanup:
  1. Clear local (blue) highlights
  2. Clear remote (orange) highlights
  3. Hide all SN Dict tooltips

### Decision 4: Auto-show Tooltip Trigger
- Subscribe to mediator events for highlight changes
- When a highlight is applied AND that panel's SN Dict is checked:
  - Extract SN code from highlighted element
  - Show tooltip for that SN near the highlighted element
- Works for both keyboard navigation (blue) and click highlights (blue/orange)

## Risks / Trade-offs
- **Risk**: Multiple tooltips could appear simultaneously (left and right both enabled)
  - Mitigation: Only show tooltip for the panel where the highlight originated
- **Risk**: Tooltip positioning edge cases near screen boundaries
  - Mitigation: Reuse Spec tooltip's positioning logic which handles this

## Migration Plan
1. Remove global SN Dict checkbox from header-right
2. Add panel-specific checkboxes
3. Update localStorage keys (old key ignored, new keys used)
4. No data migration needed - settings reset to defaults

## Open Questions
- None - requirements fully specified
