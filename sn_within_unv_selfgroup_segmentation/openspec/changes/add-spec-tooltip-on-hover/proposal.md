# Proposal: Add Spec Tooltip on Hover

## Summary

Add a "Spec" checkbox in the right panel header (next to Parsed/Raw/Notes buttons) that enables hover tooltips on spec section references like `[3.3.1]`. The tooltip displays the specification section's title and summary content, helping users understand what each section reference means without needing to open the spec file.

## Problem

The parsed output displays spec section references like `[3.3.1]`, `[3.3.2]`, `[3.3.3]` to indicate which parsing rule was applied. However, users may not remember what each section contains, and opening the spec file to check is inconvenient.

## Proposed Solution

### Phase 1: Parser Enhancement (parse_verse_v1_8.py)

Extend the existing `load_spec_sections()` function to also extract:
- Section title (e.g., "檢測算法（v1.8 通用版本：支持所有複合詞）")
- Section summary (first paragraph or first N characters after the title)

This data is **dynamically extracted** from `SPECIFICATION_v1.8.md` at parse time, so:
- No hardcoded spec content
- New sections are automatically supported
- Content stays in sync with the spec file

### Phase 2: Output Format Enhancement

Include spec metadata in the parser output (as a separate section or JSON metadata), containing:
```
Spec References:
3.3.1: 檢測算法（v1.8 通用版本：支持所有複合詞）
3.3.2: 合併規則（v1.8 通用版本）
3.3.3: 輸出格式
```

### Phase 3: Viewer Enhancement (viewer_v2)

1. Add "Spec" checkbox in right panel header (left of Parsed/Raw/Notes)
2. Wrap `[3.3.x]` references in `<span class="spec-ref" data-spec="3.3.1">` elements
3. On hover (when Spec checkbox enabled), show CSS tooltip with section title and summary
4. Use pure CSS tooltip (no popup window, no JavaScript modal)

## Scope

**Files affected:**
- `parse_verse_v1_8.py` - Extract spec titles/summaries
- `viewer_v2/index.html` - Add Spec checkbox
- `viewer_v2/css/styles.css` - Tooltip styling
- `viewer_v2/js/right_panel.js` - Parse and render spec refs with tooltip data

**Complexity:** Medium - requires coordination between parser and viewer

**Risk:** Low - additive feature, no changes to existing parsing logic

## Design Principle

**Dynamic extraction, not hardcoding**: The parser reads the spec file and extracts section metadata dynamically. If new sections are added to the spec (e.g., `[3.3.4]`), they are automatically supported without code changes.
