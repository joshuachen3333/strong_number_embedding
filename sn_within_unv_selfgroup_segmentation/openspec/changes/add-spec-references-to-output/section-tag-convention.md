# SPECIFICATION Section Tagging Convention

## Purpose
This document defines the convention for adding machine-readable tags to SPECIFICATION markdown files, enabling parsers to automatically extract section-to-rule mappings.

## Background

### The Problem
When upgrading from v1.8 to v1.9, specification chapter numbers may change (e.g., §3.3 → §3.4). Hardcoding section numbers in parser code creates maintenance burden and version inconsistency risks.

### The Solution
Use HTML comment tags in SPECIFICATION markdown files to create stable, version-independent mappings between section numbers and rule names.

## Tag Format

### Basic Syntax
```markdown
### 3.3 Section Title <!-- spec:rule_name -->
```

**Components:**
- `<!--` `-->` - HTML comment delimiters (invisible when rendering markdown)
- `spec:` - Namespace prefix (identifies this as a spec tag)
- `rule_name` - Stable identifier for this rule (snake_case, no spaces)

### Tag Placement
Tags MUST appear on the same line as the section header, after the title text.

**Correct:**
```markdown
### 3.3 複合介系詞檢測與合併（v1.7 新增） <!-- spec:compound -->
```

**Incorrect:**
```markdown
### 3.3 複合介系詞檢測與合併（v1.7 新增）
<!-- spec:compound -->  ❌ Tag on separate line won't be detected
```

## Standard Rule Names

### Core Parsing Rules (SPECIFICATION v1.8)

| Rule Name | Description | Typical Section |
|-----------|-------------|-----------------|
| `compound` | Compound preposition detection | §3.3 |
| `prefix` | 900x prefix attachment | §3.3.1 |
| `morph` | Morphology code attachment | §3.3.2 |
| `object_marker` | Object marker {<0853>} handling | §3.3.3 (Exception 2) |
| `brace_right` | Brace prep right-attach to noun | §3.3.4.1 (一般) |
| `brace_left` | Brace prep left-attach to verb | §3.3.4.2 (特例 1) |
| `grouping` | General grouping and merging | §3.4 |
| `construct` | Construct state linking | §3.4.5 |

**Stability Guarantee:**
- Rule names MUST remain stable across versions
- Section numbers MAY change (3.3 → 3.4 in v1.9)
- Tags survive copy-paste to new versions

### Naming Conventions

**DO:**
- Use descriptive, stable identifiers (`compound`, `prefix`, `morph`)
- Use snake_case for multi-word names (`object_marker`, `brace_left`)
- Keep names concise (1-2 words preferred)
- Use same names across all versions

**DON'T:**
- Include version numbers (`compound_v18` ❌)
- Include section numbers (`rule_3_3_1` ❌)
- Use spaces or special characters (`brace prep` ❌, `obj-marker` ❌)
- Change names between versions (breaks compatibility)

## Adding Tags to SPECIFICATION Files

### Step-by-Step Process

**1. Identify key sections**
Find sections that correspond to grouping rules used in parser output.

**2. Choose stable rule names**
Use names from the standard list above, or create new descriptive names following conventions.

**3. Add tags to section headers**
```markdown
### 3.3 複合介系詞檢測與合併（v1.7 新增） <!-- spec:compound -->

**在分組前執行**，檢測並合併複合介系詞：

#### 3.3.1 檢測算法（v1.8 通用版本：支持所有複合詞） <!-- spec:prefix -->

...
```

**4. Verify invisibility**
Render the markdown (GitHub, GitLab, or local viewer) and confirm tags don't appear.

**5. Test parser extraction**
Run parser and verify it successfully loads section mappings.

### Example: Tagging SPECIFICATION_v1.8.md

