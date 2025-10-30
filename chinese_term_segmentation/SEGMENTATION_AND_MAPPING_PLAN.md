# Chinese Term Segmentation & Multi-Language Mapping Plan

**Document Version**: 1.0
**Date**: 2025-10-30
**Status**: Planning Phase - Not Yet Implemented

---

## Overview

This document outlines the strategy for:
1. **Segmenting Chinese biblical text** into meaningful terms (solving the no-word-boundary problem)
2. **Mapping terms across different languages** to Strong's Numbers using semantic similarity

The approach uses a **Strategy Pattern** with swappable components, allowing empirical testing to determine optimal algorithms.

---

## Part 1: Chinese Term Segmentation Candidates

### Problem Statement

Chinese text has no inherent word boundaries. Example:
```
起初上帝創造天地
```
Could be segmented as:
- ✅ `["起初", "上帝", "創造", "天地"]` (4 terms, semantically correct)
- ❌ `["起", "初", "上", "帝", "創", "造", "天", "地"]` (8 characters, over-segmented)
- ❌ `["起初上帝", "創造天地"]` (2 phrases, under-segmented)

### Strategy: Empirical Testing with Four Segmenters

We will implement **four swappable segmentation strategies** and select the best based on downstream performance.

| # | Tokenizer | Library | Key Characteristics | Dictionary Support |
|---|-----------|---------|---------------------|-------------------|
| 1 | `tokenize_jieba` | jieba (結巴分詞) | Fast, most popular, wide adoption | ✅ Yes |
| 2 | `tokenize_pkuseg` | pkuseg (北大分詞) | Higher accuracy, domain-specific training | ✅ Yes |
| 3 | `tokenize_lac` | LAC (Baidu) | Deep learning (Bi-GRU-CRF), POS tagging | ✅ Yes |
| 4 | `tokenize_stanza` | Stanza (Stanford NLP) | Academic-grade, multi-language | ✅ Yes |

### Custom Dictionary Strategy

**Problem**: Default segmenters will incorrectly split biblical terms.

Example without custom dictionary:
```
尼布甲尼撒 → ["尼", "布", "甲", "尼", "撒"]  ❌ Wrong!
```

**Solution**: Version-specific custom dictionaries prevent over-segmentation.

Example with custom dictionary:
```
unv_bible_terms.txt contains "尼布甲尼撒"
Result: 尼布甲尼撒 → ["尼布甲尼撒"]  ✅ Correct!
```

**Biblical terms to include**:
- Proper nouns: 耶和華, 尼布甲尼撒, 所羅門, 以馬內利
- Theological terms: 人子, 上帝, 天堂/天國, 哈利路亞
- Book names: 創世記, 出埃及記, 馬太福音

### Evaluation Process

**No predetermined winner** - we test all four and measure performance.

#### Phase 1: Qualitative Evaluation (Manual Inspection)
- Select 10 representative verses (mix of OT/NT, short/long, narrative/poetic)
- Tokenize each verse with all four strategies
- Display side-by-side comparison
- Human judges which segmentation is most semantically meaningful

#### Phase 2: Quantitative Evaluation (Gold Standard)
- Create 10-20 verses with manually-verified "gold standard" segmentation
- Run each tokenizer and calculate:
  - **Precision**: % of predicted tokens that match gold standard
  - **Recall**: % of gold standard tokens that were predicted
  - **F1 Score**: Harmonic mean of precision and recall
- Rank segmenters by F1 score

#### Phase 3: Downstream Task Evaluation (Most Important)
- Create 10-20 verses with perfect Strong's Number alignments
- Run full alignment pipeline (segmentation → alignment → SN assignment)
- Measure **alignment accuracy**: % of correctly assigned Strong's Numbers
- **Winner**: Tokenizer with highest alignment accuracy

**Rationale**: The best tokenizer isn't necessarily the one with best segmentation by itself, but the one that produces segments most amenable to accurate Strong's Number alignment.

