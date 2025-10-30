"""Plugin manager singleton for plugin registration and retrieval."""

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
    """Singleton manager for plugin registration and retrieval.

    Thread-safe implementation that manages the lifecycle of all plugins.
    Supports plugin registration, retrieval, hot-swapping, and metrics collection.

    Example:
        >>> pm = PluginManager()
        >>> pm.register("tokenizer.jieba", JiebaPlugin())
        >>> tokenizer = pm.get("tokenizer.jieba")
        >>> tokens = tokenizer.tokenize("起初上帝創造天地")
    """

    _instance: Optional['PluginManager'] = None
    _lock = Lock()

    def __new__(cls):
        """Singleton constructor ensuring only one instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize plugin manager if not already initialized."""
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
        """Register a plugin.

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
                    f"Plugin must be instance of {expected_base.__name__}, "
                    f"got {type(plugin).__name__}"
                )

            self._plugins[name] = plugin
            self._metrics[name] = {
                'usage_count': 0,
                'total_time': 0.0,
                'errors': 0
            }
            logger.info(f"Registered plugin: {name} (v{plugin.version})")

    def get(self, name: str) -> Plugin:
        """Get a plugin by name.

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
        """Replace an existing plugin (hot-swap).

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
            if old_plugin.is_initialized:
                old_plugin.shutdown()

            # Replace with new plugin
            self._plugins[name] = new_plugin
            logger.info(f"Replaced plugin: {name} (old: v{old_plugin.version}, new: v{new_plugin.version})")

            return old_plugin

    def unregister(self, name: str) -> Plugin:
        """Unregister a plugin.

        Args:
            name: Plugin name to unregister

        Returns:
            Unregistered plugin instance

        Raises:
            KeyError: If plugin not found
        """
        with self._lock:
            if name not in self._plugins:
                raise KeyError(f"Plugin '{name}' not registered")

            plugin = self._plugins.pop(name)
            if plugin.is_initialized:
                plugin.shutdown()

            if name in self._metrics:
                del self._metrics[name]

            logger.info(f"Unregistered plugin: {name}")
            return plugin

    def list_plugins(self, plugin_type: Optional[str] = None) -> List[str]:
        """List registered plugins.

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
        """Get usage metrics for a plugin.

        Args:
            name: Plugin name

        Returns:
            Dict with metrics: {'usage_count': 42, 'total_time': 1.5, 'errors': 0}

        Raises:
            KeyError: If no metrics for plugin
        """
        if name not in self._metrics:
            raise KeyError(f"No metrics for plugin '{name}'")
        return self._metrics[name].copy()

    def is_registered(self, name: str) -> bool:
        """Check if a plugin is registered.

        Args:
            name: Plugin name

        Returns:
            True if registered, False otherwise
        """
        return name in self._plugins

    def reset(self) -> None:
        """Reset plugin manager (for testing purposes).

        WARNING: This will shutdown and unregister all plugins!
        """
        with self._lock:
            for plugin in self._plugins.values():
                if plugin.is_initialized:
                    plugin.shutdown()

            self._plugins.clear()
            self._metrics.clear()
            logger.warning("PluginManager reset - all plugins unregistered")
