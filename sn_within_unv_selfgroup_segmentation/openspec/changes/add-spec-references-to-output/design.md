# Design: Add Spec References to Output

## Architecture Overview

This change enhances the `format_groups_to_text()` function in `parse_verse_v1_8.py` to add specification metadata without modifying the core parsing logic in `group_and_merge()`.

The design follows a **self-contained, version-isolated architecture** where each parser version (`parse_verse_v1_8.py`, `parse_verse_v1_9.py`, etc.) independently loads and parses its corresponding SPECIFICATION file.

## Version Architecture Principles

### 1. One-to-One Version Coupling

**Principle:** `SPECIFICATION_v1.8.md` ↔ `parse_verse_v1_8.py` (strict pairing)

**Rationale:**
- Each parser version is self-contained and independent
- No shared utility modules to maintain across versions
- Upgrading to v1.9 is as simple as copying files and changing version string
- Old versions remain stable and unaffected by new versions

**Implementation:**
```python
# parse_verse_v1_8.py (Line 13)
PARSER_VERSION = "v1.8"
SPEC_FILE = f"SPECIFICATION_{PARSER_VERSION}.md"

# Automatic version detection and validation
SPEC_META = load_spec_sections()  # Reads SPECIFICATION_v1.8.md
if SPEC_META['version'] != PARSER_VERSION:
    raise ValueError("Version mismatch!")
```

### 2. Self-Contained Specification Parsing

**Decision:** Each parser contains its own `load_spec_sections()` function

**Rationale:**
- No dependency on external `spec_utils.py` or shared libraries
- Each version can evolve its parsing strategy independently
- Copying to new version brings all necessary code
- Simple, reliable, maintainable

**Implementation:**
```python
@lru_cache(maxsize=1)
def load_spec_sections():
    """
    Load section mappings from SPECIFICATION_v1.8.md

    Strategy 1 (Preferred): HTML comment tags
        ### 3.3 Title <!-- spec:compound -->

    Strategy 2 (Fallback): Known section number mappings
    """
    # Read SPECIFICATION_v1.8.md
    # Extract section numbers
    # Return {'version': 'v1.8', 'sections': {...}}
```

## Key Design Decisions

### 1. Specification Section Tagging Strategy

**Decision:** Use HTML comment tags in SPECIFICATION markdown files

**Rationale:**
- Tags are invisible when rendering markdown
- Explicit, unambiguous mapping from section to rule name
- Survives copy-paste to new versions
- Easy to maintain

**Implementation in SPECIFICATION_v1.8.md:**
```markdown
### 3.3 複合介系詞檢測與合併（v1.7 新增） <!-- spec:compound -->

#### 3.3.1 檢測算法 <!-- spec:prefix -->

#### 3.3.2 合併規則 <!-- spec:morph -->

### 3.4 分組與合併 <!-- spec:grouping -->
  * **特例 1** <!-- spec:brace_left -->
  * **特例 2** <!-- spec:object_marker -->
  * **一般** <!-- spec:brace_right -->
```

**Tag Format:**
- `<!-- spec:rule_name -->` where `rule_name` is a stable identifier
- Rule names don't change across versions (e.g., `compound`, `prefix`, `morph`)
- Section numbers MAY change (3.3 → 3.4 in v1.9), but tags stay the same

### 2. Fallback Strategy for Legacy Specifications

**Decision:** Implement dual-strategy parsing with fallback

**Rationale:**
- Support existing SPECIFICATION files without tags
- Graceful degradation if tags are missing
- Allows incremental migration to tagged format

**Implementation:**
```python
# Strategy 1: Extract tagged sections
sections = extract_spec_tags(content)

# Strategy 2: Fallback to known section numbers
if not sections:
    KNOWN_SECTIONS_V18 = {
        '3.3': 'compound',
        '3.3.1': 'prefix',
        # ...
    }
    sections = map_known_sections(section_tree, KNOWN_SECTIONS_V18)
```

### 3. Rule Determination from Group Metadata

**Decision:** Determine spec rule at formatting time, not during grouping

**Rationale:**
- Grouping logic remains unchanged (no risk to core functionality)
- Rule determination is purely presentational
- Easy to adjust priority order without touching grouping code

**Implementation:**
```python
def determine_spec_rule(group):
    """
    Determine which SPECIFICATION rule created this group.
    Uses priority order matching against group structure.
    """
    # Priority order (first match wins)
    if group.get('compound'): return SPEC_SECTIONS['compound']
    if '0853' in group.get('pre_brace', []): return SPEC_SECTIONS['object_marker']
    # ... more rules ...
```

### 2. Spec Rule Assignment Logic

**Mapping of rules to spec sections:**

| Rule Applied | Spec Section | Condition |
|--------------|--------------|-----------|
| Prefix attachment | `3.3.1` | `len(group['prefixes']) > 0` AND multi-token |
| Morphology attachment | `3.3.2` | `len(group['morph']) > 0` AND multi-token |
| Object marker `{<0853>}` | `3.3.3` | `'0853' in group['pre_brace']` |
| Brace prep right-attach | `3.3.4.1` | `len(group['pre_brace']) > 0` AND not 0853 |
| Brace prep left-attach | `3.3.4.2` | `len(group['post_brace']) > 0` |
| Compound preposition | `3.3` | `group.get('compound') == True` |
| Construct state | `3.4.5` | `'construct_of' in group` |

**Priority order** (first match wins):
1. Compound → `3.3`
2. Object marker → `3.3.3`
3. Post-brace → `3.3.4.2`
4. Pre-brace → `3.3.4.1`
5. Morphology → `3.3.2`
6. Prefix → `3.3.1`
7. Construct → `3.4.5`
8. None (single-token) → no reference

