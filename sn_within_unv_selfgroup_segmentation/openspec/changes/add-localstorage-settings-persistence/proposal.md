# Proposal: Add localStorage Settings Persistence

## Problem Statement

Currently in viewer_v2, user preferences are not persisted across browser sessions:

1. **SN Dictionary Tooltip**: The tooltip feature has no toggle control - it's always active when clicking SNs. Users should be able to disable this feature, and their preference should be remembered.

2. **Section Toggle States**: The Parsed/Raw/Notes toggle buttons in the header reset to all-ON when the page reloads or when navigating to a new verse. Users who prefer specific sections hidden must re-toggle them each time.

## Proposed Solution

Add localStorage persistence for viewer settings:

1. **SN Tooltip Toggle**: Add a checkbox control to enable/disable SN Dictionary Tooltip with localStorage persistence (default OFF)

2. **Section Toggle Persistence**: Save Parsed/Raw/Notes toggle states to localStorage with new defaults:
   - Parsed: ON (default)
   - Raw: OFF (default)
   - Notes: OFF (default)

## User Impact

**Positive:**
- Settings persist across sessions - no need to re-configure each time
- Cleaner default view with only Parsed section showing
- SN Tooltip is optional rather than always-on (reduces visual clutter)
- Consistent with modern web application UX patterns

**Negative:**
- First-time users may not notice SN Tooltip feature is available (mitigated by clear labeling)

## Technical Approach

1. **localStorage Keys**:
   - `viewer_v2_sn_tooltip_enabled` - boolean (default: false)
   - `viewer_v2_show_parsed` - boolean (default: true)
   - `viewer_v2_show_raw` - boolean (default: false)
   - `viewer_v2_show_notes` - boolean (default: false)

2. **UI Addition**: Add "SN Dict" checkbox to header (near other toggle buttons)

3. **Initialization**: Load saved preferences on page load, apply to UI state

4. **Persistence**: Save to localStorage on each toggle change

5. **Tooltip Integration**: Check enabled state before showing tooltip on SN click

## Success Criteria

- All four settings persist across page reloads
- Settings persist across browser sessions (same localStorage domain)
- Toggle buttons reflect saved state on page load
- New defaults apply on first visit (no saved settings)
- SN Tooltip only appears when enabled checkbox is checked

## Risks and Mitigations

**Risk**: localStorage not available (private browsing mode)
**Mitigation**: Graceful fallback to default values, no errors thrown

**Risk**: Users confused why tooltip stopped working
**Mitigation**: Clear "SN Dict" checkbox label indicates the feature state

## Alternatives Considered

1. **Use cookies**: More complex, localStorage is simpler for client-only state
2. **Use sessionStorage**: Would lose settings on browser close
3. **Server-side persistence**: Overkill for a client-side viewer

## Dependencies

- No external dependencies
- Builds on existing toggle button infrastructure
- Builds on existing SN Dictionary tooltip (sn_dictionary.js)

## Affected Files

- `viewer_v2/index.html` - Add SN Dict checkbox
- `viewer_v2/js/right_panel.js` - Add localStorage read/write for toggles
- `viewer_v2/js/sn_dictionary.js` - Add enabled check before showing tooltip
