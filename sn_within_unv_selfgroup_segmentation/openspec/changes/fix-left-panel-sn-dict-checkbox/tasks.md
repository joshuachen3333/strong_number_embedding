## 1. Fix SN Dict tooltip for left panel

- [ ] 1.1 In `sn_dictionary.js:handleSNHighlight()`, use `data.snDictEnabled` for left panel clicks
  - Currently checks `leftEnabled` (connected to non-existent `left-sn-dict-toggle`)
  - Should use `data.snDictEnabled` which is passed from `left_panel.js`
  - For `source === 'left'`, show tooltip if `data.snDictEnabled === true`

- [ ] 1.2 Remove dead code referencing `left-sn-dict-toggle`
  - Remove lines 77-88 that look for non-existent checkbox
  - Remove `leftEnabled` variable or repurpose it

- [ ] 1.3 Keep right panel behavior unchanged
  - Right panel still uses `right-sn-dict-toggle` checkbox
  - `rightEnabled` variable still works correctly

## 2. Update cache buster

- [ ] 2.1 Update sn_dictionary.js version in index.html

## 3. Update CLAUDE.md

- [ ] 3.1 Add Anti-Pattern: Module disconnect
  - Document the pattern where HTML IDs change but JS is not updated
  - Add to Pre-Task Checklist: "When changing HTML IDs, grep for old IDs in JS"

## 4. Verify

- [ ] 4.1 Test UNV SN Dict checkbox - should show tooltip when enabled
- [ ] 4.2 Test KJV SN Dict checkbox - should show tooltip when enabled
- [ ] 4.3 Test right panel SN Dict checkbox - should still work
- [ ] 4.4 Test cross-panel highlighting still shows tooltips correctly
