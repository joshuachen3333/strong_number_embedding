# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Dual Bible Reader with Edit Mode** - A client-side web application for synchronized Bible reading with Strong's number support and editing capabilities. This version extends the basic dual reader with right-side editing, localStorage persistence, and advanced word-level highlighting.

## Running the Application

**Basic mode** (no server): Open `index.html` directly in a web browser. All features work except group-based verse coloring.

**With group coloring** (requires server): Run `python start_server.py` from the repo root, then open `http://localhost:8080/dual_reader_right_editor/`. Click any verse in the left panel (UNV/KJV with SN enabled) to apply semantic group coloring.

## Architecture

### Core Design Pattern: Mediator Pattern

All components communicate through **MockMediator** using publish/subscribe events. Direct component-to-component calls are prohibited.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Left Reader   │◄──►│  MockMediator   │◄──►│  Right Reader   │
│   (Reference)   │    │  Event System   │    │   (Editable)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
   Read-only              Pub/Sub Events          Edit Mode
   Strong's source        State Mgmt             localStorage
   UNV default            API Cache              LCC default
```

### Component Responsibilities

**ColorMapper** (`../shared/js/color_mapper.js`):
- Shared group-based SN coloring engine (from viewer_v2)
- Token pipeline: tokenize → assign groups → render colored HTML
- 15-color palette for semantic group backgrounds

**VerseColoring** (`verse_coloring.js`):
- Fetches parsed verse data from `/api/parse` endpoint (start_server.py)
- Extracts groups using ColorMapper.parseGroups()
- Applies group coloring on verse click (left panel, UNV/KJV only)
- Gracefully disabled when server not running (typeof guard)
- In-memory cache for parsed data

**Left Reader** (`left_reader_frontend.js`):
- Reference Bible text display (read-only)
- Strong's number source for word mapping
- On-click group-based verse coloring (via VerseColoring module)
- Default: UNV version with Strong's enabled
- Can be main or follower based on follow checkboxes

**Right Reader** (`right_reader_frontend.js`):
- Editable Bible text with edit mode toggle
- Strong's number insertion and management
- localStorage-based content persistence
- Three-tier loading: JSON → localStorage → API
- Default: LCC version with edit mode enabled
- Can be main or follower based on follow checkboxes

**MockMediator** (`mock_mediator.js`):
- Event coordination (publish/subscribe)
- API integration with bible.fhl.net
- Data caching to reduce API calls
- Main/follower role management
- Position synchronization between readers

**HighlightingFoundation** (`highlighting_foundation.js`):
- A1 self-highlighting: Click word → dark blue highlight
- Future: Cross-reader word mapping (A2+)
- Pluggable enhancement without refactoring existing code

**App** (`app.js`):
- Global UI coordination
- Language switching (EN/正體中文)
- VerticalResizer for UI adjustments
- Translation management

### Main/Follower System

**Follow Checkbox Logic**:
- Two checkboxes per reader: "Follow Text Selection" (parent) and "Follow Verse Scroll" (child)
- Checked = follower, unchecked = main/independent
- Parent-child relationship: Verse scroll requires text selection
- Last checkbox wins: When any follow box is checked, that reader becomes follower
- Cross-reader update: Checking follow auto-unchecks other reader's follow boxes
- Immediate sync: Follower immediately syncs to main reader's current position

**Default Configuration**:
- Right reader: Main (both follow checkboxes unchecked, edit mode enabled)
- Left reader: Follower (both follow checkboxes checked)

### Edit Mode System

**State Management**:
- HTML checkbox (`right-reader-edit-mode`) is Single Source of Truth
- JavaScript variable (`isEditMode`) syncs from checkbox during initialization
- State changes only through event handlers

**Auto-save System**:
- Interval: 10 seconds (configurable)
- Storage: localStorage with keys like `Genesis_1_lcc_edited`
- Change tracking: `hasUnsavedChanges` flag
- Triggered by: Content modifications, verse editing

**Undo/Redo System**:
- Dual stacks: `undoStack` and `redoStack`
- Stores: `{verseId, content, cursorPos}`
- Loop prevention: `isUndoRedoAction` flag

**Three-Tier Loading Priority**:
1. Local JSON files (if available)
2. localStorage (edited content)
3. API calls (bible.fhl.net)

Critical: After API loading, `restoreEditedContent()` must overlay localStorage changes.

## Critical Development Rules

### Immutable Initialization Sequence

**DO NOT change this order**:
1. DOM Ready → DOMContentLoaded listeners
2. Book dropdown population
3. MockMediator callback registration
4. Default initialization (left reader first, right reader waits)
5. Event listener attachment
6. Initial content loading

### State Synchronization Pattern

**Single Source of Truth**:
- HTML checkbox state → JavaScript variable state
- `editModeToggle.checked` → `isEditMode`
- `followCheckbox.checked` → Main/Follower role

### Event System Rules

**Event Publishing**:
- Only publish events when reader is main
- Conditional check: `if (MockMediator.getMainReader() === 'left') { publish(...) }`
- Event names (immutable):
  - `leftReaderChapterChanged` / `rightReaderChapterChanged`
  - `mainReaderChanged`
  - `strongsNumberClicked`
  - `leftReaderHighlightModeChanged`

**Event Communication**:
- ✅ Correct: `MockMediator.publish('eventName', data)`
- ❌ Wrong: `leftReader.someFunction()` (direct calls)

### Strong's Number Integration

**Parse Formats** (four formats, must handle all):
- `<WH1234>` / `<WG5678>` - FHL format
- `{<WH1234>}` / `{<WG5678>}` - Wrapped format
- `{H1234}` / `{G5678}` - Simple format
- `(H1234)` / `(G5678)` - Parentheses format

**Event Handlers**:
- Left reader: `attachStrongsEventListeners()` - Read-only clicks
- Right reader: `attachStrongsEventListenersSecondReader()` - Edit integration
- Both publish `strongsNumberClicked` events to MockMediator

### localStorage Integration

**Critical Rule**: Never skip API loading to directly build pages from localStorage
- ❌ Wrong: Skip API → build from localStorage
- ✅ Correct: API load → render → `restoreEditedContent()` overlay

**Why**: Skipping API destroys initialization flow and loses Strong's functionality

## API Integration

**Data Source**: `https://bible.fhl.net/json/qb.php`

