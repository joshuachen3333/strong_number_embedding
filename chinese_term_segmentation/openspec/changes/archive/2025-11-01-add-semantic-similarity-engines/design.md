# Design Document: Semantic Similarity Engines

## Overview

This document outlines the technical design for implementing a pluggable semantic engine architecture in the Chinese biblical term segmentation project. The goal is to replace hard-coded edit distance logic with an extensible plugin system that supports multiple similarity algorithms.

## Design Principles

### 1. Open/Closed Principle
**Open for extension, closed for modification**

- New engines can be added without modifying existing code
- SimilarityMatcher doesn't need to know about specific engine implementations
- Plugin pattern enables third-party engines

### 2. Single Responsibility Principle
**Each class has one reason to change**

- `SemanticEngine`: Defines the interface contract
- `EditDistanceEngine`: Implements character-based similarity
- `SimilarityMatcher`: Orchestrates matching logic, delegates similarity calculations

### 3. Dependency Inversion Principle
**Depend on abstractions, not concretions**

- SimilarityMatcher depends on `SemanticEngine` interface
- Concrete engines are injected via constructor
- Easy to mock in tests

### 4. Backward Compatibility
**Default behavior unchanged**

- EditDistanceEngine as default
- Existing tests pass without modification
- No breaking changes to public APIs

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────┐
│           CLI (segment.py)                  │
│  - Parse --semantic-engine flag             │
│  - Instantiate correct engine               │
└───────────────────┬─────────────────────────┘
                    │ creates
                    ▼
┌─────────────────────────────────────────────┐
│      SimilarityMatcher                      │
│  - find_best_substring(refTerm, origText)  │
│  - Uses engine.similarity() for scoring     │
└───────────────────┬─────────────────────────┘
                    │ uses
                    ▼
┌─────────────────────────────────────────────┐
│      SemanticEngine (ABC)                   │
│  + similarity(text1, text2) → float         │
│  + get_name() → str                         │
└───────────────────┬─────────────────────────┘
                    │ implements
           ┌────────┴────────┬────────────┐
           ▼                 ▼            ▼
┌──────────────────┐  ┌─────────────┐   ...
│ EditDistance     │  │ Sentence    │   (Phase 2.2)
│ Engine           │  │ Transformer │
│ (Phase 2.1)      │  │ (Phase 2.2) │
└──────────────────┘  └─────────────┘
```

### Class Design

#### SemanticEngine (Abstract Base Class)

```python
from abc import ABC, abstractmethod

class SemanticEngine(ABC):
    """
    Abstract base class for semantic similarity engines.

    All engines must implement this interface to be compatible
    with the SimilarityMatcher system.
    """

    @abstractmethod
    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two text strings.

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Similarity score in range [0.0, 1.0]
            - 0.0: Completely dissimilar
            - 1.0: Identical or perfectly similar

        Raises:
            ValueError: If inputs are invalid (e.g., None, empty)
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the engine identifier for logging and metrics.

        Returns:
            Unique engine name (kebab-case recommended)
            Examples: "edit-distance", "sentence-transformer"
        """
        pass
```

**Design Rationale**:
- Minimal interface: Only 2 methods required
- Clear contracts: Docstrings specify exact behavior
- Type hints: Enable static analysis and IDE support
- Extensibility: Easy to add new methods in future (e.g., `batch_similarity()`)

#### EditDistanceEngine (Concrete Implementation)

```python
from src.core.semantic_engine import SemanticEngine
from src.core.char_variant_normalizer import CharVariantNormalizer

class EditDistanceEngine(SemanticEngine):
    """
    Character-based edit distance similarity engine.

    This is the baseline engine that wraps the existing edit distance
    logic. It measures character-level similarity, not semantic meaning.
    """

    def __init__(self, normalizer: CharVariantNormalizer = None):
        """
        Initialize EditDistanceEngine.

        Args:
            normalizer: Optional character variant normalizer
                       Default: Use default CharVariantNormalizer
        """
        self.normalizer = normalizer or CharVariantNormalizer()

    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute edit distance based similarity.

        Algorithm:
        1. Normalize character variants (爲 → 為)
        2. Compute Levenshtein distance
        3. Normalize to [0, 1] range

        Returns:
            1.0 - (distance / max_length)
        """
        if not text1 or not text2:
            return 0.0

        # Normalize variants
        norm1 = self.normalizer.normalize(text1)
        norm2 = self.normalizer.normalize(text2)

        # Compute edit distance
        distance = self._levenshtein(norm1, norm2)
        max_len = max(len(norm1), len(norm2))

        return 1.0 - (distance / max_len)

    def get_name(self) -> str:
        return "edit-distance"

    def _levenshtein(self, s1: str, s2: str) -> int:
        """Standard Levenshtein distance implementation"""
        # ... existing logic from SimilarityMatcher
