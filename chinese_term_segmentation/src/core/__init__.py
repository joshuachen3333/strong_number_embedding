"""Core plugin infrastructure for the Chinese Term Segmentation system."""

from .plugin_base import Plugin
from .plugin_manager import PluginManager

__all__ = ["Plugin", "PluginManager"]