**Parameters**:
- `version`: Version code (unv, kjv, esv, rcuv2010, lcc)
- `chineses`: Chinese book abbreviation (創, 出, 利, etc.)
- `chap`: Chapter number
- `strong`: Strong's flag (1 or 0)

**Characteristics**:
- Chinese abbreviations required regardless of version
- English versions may return Chinese text (handled with fallbacks)
- Strong's not consistently available via JSON (web interface has more)
- Response format: `{record: [{sec, bible_text}, ...]}`

**Book Mapping**: 66 books with English↔Chinese mapping
```javascript
{ english: "Genesis", chinese: "創" }
{ english: "Exodus", chinese: "出" }
// ... etc
```

## Critical DOM Elements

**DO NOT change these IDs**:
- Content areas: `left-reader-content-area`, `right-reader-content-area`
- Controls: `left-reader-book`, `right-reader-book`, etc.
- Follow checkboxes: `left-reader-follow-scroll`, `left-reader-follow-selection`
- Edit mode: `right-reader-edit-mode`, `strong-number-input`

**Data Attributes** (required for functionality):
- `data-verse` - Verse identification for scroll sync
- `data-book` - Book identification for API calls
- `data-chapter` - Chapter identification
- `data-strong` - Strong's number identification
- `data-original` - Edit change tracking

**CSS Classes** (functional, not just styling):
- `.verse` - Verse container
- `.verse-number` - Verse number span
- `.strongs-number` - Clickable Strong's span
- `.verse-highlighted` - Sync scroll highlighting
- `.highlight-a1` - A1 self-highlighting (dark blue)

## Anti-Patterns to Avoid

### Case 1: localStorage Direct Loading
❌ **Wrong**: Skip API loading, build page directly from localStorage
✅ **Correct**: API load → render → `restoreEditedContent()` overlay

### Case 2: State Sync Error
❌ **Wrong**: HTML `checked=true`, JavaScript `isEditMode=false`
✅ **Correct**: Initialize sync: `isEditMode = editModeToggle.checked`

### Case 3: Direct Component Calls
❌ **Wrong**: `rightReader.someFunction()`
✅ **Correct**: `MockMediator.publish('eventName', data)`

### Case 4: Ignoring Follow Checkbox Hierarchy
❌ **Wrong**: Allow verse scroll without text selection
✅ **Correct**: Enforce parent-child: verse scroll requires text selection

## Key Functions Reference

