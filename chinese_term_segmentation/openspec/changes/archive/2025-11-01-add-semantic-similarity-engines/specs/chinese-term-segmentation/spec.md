# Chinese Term Segmentation - Spec Delta

## ADDED Requirements

### Requirement: Semantic Engine Interface

The system MUST define an abstract base class for pluggable semantic similarity engines that can be used for term matching and refinement.

**Interface Definition**:
```python
class SemanticEngine(ABC):
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
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return engine identifier for logging and metrics."""
        pass
```

**Purpose**: Enable experimentation with different similarity algorithms without modifying core matching logic.

#### Scenario: EditDistanceEngine Implements Interface

**Given**: An EditDistanceEngine class that inherits from SemanticEngine
**When**: Calling `engine.similarity("神", "神")`
**Then**: Returns `1.0` (exact match)
**And**: `engine.get_name()` returns `"edit-distance"`

#### Scenario: Similarity Score Range Validation

**Given**: Any SemanticEngine implementation
**When**: Computing similarity between any two strings
**Then**: Result is a float in range [0.0, 1.0]
**And**: Never returns negative values or values > 1.0

#### Scenario: Engine Name is Unique Identifier

**Given**: Multiple registered engines (EditDistanceEngine, SentenceTransformerEngine)
**When**: Calling `get_name()` on each engine
**Then**: Each returns a unique identifier (kebab-case recommended)
**And**: Names are suitable for CLI flags and logging

---

### Requirement: SimilarityMatcher Engine Injection

The system MUST allow SimilarityMatcher to accept a pluggable SemanticEngine via dependency injection, while maintaining backward compatibility.

**Constructor Signature**:
```python
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
    self.engine = engine or EditDistanceEngine()
    # ...
```

**Design Principle**: Open/Closed Principle - open for extension, closed for modification.

#### Scenario: Default Engine is EditDistanceEngine

**Given**: SimilarityMatcher instantiated without engine parameter: `matcher = SimilarityMatcher()`
**When**: Matcher is used for finding best substring
**Then**: Uses EditDistanceEngine internally (backward compatible behavior)
**And**: All existing tests pass without modification

#### Scenario: Custom Engine Can Be Injected

**Given**: A custom engine `custom_engine = CustomEngine()`
**When**: Creating `matcher = SimilarityMatcher(engine=custom_engine)`
**Then**: Matcher uses custom_engine for all similarity calculations
**And**: Calls `custom_engine.similarity(text1, text2)` instead of internal edit distance

#### Scenario: Invalid Engine Type Raises Error

**Given**: A non-SemanticEngine object passed as engine
**When**: Creating `matcher = SimilarityMatcher(engine="invalid")`
**Then**: Raises `TypeError` with clear message
**And**: Message indicates expected type is SemanticEngine

---

### Requirement: CLI Engine Selection

The system SHALL provide a `--semantic-engine` CLI flag to allow users to select different similarity engines at runtime.

**CLI Flag**:
```bash
--semantic-engine {edit-distance,sentence-transformer,bert}
```

**Default**: `edit-distance` (backward compatible)

#### Scenario: Use Default Engine via CLI

**Given**: User runs segmentation without `--semantic-engine` flag
```bash
./segment.py --engs gen --chap 3 --sec 3 --version lcc --seg pkuseg --correct-with-sn
```
**When**: CLI processes the command
**Then**: Uses EditDistanceEngine (default)
**And**: Behavior identical to previous version (backward compatible)

#### Scenario: Explicitly Select EditDistance Engine

**Given**: User runs with explicit engine selection
```bash
./segment.py --engs gen --chap 3 --sec 3 --version lcc --seg pkuseg \
  --correct-with-sn --semantic-engine edit-distance
```
**When**: CLI processes the command
**Then**: Uses EditDistanceEngine
**And**: Output is identical to default (no flag) behavior

#### Scenario: Invalid Engine Name Shows Error

**Given**: User runs with unsupported engine name
```bash
./segment.py --engs gen --chap 3 --sec 3 --version lcc --seg pkuseg \
  --semantic-engine invalid-engine
```
**When**: CLI processes the command
**Then**: Displays error message listing valid engine choices
**And**: Exits with non-zero exit code
**And**: Does not proceed with segmentation

#### Scenario: Help Text Documents Engine Flag

**Given**: User runs `./segment.py --help`
**When**: Help output is displayed
**Then**: `--semantic-engine` flag is documented
**And**: Description explains purpose and available choices
**And**: Default value is clearly indicated

---

### Requirement: EditDistanceEngine Baseline Implementation

The system MUST provide an EditDistanceEngine that wraps existing edit distance logic and serves as the baseline implementation.

**Implementation Requirements**:
- Inherits from SemanticEngine
- Implements `similarity(text1, text2)` using Levenshtein distance
- Implements `get_name()` returning `"edit-distance"`
- Integrates with CharVariantNormalizer for character variant handling
- Produces identical results to previous implementation

#### Scenario: EditDistanceEngine Preserves Existing Logic

