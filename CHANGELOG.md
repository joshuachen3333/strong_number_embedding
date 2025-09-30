# Changelog

All notable changes to the Strong's Number Embedding Project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2025-01-XX

### Added - Major Feature: Bidirectional Main Checkbox System
- **Main Reader Control**: Added exclusive main checkboxes to both left and right readers
- **Dynamic Role Switching**: Either reader can become main via checkbox, other becomes follower automatically
- **Real-time Scroll Synchronization**: Main reader's scrolling followed in real-time by follower reader
- **Smart Content Loading**: Intelligent detection of book/chapter changes vs verse-only scrolling
- **Visual Verse Highlighting**: Synchronized verses highlighted in follower reader
- **Bidirectional Event System**: Complete event publishing and subscription system for both readers
- **UI Status Updates**: Clear status displays showing main/follower role changes
- **Left Reader Callback System**: Added `registerLeftReaderUpdateCallback()` to MockMediator
- **Comprehensive Translation Support**: Main checkbox labels in English and Traditional Chinese

### Enhanced
- **MockMediator Synchronization**: Enhanced `syncPosition()` to handle bidirectional updates
- **Event Publishing Logic**: Conditional event publishing based on main/follower status
- **Content Area Controls**: Both readers now update UI controls when following
- **Scroll Detection**: Advanced verse detection algorithms for accurate synchronization
- **Error Handling**: Improved handling of book/chapter mismatches during synchronization

### Fixed
- **Asymmetric Synchronization**: Resolved issues where left-to-right sync worked differently than right-to-left
- **Translation Key Bug**: Fixed `mainReaderChapterLabel` reference to use correct `leftReaderChapterLabel`
- **Checkbox State Loops**: Prevented infinite toggle loops with proper event handling flags
- **Content Reversion**: Fixed follower reader reverting to previous content during navigation
- **Event Publishing**: Ensured consistent conditional publishing in both readers
- **UI Control Sync**: Fixed controls not updating when reader becomes follower via scroll

### Changed
- **Reader Title Removal**: Removed "Left Reader" and "Right Reader" titles to save horizontal space
- **Strong's Numbers Default**: Changed Strong's number checkboxes to unchecked by default
- **Event System**: Unified event publishing pattern across both readers

## [1.0.0] - 2024-XX-XX

### Added - Initial Dual Reader Implementation
- **Dual Synchronized Bible Reader**: Side-by-side Bible reading with basic synchronization
- **MockMediator Pattern**: Client-side mediator for communication between readers
- **Bible.fhl.net Integration**: Live API integration with Faith, Hope, Love Bible database
- **Multiple Bible Versions**: Support for UNV, KJV, ESV, RCUV2010, LCC versions
- **Strong's Number Support**: Display and parsing of Strong's numbers in multiple formats
- **Book Mapping System**: Complete Hebrew/Chinese abbreviation mapping for 66 Bible books
- **Internationalization**: English and Traditional Chinese UI support
- **Resizable Components**: Draggable resize handles for content areas and status displays
- **Debug Mode**: Toggle-able debug output for development

### Technical Implementation
- **HTML Structure**: Complete dual reader layout in `index.html`
- **JavaScript Components**: 
  - `mock_mediator.js` - Central communication hub
  - `left_reader_frontend.js` - Left reader logic
  - `right_reader_frontend.js` - Right reader logic (initially main_reader_frontend.js)
  - `app.js` - Application initialization and utilities
- **CSS Styling**: Responsive layout with resize functionality
- **API Integration**: RESTful integration with bible.fhl.net JSON APIs

### Initial Features
- **Chapter Loading**: Load Bible chapters with version and Strong's number options
- **Basic Synchronization**: Right reader follows left reader's chapter changes
- **Strong's Number Parsing**: Multiple format support for Strong's number tags
- **Language Support**: Bilingual interface with localStorage persistence
- **Version Management**: Independent version selection for each reader
- **Content Caching**: Basic caching system in MockMediator

---

## Development Notes

### Commit Reference Guide
- **Major Features**: Version bumps with comprehensive feature additions
- **Bug Fixes**: Patch-level improvements and issue resolutions  
- **Enhancements**: Minor feature improvements and optimizations
- **Refactoring**: Code structure improvements without feature changes

### Future Development
- **WebSocket Integration**: Real-time synchronization across browser tabs/devices
- **Strong's Definition Popups**: Clickable Strong's numbers with definition display
- **Advanced Search**: Cross-reference and concordance features
- **User Preferences**: Persistent settings and bookmarks
- **Performance Optimization**: Enhanced caching and lazy loading

### Breaking Changes
- **v2.0.0**: Main/follower terminology changed from original "main/second" reader naming
- **v2.0.0**: Event publishing now conditional based on reader role (may affect custom integrations)