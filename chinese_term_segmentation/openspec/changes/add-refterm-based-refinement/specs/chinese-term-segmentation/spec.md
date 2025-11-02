# Spec Delta: Chinese Term Segmentation

## ADDED Requirements

### Requirement: RefTerm-Based Semantic Refinement

The system MUST support RefTerm-based semantic refinement using reference terms from UNV+SN as the authoritative baseline, eliminating dependency on external dictionaries.

#### Scenario: Basic RefTerm Refinement

**Given**: UNV+SN text "神<WH0430>說<WH0559>" and LCC text "上帝說"
**When**: Extracting RefTerms and applying semantic refinement
**Then**: RefTerms [('神', 'H0430'), ('說', 'H0559')] map to [('上帝', 'H0430'), ('說', 'H0559')]
**And**: Confidence scores are [0.92, 1.0]

### Requirement: RefTerm Format Handling

RefTerm extraction MUST handle all Strong's number formats including `<WH1234>`, `{<WH1234>}`, `{H1234}`, and `(H1234)`.

#### Scenario: Multiple Format Parsing

**Given**: Text with mixed formats "神<WH0430> {<WH0559>} {H1234} (G5678)"
**When**: Parsing Strong's number formats
**Then**: All formats are correctly extracted and normalized to ['H0430', 'H0559', 'H1234', 'G5678']

### Requirement: Semantic Clustering

The system MUST build semantic clusters from multiple Bible version translations to capture translation variants.

#### Scenario: Multi-Version Clustering

**Given**: Strong's number "H0430" and versions ["UNV", "KJV", "LCC"]
**When**: Building semantic cluster
**Then**: Core term is "神" with variants ["God", "上帝", "神明"]
**And**: A unified embedding is computed from all variants

### Requirement: Accuracy Target

RefTerm refinement MUST achieve > 75% accuracy for common biblical terms.

#### Scenario: Accuracy Validation

**Given**: 100 manually annotated verses
**When**: Applying RefTerm refinement
**Then**: Overall accuracy >= 75%
**And**: Common terms (神, 耶和華, 人) achieve > 90% accuracy

### Requirement: Self-Learning Capability

The system MUST support self-learning from UNV+SN corpus to build Strong's-to-Chinese mappings.

#### Scenario: Corpus Learning

**Given**: UNV+SN Bible corpus
**When**: Scanning entire corpus
**Then**: Frequency map is built (e.g., {"H0430": {"神": 2600}})
**And**: Context patterns are captured for future refinement

### Requirement: Direct Semantic Matching

Direct semantic matching MUST compare RefTerm embeddings with target segments without dictionary dependency.

#### Scenario: Dictionary-Free Matching

**Given**: RefTerm "神" and target segments ["上", "帝"]
**When**: Encoding and comparing embeddings
**Then**: Best match "上帝" is found without using dictionary

### Requirement: Segment Length Constraints

Segment combinations MUST be limited to 1-4 characters for typical Strong's number mappings.

#### Scenario: Length Validation

**Given**: Segments ["永", "恆", "主", "上", "帝"]
**When**: Generating combinations
**Then**: Valid combinations are ["永", "永恆", "永恆主", "上帝"]
**And**: "永恆主上帝" (5 chars) is rejected

### Requirement: Embedding Cache

The system MUST maintain an embedding cache for performance optimization.

#### Scenario: Cache Performance

**Given**: Repeated terms ["神", "耶和華", "神", "耶和華"]
**When**: Encoding terms
**Then**: First occurrences are computed and cached
**And**: Subsequent occurrences are retrieved from cache with 50% hit rate

### Requirement: Configurable Threshold

Semantic similarity threshold MUST be configurable with a default of 0.6.

#### Scenario: Threshold Application

**Given**: Config with similarity_threshold: 0.6 and similarities [0.5, 0.7, 0.9]
**When**: Applying threshold
**Then**: 0.5 is rejected and [0.7, 0.9] are accepted

