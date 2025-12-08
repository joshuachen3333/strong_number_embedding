# Design: Preserve Strong's Number Prefixes in Parsed Output

## Context

The UNV+SN parsing system outputs two sections for each verse:
1. **Parsed and Formatted Text Section**: Structured groupings with Strong's numbers
2. **Raw UNV+SN Source Text Section**: Original text with Strong's number tags

Strong's number tags in the raw text have prefixes indicating morphological features:
- `WH`: Base Strong's number (e.g., `<WH06440>`)
- `WAH`: With waw conjunction (e.g., `<WAH05921>`)
- `WTH`: With tense marker (e.g., `<WTH8804>`)

The parser currently strips these prefixes in the Parsed section, outputting only the numeric code (e.g., `<06440>`). This creates inconsistency with the Raw section.

## Goals / Non-Goals

**Goals:**
- Preserve complete Strong's number tags (including WAH/WH/WTH prefixes) in Parsed section output
- Maintain identical tag format between Parsed and Raw sections
- Simplify viewer color mapping logic by eliminating format differences

**Non-Goals:**
- Modifying Raw section format (already correct)
- Changing the underlying parsing logic or grouping rules
- Migrating existing output files (they are regenerable on demand)

## Decisions

### Decision 1: Extract prefixes from original bible_text_raw

**What:** Parse the original Strong's number tags from `bible_text_raw` to extract the complete tag with prefix (e.g., `<WAH05921>`)

**Why:**
- The parser already receives `bible_text_raw` containing complete tags
- Group data structure stores numeric codes without prefixes
- Need to map numeric codes back to complete tags for display

**Implementation approach:**
```python
# In format_groups_to_text():
# 1. Build a mapping: numeric_code → complete_tag from bible_text_raw
# 2. Use this mapping when constructing prefix_display, core_display, etc.
```

**Alternatives considered:**
- Store complete tags in group data structure: Rejected - requires changing entire parsing pipeline
- Maintain separate prefix arrays: Rejected - complex and error-prone

### Decision 2: Update viewer to handle prefixed format

**What:** Modify `color_mapper.js` regex patterns to extract numeric codes from prefixed tags

**Why:**
- Color mapping key should remain numeric codes (`05921`) for consistency with group structure
- Only the display format changes, not the logical grouping

**Implementation:**
```javascript
// Update extractSNsFromLine() regex:
// FROM: /<(\d+)>/
// TO: /<W[ATH]*H?(\d+)>/
// This extracts '05921' from '<WAH05921>'
```

### Decision 3: No migration of existing files

**What:** Do not migrate existing parsed output files

**Why:**
- Output files are deterministic and regenerable
- Users can regenerate specific verses if needed using `python run_parser_temp.py`
- Batch regeneration can be done per-book using existing batch scripts

## Risks / Trade-offs

### Risk 1: Viewer displays incorrectly if not updated together
**Mitigation:** Deploy parser and viewer changes together in single session

### Risk 2: Existing cached files use old format
**Impact:** Mixed format display if old and new files coexist
**Mitigation:** Document regeneration command; consider adding format version marker in future

### Trade-off: Slightly longer tags in Parsed section
**Benefit:** Complete information, visual consistency
**Cost:** 2-3 extra characters per tag (negligible)

## Implementation Plan

### Phase 1: Parser Changes
1. Add function to extract complete tags from bible_text_raw:
   ```python
   def extract_complete_tags_mapping(bible_text_raw):
       # Returns: {'0430': '<WH0430>', '05921': '<WAH05921>', ...}
   ```

2. Modify `format_groups_to_text()` to use complete tags:
   - Replace `f"<{code}>"` with lookup from mapping
   - Handle braced patterns: `f"{{<{complete_tag}>}}"`

### Phase 2: Viewer Changes
1. Update `color_mapper.js`:
   - Modify `extractSNsFromLine()` regex to handle WAH/WH/WTH prefixes
   - Ensure `applyColorsToParsedText()` works with new format

2. Test color consistency between Parsed and Raw sections

### Testing Strategy
1. Parse test verse (Gen 1:2) and verify output format
2. Load in viewer and verify:
   - Colors match between Parsed and Raw sections
   - All Strong's numbers are colored correctly
   - Spec references still align properly

## Open Questions

None - implementation approach is straightforward and well-scoped.
