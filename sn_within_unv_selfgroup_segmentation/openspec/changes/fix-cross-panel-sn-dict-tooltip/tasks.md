## 1. Add helper to check left panel checkbox state

- [x] 1.1 Add `getLeftPanelSNDictEnabled(element)` function in sn_dictionary.js
  - Takes the highlighted element as parameter
  - Checks if element is inside `.unv-section` → return `unv-sn-dict-toggle` checkbox state
  - Checks if element is inside `.kjv-section` → return `kjv-sn-dict-toggle` checkbox state
  - Returns false if element is null or not in either section

## 2. Update cross-panel tooltip logic

- [x] 2.1 Modify `handleSNHighlight()` for right → left case
  - When `isRightPanelSource` and showing left tooltip
  - After finding the highlighted element with `findHighlightedElementInPanel('left', groupSNs)`
  - Call `getLeftPanelSNDictEnabled(leftElement)` to check if tooltip should show
  - Only show tooltip if this returns true

- [x] 2.2 Remove reliance on `leftEnabled` variable for cross-panel case
  - The `leftEnabled` variable is now unused (can keep for backwards compatibility)
  - Cross-panel tooltip controlled by per-version checkbox lookup

## 3. Update cache buster

- [x] 3.1 Update sn_dictionary.js version in index.html

## 4. Verify

- [x] 4.1 Test: Click SN in right panel with UNV SN Dict checked → tooltip shows on left (UNV)
- [x] 4.2 Test: Click SN in right panel with UNV SN Dict unchecked → no tooltip on left
- [x] 4.3 Test: Click SN in right panel with KJV visible and KJV SN Dict checked → tooltip shows
- [x] 4.4 Test: Existing behavior unchanged - left panel click still works correctly