### Requirement: Confidence Scoring

The system MUST provide confidence scores for each refinement.

#### Scenario: Confidence Calculation

**Given**: RefTerm "神" matching "上帝" with similarity 0.92
**When**: Calculating confidence
**Then**: Confidence score is 0.92 with level "high"

### Requirement: Frequency-Based Mapping

The system MUST scan UNV+SN text to build frequency-based Strong's mappings.

#### Scenario: Frequency Map Building

**Given**: Verses ["神<H0430>說", "神<H0430>看"]
**When**: Scanning verses
**Then**: Frequency map {"H0430": {"神": 2}} is built

### Requirement: Knowledge Base Persistence

Knowledge base MUST be persistable and versionable for reuse.

#### Scenario: Save and Load

**Given**: Knowledge base with version "1.0"
**When**: Saving to disk and loading back
**Then**: Data is preserved with version tracked

### Requirement: Incremental Learning

The system MUST support incremental learning from new texts.

#### Scenario: Knowledge Update

**Given**: Existing KB {"H0430": {"神": 100}} and new text "上帝<H0430>"
**When**: Updating knowledge base
**Then**: KB becomes {"H0430": {"神": 100, "上帝": 1}}

### Requirement: Weighted Clustering

Multi-version clustering MUST weight translations by frequency and source authority.

#### Scenario: Authority Weighting

**Given**: Terms [("神", 2600, "UNV"), ("上帝", 12, "LCC")]
**When**: Building weighted cluster
**Then**: "神" is primary term due to frequency and UNV authority

### Requirement: Performance Target

RefTerm refinement MUST process a single verse in < 100ms.

#### Scenario: Single Verse Timing

**Given**: Genesis 3:5
**When**: Processing with RefTerm refinement
**Then**: Processing completes in < 100ms

### Requirement: Batch Processing

The system MUST support batch processing for multiple verses.

#### Scenario: Batch Efficiency

**Given**: Verses ["Gen 3:1", "Gen 3:2", "Gen 3:3"]
**When**: Processing as batch
**Then**: All verses processed with shared cache utilization

### Requirement: Memory Constraint

Memory usage MUST remain under 500MB for typical usage.

#### Scenario: Memory Monitoring

**Given**: Processing a full chapter
**When**: Monitoring memory usage
**Then**: Peak memory remains < 500MB

### Requirement: Cache Efficiency

Cache hit rate MUST exceed 80% for common biblical terms.

#### Scenario: Cache Hit Rate

**Given**: Processing Genesis 1
**When**: Using cache for common terms
**Then**: Cache hit rate >= 80%

## MODIFIED Requirements

### Requirement: Dual Mode Refinement

Semantic refinement MUST support both dictionary-based and RefTerm-based approaches with configurable preference.

**Previous**: Semantic refinement MUST use neural embeddings to match dictionary meanings with candidate terms

#### Scenario: Mode Selection

**Given**: Configuration with mode "refterm"
**When**: Processing verse
**Then**: Uses RefTerm-based refinement
**And**: Dictionary remains available as fallback

### Requirement: Dictionary as Fallback

The system MUST support loading Strong's dictionary entries as optional fallback when RefTerm matching confidence is low.

**Previous**: The system MUST load and parse Strong's dictionary entries for semantic matching

#### Scenario: Low Confidence Fallback

**Given**: RefTerm confidence 0.4 and dictionary available
**When**: RefTerm confidence below threshold
**Then**: System falls back to dictionary-based matching

### Requirement: Accuracy Improvement

RefTerm-based refinement MUST achieve > 75% accuracy, improving over dictionary-based approach by at least 30%.

**Previous**: Refinement MUST improve boundary accuracy by at least 20% over baseline

#### Scenario: Method Comparison

**Given**: Dictionary accuracy 57% and RefTerm accuracy 78%
**When**: Comparing methods
**Then**: 37% relative improvement meets requirement