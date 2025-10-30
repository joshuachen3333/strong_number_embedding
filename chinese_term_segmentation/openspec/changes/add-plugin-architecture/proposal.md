# Add Plugin Architecture Foundation

## Why

The current specification defines tokenization and alignment interfaces as standalone functions, but lacks a plugin system to enable runtime flexibility, experimentation, and production features like A/B testing. Implementing a pluggable architecture from the V2 design establishes the foundation for extensible, production-ready alignment capabilities.

## What Changes

- Add `Plugin` base abstract class with initialization and configuration lifecycle
- Add 4 plugin type interfaces: `TokenizerPlugin`, `EmbeddingPlugin`, `AlignmentPlugin`, `ScorerPlugin`
- Add `PluginManager` singleton for registration, retrieval, and hot-swapping of plugins
- Add plugin discovery system with automatic filesystem scanning and lazy loading
- Add configuration management system supporting YAML/JSON with validation
- Convert existing tokenization strategies (jieba, pkuseg) to plugin implementations
- Add plugin metrics collection for monitoring and performance tracking
- Add comprehensive test suite (T001-T010) for plugin system validation

## Impact

- **Affected specs**: `chinese-term-segmentation` (adds Requirements 8 & 9, modifies Requirement 1)
- **Affected code**: New core infrastructure
  - `src/core/plugin_base.py` - Base plugin class
  - `src/core/plugin_interfaces.py` - Plugin type interfaces
  - `src/core/plugin_manager.py` - Plugin manager singleton
  - `src/core/plugin_discovery.py` - Plugin discovery system
  - `src/plugins/tokenizers/*` - Plugin implementations
  - `config/*.yaml` - Configuration files
- **Breaking changes**: None (backward compatibility maintained via wrapper functions)
- **Performance impact**: <5% overhead from plugin indirection (validated in tests)
- **Testing additions**: T001-T010 (10 new tests covering plugin lifecycle, discovery, configuration)