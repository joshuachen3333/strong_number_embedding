# Implementation Tasks

## 1. HTML Structure

- [ ] 1.1 Add checkbox control to left panel header in index.html
  - Add `<div class="panel-controls">` container
  - Add `<input type="checkbox" id="single-highlight-mode" checked>`
  - Add `<label for="single-highlight-mode">Single HL</label>`
  - Place in `.panel-header` next to `<h2>`

## 2. CSS Styling

- [ ] 2.1 Add `.panel-controls` styles
  - Display: flex with align-items: center
  - Gap: 8px for spacing
  - Margin-left: auto to push to right side

- [ ] 2.2 Style checkbox and label
  - Cursor: pointer for both elements
  - Font-size: 14px for label
  - User-select: none for label (prevent text selection)

## 3. Left Panel Logic

- [ ] 3.1 Add state variable in left_panel.js
  - Declare `let singleHighlightMode = true;`
  - Initialize after other state variables

- [ ] 3.2 Initialize checkbox in init() function
  - Get checkbox element reference
  - Attach change event listener
  - Update singleHighlightMode on change

- [ ] 3.3 Modify handleSNClickForHighlighting()
  - Add conditional check: `if (singleHighlightMode) clearHighlighting();`
  - Ensure clearHighlighting() only called when mode is ON
  - Keep rest of highlighting logic unchanged

- [ ] 3.4 Verify global clear events
  - Confirm handleVerseSelected() always clears (no mode check)
  - Document why verse navigation ignores mode setting

## 4. Right Panel Logic

- [ ] 4.1 Add state variable in right_panel.js
  - Declare `let singleHighlightMode = true;`

- [ ] 4.2 Initialize from checkbox in init() function
  - Get same checkbox element (cross-panel coordination)
  - Attach change event listener
  - Update singleHighlightMode on change

- [ ] 4.3 Modify handleSNClickForHighlighting()
  - Add conditional check: `if (singleHighlightMode) clearHighlighting();`
  - Keep rest of highlighting logic unchanged

- [ ] 4.4 Verify handleVerseSelected() always clears
  - No mode check for verse navigation clearing

## 5. Global Click Handler

- [ ] 5.1 Verify app.js handleGlobalClick() always clears
  - Ensure no mode check in click-away clearing
  - Document that click-away ignores mode for easy reset

## 6. Testing

- [ ] 6.1 Test default state (checkbox checked)
  - Click SN, verify highlighting appears
  - Click different SN, verify first clears and second appears

- [ ] 6.2 Test multi-highlight mode (checkbox unchecked)
  - Uncheck Single HL checkbox
  - Click first SN (e.g., `<0216>`)
  - Click second SN (e.g., `<0430>`)
  - Verify both remain highlighted with proper colors

- [ ] 6.3 Test mode switching with active highlights
  - Highlight an SN in multi-mode
  - Check the Single HL checkbox
  - Verify existing highlights remain until next click
  - Click new SN, verify old clears

- [ ] 6.4 Test click-away in both modes
  - Multi-mode: highlight multiple SNs, click away, verify all clear
  - Single mode: highlight one SN, click away, verify clears

- [ ] 6.5 Test verse navigation in both modes
  - Multi-mode: highlight multiple SNs, navigate to next verse
  - Verify all highlights cleared in new verse
  - Single mode: same test

- [ ] 6.6 Test cross-panel highlighting in multi-mode
  - Highlight left panel SN (left blue, right orange)
  - Highlight right panel SN (right blue, left orange)
  - Verify both sets of highlights coexist

- [ ] 6.7 Test with repeated SNs (Gen 1:4)
  - Multi-mode: highlight `{<0853>}<0216>` group
  - Highlight `<0430>` group
  - Verify both groups highlighted correctly

## 7. Documentation

- [ ] 7.1 Add code comments explaining mode behavior
  - Comment in handleSNClickForHighlighting() explaining conditional
  - Comment in init() explaining cross-panel coordination

- [ ] 7.2 Update viewer README if exists
  - Document Single HL checkbox feature
  - Explain default behavior and multi-highlight capability

## Dependencies

- Task 1 must complete before tasks 2-5 (HTML structure needed first)
- Tasks 3 and 4 can be done in parallel
- Task 5 verification can happen anytime
- Task 6 depends on all implementation tasks (1-5) being complete
