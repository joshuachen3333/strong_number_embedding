# Design: RefTerm-Based Refinement System

## Architecture Dependencies

**IMPORTANT: This design REUSES existing components from Phase 2.1 to avoid code duplication.**

### Dependency Graph

```
RefTermSemanticEngine (Phase 2.3)
  │
  ├─> SimilarityMatcher (Phase 2.1) ✅ REUSED
  │    └─> SemanticEngine (edit-distance / sentence-transformer)
  │
  ├─> RefTermExtractor (Phase 2.3) ✅ NEW
  └─> SemanticCluster (Phase 2.3) ✅ NEW
```

### Rationale for Reuse

**Problem Identified**: Initial implementation duplicated the core matching logic:
- `SimilarityMatcher.find_best_substring()` (Phase 2.1) ✅ Already implemented
- `RefTermSemanticEngine.find_best_match()` (Phase 2.3) ❌ Was duplicate code

**Solution**: RefTermSemanticEngine delegates to SimilarityMatcher for the matching algorithm:
```python
def find_best_match(self, refterm, candidate_segments):
    # Convert segments to text
    origText = ''.join(candidate_segments)

    # REUSE: Delegate to SimilarityMatcher (DRY principle)
    return self.similarity_matcher.find_best_substring(
        refTerm=refterm.term,
        origText=origText,
        threshold=self.similarity_threshold
    )
```

**Benefits**:
- ✅ Single source of truth for semantic matching algorithms
- ✅ Easier maintenance (fix bugs in one place)
- ✅ Consistent behavior across all refinement modes
- ✅ RefTermSemanticEngine focuses on RefTerm-specific logic (caching, clustering)

## RefTerm Source and Semantic Engine: Two Independent Layers

**IMPORTANT**: RefTerm source (data selection) and semantic engine (algorithm) are SEPARATE, orthogonal concerns:

### Data Flow Diagram

```
FHL qp.php API
    │
    ├─ word (Hebrew 詞形)          Example: בְּיוֹם, אֱלֹהִים
    ├─ orig (Hebrew 詞根)          Example: יוֹם, אֱלֹהִים
    └─ exp  (FHL 中文解釋)         Example: 「日子」、「上帝、神」
           │
           │  } --refterm-source {hebrew-word, hebrew-lemma, fhl-chinese}
           │    (Data Selection Layer: Choose which field to use as RefTerm)
           │
           ▼
      RefTerm 提取
      (Extract RefTerm from chosen source)
           │
           ▼
    SimilarityMatcher.find_best_substring()
      (Core matching algorithm - REUSED from Phase 2.1)
           │
           │  } --semantic-engine {sentence-transformer, edit-distance}
           │    (Algorithm Layer: Choose similarity calculation method)
           │
    ┌──────┴──────┐
    │             │
SentenceTransformer  EditDistance
(neural embeddings)  (character-based)
    │             │
    └──────┬──────┘
           │
           ▼
       匹配結果
    (Best substring match)
```

### Layer Distinction

| Layer | Parameter | Purpose | Type | Options |
|-------|-----------|---------|------|---------|
| **Data Selection** | `--refterm-source` | Choose RefTerm data source | Configuration | `hebrew-word`, `hebrew-lemma`, `fhl-chinese` |
| **Algorithm** | `--semantic-engine` | Choose similarity algorithm | Algorithm | `sentence-transformer`, `edit-distance` |

### CLI Design

**Separate Parameters (Chosen Design)**:
```bash
segment.py \
  --use-refterm \
  --refterm-source {hebrew-word,hebrew-lemma,fhl-chinese} \  # NEW: Data source
  --semantic-engine {sentence-transformer,edit-distance} \   # Existing: Algorithm
  --correct-with-sn
```

**Total Combinations**: 3 RefTerm sources × 2 Semantic engines = **6 configurations**

**Rationale for Separate Parameters**:
- ✅ More flexible (can independently change data source or algorithm)
- ✅ Clearer separation of concerns
- ✅ Easier to extend (add new sources or engines independently)
- ✅ Better for experimentation and A/B testing

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   UNV+SN Text   │────▶│  RefTerm Extract │────▶│ RefTerm Cluster │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Target Text    │────▶│    Segmentation  │────▶│ SimilarityMatcher│ ← REUSED from Phase 2.1
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
                                                  ┌─────────────────┐
                                                  │ Refined Output  │
                                                  └─────────────────┘
```

## Core Components

### 1. RefTermExtractor
```python
class RefTermExtractor:
    """Extract reference terms from UNV+SN text"""

    def extract_terms(self, unv_sn_text: str) -> List[RefTerm]:
        """
        Parse UNV+SN text to extract (term, strong_num) pairs
        Example: '神<WH0430>' -> RefTerm('神', 'H0430')
        """

    def build_corpus_map(self) -> Dict[str, Counter]:
        """
        Scan entire UNV+SN Bible to build frequency map
        Returns: {strong_num: Counter({term: frequency})}
        """
