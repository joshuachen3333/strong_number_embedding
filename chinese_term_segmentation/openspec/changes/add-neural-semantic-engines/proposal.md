# Proposal: Add Neural Semantic Engines

## Metadata
- **Change ID**: `add-neural-semantic-engines`
- **Type**: Enhancement
- **Status**: Proposed
- **Created**: 2025-11-01
- **Depends On**: `add-semantic-similarity-engines` (Phase 2.1)
- **Phase**: 2.2

---

## Why

### Problem Statement

**Current Limitation**: EditDistanceEngine (Phase 2.1 baseline) is limited to character-level similarity and cannot recognize semantic relationships:

- "神" vs "上帝" → **0.0 similarity** (but both mean "God"!)
- "愛" vs "珍愛" → **0.5 similarity** (semantically very related, should be higher)
- "獨一無二的" vs "獨生" → Low similarity (semantically related via "unique")

**Performance Ceiling**: 61.5% match rate on Genesis 3:3 - cannot improve without semantic understanding.

### Business Value

**Target**: Increase match rate from 61.5% to **75-85%** by recognizing semantic relationships.

**Impact**:
- Better Strong's Number alignment accuracy
- Reduced manual correction effort
- More reliable biblical term mapping
- Foundation for AI-assisted translation tools

---

## What Changes

### High-Level Architecture

```
┌─────────────────────────────────────────────┐
│         SimilarityMatcher (existing)        │
│  - find_best_substring(refTerm, origText) │
└───────────────────┬─────────────────────────┘
                    │ uses
                    ▼
┌─────────────────────────────────────────────┐
│      SemanticEngine (Phase 2.1 interface)   │
└───────────────────┬─────────────────────────┘
                    │ implements
      ┌─────────────┴──────────────┬──────────────────┐
      ▼                            ▼                  ▼
┌──────────────┐        ┌────────────────────┐  ┌──────────────┐
│ EditDistance │        │ SentenceTransformer│  │ ChineseBert  │
│ (Phase 2.1)  │        │ (Phase 2.2) NEW ✨ │  │ (Phase 2.2+) │
└──────────────┘        └────────────────────┘  └──────────────┘
```

### New Components

#### 1. SentenceTransformerEngine ⭐ (Priority 1)
- **File**: `src/core/engines/sentence_transformer_engine.py`
- **Model**: `shibing624/text2vec-base-chinese` (lightweight, Chinese-optimized)
- **Features**:
  - Semantic similarity using neural embeddings
  - Handles synonyms (神 vs 上帝)
  - Multilingual support
  - Embedding caching for performance

#### 2. Benchmarking Framework 📊 (Priority 1)
- **File**: `tests/benchmark_engines.py`
- **Features**:
  - Compare multiple engines on same dataset
  - Measure accuracy, precision, recall
  - Performance metrics (speed, memory)
  - Export results to CSV/JSON

#### 3. ChineseBertEngine 🧠 (Priority 2 - Optional)
- **File**: `src/core/engines/chinese_bert_engine.py`
- **Model**: `hfl/chinese-bert-wwm-ext`
- **Features**:
  - State-of-the-art Chinese BERT
  - Higher accuracy than SentenceTransformer
  - Larger model (slower, more memory)

---

## Requirements

### Functional Requirements

**FR2.2.1**: SentenceTransformerEngine Implementation
- SHALL implement SemanticEngine interface
- SHALL use `sentence-transformers` library
- SHALL support Chinese text embeddings
- SHALL cache embeddings for repeated terms
- SHALL return similarity scores in [0, 1] range

**FR2.2.2**: CLI Integration
- SHALL add `sentence-transformer` to `--semantic-engine` choices
- SHALL handle model download on first use
- SHALL provide clear error messages if dependencies missing
- SHALL work with existing `--correct-with-sn` and `--use-refinement` flags

**FR2.2.3**: Benchmarking Framework
- SHALL compare multiple engines on same test set
- SHALL measure: accuracy, precision, recall, F1 score
- SHALL measure: latency (avg, p50, p95, p99)
- SHALL measure: memory usage
- SHALL export results in machine-readable format

### Non-Functional Requirements

**NFR2.2.1**: Performance
- SentenceTransformerEngine SHALL process queries in <100ms (before caching)
- With caching, SHALL process repeated terms in <5ms
- SHALL not degrade overall pipeline performance by >20%

**NFR2.2.2**: Accuracy
- Target match rate: 75-85% on Genesis 3:3 (vs 61.5% baseline)
- Minimum improvement: +10 percentage points over EditDistance
- SHALL NOT decrease accuracy on any test verse

**NFR2.2.3**: Dependencies
- SHALL use well-maintained, open-source libraries
- SHALL specify exact version requirements
- SHALL provide clear installation instructions
- SHALL handle missing dependencies gracefully

**NFR2.2.4**: Backward Compatibility
- SHALL maintain 100% backward compatibility with Phase 2.1
- EditDistanceEngine SHALL remain the default
- All existing tests SHALL continue to pass

---

## Proposed Solution

### Implementation Phases

#### Phase 2.2.1: SentenceTransformerEngine (Week 1)
1. **T301**: Implement SentenceTransformerEngine
   - Install `sentence-transformers` library
   - Create engine class with caching
   - Test with Chinese text pairs

2. **T302**: CLI Integration
   - Add `sentence-transformer` to CLI choices
   - Update BoundaryCorrector to support new engine
   - Add model download handling

3. **T303**: Unit Testing
   - Test engine interface compliance
   - Test embedding generation
   - Test caching mechanism
   - Test error handling

