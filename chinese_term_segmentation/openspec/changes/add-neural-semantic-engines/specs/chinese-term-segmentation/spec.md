# Chinese Term Segmentation - Spec Delta (Phase 2.2)

## ADDED Requirements

### Requirement: SentenceTransformerEngine Implementation

The system SHALL provide a neural semantic similarity engine using sentence transformers for semantic understanding beyond character-level matching.

**Purpose**: Recognize semantic relationships (synonyms, related terms) to break through the 61.5% accuracy ceiling of character-based EditDistanceEngine.

**Implementation**:
```python
class SentenceTransformerEngine(SemanticEngine):
    """Neural semantic similarity using pretrained Chinese language models."""

    def __init__(self, model_name='shibing624/text2vec-base-chinese'):
        self.model = SentenceTransformer(model_name)
        self._cache = {}

    def similarity(self, text1: str, text2: str) -> float:
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        return cosine_similarity(emb1, emb2)
```

#### Scenario: Recognize Synonyms

**Given**: SentenceTransformerEngine instance
**When**: Computing similarity("神", "上帝")
**Then**: Returns score > 0.7 (vs 0.0 with EditDistance)
**And**: Recognizes both mean "God" semantically

#### Scenario: Distinguish Related vs Unrelated Terms

**Given**: SentenceTransformerEngine instance
**When**: Computing similarity("愛", "珍愛") and similarity("神", "樹")
**Then**: Related terms ("愛", "珍愛") score > 0.6
**And**: Unrelated terms ("神", "樹") score < 0.4

#### Scenario: Embedding Caching for Performance

**Given**: SentenceTransformerEngine with LRU cache
**When**: Computing similarity("神", "上帝") twice
**Then**: First call takes ~45ms (embedding generation)
**And**: Second call takes <5ms (cache hit)
**And**: Cache hit rate > 60% for typical workloads

---

### Requirement: CLI Integration for Neural Engines

The system SHALL extend the --semantic-engine CLI flag to support neural engines.

**Enhanced CLI**:
```bash
--semantic-engine {edit-distance,sentence-transformer}
```

#### Scenario: Use Sentence Transformer via CLI

**Given**: User runs segmentation with sentence-transformer engine
```bash
./segment.py --engs gen --chap 3 --sec 3 --version lcc \
  --seg pkuseg --correct-with-sn --use-refinement \
  --semantic-engine sentence-transformer
```
**When**: CLI processes the command
**Then**: Instantiates SentenceTransformerEngine
**And**: Uses neural semantic similarity for term matching
**And**: Achieves ≥75% match rate (vs 61.5% with edit-distance)

#### Scenario: Automatic Model Download on First Use

**Given**: User runs with sentence-transformer for first time
**And**: Model not yet downloaded locally
**When**: CLI instantiates SentenceTransformerEngine
**Then**: Automatically downloads model (~400MB)
**And**: Shows progress/status messages
**And**: Caches model for future use

#### Scenario: Graceful Handling of Missing Dependencies

**Given**: User tries sentence-transformer without installing dependencies
**When**: CLI attempts to instantiate engine
**Then**: Shows clear error message
**And**: Provides installation instructions
**And**: Suggests: "pip install sentence-transformers torch"

---

### Requirement: Benchmarking Framework

The system SHALL provide a benchmarking framework to compare semantic engines on standard test sets.

**Purpose**: Measure and compare accuracy, performance, and resource usage across engines.

