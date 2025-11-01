# Tasks: Add Strong's Number-Based Segmentation Correction

**Change ID**: `add-sn-based-segmentation-correction`
**Status**: Proposed

## Implementation Checklist

### Phase 1: UNV+SN Fetching & Parsing ⏳ Week 1

- [ ] **T-01**: Extend FHLClient to fetch UNV with `strong=1` parameter
  - Modify `src/api/fhl_client.py`
  - Add method `fetch_verse_with_strongs()`
  - Test with multiple verses

- [ ] **T-02**: Create StrongsNumberParser class
  - New file: `src/core/strongs_parser.py`
  - Parse four SN formats: `<WH1234>`, `{<WH1234>}`, `{H1234}`, `(H1234)`
  - Extract term boundaries between SN tags

- [ ] **T-03**: Implement regex patterns for all SN formats
  - Hebrew patterns: `H\d+`, `WH\d+`
  - Greek patterns: `G\d+`, `WG\d+`
  - Handle wrapped formats: `<>`, `{}`, `()`

- [ ] **T-04**: Extract UNV+SN term boundaries for string matching
  - Parse: "神<G2316>愛<G25>世人<G2889>甚至<G5620>獨生<G3439>子<G5207>"
  - Output: [("神", ["G2316"]), ("愛", ["G25"]), ("世人", ["G2889"]), ("甚至", ["G5620"]), ("獨生", ["G3439"]), ("子", ["G5207"])]
  - These terms will be used for character matching against target versions (LCC)

- [ ] **T-05**: Unit Tests T011-T015
  - T011: Parse UNV+SN and extract boundaries ✓
  - T012: Handle all four SN formats ✓
  - T013: Multiple SNs per term ("獨生子<H1121><H3173>")
  - T014: Verses with no Strong's Numbers
  - T015: Edge case: consecutive SN tags

### Phase 2: Boundary Correction Engine ⏳ Week 2

- [ ] **T-06**: Create BoundaryCorrector class
  - New file: `src/core/boundary_corrector.py`
  - Method: `correct_segmentation(target_text, initial_segments, unv_sn_boundaries)`
  - **Key**: Target text (LCC) stays LCC, only boundaries corrected via string matching

- [ ] **T-07**: Implement string matching and merge algorithm
  - Input: LCC text "上帝這樣地愛世人獨生子", LCC segments ["上帝", "獨", "生子"]
  - UNV+SN reference: [("愛", [G25]), ("世人", [G2889]), ("獨生", [G3439]), ("子", [G5207])]
  - Match: "愛", "世人", "獨生", "子" found in LCC text
  - Output: ["上帝", "這樣地", "愛", "世人", "獨生", "子"] (LCC text preserved!)

- [ ] **T-08**: Implement split algorithm for matched terms
  - Input: LCC segment "下獨生子", UNV+SN has "獨生" and "子" as separate
  - Match check: "獨生" found, "子" found in LCC text
  - Output: Split as ["獨生", "子"] (ignore "下獨" part if no match)
  - **Critical**: Only split based on UNV+SN terms that exist in target text

- [ ] **T-09**: Handle unmatched segments (safe fallback)
  - LCC "上帝" vs UNV "神" - no character match
  - Action: Keep LCC "上帝" from initial segmentation (jieba)
  - No correction attempted for character-mismatched segments
  - Log unmatched segments for Phase 2

- [ ] **T-10**: Correction metrics tracking
  - Count: matched terms, corrected boundaries, unchanged segments
  - Character match rate: % of UNV+SN terms found in target text
  - Correction success rate: % of matched terms successfully corrected
  - Report: "Matched 15/20 terms (75%), corrected 12/15 boundaries (80%)"

- [ ] **T-11**: Unit Tests T016-T020
  - T016: Correct LCC with jieba initial segmentation ✓
  - T017: Correct LCC with pkuseg initial segmentation ✓
  - T018: Correct RCUV2010 with LAC initial segmentation ✓
  - T019: Verify target text never changes to UNV ✓
  - T020: Test unmatched segments keep initial segmentation ✓

### Phase 3: CLI Integration ⏳ Week 3

- [ ] **T-12**: Add `--correct-with-sn` flag to segment.py
  - Boolean flag, default: False
  - **Works with target versions**: lcc, rcuv2010, rcuv (NOT unv - that would be redundant)
  - Recommended usage: `--version lcc --correct-with-sn`
  - Error if used with UNV: "SN correction targets other versions. UNV already has Strong's Numbers."

- [ ] **T-13**: Integrate correction pipeline
  - Flow: Fetch target (LCC) → Initial segment (jieba) → Fetch UNV+SN → Match & Correct → Display
  - **Verify**: LCC text before = LCC text after (only boundaries change)
  - Handle API errors gracefully

- [ ] **T-14**: Display before/after comparison (target version preserved)
  ```
  Target Version: LCC (呂振中譯本)
  Text: 上帝這樣地愛世人，甚至賜下獨生子

  Before (jieba):  上帝 | 這樣 | 地 | 愛 | 世人 | 賜 | 下獨 | 生子
  After (SN-corrected): 上帝 | 這樣地 | 愛 | 世人 | 甚至 | 賜下 | 獨生 | 子
                                          ↑     ↑      ↑           ↑     ↑
                                          Corrected from UNV+SN matching
  ```

