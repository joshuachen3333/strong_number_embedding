# Proposal: Add Strong's Number-Based Segmentation Correction

**Change ID**: `add-sn-based-segmentation-correction`
**Status**: Proposed
**Date**: 2025-10-31
**Priority**: High

## Summary

Implement a correction layer that uses UNV (和合本) with Strong's Numbers as the authoritative reference to correct Chinese term boundaries in **target versions** (LCC, RCUV2010, etc.). This corrects initial segmentation results from jieba/pkuseg/LAC/Stanza by applying boundary rules learned from UNV+SN.

**SCOPE**:
- **Phase 1**: Simple exact string matching ✅
- **Phase 2**: CLI integration ✅
- **Phase 3**: Demo and documentation ✅

**Out of Scope** (separate proposal `add-similarity-based-matching`):
- Character variant normalization (爲→為)
- Substring extraction (handle粗粒度問題: "將他的獨生" → "獨生")
- Similarity-based matching
- Semantic alignment for different-character terms (上帝 ↔ 神)

**KEY PRINCIPLE**: Target version text (LCC) goes in → Target version text (LCC) comes out, with corrected boundaries. The text itself never changes to UNV.

## Problem Statement

### Current Issue

Initial segmentation by general-purpose Chinese word segmenters produces **inconsistent and biblically inaccurate** term boundaries:

**Example: John 3:16 (約翰福音 3:16) - LCC Version**

```
Target: LCC Text (呂振中譯本): 上帝這樣地愛世人，甚至賜下獨生子...
Reference: UNV+SN: 神<G2316>愛<G25>{}世人<G2889>，甚至<G5620>將他的獨生<G3439>子<G5207>賜給<G1325>...

❌ Jieba Initial Segmentation (LCC):
   上帝 | 這樣 | 地 | 愛 | 世人 | 甚至 | 賜 | 下獨 | 生子 | ...
   Problems:
   - "下獨 | 生子" - splits "獨生子" incorrectly
   - "賜 | 下獨" - wrong boundary for "賜下"

✅ After SN Correction (using character matching with UNV+SN):
   上帝 | 這樣地 | 愛 | 世人 | 甚至 | 賜下 | 獨生 | 子 | ...
            ↑      ↑    ↑      ↑           ↑     ↑
   Corrected boundaries (matched with UNV+SN):
   - "愛" - found in UNV as independent word → LCC also independent
   - "世人" - found in UNV as independent word → LCC also independent
   - "甚至" - found in UNV as independent word → LCC also independent
   - "獨生 | 子" - UNV+SN shows separate [G3439][G5207] → LCC also separate

   Unchanged (no character match):
   - "上帝" - LCC has "上帝", UNV has "神" → keep jieba's "上帝"
   - "這樣地" - LCC has "這樣地", UNV has "{}" → keep jieba's "這樣地"
   - "賜下" - LCC has "賜下", UNV has "將...賜給" → keep jieba's "賜下"
```

**Key Insight**: Use UNV+SN to identify term boundaries for **character sequences that exist in both versions**, without requiring semantic alignment.

### Why This Matters

1. **Correct Target Version Segmentation**: LCC, RCUV2010, and other Chinese versions need correct term boundaries for Strong's Number alignment, but only UNV has SN annotations.
2. **One-to-Many Mapping**: "獨生子" maps to two Greek words [G3439][G5207], so the boundary must be "獨生 | 子" in **all Chinese versions**, including LCC.
3. **Incremental Improvement**: Even without full semantic alignment, fixing character-matching segments (like "獨生子") significantly improves segmentation accuracy.
4. **Training Data Quality**: Corrected LCC/RCUV2010 segmentation provides better training data for Strong's Number ML models.
5. **Phase 1 Foundation**: This simple string-matching approach proves the concept before implementing complex cross-version alignment in Phase 2.

## Proposed Solution

### Architecture: Two-Stage Segmentation

```
Stage 1: Initial Segmentation (Current)
├─ Input: Raw Chinese text
├─ Process: jieba/pkuseg/LAC/stanza
└─ Output: Initial segments (may contain errors)

Stage 2: SN-Based Correction (NEW - This Proposal)
├─ Input: Initial segments + UNV+SN reference
├─ Process: Parse Strong's boundaries, enforce corrections
└─ Output: Corrected segments aligned with Strong's Numbers
```

### Core Components

#### 1. Strong's Number Boundary Parser

Parse UNV text with Strong's Numbers to extract authoritative term boundaries:

```python
# Input (UNV with SN):
"　神<H430>愛<H157>世人<H5971>，甚至<H5704>將<H5414>他的獨生子<H1121><H3173>賜給<H5414>他們"

# Output (term boundaries):
[
    ("神", ["H430"]),
    ("愛", ["H157"]),
    ("世人", ["H5971"]),
    ("甚至", ["H5704"]),
    ("將", ["H5414"]),
    ("他的", []),
    ("獨生子", ["H1121", "H3173"]),  # ✅ Authoritative boundary
    ("賜給", ["H5414"]),
    ("他們", [])
]
```

