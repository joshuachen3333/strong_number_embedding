# Chinese Term Segmentation - Plugin Architecture Changes

## ADDED Requirements

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
- `SegmenterPlugin`: Segmentation strategies
- `EmbeddingPlugin`: Word/sentence embeddings
- `AlignmentPlugin`: Alignment algorithms
- `ScorerPlugin`: Scoring and evaluation

#### Scenario: Register and Use Tokenizer Plugin

**Given**: A jieba segmenter plugin implementation
**When**: Registering with `PluginManager.register("tokenizer.jieba", JiebaPlugin())`
**Then**: Plugin is available for use via `PluginManager.get("tokenizer.jieba")`
**And**: Can be configured with `plugin.initialize({"dict_path": "unv_bible_terms.txt"})`

#### Scenario: Hot-Swap Plugins at Runtime

**Given**: System running with jieba tokenizer
**When**: Calling `PluginManager.replace("tokenizer.main", "tokenizer.pkuseg")`
**Then**: All subsequent segmentation uses pkuseg without restart
**And**: Previous segmentation results remain valid

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
├── segmenters/
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

## MODIFIED Requirements

### Requirement 1: Swappable Segmentation Strategies

The system MUST support multiple segmentation algorithms that can be easily swapped without modifying the core code.

**CHANGE**: All segmentation strategies must now implement `SegmenterPlugin` interface.

**Interface** (Updated):
```python
class SegmenterPlugin(Plugin):
    @abstractmethod
    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """
        Tokenize a Chinese sentence into words/terms.

        Args:
            text: Raw Chinese text string
            context: Optional context (verse references, surrounding text)

        Returns:
            List of word tokens (strings)
        """
        pass

    @abstractmethod
    def tokenize_with_metadata(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Tokenize with rich metadata.

        Args:
            text: Raw Chinese text string
            context: Optional context

        Returns:
            List of dicts with keys: 'word', 'position', 'pos', 'confidence'
        """
        pass

    @abstractmethod
    def supports_custom_dictionary(self) -> bool:
        """Whether this tokenizer supports custom dictionaries."""
        pass

    def load_dictionary(self, dict_path: str) -> None:
        """Load custom dictionary (optional)."""
        pass
```

**Supported Strategies** (now as plugins):
- `JiebaPlugin` - Using jieba (結巴分詞) library
- `PKUSegPlugin` - Using pkuseg (北大分詞) library
- `LACPlugin` - Using LAC (Baidu) library
- `StanzaPlugin` - Using Stanza (Stanford NLP) library

#### Scenario: Tokenize Genesis 1:1 with Jieba Plugin

**Given**: The LCC verse text "起初上帝創造天地。"
**And**: JiebaPlugin is registered in PluginManager
**When**: Getting plugin via `pm.get("tokenizer.jieba")` and calling `plugin.tokenize("起初上帝創造天地。")`
**Then**: Returns a list like `["起初", "上帝", "創造", "天", "地", "。"]`
**Note**: "天" (H8064) and "地" (H776) are separate terms with different Strong's Numbers

#### Scenario: Strategy is Passable as Plugin Instance

**Given**: A main processing function `process_verse(text, tokenizer_plugin)`
**When**: Calling `process_verse(verse_text, pm.get("tokenizer.jieba"))`
**Then**: The jieba segmenter plugin is used for segmentation
**When**: Calling `process_verse(verse_text, pm.get("tokenizer.pkuseg"))`
**Then**: The pkuseg segmenter plugin is used instead without code changes