### 3. Interleaved Text Extraction

**Detection criteria:**
- Group has 2+ tokens (excluding morphology codes)
- Tokens appear non-consecutively in `bible_text_raw` with Chinese characters between them

**Extraction algorithm:**
```python
def extract_interleaved_text(group, bible_text_raw):
    """
    Extract original text showing SN-Chinese-SN arrangement.
    Returns string like "{<0853>}天<08064>" or None if not interleaved.
    """
    # 1. Build search pattern for this group's tokens
    # 2. Find token positions in raw text
    # 3. Check if Chinese chars exist between tokens
    # 4. Extract substring from first to last token
    # 5. Strip WH/WAH/WTH prefixes
    return interleaved_snippet or None
```

**Edge cases:**
- Morphology codes (8xxx) are part of preceding SN, not separate tokens
- Multiple same SNs (e.g., `{<0853>}..{<0853>}`) - match first occurrences only
- Failed extraction → omit interleaved text, don't fail entire line

### 4. Output Formatting

**Line format** (80-character alignment):
```
<SNs> — <description>    ::<interleaved>::    [spec]
^      ^                  ^                    ^
0      varies             optional             78-80
```

**Alignment strategy:**
```python
LINE_WIDTH = 80  # Configurable constant

def format_line_with_spec_ref(base_line, interleaved_text, spec_ref):
    """
    Format: base_line + optional_interleaved + right-aligned_spec_ref
    """
    parts = [base_line]

    if interleaved_text:
        parts.append(f"    ::{interleaved_text}::")

    if spec_ref:
        current_length = sum(len(p) for p in parts)
        padding = LINE_WIDTH - current_length - len(f"[{spec_ref}]")
        if padding > 0:
            parts.append(' ' * padding)
        else:
            parts.append('  ')  # Minimum 2 spaces
        parts.append(f"[{spec_ref}]")

    return ''.join(parts)
```

### 5. Version Header

**Simple string concatenation:**
```python
output_lines = ["Parsed and Formatted Text Section (SPECIFICATION_v1.8):"]
```

**Version source:** Hardcoded constant (matches parser implementation version)

## Component Interactions

```
tokenize_and_classify()
    ↓
group_and_merge() ← ADD: _spec_rule metadata to each group
    ↓
format_groups_to_text() ← MODIFY:
    1. Add version to header
    2. Extract interleaved text
    3. Format with spec references
    ↓
Output text
```

## Testing Strategy

**Unit tests:**
1. `test_spec_rule_assignment()` - verify correct rule detection
2. `test_interleaved_text_extraction()` - test SN-Chinese-SN extraction
3. `test_line_formatting()` - verify 80-char alignment

**Integration tests:**
1. Gen 1:1 - prefix, morph, object marker cases
2. Gen 3:5 - brace prep left-attach with pronoun suffix
3. Gen 4:16 - compound preposition
4. Gen 1:2 - complex multi-group verse

**Regression tests:**
- All existing parsed output files should diff only in added annotations
- JSON output should remain unchanged

## Performance Considerations

**Impact:** Minimal
- Spec rule detection: O(1) per group (simple dict key checks)
- Interleaved text extraction: O(n) per group where n = raw text length
- Overall: No change to algorithmic complexity

**Optimization opportunities:**
- Cache compiled regex patterns for WH/WAH/WTH stripping
- Pre-compute raw text token positions once per verse

## Rollback Plan

If issues arise:
1. Revert changes to `format_groups_to_text()`
2. Remove `_spec_rule` assignments in `group_and_merge()`
3. No database/file format changes, so rollback is clean

## Version Upgrade Workflow

### Upgrading from v1.8 to v1.9

**Step 1: Copy and update SPECIFICATION**
```bash
cp SPECIFICATION_v1.8.md SPECIFICATION_v1.9.md
```

Edit `SPECIFICATION_v1.9.md`:
- Line 1: Change version number in title
- Update section numbers if restructuring (e.g., 3.3 → 3.4)
- Keep HTML comment tags unchanged (e.g., `<!-- spec:compound -->`)

**Step 2: Copy and update parser**
```bash
cp parse_verse_v1_8.py parse_verse_v1_9.py
```

Edit `parse_verse_v1_9.py`:
- Line 13: Change `PARSER_VERSION = "v1.9"`
- That's it! The parser will automatically:
  - Load `SPECIFICATION_v1.9.md`
  - Extract new section numbers
  - Validate version consistency

**Step 3: Verify**
```bash
python parse_verse_v1_9.py
# Expected output:
# ✓ Loaded SPECIFICATION_v1.9.md (parser v1.9)
#   Mapped 8 section rules
```

### Maintaining Multiple Versions Concurrently

**Directory structure:**
```
sn_within_unv_selfgroup_segmentation/
├── SPECIFICATION_v1.8.md
├── SPECIFICATION_v1.9.md      # Both can coexist
├── parse_verse_v1_8.py         # Old version still works
├── parse_verse_v1_9.py         # New version independent
└── run_parser_temp.py          # Can call either version
```

**Benefits:**
- Old parsed output remains reproducible (use v1.8 parser)
- Can compare v1.8 vs v1.9 parsing results
- No risk of breaking old version when developing new version

## Future Enhancements

**Potential v2 features:**
1. Clickable spec references in viewer (hyperlinks to SPECIFICATION_v1.8.md sections)
2. Configurable output format (compact, verbose, academic citation style)
3. Multi-language spec references (English, Chinese)
4. Automated spec reference validation (check all referenced sections exist)
5. Parser version auto-detection in `run_parser_temp.py` (discover all available versions)