4. **T304**: Integration Testing
   - Test Genesis 3:3 with new engine
   - Test multiple verses
   - Compare against EditDistance baseline

#### Phase 2.2.2: Benchmarking Framework (Week 1)
5. **T305**: Create Benchmark Suite
   - Define test dataset (20-50 verses)
   - Implement metrics calculation
   - Create comparison reports

6. **T306**: Run Comparative Analysis
   - Benchmark EditDistance vs SentenceTransformer
   - Generate performance reports
   - Document findings

#### Phase 2.2.3: Optimization & Documentation (Week 2)
7. **T307**: Performance Optimization
   - Implement batch embedding generation
   - Optimize cache management
   - Profile and tune performance

8. **T308**: Documentation
   - Update README with new engines
   - Update ARCHITECTURE_EXPLAINED
   - Add benchmark results
   - Create migration guide

9. **T309**: Optional: ChineseBertEngine
   - Implement if time permits
   - Compare against SentenceTransformer
   - Document tradeoffs

10. **T310**: Final Validation
    - Run full test suite
    - Validate OpenSpec compliance
    - Prepare for archiving

---

## Success Metrics

### Must Have ✅
- SentenceTransformerEngine implemented and tested
- CLI flag `--semantic-engine sentence-transformer` works
- Match rate improves by ≥10 percentage points
- All 68+ existing tests pass
- Performance degradation <20%
- Documentation updated

### Should Have 📊
- Benchmarking framework operational
- Comparative analysis completed
- Performance optimizations implemented
- ChineseBertEngine prototyped

### Nice to Have 🎁
- Hybrid engine (EditDistance + SentenceTransformer)
- Configuration file support for engine settings
- Automated model download with progress bar

---

## Testing Strategy

### Unit Tests (T303)
- Test engine interface compliance
- Test embedding generation for various inputs
- Test caching mechanism
- Test error handling (missing models, network issues)

### Integration Tests (T304)
- Genesis 3:3: Target ≥75% match rate
- Genesis 1:1: Maintain or improve 80% rate
- John 3:16: Target ≥65% match rate (vs 55.6% baseline)
- Multiple verses: Average ≥70% across 10 test verses

### Benchmark Tests (T305-T306)
- Accuracy metrics on 20+ verse test set
- Performance metrics (latency, memory)
- Comparison tables and visualizations

### Regression Tests
- All 68+ Phase 2.1 tests must pass
- No degradation with EditDistanceEngine (default)

---

## Dependencies

### External Libraries
- `sentence-transformers>=2.2.0` - For neural semantic similarity
- `torch>=2.0.0` - PyTorch backend
- `transformers>=4.30.0` - Hugging Face transformers

### Models
- `shibing624/text2vec-base-chinese` (~400MB) - Primary model
- Alternative: `distiluse-base-multilingual-cased-v2` (~135MB) - Lighter option

### Development Dependencies
- `pytest-benchmark` - For performance testing
- `memory_profiler` - For memory usage analysis

---

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Model download fails | Medium | Medium | Handle gracefully, provide manual download instructions |
| Performance too slow | Medium | High | Implement aggressive caching, batch processing |
| Accuracy doesn't improve | Low | High | Thorough benchmarking before commitment, fallback to EditDistance |
| Dependencies conflict | Low | Medium | Pin exact versions, test installation |
| Memory usage too high | Medium | Medium | Lazy loading, model quantization options |

---

## Timeline

**Total Duration**: 1-2 weeks

**Week 1**:
- Days 1-2: T301-T302 (SentenceTransformerEngine + CLI)
- Days 3-4: T303-T304 (Testing)
- Day 5: T305-T306 (Benchmarking)

**Week 2**:
- Days 1-2: T307 (Optimization)
- Day 3: T308 (Documentation)
- Day 4: T309 (Optional: ChineseBert)
- Day 5: T310 (Final validation)

---

## Alternatives Considered

### 1. ❌ OpenAI Embeddings API
- **Pros**: High quality, no local compute
- **Cons**: API costs, network dependency, privacy concerns
- **Decision**: Rejected - prefer self-hosted solution

### 2. ❌ Word2Vec Custom Training
- **Pros**: Biblical domain-specific
- **Cons**: Requires training data, less proven
- **Decision**: Deferred to Phase 3

### 3. ✅ SentenceTransformer (CHOSEN)
- **Pros**: Purpose-built for similarity, good Chinese support, proven
- **Cons**: Larger than edit distance
- **Decision**: Best balance of accuracy and practicality

---

## Future Enhancements (Phase 2.3+)

- **HybridEngine**: Weighted combination of multiple engines
- **CascadingEngine**: Fast path for exact matches, semantic for hard cases
- **BiblicalKnowledgeBase**: Domain-specific term relationships
- **Fine-tuning**: Train on biblical Chinese corpus

---

## Approval Checklist

- [ ] Requirements clearly defined
- [ ] Architecture diagram included
- [ ] Success metrics specified
- [ ] Risks identified and mitigated
- [ ] Timeline realistic
- [ ] Dependencies listed
- [ ] Testing strategy comprehensive
- [ ] Backward compatibility guaranteed

---

## References

- Phase 2.1: `add-semantic-similarity-engines` (baseline)
- SEMANTIC_ENGINE_STRATEGY.md (10 strategic considerations)
- SEMANTIC_ENGINE_TECHNICAL_SPECS.md (implementation details)
- SEMANTIC_SIMILARITY_PLAN.md (testing plan)

---

**Prepared by**: Claude Code
**Date**: 2025-11-01
**Status**: Awaiting Approval