```markdown
## 3.0 核心解析規則與流程

### 3.1 標記正規化（必做）
<!-- No tag needed: not used in output references -->

### 3.2 Token 正則（參考實作）
<!-- No tag needed: implementation detail -->

### 3.3 複合介系詞檢測與合併（v1.7 新增） <!-- spec:compound -->

**在分組前執行**，檢測並合併複合介系詞：

#### 3.3.1 檢測算法（v1.8 通用版本：支持所有複合詞） <!-- spec:prefix -->

...

#### 3.3.2 合併規則（v1.8 通用版本） <!-- spec:morph -->

...

### 3.4 分組與合併（Grouping & Merging） <!-- spec:grouping -->

**掃描方向**：自左往右；**忽略**標點／空白。

1. **前綴緩衝（prefix_buffer）**
   遇到 900x 先入 `prefix_buffer`...

3. **形態附著**
   遇到 morph（顯/隱）一律**左附**...

4. **brace 介詞決策樹（v1.2-A 強化版）** <!-- spec:brace_decision -->
   遇 `{<PREP>}` 時：

   * **特例 1（最高優先）** <!-- spec:brace_left -->
     若 `qp.wform` 顯示「介系詞 + 代名詞後綴」...

   * **特例 2** <!-- spec:object_marker -->
     `{<0853>}`（受詞記號 אֵת）**總是右附**...

   * **一般** <!-- spec:brace_right -->
     若右側就近（可跨 900x）為**名詞**...
```

## Parser Implementation

### Extraction Function

Parsers MUST implement a function that extracts tags using this regex pattern:

```python
import re

def extract_spec_tags(content):
    """Extract spec tags from SPECIFICATION markdown content."""
    sections = {}
    pattern = r'^###+\s+(\d+(?:\.\d+)*)\s+[^<]*<!--\s*spec:(\w+)\s*-->'

    for match in re.finditer(pattern, content, re.MULTILINE):
        section_num = match.group(1)
        rule_name = match.group(2)
        sections[rule_name] = section_num

    return sections

# Example result for v1.8:
# {
#     'compound': '3.3',
#     'prefix': '3.3.1',
#     'morph': '3.3.2',
#     'object_marker': '3.3.3',
#     'brace_left': '3.3.4.2',
#     'brace_right': '3.3.4.1',
#     'grouping': '3.4'
# }
```

### Fallback Strategy

Parsers SHOULD implement fallback for untagged specifications:

```python
KNOWN_SECTIONS_V18 = {
    '3.3': 'compound',
    '3.3.1': 'prefix',
    '3.3.2': 'morph',
    # ... hardcoded mappings for v1.8
}

def load_spec_sections():
    content = read_specification_file()

    # Strategy 1: Extract tags (preferred)
    sections = extract_spec_tags(content)

    # Strategy 2: Fallback to known mappings
    if not sections:
        sections = KNOWN_SECTIONS_V18
        print("⚠️  No spec tags found, using fallback")

    return sections
```

## Version Upgrade Workflow

### When copying SPECIFICATION_v1.8.md → SPECIFICATION_v1.9.md

**Tags automatically migrate:**
```markdown
<!-- In v1.8 -->
### 3.3 複合介系詞檢測與合併 <!-- spec:compound -->

<!-- In v1.9, section number changed but tag stays same -->
### 3.4 複合介系詞檢測與合併 <!-- spec:compound -->
     ^^^                              ^^^^^^^^^^^^^^
     Updated section number           Same tag!
```

**Parser automatically adapts:**
```python
# v1.8 parser extracts: {'compound': '3.3'}
# v1.9 parser extracts: {'compound': '3.4'}
# Output shows correct section for each version!
```

## Benefits

### ✅ Single Source of Truth
- SPECIFICATION.md is the only file to maintain
- No separate mapping configuration files
- Section numbers automatically sync

### ✅ Version Independence
- Tags are stable across versions
- Section renumbering doesn't break parsers
- Easy to upgrade (copy + modify section numbers)

### ✅ Invisible Markup
- Tags don't clutter rendered markdown
- HTML comments are standard and widely supported
- No special tooling required to view/edit

### ✅ Backward Compatible
- Untagged specifications still work (fallback strategy)
- Incremental migration possible
- No breaking changes to existing parsers

## FAQ

**Q: What if I forget to add tags to a new section?**
A: Parser will gracefully handle missing sections using `.get()` with None default. That rule simply won't have a spec reference in output.

**Q: Can I use the same tag on multiple sections?**
A: Yes, but the last occurrence wins. Generally, tag the most specific/relevant section.

**Q: Do all sections need tags?**
A: No, only sections that correspond to grouping rules used in output need tags. Internal implementation sections don't need tags.

**Q: What happens if tag format is wrong?**
A: Parser regex won't match it, falls back to known mappings or returns incomplete dict. No crashes.

**Q: Can I add custom tags for my own purposes?**
A: Yes, but use a different namespace (e.g., `<!-- custom:my_tag -->`) to avoid conflicts with standard `spec:` tags.
