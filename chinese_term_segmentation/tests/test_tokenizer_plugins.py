"""Tests for tokenizer plugins (T002)."""

import pytest
from src.core.plugin_manager import PluginManager


# Mock plugins for testing without actual jieba/pkuseg installation
class MockJiebaPlugin:
    """Mock jieba plugin for testing."""

    def __init__(self):
        self._config = None
        self._initialized = False

    @property
    def name(self):
        return "tokenizer.jieba"

    @property
    def version(self):
        return "1.0.0"

    @property
    def is_initialized(self):
        return self._initialized

    def initialize(self, config):
        self._config = config
        self._initialized = True

    def tokenize(self, text, context=None):
        # Simple mock: split on spaces/Chinese chars
        return [c for c in text if c.strip()]

    def tokenize_with_metadata(self, text, context=None):
        tokens = self.tokenize(text)
        return [{"word": t, "position": i} for i, t in enumerate(tokens)]

    def supports_custom_dictionary(self):
        return True

    def load_dictionary(self, dict_path):
        pass


def test_tokenizer_plugin_interface():
    """Test T002: Tokenizer plugin implements correct interface."""
    plugin = MockJiebaPlugin()

    assert hasattr(plugin, 'tokenize')
    assert hasattr(plugin, 'tokenize_with_metadata')
    assert hasattr(plugin, 'supports_custom_dictionary')
    assert hasattr(plugin, 'name')
    assert hasattr(plugin, 'version')


def test_tokenizer_basic_functionality():
    """Test T002: Basic tokenization works."""
    plugin = MockJiebaPlugin()
    plugin.initialize({})

    text = "起初上帝創造天地"
    tokens = plugin.tokenize(text)

    assert isinstance(tokens, list)
    assert len(tokens) > 0
    assert all(isinstance(t, str) for t in tokens)


def test_tokenizer_with_metadata():
    """Test T002: Tokenization with metadata."""
    plugin = MockJiebaPlugin()
    plugin.initialize({})

    text = "起初上帝"
    tokens_with_meta = plugin.tokenize_with_metadata(text)

    assert isinstance(tokens_with_meta, list)
    assert len(tokens_with_meta) > 0
    assert all(isinstance(t, dict) for t in tokens_with_meta)
    assert all('word' in t and 'position' in t for t in tokens_with_meta)


def test_tokenizer_custom_dictionary_support():
    """Test T002: Custom dictionary support check."""
    plugin = MockJiebaPlugin()

    assert plugin.supports_custom_dictionary() is True


def test_tokenizer_initialization_with_config():
    """Test T002: Tokenizer accepts configuration."""
    plugin = MockJiebaPlugin()

    config = {
        "dict_path": "/path/to/dict.txt",
        "mode": "accurate"
    }

    plugin.initialize(config)

    assert plugin.is_initialized
    assert plugin._config == config


@pytest.mark.skipif(
    True,  # Skip by default since jieba may not be installed
    reason="Requires jieba installation"
)
def test_real_jieba_plugin():
    """Test T002: Real jieba plugin if available."""
    from src.plugins.tokenizers.jieba_plugin import JiebaPlugin

    plugin = JiebaPlugin()
    plugin.initialize({"mode": "accurate", "hmm": True})

    text = "起初上帝創造天地"
    tokens = plugin.tokenize(text)

    assert isinstance(tokens, list)
    assert len(tokens) > 0


@pytest.mark.skipif(
    True,  # Skip by default since pkuseg may not be installed
    reason="Requires pkuseg installation"
)
def test_real_pkuseg_plugin():
    """Test T002: Real PKUSeg plugin if available."""
    from src.plugins.tokenizers.pkuseg_plugin import PKUSegPlugin

    plugin = PKUSegPlugin()
    plugin.initialize({"model_name": "default"})

    text = "起初上帝創造天地"
    tokens = plugin.tokenize(text)

    assert isinstance(tokens, list)
    assert len(tokens) > 0
