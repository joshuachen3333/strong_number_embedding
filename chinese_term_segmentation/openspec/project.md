# Project Context

## Purpose

**Chinese Term Segmentation** for Strong's Number Alignment

This sub-project tackles the word-level alignment challenge between Chinese Bible translations and original Hebrew/Greek texts with Strong's Numbers. Key objectives:

1. **Accurate Term Segmentation**: Segment Chinese biblical text into meaningful terms despite the lack of word boundaries in Chinese
2. **Strong's Number Alignment**: Map segmented Chinese terms to corresponding Strong's Numbers from original texts
3. **Training Data Generation**: Create high-quality datasets for AI/LLM-based Strong's number embedding automation
4. **Annotation Tools**: Provide utilities to assist human translators in manual Strong's number placement and verification

**Problem Statement**: Chinese text has no inherent word boundaries, making it challenging to align individual translated terms with specific Hebrew/Greek words identified by Strong's Numbers. This project aims to solve this alignment problem through NLP techniques and potentially AI/LLM models.

## Tech Stack

**Python-based Stack** (for NLP and alignment algorithms):

**Core Libraries**:
- Python 3.x
- NumPy / pandas (data manipulation)
- scikit-learn (cosine similarity, ML utilities)
- pytest (testing framework)

**Chinese Segmentation Libraries** (swappable strategies):
- **jieba** (結巴分詞) - Fast, supports custom dictionaries, most popular
- **pkuseg** (北大分詞) - Higher accuracy, domain-specific training
- **LAC** (Baidu) - Deep learning based (Bi-GRU-CRF), includes POS tagging
- **Stanza** (Stanford NLP) - Academic-grade, multi-language support

**Word Embeddings / Semantic Vectors**:
- Pre-trained Chinese word vectors (Word2Vec, GloVe, or fastText)
- Potentially: transformers library for contextualized embeddings (BERT-based)

**Data Format**:
- JSON for input/output (compatibility with parent project)
- Custom dictionary files for biblical term segmentation

**Future Integration**:
- JavaScript/TypeScript for web-based annotation UI (if needed)
- Integration with parent project's dual_reader_right_editor for visual annotation

## Project Conventions

### Code Style

**To Be Defined** - Suggestions based on common practices:

**If Python**:
- PEP 8 style guide
- Type hints for function signatures
- Docstrings for all public functions/classes
- Black for code formatting
- Maximum line length: 88 characters

**If JavaScript/TypeScript**:
- ESLint with recommended rules
- Prettier for formatting
- camelCase for variables/functions, PascalCase for classes
- JSDoc comments for documentation

