# Tasks: Context-Aware Hotkeys

## Implementation Order

### Phase 1: Active Panel State Management

- [x] **1.1** Add `activePanel` state variable to `navigation.js` with default value `'left'`
- [x] **1.2** Add `selectedGroupIndex` state variable to track current SN group selection (-1 = none)
- [x] **1.3** Add mouseenter event listeners to `.left-panel` and `.right-panel` to update `activePanel`
- [x] **1.4** Verify: Hover between panels and log `activePanel` value to console

### Phase 2: Right Panel SN Group Clickability

- [x] **2.1** Modify `right_panel.js` to make SN groups clickable (add click event listener)
- [x] **2.2** On SN group click: set `activePanel = 'right'` and update `selectedGroupIndex`
- [x] **2.3** Add CSS class `.keyboard-selected` with visible border/outline style
- [x] **2.4** Add `highlightSelectedGroup(index)` function to apply/remove `.keyboard-selected`
- [x] **2.5** Verify: Click on SN group → should show selection highlight

### Phase 3: Context-Aware Keyboard Handler

- [x] **3.1** Refactor `initKeyboard()` to check `activePanel` before handling keys
- [x] **3.2** Extract existing key handlers into `handleLeftPanelKeys(e)` function
- [x] **3.3** Create `handleRightPanelKeys(e)` function with SN group navigation logic
- [x] **3.4** Implement `navigatePreviousGroup()` - select previous SN group or go to previous verse
- [x] **3.5** Implement `navigateNextGroup()` - select next SN group or go to next verse
- [x] **3.6** Implement `navigateFirstGroup()` - select first SN group (Home key)
- [x] **3.7** Implement `navigateLastGroup()` - select last SN group (End key)
- [x] **3.8** Wire ←/→ in right panel mode to call existing verse navigation functions

### Phase 4: Cross-Panel Highlighting Integration

- [x] **4.1** When SN group is keyboard-selected, extract its SN codes
- [x] **4.2** Trigger existing bidirectional highlighting to show corresponding left panel tags
- [x] **4.3** Clear previous keyboard selection when selecting new group
- [x] **4.4** Verify: Press ↓ in right panel → both panels highlight corresponding SNs

### Phase 5: Edge Cases and Polish

- [x] **5.1** Handle verse change: reset `selectedGroupIndex` when verse changes
- [x] **5.2** Handle empty parsed section: fall back to verse navigation
- [x] **5.3** Handle Parsed section toggle off: switch to left panel mode
- [x] **5.4** Ensure smooth transition when using ↑ at first group → previous verse's last group
- [x] **5.5** Ensure smooth transition when using ↓ at last group → next verse's first group

### Phase 6: Testing and Validation

- [x] **6.1** Test left panel hover + all hotkeys work as before
- [x] **6.2** Test right panel hover + ↑↓ navigate SN groups
- [x] **6.3** Test right panel + ←→ navigate verses
- [x] **6.4** Test right panel + Home/End select first/last group
- [x] **6.5** Test boundary cases (first/last group, first/last verse)
- [x] **6.6** Test click on left panel SN switches back to left panel mode
- [x] **6.7** Test with different verses that have varying numbers of SN groups

## Dependencies

- Tasks 2.x depend on 1.x (need state management first)
- Tasks 3.x depend on 2.x (need clickable groups first)
- Tasks 4.x depend on 3.x (need keyboard navigation first)
- Tasks 5.x and 6.x can be done in parallel after 4.x

## Verification Commands

```bash
# Start the viewer
cd /Users/joshua/work/strong_number_embedding/sn_within_unv_selfgroup_segmentation
python3 -m http.server 8000
# Open http://localhost:8000/viewer/ in browser
```
