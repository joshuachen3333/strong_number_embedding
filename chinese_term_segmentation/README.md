# Chinese Term Segmentation

A pluggable framework for segmenting Chinese biblical text and mapping terms to Strong's Numbers using semantic similarity and positional alignment.

## Features

✅ **Plugin Architecture** - Hot-swappable segmentation, embedding, and alignment strategies
✅ **Multiple Segmenters** - jieba, pkuseg, LAC, Stanza support
✅ **Custom Dictionaries** - Biblical term dictionaries for accurate segmentation
✅ **Strong's Number Integration** - Automatic boundary correction using UNV+Strong's Numbers
✅ **Similarity-Based Refinement** - Extract precise terms using semantic similarity (Phase 1.5)
✅ **Pluggable Semantic Engines** - Swappable similarity algorithms (Phase 2.1)
✅ **Configuration Management** - YAML/JSON config with environment variable overrides
✅ **Lazy Loading** - Plugins loaded on-demand for performance
✅ **Comprehensive Testing** - 68+ tests including unit and integration tests

## Quick Start

### Installation

```bash
# Clone repository
cd chinese_term_segmentation

# Install dependencies
pip install -r requirements.txt

# Install segmenters (optional - install as needed)
pip install jieba        # For jieba segmenter (結巴分詞)
pip install pkuseg       # For PKUSeg segmenter (北大分詞)
pip install LAC          # For Baidu LAC segmenter
pip install stanza       # For Stanford NLP Stanza
# For Stanza, also download Chinese model:
python -c "import stanza; stanza.download('zh')"
```

### CLI Usage

Fetch Bible verses with segmentation:

```bash
# Fetch a single verse
python segment.py --verse "Gen 1:3" --version unv

# Fetch with Chinese segmentation
python segment.py --verse "創 1:1" --version unv --seg jieba

# Compare multiple segmenters side-by-side
python segment.py --verse "約 3:16" --version unv --seg jieba pkuseg lac stanza

# Use FHL API parameters directly
python segment.py --chineses 太 --chap 5 --sec 1-5 --version unv --seg jieba

# English book names
python segment.py --engs Matt --chap 5 --sec 1 --version kjv --seg jieba pkuseg

# Strong's Number correction and refinement (Phase 1.5 + 2.1)
python segment.py --engs gen --chap 3 --sec 3 --version lcc \
  --seg pkuseg --correct-with-sn --use-refinement

# With explicit semantic engine selection (Phase 2.1)
python segment.py --engs john --chap 3 --sec 16 --version lcc \
  --seg pkuseg --correct-with-sn --use-refinement \
  --semantic-engine edit-distance
```

### Strong's Number Alignment (Phase 1.5 + 2.1)

Automatically correct segmentation boundaries using UNV with Strong's Numbers as reference:

```bash
# Basic SN correction (without refinement)
./segment.py --engs gen --chap 1 --sec 1 --version lcc \
  --seg pkuseg --correct-with-sn

# With similarity-based refinement (Phase 1.5)
./segment.py --engs gen --chap 3 --sec 3 --version lcc \
  --seg pkuseg --correct-with-sn --use-refinement

# With explicit semantic engine (Phase 2.1)
./segment.py --engs gen --chap 3 --sec 3 --version lcc \
  --seg pkuseg --correct-with-sn --use-refinement \
  --semantic-engine edit-distance
```

**How it works**:
1. **UNV+SN Reference**: Fetches UNV (和合本) with embedded Strong's Numbers
2. **Boundary Correction**: Matches UNV boundaries to target text (LCC)
3. **Similarity Refinement**: Refines coarse boundaries using Strong's Dictionary + semantic matching
4. **Text Preservation**: Target text is never changed, only boundaries are corrected

**Example Output**:
```
📊 Correction Metrics:
   Match rate: 61.5% (8/13 terms)
   Refinement: 4/10 terms refined (40.0%)
   Boundaries corrected: 12
   Segments: 29 → 24
   ✅ Text preserved (target version unchanged)
```

**Semantic Engines** (Phase 2.1):
- `edit-distance` (default): Character-based similarity using Levenshtein distance
- Future: `sentence-transformer` - Neural semantic embeddings
- Future: `bert` - BERT-based Chinese semantic similarity

