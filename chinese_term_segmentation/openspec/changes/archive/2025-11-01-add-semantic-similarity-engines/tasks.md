# Tasks: Add Semantic Similarity Engines

## Phase 2.1: Architecture Refactor

### T201: Extract SemanticEngine Abstract Base Class
- [ ] Create `src/core/semantic_engine.py`
- [ ] Define `SemanticEngine(ABC)` with abstract methods:
  - [ ] `similarity(text1: str, text2: str) -> float`
  - [ ] `get_name() -> str`
- [ ] Add docstrings explaining interface contract
- [ ] Add type hints for all methods

**Acceptance Criteria**:
- Interface is importable and usable as base class
- Abstract methods raise NotImplementedError if not overridden
- Type hints pass mypy validation

---

### T202: Create EditDistanceEngine Wrapper
- [ ] Create `src/core/engines/` directory
- [ ] Create `src/core/engines/__init__.py`
- [ ] Create `src/core/engines/edit_distance_engine.py`
- [ ] Move edit distance logic from SimilarityMatcher to EditDistanceEngine
- [ ] Implement `similarity(text1, text2)` method
- [ ] Implement `get_name()` returning "edit-distance"
- [ ] Keep CharVariantNormalizer integration

**Acceptance Criteria**:
- EditDistanceEngine inherits from SemanticEngine
- All abstract methods implemented
- Produces identical results to current implementation
- CharVariantNormalizer still works correctly

---

### T203: Refactor SimilarityMatcher to Accept Engines
- [ ] Update `SimilarityMatcher.__init__()` signature:
  - [ ] Add optional `engine: SemanticEngine` parameter
  - [ ] Default to `EditDistanceEngine()` if not provided
- [ ] Replace direct edit distance calls with `self.engine.similarity()`
- [ ] Update `find_best_substring()` to use engine
- [ ] Ensure BoundaryCorrector still works

**Acceptance Criteria**:
- Can instantiate with custom engine: `SimilarityMatcher(engine=MyEngine())`
- Default behavior unchanged (uses EditDistanceEngine)
- All internal methods use `self.engine` instead of direct calculations

---

### T204: Update All Existing Tests
- [ ] Review all tests in `tests/` directory
- [ ] Update tests to explicitly use EditDistanceEngine where needed
- [ ] Ensure no tests are broken by refactoring
- [ ] Run full test suite: `python -m pytest tests/ -v`

**Acceptance Criteria**:
- All 60 currently-passing tests remain passing
- No regression in pass rate (60/80 baseline)
- Test coverage remains >80%
- Note: 18 pre-existing failing tests are not blocking (plugin/API issues)

---

### T205: Add Unit Tests for New Components
- [ ] Create `tests/test_semantic_engine_interface.py`
- [ ] **T034**: Test EditDistanceEngine implements interface correctly
  - [ ] Test `similarity()` returns float in [0, 1]
  - [ ] Test `get_name()` returns "edit-distance"
  - [ ] Test with various Chinese text pairs
- [ ] **T035**: Test SimilarityMatcher accepts and uses engine
  - [ ] Test with EditDistanceEngine
  - [ ] Test with mock custom engine
  - [ ] Verify engine methods are called
- [ ] **T036**: Test invalid engine raises appropriate error
  - [ ] Test with non-SemanticEngine object
  - [ ] Test with partially implemented engine

**Acceptance Criteria**:
- T034-T036 all pass
- Tests use proper mocking and assertions
- Edge cases covered (empty strings, None values, etc.)

---

### T206: Add CLI Flag for Engine Selection
- [ ] Update `segment.py` argparse configuration
- [ ] Add `--semantic-engine` argument with choices: `['edit-distance']`
- [ ] Default to 'edit-distance'
- [ ] Parse argument and instantiate correct engine
- [ ] Pass engine to SimilarityMatcher initialization

**Acceptance Criteria**:
- `./segment.py --help` shows `--semantic-engine` flag
- `--semantic-engine edit-distance` works correctly
- Invalid engine name shows helpful error message
- Default behavior (no flag) uses EditDistanceEngine

---

### T207: Integration Testing
- [ ] Test Genesis 3:3 still achieves 61.5% match rate
- [ ] Test with `--correct-with-sn` flag
- [ ] Test with `--use-refinement` flag
- [ ] Test with `--semantic-engine edit-distance` explicitly
- [ ] Test with `--debug` mode enabled
- [ ] Verify output format unchanged

