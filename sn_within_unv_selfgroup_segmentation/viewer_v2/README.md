# Parsed Verse Viewer v2

Event-driven architecture with mediator pattern, caching, and Strong's dictionary.

## Quick Start

```bash
cd viewer_v2
./start_viewer.sh
```

Browser opens at `http://localhost:8000/viewer_v2/`

## What's New in v2

### 1. **Mediator Pattern** - Decoupled Components
- All components communicate via events only
- No direct dependencies between modules
- Clean separation of concerns

### 2. **In-Memory Caching**
- Parsed verses cached after first load
- API responses cached by book/chapter
- Dictionary lookups cached by SN code
- Eliminates redundant network requests

### 3. **Loading States**
- Spinners during chapter/verse loading
- Visual feedback for all async operations
- Better user experience

### 4. **Error Handling**
- User-friendly error messages in UI
- Banner for critical errors (manifest load)
- Toast notifications for transient errors
- Graceful degradation

### 5. **Strong's Dictionary Preview**
- Click any SN tag to show tooltip
- Hebrew/Greek word + transliteration + definition
- Cached for instant subsequent lookups
- Mock data currently (TODO: connect to real dictionary)

## Architecture

```
Event Flow:
User Click → Mediator Event → App Controller → Data Loader → Mediator Event → UI Update

Components:
- Mediator: Central event bus
- DataLoader: Fetch + cache data
- LeftPanel: Subscribe to chapter:loaded, publish verse:select
- RightPanel: Subscribe to verse:selected
- Navigation: Subscribe to verse:selected (for hash/localStorage)
- SNDictionary: Subscribe to sn:click
```

## Event Catalog

| Event | Publisher | Subscribers | Data |
|-------|-----------|-------------|------|
| `verse:select` | LeftPanel, Navigation | App | `{book, chapter, verse}` |
| `verse:selected` | App | RightPanel, Navigation | `{book, chapter, verse, content, ...}` |
| `chapter:load` | Navigation | App | `{book, chapter, versePosition}` |
| `chapter:loaded` | App | LeftPanel | `{book, chapter, verseData}` |
| `colors:apply` | RightPanel | LeftPanel | `{colorMap}` |
| `sn:click` | LeftPanel, RightPanel | SNDictionary | `{element, snCode}` |
| `loading:start/end` | DataLoader | App (UI spinners) | `{context}` |
| `error:show` | DataLoader | App (UIUtils) | `{message, type}` |

## File Structure

```
viewer_v2/
├── index.html
├── css/
│   └── styles.css (includes spinner, toast, tooltip animations)
├── js/
│   ├── mediator.js           # Event bus
│   ├── ui_utils.js           # Spinner, toast, banner
│   ├── book_data.js          # 66 books mapping
│   ├── data_loader.js        # Fetch + cache
│   ├── color_mapper.js       # SN group colors
│   ├── sn_dictionary.js      # Dictionary tooltip
│   ├── left_panel.js         # UNV text panel
│   ├── right_panel.js        # Parsed output panel
│   ├── navigation.js         # Keyboard, hash, localStorage
│   └── app.js                # Main controller
├── start_viewer.sh           # Launch script
└── README.md                 # This file
```

## Keyboard Shortcuts

- `↑` / `↓` — Previous/next verse (crosses chapters)
- `←` / `→` — Previous/next chapter
- `Home` / `End` — First/last verse of chapter

## Testing Checklist

- [ ] Initial load shows Gen 1:1
- [ ] Verse selection updates both panels
- [ ] Colors synchronized across panels
- [ ] Keyboard navigation works
- [ ] URL hash updates on verse change
- [ ] localStorage saves position
- [ ] Spinners appear during loading
- [ ] Error banner shows if manifest missing
- [ ] SN click shows dictionary tooltip
- [ ] Toggle buttons hide/show sections
- [ ] Uncertain verses show warning

## TODO

- [ ] Connect SNDictionary to real FHL dictionary API
- [ ] Add verse count in header (e.g., "Gen 1:5 / 31")
- [ ] Prefetch next chapter while viewing current
- [ ] Add search functionality
- [ ] Add statistics dashboard
