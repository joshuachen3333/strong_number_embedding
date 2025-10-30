# Chinese Term Segmentation

A pluggable framework for segmenting Chinese biblical text and mapping terms to Strong's Numbers using semantic similarity and positional alignment.

## Features

✅ **Plugin Architecture** - Hot-swappable tokenization, embedding, and alignment strategies
✅ **Multiple Tokenizers** - jieba, pkuseg, LAC, Stanza support
✅ **Custom Dictionaries** - Biblical term dictionaries for accurate segmentation
✅ **Configuration Management** - YAML/JSON config with environment variable overrides
✅ **Lazy Loading** - Plugins loaded on-demand for performance
✅ **Comprehensive Testing** - Unit and integration tests with pytest

## Quick Start

### Installation

```bash
# Clone repository
cd chinese_term_segmentation

# Install dependencies
pip install -r requirements.txt

# Install tokenizers (optional - install as needed)
pip install jieba        # For jieba tokenizer
pip install pkuseg       # For PKUSeg tokenizer
```

###Usage

```python
from src.core.plugin_manager import PluginManager
from src.plugins.tokenizers.jieba_plugin import JiebaPlugin

# Initialize plugin manager
pm = PluginManager()

# Register jieba tokenizer
jieba = JiebaPlugin()
pm.register("tokenizer.jieba", jieba)

# Configure and initialize
config = {
    "dict_path": "dictionaries/unv_bible_terms.txt",
    "hmm": True,
    "mode": "accurate"
}
jieba.initialize(config)

# Tokenize Chinese text
text = "起初上帝創造天地"
tokens = jieba.tokenize(text)
print(tokens)  # ['起初', '上帝', '創造', '天地']

# Tokenize with metadata
tokens_meta = jieba.tokenize_with_metadata(text)
for token in tokens_meta:
    print(f"{token['word']} (pos: {token['position']}, POS: {token['pos']})")
```

### Using Plugin Discovery

```python
from src.core.plugin_loader import PluginLoader

# Initialize loader
loader = PluginLoader("src/plugins")

# Discover all available plugins
loader.discover_plugins()

# Load plugin lazily
tokenizer = loader.load("tokenizer.jieba", config={
    "hmm": True,
    "mode": "accurate"
})

# Use tokenizer
tokens = tokenizer.tokenize("起初上帝創造天地")
```

### Configuration

Create a `config.yaml` file:

```yaml
plugins:
  tokenizers:
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
tokenizer_config = config_mgr.get("plugins.tokenizers.jieba.config")
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
│       └── tokenizers/
│           ├── jieba_plugin.py
│           ├── pkuseg_plugin.py
│           └── plugin.json
├── config/                      # Configuration files
│   ├── default.yaml
│   └── testing.yaml
├── tests/                       # Test suite
│   ├── test_plugin_base.py
│   ├── test_plugin_manager.py
│   ├── test_plugin_discovery.py
│   └── test_tokenizer_plugins.py
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

Create a new tokenizer plugin:

```python
from src.core.plugin_interfaces import TokenizerPlugin
from typing import List, Dict, Optional

class MyTokenizerPlugin(TokenizerPlugin):
    @property
    def name(self) -> str:
        return "tokenizer.my_tokenizer"

    @property
    def version(self) -> str:
        return "1.0.0"

    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        # Your tokenization logic here
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
      "class_name": "MyTokenizerPlugin",
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

**Current Version**: 0.1.0
**OpenSpec Proposal**: `add-plugin-architecture` (Implemented)

**Implemented**:
- ✅ Plugin architecture foundation
- ✅ Plugin manager and discovery
- ✅ Jieba and PKUSeg tokenizer plugins
- ✅ Configuration management
- ✅ Comprehensive test suite (T001-T010)

**Pending**:
- ⏳ Embedding plugins
- ⏳ Alignment plugins
- ⏳ Scorer plugins
- ⏳ Full Bible processing pipeline
