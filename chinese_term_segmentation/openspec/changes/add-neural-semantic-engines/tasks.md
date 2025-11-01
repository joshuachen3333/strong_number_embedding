# Tasks: Add Neural Semantic Engines (Phase 2.2)

## Overview
Implement neural semantic similarity engines to break through the 61.5% accuracy ceiling.

**Target**: 75-85% match rate (vs current 61.5%)

---

## Phase 2.2.1: SentenceTransformerEngine Implementation

### T301: Implement SentenceTransformerEngine
- [ ] Install dependencies (`sentence-transformers`, `torch`)
- [ ] Create `src/core/engines/sentence_transformer_engine.py`
- [ ] Implement SemanticEngine interface:
  - [ ] `similarity(text1, text2) → float`
  - [ ] `get_name() → str` returns "sentence-transformer"
- [ ] Add embedding generation:
  - [ ] Load model: `shibing624/text2vec-base-chinese`
  - [ ] Generate embeddings for input texts
  - [ ] Calculate cosine similarity
- [ ] Implement embedding cache:
  - [ ] LRU cache for repeated terms
  - [ ] Cache hit/miss metrics
- [ ] Add docstrings and type hints

**Acceptance Criteria**:
- Engine implements SemanticEngine interface
- Returns similarity scores in [0, 1] range
- Model loads successfully on first use
- Caching reduces repeated queries to <5ms
- Works with Chinese text

**Test Command**:
```python
from src.core.engines.sentence_transformer_engine import SentenceTransformerEngine
engine = SentenceTransformerEngine()
score = engine.similarity("神", "上帝")
assert 0.7 < score < 1.0  # Should recognize semantic similarity!
```

---

### T302: CLI Integration
- [ ] Update `segment.py` argparse:
  - [ ] Add `'sentence-transformer'` to `--semantic-engine` choices
  - [ ] Update help text
- [ ] Add engine instantiation in CLI:
  - [ ] Map `'sentence-transformer'` → `SentenceTransformerEngine()`
  - [ ] Handle model download on first use
  - [ ] Show progress/status messages
- [ ] Update `requirements.txt`:
  - [ ] Add `sentence-transformers>=2.2.0`
  - [ ] Add `torch>=2.0.0`
- [ ] Test CLI command:
  ```bash
  ./segment.py --engs gen --chap 3 --sec 3 --version lcc \
    --seg pkuseg --correct-with-sn --use-refinement \
    --semantic-engine sentence-transformer
  ```

**Acceptance Criteria**:
- `./segment.py --help` shows new engine option
- Engine selection works via CLI
- First-time use downloads model successfully
- Clear error messages if dependencies missing

---

### T303: Unit Testing
- [ ] Create `tests/test_sentence_transformer_engine.py`
- [ ] **T042**: Test interface compliance
  - [ ] Inherits from SemanticEngine
  - [ ] Implements all abstract methods
  - [ ] Returns float in [0, 1]
- [ ] **T043**: Test semantic understanding
  - [ ] Synonyms: `similarity("神", "上帝")` > 0.7
  - [ ] Related: `similarity("愛", "珍愛")` > 0.6
  - [ ] Unrelated: `similarity("神", "樹")` < 0.4
- [ ] **T044**: Test embedding caching
  - [ ] First call slower (embedding generation)
  - [ ] Second call faster (cache hit)
  - [ ] Cache hit rate tracked
- [ ] **T045**: Test error handling
  - [ ] Empty strings
  - [ ] Very long texts (>512 tokens)
  - [ ] Unicode edge cases

**Acceptance Criteria**:
- All 4 tests pass (T042-T045)
- Test coverage >85% for new engine
- Tests run in <30 seconds

---

### T304: Integration Testing
- [ ] Test Genesis 3:3 with SentenceTransformer:
  ```bash
  ./segment.py --engs gen --chap 3 --sec 3 --version lcc \
    --seg pkuseg --correct-with-sn --use-refinement \
    --semantic-engine sentence-transformer
  ```
- [ ] Measure match rate - **Target: ≥75%**
- [ ] Test Genesis 1:1 - Target: ≥80%
- [ ] Test John 3:16 - Target: ≥65%
- [ ] Create integration test suite:
  - [ ] `tests/test_integration_phase22.py`
  - [ ] T046: Genesis 3:3 with SentenceTransformer (≥75%)
  - [ ] T047: Comparative test (EditDistance vs SentenceTransformer)
  - [ ] T048: Performance regression test (<100ms per query)

