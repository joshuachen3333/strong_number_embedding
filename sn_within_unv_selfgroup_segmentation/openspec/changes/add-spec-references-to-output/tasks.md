# Tasks: Add Spec References to Output

## Task Breakdown

### 1. Add Version to Section Header
**Description:** Update section header to include SPECIFICATION version identifier

**Steps:**
- Modify `format_groups_to_text()` line 570 to change header from:
  ```python
  output_lines = ["Parsed and Formatted Text Section:"]
  ```
  to:
  ```python
  output_lines = ["Parsed and Formatted Text Section (SPECIFICATION_v1.8):"]
  ```

**Validation:**
- Run parser on Gen 1:1
- Verify header displays `(SPECIFICATION_v1.8)` suffix
- Confirm no other sections get version suffix

**Files:**
- `parse_verse_v1_8.py` (line ~570)

---

### 2. Implement Specification Section Loading
**Description:** Create self-contained function to load and parse SPECIFICATION_v1.8.md section mappings

**Steps:**
- Add constants at top of file (~line 13):
  ```python
  PARSER_VERSION = "v1.8"
  SPEC_FILE = f"SPECIFICATION_{PARSER_VERSION}.md"
  ```
- Add new function `load_spec_sections()` before `format_groups_to_text()` (~line 30-120):
  1. Check if `SPEC_FILE` exists, raise error if not found
  2. Read file content and extract version from first line
  3. Verify version matches `PARSER_VERSION`, raise error if mismatch
  4. **Strategy 1 (Preferred)**: Extract HTML comment tags `<!-- spec:rule_name -->`
     - Pattern: `^###+\s+(\d+(?:\.\d+)*)\s+[^<]*<!--\s*spec:(\w+)\s*-->`
     - Build dict mapping rule_name → section_number
  5. **Strategy 2 (Fallback)**: Use known section mappings for v1.8
     - Define `KNOWN_SECTIONS_V18` dict
     - Map standard section numbers to rule names
  6. Return `{'version': 'v1.8', 'sections': {...}}`
  7. Use `@lru_cache(maxsize=1)` decorator for performance
- Call `load_spec_sections()` at module level (after function definition):
  ```python
  SPEC_META = load_spec_sections()
  SPEC_SECTIONS = SPEC_META['sections']
  print(f"✓ Loaded {SPEC_FILE} (parser v{PARSER_VERSION})")
  ```

**Validation:**
- Test with SPECIFICATION_v1.8.md (both with and without tags)
- Verify version mismatch raises clear error
- Verify file not found raises clear error
- Check that caching works (function called only once)

**Files:**
- `parse_verse_v1_8.py` (new constants ~line 13, new function ~line 30-120)

---

### 3. Implement Spec Rule Detection Logic
**Description:** Create function to determine which spec rule created each group

**Steps:**
- Add new function `determine_spec_rule(group)` after `load_spec_sections()` (~line 125):
  1. Count tokens (prefixes + pre_brace + core + post_brace)
  2. Return `None` if single-token group (no grouping rules applied)
  3. Implement priority-based rule detection using `SPEC_SECTIONS` dict:
     - Check `compound` → return `SPEC_SECTIONS['compound']`
     - Check `'0853' in pre_brace` → return `SPEC_SECTIONS['object_marker']`
     - Check `post_brace` → return `SPEC_SECTIONS['brace_left']`
     - Check `pre_brace` → return `SPEC_SECTIONS['brace_right']`
     - Check `morph` → return `SPEC_SECTIONS['morph']`
     - Check `prefixes` → return `SPEC_SECTIONS['prefix']`
     - Check `construct_of` → return `SPEC_SECTIONS.get('construct')`
     - Default → return `None`
  4. Handle missing keys gracefully with `.get()` method

**Validation:**
- Unit test with mock groups for each rule type
- Verify priority order works correctly
- Test edge cases (empty lists, missing keys, missing sections in dict)
- Verify single-token groups return None

**Files:**
- `parse_verse_v1_8.py` (new function ~line 125)

---

### 4. Implement Interleaved Text Extraction
**Description:** Create function to extract SN-Chinese-SN patterns from raw text

**Steps:**
- Add new function `extract_interleaved_text(group, bible_text_raw)` before `format_groups_to_text()`
- Implement extraction algorithm:
  1. Count tokens (excluding morph codes): if < 2, return `None`
  2. Build search patterns for each token in group (handle braces, prefixes)
  3. Find positions of first and last token in `bible_text_raw`
  4. Check if Chinese characters exist between positions
  5. Extract substring from first token start to last token end
  6. Strip WH/WAH/WTH prefixes using regex
  7. Return cleaned snippet or `None` on failure
- Add error handling for edge cases (duplicate SNs, not found, etc.)

**Validation:**
- Test with Gen 1:1 verse 1: `{<WH0853>}天<WH08064>` → `{<0853>}天<08064>`
- Test with adjacent tokens (should return `None`)
- Test with Chinese before tokens (should return `None`)
- Test extraction failure gracefully returns `None`

**Files:**
- `parse_verse_v1_8.py` (new function ~555)

---

### 5. Implement Line Formatting with Alignment
**Description:** Create function to format output line with spec reference and optional interleaved text

**Steps:**
- Add constant `LINE_WIDTH = 80` at top of file
- Add new function `format_line_with_annotations(base_line, interleaved_text, spec_ref, line_width=LINE_WIDTH)`
- Implement formatting logic:
  1. Start with `base_line`
  2. If `interleaved_text`: append `    ::` + text + `::`
  3. If `spec_ref`: calculate padding to reach `line_width`, append `[` + ref + `]`
  4. Use minimum 2-space gap if line exceeds `line_width`
  5. Return formatted line
