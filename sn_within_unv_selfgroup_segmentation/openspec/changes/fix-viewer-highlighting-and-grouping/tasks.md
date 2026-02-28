# Tasks: Fix Viewer Highlighting and Grouping

## Task Breakdown

### 1. Update Selected Verse Styling (css/styles.css)
**Description:** Replace light blue background with deep blue vertical borders only

**Steps:**
- Remove `background-color: #e3f2fd;` from `.verse.selected`
- Add `border-right: 3px solid #2196f3;` to create right-side indicator
- Verify left border already exists (update if needed to ensure visibility)

**Validation:**
- Click on various verses in left panel
- Confirm selected verse shows blue vertical bars at both edges with no background
- Confirm Strong's Number colors remain fully visible on selected verses

**Files:**
- `viewer_v2/css/styles.css` (lines ~165-168)

---

### 2. Extend Color Application to Morphology Codes (js/color_mapper.js)
**Description:** Update regex pattern to capture and color morphology codes alongside their Strong's numbers

**Steps:**
- Modify `applyColorsToRawText()` regex pattern to include `(**dddd)` patterns
- Update pattern from `/(\{?<W[ATH]*H?(\d+)>\}?)/g` to capture adjacent morphology codes
- Ensure morphology codes get same color as their preceding Strong's number
- Preserve HTML escaping for angle brackets

**Validation:**
- Navigate to Genesis 1:1 and verify `<01254>(8804)` shows unified background color
- Check multiple verses with different morphology patterns `(**dddd)`, `(*dddd)`
- Confirm click handlers still work on Strong's number portion

**Files:**
- `viewer_v2/js/color_mapper.js` (lines ~111-124)

---

### 3. Extend Color Application to Braced Patterns (js/color_mapper.js)
**Description:** Ensure braced Strong's numbers like `{<0853>}` inherit group colors

**Steps:**
- Verify regex pattern captures `{<WHdddd>}` patterns (should already match based on current pattern)
- If not matching, update pattern to explicitly handle opening/closing braces
- Test with implicit object markers in Genesis 1:1

**Validation:**
- Navigate to Genesis 1:1 and verify `{<0853>}<08064>` shows unified background color
- Check that both `{<0853>}` and `<08064>` have matching colors
- Verify braced patterns remain clickable for dictionary lookups

**Files:**
- `viewer_v2/js/color_mapper.js` (lines ~111-124)

---

### 4. Manual Testing Across Multiple Verses
**Description:** Comprehensive visual validation

**Test Cases:**
- Genesis 1:1 - morphology codes and braced patterns
- Genesis 1:2 - multiple groups with varied patterns
- Genesis 1:3 - simpler structure for baseline
- Genesis 3:5 - infinitive constructs
- Genesis 4:16 - compound prepositions

**Validation Checklist:**
- [x] Selected verse shows borders only (no background)
- [x] All SN group components share same color
- [x] Click handlers work on all SN tags
- [x] No visual regressions in right panel
- [x] Keyboard navigation preserves highlighting
- [x] URL hash updates don't break styling

---

## Dependencies
None - tasks can be executed sequentially in order listed

## Parallelization Opportunities
Tasks 2 and 3 can be combined into a single regex update if the pattern modification handles both cases simultaneously

## Rollback Plan
If issues arise:
1. Revert CSS changes: restore `background-color: #e3f2fd;`
2. Revert JS changes: restore original regex pattern `/(\{?<W[ATH]*H?(\d+)>\}?)/g`
3. Hard refresh browser (Ctrl+Shift+R) to clear cached JS/CSS