**Acceptance Criteria**:
- Genesis 3:3: ≥75% match rate (vs 61.5% baseline)
- At least +10 percentage point improvement over EditDistance
- All existing 68+ tests still pass
- Text preservation: 100%

---

## Phase 2.2.2: Benchmarking Framework

### T305: Create Benchmark Suite
- [ ] Create `tests/benchmark_engines.py`
- [ ] Define benchmark dataset:
  - [ ] 20-50 test verses with known Strong's mappings
  - [ ] Mix of OT and NT verses
  - [ ] Various difficulty levels
- [ ] Implement metrics calculation:
  - [ ] Accuracy (match rate)
  - [ ] Precision, Recall, F1 score
  - [ ] Latency (avg, p50, p95, p99)
  - [ ] Memory usage
- [ ] Create comparison framework:
  - [ ] Run same test set on multiple engines
  - [ ] Generate comparison tables
  - [ ] Export to CSV/JSON
- [ ] Add visualization:
  - [ ] Accuracy comparison chart
  - [ ] Performance comparison chart

**Acceptance Criteria**:
- Benchmark suite runs successfully
- Compares at least 2 engines (EditDistance, SentenceTransformer)
- Generates machine-readable results (CSV/JSON)
- Clear visualization of improvements

**Example Output**:
```
Engine Comparison Results:
┌──────────────────────┬──────────┬──────────┬────────────┐
│ Engine               │ Accuracy │ Avg Time │ Memory    │
├──────────────────────┼──────────┼──────────┼────────────┤
│ edit-distance        │ 62.3%    │ 1.2ms    │ 10MB      │
│ sentence-transformer │ 78.5%    │ 45ms     │ 450MB     │
└──────────────────────┴──────────┴──────────┴────────────┘

Improvement: +16.2 percentage points ✨
```

---

### T306: Run Comparative Analysis
- [ ] Run benchmarks on full test set
- [ ] Generate detailed report:
  - [ ] Overall accuracy comparison
  - [ ] Per-verse breakdown
  - [ ] Performance analysis
  - [ ] Memory footprint analysis
- [ ] Document findings:
  - [ ] Where SentenceTransformer excels
  - [ ] Where EditDistance is sufficient
  - [ ] Performance/accuracy tradeoffs
- [ ] Create recommendation matrix:
  - [ ] When to use each engine
  - [ ] Hybrid engine opportunities

**Acceptance Criteria**:
- Comprehensive benchmark report generated
- Clear evidence of improvement (or lack thereof)
- Documented tradeoffs
- Recommendations for production use

---

## Phase 2.2.3: Optimization & Documentation

### T307: Performance Optimization
- [ ] Profile SentenceTransformerEngine:
  - [ ] Identify bottlenecks
  - [ ] Measure cache effectiveness
- [ ] Implement batch embedding generation:
  - [ ] Process multiple terms in one forward pass
  - [ ] Reduce model loading overhead
- [ ] Optimize cache management:
  - [ ] LRU cache with size limit
  - [ ] Cache persistence (save/load)
- [ ] Add performance monitoring:
  - [ ] Cache hit rate
  - [ ] Average query time
  - [ ] Memory usage tracking

**Acceptance Criteria**:
- Cache hit rate >70% for typical workloads
- Cached queries <5ms
- Batch processing 3-5x faster than individual
- Memory usage <500MB with caching

---

### T308: Documentation Updates
- [ ] Update `README.md`:
  - [ ] Add SentenceTransformerEngine to features
  - [ ] Add installation instructions
  - [ ] Add usage examples
  - [ ] Document performance characteristics
- [ ] Update `ARCHITECTURE_EXPLAINED.md`:
  - [ ] Add Phase 2.2 section
  - [ ] Explain neural engines
  - [ ] Architecture diagrams
  - [ ] Comparison tables
- [ ] Create migration guide:
  - [ ] How to switch from EditDistance to SentenceTransformer
  - [ ] Performance expectations
  - [ ] Troubleshooting common issues
- [ ] Update CLI help text:
  - [ ] Document new engine option
  - [ ] Explain tradeoffs

**Acceptance Criteria**:
- All documentation updated
- Installation guide tested on clean environment
- Examples work as documented
- Troubleshooting section covers common issues

---

