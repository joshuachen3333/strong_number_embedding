# Proposal: Add Similarity-Based Term Refinement

**Change ID**: `add-similarity-based-refinement`
**Status**: Proposed
**Date**: 2025-11-01
**Priority**: High
**Phase**: 1.5 (Enhancement to existing SN-based correction)

## Why

The current SN-based segmentation correction (Phase 1) has a fundamental limitation: **FHL's coarse-grained boundaries**. FHL sometimes tags entire phrases with a single Strong's Number when only a subset of that phrase semantically corresponds to the SN.

**Example Problem**:
```
FHL Annotation: 甚至將他的獨生<G3439>子<G5207>賜給
                     └──────┬─────┘
                      Coarse boundary

Strong's G3439: μονογενής = "only begotten" = "獨生的"

Reality:
  "將他的" - grammatical particles (NOT G3439)
  "獨生"   - ✅ semantic match for G3439
```

**Impact**: Phase 1 treats "將他的獨生" as atomic, causing:
- Failed matches in target versions (LCC doesn't contain "將他的獨生")
- Incorrect term-to-SN associations
- Lower match rates (~57% vs ≥70% target)

**Solution**: Use Strong's Dictionary semantic meanings to **refine coarse boundaries into precise terms** before matching to target versions. This two-stage approach:
1. **Stage 1**: Use SN semantics ("獨生的") to find precise term ("獨生") within UNV's coarse boundary
2. **Stage 2**: Match refined term to target version with character variant handling

**Expected Improvement**: Match rate from ~57% → ≥70%, fixing issues documented in CURRENT_STATUS.md.

## What Changes

- Add FHL Strong's Dictionary API integration (`sd.php` endpoint)
- Add `StrongEntry` dataclass for dictionary responses
- Add `FHLClient.fetch_strong_dict()` method with caching
- Add `SimilarityMatcher` class for substring matching with edit distance
- Add character variant normalization system (爲→為, 衞→衛, 綫→線)
- Add `BoundaryCorrector.correct_with_refinement()` for two-stage correction
- Enhance `CorrectionMetrics` with refinement-specific stats
- Add `--use-refinement` CLI flag to `segment.py`
- Add `demo_similarity_refinement.py` for visualization
- Add comprehensive test suite (T026-T042) for refinement validation

## How

### Stage 1: UNV Term Refinement

For each `(coarse_term, SN)` pair from UNV+SN:
1. Fetch SN semantic meaning from FHL API (`sd.php`)
   - Example: `G3439` → "μονογενής" → "獨生的"
2. Generate all substrings (≥2 chars) of `coarse_term`
   - "將他的獨生" → ["將他", "他的", "的獨", "獨生", "將他的", ...]
3. Calculate similarity for each substring vs SN meaning
   - Use edit distance after character variant normalization
   - `similarity = 1.0 - (edit_distance / max_length)`
4. Return substring with highest similarity above threshold (0.6)
   - "獨生" matches "獨生的" with score ~0.67

**Output**: Refined UNV boundaries with precise terms

### Stage 2: Target Version Matching

1. Take refined terms from Stage 1
2. Match each term in target text (LCC)
   - Direct string match: `"獨生" in target_text`
   - Variant match: `normalize("獨生") in normalize(target_text)`
3. Apply boundary corrections (reuse Phase 1 logic)

**Output**: Corrected target version segmentation

### Implementation Components

**New Classes**:
- `StrongEntry` - Dictionary entry dataclass (sn, original, chinese_meaning, etc.)
- `SimilarityMatcher` - Substring extraction and similarity calculation
  - `find_best_substring(refTerm, origText, threshold)` → best match
  - `_normalize_variants(text)` → normalized text (爲→為)
  - `_similarity(s1, s2)` → score 0.0-1.0

**Enhanced Classes**:
- `FHLClient.fetch_strong_dict(sn, simplified)` → StrongEntry
- `BoundaryCorrector.correct_with_refinement(...)` → (corrected, metrics)

**Performance**:
- API caching: First verse ~1s, subsequent ~0ms per verse
- Substring complexity: O(n²) where n=coarse term length (5-10 chars)
- Target overhead: <150ms per verse

## Success Criteria

**Quantitative**:
- Character match rate: ≥70% (up from ~57%)
- Boundary accuracy: ≥65% (up from 55-62%)
- Performance overhead: <150ms per verse
- All existing tests (T001-T025) continue passing

**Qualitative**:
- Correctly refines coarse boundaries (e.g., "將他的獨生" → "獨生")
- Handles character variants transparently (因爲 matches 因為)
- Graceful fallback when refinement fails (use coarse term)
- Clear visualization of refinement stages in demos

## Testing

**New Tests (T026-T042)**:
- **T026-T028**: FHL API integration (Greek, Hebrew, error handling)
- **T029-T033**: Similarity matcher (substring extraction, variants, edge cases)
- **T034-T038**: Two-stage correction (end-to-end, improvement vs Phase 1)
- **T039-T042**: CLI integration and documentation

**Cumulative Testing**: All existing tests T001-T025 must pass (plugin architecture + Phase 1 correction)

## Impact

**Affected Components**:
- `src/api/fhl_client.py` - Add `fetch_strong_dict()` method
- `src/core/similarity_matcher.py` - New file
- `src/core/boundary_corrector.py` - Add `correct_with_refinement()` method
- `segment.py` - Add `--use-refinement` flag (optional)
- Demo scripts - Add refinement visualization

**Backwards Compatibility**: ✅ Fully compatible
- Phase 1 logic unchanged (existing `correct()` method)
- Refinement is opt-in via `--use-refinement` flag
- No breaking changes to existing APIs

## Risks

**Risk 1: FHL API availability**
- Mitigation: Cache responses, fallback to coarse terms

**Risk 2: Performance overhead**
- Mitigation: Leverage coarse boundaries (~40x fewer substrings than full verse)

**Risk 3: Ambiguous substring matches**
- Mitigation: Use threshold (0.6), prefer longer matches, fallback to coarse

**Risk 4: Incomplete character variants**
- Mitigation: Start with common variants (爲/為, 衞/衛, 綫/線), expand as discovered

## Related Work

- **Previous**: `add-sn-based-segmentation-correction` (Phase 1 - foundation)
- **Next**: `add-inter-version-term-boundary-mapping` (Phase 2 - full semantic alignment)

## Alternatives Considered

**Option A: Use entire verse for substring matching**
- ❌ Too slow: 30 chars → 435 substrings vs 5 chars → 10 substrings

**Option B: Skip refinement, only use coarse boundaries**
- ❌ Low match rate (~57%) doesn't meet target (≥70%)

**Option C: Use ML embeddings (BERT) for similarity**
- ⏰ Too complex for Phase 1.5, save for Phase 2

**Chosen: Edit distance with character variant normalization**
- ✅ Simple, fast, no training data required
- ✅ Good enough for common cases
- ✅ Upgradeable to ML in Phase 2

## References

- FHL Strong's Dictionary API: `https://bible.fhl.net/json/` (sd.php endpoint)
- Current implementation: `src/core/boundary_corrector.py` (Phase 1)
- Known issues: `CURRENT_STATUS.md` (match rate ~57%, character variants)
- User requirements: `prompt.history` entries 31-36