- Handle None values gracefully

**Validation:**
- Test short line (should pad to column 80)
- Test long line (should use 2-space minimum gap)
- Test with/without interleaved text
- Test with/without spec reference

**Files:**
- `parse_verse_v1_8.py` (new function ~690, constant ~30)

---

### 6. Integrate into format_groups_to_text()
**Description:** Modify main formatting loop to use new functions

**Steps:**
- In the main `for group in groups:` loop (~577-656):
  - After building `formatted_line` (line ~655), call new functions:
    ```python
    spec_rule = determine_spec_rule(group)
    interleaved = extract_interleaved_text(group, bible_text_raw)
    formatted_line = format_line_with_annotations(formatted_line, interleaved, spec_rule)
    ```
  - Apply same logic to compound preposition branch (~598)
- Ensure both regular and compound paths use new formatting

**Validation:**
- Run parser on Gen 1:1
- Verify all multi-token groups show spec references
- Verify single-token groups do not show spec references
- Verify interleaved text appears for appropriate groups
- Check alignment is consistent

**Files:**
- `parse_verse_v1_8.py` (lines ~598, ~655)

---

### 7. Add HTML Comment Tags to SPECIFICATION_v1.8.md
**Description:** Add machine-readable tags to key sections in SPECIFICATION file

**Steps:**
- Open `SPECIFICATION_v1.8.md`
- Add `<!-- spec:rule_name -->` tags to key sections:
  - Section 3.3: `<!-- spec:compound -->`
  - Section 3.3.1: `<!-- spec:prefix -->`
  - Section 3.3.2: `<!-- spec:morph -->`
  - Section 3.4: `<!-- spec:grouping -->`
  - Brace prep sections: `<!-- spec:brace_left -->`, `<!-- spec:brace_right -->`, `<!-- spec:object_marker -->`
- Verify tags are invisible when rendering markdown
- Test parser can extract tags correctly

**Validation:**
- Visual inspection of markdown rendering (tags should be invisible)
- Run parser and check that tags are extracted
- Verify fallback still works if tags are removed

**Files:**
- `SPECIFICATION_v1.8.md` (add tags to ~8-10 key sections)

---

### 8. Test with Multiple Verses
**Description:** Comprehensive validation across different verse patterns

**Test Cases:**
- **Gen 1:1** - prefix, morph, object marker, interleaved text
- **Gen 1:2** - multiple groups, brace prep right-attach
- **Gen 3:5** - brace prep left-attach (pronoun suffix case)
- **Gen 4:16** - compound preposition
- **Gen 1:5** - FHL profile, inferred prefixes, construct state

**Validation Checklist:**
- [x] Header shows `(SPECIFICATION_v1.8)` in all test cases
- [x] Multi-token groups display correct spec references
- [x] Single-token groups show no spec references
- [x] Interleaved text displayed with `::` delimiters where applicable
- [x] Alignment is visually consistent (column 80 target)
- [x] Compound prepositions show `[3.3]` reference (when encountered)
- [x] No regressions in morphology notes or uncertainty notes

**Files:**
- Test verses in `output/` directory
- Manual visual inspection

---

### 9. Regression Testing
**Description:** Ensure no breaking changes to existing functionality

**Steps:**
- Run parser on previously parsed verses
- Compare new output to old output (diff)
- Verify only differences are:
  1. Added `(SPECIFICATION_v1.8)` in header
  2. Added spec references to multi-token lines
  3. Added interleaved text to applicable lines
- Confirm no changes to:
  - Group structure or ordering
  - Chinese meanings or Hebrew text
  - Morphology notes
  - Uncertainty notes
  - Raw UNV+SN section

**Validation:**
- Run `diff` on old vs new output files
- Check that JSON output format is unchanged
- Verify no new warnings or errors appear

**Files:**
- Existing files in `output/Genesis/1/` directory

---

## Dependencies
- Task 1 is independent (header change only)
- Task 2 must complete before task 3 (spec sections must be loaded before rule detection)
- Tasks 4-5 are independent of tasks 2-3 (can develop in parallel)
- Task 6 depends on tasks 2-5 (all helper functions must exist)
- Task 7 depends on task 2 (parser must load spec successfully)
- Tasks 8-9 depend on task 6 (integration must be complete)

## Parallelization Opportunities
- Tasks 4-5 can be developed concurrently with task 2 (different functions)
- Task 7 (adding tags) can be done early to enable testing task 2
- Unit tests can be written alongside each function implementation

## Rollback Plan
If issues arise:
1. Revert changes to `format_groups_to_text()` integration (task 6)
2. Remove new helper functions (tasks 2-5)
3. Restore original header string (task 1)
4. Remove HTML tags from SPECIFICATION_v1.8.md (task 7) if needed
5. Re-test with original parser to confirm rollback success

## Estimated Complexity
- **Task 1**: Trivial (1 line change)
- **Task 2**: Medium (80-100 lines, spec file parsing with dual strategy)
- **Task 3**: Low (20-30 lines, straightforward conditionals)
- **Task 4**: Medium (40-50 lines, regex and string manipulation)
- **Task 5**: Low (15-20 lines, string formatting)
- **Task 6**: Low (5-10 lines, function calls)
- **Task 7**: Low (add ~10 HTML comment tags to markdown)
- **Task 8**: Medium (manual testing effort)
- **Task 9**: Low (automated diff comparison)

**Total estimated implementation:** ~180-230 new lines of code + SPECIFICATION.md tags