```bash
# See available engines
./segment.py --help | grep semantic-engine
```

### Programmatic Usage

```python
from src.core.plugin_manager import PluginManager
from src.plugins.segmenters.jieba_plugin import JiebaPlugin

# Initialize plugin manager
pm = PluginManager()

# Register jieba segmenter
jieba = JiebaPlugin()
pm.register("segmenter.jieba", jieba)

# Configure and initialize
config = {
    "dict_path": "dictionaries/unv_bible_terms.txt",
    "hmm": True,
    "mode": "accurate"
}
jieba.initialize(config)

# Segment Chinese text
text = "起初上帝創造天地"
segments = jieba.segment(text)
print(segments)  # ['起初', '上帝', '創造', '天地']

# Segment with metadata
segments_meta = jieba.segment_with_metadata(text)
for seg in segments_meta:
    print(f"{seg['word']} (pos: {seg['position']}, POS: {seg['pos']})")
```

### Using Plugin Discovery

```python
from src.core.plugin_loader import PluginLoader

# Initialize loader
loader = PluginLoader("src/plugins")

# Discover all available plugins
loader.discover_plugins()

# Load plugin lazily
segmenter = loader.load("segmenter.jieba", config={
    "hmm": True,
    "mode": "accurate"
})

# Use segmenter
segments = segmenter.segment("起初上帝創造天地")
```

### Configuration

Create a `config.yaml` file:

```yaml
plugins:
  segmenters:
    default: jieba
    jieba:
      enabled: true
      config:
        dict_path: dictionaries/unv_bible_terms.txt
        hmm: true
        mode: accurate
```

Load configuration:

```python
from src.core.config_manager import ConfigManager

config_mgr = ConfigManager()
config = config_mgr.load("config/default.yaml")

# Get specific values
segmenter_config = config_mgr.get("plugins.segmenters.jieba.config")
```

## Available Segmenters

### 1. Jieba (結巴分詞)
- **Speed**: ⚡⚡⚡ Fast
- **Accuracy**: ⭐⭐⭐ Good
- **Custom Dict**: ✅ Yes
- **Install**: `pip install jieba`
- **Best for**: General-purpose Chinese segmentation, fast prototyping

### 2. PKUSeg (北大分詞)
- **Speed**: ⚡⚡ Moderate
- **Accuracy**: ⭐⭐⭐⭐ High
- **Custom Dict**: ✅ Yes (via user dictionary)
- **Install**: `pip install pkuseg`
- **Best for**: Domain-specific text (news, medicine, tourism, mixed)

### 3. LAC (Baidu Lexical Analysis)
- **Speed**: ⚡ Slower (neural model)
- **Accuracy**: ⭐⭐⭐⭐ High
- **Custom Dict**: ✅ Yes
- **Install**: `pip install LAC`
- **Best for**: Deep learning approach with POS tagging

### 4. Stanza (Stanford NLP)
- **Speed**: ⚡ Slower (neural model)
- **Accuracy**: ⭐⭐⭐⭐⭐ Very High
- **Custom Dict**: ❌ No (uses pre-trained models)
- **Install**: `pip install stanza` + model download
- **Best for**: Academic-grade accuracy, research applications

**Comparison**:
```bash
python segment.py --verse "約 3:16" --version unv --seg jieba pkuseg lac stanza
```

## Project Structure

```
chinese_term_segmentation/
├── src/
│   ├── core/                    # Core plugin infrastructure
│   │   ├── plugin_base.py       # Base plugin class
│   │   ├── plugin_interfaces.py # Plugin type interfaces
│   │   ├── plugin_manager.py    # Plugin manager singleton
│   │   ├── plugin_discovery.py  # Plugin discovery system
│   │   ├── plugin_loader.py     # Lazy loading loader
│   │   └── config_manager.py    # Configuration management
│   └── plugins/                 # Plugin implementations
│       └── segmenters/          # Chinese word segmenters
│           ├── jieba_plugin.py
│           ├── pkuseg_plugin.py
│           ├── lac_plugin.py
│           ├── stanza_plugin.py
│           └── plugin.json
├── src/api/                     # FHL Bible API client
│   ├── fhl_client.py
│   ├── verse_parser.py
│   └── book_mappings.py
├── config/                      # Configuration files
│   ├── default.yaml
│   └── testing.yaml
├── tests/                       # Test suite
│   ├── test_plugin_base.py
│   ├── test_plugin_manager.py
│   ├── test_plugin_discovery.py
│   └── test_segmenter_plugins.py
├── segment.py                   # CLI tool for verse fetching and segmentation
├── openspec/                    # OpenSpec specifications
└── requirements.txt
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/test_plugin_manager.py -v
```

