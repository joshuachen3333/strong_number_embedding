# Change: Fix cross-panel SN Dict tooltip (right → left)

## Why

When clicking an SN in the right panel, the left panel correctly shows orange highlighting on the corresponding SN. However, even when the left panel's SN Dict checkbox is checked, no tooltip appears on the left panel.

**Root cause**: The recent fix for left panel SN Dict (commit `f21d166`) uses `snDictEnabled` from the event data for left panel clicks, but falls back to `leftEnabled` (always false) for cross-panel clicks from the right panel.

```javascript
// Current code - line 152 of sn_dictionary.js
const leftEnabledForThisClick = isLeftPanelSource ? snDictEnabled : leftEnabled;
// When isLeftPanelSource is false, leftEnabled is always false (no checkbox sets it)
```

## What Changes

For cross-panel highlighting (right → left), `sn_dictionary.js` should:
1. Find which section (UNV or KJV) received the orange highlight
2. Check that section's SN Dict checkbox state
3. Show tooltip only if that checkbox is checked

## Impact

- Affected file: `viewer_v2/js/sn_dictionary.js`
- No HTML changes needed
- Fixes: Tooltip not appearing on left panel when clicking SN in right panel

## Design Decision

**Option A (Recommended)**: Query checkbox state directly in sn_dictionary.js
- Add helper function to check UNV/KJV checkbox based on highlighted element's container
- Simple, self-contained fix

**Option B**: Have left_panel.js publish which version got highlighted
- Requires modifying the highlighting flow to track version info
- More complex, changes multiple modules