### Interface Design

All segmenters must implement this consistent interface:

```python
def tokenize(sentence: str) -> List[str]:
    """
    Tokenize a Chinese sentence into words/terms.

    Args:
        sentence: Raw Chinese text string

    Returns:
        List of word tokens (strings), preserving order
    """
    pass

def tokenize_with_positions(sentence: str) -> List[Tuple[str, int]]:
    """
    Tokenize with position information for alignment.

    Args:
        sentence: Raw Chinese text string

    Returns:
        List of (token, position) tuples where position is 0-indexed
    """
    pass
```

**Output Format**:
```python
# Basic output
["起初", "上帝", "創造", "天地", "。"]

# With positions (for alignment)
[("起初", 0), ("上帝", 1), ("創造", 2), ("天地", 3), ("。", 4)]
```

---

## Part 2: Multi-Language Term Mapping Plan

### Architecture: Version-Specific Dictionaries + Semantic Similarity Bridge

### Problem Statement

Different Bible versions (even in the same language) use different vocabulary:

| Concept | UNV (中文) | LCC (中文) | RCUV2010 (中文) | KJV (English) | Strong's # |
|---------|-----------|-----------|----------------|---------------|-----------|
| Heaven | 天堂 | 天國 | 天國 | heaven | H8064 |
| Nicodemus | 尼哥底母 | 尼哥底母 | 尼哥德慕 | Nicodemus | G3530 |
| LORD | 耶和華 | 耶和華 | 耶和華 | LORD | H3068 |

**Challenge**: How do we map LCC "天國" to H8064 when UNV uses "天堂"?

**Solution**: Don't map LCC → UNV directly. Instead, map both to the original Hebrew/Greek, using Strong's Numbers as the universal bridge.

### Version-Specific Dictionary Architecture

**Each Bible version gets its own dictionary**:

```
dictionaries/
├── unv_bible_terms.txt         # 和合本 (Chinese, has Strong's)
├── lcc_bible_terms.txt         # 呂振中譯本 (Chinese, target)
├── rcuv2010_bible_terms.txt    # 和合本2010 (Chinese, target)
├── kjv_bible_terms.txt         # King James Version (English, has Strong's)
├── nasb_bible_terms.txt        # New American Standard (English, has Strong's)
├── esv_bible_terms.txt         # English Standard Version (English, target)
└── all_bible_terms.json        # Cross-reference (optional)
```

**Dictionary Format** (plain text, one term per line):

```
# unv_bible_terms.txt
# UNV Biblical Terms Dictionary
# Auto-generated from UNV verses with Strong's annotations
# One term per line, UTF-8 encoding

耶和華
尼布甲尼撒
所羅門
以馬內利
人子
上帝
天堂
哈利路亞
```

```
# lcc_bible_terms.txt
# LCC Biblical Terms Dictionary
# Initially bootstrapped from unv_bible_terms.txt, then refined
# One term per line, UTF-8 encoding

耶和華
尼布甲尼撒
所羅門
以馬內利
人子
上帝
天國    # ← Different from UNV's "天堂"!
哈利路亞
```

**Why Version-Specific?**
1. Prevents incorrect segmentation: "天堂" is one term in UNV, "天國" is one term in LCC
2. Accommodates translation differences: same concept, different vocabulary
3. Extensible: works with any Bible version (Chinese, English, Korean, etc.)
4. Independent segmentation: each version tokenized with its own dictionary