**Framework Components**:
- Test dataset (20-50 verses with known Strong's mappings)
- Metrics calculation (accuracy, precision, recall, F1, latency)
- Comparison reports (tables, charts, CSV/JSON export)

#### Scenario: Compare EditDistance vs SentenceTransformer

**Given**: Benchmark framework with 20-verse test set
**And**: Both EditDistanceEngine and SentenceTransformerEngine registered
**When**: Running benchmark comparison
**Then**: Generates accuracy comparison table
**And**: Shows SentenceTransformer ≥10 percentage points higher
**And**: Shows latency comparison (EditDistance ~1ms, SentenceTransformer ~45ms)
**And**: Exports results to CSV for further analysis

#### Scenario: Performance Metrics Collection

**Given**: Benchmark framework running on full test set
**When**: Measuring engine performance
**Then**: Collects average latency (mean, p50, p95, p99)
**And**: Measures memory usage
**And**: Tracks cache hit rate (for cached engines)
**And**: Generates visualization charts

**Example Output**:
```
Engine Comparison Results:
┌──────────────────────┬──────────┬──────────┬────────────┐
│ Engine               │ Accuracy │ Avg Time │ Memory     │
├──────────────────────┼──────────┼──────────┼────────────┤
│ edit-distance        │ 62.3%    │ 1.2ms    │ 10MB       │
│ sentence-transformer │ 78.5%    │ 45ms     │ 450MB      │
└──────────────────────┴──────────┴──────────┴────────────┘

Improvement: +16.2 percentage points ✨
```

---

### Requirement: Accuracy Improvement Target

The system SHALL achieve ≥75% match rate on Genesis 3:3 using neural semantic engines, representing a minimum 10 percentage point improvement over the EditDistance baseline.

**Baseline** (Phase 2.1): 61.5% with EditDistanceEngine
**Target** (Phase 2.2): ≥75% with SentenceTransformerEngine

#### Scenario: Genesis 3:3 Accuracy with SentenceTransformer

**Given**: Genesis 3:3 LCC segmentation with SentenceTransformerEngine
**When**: Running with `--semantic-engine sentence-transformer`
**Then**: Achieves ≥75% match rate
**And**: Improves by ≥10 percentage points over EditDistance baseline (61.5%)
**And**: Text preservation remains 100%

#### Scenario: Multi-Verse Accuracy Improvement

**Given**: Test set of 10 verses (Genesis 1:1, 3:3, John 3:16, etc.)
**When**: Running with SentenceTransformerEngine
**Then**: Average match rate ≥70% across all verses
**And**: No verse shows degradation vs EditDistance
**And**: At least 7/10 verses show improvement

---

### Requirement: Performance Degradation Limit

The system SHALL ensure that neural engines do not degrade overall pipeline performance by more than 20%, with caching providing acceptable performance for production use.

**Target**: Overall pipeline time increase <20% (vs EditDistance baseline)

#### Scenario: First-Time Query Performance

**Given**: SentenceTransformerEngine without cache
**When**: Processing first query
**Then**: Embedding generation completes in <100ms
**And**: Overall query time acceptable for interactive use

#### Scenario: Cached Query Performance

**Given**: SentenceTransformerEngine with populated cache
**When**: Processing repeated query
**Then**: Cache hit detected
**And**: Query completes in <5ms
**And**: Performance comparable to EditDistance

#### Scenario: Overall Pipeline Performance

**Given**: Full segmentation pipeline with SentenceTransformerEngine
**When**: Processing Genesis 3:3 with refinement
**Then**: Total time increases by <20% vs EditDistance baseline
**And**: Cache hit rate >60% for typical workloads
**And**: Performance acceptable for production use

---

### Requirement: Dependency Management

The system SHALL handle neural engine dependencies gracefully with clear installation instructions and optional dependency support.

**Dependencies**:
- `sentence-transformers>=2.2.0`
- `torch>=2.0.0`
- `transformers>=4.30.0`

#### Scenario: Install Dependencies

**Given**: User wants to use sentence-transformer engine
**When**: Running pip install
```bash
pip install sentence-transformers torch
```
**Then**: All required dependencies installed
**And**: Model auto-downloaded on first use
**And**: Engine ready for use

#### Scenario: Missing Dependencies Handled Gracefully

**Given**: Dependencies not installed
**When**: User tries `--semantic-engine sentence-transformer`
**Then**: System shows clear error message
**And**: Provides exact installation command
**And**: Suggests falling back to edit-distance

---

## MODIFIED Requirements

### Requirement: CLI Engine Selection (Enhanced)

The system SHALL extend the --semantic-engine CLI flag to support both 'edit-distance' and 'sentence-transformer' options.

**Enhancement**: Extend choices from `['edit-distance']` to `['edit-distance', 'sentence-transformer']`.

**Before** (Phase 2.1):
```bash
--semantic-engine {edit-distance}
```

**After** (Phase 2.2):
```bash
--semantic-engine {edit-distance,sentence-transformer}
```

#### Scenario: New Engine Option Available

**Given**: User runs `./segment.py --help`
**When**: Viewing --semantic-engine options
**Then**: Shows both 'edit-distance' and 'sentence-transformer'
**And**: Describes each engine's characteristics
**And**: Notes performance/accuracy tradeoffs

---

## Testing Requirements

### T042-T045: SentenceTransformerEngine Unit Tests
- T042: Interface compliance
- T043: Semantic understanding (synonyms, related terms)
- T044: Caching mechanism
- T045: Error handling

### T046-T048: Integration Tests
- T046: Genesis 3:3 with SentenceTransformer (≥75% target)
- T047: Comparative test (EditDistance vs SentenceTransformer)
- T048: Performance regression test

### Benchmark Suite
- 20-50 verse test dataset
- Accuracy metrics (match rate, precision, recall, F1)
- Performance metrics (latency, memory)
- Comparison reports and visualizations

---

## Non-Functional Enhancements

### Performance
- First-time query: <100ms
- Cached query: <5ms
- Pipeline degradation: <20%
- Cache hit rate: >60%

### Resource Usage
- Model size: ~400MB
- Memory overhead: <500MB
- Cache size: ~2MB (1000 entries)

### Usability
- Automatic model download
- Clear error messages
- Installation documentation
- Migration guide from EditDistance

---

## Future Considerations (Phase 2.3+)

**Not in Phase 2.2 scope**:
- HybridEngine (weighted combination of multiple engines)
- Fine-tuning on biblical Chinese corpus
- GPU acceleration
- Model quantization
- Real-time performance optimization (<10ms)

---

**Change ID**: add-neural-semantic-engines
**Phase**: 2.2
**Status**: Proposed
**Depends On**: Phase 2.1 (add-semantic-similarity-engines) ✅
**Target**: 75-85% match rate (vs 61.5% baseline)
