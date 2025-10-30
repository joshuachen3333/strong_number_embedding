"""Tests for plugin manager (T003, T007)."""

import pytest
from src.core.plugin_base import Plugin
from src.core.plugin_interfaces import TokenizerPlugin
from src.core.plugin_manager import PluginManager
from typing import List, Dict, Optional


class MockTokenizerPlugin(TokenizerPlugin):
    """Mock tokenizer plugin for testing."""

    @property
    def name(self) -> str:
        return "tokenizer.mock"

    @property
    def version(self) -> str:
        return "1.0.0"

    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        return text.split()

    def tokenize_with_metadata(self, text: str, context: Optional[Dict] = None) -> List[Dict]:
        words = text.split()
        return [{"word": w, "position": i} for i, w in enumerate(words)]

    def supports_custom_dictionary(self) -> bool:
        return False


@pytest.fixture
def plugin_manager():
    """Fresh plugin manager for each test."""
    pm = PluginManager()
    pm.reset()  # Clear any existing plugins
    return pm


def test_singleton_pattern(plugin_manager):
    """Test T003: Plugin manager is singleton."""
    pm1 = PluginManager()
    pm2 = PluginManager()

    assert pm1 is pm2


def test_register_plugin(plugin_manager):
    """Test T003: Plugin registration."""
    plugin = MockTokenizerPlugin()

    plugin_manager.register("tokenizer.mock", plugin)

    assert plugin_manager.is_registered("tokenizer.mock")
    assert "tokenizer.mock" in plugin_manager.list_plugins()


def test_get_plugin(plugin_manager):
    """Test T003: Plugin retrieval."""
    plugin = MockTokenizerPlugin()
    plugin_manager.register("tokenizer.mock", plugin)

    retrieved = plugin_manager.get("tokenizer.mock")

    assert retrieved is plugin
    assert retrieved.name == "tokenizer.mock"


def test_get_nonexistent_plugin(plugin_manager):
    """Test T003: Get non-existent plugin raises KeyError."""
    with pytest.raises(KeyError, match="not registered"):
        plugin_manager.get("tokenizer.nonexistent")


def test_register_duplicate_plugin(plugin_manager):
    """Test T003: Register duplicate plugin raises ValueError."""
    plugin1 = MockTokenizerPlugin()
    plugin2 = MockTokenizerPlugin()

    plugin_manager.register("tokenizer.mock", plugin1)

    with pytest.raises(ValueError, match="already registered"):
        plugin_manager.register("tokenizer.mock", plugin2)


def test_replace_plugin(plugin_manager):
    """Test T003: Hot-Swap Plugins at Runtime."""
    class MockTokenizerV2(MockTokenizerPlugin):
        @property
        def version(self) -> str:
            return "2.0.0"

    plugin_v1 = MockTokenizerPlugin()
    plugin_v2 = MockTokenizerV2()

    # Register v1
    plugin_manager.register("tokenizer.mock", plugin_v1)
    plugin_v1.initialize({})

    # Replace with v2
    old_plugin = plugin_manager.replace("tokenizer.mock", plugin_v2)

    assert old_plugin is plugin_v1
    assert not old_plugin.is_initialized  # Should be shut down
    assert plugin_manager.get("tokenizer.mock") is plugin_v2


def test_unregister_plugin(plugin_manager):
    """Test T007: Plugin Lifecycle - unregistration."""
    plugin = MockTokenizerPlugin()
    plugin_manager.register("tokenizer.mock", plugin)
    plugin.initialize({})

    unregistered = plugin_manager.unregister("tokenizer.mock")

    assert unregistered is plugin
    assert not unregistered.is_initialized
    assert not plugin_manager.is_registered("tokenizer.mock")


def test_list_plugins_by_type(plugin_manager):
    """Test T003: List plugins with type filter."""
    plugin1 = MockTokenizerPlugin()

    class MockEmbeddingPlugin(Plugin):
        @property
        def name(self) -> str:
            return "embedding.mock"

        @property
        def version(self) -> str:
            return "1.0.0"

    from src.core.plugin_interfaces import EmbeddingPlugin

    class RealMockEmbedding(EmbeddingPlugin):
        @property
        def name(self) -> str:
            return "embedding.mock"

        @property
        def version(self) -> str:
            return "1.0.0"

        def embed(self, text: str, context: Optional[Dict] = None):
            import numpy as np
            return np.zeros(300)

        @property
        def dimension(self) -> int:
            return 300

        def supports_contextualization(self) -> bool:
            return False

    plugin2 = RealMockEmbedding()

    plugin_manager.register("tokenizer.mock", plugin1)
    plugin_manager.register("embedding.mock", plugin2)

    tokenizers = plugin_manager.list_plugins("tokenizer")
    embeddings = plugin_manager.list_plugins("embedding")

    assert "tokenizer.mock" in tokenizers
    assert "embedding.mock" not in tokenizers
    assert "embedding.mock" in embeddings
    assert "tokenizer.mock" not in embeddings


def test_plugin_metrics(plugin_manager):
    """Test T009: Plugin Monitoring - metrics collection."""
    plugin = MockTokenizerPlugin()
    plugin_manager.register("tokenizer.mock", plugin)

    # Access plugin multiple times
    for _ in range(5):
        plugin_manager.get("tokenizer.mock")

    metrics = plugin_manager.get_metrics("tokenizer.mock")

    assert metrics['usage_count'] == 5
    assert 'total_time' in metrics
    assert 'errors' in metrics


def test_invalid_plugin_type(plugin_manager):
    """Test T001: Plugin validation - wrong type."""
    class WrongPlugin(Plugin):
        @property
        def name(self) -> str:
            return "tokenizer.wrong"

        @property
        def version(self) -> str:
            return "1.0.0"

    plugin = WrongPlugin()  # Not a TokenizerPlugin!

    with pytest.raises(ValueError, match="must be instance of"):
        plugin_manager.register("tokenizer.wrong", plugin)
