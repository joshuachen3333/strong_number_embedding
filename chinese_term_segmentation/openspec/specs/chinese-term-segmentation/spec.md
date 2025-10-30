# Chinese Term Segmentation

**Status**: Active
**Version**: 1.0
**Owner**: Strong's Number Embedding Project

## Purpose

Chinese term segmentation breaks continuous Chinese biblical text (which has no inherent word boundaries) into meaningful semantic units (words/terms) that can be used for Strong's Number alignment and other NLP tasks.

This capability uses a **Strategy Pattern** to support multiple swappable segmentation algorithms, allowing experimentation to find the best approach for biblical Chinese text.
## Requirements

### Requirement 1: Swappable Tokenization Strategies

The system MUST support multiple tokenization algorithms that can be easily swapped without modifying the core code.

**Interface**:
```python
def tokenize(sentence: str) -> List[str]:
    """
    Tokenize a Chinese sentence into words/terms.

    Args:
        sentence: Raw Chinese text string

    Returns:
        List of word tokens (strings)
    """
```

**Supported Strategies**:
- `tokenize_jieba` - Using jieba (結巴分詞) library
- `tokenize_pkuseg` - Using pkuseg (北大分詞) library
- `tokenize_lac` - Using LAC (Baidu) library
- `tokenize_stanza` - Using Stanza (Stanford NLP) library

#### Scenario: Tokenize Genesis 1:1 with Jieba

**Given**: The LCC verse text "起初上帝創造天地。"
**When**: Calling `tokenize_jieba("起初上帝創造天地。")`
**Then**: Returns a list like `["起初", "上帝", "創造", "天", "地", "。"]`
**Note**: "天" (H8064) and "地" (H776) are separate terms with different Strong's Numbers

#### Scenario: Tokenize Same Verse with PKUSeg

**Given**: The LCC verse text "起初上帝創造天地。"
**When**: Calling `tokenize_pkuseg("起初上帝創造天地。")`
**Then**: Returns a list (may differ from jieba based on algorithm)
**And**: The returned list type and structure matches the tokenizer interface

#### Scenario: Strategy is Passable as Function Parameter

**Given**: A main processing function `process_verse(text, tokenizer)`
**When**: Calling `process_verse(verse_text, tokenize_jieba)`
**Then**: The jieba tokenizer is used for segmentation
**When**: Calling `process_verse(verse_text, tokenize_pkuseg)`
**Then**: The pkuseg tokenizer is used instead without code changes

### Requirement 2: Multi-Dictionary Support

The system MUST support separate dictionaries for different Bible versions to accommodate their distinct translation vocabularies.

**Note**: This is a general architecture. While examples use UNV (source) and LCC (target), the system should work with any combination:
- Source versions with Strong's Numbers: UNV, KJV, NASB, etc.
- Target versions: LCC, RCUV2010, ESV, or any version needing Strong's Number annotation

**Dictionary Architecture**:

1. **Version-Specific Dictionaries** (one per version):
   - Naming pattern: `{version}_bible_terms.txt` (e.g., `unv_bible_terms.txt`, `kjv_bible_terms.txt`)
   - Examples in this spec use `unv_bible_terms.txt` and `lcc_bible_terms.txt`
   - Format: One term per line (UTF-8 encoded)

2. **Cross-Version Dictionary** (optional):
   - `all_bible_terms.json` - Aggregated terms from all versions
   - Format: JSON with version keys (extensible to any version)
   ```json
   {
     "unv": ["耶和華", "尼哥底母", "天堂", ...],
     "kjv": ["LORD", "Nicodemus", "heaven", ...],
     "nasb": ["LORD", "Nicodemus", "heaven", ...],
     "lcc": ["耶和華", "尼哥底母", "天國", ...],
     "rcuv2010": ["耶和華", "尼哥德慕", "天國", ...]
   }
   ```

**Dictionary Purpose**: Prevent over-segmentation of terms that correspond to single Strong's Numbers in their respective versions

