# Change: Split SN Dict Controls and Add Highlight Timeout

## Why
The current global SN Dict toggle does not provide granular control over which panel displays Strong's Number dictionary tooltips. Additionally, highlights and tooltips persist indefinitely, which can clutter the UI. Users need independent control per panel and automatic cleanup.

## What Changes
- **BREAKING**: Remove global "SN Dict" checkbox from header-right
- Convert "Spec" toggle button to checkbox style (matching SN Dict style)
- Add independent "SN Dict" checkbox to left panel header
- Add independent "SN Dict" checkbox to right panel header
- New left panel header order: `[SN Dict checkbox] [Single HL checkbox]`
- New right panel header order: `[SN Dict checkbox] [Spec checkbox] [Parsed] [Raw] [Notes]`
- Auto-show SN Dict tooltip when SN is highlighted (blue or orange) AND panel's SN Dict is checked
- Change SN Dict tooltip style from popup window to hover-style floating (like Spec tooltip)
- Add 10-second timeout for blue/orange highlights and tooltips
- Highlight/tooltip timeout resets on new highlight actions
- Synchronized highlight cleanup: blue disappears → orange disappears → tooltips disappear

## Impact
- Affected specs: viewer-ui
- Affected code:
  - `viewer_v2/index.html` - Layout changes
  - `viewer_v2/css/styles.css` - Tooltip styling
  - `viewer_v2/js/sn_dictionary.js` - Dual panel support, new tooltip style
  - `viewer_v2/js/left_panel.js` - SN Dict integration
  - `viewer_v2/js/right_panel.js` - SN Dict integration
  - `viewer_v2/js/navigation.js` - Timeout management for highlights
  - `viewer_v2/js/app.js` - Initialization and localStorage persistence
