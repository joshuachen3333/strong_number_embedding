"""Plugin discovery system for automatic filesystem scanning."""

import os
import json
import importlib.util
from pathlib import Path
from typing import List, Dict, Optional, Type
import logging

logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Discovers and loads plugins from filesystem.

    Scans designated plugin directories, reads metadata from plugin.json files,
    and dynamically loads plugin modules.

    Example plugin.json:
        {
            "plugins": [
                {
                    "name": "tokenizer.jieba",
                    "module_path": "jieba_plugin.py",
                    "class_name": "JiebaPlugin",
                    "description": "Jieba Chinese tokenizer"
                }
            ]
        }
    """

    def __init__(self, plugins_dir: str = "src/plugins"):
        """Initialize plugin discovery.

        Args:
            plugins_dir: Root directory for plugins
        """
        self.plugins_dir = Path(plugins_dir)
        self._discovered: List[Dict] = []

    def discover(self) -> List[Dict]:
        """Discover all plugins in plugins directory.

        Scans subdirectories for plugin.json files and parses metadata.

        Returns:
            List of plugin metadata dicts
        """
        self._discovered.clear()

        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return []

        # Scan subdirectories (tokenizers, embeddings, aligners, scorers)
        for plugin_type_dir in self.plugins_dir.iterdir():
            if not plugin_type_dir.is_dir():
                continue

            if plugin_type_dir.name.startswith('__'):
                continue  # Skip __pycache__ etc.

            plugin_type = plugin_type_dir.name

            # Look for plugin.json
            metadata_file = plugin_type_dir / "plugin.json"
            if not metadata_file.exists():
                logger.debug(f"No plugin.json in {plugin_type_dir}")
                continue

            # Load metadata
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)

                # Validate structure
                if 'plugins' not in metadata:
                    logger.error(f"Invalid plugin.json in {plugin_type_dir}: missing 'plugins' key")
                    continue

                # Add plugin type and base directory to each plugin entry
                for plugin_info in metadata['plugins']:
                    plugin_info['plugin_type'] = plugin_type
                    plugin_info['base_dir'] = str(plugin_type_dir)
                    self._discovered.append(plugin_info)

                logger.info(f"Discovered {len(metadata['plugins'])} plugins in {plugin_type_dir}")

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing {metadata_file}: {e}")
            except Exception as e:
                logger.error(f"Error loading metadata from {metadata_file}: {e}")

        return self._discovered

    def load_plugin(self, plugin_info: Dict) -> Optional[Type]:
        """Dynamically load a plugin class from module.

        Args:
            plugin_info: Plugin metadata dict with 'module_path' and 'class_name'

        Returns:
            Loaded plugin class or None if failed
        """
        module_path = plugin_info.get('module_path')
        class_name = plugin_info.get('class_name')

        if not module_path or not class_name:
            logger.error(f"Invalid plugin info: missing module_path or class_name")
            return None

        try:
            # Construct full path
            full_path = Path(plugin_info['base_dir']) / module_path

            if not full_path.exists():
                logger.error(f"Plugin module not found: {full_path}")
                return None

            # Load module dynamically
            spec = importlib.util.spec_from_file_location(
                class_name,
                full_path
            )

            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {full_path}")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get plugin class
            plugin_class = getattr(module, class_name, None)

            if plugin_class is None:
                logger.error(f"Class {class_name} not found in {module_path}")
                return None

            logger.info(f"Loaded plugin class: {class_name} from {module_path}")
            return plugin_class

        except Exception as e:
            logger.error(f"Error loading plugin {class_name}: {e}", exc_info=True)
            return None

    def get_discovered(self) -> List[Dict]:
        """Get list of discovered plugins.

        Returns:
            List of plugin metadata dicts
        """
        return self._discovered.copy()

    def find_by_name(self, name: str) -> Optional[Dict]:
        """Find plugin metadata by name.

        Args:
            name: Plugin name (e.g., 'tokenizer.jieba')

        Returns:
            Plugin metadata dict or None if not found
        """
        for plugin_info in self._discovered:
            if plugin_info.get('name') == name:
                return plugin_info
        return None