**Key Insight**: Characters between Strong's tags form atomic terms that **must not be split**.

#### 2. Boundary Correction Engine

Apply UNV+SN boundaries to target version (LCC) using **character string matching**:

```python
def correct_segmentation(target_text, initial_segments, unv_sn_boundaries):
    """
    Correct target version segmentation using UNV+SN boundaries.
    Only applies corrections where character sequences match.

    Args:
        target_text: "上帝這樣地愛世人，甚至賜下獨生子" (LCC)
        initial_segments: ["上帝", "這樣", "地", "愛", "世人", ...] (jieba)
        unv_sn_boundaries: [("神", [G2316]), ("愛", [G25]), ("世人", [G2889]),
                           ("獨生", [G3439]), ("子", [G5207]), ...]

    Algorithm:
        1. For each UNV+SN term (e.g., "愛", "世人", "獨生", "子"):
           - Check if character sequence exists in target_text
           - If found, mark as "should be independent term"

        2. Scan initial_segments:
           - If segment matches marked term → keep as is
           - If segment contains marked term → split it
           - If segment should merge with next → merge them

        3. Segments with no character match → keep initial segmentation

    Returns:
        corrected: ["上帝", "這樣地", "愛", "世人", "甚至", "賜下", "獨生", "子"]
                    ↑ unchanged  ↑ unchanged  ↑ corrected from UNV+SN
    """
```

**Example Corrections**:
- ✅ "下獨 | 生子" → "獨生 | 子" (characters match UNV+SN)
- ✅ "獨生子" → "獨生 | 子" (split based on UNV+SN)
- ⚠️ "上帝" → "上帝" (no match with "神", keep original)
- ⚠️ "這樣地" → "這樣地" (no match with "{}", keep original)

#### 3. Correction Metrics & Reporting

Track segmentation quality improvements:

```
Initial Segmentation Errors: 15 incorrect boundaries
After SN Correction: 2 incorrect boundaries (87% improvement)

Error Types:
- Merged incorrect splits: 10 (e.g., "獨生 | 子" → "獨生子")
- Split incorrect merges: 3 (e.g., "賜下獨生" → "賜下 | 獨生子")
- Unchanged correct: 150
```

## Technical Design

### Data Flow

```
┌─────────────────┐
│  User Query     │  --version lcc --verse "John 3:16" --correct-with-sn
└────────┬────────┘
         │
         v
┌─────────────────────────────────────┐
│ Fetch Target Version (LCC)          │
│   "上帝這樣地愛世人，甚至賜下獨生子"│
└────────┬────────────────────────────┘
         │
         v
┌─────────────────┐
│ Initial Segment │  jieba: ["上帝", "這樣", "地", "愛", "世人", "賜", "下獨", "生子"]
│  (Stage 1)      │  ❌ Has boundary errors
└────────┬────────┘
         │
         v
┌─────────────────────────────────────┐
│ Fetch UNV+SN (Reference Standard)   │  ← NEW COMPONENT
│   "神<G2316>愛<G25>世人<G2889>..."   │
│   "甚至<G5620>將他的獨生<G3439>"     │
│   "子<G5207>賜給<G1325>..."          │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│ Parse UNV+SN Boundaries              │  ← NEW COMPONENT
│   Extract terms: ["神", "愛", "世人", │
│   "甚至", "獨生", "子", "賜給", ...]  │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│ String Matching & Correction         │  ← NEW COMPONENT
│   Match LCC text with UNV+SN terms:  │
│   - "愛" found in LCC → independent  │
│   - "世人" found → independent       │
│   - "獨生" found → independent       │
│   - "子" found → independent         │
│   Apply corrections to LCC segments  │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────┐
│ Display Results │  ✅ Corrected LCC segmentation (still LCC text!)
│ Before:         │  上帝 | 這樣 | 地 | 愛 | 世人 | 賜 | 下獨 | 生子
│ After:          │  上帝 | 這樣地 | 愛 | 世人 | 甚至 | 賜下 | 獨生 | 子
└─────────────────┘
```

**Key Points**:
- Target version text (LCC) **never changes to UNV**
- Only boundaries are corrected where character sequences match
- No semantic alignment required in Phase 1

### Strong's Number Format Support

Must handle all four FHL Strong's formats:

1. `<WH1234>` / `<WG5678>` - FHL Hebrew/Greek format
2. `{<WH1234>}` / `{<WG5678>}` - Wrapped format
3. `{H1234}` / `{G5678}` - Simple format
4. `(H1234)` / `(G5678)` - Parentheses format

**Regex Pattern**:
```python
STRONGS_PATTERN = re.compile(
    r'[<{(]?(?:W)?([HG]\d+)[>})]?'
)
```

## Implementation Phases

### Phase 1: UNV+SN Fetching & Parsing (Week 1)
- [ ] Extend `FHLClient` to fetch UNV with `strong=1`
- [ ] Implement `StrongsNumberParser` class
- [ ] Parse all four SN formats
- [ ] Extract term boundaries
- [ ] Unit tests: T011-T015

