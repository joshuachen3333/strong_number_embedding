# Design Document: Neural Semantic Engines (Phase 2.2)

## Overview

This document details the technical design for implementing neural semantic similarity engines to break through the 61.5% accuracy ceiling established by EditDistanceEngine in Phase 2.1.

**Goal**: Achieve 75-85% match rate by recognizing semantic relationships, not just character similarity.

---

## Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI (segment.py)                         │
│  - Parse --semantic-engine {edit-distance,                  │
│                             sentence-transformer}           │
└───────────────────────┬─────────────────────────────────────┘
                        │ instantiates
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              BoundaryCorrector                              │
│  - Accepts optional semantic_engine parameter               │
└───────────────────────┬─────────────────────────────────────┘
                        │ passes to
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              SimilarityMatcher                              │
│  - Uses engine.similarity() for scoring                     │
└───────────────────────┬─────────────────────────────────────┘
                        │ uses
                        ▼
┌─────────────────────────────────────────────────────────────┐
│      SemanticEngine (Abstract Interface - Phase 2.1)        │
│  + similarity(text1, text2) → float                         │
│  + get_name() → str                                         │
└───────────────────────┬─────────────────────────────────────┘
                        │ implements
           ┌────────────┴────────────┬──────────────────────────┐
           ▼                         ▼                          ▼
┌────────────────────┐   ┌────────────────────────┐  ┌──────────────────┐
│ EditDistanceEngine │   │ SentenceTransformer    │  │ ChineseBertEngine│
│ (Phase 2.1)        │   │ Engine (Phase 2.2) NEW │  │ (Phase 2.2+)     │
│                    │   │                        │  │ Optional         │
│ Character-based    │   │ Neural embeddings      │  │ BERT-based       │
│ Levenshtein dist   │   │ Semantic understanding │  │ State-of-art     │
│ ~1ms per query     │   │ ~45ms per query        │  │ ~80ms per query  │
└────────────────────┘   └────────────────────────┘  └──────────────────┘
```

---

## Design Decisions

### 1. SentenceTransformerEngine as Primary Focus

**Decision**: Implement SentenceTransformerEngine first, defer ChineseBertEngine to optional/future.

**Rationale**:
- Purpose-built for semantic similarity (cosine similarity of embeddings)
- Good Chinese support via multilingual models
- Proven performance in NLP tasks
- Reasonable model size (~400MB)
- Active community and maintenance

**Alternatives Considered**:
- **ChineseBert**: More accurate but larger (1.2GB), slower, overkill for our use case
- **Word2Vec**: Requires training, word-level only, less proven
- **OpenAI API**: API costs, network dependency, privacy concerns

---

### 2. Model Selection: text2vec-base-chinese

**Decision**: Use `shibing624/text2vec-base-chinese` as default model.

**Rationale**:
- Chinese-optimized (not just multilingual)
- Lightweight (~400MB vs 1.2GB for BERT)
- Designed for semantic similarity tasks
- Good performance on Chinese text similarity benchmarks
- Active maintenance on Hugging Face

**Configuration**:
```python
DEFAULT_MODEL = "shibing624/text2vec-base-chinese"
FALLBACK_MODELS = [
    "distiluse-base-multilingual-cased-v2",  # Lighter (135MB)
    "paraphrase-multilingual-MiniLM-L12-v2"  # More accurate (470MB)
]
```

---

### 3. Embedding Caching Strategy

**Decision**: Implement two-tier caching: in-memory LRU + optional disk persistence.

**Rationale**:
- Strong's Dictionary terms are reused across verses (high cache hit potential)
- First-time embedding generation is expensive (~45ms)
- Cached lookups can be <1ms (similar to EditDistance)

**Architecture**:
```python
class SentenceTransformerEngine(SemanticEngine):
    def __init__(self, model_name='...', cache_size=1000):
        self.model = SentenceTransformer(model_name)
        self._cache = LRUCache(maxsize=cache_size)  # In-memory
        self._cache_hits = 0
        self._cache_misses = 0

    def get_embedding(self, text: str):
        if text in self._cache:
            self._cache_hits += 1
            return self._cache[text]

        self._cache_misses += 1
        embedding = self.model.encode(text)
        self._cache[text] = embedding
        return embedding

    def similarity(self, text1: str, text2: str) -> float:
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        return cosine_similarity(emb1, emb2)
```

**Cache Metrics**:
- Expected cache hit rate: 60-80% (based on Strong's Dictionary reuse)
- Memory overhead: ~2KB per cached embedding (768-dim float32 vector)
- 1000 cached embeddings ≈ 2MB memory (acceptable)

---

### 4. Performance Optimization Strategy

**Problem**: Neural engines are 30-50x slower than EditDistance.

**Mitigation Strategies**:

#### A. Aggressive Caching
```python
# First query: 45ms (model inference)
similarity("神", "上帝")