### T309: Optional - ChineseBertEngine
*Only if time permits and SentenceTransformer shows promise*

- [ ] Create `src/core/engines/chinese_bert_engine.py`
- [ ] Use model: `hfl/chinese-bert-wwm-ext`
- [ ] Implement same interface as SentenceTransformer
- [ ] Compare against SentenceTransformer:
  - [ ] Accuracy comparison
  - [ ] Performance comparison
  - [ ] Memory usage comparison
- [ ] Document tradeoffs

**Acceptance Criteria**:
- ChineseBertEngine implements SemanticEngine
- Benchmark comparison shows meaningful difference
- Documented recommendation on when to use

---

### T310: Final Validation
- [ ] Run full test suite:
  - [ ] All 68+ Phase 2.1 tests pass
  - [ ] All 4+ Phase 2.2 tests pass (T042-T048)
  - [ ] Benchmark suite executes successfully
- [ ] Validate OpenSpec compliance:
  - [ ] `openspec validate add-neural-semantic-engines --strict`
- [ ] Performance validation:
  - [ ] Genesis 3:3: ≥75% match rate
  - [ ] Pipeline degradation <20%
  - [ ] Memory usage acceptable
- [ ] Create Phase 2.2 completion report:
  - [ ] Achievements summary
  - [ ] Benchmark results
  - [ ] Performance metrics
  - [ ] Lessons learned

**Acceptance Criteria**:
- OpenSpec validation passes
- All success metrics met
- Completion report comprehensive
- Ready for archiving

---

## Deliverables Checklist

### Code Files ✅
- [ ] `src/core/engines/sentence_transformer_engine.py`
- [ ] `src/core/engines/chinese_bert_engine.py` (optional)
- [ ] `tests/benchmark_engines.py`
- [ ] Updated `segment.py`
- [ ] Updated `requirements.txt`

### Test Files ✅
- [ ] `tests/test_sentence_transformer_engine.py` (T042-T045)
- [ ] `tests/test_integration_phase22.py` (T046-T048)
- [ ] Benchmark results (CSV/JSON)

### Documentation ✅
- [ ] Updated `README.md`
- [ ] Updated `ARCHITECTURE_EXPLAINED.md`
- [ ] Migration guide
- [ ] Phase 2.2 completion report

### OpenSpec ✅
- [ ] `proposal.md` complete
- [ ] `tasks.md` complete (this file)
- [ ] `design.md` complete
- [ ] `specs/chinese-term-segmentation/spec.md` (delta)
- [ ] Validation passing

---

## Success Criteria

### Must Have (Blocking Merge)
- ✅ SentenceTransformerEngine implemented and tested
- ✅ Match rate ≥75% on Genesis 3:3 (vs 61.5% baseline)
- ✅ All 68+ existing tests pass
- ✅ CLI integration works
- ✅ Documentation updated
- ✅ OpenSpec validation passes

### Should Have (Nice to Have)
- ✅ Benchmarking framework operational
- ✅ Performance optimizations implemented
- ✅ Comparative analysis documented

### Won't Have (Phase 2.3+)
- ❌ HybridEngine (weighted combination)
- ❌ Fine-tuning on biblical corpus
- ❌ Real-time performance (<10ms)

---

## Risk Management

| Risk | Mitigation |
|------|------------|
| Accuracy doesn't improve | Thorough benchmarking before committing; fallback to EditDistance |
| Performance too slow | Aggressive caching, batch processing, user can choose engine |
| Model download fails | Graceful error handling, manual download instructions |
| Dependencies conflict | Pin exact versions, test installation thoroughly |
| Memory usage excessive | Lazy loading, cache limits, documentation on requirements |

---

## Timeline Estimate

**Total**: 1-2 weeks (40-80 hours)

- T301: 4-6 hours (SentenceTransformer implementation)
- T302: 2-3 hours (CLI integration)
- T303: 3-4 hours (Unit testing)
- T304: 4-6 hours (Integration testing)
- T305: 6-8 hours (Benchmark suite)
- T306: 4-6 hours (Comparative analysis)
- T307: 4-6 hours (Optimization)
- T308: 4-6 hours (Documentation)
- T309: 6-8 hours (Optional: ChineseBert)
- T310: 2-3 hours (Final validation)

---

**Status**: Not Started
**Last Updated**: 2025-11-01
**Dependencies**: Phase 2.1 complete ✅