```

**Design Rationale**:
- **Wraps existing code**: Minimal changes to proven logic
- **Maintains normalizer**: CharVariantNormalizer still integrated
- **Private methods**: `_levenshtein()` is implementation detail
- **Backward compatible**: Produces identical results to current system

#### SimilarityMatcher (Refactored)

```python
from src.core.semantic_engine import SemanticEngine
from src.core.engines.edit_distance_engine import EditDistanceEngine

class SimilarityMatcher:
    """
    Finds best matching substring using semantic similarity.

    Refactored to use pluggable semantic engines instead of
    hard-coded edit distance logic.
    """

    def __init__(self,
                 engine: SemanticEngine = None,
                 boundary_corrector: BoundaryCorrector = None,
                 threshold: float = 0.5):
        """
        Initialize SimilarityMatcher.

        Args:
            engine: Semantic similarity engine to use
                   Default: EditDistanceEngine()
            boundary_corrector: Optional boundary correction
            threshold: Minimum similarity score to accept match
        """
        # Default to EditDistanceEngine for backward compatibility
        self.engine = engine or EditDistanceEngine()
        self.boundary_corrector = boundary_corrector
        self.threshold = threshold

    def find_best_substring(self, refTerm: str, origText: str) -> Optional[str]:
        """
        Find best matching substring in origText for refTerm.

        Strategy:
        1. Generate all candidate substrings
        2. Score each candidate using self.engine.similarity()
        3. Return candidate with highest score above threshold
        4. Apply boundary correction if enabled
        """
        candidates = self._generate_candidates(origText, len(refTerm))

        best_match = None
        best_score = self.threshold

        for candidate in candidates:
            # Use pluggable engine for scoring
            score = self.engine.similarity(refTerm, candidate)

            if score > best_score:
                best_score = score
                best_match = candidate

        # Apply boundary correction if configured
        if best_match and self.boundary_corrector:
            best_match = self.boundary_corrector.correct(best_match, origText)

        return best_match
```

**Design Rationale**:
- **Dependency injection**: Engine passed in constructor
- **Safe default**: Uses EditDistanceEngine if none provided
- **Delegation**: Delegates similarity calculation to engine
- **Preserves features**: BoundaryCorrector still works

### Data Flow

#### Sequence Diagram: Finding Best Substring

```
CLI                SimilarityMatcher       SemanticEngine       BoundaryCorrector
 │                        │                       │                    │
 ├─(1) Instantiate engine───────────────────────>│                    │
 │                        │                       │                    │
 ├─(2) Create matcher with engine────────────────>│                    │
 │                        │                       │                    │
 ├─(3) find("神", "上帝...")│                       │                    │
 │                        │                       │                    │
 │                        ├─(4) Generate candidates                    │
 │                        │                       │                    │
 │                        ├─(5) similarity("神", "上帝")                │
 │                        │<────────(6) 0.0 ──────┤                    │
 │                        │                       │                    │
 │                        ├─(7) similarity("神", "神")                  │
 │                        │<────────(8) 1.0 ──────┤                    │
 │                        │                       │                    │
 │                        ├─(9) correct("神", "上帝...")───────────────>│
 │                        │<────(10) "神"──────────────────────────────┤
 │<─(11) "神"─────────────┤                       │                    │
