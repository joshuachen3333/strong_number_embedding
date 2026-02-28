# Change: Fix left panel SN Dict checkbox disconnect

## Why

The SN Dict checkboxes in the left panel (UNV and KJV) do not show tooltips when checked because `sn_dictionary.js` is looking for a non-existent element ID.

**Root cause:** When the UNV/KJV split was implemented, the HTML checkbox IDs changed:
- Old: `left-sn-dict-toggle` (single checkbox)
- New: `unv-sn-dict-toggle` and `kjv-sn-dict-toggle` (per-version checkboxes)

But `sn_dictionary.js` was never updated to use the new IDs.

## What Changes

Option A (Recommended): Use the `snDictEnabled` flag from SN_CLICK event
- `left_panel.js` already passes `snDictEnabled: version === 'unv' ? unvSNDict : kjvSNDict`
- `sn_dictionary.js` should use this flag instead of its own `leftEnabled` variable

Option B: Connect to both UNV and KJV checkboxes
- Add listeners to both `unv-sn-dict-toggle` and `kjv-sn-dict-toggle`
- Track `unvEnabled` and `kjvEnabled` separately
- More complex, requires knowing which version was clicked

## Impact

- Affected file: `viewer_v2/js/sn_dictionary.js`
- No HTML changes needed
- Fixes: Left panel (UNV/KJV) SN Dict tooltips not appearing

## CLAUDE.md Update Required

Yes - this is a case of module disconnect (Anti-Pattern: modules not communicating properly through events). Should be documented.
