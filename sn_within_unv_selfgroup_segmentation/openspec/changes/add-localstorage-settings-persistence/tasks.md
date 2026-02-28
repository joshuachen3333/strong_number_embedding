# Implementation Tasks

## 1. HTML Structure

- [ ] 1.1 Add SN Dict toggle checkbox to header
  - Add to `.header-right` section in index.html
  - Add `<input type="checkbox" id="sn-dict-toggle">`
  - Add `<label for="sn-dict-toggle">SN Dict</label>`
  - Position before other toggle buttons

## 2. CSS Styling

- [ ] 2.1 Style SN Dict checkbox (if needed)
  - Ensure consistent styling with existing Single HL checkbox
  - Add appropriate spacing/gap

## 3. localStorage Utility Functions

- [ ] 3.1 Create settings persistence helper in right_panel.js
  - Define localStorage key constants:
    - `STORAGE_KEY_SN_TOOLTIP = 'viewer_v2_sn_tooltip_enabled'`
    - `STORAGE_KEY_SHOW_PARSED = 'viewer_v2_show_parsed'`
    - `STORAGE_KEY_SHOW_RAW = 'viewer_v2_show_raw'`
    - `STORAGE_KEY_SHOW_NOTES = 'viewer_v2_show_notes'`
  - Create `loadSetting(key, defaultValue)` function with try/catch for localStorage errors
  - Create `saveSetting(key, value)` function with try/catch

## 4. Section Toggle Persistence (right_panel.js)

- [ ] 4.1 Load saved toggle states on init
  - Call `loadSetting()` for each toggle
  - Apply to `showParsed`, `showRaw`, `showNotes` variables
  - Update button active states to match

- [ ] 4.2 Change default values
  - `showParsed = true` (keep current default)
  - `showRaw = false` (change from true)
  - `showNotes = false` (change from true)

- [ ] 4.3 Save toggle states on change
  - In toggle button click handlers, call `saveSetting()` after state change
  - Save before calling `render()` to ensure persistence

- [ ] 4.4 Update toggle button UI on load
  - Ensure `.active` class matches loaded state
  - Call `classList.toggle('active', showParsed)` etc. on init

## 5. SN Tooltip Toggle (sn_dictionary.js)

- [ ] 5.1 Add enabled state variable
  - Declare `let tooltipEnabled = false` (default OFF)

- [ ] 5.2 Load saved state on init
  - Read from localStorage on module initialization
  - Use same `loadSetting()` pattern (or inline try/catch)

- [ ] 5.3 Check enabled before showing tooltip
  - In `handleSNClick()`, return early if `!tooltipEnabled`
  - Log message for debugging: `[SNDictionary] Tooltip disabled, skipping`

- [ ] 5.4 Listen for checkbox changes
  - Get checkbox element reference
  - Add change event listener
  - Update `tooltipEnabled` and save to localStorage on change

- [ ] 5.5 Initialize checkbox state on load
  - Set checkbox `.checked` to match loaded `tooltipEnabled` value

## 6. Testing

- [ ] 6.1 Test default state (first visit / cleared localStorage)
  - Clear localStorage for viewer_v2 keys
  - Refresh page
  - Verify: Parsed ON, Raw OFF, Notes OFF, SN Dict OFF
  - Verify toggle buttons reflect these states

- [ ] 6.2 Test section toggle persistence
  - Toggle Raw ON, Notes ON
  - Refresh page
  - Verify: Raw and Notes still ON

- [ ] 6.3 Test SN Tooltip toggle persistence
  - Check "SN Dict" checkbox
  - Click an SN, verify tooltip appears
  - Refresh page
  - Verify: SN Dict checkbox still checked
  - Click an SN, verify tooltip still appears

- [ ] 6.4 Test SN Tooltip disabled state
  - Uncheck "SN Dict" checkbox
  - Click an SN
  - Verify: No tooltip appears
  - Refresh page
  - Verify: SN Dict still unchecked, no tooltip on SN click

- [ ] 6.5 Test verse navigation preserves toggle states
  - Set specific toggle configuration
  - Navigate to different verse
  - Verify: Toggle states unchanged

- [ ] 6.6 Test localStorage error handling
  - Test in private browsing mode (if possible)
  - Verify: No console errors, defaults applied gracefully

## 7. Cache Busting

- [ ] 7.1 Update version query parameters
  - Update index.html script tags with new version string
  - Ensure changes are picked up on reload

## Dependencies

- Tasks 1-2 can be done in parallel with task 3
- Task 4 depends on task 3 (utility functions)
- Task 5 depends on task 1 (checkbox in HTML) and task 3 (utility pattern)
- Task 6 depends on all implementation tasks (1-5)
- Task 7 should be done after all implementation is complete
