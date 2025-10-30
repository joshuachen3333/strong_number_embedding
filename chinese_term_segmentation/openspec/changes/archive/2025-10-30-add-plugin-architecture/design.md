# Design Document: Plugin Architecture

## Change ID: add-plugin-architecture

## Overview

This design implements a flexible plugin architecture based on the V2 architecture document, enabling runtime component swapping, extensibility, and production-ready features like A/B testing and monitoring.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   Application                        │
│          (Tokenization, Alignment, etc.)             │
└───────────────────┬─────────────────────────────────┘
                    │
                    ↓
┌─────────────────────────────────────────────────────┐
│               PluginManager                          │
│  - register(name, plugin)                            │
│  - get(name) → plugin                                │
│  - replace(name, new_plugin)                         │
│  - list_plugins() → List[PluginInfo]                 │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┼───────────┬──────────┐
        ↓           ↓           ↓          ↓
┌─────────────┐ ┌──────────┐ ┌────────┐ ┌─────────┐
│ Tokenizer   │ │Embedding │ │Aligner │ │ Scorer  │
│  Plugins    │ │ Plugins  │ │Plugins │ │ Plugins │
└─────────────┘ └──────────┘ └────────┘ └─────────┘
    │               │            │          │
    ↓               ↓            ↓          ↓
┌────────┐     ┌────────┐   ┌────────┐ ┌────────┐
│ Jieba  │     │Word2Vec│   │Cosine  │ │Accuracy│
│ PKUSeg │     │ BERT   │   │Attn    │ │Confid. │
│ LAC    │     │fastText│   │Graph   │ │F1Score │
│Stanza  │     │ ...    │   │ ...    │ │ ...    │
└────────┘     └────────┘   └────────┘ └────────┘
```

## Core Components

### 1. Plugin Base Class

```python
# src/core/plugin_base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for all plugins in the system."""

    def __init__(self):
        self._config: Optional[Dict[str, Any]] = None
        self._initialized = False
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier (e.g., 'tokenizer.jieba')."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version (semantic versioning: '1.0.0')."""
        pass

    @property
    def plugin_type(self) -> str:
        """Plugin type derived from class hierarchy."""
        return self.__class__.__bases__[0].__name__

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If configuration is invalid
        """
        # Base implementation - override in subclasses
        return True

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize plugin with configuration.

        Args:
            config: Configuration dictionary

        Raises:
            RuntimeError: If initialization fails
        """
        if not self.validate_config(config):
            raise ValueError(f"Invalid configuration for {self.name}")

        self._config = config
        self._initialized = True
        self._logger.info(f"Plugin {self.name} v{self.version} initialized")

    def shutdown(self) -> None:
        """Cleanup plugin resources."""
        self._initialized = False
        self._logger.info(f"Plugin {self.name} shutdown")

    @property
    def is_initialized(self) -> bool:
        """Check if plugin is initialized."""
        return self._initialized
```

### 2. Plugin Type Interfaces

```python
# src/core/plugin_interfaces.py

from abc import abstractmethod
from typing import List, Dict, Optional, Tuple
import numpy as np
from .plugin_base import Plugin