**Bootstrap Strategy**:
```python
# Step 1: Generate source dictionary (UNV has Strong's Numbers)
for verse in UNV_bible:
    for (term, strong_number) in extract_annotated_terms(verse):
        add_to_dictionary("unv_bible_terms.txt", term)

# Step 2: Bootstrap target dictionary (LCC doesn't have Strong's yet)
copy("unv_bible_terms.txt", "lcc_bible_terms.txt")  # Start with UNV terms

# Step 3: Iterative refinement
while refining:
    tokenize_lcc_verses_with_dictionary("lcc_bible_terms.txt")
    review_results()
    if found_lcc_specific_term:  # e.g., "天國" instead of "天堂"
        add_term("lcc_bible_terms.txt", term)
    if found_inappropriate_term:
        remove_term("lcc_bible_terms.txt", term)
```

### Cross-Language Alignment Algorithm: The Three-Way Bridge

**Key Insight**: Don't align translations directly. Use original Hebrew/Greek as the universal bridge.

```
┌─────────────────┐
│  Target Version │  (e.g., LCC 中文, no Strong's)
│   天國, 尼哥底母   │
└────────┬────────┘
         │ Semantic Similarity
         │ (Word Embeddings)
         ↓
┌─────────────────────┐
│ Original Languages  │  Hebrew (BHS) / Greek (FHLWH)
│   שָׁמַיִם, Νικόδημος │  with Strong's Numbers
└────────┬────────────┘
         │ Semantic Similarity
         │ (Word Embeddings)
         ↓
┌─────────────────┐
│  Source Version │  (e.g., UNV 中文 or KJV English, has Strong's)
│   天堂, 尼哥底母   │
└─────────────────┘
```

**Strong's Number = Universal ID**: All versions refer to the same H8064 or G3530, regardless of language.

### AlignVerse Algorithm (Per-Verse Alignment)

**Input**:
- Source verse (e.g., UNV) with embedded Strong's Numbers: "起初<H7225>上帝<H430>創造<H1254>天<H8064>地<H776>"
- Target verse (e.g., LCC) without Strong's Numbers: "起初上帝創造天地"
- Original text (BHS Hebrew or FHLWH Greek) keyed by Strong's Number

**Algorithm Flow**:

```
Step 1: Segmentation
--------
TGT_words = tokenizer(lcc_verse)
# Result: ["起初", "上帝", "創造", "天地"]
# With positions: [("起初", 0), ("上帝", 1), ("創造", 2), ("天地", 3)]

Step 2: Extract Source Words with Strong's Numbers
--------
SRC_words = extract_words_with_sn(unv_verse)
# Result: [("起初", "H7225"), ("上帝", "H430"), ("創造", "H1254"),
#          ("天", "H8064"), ("地", "H776")]

Step 3: Alignment Loop (for each source term)
--------
For each (src_word, strong_number) in SRC_words:

    # Get original Hebrew/Greek word
    orig_word = lookup_strong_number(strong_number)  # e.g., H8064 → "שָׁמַיִם"

    # Get word embedding vectors
    V_orig = get_embedding(orig_word)      # Hebrew/Greek embedding
    V_src = get_embedding(src_word)        # Source version embedding (optional)

    # Find best match in target
    best_match = None
    best_score = -infinity

    For each tgt_word in TGT_words (if not already matched):
        V_tgt = get_embedding(tgt_word)

        # Calculate semantic similarity
        semantic_sim = semantic_strategy(V_orig, V_tgt)
        # Options: cosine similarity, euclidean distance, dot product

        # Calculate positional similarity
        positional_sim = positional_strategy(src_pos, tgt_pos, len_src, len_tgt)
        # Options: linear, gaussian, window, none

        # Weighted combination
        final_score = (semantic_weight * semantic_sim) +
                     ((1 - semantic_weight) * positional_sim)

        if final_score > best_score:
            best_score = final_score
            best_match = tgt_word

    # Assign Strong's Number to best matching target word
    assign_strong_number(best_match, strong_number)
    mark_as_matched(best_match)

Step 4: Output
--------
Return: List of (lcc_word, strong_number) pairs
# Example: [("起初", "H7225"), ("上帝", "H430"), ("創造", "H1254"),
#           ("天地", "H8064+H776")]  # Compound if needed
```

