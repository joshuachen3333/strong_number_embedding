# Proposal: Add Semantic Similarity Engines

## Metadata
- **Change ID**: `add-semantic-similarity-engines`
- **Type**: Enhancement
- **Status**: Proposed
- **Created**: 2025-11-01
- **Affected Components**: `src/core/similarity_matcher.py`, CLI, tests
- **Related Changes**: `add-similarity-based-refinement` (predecessor)

## Summary

Replace the character-based edit distance approach in `SimilarityMatcher` with pluggable semantic similarity engines that understand meaning, not just character overlap. This addresses the fundamental limitation preventing Phase 1.5 from exceeding 60-65% match rates.

## Motivation

### Current Problem

Phase 1.5 refinement (commit `0dd2830`) successfully improved match rates to 61.5% on Genesis 3:3, but has hit a ceiling due to edit distance limitations:

```python
# Edit Distance Failures (Current):
"神" vs "上帝"     → 0.0 similarity ❌ (synonyms, different chars)
"碰觸" vs "摸"     → 0.0 similarity ❌ (synonyms, different chars)
"果實" vs "果子"   → 0.4 similarity ❌ (related, below threshold)
"獨一無二的" vs "將他的獨生" → 0.2 ❌ (semantic relation lost)
```

**Root Cause**: Edit distance measures **character similarity**, not **semantic meaning**.

### User Impact

Current limitations affect biblical Chinese segmentation accuracy:
- Synonyms are not recognized (神/上帝, 碰觸/摸)
- Semantic relationships missed (獨一無二的 means "only begotten")
- Match rate ceiling at ~60-65% across verses
- Cannot handle cross-translation term alignment

### Success from Phase 1.5

What IS working (validates the approach):
- ✅ Substring extraction: '那棵樹' → '樹' (works because substring)
- ✅ Character variants: '爲' → '為' (normalization works)
- ✅ Refinement architecture: 40% of terms successfully refined
- ✅ Text preservation: 100% target text integrity

**Phase 1.5 proved the concept works**, but needs semantic understanding to reach 80%+ accuracy.

## Requirements

### Functional Requirements

#### R201: SemanticEngine Interface
Define abstract base class for all semantic similarity engines:
```python
class SemanticEngine(ABC):
    @abstractmethod
    def similarity(self, text1: str, text2: str) -> float:
        """Return semantic similarity score [0, 1]"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return engine identifier for logging/metrics"""
        pass
```

#### R202: Minimum 3 Engine Implementations
Implement at least 3 engines in Phase 2.1-2.2:
1. **EditDistanceEngine** (baseline, existing code wrapped)
2. **SentenceTransformerEngine** (primary, Chinese model)
3. **ChineseBertEngine** (alternative, BERT-based)

#### R203: Benchmark Framework
Create framework to compare engines objectively:
- Test dataset with 50+ biblical term pairs
- Metrics: accuracy, speed, memory usage
- Comparison output: table format for analysis

#### R204: CLI Integration
Add engine selection to CLI:
```bash
--semantic-engine {edit-distance,sentence-transformer,bert}
```

#### R205: Configuration File Support
Support YAML configuration for engine settings:
```yaml
semantic_engines:
  default: sentence-transformer
  engines:
    sentence-transformer:
      model: shibing624/text2vec-base-chinese
      device: cpu
```

#### R206: Backward Compatibility
Default behavior unchanged:
- Default engine: EditDistanceEngine
- Existing tests must pass
- No breaking changes to existing API

### Non-Functional Requirements

#### NF201: Performance
- EditDistance baseline: <1ms per query
- Neural engines: <50ms per query (before caching)
- Memory footprint: <500MB for base deployment

#### NF202: Accuracy
- Baseline (EditDistance): 60-65% (current)
- SentenceTransformer target: 70-75%
- ChineseBERT target: 65-70%

#### NF203: Extensibility
- Easy to add new engines (plugin pattern)
- No core code changes required for new engines
- Configuration-driven engine selection

## Proposed Solution

### Architecture

**Plugin-Based Semantic Engine System**:

