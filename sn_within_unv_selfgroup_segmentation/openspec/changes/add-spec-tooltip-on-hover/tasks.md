# Tasks: Add Spec Tooltip on Hover

## Phase 1: Parser Enhancement

- [x] Extend `load_spec_sections()` in `parse_verse_v1_8.py` to extract section titles
  - Parse markdown headers: `#### 3.3.1 Title Text <!-- spec:tag -->`
  - Store mapping: `section_number -> {title, tag}`
- [x] Add function to extract section summaries (first paragraph after header)
  - Limit summary to ~200 characters
  - Strip markdown formatting
- [x] Store spec metadata in `SPEC_META` dict for use during parsing

## Phase 2: Output Format Enhancement

- [x] Add new output section: "Spec References Section:"
  - List all spec references used in this verse's output
  - Format: `[3.3.1]: Section Title`
- [x] Update `DataLoader.parseSections()` in viewer to parse new section
  - Extract spec references into `sections.specRefs` object

## Phase 3: Viewer UI Enhancement

- [x] Add "Spec" checkbox to right panel header in `index.html`
  - Position: right of Parsed/Raw/Notes buttons (as toggle button)
  - Default: unchecked
- [x] Add localStorage persistence for Spec checkbox in `right_panel.js`
  - Key: `viewer_v2_show_spec`
- [x] Add CSS styles for spec-ref elements and tooltips in `styles.css`
  - `.spec-ref-tooltip` base styling (purple, dotted underline)
  - `.spec-tooltip-container` tooltip styling (JavaScript-managed)
  - Tooltip positioning via JavaScript

## Phase 4: Tooltip Rendering

- [x] Modify `render()` in `right_panel.js` to wrap spec references
  - Regex: `/\[(\d+(?:\.\d+)+)\]/g`
  - Wrap with: `<span class="spec-ref-tooltip" data-spec-ref="X.X.X">`
- [x] Populate tooltip content from parsed spec metadata via JavaScript
- [x] Only apply spec-ref wrapping when Spec button is enabled

## Verification

- [x] Parser correctly extracts all section titles from SPECIFICATION_v1.8.md
- [x] Output includes Spec References Section with correct mappings
- [x] Spec button appears in correct position (right of Parsed/Raw/Notes)
- [x] Spec button state persists across page reloads
- [x] Tooltips appear on hover when Spec is enabled
- [x] Tooltips do not appear when Spec is disabled
- [x] Adding new sections to spec file automatically works (dynamic extraction)
