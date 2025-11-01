# Implementation Tasks: add-similarity-based-refinement

## Phase 1.5.1: FHL Strong's Dictionary Integration (Week 1)

### API Integration
- [ ] Add `StrongEntry` dataclass to `src/api/fhl_client.py`
  - [ ] Fields: `sn`, `original`, `chinese_meaning`, `english_meaning`, `related`
  - [ ] Add `__repr__` for debugging
- [ ] Implement `fetch_strong_dict()` method in `FHLClient`
  - [ ] Testament detection: G prefix → N=0 (NT), H prefix → N=1 (OT)
  - [ ] Parameter construction: strip prefix, convert to numeric
  - [ ] Request execution with timeout (10s)
  - [ ] Response parsing and validation
  - [ ] Extract Chinese meaning from `dic_text` (【...】 pattern)
- [ ] Add in-memory caching for Strong's entries
  - [ ] Cache key: `f"{sn}_{simplified}"`
  - [ ] Session-scoped (no persistence)
- [ ] Error handling
  - [ ] Network errors (timeout, connection failure)
  - [ ] HTTP errors (404, 500)
  - [ ] JSON parse errors
  - [ ] Missing/malformed dictionary entries
  - [ ] Log warnings, return None for graceful fallback

### Unit Tests (T026-T028)
- [ ] T026: Fetch Greek Strong's Number
  - [ ] Input: "G3439"
  - [ ] Expected: sn="3439", original="μονογενής", chinese_meaning contains "獨生"
  - [ ] Verify testament N=0
- [ ] T027: Fetch Hebrew Strong's Number
  - [ ] Input: "H430"
  - [ ] Expected: sn="430", original="אֱלֹהִים", chinese_meaning contains "神"
  - [ ] Verify testament N=1
- [ ] T028: Error handling
  - [ ] Test missing entry (e.g., "G99999")
  - [ ] Test network failure (mock)
  - [ ] Test malformed response
  - [ ] Verify returns None gracefully

## Phase 1.5.2: Similarity Matcher Implementation (Week 2)

### Core Matcher Class
- [ ] Create `src/core/similarity_matcher.py`
- [ ] Implement `SimilarityMatcher` class
  - [ ] `__init__()` - Load character variant map
  - [ ] `find_best_substring()` - Main entry point
  - [ ] `_similarity()` - Calculate similarity score
  - [ ] `_normalize_variants()` - Character normalization
  - [ ] `_edit_distance()` - Levenshtein distance
  - [ ] `_load_character_variants()` - Variant mapping

### Substring Matching Logic
- [ ] Implement `find_best_substring(refTerm, origText, threshold=0.6)`
  - [ ] Generate all substrings of origText (length ≥ 2)
  - [ ] Skip single-character substrings
  - [ ] Calculate similarity for each substring
  - [ ] Collect candidates above threshold
  - [ ] Sort by: (1) similarity score, (2) length (prefer longer)
  - [ ] Return best match or None

### Similarity Calculation
- [ ] Implement `_similarity(s1, s2)`
  - [ ] Normalize both strings (character variants)
  - [ ] Calculate edit distance
  - [ ] Normalize by max length: `1.0 - (distance / max_len)`
  - [ ] Return score 0.0-1.0

### Character Variant Normalization
- [ ] Implement `_normalize_variants(text)`
  - [ ] Apply variant map: 爲→為, 衞→衛, 綫→線
  - [ ] Return normalized text
- [ ] Implement `_load_character_variants()`
  - [ ] Return dict of common biblical variants
  - [ ] Documented with Unicode codepoints
  - [ ] Expandable for future discoveries

### Unit Tests (T029-T033)
- [ ] T029: Substring extraction
  - [ ] refTerm="獨生的", origText="將他的獨生"
  - [ ] Expected: "獨生" (highest similarity)
- [ ] T030: Character variant matching
  - [ ] refTerm="因為" (U+70BA), origText="因爲天國" (U+7232)
  - [ ] Expected: "因爲" (matches after normalization)
- [ ] T031: Edit distance accuracy
  - [ ] Test identical strings: distance=0, similarity=1.0
  - [ ] Test single char diff: appropriate score
- [ ] T032: Threshold filtering
  - [ ] Substrings below threshold rejected
  - [ ] Returns None if all below threshold
- [ ] T033: Edge cases
  - [ ] Empty strings
  - [ ] No match (completely different text)
  - [ ] Single character origText (skip)

## Phase 1.5.3: Two-Stage Correction Integration (Week 3)

### Enhance BoundaryCorrector
- [ ] Add `correct_with_refinement()` method to `BoundaryCorrector`
  - [ ] Accept same parameters as `correct()`
  - [ ] Parse coarse boundaries (reuse existing parser)
  - [ ] Call Stage 1: refine terms
  - [ ] Call Stage 2: match to target
  - [ ] Apply corrections (reuse existing logic)
  - [ ] Calculate enhanced metrics
- [ ] Implement `_refine_term(coarse_term, sn)` (Stage 1)
  - [ ] Fetch Strong's entry via `fhl_client.fetch_strong_dict(sn)`
  - [ ] Handle None return (API failure)
  - [ ] Call `matcher.find_best_substring()`
  - [ ] Fallback to coarse_term if refinement fails
  - [ ] Cache refinement results within session
- [ ] Implement `_find_matches_with_variants(target_text, refined_terms)` (Stage 2)
  - [ ] Try direct string match first
  - [ ] Try variant-normalized match if direct fails
  - [ ] Collect all matched terms
  - [ ] Return set of matched terms
