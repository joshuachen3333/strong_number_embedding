# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Strong's Number Embedding Project** - A system that leverages AI and Large Language Models to (semi)automate the insertion of Strong's Numbers into various Bible translations. Strong's Numbers are unique identifiers for Hebrew (Old Testament) and Greek (New Testament) root words that enable deep linguistic Bible study across translations.

## Project Structure

The repository has three main components:

### 1. `original_text_preparation/`
Data processing toolkit for extracting and preparing Bible texts from SQLite databases.

**Purpose**: Download and convert FHL (Faith, Hope, Love) Bible database snapshots into structured JSON datasets.

**Key Scripts** (in `helper_scripts/`):
- `extract_whole_bible_db2json2.sh` - Extract complete Bible versions to JSON (KJV, UNV, BHS Hebrew, FHLWH Greek)
- `batch_extract_strong_dictionary_words2.sh` - Extract Strong's dictionaries (Hebrew/Greek mappings)

**Data Flow**:
1. Download SQLite zips from `https://ftp.fhl.net/FHL/COBS/data/` (e.g., `bible_little.zip`, `bible_kjv.zip`)
2. Extract to `source_sqlite/`
3. Run scripts to generate JSON in `bible_text_json/` and `strong_dict_json/`

**Important**: This directory does NOT create new translations. It strictly follows FHL data snapshots and may need periodic updates when FHL revises source data.

### 2. `dual_reader/`
Basic dual Bible reader web application with synchronized reading and Strong's number support.

**How to Run**: Open `dual_reader/index.html` directly in a browser (no server required).

**Features**:
- Side-by-side synchronized Bible reading
- Multiple Bible versions (UNV, KJV, ESV, RCUV2010, LCC)
- Strong's number display with multiple format support
- Follow checkbox system for main/follower synchronization
- Live API integration with bible.fhl.net

**See**: `dual_reader/CLAUDE.md` for detailed development guidance on this component.

### 3. `dual_reader_right_editor/`
**Advanced variant** with edit mode, localStorage persistence, and word-level highlighting.

**How to Run**: Open `dual_reader_right_editor/index.html` directly in a browser.

**Additional Features** (beyond basic dual_reader):
- **Edit Mode**: Right reader supports editing with auto-save to localStorage
- **Undo/Redo**: Full edit history management
- **Three-tier Loading**: JSON → localStorage → API fallback
- **A1 Highlighting**: Click-to-highlight word system (dark blue)
- **Advanced Synchronization**: Granular follow controls (text selection vs verse scroll)

**Default Setup**:
- Left reader: UNV with Strong's enabled (follower mode)
- Right reader: LCC with edit mode enabled (main mode)

**See**: `dual_reader_right_editor/CLAUDE.md` for comprehensive development rules, architecture details, and critical anti-patterns.

## Architecture Overview

Both dual reader variants use a **Mediator Pattern** with these core components:

- **MockMediator** (`mock_mediator.js`): Central event hub for publish/subscribe communication
- **Left Reader** (`left_reader_frontend.js`): Reference reader, can be main or follower
- **Right Reader** (`right_reader_frontend.js`): Can sync or operate independently; has edit mode in advanced variant
- **App Controller** (`app.js`): Global UI coordination, internationalization (EN/正體中文)