```

## Implementation Strategy

### Phase 2.1 Focus: Refactoring Only

**Scope**:
- Extract interface
- Wrap existing logic
- Refactor SimilarityMatcher
- Add CLI flag
- Maintain 100% backward compatibility

**Out of Scope**:
- Neural engines (Phase 2.2)
- Configuration files (Phase 2.2)
- Caching (Phase 2.3)
- Benchmarking framework (Phase 2.2)

### Migration Path

#### Step 1: Extract Interface
```python
# Create src/core/semantic_engine.py
class SemanticEngine(ABC):
    @abstractmethod
    def similarity(self, text1: str, text2: str) -> float:
        pass
```

#### Step 2: Wrap Existing Logic
```python
# Create src/core/engines/edit_distance_engine.py
class EditDistanceEngine(SemanticEngine):
    # Move logic from SimilarityMatcher
```

#### Step 3: Refactor SimilarityMatcher
```python
# In src/core/similarity_matcher.py
class SimilarityMatcher:
    def __init__(self, engine: SemanticEngine = None):
        self.engine = engine or EditDistanceEngine()
```

#### Step 4: Update Tests
```python
# Ensure all tests explicitly use EditDistanceEngine
def test_matching():
    engine = EditDistanceEngine()
    matcher = SimilarityMatcher(engine=engine)
    # ... test logic
```

#### Step 5: Add CLI Support
```python
# In segment.py
parser.add_argument('--semantic-engine',
                   choices=['edit-distance'],
                   default='edit-distance')
```

## Error Handling

### Invalid Engine
```python
# In SimilarityMatcher.__init__()
if not isinstance(engine, SemanticEngine):
    raise TypeError(
        f"engine must be instance of SemanticEngine, "
        f"got {type(engine).__name__}"
    )
```

### Engine Failures
```python
# In SimilarityMatcher.find_best_substring()
try:
    score = self.engine.similarity(refTerm, candidate)
except Exception as e:
    logger.warning(f"Engine {self.engine.get_name()} failed: {e}")
    score = 0.0  # Treat as no match
```

### Invalid Inputs
```python
# In EditDistanceEngine.similarity()
if not text1 or not text2:
    raise ValueError("text1 and text2 must be non-empty strings")
```

## Testing Strategy

### Unit Tests

#### Test EditDistanceEngine
```python
def test_edit_distance_engine_exact_match():
    engine = EditDistanceEngine()
    assert engine.similarity("神", "神") == 1.0

def test_edit_distance_engine_no_match():
    engine = EditDistanceEngine()
    assert engine.similarity("神", "上帝") == 0.0

def test_edit_distance_engine_partial_match():
    engine = EditDistanceEngine()
    score = engine.similarity("神的", "神")
    assert 0.0 < score < 1.0
```

#### Test SimilarityMatcher with Engines
```python
def test_matcher_uses_provided_engine():
    mock_engine = Mock(spec=SemanticEngine)
    mock_engine.similarity.return_value = 0.8

    matcher = SimilarityMatcher(engine=mock_engine)
    result = matcher.find_best_substring("test", "test text")

    mock_engine.similarity.assert_called()
```

### Integration Tests

#### Test CLI with Engine Flag
```bash
# Test explicit engine selection
./segment.py --engs gen --chap 3 --sec 3 --version lcc \
  --seg pkuseg --semantic-engine edit-distance

# Expected: Same output as without flag
```

#### Test Accuracy Preservation
```python
def test_genesis_3_3_accuracy_preserved():
    """Ensure 61.5% match rate is maintained after refactor"""
    result = run_segmentation(
        book="gen", chapter=3, verse=3,
        version="lcc", segmenter="pkuseg",
        correct_with_sn=True, use_refinement=True,
        semantic_engine="edit-distance"
    )

    match_rate = result.get_match_rate()
    assert 0.59 <= match_rate <= 0.64  # 61.5% ± 2.5%
