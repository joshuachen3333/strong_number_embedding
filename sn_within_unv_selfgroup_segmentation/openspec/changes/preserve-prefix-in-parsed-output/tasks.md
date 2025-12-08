# Implementation Tasks

## 1. Parser Modifications

- [x] 1.1 Add function to extract complete Strong's number tags from bible_text_raw
  - Create `extract_complete_tags_mapping(bible_text_raw)` helper function
  - Returns dict mapping numeric codes to complete tags (e.g., `{'05921': '<WAH05921>'}`)
  - Handle all prefix patterns: WH, WAH, WTH

- [x] 1.2 Modify `format_groups_to_text()` to use complete tags
  - Update `prefix_display` construction to use complete tags from mapping
  - Update `core_display` construction to use complete tags from mapping
  - Update `pre_brace_display` and `post_brace_display` for braced patterns
  - Handle compound prepositions (already use `<{code}>` format)

- [x] 1.3 Test parser output format
  - Run `python run_parser_temp.py --no-write 1 2` (Genesis 1:2)
  - Verify Parsed section shows `{<WAH05921>}<WH06440>` instead of `{<05921>}<06440>`
  - Verify all prefixes (WAH, WH, WTH) are preserved
  - Verify spec references still align correctly at column 80

## 2. Viewer Modifications

- [x] 2.1 Update `extractSNsFromLine()` in color_mapper.js
  - Modify regex to extract numeric codes from prefixed tags
  - Pattern: `/<W[ATH]*H?(\d+)>/` to match `<WHdddd>`, `<WAHdddd>`, `<WTHdddd>`
  - Ensure function returns numeric codes only (e.g., `'05921'` from `<WAH05921>`)

- [x] 2.2 Update `applyColorsToParsedText()` if needed
  - Review regex pattern for coloring SN groups
  - Ensure it matches complete prefixed tags
  - Test with both regular and braced patterns

- [x] 2.3 Test viewer display
  - Reload viewer in browser (hard refresh to bypass cache)
  - Navigate to Genesis 1:2
  - Verify Parsed section displays with complete tags
  - Verify color consistency between left panel, Parsed section, and Raw section

## 3. Integration Testing

- [x] 3.1 Regenerate test verses
  - Parse Gen 1:1, 1:2, 1:3 with new format
  - Verify all output files have consistent format

- [x] 3.2 Verify viewer functionality
  - Test color mapping for all sections
  - Verify `{<WAH05921>}<WH06440>` appears same color in:
    - Left panel (UNV+SN Text)
    - Right panel Parsed section
    - Right panel Raw section
  - Test clicking on Strong's numbers (if functionality exists)

- [x] 3.3 Document regeneration process
  - Update documentation with command to regenerate verses if needed
  - Note that existing files use old format until regenerated

## 4. Validation

- [x] 4.1 Run comprehensive test
  - Parse complete chapter (Gen 1:1-31)
  - Spot check multiple verses for format consistency
  - Verify no regression in spec reference alignment

- [x] 4.2 Check edge cases
  - Compound prepositions (e.g., מֵעַל in Gen 4:16)
  - Morphology codes (e.g., `<WH01254><WTH8804>`)
  - Braced patterns (e.g., `{<WAH0853>}`)
  - Mixed prefix types in single verse
