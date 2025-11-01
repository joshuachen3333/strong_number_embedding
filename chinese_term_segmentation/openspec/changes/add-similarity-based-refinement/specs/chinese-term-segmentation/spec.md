# Spec Deltas: Chinese Term Segmentation - Similarity-Based Refinement

## ADDED Requirements

### Requirement: FHL Strong's Dictionary API Integration

The system MUST integrate with FHL Strong's Dictionary API to fetch semantic meanings for Strong's Numbers.

**Purpose**: Enable refinement of coarse-grained FHL boundaries by understanding the semantic meaning of each Strong's Number.

**API Specification**:
- **Endpoint**: `https://bible.fhl.net/json/sd.php`
- **Parameters**:
  - `N`: Testament (0=New Testament, 1=Old Testament)
  - `k`: Strong's number (numeric, without G/H prefix)
  - `gb`: Language (0=traditional Chinese, 1=simplified Chinese)

**Interface**:
```python
@dataclass
class StrongEntry:
    """Strong's dictionary entry."""
    sn: str                    # "3439"
    original: str              # "μονογενής"
    chinese_meaning: str       # "獨生的"
    english_meaning: str       # "only begotten"
    related: List[str]         # Related words (NT only)

class FHLClient:
    def fetch_strong_dict(
        self,
        sn: str,
        simplified: bool = False
    ) -> Optional[StrongEntry]:
        """Fetch Strong's dictionary entry from FHL API."""
```

#### Scenario: Fetch Greek Strong's Number

**Given**: Strong's Number "G3439" (μονογενής)
**When**: Calling `fhl_client.fetch_strong_dict("G3439")`
**Then**: Returns `StrongEntry` with:
- `sn = "3439"`
- `original = "μονογενής"`
- `chinese_meaning = "獨生的"` (or similar)
- `english_meaning` contains "only begotten"

**And**: API called with parameters `N=0, k=3439, gb=0`

#### Scenario: Fetch Hebrew Strong's Number

**Given**: Strong's Number "H430" (אֱלֹהִים = God)
**When**: Calling `fhl_client.fetch_strong_dict("H430")`
**Then**: Returns `StrongEntry` with:
- `sn = "430"`
- `original = "אֱלֹהִים"`
- `chinese_meaning = "神"` (or similar)

**And**: API called with parameters `N=1, k=430, gb=0` (Testament=1 for OT)

#### Scenario: Handle API Errors Gracefully

**Given**: Network error or missing dictionary entry
**When**: Calling `fhl_client.fetch_strong_dict("G99999")`
**Then**: Returns `None` (not exception)
**And**: Logs warning about missing entry
**And**: Caller can fallback to coarse boundary

### Requirement: Similarity-Based Substring Matching

The system MUST find the best matching substring within coarse-grained boundaries using character-level similarity.

**Problem**: FHL annotations like "將他的獨生<G3439>" include extra characters beyond the core semantic meaning.

**Solution**: Use Strong's Dictionary meaning ("獨生的") to find the precise matching substring ("獨生") within the coarse boundary.

**Algorithm**:
1. Generate all substrings of coarse boundary (length ≥ 2)
2. Normalize character variants for comparison
3. Calculate edit distance similarity for each substring
4. Return substring with highest similarity above threshold

**Interface**:
```python
class SimilarityMatcher:
    def find_best_substring(
        self,
        refTerm: str,
        origText: str,
        threshold: float = 0.6
    ) -> Optional[str]:
        """Find best matching substring in origText."""

    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity score (0.0-1.0)."""

    def _normalize_variants(self, text: str) -> str:
        """Normalize character variants (爲→為)."""
```

**Similarity Scoring**:
```
similarity = 1.0 - (edit_distance / max_length)
```

#### Scenario: Extract Precise Term from Coarse Boundary