**Key Principle**: Even within the same verse, source and target versions may use different terms for the same concept (e.g., UNV "天堂" vs LCC "天國", or RCUV2010 "尼哥德慕" vs UNV "尼哥底母"). This is why:
- Each version needs its own dictionary
- Tokenization happens independently per version
- **Alignment** (matching terms between versions) happens AFTER tokenization using semantic similarity + positional similarity
- **Extensible Design**: Works with any source version (UNV, KJV, NASB) and any target version

#### Scenario: Load Version-Specific Dictionary for UNV

**Given**: A file `unv_bible_terms.txt` extracted from UNV containing:
```
耶和華
以馬內利
尼布甲尼撒
所羅門
人子
創世記
上帝
天堂
```
**When**: Tokenizing UNV text with this dictionary
**Then**: These terms will not be over-split during tokenization
**And**: Each term corresponds to a single Strong's Number in UNV

#### Scenario: Load Version-Specific Dictionary for LCC

**Given**: A file `lcc_bible_terms.txt` containing LCC-specific terms:
```
耶和華
以馬內利
尼布甲尼撒
所羅門
人子
創世記
上帝
天國
```
**When**: Tokenizing LCC text with this dictionary
**Then**: LCC terms are correctly preserved
**Note**: "天國" in LCC vs "天堂" in UNV - same concept, different terms

#### Scenario: Tokenize UNV with UNV Dictionary

**Given**: `unv_bible_terms.txt` contains "耶和華"
**And**: UNV input text is "耶和華上帝創造天地"
**When**: Tokenizing with jieba configured with `unv_bible_terms.txt`
**Then**: "耶和華" appears as a single token, not split into "耶", "和", "華"

#### Scenario: Bootstrap Target Dictionary from Source Dictionary

**Given**: `lcc_bible_terms.txt` does not exist yet (initial state)
**When**: Starting LCC tokenization work
**Then**: System can copy `unv_bible_terms.txt` → `lcc_bible_terms.txt` as starting point
**And**: User iteratively refines `lcc_bible_terms.txt` based on tokenization results
**Note**: This is a practical "lazy start" approach - many terms are shared between versions
**Generalizes to**: Any target dictionary can bootstrap from any source dictionary (e.g., `nasb → esv`, `kjv → rcuv2010`)

#### Scenario: Prevent Over-Segmentation of Proper Nouns

**Given**: A tokenizer without custom dictionary splits "尼布甲尼撒" into ["尼", "布", "甲", "尼", "撒"]
**When**: "尼布甲尼撒" is added to version-specific dictionary (e.g., `unv_bible_terms.txt`)
**And**: Tokenizer is reloaded with updated dictionary
**Then**: "尼布甲尼撒" (Nebuchadnezzar) is tokenized as a single unit
**Note**: "尼布甲尼撒" corresponds to one Hebrew word (H5019), so it should not be split

#### Scenario: Same Verse, Different Terms in Different Versions

**Given**: UNV verse uses "天堂" (extracted to `unv_bible_terms.txt`)
**And**: LCC verse uses "天國" (added to `lcc_bible_terms.txt`)
**When**: Tokenizing the same verse reference in both versions
**Then**: UNV tokenization preserves "天堂" as single token
**And**: LCC tokenization preserves "天國" as single token
**Note**: These represent the same concept but with different Chinese terms
**Important**: Alignment (matching these terms) happens AFTER tokenization using semantic similarity

### Requirement 3: Consistent Output Format

All tokenization strategies MUST return results in the same format to ensure interoperability.

**Output Format**:
- Type: `List[str]`
- Each element is a single word/term (string)
- Preserves order from original text
- Includes punctuation as separate tokens (if applicable to strategy)

#### Scenario: Output is Always a List of Strings

**Given**: Any tokenization strategy (jieba, pkuseg, lac, stanza)
**When**: Tokenizing any Chinese text
**Then**: Output is a Python list
**And**: Every element in the list is a string
**And**: List is not empty for non-empty input

#### Scenario: Empty Input Handling

**Given**: Empty string input `""`
**When**: Tokenizing with any strategy
**Then**: Returns empty list `[]`
**And**: Does not raise an exception

