"""Configuration management system with YAML/JSON support."""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading and validation.

    Supports YAML and JSON formats with environment variable overrides.
    Configuration hierarchy: defaults < file < environment variables

    Example config.yaml:
        plugins:
          segmenters:
            default: jieba
            jieba:
              enabled: true
              config:
                dict_path: dictionaries/unv_bible_terms.txt
                hmm: true
    """

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_file: Optional path to config file (YAML or JSON)
        """
        self._config: Dict[str, Any] = {}
        self._config_file = config_file
        self._loaded = False

    def load(self, config_file: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file.

        Args:
            config_file: Path to config file. If None, uses self._config_file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config file format invalid
        """
        config_file = config_file or self._config_file

        if config_file is None:
            logger.warning("No config file specified, using defaults")
            return self._config

        config_path = Path(config_file)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")

        # Determine format from extension
        if config_path.suffix in ['.yaml', '.yml']:
            self._config = self._load_yaml(config_path)
        elif config_path.suffix == '.json':
            self._config = self._load_json(config_path)
        else:
            raise ValueError(f"Unsupported config format: {config_path.suffix}")

        # Apply environment variable overrides
        self._apply_env_overrides()

        self._loaded = True
        logger.info(f"Loaded configuration from {config_file}")

        return self._config

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML configuration file.

        Args:
            path: Path to YAML file

        Returns:
            Configuration dictionary
        """
        try:
            import yaml

            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            return config or {}

        except ImportError:
            raise RuntimeError(
                "PyYAML not installed. Install with: pip install pyyaml"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON configuration file.

        Args:
            path: Path to JSON file

        Returns:
            Configuration dictionary
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides.

        Environment variables in format: SEGMENTATION_KEY__SUBKEY=value
        Example: SEGMENTATION_PLUGINS__TOKENIZERS__DEFAULT=pkuseg
        """
        prefix = "SEGMENTATION_"

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            # Remove prefix and convert to nested dict path
            config_path = key[len(prefix):].lower().split('__')

            # Navigate/create nested dict structure
            current = self._config
            for part in config_path[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set value (try to parse as JSON for complex types)
            try:
                current[config_path[-1]] = json.loads(value)
            except json.JSONDecodeError:
                current[config_path[-1]] = value

            logger.debug(f"Applied env override: {key} = {value}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dotted key path.

        Args:
            key_path: Dotted path like 'plugins.segmenters.default'
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        current = self._config

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default

        return current

    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value by dotted key path.

        Args:
            key_path: Dotted path like 'plugins.segmenters.default'
            value: Value to set
        """
        keys = key_path.split('.')
        current = self._config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def validate(self, schema: Optional[Dict] = None) -> bool:
        """Validate configuration against schema.

        Args:
            schema: Optional schema dict for validation

        Returns:
            True if valid

        Note:
            Basic implementation. Can be extended with jsonschema library.
        """
        if schema is None:
            return True

        # Basic validation - check required keys
        required_keys = schema.get('required', [])
        for key in required_keys:
            if self.get(key) is None:
                logger.error(f"Required configuration key missing: {key}")
                return False

        return True

    def save(self, output_file: str) -> None:
        """Save current configuration to file.

        Args:
            output_file: Path to output file (YAML or JSON based on extension)
        """
        output_path = Path(output_file)

        if output_path.suffix in ['.yaml', '.yml']:
            self._save_yaml(output_path)
        elif output_path.suffix == '.json':
            self._save_json(output_path)
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")

        logger.info(f"Saved configuration to {output_file}")

    def _save_yaml(self, path: Path) -> None:
        """Save configuration as YAML.

        Args:
            path: Output path
        """
        try:
            import yaml

            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._config, f, default_flow_style=False)

        except ImportError:
            raise RuntimeError(
                "PyYAML not installed. Install with: pip install pyyaml"
            )

    def _save_json(self, path: Path) -> None:
        """Save configuration as JSON.

        Args:
            path: Output path
        """
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    @property
    def config(self) -> Dict[str, Any]:
        """Get full configuration dictionary.

        Returns:
            Configuration dict
        """
        return self._config.copy()

    @property
    def is_loaded(self) -> bool:
        """Check if configuration is loaded.

        Returns:
            True if loaded, False otherwise
        """
        return self._loaded