### Swappable Strategy Components

The alignment algorithm accepts **three types of pluggable strategies**:

#### 1. Semantic Similarity Strategies

```python
def semantic_strategy(vector1: np.ndarray, vector2: np.ndarray) -> float:
    """
    Calculate semantic similarity between two word embeddings.

    Returns:
        Similarity score between 0.0 and 1.0 (higher = more similar)
    """
    pass
```

**Options**:
- `strategy_cosine`: Cosine similarity (recommended, direction-based)
  ```python
  return dot(v1, v2) / (norm(v1) * norm(v2))
  ```
- `strategy_euclidean`: Euclidean distance (magnitude-sensitive)
  ```python
  return 1 / (1 + euclidean_distance(v1, v2))
  ```
- `strategy_dot_product`: Dot product (length-sensitive, rarely used)

#### 2. Positional Similarity Strategies

```python
def positional_strategy(pos1: int, pos2: int, len1: int, len2: int) -> float:
    """
    Calculate positional similarity between two word positions.

    Returns:
        Similarity score between 0.0 and 1.0 (higher = closer position)
    """
    pass
```

**Options**:
- `strategy_pos_linear`: Normalized linear distance
  ```python
  return 1 - abs(pos1/len1 - pos2/len2)
  ```
- `strategy_pos_gaussian`: Gaussian decay (soft penalty)
  ```python
  return exp(-((pos1 - pos2)**2) / (2 * sigma**2))
  ```
- `strategy_pos_window`: Fixed window (hard threshold)
  ```python
  return 1.0 if abs(pos1 - pos2) <= window else 0.0
  ```
- `strategy_pos_none`: No positional penalty (baseline)
  ```python
  return 1.0  # Always perfect positional match
  ```

#### 3. Segmentation Strategies

Already covered in Part 1 (jieba, pkuseg, LAC, Stanza).

### Word Embeddings

**Required for semantic similarity calculation**:

| Language | Embedding Source | Notes |
|----------|-----------------|-------|
| Chinese | Word2Vec, GloVe, fastText | Pre-trained on Chinese corpora |
| English | Word2Vec, GloVe, fastText | Pre-trained on English corpora |
| Hebrew | Custom or transliteration | May need to train or use transliterated forms |
| Greek | Custom or transliteration | May need to train or use transliterated forms |
| Multi-lingual | mBERT, XLM-RoBERTa | Contextualized embeddings across languages |

**Embedding Lookup Strategy**:
```python
# Option 1: Pre-trained static embeddings
embedding = word2vec_model[word]

# Option 2: Contextualized embeddings (BERT-based)
embedding = bert_model.encode(sentence)[word_index]

# Option 3: Transliteration for Hebrew/Greek
transliterated = transliterate(hebrew_word)  # שָׁמַיִם → "shamayim"
embedding = word2vec_model[transliterated]
```

### Language-Agnostic Design

**The system works with ANY language combination** as long as:

1. ✅ **Tokenizer exists** (or use character-level for languages without segmenters)
2. ✅ **Word embeddings available** (pre-trained or trained on-demand)
3. ✅ **Custom dictionary created** (bootstrapped from similar version or manual)

**Example Workflows**:

**Chinese → Hebrew**:
```
LCC (Chinese, no SN) → BHS (Hebrew, with SN)
using UNV (Chinese, with SN) as reference
```

**English → Greek**:
```
ESV (English, no SN) → FHLWH (Greek, with SN)
using KJV/NASB (English, with SN) as reference
```

**Korean → Hebrew/Greek**:
```
Korean Bible (no SN) → BHS/FHLWH (with SN)
using any version with SN as reference
```

**Cross-Language via Strong's Numbers**:
```
Chinese term → Strong's # → English term
"天國" (LCC) → H8064 → "heaven" (KJV)
```

### Cross-Version Dictionary (Optional Aggregation)