#### Scenario: Whitespace Handling

**Given**: Input text with spaces: "起初 上帝 創造天地"
**When**: Tokenizing with any strategy
**Then**: Whitespace is handled consistently (either preserved as tokens or removed)
**And**: Behavior is documented for each strategy

### Requirement 4: Position Information Preservation

The system MUST preserve positional information of tokens within the original verse for alignment algorithms.

**Enhanced Output Option**:
```python
def tokenize_with_positions(sentence: str) -> List[Tuple[str, int]]:
    """
    Tokenize with position information.

    Args:
        sentence: Raw Chinese text string

    Returns:
        List of (token, position) tuples where position is 0-indexed
    """
```

#### Scenario: Tokenize with Position Indices

**Given**: Input text "起初上帝創造天地"
**When**: Calling `tokenize_with_positions(text)`
**Then**: Returns `[("起初", 0), ("上帝", 1), ("創造", 2), ("天地", 3)]`

#### Scenario: Position Information for Alignment

**Given**: Tokenized verse with positions
**When**: Alignment algorithm needs to calculate positional similarity
**Then**: Position indices are available for each token
**And**: Position is 0-indexed and sequential

### Requirement 5: Tokenization Evaluation

The system MUST provide methods to evaluate and compare tokenization quality across different strategies.

**Evaluation Approaches**:
1. **Qualitative**: Manual inspection of sample verses
2. **Quantitative**: Downstream task performance (alignment accuracy)

#### Scenario: Qualitative Evaluation - Manual Inspection

**Given**: A set of 10 representative verses (OT and NT, various lengths)
**When**: Each verse is tokenized using jieba, pkuseg, and lac
**Then**: Results can be displayed side-by-side for comparison
**And**: A human can judge which segmentation is most semantically meaningful

#### Scenario: Quantitative Evaluation - Gold Standard Comparison

**Given**: 20 verses with manually-created "gold standard" tokenization
**When**: Each verse is tokenized using a strategy
**Then**: System calculates precision, recall, F1 against gold standard
**And**: Best strategy = highest F1 score

#### Scenario: Downstream Task Evaluation

**Given**: Gold standard Strong's Number alignments for 20 verses
**When**: Full alignment pipeline is run with different tokenizers
**Then**: Alignment accuracy is measured for each tokenizer
**And**: Best tokenizer = highest alignment accuracy
**Note**: This is the most important evaluation metric

### Requirement 6: Performance Requirements

Tokenization MUST be performant enough to process full Bible books in reasonable time.

**Performance Target**: Process a full Bible book (e.g., Genesis with 50 chapters) in < 1 minute on standard hardware.

#### Scenario: Process Single Verse Quickly

**Given**: A single verse of moderate length (20-30 Chinese characters)
**When**: Tokenizing with any strategy
**Then**: Processing completes in < 100ms

#### Scenario: Batch Process Full Chapter

**Given**: Genesis Chapter 1 (31 verses)
**When**: Tokenizing all verses sequentially
**Then**: Total processing time < 5 seconds

### Requirement 7: Unicode and Special Character Handling

The system MUST correctly handle Chinese characters (Traditional and Simplified), punctuation, and embedded Strong's Number tags.

#### Scenario: Handle Traditional Chinese Characters

**Given**: LCC text using Traditional Chinese: "起初上帝創造天地"
**When**: Tokenizing with any strategy
**Then**: Characters are correctly recognized and segmented
**And**: No encoding errors occur

#### Scenario: Handle Punctuation

**Given**: Text with Chinese punctuation: "上帝說，要有光。"
**When**: Tokenizing
**Then**: Punctuation (，。) is handled (either as separate tokens or attached to words)
**And**: Behavior is consistent and documented

#### Scenario: Handle Existing Strong's Number Tags

**Given**: UNV text with embedded tags: "起初<H7225>上帝<H430>創造<H1254>天<H8064>地<H776>"
**When**: Tokenizing
**Then**: System can optionally preserve or strip Strong's tags
**And**: Tokenization of Chinese text is not disrupted by tags

