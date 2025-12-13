## 1. Tooltip Pool Management
- [x] 1.1 Create tooltip pool (3 tooltips per panel: left-0, left-1, left-2, right-0, right-1, right-2)
- [x] 1.2 Add CSS class for tooltip index (`.sn-tooltip-0`, `.sn-tooltip-1`, `.sn-tooltip-2`)
- [x] 1.3 Implement `hideAllTooltipsForPanel(panel)` to hide all 3 tooltips

## 2. Multi-SN Processing
- [x] 2.1 Modify `handleSNHighlight()` to pass full `groupSNs` array to tooltip functions
- [x] 2.2 Create `showMultipleTooltipsForPanel(panel, element, snCodes[])` function
- [x] 2.3 Fetch all definitions in parallel using `Promise.all()`

## 3. Layout Algorithm
- [x] 3.1 Implement `calculateMultiTooltipPositions(element, tooltipCount)`:
  - 2 tooltips: above + below
  - 3 tooltips: 1 above, 2 below (horizontal) OR 2 above (horizontal), 1 below
- [x] 3.2 Check screen bounds and adjust layout if needed
- [x] 3.3 Ensure tooltips don't overlap each other

## 4. CSS Updates
- [x] 4.1 CSS classes added via JavaScript (`.sn-tooltip-0`, `.sn-tooltip-1`, `.sn-tooltip-2`)
- [x] 4.2 Z-index handled by existing tooltip styles
- [x] 4.3 Update CSS version for cache busting (v=20251212J)

## 5. Testing
- [x] 5.1 Test 2-SN group (e.g., prefix + core) - Verified with Gen 1:6 `<WAH09002><WH08432>`
- [x] 5.2 Test 3-SN group (e.g., prefix + prefix + core) - Verified with Gen 37:10 `<09001><09001><07812>`
- [x] 5.3 Test edge cases near screen boundaries - Top: tooltips below; Bottom: tooltips above ✓
- [x] 5.4 Test single SN (backwards compatibility)

## 6. Bug Fix (discovered during testing)
- [x] 6.1 Fixed `extractSNsFromLine()` regex in color_mapper.js to support both formats:
  - Raw UNV+SN: `<WHxxxx>`, `<WAHxxxx>`, `<WTHxxxx>`
  - Parsed output: `<xxxx>` (no W prefix)
  - Changed pattern from `/<W[ATH]*H?(\d+)>/` to `/<(?:W[ATH]*H?)?(\d+)>/`