**Given**: Previous implementation's edit distance calculation for ("神", "上帝")
**When**: Using `EditDistanceEngine().similarity("神", "上帝")`
**Then**: Returns identical score to previous implementation
**And**: Character variant normalization still applies

#### Scenario: EditDistanceEngine Exact Match

**Given**: EditDistanceEngine instance
**When**: Computing similarity of identical strings: `similarity("起初上帝創造天地", "起初上帝創造天地")`
**Then**: Returns `1.0` (perfect match)

#### Scenario: EditDistanceEngine No Match

**Given**: EditDistanceEngine instance
**When**: Computing similarity of completely different strings: `similarity("神", "上帝")`
**Then**: Returns `0.0` (no shared characters after normalization)

#### Scenario: EditDistanceEngine Partial Match

**Given**: EditDistanceEngine instance
**When**: Computing similarity of partially overlapping strings: `similarity("神的", "神")`
**Then**: Returns score in range `(0.0, 1.0)` based on character overlap
**And**: Longer common substring yields higher score

---

### Requirement: Backward Compatibility Guarantee

Phase 2.1 refactoring MUST maintain 100% backward compatibility with existing functionality.

**Non-Breaking Changes**:
- All 60 currently-passing tests remain passing (baseline: 60/80 passing)
- Default behavior (no `--semantic-engine` flag) unchanged
- Performance within 5% of baseline
- Accuracy on Genesis 3:3 remains 61.5% ± 2%
- 18 pre-existing failing tests (plugin/API issues) remain unchanged (not a regression)

#### Scenario: All Currently-Passing Tests Remain Passing

**Given**: Current test baseline of 60 passing tests out of 80 total
**And**: 18 tests failing due to pre-existing issues (plugin/API)
**When**: Running `python -m pytest tests/ -v` after Phase 2.1 changes
**Then**: At least 60 tests pass (same or better than baseline)
**And**: No currently-passing tests become failing (no regressions)
**And**: Test coverage remains >80%
**Note**: The 18 pre-existing failures are not blocking for Phase 2.1

#### Scenario: CLI Without New Flag Works Identically

**Given**: Existing CLI command from before Phase 2.1:
```bash
./segment.py --engs gen --chap 3 --sec 3 --version lcc --seg pkuseg \
  --correct-with-sn --use-refinement
```
**When**: Running this command after Phase 2.1 refactoring
**Then**: Output format is identical
**And**: Match rate is 61.5% ± 2% (within statistical variance)
**And**: No new warnings or errors appear

#### Scenario: Performance Does Not Degrade

**Given**: Performance baseline from before Phase 2.1 (e.g., 50ms per verse)
**When**: Running same workload after Phase 2.1
**Then**: Performance is within 5% of baseline (≤52.5ms per verse)
**And**: Memory usage increase is less than 10%

---

## MODIFIED Requirements

### Requirement 5: Segmentation Evaluation (Enhancement)

**Enhancement**: Add semantic engine comparison as an evaluation dimension.

**Added Evaluation Approach**:
3. **Engine Comparison**: Compare accuracy across different semantic engines

#### Scenario: Compare Multiple Engines on Same Dataset

**Given**: A test set of 20 verses with gold standard Strong's alignments
**And**: Three engines registered: EditDistanceEngine, SentenceTransformerEngine, ChineseBertEngine
**When**: Running alignment pipeline with each engine
**Then**: System reports accuracy metrics for each engine
**And**: Results displayed in comparison table format
**And**: Best engine identified by highest accuracy

**Added to existing evaluation approaches** (Qualitative and Quantitative remain unchanged).

---

### Requirement 6: Performance Requirements (Clarification)

**Clarification**: Performance targets apply to EditDistanceEngine. Future neural engines have different targets.

**Performance Targets by Engine Type**:
- **EditDistanceEngine**: < 1ms per similarity query
- **Neural engines** (Phase 2.2): < 50ms per query (before caching)

**Existing Target Unchanged**: Process a full Bible book (e.g., Genesis with 50 chapters) in < 1 minute on standard hardware.

#### Scenario: EditDistanceEngine Maintains Fast Performance

**Given**: EditDistanceEngine used in SimilarityMatcher
**When**: Processing single verse segmentation
**Then**: Similarity queries complete in < 1ms each
**And**: Total verse processing remains < 100ms

---

## Notes

**Phase 2.1 Scope**:
- This delta covers ONLY the architecture refactoring
- Neural engine implementations (SentenceTransformer, BERT) are NOT in this change
- Neural engines will be added in Phase 2.2 (separate OpenSpec proposal)

**Testing Strategy**:
- All new requirements have corresponding test scenarios (T034-T036)
- Backward compatibility validated through regression testing
- Performance validated through benchmarking

**Future Extensions** (Not in Phase 2.1):
- SentenceTransformerEngine implementation
- ChineseBertEngine implementation
- Configuration file support (YAML)
- Caching layer
- Benchmark framework

---

**Change ID**: add-semantic-similarity-engines
**Phase**: 2.1 (Architecture Refactor)
**Status**: Proposed
**Blocks**: Phase 2.2 (Neural Engine Implementation)