```

## Performance Considerations

### Baseline Performance
- Edit distance: ~1ms per query
- No caching yet (Phase 2.3)
- Pure Python implementation

### Performance Budget
- Refactoring overhead: <5% slowdown acceptable
- Memory overhead: <10MB additional
- No performance improvements expected in Phase 2.1

### Profiling Points
```python
# Add timing instrumentation
@profile
def find_best_substring(self, refTerm: str, origText: str):
    with timer(f"Engine: {self.engine.get_name()}"):
        # ... matching logic
```

## Future Extensions (Phase 2.2+)

### Neural Engines
```python
class SentenceTransformerEngine(SemanticEngine):
    def __init__(self, model_name: str = "shibing624/text2vec-base-chinese"):
        self.model = SentenceTransformer(model_name)

    def similarity(self, text1: str, text2: str) -> float:
        emb1 = self.model.encode(text1)
        emb2 = self.model.encode(text2)
        return cosine_similarity(emb1, emb2)
```

### Configuration-Driven Selection
```yaml
# config/engines.yaml
semantic_engines:
  default: hybrid
  engines:
    hybrid:
      type: HybridEngine
      components:
        - engine: edit-distance
          weight: 2.0
        - engine: sentence-transformer
          weight: 1.0
```

### Batch Processing
```python
class SemanticEngine(ABC):
    def similarity_batch(self, pairs: List[Tuple[str, str]]) -> List[float]:
        """Process multiple pairs efficiently"""
        return [self.similarity(t1, t2) for t1, t2 in pairs]
```

## Security Considerations

### Input Validation
- Validate engine type in constructor
- Sanitize text inputs (no code injection)
- Handle unicode edge cases

### Resource Limits
- No limits yet (Phase 2.1)
- Future: Timeout for slow engines
- Future: Memory limits for neural models

## Documentation

### User-Facing
- CLI help text: Explain `--semantic-engine` flag
- README: Add engine concept section
- Examples: Show how to use different engines

### Developer-Facing
- Architecture diagrams: Show component relationships
- API docs: Document SemanticEngine interface
- Examples: Show how to implement custom engines

## Open Questions

1. **Should we add validation in SemanticEngine base class?**
   - Pros: Consistent error handling
   - Cons: Extra overhead for every call
   - Decision: Add in base class, minimal overhead

2. **Should engines be stateful or stateless?**
   - EditDistance: Stateless (except normalizer)
   - Neural engines: Stateful (model weights)
   - Decision: Allow both, document clearly

3. **How to handle engine initialization failures?**
   - Model not found
   - Out of memory
   - Decision: Fail fast with clear error message

## Risks and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Regression in accuracy | Medium | High | Comprehensive testing |
| Performance degradation | Low | Medium | Profiling + 5% budget |
| Complex architecture | Low | Low | Keep interface minimal |
| Hard to extend | Low | Medium | Well-documented examples |

## Success Criteria

**Phase 2.1 Complete When**:
1. ✅ All 60 currently-passing tests remain passing (baseline: 60/80)
2. ✅ EditDistanceEngine produces identical results
3. ✅ CLI flag works
4. ✅ Performance within 5% of baseline
5. ✅ Documentation updated
6. ✅ OpenSpec validation passes
7. ✅ 18 pre-existing failing tests remain unchanged (not a regression)

## References

- **SEMANTIC_ENGINE_STRATEGY.md**: Strategic considerations
- **SEMANTIC_ENGINE_TECHNICAL_SPECS.md**: Detailed specifications
- **ARCHITECTURE_EXPLAINED.md**: Current architecture
- **CUMULATIVE_TEST_PLAN.md**: Testing approach

---

**Prepared by**: Claude Code
**Last Updated**: 2025-11-01
**Status**: Draft for Review