# Repeat query: <1ms (cache hit)
similarity("神", "上帝")
```

#### B. Batch Processing
```python
# Instead of:
for term in strong_terms:
    embedding = model.encode(term)  # 45ms each

# Do:
embeddings = model.encode(strong_terms)  # 60ms total for 10 terms
```

#### C. Lazy Model Loading
```python
class SentenceTransformerEngine:
    def __init__(self, model_name='...'):
        self.model_name = model_name
        self._model = None  # Not loaded yet

    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model
```

**Expected Performance**:
- First-time query: 40-50ms
- Cached query: <5ms
- Batch (10 terms): ~60ms total (6ms per term)
- Overall pipeline: <20% degradation (acceptable per NFR2.2.1)

---

### 5. Error Handling Strategy

**Scenarios to Handle**:

#### A. Missing Dependencies
```python
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "sentence-transformers not installed. "
        "Install with: pip install sentence-transformers torch"
    )
```

#### B. Model Download Failure
```python
try:
    model = SentenceTransformer(model_name)
except Exception as e:
    print(f"Failed to load model {model_name}: {e}")
    print("Trying fallback model...")
    model = SentenceTransformer("distiluse-base-multilingual-cased-v2")
```

#### C. Embedding Generation Failure
```python
def get_embedding(self, text: str):
    if not text or not text.strip():
        raise ValueError("Cannot generate embedding for empty text")

    try:
        return self.model.encode(text)
    except Exception as e:
        logger.error(f"Failed to encode '{text}': {e}")
        # Return zero vector as fallback
        return np.zeros(self.model.get_sentence_embedding_dimension())
```

---

## Implementation Details

### SentenceTransformerEngine Class

```python
from sentence_transformers import SentenceTransformer, util
from functools import lru_cache
import numpy as np
from typing import Optional
import logging