- [ ] Add refinement caching
  - [ ] Cache key: `(coarse_term, sn)`
  - [ ] Session-scoped dict
  - [ ] Clear on new verse

### Enhanced Metrics
- [ ] Extend `CorrectionMetrics` dataclass
  - [ ] Add `refinement_rate: float` - % of coarse terms refined
  - [ ] Add `variant_match_rate: float` - % matched via variants
  - [ ] Add `stage1_precision: float` - Refinement accuracy
  - [ ] Add `stage2_recall: float` - Target matching coverage
- [ ] Update `_calculate_metrics()` to compute new fields

### Unit Tests (T034-T038)
- [ ] T034: End-to-end refinement (John 3:16)
  - [ ] Verify coarse "將他的獨生" → refined "獨生"
  - [ ] Verify "獨生" matches in LCC
  - [ ] Check improved match rate vs Phase 1
- [ ] T035: Genesis 1:1 improvement
  - [ ] Known low match rate case
  - [ ] Verify refinement improves results
- [ ] T036: Multiple SNs per coarse term
  - [ ] Handle terms with 2+ SNs
  - [ ] Use first SN for refinement
- [ ] T037: Missing SN dictionary entry
  - [ ] API returns None
  - [ ] Verify fallback to coarse term works
- [ ] T038: Performance benchmark
  - [ ] 100 verses < 15 seconds total
  - [ ] <150ms overhead per verse
  - [ ] Verify caching reduces API calls

## Phase 1.5.4: CLI & Demo Integration (Week 4)

### CLI Enhancement
- [ ] Add `--use-refinement` flag to `segment.py`
  - [ ] Boolean flag (default: False)
  - [ ] Help text explaining Phase 1.5 refinement
  - [ ] Validation: requires `--correct-with-sn` to be enabled
- [ ] Update correction logic in segment.py
  - [ ] Check `--use-refinement` flag
  - [ ] Call `correct_with_refinement()` if enabled
  - [ ] Call `correct()` (Phase 1) if disabled
  - [ ] Display which mode is active
- [ ] Enhance metrics display
  - [ ] Show refinement stats if Phase 1.5
  - [ ] Color-code improvement vs Phase 1
  - [ ] Display stage-by-stage breakdown

### Demo Scripts
- [ ] Create `demo_similarity_refinement.py`
  - [ ] Three-way comparison: Phase 1 / Phase 1.5 / Reference
  - [ ] Show Stage 1: Coarse → Refined (with SN meanings)
  - [ ] Show Stage 2: Refined → Matched (in target)
  - [ ] Color-code: red=coarse, yellow=refined, green=matched
  - [ ] Display Strong's dictionary lookups
  - [ ] Show substring matching process
- [ ] Update `demo_sn_correction.py`
  - [ ] Add optional refinement mode
  - [ ] Side-by-side Phase 1 vs Phase 1.5

### Documentation
- [ ] Update `ARCHITECTURE_EXPLAINED.md`
  - [ ] Add Phase 1.5 section
  - [ ] Diagram of two-stage flow
  - [ ] Examples of refinement
- [ ] Update `CURRENT_STATUS.md`
  - [ ] Document Phase 1.5 completion
  - [ ] Update match rate stats
  - [ ] Mark character variant issue as resolved
- [ ] Create `SIMILARITY_REFINEMENT.md`
  - [ ] Detailed explanation of algorithm
  - [ ] Examples with real verses
  - [ ] Troubleshooting guide
- [ ] Update `README.md`
  - [ ] Add `--use-refinement` to CLI reference
  - [ ] Update feature list
  - [ ] Add Phase 1.5 to roadmap

### Integration Tests (T039-T042)
- [ ] T039: CLI flag works
  - [ ] `--use-refinement` enables Phase 1.5
  - [ ] Validation error if used without `--correct-with-sn`
- [ ] T040: Demo displays correctly
  - [ ] All three stages shown
  - [ ] Color coding works
  - [ ] No rendering errors
- [ ] T041: Phase 1 vs 1.5 comparison
  - [ ] Run same verse through both
  - [ ] Verify 1.5 improves match rate
  - [ ] Document differences
- [ ] T042: Documentation complete
  - [ ] All docs updated
  - [ ] Examples accurate
  - [ ] Help text clear

## Acceptance Criteria

- [ ] All tests T026-T042 pass
- [ ] All existing tests T001-T025 still pass (no regressions)
- [ ] Match rate improves: Phase 1 ~57% → Phase 1.5 ≥70%
- [ ] Performance: <150ms overhead per verse
- [ ] CLI `--use-refinement` flag works end-to-end
- [ ] Documentation complete and accurate
- [ ] Code reviewed and meets quality standards
- [ ] OpenSpec validation passes: `openspec validate --strict`

## Testing Summary

**Total New Tests**: 17
- API Integration: 3 tests (T026-T028)
- Similarity Matcher: 5 tests (T029-T033)
- Two-Stage Correction: 5 tests (T034-T038)
- CLI/Demo: 4 tests (T039-T042)

**Cumulative Coverage**: 42 tests (T001-T042)
- Plugin Architecture: T001-T010 (10 tests)
- Phase 1 SN Correction: T011-T025 (15 tests)
- Phase 1.5 Refinement: T026-T042 (17 tests)

**Performance Benchmarks**:
- [ ] Measure API latency (first vs cached)
- [ ] Measure substring generation time
- [ ] Measure end-to-end overhead per verse
- [ ] Compare Phase 1 vs Phase 1.5 execution time
