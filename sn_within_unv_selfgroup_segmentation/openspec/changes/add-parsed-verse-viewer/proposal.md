# Change: Add Parsed Verse Viewer

## Why

The UNV+SN parsing system produces structured output files in `output/{Book}/{Chapter}/{verse}` but lacks a convenient way to review parser quality verse-by-verse. Reviewers need to visually verify SN groupings are correct and identify uncertain or problematic verses. A dedicated dual-panel viewer enables efficient review with synchronized color-coded groups between source text and parsed output.

## What Changes

- **NEW**: Add `viewer/` directory with complete web application
- **NEW**: Add event-driven architecture using Mediator pattern (like `dual_reader_right_editor/`)
- **NEW**: Add 8 JavaScript modules implementing modular viewer architecture
- **NEW**: Add CSS styling for dual-panel layout with responsive design
- **NEW**: Add `generate_manifest.py` script to index available parsed verses
- **NEW**: Add `start_viewer.sh` for launching local HTTP server

### Architecture Improvements (vs initial prototype)

1. **Event Bus Pattern** (`mediator.js`)
   - Decoupled component communication via publish/subscribe
   - Components never call each other directly
   - Events: `verse:selected`, `chapter:loaded`, `colors:applied`, etc.

2. **Loading States**
   - Spinner/skeleton UI during data fetching
   - Visual feedback for all async operations

3. **Error Handling**
   - User-friendly error messages in UI (not just console)
   - Graceful degradation when API fails

4. **Caching Layer**
   - In-memory cache for API responses
   - Cache parsed files after first load
   - Reduces redundant network requests

5. **Strong's Dictionary Preview**
   - Click any SN tag to show Hebrew/Greek definition tooltip
   - Uses FHL dictionary API or local dictionary data

### Components

1. **Mediator** (`mediator.js`)
   - Central event hub for publish/subscribe communication
   - Event types: `verse:select`, `chapter:load`, `error:show`, etc.

2. **Data Loading** (`data_loader.js`)
   - Load `manifest.json` for verse availability
   - Fetch parsed output from local files
   - API fallback to FHL `bible.fhl.net` for UNV+SN source text
   - In-memory caching for performance

3. **Dual-Panel UI** (`left_panel.js`, `right_panel.js`)
   - Left panel: chapter verses with clickable selection
   - Right panel: parsed output with 3 collapsible sections
   - Color-coded SN groups synchronized across panels
   - Loading spinners during data fetch

4. **Navigation** (`navigation.js`)
   - Keyboard: Up/Down (verse), Left/Right (chapter), Home/End
   - URL hash: `#Gen/1/5` format for bookmarkable positions
   - localStorage persistence for session continuity

5. **Color Mapping** (`color_mapper.js`)
   - 15-color fixed palette for SN group visualization
   - Extract groups from parsed text section
   - Apply matching colors to raw UNV+SN text

6. **Strong's Dictionary** (`sn_dictionary.js`)
   - Tooltip display on SN click
   - Hebrew/Greek definitions from FHL or local data
   - Caches dictionary lookups

7. **Book Data** (`book_data.js`)
   - All 66 books with English/Chinese mappings
   - Chapter counts for navigation bounds

8. **UI Utilities** (`ui_utils.js`)
   - Loading spinner component
   - Error message display
   - Toast notifications

## Impact

- Affected specs: NEW `parsed-verse-viewer` capability
- Affected code:
  - `viewer/` — all new files
  - `generate_manifest.py` — new script at project root
  - `output/manifest.json` — generated index file
- No breaking changes to existing parsing functionality
