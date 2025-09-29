# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Strong's Number Embedding Project** - a system that aims to leverage AI and Large Language Models to (semi)automate the insertion of Strong's Numbers into various Bible translations. The project has two main components:

1. **Original Text Preparation** (`original_text_preparation/`): Data processing tools and scripts to generate structured JSON datasets from bible.fhl.net
2. **Dual Bible Reader** (`dual_reader/`): A web-based application for synchronized Bible reading with Strong's number support

## Development Commands

Since this is primarily a client-side web application with shell scripts for data processing, there are no traditional build/test commands. However, here are the key operational commands:

### Running the Dual Bible Reader
- Open `dual_reader/index.html` directly in a web browser
- No server setup required for the current version

### Data Processing Scripts
Located in `original_text_preparation/helper_scripts/`:
- `extract_whole_bible_db2json2.sh` - Extract complete Bible text from SQLite to JSON
- `batch_extract_strong_dictionary_words2.sh` - Extract Strong's dictionary data

### API Testing
The application uses live API calls to `https://bible.fhl.net/json/qb.php` with parameters:
- `version`: Bible version (unv, kjv, esv, etc.)
- `chineses`: Chinese book abbreviation (創, 出, 利, etc.)
- `chap`: Chapter number
- `strong`: Strong's numbers flag (1 or 0)

## Architecture Overview

### Dual Bible Reader Architecture

The dual reader uses a **Mediator Pattern** for component communication:

**Core Components:**
- **MockMediator** (`mock_mediator.js`): Central communication hub managing data flow and synchronization
- **Left Reader** (`left_reader_frontend.js`): Primary Bible reader that can act as main or follower
- **Right Reader** (`right_reader_frontend.js`): Secondary reader that synchronizes with left reader
- **App Controller** (`app.js`): Application initialization and UI coordination

**Key Design Patterns:**
- **Main/Follower System**: Either reader can become "main" based on last user interaction
- **Event-driven Communication**: Components communicate via publish/subscribe events through MockMediator
- **Real-time API Integration**: Live data fetching from bible.fhl.net APIs
- **Caching Strategy**: MockMediator implements data caching to reduce API calls

### Data Sources and APIs

**Primary Data Source:** bible.fhl.net (Faith, Hope, Love ministry)
- **Bible Text API**: `https://bible.fhl.net/json/qb.php`
- **Strong's Dictionary API**: `https://bible.fhl.net/json/sd.php` (planned)
- **Authorization**: Data usage authorized by bible.fhl.net

**Supported Bible Versions:**
- UNV (Chinese Union Version, 和合本)
- KJV (King James Version)
- ESV (English Standard Version)
- RCUV2010 (和合本2010)
- LCC (呂振中譯本)

### Book Mapping System

The application maintains a comprehensive mapping between English book names and Chinese abbreviations required by the FHL API:

```javascript
{ english: "Genesis", chinese: "創" }
{ english: "Matthew", chinese: "太" }
// ... 66 books total
```

## Key Technical Details

### Strong's Number Handling

The application processes multiple Strong's number formats from the FHL API:
- `<WH1234>` - FHL Hebrew format
- `<WG5678>` - FHL Greek format  
- `{<WH1234>}` - Wrapped format
- `{H1234}` - Simple format

Strong's numbers are rendered as clickable spans when enabled:
```html
<span class="strongs-number" data-strong="G1722" title="Strong's G1722">[G1722]</span>
```

### Follow Checkbox Synchronization System

The application features a sophisticated **bidirectional main/follower system** controlled by granular follow checkboxes:

**Core Features:**
- **Granular Follow Controls**: Two checkbox types per reader - "Follow Text Selection" and "Follow Verse Scroll"
- **Intuitive Follow Logic**: Checked = follower, unchecked = independent/main
- **Last Checkbox Wins**: When any follow checkbox is checked, that reader becomes follower and the other becomes main
- **Parent-Child Relationship**: "Follow Text Selection" is parent control, "Follow Verse Scroll" is child
- **Immediate Synchronization**: When reader becomes follower, immediately updates to match main reader's position
- **Smart Content Loading**: Detects book/chapter changes vs verse-only scrolling for performance

**Follow Checkbox Hierarchy:**
- **Follow Text Selection**: Controls book/chapter following (parent control)
- **Follow Verse Scroll**: Controls verse-level scroll following (child control)
- **Logic Rules**: Child cannot be checked without parent; parent checked enables child by default

