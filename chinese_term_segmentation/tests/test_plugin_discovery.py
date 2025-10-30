"""Tests for plugin discovery system (T006, T008)."""

import pytest
import json
import tempfile
from pathlib import Path
from src.core.plugin_discovery import PluginDiscovery
from src.core.plugin_loader import PluginLoader


@pytest.fixture
def temp_plugin_dir(tmp_path):
    """Create temporary plugin directory structure."""
    # Create tokenizers directory
    tokenizers_dir = tmp_path / "tokenizers"
    tokenizers_dir.mkdir()

    # Create plugin.json
    plugin_metadata = {
        "plugins": [
            {
                "name": "tokenizer.test",
                "module_path": "test_plugin.py",
                "class_name": "TestPlugin",
                "description": "Test tokenizer plugin"
            }
        ]
    }

    with open(tokenizers_dir / "plugin.json", 'w') as f:
        json.dump(plugin_metadata, f)

    # Create test plugin module
    plugin_code = '''
from src.core.plugin_interfaces import TokenizerPlugin
from typing import List, Dict, Optional

class TestPlugin(TokenizerPlugin):
    @property
    def name(self) -> str:
        return "tokenizer.test"

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
'''

    with open(tokenizers_dir / "test_plugin.py", 'w') as f:
        f.write(plugin_code)

    return tmp_path


def test_discover_plugins(temp_plugin_dir):
    """Test T006: Automatic Plugin Discovery."""
    discovery = PluginDiscovery(str(temp_plugin_dir))

    plugins = discovery.discover()

    assert len(plugins) == 1
    assert plugins[0]['name'] == 'tokenizer.test'
    assert plugins[0]['class_name'] == 'TestPlugin'
    assert plugins[0]['plugin_type'] == 'tokenizers'


def test_discover_no_plugin_directory():
    """Test T006: Discovery handles missing directory gracefully."""
    discovery = PluginDiscovery("/nonexistent/path")

    plugins = discovery.discover()

    assert len(plugins) == 0


def test_find_plugin_by_name(temp_plugin_dir):
    """Test T006: Find plugin metadata by name."""
    discovery = PluginDiscovery(str(temp_plugin_dir))
    discovery.discover()

    plugin_info = discovery.find_by_name('tokenizer.test')

    assert plugin_info is not None
    assert plugin_info['name'] == 'tokenizer.test'


def test_find_nonexistent_plugin(temp_plugin_dir):
    """Test T006: Find returns None for unknown plugin."""
    discovery = PluginDiscovery(str(temp_plugin_dir))
    discovery.discover()

    plugin_info = discovery.find_by_name('tokenizer.nonexistent')

    assert plugin_info is None


def test_load_plugin_class(temp_plugin_dir):
    """Test T006: Load plugin class from module."""
    discovery = PluginDiscovery(str(temp_plugin_dir))
    plugins = discovery.discover()

    plugin_info = plugins[0]
    plugin_class = discovery.load_plugin(plugin_info)

    assert plugin_class is not None
    assert plugin_class.__name__ == 'TestPlugin'


def test_plugin_loader_lazy_loading(temp_plugin_dir):
    """Test T006: Lazy Plugin Loading."""
    loader = PluginLoader(str(temp_plugin_dir))

    # Before discovery
    assert loader.is_cached('tokenizer.test') is False

    # Discover plugins
    count = loader.discover_plugins()
    assert count == 1

    # Still not cached (lazy loading)
    assert loader.is_cached('tokenizer.test') is False

    # Load plugin (triggers lazy load)
    plugin = loader.load('tokenizer.test')

    assert plugin is not None
    assert plugin.name == 'tokenizer.test'
    assert loader.is_cached('tokenizer.test') is True


def test_plugin_loader_cache(temp_plugin_dir):
    """Test T006: Plugin caching works correctly."""
    loader = PluginLoader(str(temp_plugin_dir))
    loader.discover_plugins()

    # Load twice
    plugin1 = loader.load('tokenizer.test')
    plugin2 = loader.load('tokenizer.test')

    # Should return same instance
    assert plugin1 is plugin2


def test_plugin_loader_clear_cache(temp_plugin_dir):
    """Test T006: Clear plugin cache."""
    loader = PluginLoader(str(temp_plugin_dir))
    loader.discover_plugins()

    # Load and cache
    loader.load('tokenizer.test')
    assert loader.is_cached('tokenizer.test')

    # Clear cache
    loader.clear_cache('tokenizer.test')

    assert not loader.is_cached('tokenizer.test')


def test_plugin_loader_cache_stats(temp_plugin_dir):
    """Test T009: Plugin metrics - cache statistics."""
    loader = PluginLoader(str(temp_plugin_dir))
    loader.discover_plugins()

    # Initial stats
    stats = loader.get_cache_stats()
    assert stats['cached_count'] == 0

    # Load plugin
    loader.load('tokenizer.test')

    stats = loader.get_cache_stats()
    assert stats['cached_count'] == 1
    assert 'tokenizer.test' in stats['plugins']


def test_invalid_plugin_json(tmp_path):
    """Test T006: Handle invalid plugin.json gracefully."""
    tokenizers_dir = tmp_path / "tokenizers"
    tokenizers_dir.mkdir()

    # Create invalid JSON
    with open(tokenizers_dir / "plugin.json", 'w') as f:
        f.write("{invalid json")

    discovery = PluginDiscovery(str(tmp_path))
    plugins = discovery.discover()

    # Should handle error gracefully
    assert len(plugins) == 0
