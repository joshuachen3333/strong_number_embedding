# Tasks: Fix Viewer Color Grouping and Parsed Output Markers

## Task 1: Update Parser to Preserve WH/WAH Prefixes in Markers

**Files:** `parse_verse_v1_8.py`

**Steps:**
1. Extend token data structure to store both `sn` (normalized) and `original` (with WH prefix)
2. Modify normalization logic to preserve original form alongside normalized code
3. Update marker generation (`:: ::`) to use original form instead of normalized form
4. Test with Gen 1:1 to verify markers show `{<WH0853>}` not `{<0853>}`

**Validation:**
- Run: `python run_parser_temp.py 1 1 --no-write`
- Check output contains `::{<WH0853>}天<WH08064>::` not `::{<0853>}天<08064>::`
- Verify all marker formats match the main SN display format

**Dependencies:** None

**Estimated Impact:** Low risk - only affects display, not parsing logic

---

## Task 2: Implement Position-Based Color Mapping

**Files:** `viewer_v2/js/color_mapper.js`

**Steps:**
1. Add `buildGroupPatterns()` function to create regex patterns for each group
2. Add `buildRegexPattern(sns)` to create pattern matching a specific SN sequence
3. Modify `applyColorsToRawText()` to:
   - Accept `groups` parameter (not just `colorMap`)
   - Build group patterns
   - Match groups sequentially in raw text
   - Color SNs based on group membership, not just SN code
4. Add edge case handling for SNs not in any group

**Validation:**
- Load viewer_v2 with Gen 1:1
- Verify `{<WH0853>}` in first group has different color than `{<WH0853>}` in second group
- Check console for any pattern matching errors

**Dependencies:** None

**Estimated Impact:** Medium risk - core color mapping logic change

---

## Task 3: Update applyColorsToRawText Call Sites

**Files:** `viewer_v2/js/left_panel.js`, `viewer_v2/js/right_panel.js`

**Steps:**
1. Find all calls to `ColorMapper.applyColorsToRawText()`
2. Update to pass `groups` parameter: `applyColorsToRawText(text, colorMap, groups)`
3. Ensure `currentGroups` is available in scope where needed

**Validation:**
- Search: `rg "applyColorsToRawText" viewer_v2/js/`
- Verify all call sites updated
- Test loading different verses to ensure no JS errors

**Dependencies:** Task 2 (must be completed first)

**Estimated Impact:** Low risk - straightforward parameter addition

---

## Task 4: Add Fallback for Pattern Matching Failures

**Files:** `viewer_v2/js/color_mapper.js`

**Steps:**
1. Track which SNs were successfully colored by group patterns
2. For remaining uncolored SNs, fall back to SN-based color map
3. Add console warnings for pattern matching failures

**Validation:**
- Test with verses containing unusual SN patterns
- Check console for warnings about unmatched SNs
- Verify all SNs receive some color (either group-based or fallback)

**Dependencies:** Task 2, Task 3

**Estimated Impact:** Low risk - safety net for edge cases

---

## Task 5: Test with Multiple Verses

**Files:** N/A (testing task)

**Steps:**
1. Test Gen 1:1 (object markers in multiple groups)
2. Test Gen 1:4 (multiple `<0853>` and `<0216>`)
3. Test Gen 1:5 (various SN types)
4. Verify Single HL mode still works correctly
5. Verify bidirectional highlighting still works

**Validation:**
- Create test checklist
- Document any regressions
- Screenshot before/after for visual comparison

**Dependencies:** All previous tasks

**Estimated Impact:** N/A (testing only)

---

## Task 6: Update Documentation

**Files:** `viewer_v2/README.md` (if exists), code comments

**Steps:**
1. Document the position-based color mapping approach in color_mapper.js
2. Add comments explaining why groups parameter is needed
3. Document the marker format change in parser comments

**Validation:**
- Code review for comment clarity
- Ensure future maintainers understand the "why"

**Dependencies:** Task 1-4 completed

**Estimated Impact:** None (documentation only)

---

## Task Summary

**Order of execution:**
1. Task 1 (Parser markers) - can be done in parallel with Task 2
2. Task 2 (Color mapping logic) - can be done in parallel with Task 1
3. Task 3 (Update call sites) - depends on Task 2
4. Task 4 (Fallback logic) - depends on Task 2, 3
5. Task 5 (Testing) - depends on all
6. Task 6 (Documentation) - depends on all

**Parallelizable work:**
- Task 1 and Task 2 can be done simultaneously (different codebases)

**Critical path:**
Task 2 → Task 3 → Task 4 → Task 5

**Total estimated effort:** 4-6 hours
- Task 1: 1 hour
- Task 2: 2 hours
- Task 3: 30 minutes
- Task 4: 1 hour
- Task 5: 1 hour
- Task 6: 30 minutes
