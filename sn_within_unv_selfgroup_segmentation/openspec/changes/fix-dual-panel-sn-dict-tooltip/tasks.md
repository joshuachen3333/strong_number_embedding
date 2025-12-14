## 1. Modify findHighlightedElementInPanel for dual-panel support

- [x] 1.1 Update `findHighlightedElementInPanel()` to use `querySelectorAll` instead of `querySelector`
  - Change from: `container.querySelector('.clicked-remote')`
  - Change to: `container.querySelectorAll('.clicked-remote')`
  - Return the first element whose section has SN Dict enabled

- [x] 1.2 Add section-aware filtering logic
  - For each element found, call `getLeftPanelSNDictEnabled(element)`
  - Return the first element where this returns true
  - If no element has enabled checkbox, return null (or first element for fallback)

## 2. Update cache buster

- [x] 2.1 Update sn_dictionary.js version in index.html (v=20251215C)

## 3. Verify

- [ ] 3.1 Test: Both UNV+KJV visible, UNV SN Dict OFF, KJV SN Dict ON → click right panel SN → tooltip shows on KJV
  - **BLOCKED**: KJV API (bible.fhl.net) returning errors - cannot load KJV data
- [ ] 3.2 Test: Both UNV+KJV visible, UNV SN Dict ON, KJV SN Dict OFF → click right panel SN → tooltip shows on UNV
  - **BLOCKED**: KJV API (bible.fhl.net) returning errors - cannot load KJV data
- [ ] 3.3 Test: Both UNV+KJV visible, both SN Dict ON → click right panel SN → tooltip shows (on first visible)
  - **BLOCKED**: KJV API (bible.fhl.net) returning errors - cannot load KJV data
- [x] 3.4 Test: Only UNV visible, UNV SN Dict ON → tooltip shows on UNV (existing behavior preserved)
  - **PASSED**: Tooltip for H0430 (אֱלֹהִים) appeared correctly
- [ ] 3.5 Test: Only KJV visible, KJV SN Dict ON → tooltip shows on KJV (existing behavior preserved)
  - **BLOCKED**: KJV API (bible.fhl.net) returning errors - cannot load KJV data

## Notes

Implementation is complete. Testing blocked by external KJV API failures.
The code logic has been reviewed and is correct:
1. Uses `querySelectorAll` to find ALL highlighted elements
2. Iterates through elements to find one with SN Dict enabled
3. Returns the correct element for tooltip positioning