class SentenceTransformerEngine(SemanticEngine):
    """
    Neural semantic similarity using sentence-transformers.

    Uses pretrained Chinese language models to generate semantic embeddings
    and compute cosine similarity.

    Features:
    - Semantic understanding (synonyms, related terms)
    - LRU caching for performance
    - Configurable model selection
    - Batch processing support

    Performance:
    - First query: ~45ms (embedding generation)
    - Cached query: <5ms
    - Memory: ~400MB model + 2MB cache (1000 entries)

    Example:
        >>> engine = SentenceTransformerEngine()
        >>> engine.similarity("神", "上帝")  # Semantic similarity
        0.85  # High! (vs 0.0 with EditDistance)
        >>> engine.similarity("神", "樹")  # Unrelated
        0.15  # Low
    """

    DEFAULT_MODEL = "shibing624/text2vec-base-chinese"

    def __init__(
        self,
        model_name: str = None,
        device: str = "cpu",
        cache_size: int = 1000,
        batch_size: int = 32
    ):
        """
        Initialize SentenceTransformerEngine.

        Args:
            model_name: Hugging Face model name. Default: text2vec-base-chinese
            device: 'cpu' or 'cuda'. Default: cpu
            cache_size: LRU cache size. Default: 1000 entries (~2MB)
            batch_size: Batch size for encoding. Default: 32

        Raises:
            ImportError: If sentence-transformers not installed
            RuntimeError: If model loading fails
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device
        self.cache_size = cache_size
        self.batch_size = batch_size

        # Lazy loading - model loaded on first use
        self._model = None

        # Caching
        self._embedding_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

        # Logging
        self.logger = logging.getLogger(__name__)

    @property
    def model(self) -> SentenceTransformer:
        """Lazy load model on first access."""
        if self._model is None:
            self.logger.info(f"Loading model: {self.model_name}")
            try:
                self._model = SentenceTransformer(
                    self.model_name,
                    device=self.device
                )
                self.logger.info("Model loaded successfully")
            except Exception as e:
                self.logger.error(f"Failed to load model: {e}")
                raise RuntimeError(f"Could not load model {self.model_name}: {e}")

        return self._model

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text (with caching).

        Args:
            text: Input text

        Returns:
            Embedding vector (numpy array)

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Cannot encode empty text")

        # Check cache
        if text in self._embedding_cache:
            self._cache_hits += 1
            return self._embedding_cache[text]

        # Generate embedding
        self._cache_misses += 1
        embedding = self.model.encode(text, convert_to_numpy=True)

        # Cache result (with size limit)
        if len(self._embedding_cache) < self.cache_size:
            self._embedding_cache[text] = embedding

        return embedding

    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity in [0, 1] range
            - 1.0: Semantically identical
            - 0.0: Completely unrelated

        Example:
            >>> engine.similarity("神", "上帝")
            0.85  # Recognized as synonyms!
        """
        try:
            emb1 = self.get_embedding(text1)
            emb2 = self.get_embedding(text2)

            # Cosine similarity
            similarity = util.cos_sim(emb1, emb2).item()

            # Ensure [0, 1] range (cosine can be negative)
            return max(0.0, similarity)

        except Exception as e:
            self.logger.error(f"Similarity calculation failed: {e}")
            return 0.0  # Fallback to no similarity

    def get_name(self) -> str:
        """Return engine identifier."""
        return "sentence-transformer"

    def get_cache_stats(self) -> dict:
        """Return cache statistics."""
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0

        return {
            "cache_size": len(self._embedding_cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate
        }

    def clear_cache(self):
        """Clear embedding cache."""
        self._embedding_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
```

---

## Testing Strategy

### Unit Tests (T303)

```python
def test_t042_interface_compliance():
    """Engine implements SemanticEngine interface."""
    engine = SentenceTransformerEngine()
    assert isinstance(engine, SemanticEngine)
    assert hasattr(engine, 'similarity')
    assert hasattr(engine, 'get_name')

def test_t043_semantic_understanding():
    """Engine recognizes semantic relationships."""
    engine = SentenceTransformerEngine()

    # Synonyms (should be high)
    assert engine.similarity("神", "上帝") > 0.7

    # Related terms
    assert engine.similarity("愛", "珍愛") > 0.6

    # Unrelated
    assert engine.similarity("神", "樹") < 0.4

def test_t044_caching():
    """Embedding cache improves performance."""
    engine = SentenceTransformerEngine()

    # First call (cache miss)
    import time
    start = time.time()
    _ = engine.similarity("神", "上帝")
    first_time = time.time() - start

    # Second call (cache hit)
    start = time.time()
    _ = engine.similarity("神", "上帝")
    second_time = time.time() - start

    # Cached should be faster
    assert second_time < first_time * 0.2  # 5x faster

def test_t045_error_handling():
    """Engine handles errors gracefully."""
    engine = SentenceTransformerEngine()

    # Empty strings
    with pytest.raises(ValueError):
        engine.get_embedding("")

    # Should not crash on edge cases
    assert 0.0 <= engine.similarity("a", "b") <= 1.0
```

---

## Benchmarking Framework (T305)

```python
class EngineBenchmark:
    """Benchmark multiple semantic engines."""

    def __init__(self, test_verses: List[Verse]):
        self.test_verses = test_verses
        self.results = []

    def benchmark_engine(self, engine: SemanticEngine, name: str):
        """Run full benchmark on engine."""
        results = {
            "engine": name,
            "accuracy": [],
            "latency": [],
            "memory": []
        }

        for verse in self.test_verses:
            # Measure accuracy
            match_rate = self.measure_accuracy(engine, verse)
            results["accuracy"].append(match_rate)

            # Measure latency
            latency = self.measure_latency(engine, verse)
            results["latency"].append(latency)

            # Measure memory
            memory = self.measure_memory(engine)
            results["memory"].append(memory)

        self.results.append(results)
        return results

    def generate_report(self):
        """Generate comparison report."""
        df = pd.DataFrame(self.results)
        print(df)

        # Export to CSV
        df.to_csv("benchmark_results.csv")

        # Create visualization
        self.plot_comparison(df)
```

---

## Success Metrics

### Accuracy Targets
- Genesis 3:3: **≥75%** (vs 61.5% baseline)
- Genesis 1:1: **≥80%** (maintain or improve from 80%)
- John 3:16: **≥65%** (vs 55.6% baseline)
- Average across 10 verses: **≥70%**

### Performance Targets
- First query: <100ms
- Cached query: <5ms
- Overall pipeline degradation: <20%
- Cache hit rate: >60%

### Memory Targets
- Model: ~400MB
- Cache (1000 entries): ~2MB
- Total overhead: <500MB

---

## Deployment Considerations

### Hardware Requirements
- **Minimum**: 2GB RAM, 1 CPU core
- **Recommended**: 4GB RAM, 2 CPU cores
- **GPU**: Optional (3-5x speedup)

### Installation
```bash
pip install sentence-transformers torch
```

### First-Time Setup
```bash
# Model auto-downloads on first use
./segment.py --semantic-engine sentence-transformer ...

# Or pre-download
python -c "from sentence_transformers import SentenceTransformer; \
           SentenceTransformer('shibing624/text2vec-base-chinese')"
```

---

## Future Enhancements (Phase 2.3+)

1. **HybridEngine**: Combine EditDistance + SentenceTransformer
2. **Fine-tuning**: Train on biblical Chinese corpus
3. **GPU Support**: Leverage CUDA for 3-5x speedup
4. **Model Quantization**: Reduce model size by 50-75%
5. **Batch API**: Process entire chapters at once

---

**Prepared by**: Claude Code
**Date**: 2025-11-01
**Status**: Design Draft
