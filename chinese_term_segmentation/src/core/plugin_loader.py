"""Plugin loader with lazy loading and caching."""

from typing import Dict, Optional
import logging
from .plugin_base import Plugin
from .plugin_discovery import PluginDiscovery

logger = logging.getLogger(__name__)


class PluginLoader:
    """Lazy loading plugin loader with caching.

    Plugins are discovered on initialization but only loaded when first accessed.
    Loaded plugin instances are cached for subsequent requests.
    """

    def __init__(self, plugins_dir: str = "src/plugins"):
        """Initialize plugin loader.

        Args:
            plugins_dir: Root directory for plugins
        """
        self.discovery = PluginDiscovery(plugins_dir)
        self._cache: Dict[str, Plugin] = {}
        self._discovered = False

    def discover_plugins(self) -> int:
        """Discover all available plugins.

        Returns:
            Number of plugins discovered
        """
        plugins = self.discovery.discover()
        self._discovered = True
        logger.info(f"Discovered {len(plugins)} plugins")
        return len(plugins)

    def load(self, name: str, config: Optional[Dict] = None) -> Optional[Plugin]:
        """Load a plugin by name (lazy loading with cache).

        Args:
            name: Plugin name (e.g., 'segmenter.jieba')
            config: Optional configuration dict

        Returns:
            Plugin instance or None if load failed
        """
        # Check cache first
        if name in self._cache:
            logger.debug(f"Plugin {name} loaded from cache")
            return self._cache[name]

        # Discover if not already done
        if not self._discovered:
            self.discover_plugins()

        # Find plugin metadata
        plugin_info = self.discovery.find_by_name(name)
        if plugin_info is None:
            logger.error(f"Plugin {name} not found in discovered plugins")
            return None

        # Load plugin class
        plugin_class = self.discovery.load_plugin(plugin_info)
        if plugin_class is None:
            return None

        # Instantiate plugin
        try:
            plugin_instance = plugin_class()

            # Initialize with config if provided
            if config is not None:
                plugin_instance.initialize(config)

            # Cache instance
            self._cache[name] = plugin_instance

            logger.info(f"Loaded and cached plugin: {name}")
            return plugin_instance

        except Exception as e:
            logger.error(f"Error instantiating plugin {name}: {e}", exc_info=True)
            return None

    def preload(self, name: str, config: Optional[Dict] = None) -> bool:
        """Preload a plugin (eagerly load and cache).

        Args:
            name: Plugin name
            config: Optional configuration dict

        Returns:
            True if loaded successfully, False otherwise
        """
        plugin = self.load(name, config)
        return plugin is not None

    def is_cached(self, name: str) -> bool:
        """Check if plugin is already loaded and cached.

        Args:
            name: Plugin name

        Returns:
            True if cached, False otherwise
        """
        return name in self._cache

    def clear_cache(self, name: Optional[str] = None) -> None:
        """Clear plugin cache.

        Args:
            name: Optional plugin name to clear specific plugin.
                  If None, clears all cached plugins.
        """
        if name is None:
            # Shutdown all cached plugins
            for plugin in self._cache.values():
                if plugin.is_initialized:
                    plugin.shutdown()
            self._cache.clear()
            logger.info("Cleared all plugin cache")
        else:
            if name in self._cache:
                plugin = self._cache.pop(name)
                if plugin.is_initialized:
                    plugin.shutdown()
                logger.info(f"Cleared plugin from cache: {name}")

    def get_cache_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            Dict with cache stats: {'cached_count': 5, 'plugins': [...]}
        """
        return {
            'cached_count': len(self._cache),
            'plugins': list(self._cache.keys())
        }