## Plugin Development

Create a new segmenter plugin:

```python
from src.core.plugin_interfaces import SegmenterPlugin
from typing import List, Dict, Optional

class MySegmenterPlugin(SegmenterPlugin):
    @property
    def name(self) -> str:
        return "tokenizer.my_tokenizer"

    @property
    def version(self) -> str:
        return "1.0.0"

    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        # Your segmentation logic here
        return text.split()

    def tokenize_with_metadata(self, text: str, context: Optional[Dict] = None) -> List[Dict]:
        tokens = self.tokenize(text)
        return [{"word": t, "position": i} for i, t in enumerate(tokens)]

    def supports_custom_dictionary(self) -> bool:
        return False
```

Register in `plugin.json`:

```json
{
  "plugins": [
    {
      "name": "tokenizer.my_tokenizer",
      "module_path": "my_tokenizer_plugin.py",
      "class_name": "MySegmenterPlugin",
      "description": "My custom tokenizer"
    }
  ]
}
```

## Documentation

- **OpenSpec**: `openspec/specs/chinese-term-segmentation/spec.md` - Full specification
- **Architecture**: `SEGMENTATION_MAPPING_ARCHITECTURE_V2.md` - Design document
- **Testing Plan**: `CUMULATIVE_TEST_PLAN.md` - Test strategy

## License

See parent project LICENSE file.

## Contributing

This project uses OpenSpec for spec-driven development. Before making changes:

1. Review `openspec/specs/chinese-term-segmentation/spec.md`
2. Create change proposal in `openspec/changes/`
3. Get approval before implementation
4. Follow cumulative testing strategy

## Status

**Current Version**: 0.2.1
**Latest OpenSpec**: `add-semantic-similarity-engines` (Phase 2.1 - Implemented ✅)

### Implemented Features

**Phase 1: Plugin Architecture** ✅
- ✅ Plugin architecture foundation
- ✅ Plugin manager and discovery
- ✅ Jieba, PKUSeg, LAC, Stanza segmenter plugins
- ✅ Configuration management
- ✅ Test suite (T001-T010)

**Phase 1.5: Similarity-Based Refinement** ✅
- ✅ Strong's Number boundary correction (--correct-with-sn)
- ✅ Strong's Dictionary integration with FHL API
- ✅ Similarity-based term refinement (--use-refinement)
- ✅ Character variant normalization (爲→為)
- ✅ 61.5% match rate on Genesis 3:3 (baseline)
- ✅ Test suite (T029-T033)

**Phase 2.1: Pluggable Semantic Engines** ✅
- ✅ SemanticEngine abstract interface
- ✅ EditDistanceEngine (baseline implementation)
- ✅ Refactored SimilarityMatcher for dependency injection
- ✅ CLI flag: --semantic-engine {edit-distance}
- ✅ 100% backward compatibility maintained
- ✅ Integration test suite (T034-T041)
- ✅ 68+ tests passing
- ✅ Performance: 1.33s average (excellent)

### Upcoming Features

**Phase 2.2: Neural Semantic Engines** 🚧
- ⏳ SentenceTransformerEngine (Chinese embeddings)
- ⏳ ChineseBertEngine (BERT-based similarity)
- ⏳ Biblical knowledge base enhancement
- ⏳ Target: 75-85% match rate

**Phase 2.3: Performance Optimization** 🔜
- ⏳ Three-tier caching system
- ⏳ Batch processing for neural engines
- ⏳ Embedding plugins
- ⏳ Alignment plugins

### Test Results

**Unit Tests**: 63/80 passing (18 pre-existing failures in plugins/API)
**Integration Tests**: 5/5 passing (T037-T041)
**Total Coverage**: 68+ tests

**Benchmark** (Genesis 3:3):
- Match rate: 61.5% ✅
- Refinement rate: 40% ✅
- Performance: 1.33s avg ✅
- Text preservation: 100% ✅
