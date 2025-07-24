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

### Synchronization Mechanism

**Cross-reader synchronization works through:**
1. Scroll detection in active reader
2. Position reporting to MockMediator
3. MockMediator broadcasting to follower reader
4. Follower reader updating display and scrolling to verse

**Event Types:**
- `leftReaderChapterChanged` / `rightReaderChapterChanged` - Chapter navigation
- `mainReaderChanged` - Reader role switching
- `strongsNumberClicked` - Strong's number interaction

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

## Common Development Tasks

When modifying this codebase:

1. **Adding Bible Versions**: Update the `<select>` options in `index.html` for both readers
2. **Modifying Synchronization**: Work with MockMediator's event system and callback registration
3. **UI Changes**: Update both HTML structure and corresponding JavaScript selectors
4. **API Integration**: Modify `MockMediator.fetchChapter()` method for data source changes
5. **Strong's Number Handling**: Update the parsing regex patterns in both reader files

## Data Processing Workflow

For the original text preparation component:
1. Download SQLite databases from bible.fhl.net (URLs in `original_text_preparation/source_sqlite/download_url`)
2. Run extraction scripts to convert to JSON format
3. Generated JSON files serve as structured datasets for the web application
4. Bible texts include embedded Strong's number tags in various formats

The web application can work with either live API data or pre-processed JSON files, making it flexible for different deployment scenarios.