- [ ] **T-15**: Show correction metrics
  ```
  UNV+SN Reference: 20 terms extracted
  Character Matching: 15/20 terms found in LCC (75% match rate)
  Corrections Applied: 12/15 matched boundaries corrected (80% success)
  Unchanged Segments: 5 (no character match with UNV, kept jieba segmentation)
  Target Text: ✅ Preserved (LCC text unchanged)
  ```

- [ ] **T-16**: Handle multi-verse correction
  - Apply corrections across verse ranges
  - Aggregate metrics

- [ ] **T-17**: Integration Tests T021-T025
  - T021: CLI `--version lcc --correct-with-sn` works ✓
  - T022: Display shows LCC text preserved before/after ✓
  - T023: Multi-verse LCC correction (John 3:16-17) ✓
  - T024: Test RCUV2010 version correction ✓
  - T025: Edge case: verse with no character matches (all segments unchanged)

### Phase 4: Validation & Documentation ⏳ Week 4

- [ ] **T-18**: Test with 100 LCC verses (Old Testament)
  - Sample: Genesis 1-3, Exodus 20, Psalms 23, Isaiah 53
  - Measure: character match rate, correction success rate
  - Verify: LCC text preserved in all cases

- [ ] **T-19**: Test with 100 LCC verses (New Testament)
  - Sample: Matthew 5-7, John 3, Romans 8, Revelation 21-22
  - Test with all 4 segmenters: jieba, pkuseg, LAC, stanza
  - Verify: LCC text preserved across all segmenters

- [ ] **T-20**: Measure correction effectiveness
  - Metric 1: Character match rate (target: ≥60% of UNV+SN terms found)
  - Metric 2: Correction success rate (target: ≥80% of matched terms corrected)
  - Metric 3: Text preservation (target: 100% - target text never changes to UNV)
  - Analyze unmatched patterns for Phase 2

- [ ] **T-21**: Document edge cases
  - Verses with no Strong's Numbers in UNV
  - Verses with no character matches (all segments kept from jieba)
  - Partial matches (some terms matched, some not)
  - API failures (fallback to initial segmentation)

- [ ] **T-22**: Update documentation
  - README.md: Add --correct-with-sn examples showing LCC → LCC correction
  - ARCHITECTURE_EXPLAINED.md: Document string matching algorithm
  - FHL_API_REFERENCE.md: Clarify UNV is only version with SN
  - Add examples showing target text preservation

- [ ] **T-23**: Create user guide
  - When to use --correct-with-sn (LCC, RCUV2010, not UNV)
  - Understanding character match rate vs correction success rate
  - What to expect: partial correction (matched segments only)
  - Phase 2 preview: semantic alignment for unmatched segments

## Test Coverage Requirements

### Unit Tests (T011-T020)
- **Coverage Target**: ≥90% for new code
- **Files**: `strongs_parser.py`, `boundary_corrector.py`
- **Framework**: pytest

### Integration Tests (T021-T025)
- **Coverage Target**: All CLI paths
- **End-to-end**: Fetch → Parse → Correct → Display
- **Performance**: <100ms per verse

### Validation Tests
- **Real Data**: 200 LCC verses across OT/NT
- **Target Versions**: LCC (primary), RCUV2010, RCUV (secondary)
- **All Segmenters**: jieba, pkuseg, LAC, stanza
- **Critical Check**: Target text preserved (LCC stays LCC, never becomes UNV)

## Dependencies

### External
- None (uses existing `requests` library)

### Internal
- `src/api/fhl_client.py` (existing)
- `src/plugins/segmenters/` (existing)
- `src/core/plugin_manager.py` (existing)

## Success Metrics

- [ ] All 15 new tests (T011-T025) passing
- [ ] Character match rate ≥60% (UNV+SN terms found in target version)
- [ ] Correction success rate ≥80% (matched terms corrected)
- [ ] Text preservation 100% (target text never changes to UNV)
- [ ] Performance <100ms per verse
- [ ] Zero regressions in existing tests (T001-T010)

## Risk Mitigation

- [ ] **API Rate Limiting**: Implement caching for UNV+SN fetches
- [ ] **Incomplete SN Data**: Graceful fallback to initial segmentation
- [ ] **Low Character Match Rate**: Accept partial correction, document unmatched segments for Phase 2
- [ ] **Text Corruption Risk**: Add assertion to verify target text never changes to UNV
- [ ] **Performance**: Profile and optimize string matching algorithms

## Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Parsing | StrongsNumberParser + T011-T015 |
| 2 | Correction | BoundaryCorrector + T016-T020 |
| 3 | Integration | CLI flags + T021-T025 |
| 4 | Validation | Testing + Documentation |

**Total Estimated Time**: 4 weeks

---

**Note**: This proposal depends on existing FHL API infrastructure. Proceed only after user approval.
