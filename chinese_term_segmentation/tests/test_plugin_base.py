"""Tests for plugin base class (T001)."""

import pytest
from src.core.plugin_base import Plugin


class MockPlugin(Plugin):
    """Mock plugin for testing."""

    @property
    def name(self) -> str:
        return "test.mock"

    @property
    def version(self) -> str:
        return "1.0.0"


def test_plugin_initialization():
    """Test T001: Plugin Interface Validation - initialization."""
    plugin = MockPlugin()

    assert plugin.name == "test.mock"
    assert plugin.version == "1.0.0"
    assert not plugin.is_initialized
    assert plugin.config is None


def test_plugin_configuration():
    """Test T001: Plugin Interface Validation - configuration."""
    plugin = MockPlugin()
    config = {"key": "value"}

    plugin.initialize(config)

    assert plugin.is_initialized
    assert plugin.config == config


def test_plugin_validation():
    """Test T001: Plugin Interface Validation - config validation."""
    plugin = MockPlugin()

    # Base implementation should accept any config
    assert plugin.validate_config({})
    assert plugin.validate_config({"test": "data"})


def test_plugin_shutdown():
    """Test T007: Plugin Lifecycle - shutdown."""
    plugin = MockPlugin()
    plugin.initialize({"test": "data"})

    assert plugin.is_initialized

    plugin.shutdown()

    assert not plugin.is_initialized


def test_plugin_invalid_config():
    """Test T001: Plugin Interface Validation - invalid config handling."""

    class StrictPlugin(Plugin):
        """Plugin with strict validation."""

        @property
        def name(self) -> str:
            return "test.strict"

        @property
        def version(self) -> str:
            return "1.0.0"

        def validate_config(self, config) -> bool:
            return "required_key" in config

    plugin = StrictPlugin()

    with pytest.raises(ValueError, match="Invalid configuration"):
        plugin.initialize({"wrong_key": "value"})


def test_plugin_type_property():
    """Test T001: Plugin Interface Validation - plugin type detection."""
    plugin = MockPlugin()

    assert plugin.plugin_type == "Plugin"