**Purpose**: Track terms across all versions for analysis and comparison.

```json
{
  "unv": {
    "terms": ["耶和華", "尼布甲尼撒", "天堂"],
    "language": "zh-TW",
    "status": "completed",
    "has_strongs": true
  },
  "lcc": {
    "terms": ["耶和華", "尼布甲尼撒", "天國"],
    "language": "zh-TW",
    "status": "in_progress",
    "has_strongs": false
  },
  "kjv": {
    "terms": ["LORD", "Nebuchadnezzar", "heaven"],
    "language": "en",
    "status": "completed",
    "has_strongs": true
  },
  "nasb": {
    "terms": ["LORD", "Nebuchadnezzar", "heaven"],
    "language": "en",
    "status": "completed",
    "has_strongs": true
  },
  "esv": {
    "terms": ["LORD", "Nebuchadnezzar", "heaven"],
    "language": "en",
    "status": "not_started",
    "has_strongs": false
  }
}
```

**Use Cases**:
- Identify which terms are shared across versions
- Track progress of dictionary building
- Generate cross-version term concordance

---

## Part 3: Evaluation Strategy

### Segmentation Evaluation (Part 1)

See "Evaluation Process" in Part 1 above.

### Alignment Evaluation (Part 2)

**Metrics**:
- **Precision**: % of assigned Strong's Numbers that are correct
- **Recall**: % of correct Strong's Numbers that were assigned
- **F1 Score**: Harmonic mean of precision and recall
- **Accuracy**: % of words with correctly assigned Strong's Numbers

**Gold Standard Creation**:
- Select 20 verses (10 OT, 10 NT)
- Mix of lengths: short (5-10 words), medium (10-20), long (20-30)
- Mix of types: narrative, law, poetry, prophecy, gospel, epistle
- Manually create perfect alignments (expert review)

**Experiment Matrix**:
Test combinations of:
- 4 segmenters × 3 semantic strategies × 4 positional strategies = 48 configurations
- For each configuration, run on 20 gold standard verses
- Record accuracy metrics
- Find best combination

**Expected Tuning Parameters**:
- `semantic_weight`: Balance between semantic and positional similarity (0.0 to 1.0)
- `sigma` (for Gaussian positional strategy): Controls how quickly positional penalty decays
- `window` (for window positional strategy): How many positions away is acceptable

---

## Part 4: Implementation Roadmap

### Phase 1: Foundation
- [ ] Set up Python environment (venv, dependencies)
- [ ] Install segmentation libraries (jieba, pkuseg, LAC, Stanza)
- [ ] Bootstrap `unv_bible_terms.txt` from UNV data
- [ ] Bootstrap `lcc_bible_terms.txt` from UNV dictionary

### Phase 2: Segmentation Implementation
- [ ] Implement `tokenize_jieba(sentence, dict_path)`
- [ ] Implement `tokenize_pkuseg(sentence, dict_path)`
- [ ] Implement `tokenize_lac(sentence, dict_path)`
- [ ] Implement `tokenize_stanza(sentence, dict_path)`
- [ ] Implement `tokenize_with_positions()` variants
- [ ] Write unit tests for each tokenizer

### Phase 3: Alignment Core
- [ ] Implement semantic similarity strategies (cosine, euclidean, dot_product)
- [ ] Implement positional similarity strategies (linear, gaussian, window, none)
- [ ] Load word embeddings (Chinese Word2Vec/GloVe)
- [ ] Implement `extract_words_with_sn(unv_verse)` parser
- [ ] Implement `AlignVerse` main algorithm
- [ ] Write integration tests

### Phase 4: Data Pipeline
- [ ] Load Bible text from `../original_text_preparation/bible_text_json/`
- [ ] Load Strong's dictionaries from `../original_text_preparation/strong_dict_json/`
- [ ] Implement batch processing (full chapters/books)
- [ ] Output format compatible with dual readers