class TokenizerPlugin(Plugin):
    """Interface for tokenization strategies."""

    @abstractmethod
    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        """
        Tokenize text into words/terms.

        Args:
            text: Raw text string
            context: Optional context (verse references, surrounding text)

        Returns:
            List of word tokens
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
            text: Raw text string
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
        if not self.supports_custom_dictionary():
            raise NotImplementedError(
                f"{self.name} does not support custom dictionaries"
            )


class EmbeddingPlugin(Plugin):
    """Interface for word/sentence embedding strategies."""

    @abstractmethod
    def embed(self, text: str, context: Optional[Dict] = None) -> np.ndarray:
        """
        Generate embedding vector for text.

        Args:
            text: Text to embed
            context: Optional context for contextualized embeddings

        Returns:
            Embedding vector as numpy array
        """
        pass

    def batch_embed(self, texts: List[str]) -> np.ndarray:
        """
        Efficiently embed multiple texts.

        Args:
            texts: List of text strings

        Returns:
            2D numpy array of embeddings
        """
        # Default implementation - can be overridden for efficiency
        return np.array([self.embed(text) for text in texts])

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass

    @abstractmethod
    def supports_contextualization(self) -> bool:
        """Whether embeddings are context-aware."""
        pass


class AlignmentPlugin(Plugin):
    """Interface for alignment strategies."""

    @abstractmethod
    def align(
        self,
        source_tokens: List[Dict],
        target_tokens: List[Dict],
        context: Optional[Dict] = None
    ) -> List[Tuple[int, int, float]]:
        """
        Align source and target tokens.

        Args:
            source_tokens: List of source token dicts
            target_tokens: List of target token dicts
            context: Optional context

        Returns:
            List of (source_idx, target_idx, confidence) tuples
        """
        pass

    @abstractmethod
    def supports_many_to_many(self) -> bool:
        """Whether this aligner supports many-to-many alignments."""
        pass

    @abstractmethod
    def confidence_threshold(self) -> float:
        """Minimum confidence for accepting an alignment."""
        pass


class ScorerPlugin(Plugin):
    """Interface for scoring/evaluation strategies."""

    @abstractmethod
    def score(
        self,
        predicted: List[Tuple],
        gold: List[Tuple]
    ) -> Dict[str, float]:
        """
        Score predicted alignments against gold standard.

        Args:
            predicted: List of predicted alignments
            gold: List of gold standard alignments

        Returns:
            Dict with metrics (precision, recall, f1, etc.)
        """
        pass

    def confidence_score(self, alignment: Tuple) -> float:
        """
        Calculate confidence score for single alignment.

        Args:
            alignment: (source_idx, target_idx, score) tuple

        Returns:
            Confidence value between 0.0 and 1.0
        """
        # Default: use alignment score directly
        return alignment[2] if len(alignment) > 2 else 0.0
```

### 3. Plugin Manager (Singleton)

```python
# src/core/plugin_manager.py

from typing import Dict, List, Optional, Type
from threading import Lock
import logging
from .plugin_base import Plugin
from .plugin_interfaces import (
    TokenizerPlugin,
    EmbeddingPlugin,
    AlignmentPlugin,
    ScorerPlugin
)

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Singleton manager for plugin registration and retrieval.
    Thread-safe implementation.
    """

    _instance: Optional['PluginManager'] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._plugins: Dict[str, Plugin] = {}
        self._plugin_types: Dict[str, Type[Plugin]] = {
            'tokenizer': TokenizerPlugin,
            'embedding': EmbeddingPlugin,
            'alignment': AlignmentPlugin,
            'scorer': ScorerPlugin
        }
        self._metrics: Dict[str, Dict] = {}
        self._initialized = True
        logger.info("PluginManager initialized")

    def register(self, name: str, plugin: Plugin) -> None:
        """
        Register a plugin.

        Args:
            name: Unique plugin name (e.g., 'tokenizer.jieba')
            plugin: Plugin instance

        Raises:
            ValueError: If name already registered or plugin invalid
        """
        with self._lock:
            if name in self._plugins:
                raise ValueError(f"Plugin '{name}' already registered")

            # Validate plugin type
            plugin_type = name.split('.')[0]
            if plugin_type not in self._plugin_types:
                raise ValueError(f"Unknown plugin type: {plugin_type}")

            expected_base = self._plugin_types[plugin_type]
            if not isinstance(plugin, expected_base):
                raise ValueError(
                    f"Plugin must be instance of {expected_base.__name__}"
                )

            self._plugins[name] = plugin
            self._metrics[name] = {
                'register_time': None,  # TODO: add timestamp
                'usage_count': 0,
                'total_time': 0.0
            }
            logger.info(f"Registered plugin: {name} (v{plugin.version})")

    def get(self, name: str) -> Plugin:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance

        Raises:
            KeyError: If plugin not found
        """
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' not registered")

        self._metrics[name]['usage_count'] += 1
        return self._plugins[name]

    def replace(self, name: str, new_plugin: Plugin) -> Plugin:
        """
        Replace an existing plugin.

        Args:
            name: Plugin name to replace
            new_plugin: New plugin instance

        Returns:
            Old plugin instance

        Raises:
            KeyError: If plugin not found
        """
        with self._lock:
            old_plugin = self.get(name)

            # Shutdown old plugin
            old_plugin.shutdown()

            # Register new plugin
            self._plugins[name] = new_plugin
            logger.info(f"Replaced plugin: {name}")

            return old_plugin

    def list_plugins(self, plugin_type: Optional[str] = None) -> List[str]:
        """
        List registered plugins.

        Args:
            plugin_type: Optional type filter ('tokenizer', 'embedding', etc.)

        Returns:
            List of plugin names
        """
        if plugin_type is None:
            return list(self._plugins.keys())

        return [
            name for name in self._plugins.keys()
            if name.startswith(f"{plugin_type}.")
        ]

    def get_metrics(self, name: str) -> Dict:
        """Get usage metrics for a plugin."""
        if name not in self._metrics:
            raise KeyError(f"No metrics for plugin '{name}'")
        return self._metrics[name].copy()
```

### 4. Plugin Discovery

```python
# src/core/plugin_discovery.py

import os
import json
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Discovers and loads plugins from filesystem."""

    def __init__(self, plugins_dir: str = "src/plugins"):
        self.plugins_dir = Path(plugins_dir)
        self._discovered: List[Dict] = []

    def discover(self) -> List[Dict]:
        """
        Discover all plugins in plugins directory.

        Returns:
            List of plugin metadata dicts
        """
        self._discovered.clear()

        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return []

        # Scan subdirectories
        for plugin_type_dir in self.plugins_dir.iterdir():
            if not plugin_type_dir.is_dir():
                continue

            plugin_type = plugin_type_dir.name

            # Look for plugin.json
            metadata_file = plugin_type_dir / "plugin.json"
            if not metadata_file.exists():
                logger.debug(f"No plugin.json in {plugin_type_dir}")
                continue

            # Load metadata
            try:
                with open(metadata_file) as f:
                    metadata = json.load(f)

                metadata['plugin_type'] = plugin_type
                metadata['base_dir'] = str(plugin_type_dir)
                self._discovered.append(metadata)

                logger.info(f"Discovered plugins in {plugin_type_dir}")
            except Exception as e:
                logger.error(f"Error loading metadata from {metadata_file}: {e}")

        return self._discovered

    def load_plugin(self, plugin_info: Dict) -> Optional[object]:
        """
        Dynamically load a plugin module.

        Args:
            plugin_info: Plugin metadata dict

        Returns:
            Loaded plugin class or None if failed
        """
        module_path = plugin_info.get('module_path')
        class_name = plugin_info.get('class_name')

        if not module_path or not class_name:
            logger.error(f"Invalid plugin info: {plugin_info}")
            return None

        try:
            # Construct full path
            full_path = Path(plugin_info['base_dir']) / module_path

            # Load module
            spec = importlib.util.spec_from_file_location(
                class_name,
                full_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get class
            plugin_class = getattr(module, class_name)

            logger.info(f"Loaded plugin: {class_name} from {module_path}")
            return plugin_class

        except Exception as e:
            logger.error(f"Error loading plugin {class_name}: {e}")
            return None
```

## Configuration Schema

```yaml
# config/plugins.yaml

plugins:
  tokenizers:
    default: jieba

    jieba:
      enabled: true
      config:
        dict_path: "dictionaries/unv_bible_terms.txt"
        hmm: true

    pkuseg:
      enabled: true
      config:
        model_name: "default"
        dict_path: "dictionaries/lcc_bible_terms.txt"

  embeddings:
    default: word2vec

    word2vec:
      enabled: true
      config:
        model_path: "models/chinese_word2vec.bin"
        dimension: 300

  alignments:
    default: cosine

    cosine:
      enabled: true
      config:
        threshold: 0.5
        weight_semantic: 0.7
        weight_positional: 0.3
```

## Performance Considerations

1. **Lazy Loading**: Plugins loaded only when first accessed
2. **Caching**: PluginManager caches plugin instances
3. **Thread Safety**: Lock-based synchronization for registration
4. **Metrics Collection**: Minimal overhead tracking (<1%)

## Migration Path

### Before (Direct Function Calls)
```python
from tokenizers import tokenize_jieba

tokens = tokenize_jieba("起初上帝創造天地")
```

### After (Plugin-Based)
```python
from core.plugin_manager import PluginManager

pm = PluginManager()
tokenizer = pm.get('tokenizer.jieba')
tokens = tokenizer.tokenize("起初上帝創造天地")
```

### Compatibility Layer (Optional)
```python
# tokenizers/__init__.py
from core.plugin_manager import PluginManager

def tokenize_jieba(text):
    """Backward compatibility wrapper."""
    pm = PluginManager()
    return pm.get('tokenizer.jieba').tokenize(text)
```

## Security Considerations

1. **Plugin Validation**: Metadata checked before loading
2. **Type Checking**: Plugins must implement correct interface
3. **Sandboxing**: Future: Run untrusted plugins in isolated environment
4. **Version Compatibility**: Check plugin version against system version

## Future Enhancements

1. **Remote Plugin Loading**: Download plugins from registry
2. **Plugin Marketplace**: Share and discover community plugins
3. **Auto-Update**: Automatically update plugins with permission
4. **Dependency Management**: Handle plugin dependencies
5. **Plugin Signing**: Verify plugin authenticity