**Synchronization Flow:**
1. **Checkbox Selection**: User checks any follow checkbox on left/right reader
2. **Role Assignment**: MockMediator sets that reader as follower, other becomes main
3. **Cross-Reader Update**: Other reader's follow checkboxes are auto-unchecked
4. **Immediate Sync**: Follower reader updates to match main reader's current position
5. **Ongoing Sync**: Main reader's scroll/navigation events trigger follower updates

**Event Types:**
- `leftReaderChapterChanged` / `rightReaderChapterChanged` - Chapter navigation events
- `mainReaderChanged` - Reader role switching notifications
- `strongsNumberClicked` - Strong's number interaction
- `MockMediator.syncPosition()` - Verse-level scroll synchronization

### Internationalization

The application supports English and Traditional Chinese (正體中文) with:
- Dynamic UI text updates via `translations` object in `app.js`
- Language preference persistence in localStorage
- Localized loading messages and status updates

### User Interface Features

**Resizable Components:** Both content areas and status displays support manual resizing
**Debug Mode:** Toggle-able debug output for development
**Independent Controls:** Each reader maintains separate version and Strong's settings
**Status Logging:** Real-time status updates with timestamps

## File Structure Priority

When working on this codebase, focus on these key files:

**Critical Files:**
- `dual_reader/js/mock_mediator.js` - Central data management and API integration
- `dual_reader/js/left_reader_frontend.js` - Left reader logic and event handling
- `dual_reader/js/right_reader_frontend.js` - Right reader logic and synchronization
- `dual_reader/index.html` - Main application HTML structure

**Important Configuration:**
- Bible version options defined in `index.html`
- Book mappings defined in each reader frontend file
- CSS styling in `dual_reader/css/style.css`

## API Integration Notes

**Important:** The FHL API has specific characteristics:
- Chinese book abbreviations are required regardless of Bible version
- English versions may return Chinese text (the application handles this with fallback messages)
- Strong's numbers are not consistently available via JSON API (web interface has more complete data)
- API responses use `record` array with `bible_text` field for verse content

## Recent Development Summary

### Follow Checkbox System Implementation (Latest Feature)

**Development Period**: Recent major enhancement evolving from main checkboxes to intuitive follow controls.

**Key Achievements:**
- **Intuitive Follow Controls**: Replaced confusing "main" checkboxes with clear "follow" checkboxes
- **Granular Control**: Separate checkboxes for text selection following vs verse scroll following
- **Complete Bidirectional Sync**: Both readers can act as main or follower with "last checkbox wins" logic
- **Parent-Child Checkbox Logic**: Follow Text Selection enables Follow Verse Scroll functionality
- **Real-time Scroll Following**: Verse-level synchronization with visual highlighting
- **Smart Content Management**: Efficient loading based on content differences
- **Bug Fixes**: Resolved asymmetric behavior and infinite loop issues

**Technical Implementation:**
- Replaced main checkboxes with two follow checkboxes per reader
- Implemented parent-child checkbox relationship logic
- Enhanced MockMediator with bidirectional callback support and role management
- Added `isUpdatingCheckboxes` flag to prevent infinite loops
- Implemented comprehensive event publishing system with follow checkbox validation
- Added scroll detection and verse identification algorithms
- Created smart content loading with difference detection

**Files Modified:**
- `dual_reader/index.html` - Follow checkbox UI elements replacing main checkboxes
- `dual_reader/js/app.js` - Translation support for follow labels
- `dual_reader/js/mock_mediator.js` - Bidirectional synchronization with follow logic
- `dual_reader/js/left_reader_frontend.js` - Complete follow/main implementation
- `dual_reader/js/right_reader_frontend.js` - Complete follow/main implementation

## Common Development Tasks

When modifying this codebase:

1. **Adding Bible Versions**: Update the `<select>` options in `index.html` for both readers
2. **Modifying Synchronization**: Work with MockMediator's event system and callback registration
3. **UI Changes**: Update both HTML structure and corresponding JavaScript selectors
4. **API Integration**: Modify `MockMediator.fetchChapter()` method for data source changes
5. **Strong's Number Handling**: Update the parsing regex patterns in both reader files
6. **Follow Checkbox Logic**: Ensure both readers handle follow checkbox changes and parent-child relationships consistently
7. **Event Publishing**: Maintain conditional publishing based on main/follower status determined by follow checkboxes

## Data Processing Workflow

For the original text preparation component:
1. Download SQLite databases from bible.fhl.net (URLs in `original_text_preparation/source_sqlite/download_url`)
2. Run extraction scripts to convert to JSON format
3. Generated JSON files serve as structured datasets for the web application
4. Bible texts include embedded Strong's number tags in various formats

The web application can work with either live API data or pre-processed JSON files, making it flexible for different deployment scenarios.