### Requirement: Plugin System Architecture

The system MUST implement a plugin architecture that allows runtime registration and configuration of all strategy components.

**Plugin Base Interface**:
```python
class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version for compatibility."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict) -> bool:
        """Validate configuration."""
        pass

    @abstractmethod
    def initialize(self, config: Dict) -> None:
        """Initialize with configuration."""
        pass
```

**Supported Plugin Types**:
- `TokenizerPlugin`: Tokenization strategies
- `EmbeddingPlugin`: Word/sentence embeddings
- `AlignmentPlugin`: Alignment algorithms
- `ScorerPlugin`: Scoring and evaluation

#### Scenario: Register and Use Tokenizer Plugin

**Given**: A jieba tokenizer plugin implementation
**When**: Registering with `PluginManager.register("tokenizer.jieba", JiebaPlugin())`
**Then**: Plugin is available for use via `PluginManager.get("tokenizer.jieba")`
**And**: Can be configured with `plugin.initialize({"dict_path": "unv_bible_terms.txt"})`

#### Scenario: Hot-Swap Plugins at Runtime

**Given**: System running with jieba tokenizer
**When**: Calling `PluginManager.replace("tokenizer.main", "tokenizer.pkuseg")`
**Then**: All subsequent tokenization uses pkuseg without restart
**And**: Previous tokenization results remain valid

#### Scenario: Plugin Version Compatibility

**Given**: Plugin interface version 1.0
**When**: Loading a plugin with version 0.9
**Then**: System checks compatibility and warns about version mismatch
**And**: Falls back to compatible plugin if available

### Requirement: Plugin Discovery and Loading

The system MUST support automatic plugin discovery and lazy loading from designated directories.

**Discovery Mechanism**:
```
plugins/
├── tokenizers/
│   ├── jieba_plugin.py
│   ├── pkuseg_plugin.py
│   └── plugin.json      # Metadata
├── embeddings/
│   ├── word2vec_plugin.py
│   └── bert_plugin.py
└── aligners/
    ├── cosine_plugin.py
    └── attention_plugin.py
```

#### Scenario: Automatic Plugin Discovery

**Given**: Plugins directory with multiple plugin implementations
**When**: System starts up
**Then**: All plugins are discovered and registered automatically
**And**: Metadata is loaded from plugin.json files

#### Scenario: Lazy Plugin Loading

**Given**: 10 plugins registered but not initialized
**When**: First request for specific plugin
**Then**: Plugin is loaded and initialized on-demand
**And**: Subsequent requests use cached instance

## Data Formats

### Input Format

**Verse Object**:
```python
{
    "book": "Genesis",      # English book name
    "chapter": 1,           # Integer chapter number
    "verse": 1,             # Integer verse number
    "version": "lcc",       # Bible version code (lcc, unv, etc.)
    "text": "起初上帝創造天地。"  # Raw Chinese text
}
```

### Output Format (Basic)

**Tokenized Verse**:
```python
{
    "book": "Genesis",
    "chapter": 1,
    "verse": 1,
    "version": "lcc",
    "tokens": ["起初", "上帝", "創造", "天地", "。"],
    "tokenizer": "jieba"    # Which strategy was used
}
```

### Output Format (With Positions)

**Tokenized Verse with Positions**:
```python
{
    "book": "Genesis",
    "chapter": 1,
    "verse": 1,
    "version": "lcc",
    "tokens": [
        {"word": "起初", "position": 0},
        {"word": "上帝", "position": 1},
        {"word": "創造", "position": 2},
        {"word": "天地", "position": 3},
        {"word": "。", "position": 4}
    ],
    "tokenizer": "jieba"
}
```

### Custom Dictionary Formats

**Version-Specific Dictionary (e.g., unv_bible_terms.txt)**:
```
# UNV Biblical Terms Dictionary
# Auto-generated from UNV (和合本 with Strong's Numbers)
# One term per line, UTF-8 encoding
# Each term corresponds to a single Strong's Number in UNV
# Lines starting with # are comments

耶和華
尼布甲尼撒
所羅門
以馬內利
人子
創世記
上帝
天堂
哈利路亞
```

