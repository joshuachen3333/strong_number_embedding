# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Dual Bible Reader** application - a web-based dual-pane Bible reader with synchronized scrolling and advanced follow features. The application allows users to view two Bible readers side-by-side, where either reader can act as "main" or "follower" with granular control over text selection and verse scroll synchronization.

## Development Commands

Since this is a client-side web application, there are no traditional build commands. To run the application:

- Open `index.html` directly in a web browser
- No server setup required for the current version

## Architecture Overview

The application uses a **Mediator Pattern** for component communication with bidirectional synchronization capabilities.

### Core Components

- **MockMediator** (`js/mock_mediator.js`): Central communication hub managing data flow, API integration, and reader synchronization
- **Left Reader** (`js/left_reader_frontend.js`): Primary Bible reader that can act as main or follower
- **Right Reader** (`js/right_reader_frontend.js`): Secondary reader with identical capabilities to left reader
- **App Controller** (`js/app.js`): Application initialization, language switching, and UI coordination

### Key Design Patterns

- **Main/Follower System**: Either reader can become "main" based on follow checkbox selections
- **Event-driven Communication**: Components communicate via publish/subscribe events through MockMediator
- **Real-time API Integration**: Live data fetching from bible.fhl.net APIs
- **Caching Strategy**: MockMediator implements data caching to reduce API calls

## Follow Checkbox Synchronization System

The application's core feature is a sophisticated **bidirectional main/follower system** controlled by granular follow checkboxes.

### Follow Checkbox Types

Each reader has two follow checkboxes:
- **Follow Text Selection** (`FL Tx Sel`): Controls book/chapter following (parent control)
- **Follow Verse Scroll** (`FL Ver Scrl`): Controls verse-level scroll following (child control)

### Follow Logic Rules

- **Intuitive Control**: Checked = follower, unchecked = independent/main
- **Last Checkbox Wins**: When any follow checkbox is checked, that reader becomes follower and the other becomes main
- **Parent-Child Relationship**: "Follow Text Selection" is parent control, "Follow Verse Scroll" is child
- **Child Dependency**: Child cannot be checked without parent; parent checked enables child by default

### Synchronization Flow

1. **Checkbox Selection**: User checks any follow checkbox on left/right reader
2. **Role Assignment**: MockMediator sets that reader as follower, other becomes main
3. **Cross-Reader Update**: Other reader's follow checkboxes are auto-unchecked
4. **Immediate Sync**: Follower reader updates to match main reader's current position
5. **Ongoing Sync**: Main reader's scroll/navigation events trigger follower updates

## Data Sources and APIs

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

## Strong's Number Handling

The application processes multiple Strong's number formats from the FHL API:
- `<WH1234>` - FHL Hebrew format
- `<WG5678>` - FHL Greek format
- `{<WH1234>}` - Wrapped format
- `{H1234}` - Simple format

Strong's numbers are rendered as clickable spans when enabled:
```html
<span class="strongs-number" data-strong="G1722" title="Strong's G1722">[G1722]</span>
```

## Event System

### Core Event Types

- **Chapter Change Events**: `leftReaderChapterChanged` / `rightReaderChapterChanged`
- **Role Change Events**: `mainReaderChanged` - Published when main reader switches
- **Position Sync**: `MockMediator.syncPosition()` - Verse-level scroll synchronization
- **Strong's Interaction**: `strongsNumberClicked` - Strong's number click events

### Event Publishing Logic

Both readers use **conditional publishing** based on main/follower status:

```javascript
// Only publish events when this reader is main
if (MockMediator.getMainReader() === 'left') {
    MockMediator.publish('leftReaderChapterChanged', eventData);
}
```

## Key Files and Structure

```
├── index.html                    # Main application HTML structure
├── css/style.css                 # Application styling
├── js/
│   ├── mock_mediator.js          # Central data management and API integration
│   ├── left_reader_frontend.js   # Left reader logic and event handling
│   ├── right_reader_frontend.js  # Right reader logic and synchronization
│   └── app.js                    # Application initialization and UI coordination
├── DESIGN.md                     # Software architecture documentation
├── DEVELOPMENT.md                # Technical implementation details
├── IMPLEMENTATION.md             # Component-level implementation guide
└── USER_GUIDE.md                 # End-user documentation
```

## Internationalization

The application supports English and Traditional Chinese (正體中文) with:
- Dynamic UI text updates via `translations` object in `app.js`
- Language preference persistence in localStorage
- Localized loading messages and status updates

## API Integration Details

**Important API Characteristics:**
- Chinese book abbreviations are required regardless of Bible version
- English versions may return Chinese text (the application handles this with fallback messages)
- Strong's numbers are not consistently available via JSON API (web interface has more complete data)
- API responses use `record` array with `bible_text` field for verse content

## Performance Optimizations

### Smart Content Loading
```javascript
// Only load new content when book/chapter actually differs
if (currentDisplayedBook !== targetBook || currentDisplayedChapter !== chapter) {
    // Load different chapter
    loadChapterContent().then(() => scrollToVerse(verse));
} else {
    // Same chapter, just scroll to verse (no API call needed)
    scrollToVerse(verse);
}
```

### Loop Prevention
```javascript
let isUpdatingCheckboxes = false;

function handleFollowToggle() {
    if (isUpdatingCheckboxes) return; // Prevent infinite loops
    isUpdatingCheckboxes = true;
    // ... toggle logic
    setTimeout(() => { isUpdatingCheckboxes = false; }, 100);
}
```

## Common Development Tasks

### Adding Bible Versions
Update the `<select>` options in `index.html` for both readers

### Modifying Synchronization Logic
Work with MockMediator's event system and callback registration in `js/mock_mediator.js`

### Follow Checkbox Logic
Ensure both readers handle follow checkbox changes and parent-child relationships consistently

### Event Publishing
Maintain conditional publishing based on main/follower status determined by follow checkboxes

### Strong's Number Handling
Update the parsing regex patterns in both reader files for new Strong's number formats

## UI Features

- **Resizable Components**: Both content areas and status displays support manual resizing
- **Debug Mode**: Toggle-able debug output for development
- **Independent Controls**: Each reader maintains separate version and Strong's settings
- **Status Logging**: Real-time status updates with timestamps
- **Visual Highlighting**: Follow verse scroll includes visual highlighting of current verse