**Naming Conventions**:
- Files: kebab-case (e.g., `chinese-segmenter.py`, `strongs-mapper.js`)
- Functions: verb-led descriptive names (e.g., `segmentChineseText`, `mapToStrongsNumber`)
- Variables: descriptive, avoid abbreviations except for domain terms (SN for Strong's Number is acceptable)

### Architecture Patterns

**Strategy Pattern for Swappable Components**:

This project uses the Strategy Pattern to allow flexible experimentation with different algorithms. The core alignment algorithm accepts strategy functions as parameters, making it easy to test different approaches.

**Three Types of Swappable Strategies**:

1. **Segmentation Strategies** (`tokenizer`):
   - Input: Raw sentence string
   - Output: List of word tokens
   - Examples: `tokenize_jieba`, `tokenize_pkuseg`, `tokenize_lac`, `tokenize_stanza`
   - Supports custom dictionaries for biblical terms

2. **Semantic Similarity Strategies** (`semantic_strategy`):
   - Input: Two word embedding vectors
   - Output: Similarity score (0.0 to 1.0)
   - Options:
     - `strategy_cosine` - Cosine similarity (recommended, direction-based)
     - `strategy_euclidean` - Euclidean distance (magnitude-sensitive)
     - `strategy_dot_product` - Dot product (length-sensitive, rarely used)

3. **Positional Similarity Strategies** (`positional_strategy`):
   - Input: Two positions, sentence lengths
   - Output: Similarity score (0.0 to 1.0)
   - Options:
     - `strategy_pos_linear` - Normalized linear distance: `1 - abs(p1-p2)/length`
     - `strategy_pos_gaussian` - Gaussian decay: `exp(-((p1-p2)^2)/(2*sigma^2))`
     - `strategy_pos_window` - Fixed window: 1.0 if within window, 0.0 otherwise
     - `strategy_pos_none` - No penalty: always 1.0 (baseline for testing)

**Core Algorithm Framework** (`AlignVerse`):

**Goal**: Auto-generate Strong's Numbers (SN) for target translation (e.g., LCC) using reference translation (e.g., UNV) and original texts (BHS/FHLWH).

**Version Abbreviations**:
- `unv` - 和合本 (Union Version, reference with SN annotations)
- `lcc` - 呂振中譯本 (Lu Cheng-chung Version, target for annotation)
- `bhs` - 馬索拉譯本 (Biblia Hebraica Stuttgartensia, Hebrew OT)
- `fhlwh` - 新約希臘文原文 (Greek NT, likely FHLWH from parent project)

**Algorithm Flow** (per verse):
```
1. Segmentation:
   TGT_words = tokenizer(lcc_verse)  # Swappable tokenizer

2. Extract Source Words:
   SRC_words = extract_words_with_sn(unv_verse)  # (word, sn) pairs

3. Alignment Loop:
   For each (src_word, sn) in SRC_words:
     a. Get ORIG word from BHS/FHLWH using sn
     b. Get embedding vectors: V_orig, V_tgt
     c. For each unmatched tgt_word in TGT_words:
        - semantic_sim = semantic_strategy(V_orig, V_tgt)
        - positional_sim = positional_strategy(src_pos, tgt_pos, len_src, len_tgt)
        - final_score = (semantic_weight * semantic_sim) + ((1-semantic_weight) * positional_sim)
     d. Select best matching tgt_word (highest final_score)
     e. Assign sn to tgt_word, mark as matched

4. Output: List of (lcc_word, sn) pairs
```

**Modular Design**:
- Separate concerns: segmentation, embedding, similarity calculation, alignment logic
- Clear function interfaces with type hints
- Stateless strategy functions for easy testing and composition

**Integration Points**:
- Read data from `../original_text_preparation/bible_text_json/`
- Read Strong's dictionaries from `../original_text_preparation/strong_dict_json/`
- Optional: Query FHL API for live data
- Output formats compatible with dual reader applications

**Design Principles**:
- Strategy Pattern for algorithm flexibility
- Functional programming for data transformations
- Immutable data structures preferred
- Configuration over hardcoding (use config files for versions, parameters, weights)

### Testing Strategy

**Unit Tests** (pytest framework):
- Test individual segmentation strategies with known inputs
- Test semantic similarity strategies (cosine, euclidean) with test vectors
- Test positional similarity strategies with boundary cases
- Test Strong's number parsing and extraction from UNV
- Test data transformation utilities
- Minimum 80% code coverage goal

**Integration Tests**:
- Test end-to-end `AlignVerse` pipeline with sample verses
- Test data loading from parent project sources (JSON, dictionaries)
- Test output format compatibility with dual reader applications
- Test strategy swapping (ensure changing strategies doesn't break the pipeline)

**Test Data**:
- **Sample verses** from different Bible books (Genesis, Psalms, Matthew, Romans)
- **Edge cases**: short verses (1-2 words), long verses (30+ words), verses with punctuation
- **Coverage**: OT (Hebrew/H-numbers) and NT (Greek/G-numbers)
- **Gold standard**: 10-20 manually annotated verses for evaluation

**Segmentation Evaluation**:

1. **Qualitative (Manual Inspection)**:
   - Sample representative verses (different styles, lengths, OT/NT)
   - Compare segmentation results across strategies (jieba, pkuseg, LAC)
   - Identify which tokenizer produces most semantically meaningful units

2. **Quantitative (Downstream Task Performance)**:
   - **Gold Standard**: Manually create perfect alignment for 10-20 verses
   - Run full alignment pipeline with different segmenters
   - Measure alignment accuracy (precision, recall, F1) against gold standard
   - **Best tokenizer** = highest downstream task accuracy

**Custom Dictionary Management**:
- `bible_terms.txt` - Biblical terms to prevent incorrect segmentation
  - Examples: 耶和華, 尼布甲尼撒, 人子, 以馬內利, 哈利路亞
  - Include common theological phrases if needed
- Iterative refinement: sample check → add terms → re-run → repeat
- Version control custom dictionary to track improvements

**Experiment Tracking**:
- Record configurations: tokenizer, semantic_strategy, positional_strategy, weights
- Log evaluation metrics for each configuration
- Document which combinations work best for different Bible book types

### Git Workflow

**Follows Parent Project Conventions**:

**Branching**:
- `main` branch - production-ready code
- Feature branches: `feature/description` or `add-description`
- Bug fixes: `fix/description`

**Commit Messages**:
- Format: `Type: Brief description`
- Types: `Feat`, `Fix`, `Docs`, `Refactor`, `Test`, `Chore`
- Examples:
  - `Feat: Add jieba-based Chinese segmentation`
  - `Fix: Correct Strong's number regex pattern`
  - `Docs: Update project.md with tech stack decisions`
- Include `🤖 Generated with [Claude Code](https://claude.com/claude-code)` footer when using AI assistance
- Co-authored-by: `Claude <noreply@anthropic.com>` when AI-assisted

**Pull Requests**:
- Reference OpenSpec change proposals in PR description
- Ensure all tasks in `tasks.md` are completed
- Run tests and validation before submitting

## Domain Context

### Chinese Biblical Text Characteristics

**Language Challenges**:
- **No Word Boundaries**: Chinese text is continuous; segmentation is interpretation-dependent
- **Character vs. Word**: Single character can be a word or part of a word
- **Context Sensitivity**: Proper segmentation requires understanding biblical/theological context
- **Multiple Translations**: Different Chinese Bible versions use different vocabulary and styles

**Strong's Number System**:
- **Hebrew (OT)**: H1 - H8674 (original words from Masoretic Text)
- **Greek (NT)**: G1 - G5624 (original words from Greek New Testament)
- **Format Variants**: `<WH1234>`, `<WG5678>`, `{H1234}`, `{G5678}`, `(H1234)`, `(G5678)`
- **One-to-Many Mapping**: One original word (Strong's number) may map to multiple Chinese terms depending on context
- **Many-to-One Mapping**: Multiple Chinese terms may map to same Strong's number

**Bible Versions with Strong's Numbers** (from parent project):
- **UNV (和合本)**: Chinese Union Version - has Strong's numbers embedded
- **KJV**: King James Version - has Strong's numbers embedded

**Bible Versions without Strong's Numbers** (target for annotation):
- **LCC (呂振中譯本)**: Lü Zhènzhōng Translation
- **RCUV2010 (和合本2010)**: Revised Chinese Union Version 2010
- **ESV**: English Standard Version

**Biblical Structure**:
- 66 books (39 OT, 27 NT)
- Book → Chapter → Verse hierarchy
- Verse is atomic unit for alignment

### Segmentation Considerations

**Theological Terms**: Many biblical terms are specialized (e.g., 上帝 "God", 耶和華 "Jehovah/Yahweh", 彌賽亞 "Messiah")

**Proper Names**: Biblical names need special handling (people, places, nations)

**Numerical Expressions**: Age, measurements, quantities in biblical text

**Poetic Structure**: Psalms, Proverbs have parallel structures that may inform segmentation

## Important Constraints

### Data Authorization
- **Source Data**: All bible.fhl.net data usage is authorized for this project
- **Attribution**: Must acknowledge FHL (Faith, Hope, Love ministry) as data source
- **Usage**: Educational and biblical study purposes

### Accuracy Requirements
- **Alignment Accuracy**: High precision required for theological correctness
- **Human Verification**: AI-generated alignments should be human-reviewable
- **Reversibility**: Changes to annotations must be undoable
- **Audit Trail**: Track who/what made alignment decisions (human vs. AI)

### Technical Constraints
- **Data Format Compatibility**: Must work with existing JSON formats from parent project
- **Performance**: Segmentation should process full Bible books in reasonable time (< 1 minute per book)
- **Memory**: Handle full Bible text in memory (not massive, but consider efficiency)
- **Unicode**: Proper handling of Chinese characters, Hebrew/Greek text, punctuation

### Integration Constraints
- **File Paths**: Relative paths to parent project data sources must remain stable
- **API Compatibility**: If integrating with dual readers, must match their data structure expectations
- **Version Control**: Code must work across different Bible versions with minimal changes

## External Dependencies

### Parent Project Data Sources

**Bible Text JSON** (`../original_text_preparation/bible_text_json/`):
- Structured Bible text in JSON format
- Multiple versions available
- Contains embedded Strong's numbers for UNV and KJV

**Strong's Dictionaries** (`../original_text_preparation/strong_dict_json/`):
- Hebrew Strong's dictionary (H-numbers with definitions)
- Greek Strong's dictionary (G-numbers with definitions)
- JSON format with word, transliteration, definition fields

### External APIs

**FHL Bible API** (`https://bible.fhl.net/json/qb.php`):
- Parameters: `version`, `chineses` (Chinese book abbreviation), `chap`, `strong` (0/1)
- Response: JSON with verse records
- Used for: Live data fetching, verification against source

**FHL Bible Version List** (`https://bible.fhl.net/json/abv.php`):
- Lists all available Bible versions
- Helper scripts: `../original_text_preparation/list_all_bible_versions`

### External Libraries (To Be Determined)

**Chinese NLP Libraries** (if using Python):
- jieba - Popular Chinese word segmentation
- pkuseg - More accurate for specific domains
- LAC (Lexical Analysis of Chinese) - Baidu's NLP toolkit
- HanLP - Multi-functional NLP library

**ML/AI Libraries** (if using models):
- transformers - Hugging Face library for LLMs
- openai / anthropic - For Claude/GPT API integration if using external LLMs
- scikit-learn - For traditional ML approaches

### Development Tools

**OpenSpec**: Spec-driven development framework (already initialized)
- Manages change proposals and specifications
- CLI tool for validation and lifecycle management

**Version Control**: Git (already in use by parent project)

---

## Next Steps

**Phase 1: Foundation Setup**
1. ✅ **Tech Stack Decided**: Python-based with swappable NLP strategies
2. **Setup Development Environment**:
   - Create virtual environment
   - Install dependencies: numpy, pandas, scikit-learn, pytest
   - Install segmenters: jieba, pkuseg (LAC/Stanza later)
3. **Create Custom Dictionary**: `bible_terms.txt` with essential biblical terms

**Phase 2: Core Implementation (OpenSpec-driven)**
4. **Create OpenSpec Specification**: Define `alignment-algorithm` capability
   - Document AlignVerse function interface
   - Specify strategy interfaces (tokenizer, semantic_strategy, positional_strategy)
   - Define input/output data formats
5. **Implement Strategy Functions**:
   - Segmentation strategies: jieba, pkuseg with custom dictionary support
   - Semantic strategies: cosine, euclidean
   - Positional strategies: linear, gaussian, window, none
6. **Implement Core Algorithm**: `AlignVerse` function accepting swappable strategies

**Phase 3: Data Integration**
7. **Data Loading Utilities**:
   - Load UNV verses with Strong's numbers from `../original_text_preparation/`
   - Load LCC verses (target for annotation)
   - Load BHS/FHLWH original texts
   - Parse Strong's number formats from UNV
8. **Word Embeddings**:
   - Source or train Chinese word vectors
   - Create embedding lookup utilities

**Phase 4: Evaluation & Optimization**
9. **Create Gold Standard**: Manually annotate 10-20 representative verses
10. **Run Experiments**: Test different strategy combinations
    - Compare segmenters (jieba vs pkuseg vs LAC)
    - Compare similarity strategies
    - Tune semantic_weight parameter
11. **Document Results**: Track which configurations work best for different contexts

**Phase 5: Production Pipeline**
12. **Batch Processing**: Process full books/Bible
13. **Output Integration**: Export results compatible with dual_reader applications
14. **Quality Assurance**: Human review workflow for AI-generated alignments