**Command**:
```bash
./segment.py --engs gen --chap 3 --sec 3 --version lcc \
  --seg pkuseg --correct-with-sn --use-refinement \
  --semantic-engine edit-distance
```

**Acceptance Criteria**:
- Match rate: 61.5% ± 2%
- No errors or warnings
- Output format identical to previous version
- Performance within 10% of baseline

---

### T208: Update Documentation
- [ ] Update `README.md`:
  - [ ] Add `--semantic-engine` flag to CLI usage section
  - [ ] Explain engine concept briefly
- [ ] Update `ARCHITECTURE_EXPLAINED.md`:
  - [ ] Add semantic engine section
  - [ ] Document plugin architecture
  - [ ] Add diagram of engine relationships
- [ ] Update `CURRENT_STATUS.md`:
  - [ ] Mark Phase 2.1 as "In Progress" → "Complete"
  - [ ] Update capability summary
- [ ] Update CLI help text in `segment.py`:
  - [ ] Add helpful description for `--semantic-engine`

**Acceptance Criteria**:
- Documentation is clear and accurate
- Examples are tested and work
- No broken links or references
- Markdown formatting is correct

---

### T209: Performance Validation
- [ ] Benchmark edit distance performance before/after refactor
- [ ] Ensure no regression (target: <5% slowdown)
- [ ] Profile memory usage
- [ ] Run timing tests on 100 verse samples

**Command**:
```bash
python -m pytest tests/ -v --benchmark-only
```

**Acceptance Criteria**:
- Performance within 5% of baseline
- Memory usage within 10% of baseline
- No memory leaks detected

---

### T210: Final Validation and OpenSpec Check
- [ ] Run `openspec validate add-semantic-similarity-engines --strict`
- [ ] Ensure all deliverables are complete
- [ ] Run full test suite one final time
- [ ] Check git status for uncommitted changes
- [ ] Review commit messages for clarity

**Acceptance Criteria**:
- OpenSpec validation passes
- All tests pass (23/23)
- Git history is clean
- No TODO comments left in code
- Ready for merge

---

## Deliverables Checklist

### Code Files
- [ ] `src/core/semantic_engine.py` - Abstract base class
- [ ] `src/core/engines/__init__.py` - Package initialization
- [ ] `src/core/engines/edit_distance_engine.py` - Baseline implementation
- [ ] `src/core/similarity_matcher.py` - Refactored to use engines
- [ ] `segment.py` - CLI with `--semantic-engine` flag

### Test Files
- [ ] `tests/test_semantic_engine_interface.py` - T034-T036
- [ ] All existing tests updated and passing

### Documentation
- [ ] `README.md` updated
- [ ] `ARCHITECTURE_EXPLAINED.md` updated
- [ ] `CURRENT_STATUS.md` updated
- [ ] CLI help text updated

### OpenSpec
- [x] `proposal.md` complete
- [x] `tasks.md` complete (this file)
- [ ] `design.md` complete
- [ ] Validation passing

---

## Testing Matrix

| Test Case | EditDistanceEngine | Expected Result |
|-----------|-------------------|-----------------|
| Genesis 3:3 | ✓ | 61.5% match rate |
| John 3:16 | ✓ | ~55% match rate |
| With --correct-with-sn | ✓ | SN correction works |
| With --use-refinement | ✓ | Refinement works |
| With --debug | ✓ | Debug output shown |
| Performance | ✓ | <5% regression |

---

## Success Criteria Summary

**Must Have** (blocking merge):
- ✅ All 60 currently-passing tests remain passing (baseline: 60/80)
- ✅ EditDistanceEngine produces identical results
- ✅ CLI flag works correctly
- ✅ Performance unchanged (<5% regression)
- ✅ Documentation updated
- ✅ OpenSpec validation passes

**Should Have** (nice to have):
- Code coverage >90%
- Benchmark suite created
- Architecture diagrams updated

**Won't Have** (deferred to Phase 2.2):
- Neural engine implementations
- Configuration file support
- Benchmark dataset

---

## Notes

- **Backward Compatibility**: Critical requirement. No breaking changes allowed.
- **Testing**: Run tests frequently during refactoring to catch regressions early.
- **Performance**: Profile before and after to ensure no degradation.
- **Documentation**: Update as you go, not at the end.
- **OpenSpec**: Validate frequently with `openspec validate --strict`.

---

**Total Estimated Effort**: 1-2 days (12-16 hours)

**Status**: Not Started
**Last Updated**: 2025-11-01