**Critical Design Rules**:
- Components communicate ONLY through MockMediator events (never direct calls)
- Follow checkbox logic: checked = follower, unchecked = independent/main
- Parent-child hierarchy: "FL TxT Sel" (Follow Text Selection) enables "FL Ver Scrl" (Follow Verse Scroll)
- Last checkbox wins: checking any follow box makes that reader the follower
- Other abbreviated controls: "SN" (Strong's Numbers), "Ver HL" (Verse Highlight), "Single HL" (Single Highlight)

## API Integration

**Data Source**: bible.fhl.net (authorized for this project)

**Bible Text API**: `https://bible.fhl.net/json/qb.php`
- Parameters: `version` (unv, kjv, esv, etc.), `chineses` (Chinese book abbreviation), `chap` (chapter), `strong` (0 or 1)
- Response: `{record: [{sec, bible_text}, ...]}`

**Book Mapping**: 66 books with English ↔ Chinese abbreviations (e.g., "Genesis" ↔ "創", "Matthew" ↔ "太")

**API Characteristics**:
- Chinese abbreviations required regardless of Bible version
- English versions may return Chinese text (handled with fallbacks)
- Strong's numbers not consistently available via JSON API (web interface has more complete data)

## Strong's Number Formats

The application parses four formats from FHL API:
- `<WH1234>` / `<WG5678>` - FHL Hebrew/Greek format
- `{<WH1234>}` / `{<WG5678>}` - Wrapped format
- `{H1234}` / `{G5678}` - Simple format
- `(H1234)` / `(G5678)` - Parentheses format

Rendered as clickable spans:
```html
<span class="strongs-number" data-strong="G1722" title="Strong's G1722">[G1722]</span>
```

## UI Control Abbreviations

To save horizontal space, control labels use abbreviated strings:

**Follow Controls**:
- **FL TxT Sel** - Follow Text Selection (parent control for chapter/book sync)
- **FL Ver Scrl** - Follow Verse Scroll (child control for verse-level scroll sync)

**Display Controls**:
- **SN** - Strong's Numbers toggle
- **Ver HL** - Verse Highlight toggle
- **Single HL** - Single Highlight mode (left reader only)

**Other Controls**:
- **Edit** - Edit mode toggle (right reader only in advanced variant)
- **SN cpd** - Strong's Number compound input field (for manual entry)
- **Ver** - Bible version selector
- **BK** - Book selector
- **Cptr** - Chapter selector

## Development Commands

**No build system required** - these are pure client-side web applications with shell script data processing.

### Running Applications
```bash
# Basic dual reader
open dual_reader/index.html

# Advanced variant with edit mode
open dual_reader_right_editor/index.html
```

### Data Processing
```bash
# Navigate to original_text_preparation/

# Download source data
cd source_sqlite/
wget https://ftp.fhl.net/FHL/COBS/data/bible_little.zip
wget https://ftp.fhl.net/FHL/COBS/data/bible_kjv.zip
unzip bible_little.zip
unzip bible_kjv.zip

# Extract Strong's dictionaries
cd ../strong_dict_json/
# Copy script and database, then run:
./batch_extract_strong_dictionary_words2.sh 1 9015 ot  # Old Testament
./batch_extract_strong_dictionary_words2.sh 1 1768 nt  # New Testament

# Extract Bible versions
cd ../bible_text_json/
./extract_whole_bible_db2json2.sh -f ../source_sqlite/bible_kjv.db -d kjv
./extract_whole_bible_db2json2.sh -f ../source_sqlite/bible_little.db -d unv
```

## Working with Subdirectories

**When modifying `dual_reader/`**: Consult `dual_reader/CLAUDE.md` for basic dual reader architecture.

**When modifying `dual_reader_right_editor/`**:
- **MUST READ** `dual_reader_right_editor/CLAUDE.md` first
- Contains critical development rules learned from painful debugging experiences
- Documents immutable initialization sequences, anti-patterns to avoid, and state management rules
- See `dual_reader_right_editor/dev_criteria_en.md` for comprehensive development checklist

**When modifying `original_text_preparation/`**: Focus on shell script robustness and data format compatibility.

## Common Development Tasks

### Adding Bible Versions
1. Update `<select>` options in `index.html` for both readers
2. Ensure version code matches FHL API conventions
3. Test with both Strong's enabled and disabled

### Modifying Synchronization
1. Work through MockMediator's event system
2. Use `MockMediator.publish(eventName, data)` - never direct component calls
3. Check follow checkbox state before publishing events
4. Test bidirectional sync (both readers as main/follower)

### UI Changes
1. Update HTML structure in `index.html`
2. Update corresponding JavaScript selectors (avoid ID changes for critical elements)
3. Test resizable components still function
4. Verify internationalization (EN/中文) for new UI elements

### Strong's Number Handling
1. Update parsing regex patterns in both reader files
2. Test all four Strong's number formats
3. Ensure clickability and event publishing work
4. Verify proper rendering with `data-strong` attributes

## File Organization

**Root Level**:
- `CLAUDE.md` (this file) - Project-wide guidance
- `README.txt` - Project purpose and background
- `CHANGELOG.md` - Version history and breaking changes
- `LICENSE`, `seek4help.txt` - Legal and support info

**Critical Files by Component**:
- **original_text_preparation**: `helper_scripts/*.sh`, READMEs in `doc/`
- **dual_reader**: `index.html`, `js/mock_mediator.js`, `js/*_reader_frontend.js`, `js/app.js`
- **dual_reader_right_editor**: Same as dual_reader + `js/highlighting_foundation.js`, comprehensive documentation files

## Supported Bible Versions

- **UNV** (和合本) - Chinese Union Version with Strong's
- **KJV** - King James Version with Strong's
- **ESV** - English Standard Version
- **RCUV2010** (和合本2010) - Revised Chinese Union Version 2010
- **LCC** (呂振中譯本) - Lü Zhènzhōng Translation
- **BHS** - Biblia Hebraica Stuttgartensia (Hebrew OT, via data extraction)
- **FHLWH** - FHL Westcott-Hort Greek NT (via data extraction)

## Internationalization

Both dual reader applications support:
- **English** (default)
- **正體中文** (Traditional Chinese)

Language preference persists in localStorage. Dynamic UI updates via `translations` object in `app.js`.

## Important Notes

**Data Authorization**: All bible.fhl.net usage is authorized for this project.

**Browser Requirements**: Modern browsers with localStorage and fetch API support.

**No Backend**: Pure client-side applications with RESTful API integration.

**Development Focus**:
- `dual_reader/` = basic synchronized reading
- `dual_reader_right_editor/` = advanced editing and highlighting capabilities
- Choose appropriate variant based on feature requirements

**Future Goals**: AI/LLM integration to automate Strong's number embedding into unannotated Bible translations, with human-in-the-loop editing environment.