```
┌─────────────────────────────────────┐
│      SimilarityMatcher              │
│  (existing class, refactored)       │
└─────────────────┬───────────────────┘
                  │ uses
                  ▼
┌─────────────────────────────────────┐
│      SemanticEngine (ABC)           │
│  - similarity(text1, text2) → float │
│  - get_name() → str                 │
└─────────────────┬───────────────────┘
                  │ implements
         ┌────────┴─────────┬─────────────┐
         ▼                  ▼             ▼
┌────────────────┐  ┌─────────────┐  ┌──────────┐
│ EditDistance   │  │ Sentence    │  │ Chinese  │
│ Engine         │  │ Transformer │  │ BERT     │
│ (baseline)     │  │ Engine      │  │ Engine   │
└────────────────┘  └─────────────┘  └──────────┘
```

### Implementation Phases

#### Phase 2.1: Architecture Refactor (Current Proposal)
**Goal**: Make engines pluggable without breaking existing functionality

Tasks:
1. Extract `SemanticEngine` abstract base class
2. Wrap existing edit distance code in `EditDistanceEngine`
3. Refactor `SimilarityMatcher.__init__()` to accept engine parameter
4. Add `--semantic-engine` CLI flag with "edit-distance" as default
5. Update all tests to explicitly use `EditDistanceEngine`
6. Validate backward compatibility (all 60 currently-passing tests remain passing)

**Deliverables**:
- `src/core/semantic_engine.py` (abstract base)
- `src/core/engines/edit_distance_engine.py` (baseline)
- Refactored `src/core/similarity_matcher.py`
- Updated CLI in `segment.py`
- All existing tests passing

**Success Criteria**:
- ✅ All 60 currently-passing tests remain passing
- ✅ Can swap engines via CLI flag
- ✅ Performance unchanged (still ~1ms)
- ✅ No regressions in accuracy

#### Phase 2.2: Neural Engine Implementation (Next Proposal)
**Goal**: Add semantic understanding with neural models

Tasks (future):
1. Implement `SentenceTransformerEngine`
2. Implement `ChineseBertEngine`
3. Create benchmark dataset
4. Run comparative benchmarks
5. Document results and recommendations

**Not in this proposal** - will be separate OpenSpec change.

## Impact Analysis

### Benefits

**Immediate (Phase 2.1)**:
- ✅ Clean architecture for future engines
- ✅ No performance degradation
- ✅ Backward compatible
- ✅ Foundation for Phase 2.2

**Future (Phase 2.2+)**:
- 📈 Match rate: 60% → 75-85%
- 🧠 Semantic understanding: synonyms recognized
- 🌏 Cross-translation alignment possible
- 📊 Biblical-specific optimization feasible

### Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Regression in existing tests | Medium | High | Comprehensive testing, backward compat |
| Performance degradation | Low | Medium | Keep EditDistance as default |
| Architecture too complex | Low | Low | Simple ABC pattern, well-documented |
| Neural engines too slow | Medium | High | Caching strategy (Phase 2.3) |

### Breaking Changes

**None** - this is a refactoring with backward compatibility:
- Default engine remains EditDistance
- Existing API unchanged
- All tests pass without modification
- Optional feature (new CLI flag)

## Alternatives Considered

### Alternative 1: Keep Edit Distance, Add Preprocessing
**Approach**: Add synonym dictionary, character variant expansion
**Pros**: Simple, no architecture change
**Cons**: Doesn't solve semantic similarity problem, still limited to 65%
**Decision**: Rejected - doesn't address root cause

### Alternative 2: Direct Neural Integration (No Plugin Pattern)
**Approach**: Hard-code SentenceTransformer into SimilarityMatcher
**Pros**: Faster to implement, simpler initially
**Cons**: Not extensible, hard to test different engines, vendor lock-in
**Decision**: Rejected - limits future flexibility

### Alternative 3: Full Rewrite with ML Framework
**Approach**: Replace entire matching system with end-to-end neural model
**Pros**: Maximum accuracy potential
**Cons**: 3-6 months, expensive, loses existing work, high risk
**Decision**: Rejected - progressive approach is safer

## Dependencies

### Technical Dependencies

**Phase 2.1 (This Proposal)**:
- No new dependencies
- Uses existing Python stdlib

**Phase 2.2 (Future)**:
- `transformers` (Hugging Face)
- `sentence-transformers`
- `torch` (PyTorch)

### Project Dependencies

**Prerequisites**:
- ✅ Phase 1.5 complete (commit `0dd2830`)
- ✅ Planning documents complete (commit `9a8c6ba`)

**Blocks**:
- Phase 2.2: Neural engines (waits for Phase 2.1 architecture)
- Phase 2.3: Biblical optimization (waits for Phase 2.2 results)

## Testing Strategy

### Unit Tests