**Given**:
- Reference term: "獨生的" (from Strong's G3439)
- Coarse boundary: "將他的獨生" (from FHL)

**When**: Calling `matcher.find_best_substring("獨生的", "將他的獨生")`
**Then**: Returns `"獨生"`
**And**: Similarity score ≥ 0.6
**And**: "獨生" is the substring most similar to "獨生的" (removing "的" suffix)

#### Scenario: Handle Character Variants

**Given**:
- Reference term: "因為" (U+70BA standard form)
- Coarse boundary: "因爲天國" (U+7232 variant form)

**When**: Calling `matcher.find_best_substring("因為", "因爲天國")`
**Then**: Returns `"因爲"`
**And**: Character variants normalized before matching
**And**: Normalized forms match exactly (both become "因為")

#### Scenario: No Good Match Returns None

**Given**:
- Reference term: "獨生的"
- Coarse boundary: "天國是" (unrelated text)

**When**: Calling `matcher.find_best_substring("獨生的", "天國是")`
**Then**: Returns `None`
**And**: No substring exceeds threshold (0.6)
**And**: Caller falls back to coarse boundary "天國是"

#### Scenario: Skip Single-Character Substrings

**Given**:
- Reference term: "神"
- Coarse boundary: "上帝的神蹟"

**When**: Generating substrings for matching
**Then**: Single-character substrings ("上", "帝", "的", "神", "蹟") are skipped
**And**: Only multi-character substrings considered (e.g., "上帝", "神蹟")
**And**: Avoids unreliable single-char matches

### Requirement: Two-Stage Term Refinement

The system MUST implement a two-stage refinement process that refines UNV boundaries first, then matches to target versions.

**Stage 1: UNV Term Refinement**
- Input: Coarse UNV boundaries with Strong's Numbers
- Process: For each `(coarse_term, SN)`:
  1. Fetch SN semantic meaning from Strong's Dictionary
  2. Find best substring in coarse_term matching the meaning
  3. Replace coarse term with refined term
- Output: Refined UNV boundaries (precise terms)

**Stage 2: Target Version Matching**
- Input: Refined UNV terms + target version text (LCC)
- Process: Match each refined term in target text with variant handling
- Output: Matched terms for boundary correction

**Interface**:
```python
class BoundaryCorrector:
    def correct_with_refinement(
        self,
        target_text: str,
        initial_segments: List[str],
        unv_sn_text: str
    ) -> Tuple[List[str], CorrectionMetrics]:
        """Correct with two-stage refinement."""

    def _refine_term(
        self,
        coarse_term: str,
        sn: str
    ) -> Optional[str]:
        """Refine coarse term using SN semantics (Stage 1)."""

    def _find_matches_with_variants(
        self,
        target_text: str,
        refined_terms: List[str]
    ) -> Set[str]:
        """Match refined terms in target (Stage 2)."""
```

**Enhanced Metrics**:
```python
@dataclass
class CorrectionMetrics:
    # Existing Phase 1 metrics
    character_match_rate: float
    correction_success_rate: float

    # New Phase 1.5 metrics
    refinement_rate: float        # % of coarse terms refined
    variant_match_rate: float     # % matched via variants
    stage1_precision: float       # Refinement accuracy
    stage2_recall: float          # Target matching coverage
```

#### Scenario: Refine Coarse UNV and Match to LCC

**Given**:
- UNV+SN text: "甚至將他的獨生<G3439>子<G5207>賜給"
- LCC text: "甚至賜下獨生子"
- Initial LCC segments: `["甚至", "賜", "下獨", "生子"]`

**When**: Calling `corrector.correct_with_refinement(lcc_text, segments, unv_sn_text)`
**Then**:
- **Stage 1**: Coarse "將他的獨生" → Refined "獨生" (using G3439 meaning "獨生的")
- **Stage 2**: "獨生" found in LCC text "賜下獨生子"
- **Correction**: Merges incorrect "下獨 | 生子" → correct "獨生 | 子"
- **Output**: `["甚至", "賜下", "獨生", "子"]`

**And**: Match rate improves vs Phase 1

#### Scenario: Fallback When Refinement Fails

**Given**:
- Coarse term: "天國的人"
- Strong's Number: G932
- FHL API unavailable (returns None)

**When**: Attempting to refine term
**Then**:
- Stage 1 returns None for Strong's entry
- Falls back to coarse term "天國的人"
- Stage 2 proceeds with coarse term
- No worse than Phase 1 behavior

**And**: Logs warning about API failure

#### Scenario: Improved Match Rate vs Phase 1

**Given**: John 3:16 test verse
**And**: Phase 1 character match rate: 55.6%
**When**: Using Phase 1.5 refinement
**Then**: Character match rate ≥ 65%
**And**: Metrics show `refinement_rate` > 0
**And**: Metrics show specific improvements (coarse → refined counts)

### Requirement: Character Variant Normalization

The system MUST normalize common Chinese character variants to improve matching accuracy.

**Common Biblical Variants**:

| Variant | Standard | Unicode | Example |
|---------|----------|---------|---------|
| 爲 | 為 | U+7232 → U+70BA | 因爲 (because) |
| 衞 | 衛 | U+885E → U+885B | 大衞 (David) |
| 綫 | 線 | U+7DAB → U+7DDA | 界綫 (boundary) |

**Strategy**: Hardcoded mapping for common variants (expandable as new variants discovered)

**Interface**:
```python
class SimilarityMatcher:
    def _normalize_variants(self, text: str) -> str:
        """Normalize character variants to standard form."""

    def _load_character_variants(self) -> Dict[str, str]:
        """Load variant mapping dictionary."""
```

#### Scenario: Normalize 爲 to 為

**Given**: Text containing "因爲" (LCC with variant U+7232)
**When**: Calling `matcher._normalize_variants("因爲天國")`
**Then**: Returns `"因為天國"` (standard U+70BA)
**And**: Now matches UNV text "因為天國" via string equality

#### Scenario: Match Across Versions Despite Variants

**Given**:
- Refined UNV term: "因為" (standard form)
- LCC text: "因爲天國是" (variant form)

**When**: Stage 2 matching with variant handling
**Then**:
- Direct match fails: `"因為" not in "因爲天國是"`
- Variant-normalized match succeeds: `normalize("因為") in normalize("因爲天國是")`
- Matched term: `"因爲"` (preserves LCC's original variant)

**And**: LCC text unchanged (still uses 爲)

#### Scenario: Log Unmatched Terms for Discovery

**Given**: An unmatched term that may contain unknown variant
**When**: Both direct and variant-normalized matching fail
**Then**: System logs: `"Unmatched term: {term} (consider variant?)"`
**And**: Developers can review logs to discover new variants
**And**: Variant map can be expanded in future

### Requirement: Performance Optimization

The system MUST optimize refinement performance by leveraging existing coarse-grained boundaries.

**Optimization Strategy**:
- ✅ Use coarse boundaries (5-10 chars) not entire verses (30+ chars)
- ✅ Cache Strong's Dictionary API responses (session-scoped)
- ✅ Cache refinement results per verse
- ✅ Early termination for high-confidence matches

**Performance Targets**:
- API latency (first verse): ≤1000ms amortized across ~20 SNs
- API latency (cached): 0ms
- Refinement overhead: <150ms per verse
- Total overhead vs Phase 1: <200ms

**Caching**:
```python
# Session-scoped caches (in-memory, no persistence)
_strong_dict_cache: Dict[str, StrongEntry] = {}
_refinement_cache: Dict[Tuple[str, str], str] = {}
```

#### Scenario: Substring Complexity Advantage

**Given**: Coarse term "將他的獨生" (5 characters)
**When**: Generating all substrings (length ≥ 2)
**Then**: Generates 10 substrings:
- Length 2: ["將他", "他的", "的獨", "獨生"]
- Length 3: ["將他的", "他的獨", "的獨生"]
- Length 4: ["將他的獨", "他的獨生"]
- Length 5: ["將他的獨生"]

**And**: Complexity O(n²) = O(25) operations
**Comparison**: Entire verse (30 chars) = O(900) operations
**Improvement**: 36x fewer substrings to evaluate

#### Scenario: API Response Caching

**Given**: Processing John 3:16-20 (5 verses)
**And**: G3439 (μονογενής) appears in multiple verses
**When**: First lookup of G3439
**Then**: Fetches from API (~50-100ms latency)
**And**: Caches result in memory with key "G3439_0" (sn + simplified flag)
**When**: Subsequent lookups of G3439 in other verses
**Then**: Returns from cache (0ms latency)
**And**: Total API calls = unique SNs, not total SN occurrences

#### Scenario: Meet Performance Budget

**Given**: Verse with 20 terms requiring refinement
**When**: Processing with Phase 1.5
**Then**:
- API calls (from cache): 0ms
- Refinement (20 terms × 5ms avg): ~100ms
- Variant matching: ~50ms
- **Total overhead**: ~150ms

**And**: Stays under 200ms budget
**And**: Acceptable for interactive CLI usage

## MODIFIED Requirements

None. All existing requirements remain unchanged. This proposal is purely additive.

## REMOVED Requirements

None. This proposal removes no functionality.

## RENAMED Requirements

None. This proposal renames no requirements.