### Phase 5: Evaluation
- [ ] Create 20 gold standard verses with manual alignments
- [ ] Implement evaluation metrics (precision, recall, F1, accuracy)
- [ ] Run experiment matrix (48+ configurations)
- [ ] Document best-performing configurations
- [ ] Publish results and analysis

### Phase 6: Production Pipeline
- [ ] Implement user-facing CLI tool
- [ ] Generate Strong's Numbers for full LCC Bible
- [ ] Export results to dual_reader_right_editor format
- [ ] Human review/editing workflow

---

## Part 5: Key Design Decisions

### Why Strategy Pattern?

**Flexibility**: Biblical text is unique. We don't know which algorithms work best until we test them empirically.

**Modularity**: Easy to add new segmenters or similarity strategies without touching core logic.

**Testability**: Each strategy can be unit tested independently.

**Composability**: Mix and match strategies to find optimal combination.

### Why Version-Specific Dictionaries?

**Accuracy**: Prevents false negatives (splitting terms that should stay together).

**Extensibility**: Works with any Bible version, any language.

**Maintainability**: Each version's dictionary evolves independently.

**Bootstrapping**: New versions can start from similar versions, then refine.

### Why Semantic + Positional Similarity?

**Semantic Alone**: May align "天" (heaven) with "地" (earth) if embeddings are poor quality.

**Positional Alone**: Assumes perfect word order, but translations often reorder phrases.

**Combined**: Leverages both meaning and structure for robust alignment.

**Tunable**: Weight parameter allows optimization for different Bible book types.

### Why Original Languages as Bridge?

**Universal Reference**: Hebrew/Greek words are the "ground truth" regardless of translation.

**Strong's Numbers**: Already established, universally recognized lexical IDs.

**Cross-Language**: Enables Chinese ↔ English alignment via H/G numbers.

**Future-Proof**: New translations always map to same original language.

---

## Part 6: Open Questions

### 1. Hebrew/Greek Word Embeddings
**Question**: How do we get quality embeddings for ancient languages with limited corpora?

**Options**:
- Use transliterated forms (e.g., H8064 "shamayim" → English-trained embeddings)
- Train embeddings on available Hebrew/Greek biblical/classical texts
- Use multilingual BERT pre-trained on ancient languages
- Manual synonym mapping for key theological terms

### 2. Compound Strong's Numbers
**Question**: How do we handle when multiple Chinese characters map to one Hebrew word or vice versa?

**Examples**:
- UNV: "天地" (heaven-earth) might be two separate H numbers
- LCC: same verse might tokenize differently

**Approach**:
- Allow compound assignments: "天地" → "H8064+H776"
- Track segmentation differences in metadata
- Post-process to merge/split as needed

### 3. Context-Aware Segmentation
**Question**: Should we use surrounding verses for disambiguation?

**Example**:
- "上帝說" (God said) - "上帝" is clearly a theological term
- "上帝說" in narrative vs poetry might tokenize differently

**Approach**:
- Phase 1: Verse-level (simpler, faster)
- Phase 2: Context-aware (more accurate, more complex)

### 4. Human-in-the-Loop
**Question**: How much manual review is acceptable/necessary?

**Approach**:
- AI generates initial alignments (80-90% accuracy target)
- Human reviewers verify/correct (dual_reader_right_editor integration)
- Learn from corrections to improve model
- Track confidence scores to prioritize review

---

## References

- **OpenSpec Specification**: `openspec/specs/chinese-term-segmentation/spec.md`
- **Project Conventions**: `openspec/project.md`
- **Parent Project**: `../CLAUDE.md`
- **FHL Bible API**: `https://bible.fhl.net/json/qb.php`

---

## Document Status

**Current State**: Planning complete, implementation not yet started.

**Next Action**: Proceed to Phase 1 (Foundation) - set up development environment and bootstrap dictionaries.

**Last Updated**: 2025-10-30