### MockMediator Core Methods
- `subscribe(eventName, callback)` - Event subscription
- `publish(eventName, data)` - Event publishing
- `fetchChapter(book, chapter, version, strong)` - API integration
- `syncPosition(payload)` - Chapter-level sync
- `setMainReader(readerType, interaction)` - Role management
- `getMainReader()` / `getFollowerReader()` - Role queries
- `registerLeftReaderUpdateCallback(callback)` - Left reader callback
- `registerRightReaderUpdateCallback(callback)` - Right reader callback

### Reader Initialization
- `loadLeftPassage(book, chapter, verse)` - Mediator sync callback (left)
- `loadPassage(book, chapter, verse)` - Mediator sync callback (right)
- `loadChapterContent()` - Main content loading
- `initializeLeftReaderDefaults()` - UNV, Strong's ON, follow right
- `initializeRightReaderDefaults()` - LCC, Edit Mode ON

### Edit Mode Functions
- `handleEditModeToggle()` - Edit mode toggle handler
- `saveEditedContent()` - localStorage persistence
- `restoreEditedContent()` - localStorage restoration
- `performUndo()` / `performRedo()` - Edit history

### Strong's Functions
- `parseStrongsNumbers(text)` - Convert tags to clickable spans
- `attachStrongsEventListeners()` - Left reader clicks
- `attachStrongsEventListenersSecondReader()` - Right reader clicks

### Highlighting Functions
- `HighlightingFoundation.init()` - Initialize A1 system
- `HighlightingFoundation.highlightTerm(element, readerType)` - Dark blue highlight
- `HighlightingFoundation.clearHighlights()` - Clear all highlights
- `HighlightingFoundation.testA1(readerType, text)` - Test function

## Development Guidelines

### Before Modifying Code

**1. Check Architecture Consistency**:
- Does it follow Mediator pattern?
- Does it maintain module boundaries?
- Does it preserve existing APIs?

**2. Verify Dependency Integrity**:
- Initialization order: DOM → Listeners → State → Content
- Event flow: User → Event → Mediator → Target
- Dependency chain: DOM → Variables → Logic

**3. Validate State Management**:
- JavaScript variables sync with DOM state?
- Single Source of Truth maintained?
- State changes through proper channels?

**4. Confirm Functional Boundaries**:
- Left/right readers remain independent?
- MockMediator only coordinates, no business logic?
- localStorage management centralized?

### When Adding Features

**Additive Enhancement**:
- Preserve all existing functionality
- Integrate with MockMediator event system
- Minimal, focused, testable changes
- Follow existing patterns

**Follow Checkbox Integration**:
- Ensure parent-child relationships respected
- Update cross-reader checkboxes appropriately
- Prevent infinite loops with `isUpdatingCheckboxes` flag
- Test both main/follower scenarios

**Event Publishing**:
- Publish only when reader is main
- Use existing event names
- Maintain event data structure format
- Include error handling in callbacks

## Internationalization

**Supported Languages**: English, 正體中文

**Translation System**:
- `translations` object in `app.js`
- localStorage persistence: `selectedLanguage`
- Dynamic UI updates on language switch
- Localized loading/status messages

## Testing the Application

**Manual Testing Checklist**:
1. Both readers load independently
2. Follow checkboxes work bidirectionally
3. Edit mode saves to localStorage
4. Strong's numbers display and are clickable
5. A1 highlighting applies dark blue on click
6. Undo/redo works in edit mode
7. Language switching updates UI
8. Auto-save triggers after edits
9. Main/follower roles switch correctly
10. Cross-reader synchronization works

**Debug Mode**: Enable via checkbox in UI to see console output

## File Organization

**Critical Files**:
- `index.html` - Application structure
- `js/mock_mediator.js` - Event coordination
- `js/left_reader_frontend.js` - Reference reader
- `js/right_reader_frontend.js` - Editable reader
- `js/highlighting_foundation.js` - A1 highlighting
- `js/app.js` - Global UI coordination
- `css/style.css` - Application styling

**Documentation**:
- `dev_criteria_en.md` - Comprehensive development rules
- `DESIGN.md` - Architecture design
- `DEVELOPMENT.md` - Main checkbox system (legacy)
- `IMPLEMENTATION.md` - Implementation details
- `USER_GUIDE.md` - User documentation
- `highlight_todo.md` - Advanced highlighting roadmap

## Important Notes

**Data Source Authorization**: bible.fhl.net usage is authorized for this project

**Browser Compatibility**: Modern browsers with localStorage and fetch API support

**No Backend Required**: Pure client-side application with API integration

**Development Focus**: This is the "right editor" variant with advanced editing capabilities beyond the basic dual reader at the parent directory level
