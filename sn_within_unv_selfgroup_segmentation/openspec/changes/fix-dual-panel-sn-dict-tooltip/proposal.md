# Change: Fix dual-panel SN Dict tooltip (both UNV and KJV visible)

## Why

When BOTH UNV and KJV are visible in the left panel with different SN Dict checkbox states:
- UNV SN Dict: unchecked
- KJV SN Dict: checked

Clicking an SN in the right panel highlights BOTH UNV and KJV sections (orange `.clicked-remote`), but NO tooltip appears on KJV even though its checkbox is enabled.

**Root cause**: `findHighlightedElementInPanel()` uses `querySelector('.clicked-remote')` which returns only the FIRST matching element. Since UNV comes before KJV in the DOM, it always finds UNV first, checks UNV's checkbox (unchecked), and never checks KJV.

```javascript
// Current code - line 647 of sn_dictionary.js
const remoteHighlighted = container.querySelector('.clicked-remote');
// Returns FIRST match (UNV), misses KJV even when KJV has checkbox enabled
```

## What Changes

Modify the cross-panel tooltip logic in `sn_dictionary.js` to:
1. Find ALL elements with `.clicked-remote` in the left panel
2. For each element, check if its section's SN Dict checkbox is enabled
3. Show tooltip on the first element where the checkbox is enabled

## Impact

- Affected file: `viewer_v2/js/sn_dictionary.js`
- No HTML changes needed
- Fixes: KJV tooltip not appearing when both versions visible with mixed checkbox states

## Design Decision

**Option A (Recommended)**: Iterate through all `.clicked-remote` elements
- Use `querySelectorAll` instead of `querySelector`
- Find first element whose section has SN Dict enabled
- Minimal change, preserves existing helper functions

**Option B**: Modify `findHighlightedElementInPanel` to accept a section filter
- More invasive change
- Would require updating all call sites
