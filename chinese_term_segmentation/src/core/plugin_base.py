"""Base plugin class for all plugins in the system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for all plugins in the system.

    All plugins must inherit from this class and implement the required
    abstract methods. Plugins follow a lifecycle: validate -> initialize -> use -> shutdown.
    """

    def __init__(self):
        """Initialize plugin with default state."""
        self._config: Optional[Dict[str, Any]] = None
        self._initialized = False
        self._logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin identifier (e.g., 'tokenizer.jieba').

        Returns:
            Plugin name as string
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version (semantic versioning: '1.0.0').

        Returns:
            Version string
        """
        pass

    @property
    def plugin_type(self) -> str:
        """Plugin type derived from class hierarchy.

        Returns:
            Plugin type name (e.g., 'TokenizerPlugin')
        """
        return self.__class__.__bases__[0].__name__

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid, False otherwise

        Raises:
            ValueError: If configuration is invalid
        """
        # Base implementation - override in subclasses for custom validation
        return True

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration.

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
        """Check if plugin is initialized.

        Returns:
            True if initialized, False otherwise
        """
        return self._initialized

    @property
    def config(self) -> Optional[Dict[str, Any]]:
        """Get plugin configuration.

        Returns:
            Configuration dictionary or None if not initialized
        """
        return self._config