### Phase 2: Boundary Correction Engine (Week 2)
- [ ] Implement `BoundaryCorrector` class
- [ ] Merge algorithm (fix splits like "獨生 | 子")
- [ ] Split algorithm (fix merges like "賜下獨生子")
- [ ] Handle ambiguous cases
- [ ] Unit tests: T016-T020

### Phase 3: CLI Integration (Week 3)
- [ ] Add `--correct-with-sn` flag to `segment.py`
- [ ] **Support target versions**: LCC, RCUV2010, RCUV (default: LCC)
- [ ] Display before/after comparison showing target version text unchanged
- [ ] Show correction metrics: matched terms, corrected boundaries, unchanged segments
- [ ] Integration tests: T021-T025

### Phase 4: Validation & Documentation (Week 4)
- [ ] Test with 100 verses across OT/NT
- [ ] Measure correction accuracy
- [ ] Document edge cases
- [ ] Update ARCHITECTURE.md

## Success Criteria

### Quantitative Metrics

1. **Character Match Rate**: ≥60% of UNV+SN terms found in target version (LCC)
2. **Boundary Improvement**: ≥50% of matched segments corrected successfully
3. **Performance**: <100ms additional latency per verse
4. **Coverage**: Works with all target versions (LCC, RCUV2010) and all 4 segmenters (jieba, pkuseg, LAC, stanza)
5. **No False Positives**: Unmatched segments keep initial segmentation (safe fallback)

### Qualitative Goals

1. **Text Preservation**: Target version text (LCC) never changes to UNV - only boundaries corrected
2. **Theological Integrity**: Core biblical terms like "獨生子" correctly split as "獨生 | 子" across all versions
3. **Reproducibility**: Same verse always produces same boundaries
4. **Transparency**: Clear reporting showing which segments were corrected vs unchanged
5. **Safe Fallback**: Segments without character matches keep initial segmentation

## Test Plan (Cumulative)

### New Tests (T011-T025)

**T011**: Parse UNV+SN and extract term boundaries
**T012**: Handle all four Strong's Number formats
**T013**: Merge incorrectly split terms (獨生 | 子 → 獨生子)
**T014**: Split incorrectly merged terms
**T015**: Handle verses with no Strong's Numbers
**T016**: Correct jieba segmentation with UNV standard
**T017**: Correct pkuseg segmentation with UNV standard
**T018**: Correct LAC segmentation with UNV standard
**T019**: Correct stanza segmentation with UNV standard
**T020**: Handle ambiguous correction cases
**T021**: CLI flag --correct-with-sn integration
**T022**: Display before/after comparison
**T023**: Multi-verse correction (John 3:16-17)
**T024**: Performance test (100 verses)
**T025**: Edge case: verse with special characters

**Existing Tests**: T001-T010 must continue passing

## Dependencies

### Existing Components (Already Implemented)
- ✅ FHLClient - API wrapper
- ✅ SegmenterPlugin - jieba, pkuseg, LAC, stanza
- ✅ PluginManager - Plugin orchestration

### New Dependencies
- None (uses existing requests library)

## Risks & Mitigations

### Risk 1: UNV Strong's Numbers Incomplete
**Impact**: Some verses lack SN annotations
**Mitigation**: Fallback to initial segmentation, log warnings

### Risk 2: Partial Coverage Due to Character Mismatch
**Impact**: Segments where LCC differs from UNV (e.g., LCC "上帝" vs UNV "神") cannot be corrected
**Mitigation**:
- Phase 1 (this proposal): Correct character-matching segments only (estimated 60-70% coverage)
- Phase 2 (future proposal): `add-inter-version-term-boundary-mapping` will handle character mismatches using semantic alignment
- Safe fallback: Keep initial segmentation for unmatched segments (no worse than before)

### Risk 3: Multiple Valid Segmentations
**Impact**: Some boundaries are ambiguous
**Mitigation**: Always prefer UNV+SN as authoritative

## Related Proposals

- **Next**: `add-inter-version-term-boundary-mapping` - Phase 2: Semantic alignment for character-mismatched segments
- **Previous**: `add-plugin-architecture` - Foundation (archived)

## Clarification History

This proposal was initially designed to correct UNV text only, but user feedback clarified the requirement:

**User Requirement**: "SN 校正一定要作用於目標版本 (LCC), that is, before sn correction's LCC vs after sn correction's LCC"

**Key Insight**: Target version (LCC) goes in → Target version (LCC) comes out, with corrected boundaries. Text never changes to UNV.

**Approach**: Use simple string matching to find character sequences that exist in both LCC and UNV+SN, then apply UNV+SN boundaries to those matched segments. No semantic alignment required for Phase 1.

See `prompt.history` for full discussion.

## References

- FHL API Documentation: `FHL_API_REFERENCE.md`
- Strong's Number Formats: `src/api/fhl_client.py:32-45`
- Current Segmentation: `segment.py:307-351`

---

**Approval Required**: User must approve before implementation begins.