```

### 2. RefTermSemanticEngine
```python
class RefTermSemanticEngine:
    """Core semantic matching using RefTerms as baseline

    ARCHITECTURE: Delegates to SimilarityMatcher (Phase 2.1) for matching logic.
    Focuses on RefTerm-specific features: caching, clustering, batch processing.
    """

    def __init__(self, base_engine):
        self.base_engine = base_engine  # SentenceTransformer

        # REUSE: SimilarityMatcher from Phase 2.1
        self.similarity_matcher = SimilarityMatcher(
            semantic_engine=base_engine,
            default_threshold=0.6
        )

        self.refterm_cache = {}   # RefTerm-specific cache
        self.cluster_cache = {}   # Semantic cluster cache

    def encode_refterm(self, refterm: str) -> np.ndarray:
        """Encode RefTerm with caching (separate from base engine cache)"""

    def find_best_match(self, refterm: RefTerm,
                       candidate_segments: List[str]) -> Tuple[str, float]:
        """Find best matching candidate for RefTerm

        DELEGATES to SimilarityMatcher.find_best_substring() - NO duplicate code!
        """
        origText = ''.join(candidate_segments)
        return self.similarity_matcher.find_best_substring(
            refTerm=refterm.term,
            origText=origText,
            threshold=self.similarity_threshold
        )

    def build_semantic_cluster(self, strong_num: str) -> SemanticCluster:
        """Build cluster from multiple translation variants"""
```

### 3. SemanticCluster
```python
class SemanticCluster:
    """Represent semantic variants for a Strong's number"""

    def __init__(self, strong_num: str):
        self.strong_num = strong_num
        self.core_term = None  # Primary RefTerm from UNV
        self.variants = []     # Alternative translations
        self.embeddings = []   # Pre-computed embeddings

    def add_variant(self, term: str, source: str):
        """Add translation variant from a source"""

    def get_unified_embedding(self) -> np.ndarray:
        """Get averaged embedding of all variants"""
```

### 4. RefTermRefinementPipeline
```python
class RefTermRefinementPipeline:
    """Complete pipeline for RefTerm-based refinement"""

    def refine(self, coarse_term: str, strong_num: str,
               target_segments: List[str]) -> str:
        """
        Main refinement method
        1. Extract clean RefTerm from coarse_term
        2. Get/build semantic cluster for strong_num
        3. Find best match in target_segments
        4. Return refined term
        """

    def refine_batch(self, alignments: List[dict],
                     target_text: str) -> List[dict]:
        """Batch refinement for entire verse"""
```

## Key Algorithms

### Direct Semantic Matching
```python
def direct_semantic_match(refterm: str, target_segments: List[str],
                         semantic_engine) -> Tuple[str, float]:
    """
    Core algorithm: Match RefTerm directly against segments
    No dictionary needed!
    """
    ref_embedding = semantic_engine.encode(refterm)

    best_match = None
    best_score = 0.0

    # Try all possible segment combinations (1-4 chars typical)
    for i in range(len(target_segments)):
        for length in range(1, min(5, len(target_segments) - i + 1)):
            candidate = ''.join(target_segments[i:i+length])

            # Skip if too long (Strong's rarely > 4 chars in Chinese)
            if len(candidate) > 4 and not is_compound_term(candidate):
                continue

            cand_embedding = semantic_engine.encode(candidate)
            similarity = cosine_similarity(ref_embedding, cand_embedding)

            if similarity > best_score:
                best_score = similarity
                best_match = candidate

    return best_match, best_score
```

### Self-Learning from Corpus
```python
def build_strong_knowledge_base(unv_bible_path: str) -> Dict:
    """
    Learn Strong's mappings from UNV+SN itself
    This is more reliable than any dictionary!
    """
    knowledge_base = defaultdict(lambda: defaultdict(int))

    for verse in read_unv_bible(unv_bible_path):
        ref_terms = extract_refterms(verse.text)

        for term, strong_num in ref_terms:
            # Count frequency of each term for this Strong's
            knowledge_base[strong_num][term] += 1

            # Also capture context patterns
            context = get_surrounding_words(term, verse.text)
            knowledge_base[f"{strong_num}_context"][context] += 1

    return knowledge_base
```

### Multi-Version Clustering
```python
def build_translation_clusters(strong_num: str,
                              versions: List[str]) -> SemanticCluster:
    """
    Build semantic cluster from multiple Bible versions
    """
    cluster = SemanticCluster(strong_num)

    # Primary: UNV translation
    unv_terms = get_terms_for_strong('UNV', strong_num)
    cluster.core_term = most_frequent(unv_terms)

    # Add variants from other versions
    for version in versions:
        terms = get_terms_for_strong(version, strong_num)
        for term in terms:
            cluster.add_variant(term, version)

    # Compute unified representation
    cluster.compute_embeddings()

    return cluster
```

## Configuration

```yaml
refterm_refinement:
  # Semantic matching thresholds
  similarity_threshold: 0.6  # Lower than before since RefTerms are authoritative

  # Segment length constraints
  max_segment_length: 4  # Most Strong's map to 1-4 Chinese chars

  # Clustering parameters
  min_cluster_frequency: 3  # Min occurrences to include in cluster

  # Caching
  enable_embedding_cache: true
  cache_size: 10000
```

## Data Flow Example

Input:
```
UNV+SN: 神<WH0430>說<WH0559>
LCC: 上帝說
```

Process:
1. Extract RefTerms: [('神', 'H0430'), ('說', 'H0559')]
2. Segment LCC: ['上帝', '說']
3. Semantic match:
   - '神' → '上帝' (similarity: 0.92)
   - '說' → '說' (similarity: 1.0)
4. Output: [('上帝', 'H0430'), ('說', 'H0559')]

## Testing Strategy

1. **Unit Tests**: RefTerm extraction, semantic matching
2. **Integration Tests**: Full pipeline with real verses
3. **Accuracy Tests**: Measure improvement over dictionary-based approach
4. **Performance Tests**: Ensure < 100ms per verse

## Migration Path

1. Keep existing dictionary-based system as fallback
2. Add RefTerm system in parallel
3. A/B test on sample verses
4. Gradual rollout based on confidence scores
5. Full migration once accuracy > 75%