**New Tests**:
- `test_semantic_engine_interface.py` (T034-T036)
  - T034: EditDistanceEngine implements interface correctly
  - T035: SimilarityMatcher accepts and uses engine
  - T036: Invalid engine raises appropriate error

**Modified Tests**:
- All existing tests explicitly use `EditDistanceEngine()`
- Ensures backward compatibility validation

### Integration Tests

**Regression Tests**:
- Run all 60 currently-passing tests with new architecture
- Verify Genesis 3:3 still achieves 61.5% with EditDistance
- CLI tests: ensure `--semantic-engine edit-distance` works
- Note: 18 failing tests and 2 skipped tests are pre-existing issues (not blocking)

**Future Tests** (Phase 2.2):
- Benchmark tests comparing engines
- Accuracy tests on biblical dataset

### Manual Testing

```bash
# Test backward compatibility
./segment.py --engs gen --chap 3 --sec 3 --version lcc --seg pkuseg --correct-with-sn --use-refinement

# Test explicit engine selection
./segment.py --engs gen --chap 3 --sec 3 --version lcc --seg pkuseg --correct-with-sn --use-refinement --semantic-engine edit-distance

# Test with debug mode
./segment.py --engs gen --chap 3 --sec 3 --version lcc --seg pkuseg --correct-with-sn --use-refinement --semantic-engine edit-distance --debug
```

## Documentation

### User Documentation

**Updates Required**:
- README.md: Add `--semantic-engine` flag documentation
- CLI help text: Document new flag
- SEMANTIC_SIMILARITY_PLAN.md: Mark Phase 2.1 as "In Progress"

### Developer Documentation

**New Documents**:
- Architecture guide for adding new engines
- SemanticEngine interface specification
- Testing guide for engines

**Updates Required**:
- CURRENT_STATUS.md: Update to Phase 2.1
- ARCHITECTURE_EXPLAINED.md: Add semantic engine section

## Timeline

**Estimated Effort**: 1-2 days

**Day 1** (Architecture):
- Extract SemanticEngine interface (2 hours)
- Create EditDistanceEngine wrapper (2 hours)
- Refactor SimilarityMatcher (2 hours)
- Update tests (2 hours)

**Day 2** (CLI & Validation):
- Add CLI flag (1 hour)
- Integration testing (2 hours)
- Documentation (2 hours)
- Final validation (1 hour)

**Buffer**: 0.5 days for unexpected issues

## Success Metrics

### Phase 2.1 Success Criteria

**Must Have**:
- ✅ All 60 currently-passing tests remain passing (baseline: 60/80 passing)
- ✅ SemanticEngine interface defined and used
- ✅ EditDistanceEngine wraps existing code
- ✅ CLI flag `--semantic-engine` works
- ✅ Performance unchanged (still ~1ms)
- ✅ Accuracy unchanged (still 61.5% on Genesis 3:3)

**Should Have**:
- ✅ Code coverage >90% for new code
- ✅ Documentation updated
- ✅ Clean commit history

**Nice to Have**:
- Configuration file support (YAML)
- Benchmark framework stub

### Phase 2.2 Success Criteria (Future)

**Target Metrics** (not in this proposal):
- Accuracy: >75% on biblical benchmark
- Speed: <50ms per query (before caching)
- Synonym recognition: >80% success rate

## Approval Checklist

Before implementation:
- [ ] Requirements reviewed and approved
- [ ] Architecture reviewed and approved
- [ ] Testing strategy reviewed and approved
- [ ] Timeline is realistic
- [ ] Dependencies are acceptable
- [ ] Backward compatibility guaranteed

## References

**Related Documents**:
- `SEMANTIC_SIMILARITY_PLAN.md` - Overall testing and implementation plan
- `SEMANTIC_ENGINE_TECHNICAL_SPECS.md` - Detailed engine implementations
- `SEMANTIC_ENGINE_STRATEGY.md` - 10 strategic considerations

**Related Commits**:
- `0dd2830` - Phase 1.5 completion (refinement working)
- `9a8c6ba` - Planning documents added
- `735b86c` - `--use-refinement` CLI flag
- `a21806c` - Two-stage refinement implementation

**Related Changes**:
- `add-similarity-based-refinement` - Predecessor (reverted then completed)
- `add-sn-based-segmentation-correction` - Phase 1 foundation

---

**Prepared by**: Claude Code
**Review Required**: Architecture, Testing Strategy, Timeline
**Next Step**: Create `tasks.md` with implementation checklist