**LCC Dictionary (lcc_bible_terms.txt)**:
```
# LCC Biblical Terms Dictionary
# Initially copied from unv_bible_terms.txt, then manually refined
# One term per line, UTF-8 encoding
# Lines starting with # are comments

耶和華
尼布甲尼撒
所羅門
以馬內利
人子
創世記
上帝
天國
哈利路亞
```

**Cross-Version Dictionary (all_bible_terms.json)**:
```json
{
  "unv": {
    "terms": ["耶和華", "尼布甲尼撒", "所羅門", "天堂"],
    "status": "completed",
    "has_strongs": true
  },
  "kjv": {
    "terms": ["LORD", "Nebuchadnezzar", "Solomon", "heaven"],
    "status": "completed",
    "has_strongs": true
  },
  "nasb": {
    "terms": ["LORD", "Nebuchadnezzar", "Solomon", "heaven"],
    "status": "completed",
    "has_strongs": true
  },
  "lcc": {
    "terms": ["耶和華", "尼布甲尼撒", "所羅門", "天國"],
    "status": "in_progress",
    "has_strongs": false
  },
  "rcuv2010": {
    "terms": ["耶和華", "尼布甲尼撒", "所羅門", "天國"],
    "status": "not_started",
    "has_strongs": false
  }
}
```
**Note**: Extensible to any Bible version. Add new versions as needed.

**Generation Method for Source Version Dictionary**:
```python
# Pseudo-code for generating unv_bible_terms.txt
for verse in UNV_bible:
    for (term, strong_number) in extract_annotated_terms(verse):
        add_to_dictionary(term)  # e.g., "耶和華" from "耶和華<H3068>"
```

**Workflow for Target Version Dictionary**:
```python
# Pseudo-code for LCC dictionary evolution
# Step 1: Bootstrap
copy(unv_bible_terms.txt, lcc_bible_terms.txt)

# Step 2: Iterative refinement
while refining:
    tokenize_lcc_with_dictionary(lcc_bible_terms.txt)
    review_tokenization_results()
    if found_lcc_specific_term:
        add_to_dictionary(lcc_bible_terms.txt, term)
    if found_inappropriate_term:
        remove_from_dictionary(lcc_bible_terms.txt, term)
```

## Dependencies

**External Libraries**:
- `jieba` - Chinese word segmentation library
- `pkuseg` - PKU Chinese word segmentation toolkit
- `LAC` (optional) - Baidu's Lexical Analysis of Chinese
- `Stanza` (optional) - Stanford NLP library

**Parent Project Data**:
- Bible text from `../original_text_preparation/bible_text_json/`
- Reference to UNV (for Strong's tags), LCC (target for segmentation)

## Non-Functional Requirements

### Maintainability
- Strategy functions are self-contained and independently testable
- Adding a new tokenizer requires minimal code changes (just add new strategy function)
- Custom dictionary is version-controlled and documented

### Testability
- Each tokenizer strategy can be unit tested independently
- Test data includes edge cases (empty strings, very long verses, special characters)
- Integration tests verify strategy swapping works correctly

### Extensibility
- New tokenization algorithms can be added without modifying existing code
- Custom dictionary can be expanded iteratively based on evaluation
- Future: Support for context-aware tokenization (using surrounding verses)

## Future Considerations

### Context-Aware Tokenization
- Use surrounding verse context to improve segmentation accuracy
- Leverage parallel structure in poetic books (Psalms, Proverbs)

### Domain-Specific Training
- Train custom pkuseg models on biblical Chinese text
- Fine-tune LAC models with biblical corpus

### Interactive Dictionary Building
- Tool to visualize tokenization results
- Allow quick addition of terms to custom dictionary
- Integration with dual_reader_right_editor for visual feedback

## Related Specifications

- **[Future]** `alignment-algorithm` - Uses tokenized output for Strong's Number alignment
- **[Future]** `verse-annotation` - Annotation workflow for manual verification
