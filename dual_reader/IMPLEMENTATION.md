# Implementation Details: Dual Synchronized Bible Reader

This document provides details on the implementation of the Dual Synchronized Bible Reader, focusing on its file structure, key JavaScript functions, and how data is handled and rendered.

## 1. File Structure

The application is organized into the following file structure, with all relevant files for this dual reader application residing under the `dual_reader/` directory:

```
.
└── dual_reader/
    ├── index.html                  # Main HTML page hosting both readers
    ├── DESIGN.md                   # Software Design Document
    ├── IMPLEMENTATION.md           # This Implementation Details Document
    ├── USER_GUIDE.md               # User Guide
    ├── css/
    │   └── style.css               # Basic CSS for styling
    └── js/
        ├── mock_mediator.js        # Simulates the backend mediator and API
        ├── main_reader_frontend.js # JavaScript for the Main Reader component
        ├── second_reader_frontend.js# JavaScript for the Second Reader component
        └── app.js                  # Main application script (initialization)
```

The rest of the document refers to files like `js/mock_mediator.js`. These paths are now implicitly relative to the `dual_reader/` directory if one considers `dual_reader/` as the project root for this specific application part. For clarity within this document, references like "js/mock_mediator.js" mean `dual_reader/js/mock_mediator.js` in the overall repository.

## 2. Core JavaScript Components

### 2.1. `js/mock_mediator.js`

*   **Purpose:** Simulates a backend mediator service. This is crucial for frontend development without a live backend. It manages the overall synchronization state and simulates API responses for Bible content.
*   **Key Object:** `mockMediator` (global or module)
    *   `_currentSynchedVerse`: Stores the current passage (`{ book, chapter, verse }`) that the Main Reader is focused on.
    *   `_secondReaderUpdateFn`: A callback function registered by the Second Reader to receive updates.
    *   `_bookDataCache`: A simple object to cache chapter data, reducing redundant mock data generation.
    *   **`fetchChapter(book, chapter, version, strong)`:**
        *   Simulates `GET /api/chapter`.
        *   Constructs a mock JSON response mimicking the structure of `bible.fhl.net/json/qb.php` (as transformed by the mediator).
        *   Includes verse text with embedded Strong's number tags (e.g., `{<WG1722>}`).
        *   Uses the `_bookDataCache` to return cached data if available.
    *   **`syncPosition(payload)`:**
        *   Simulates `POST /api/sync`.
        *   Updates `_currentSynchedVerse`.
        *   If `_secondReaderUpdateFn` is registered, it calls this function with the new `book`, `chapter`, and `verse`, effectively notifying the Second Reader.
    *   **`fetchStrongDefinition(strongId)`:**
        *   Simulates `GET /api/strong_definition`.
        *   Returns a mock JSON response for a Strong's number definition (mimicking `bible.fhl.net/json/sd.php` output).
    *   **`registerSecondReaderUpdateCallback(callback)`:** Allows `second_reader_frontend.js` to provide its main update function to the mediator.

### 2.2. `js/main_reader_frontend.js`

*   **Purpose:** Manages the Main Bible Reader interface and its interactions.
*   **Initialization (`DOMContentLoaded`):**
    *   Gets references to DOM elements (content area, book/chapter selectors).
    *   Populates book selection dropdown (example uses a static list).
    *   Attaches event listeners to the "Load Chapter" button and the content area's scroll event.
    *   Calls `initialLoad()` to load a default chapter.
*   **`fetchChapterFromMediator(book, chapter, version, strong)`:**
    *   Calls `mockMediator.fetchChapter()` to get chapter data.
*   **`renderChapter(apiResponse)`:**
    *   Clears previous content from `#main-reader-content-area`.
    *   Iterates through `apiResponse.data.verses`.
    *   For each verse, creates a `div.verse-block` with:
        *   A unique `id` (e.g., `main-verse-Luke-12-1`).
        *   `data-book`, `data-chapter`, `data-verse` attributes.
        *   A `span.verse-number` and `span.verse-text`.
        *   The `verse.text` (containing Strong's tags) is directly inserted into `span.verse-text`.
*   **`getTopmostVerseReference()`:**
    *   Attached to the scroll event of `#main-reader-content-area`.
    *   Calculates which `div.verse-block` is currently most visible at the top of the scrollable area by checking `getBoundingClientRect()`.
    *   Returns an object `{ book, chapter, verse }` based on the `data-*` attributes of that element.
*   **`handleScroll()`:**
    *   Debounces the scroll event.
    *   Calls `getTopmostVerseReference()`.
    *   If a new verse is identified, calls `syncPositionWithMediator()`.
*   **`syncPositionWithMediator(book, chapter, verse)`:**
    *   Calls `mockMediator.syncPosition()` to report the Main Reader's current state.
*   **`initialLoad()`:**
    *   Loads a default chapter (e.g., Luke 12) upon page load.
    *   Calls `syncPositionWithMediator()` after the first render to initialize synchronization.

### 2.3. `js/second_reader_frontend.js`

*   **Purpose:** Manages the Second Bible Reader, keeping it synchronized with the Main Reader while allowing independent display settings.
*   **Initialization (`DOMContentLoaded`):**
    *   Gets references to its DOM elements (content area, version select, Strong's toggle).
    *   Attaches event listeners to its version and Strong's number controls.
    *   Registers its main update function (`loadPassage`) with the `mockMediator` using `mockMediator.registerSecondReaderUpdateCallback(loadPassage)`.
*   **`loadPassage(book, chapter, verseToScrollTo)`:**
    *   This is the core update function, called by the `mockMediator` when synchronization is needed.
    *   Stores `book`, `chapter`, `verseToScrollTo` internally for context (e.g., if user changes version, it reloads the same passage).
    *   Reads the current `version` and `strong` settings from its own UI controls.
    *   Calls `fetchChapterFromMediator(book, chapter, selectedVersion, strongEnabled)`.
*   **`fetchChapterFromMediator(book, chapter, version, strong)`:**
    *   Calls `mockMediator.fetchChapter()` to get its specific view of the chapter data.
*   **`renderChapterForSecondReader(apiResponse)`:**
    *   Similar to the Main Reader's render function.
    *   Clears its `#second-reader-content-area`.
    *   Renders verses into `div.verse-block` elements with unique IDs (e.g., `second-reader-verse-Luke-12-1`).
    *   The `verse.text` (with Strong's tags) is rendered directly.
*   **`scrollToVerse(book, chapter, verse)`:**
    *   Calculates the position of the target verse `div` within `#second-reader-content-area`.
    *   Sets `scrollTop` of the content area to bring the verse into view.
    *   Optionally applies a highlighting class (`.verse-highlighted`) to the target verse.
*   **Event Listeners for UI Controls:**
    *   When the version or Strong's toggle changes, `loadPassage` is called with the stored `currentBookToDisplay`, `currentChapterToDisplay`, and `currentVerseToHighlight` to reload the content with the new settings.

### 2.4. `js/app.js`

*   **Purpose:** General application initialization.
*   **Current Implementation:**
    *   May be minimal, primarily ensuring the other scripts are loaded and perhaps logging an "App initialized" message.
    *   Could be used to explicitly instantiate or make `mockMediator` globally available if not done directly in `mock_mediator.js`. (The current design implies `mockMediator` is a global object for simplicity).

## 3. Content Rendering and Strong's Numbers

*   Both readers fetch chapter data as structured JSON from the Mock Mediator. This data is expected to be similar to the `qb.php` output, where each verse object has a `text` field.
*   The `text` field contains the Bible verse mixed with Strong's number tags directly from the `fhl.net` API (e.g., `{<WG1722>}word<WGXYZ>...`).
*   **Current Rendering:** These tags are rendered as literal text as part of the verse. For example, the user will see `{<WG1722>}` in the output.
*   **Future Enhancement (Clickable Strong's):** To make Strong's numbers interactive:
    1.  The `renderChapter` functions in each reader would need to parse the `verse.text`.
    2.  Replace tags like `{<WG1722>}` with HTML elements (e.g., `<span class="strong-tag" data-strong-id="G1722">{G1722}</span>`).
    3.  Attach click event listeners to these elements.
    4.  On click, call a function like `mockMediator.fetchStrongDefinition(strongId)`.
    5.  Display the returned definition in a UI element (popup, panel).

## 4. Synchronization Mechanism (Same-Page)

1.  The Second Reader registers its `loadPassage` function with the `mockMediator`.
2.  When the Main Reader scrolls, it determines the new active verse and calls `mockMediator.syncPosition()`.
3.  `mockMediator.syncPosition()` updates its internal current verse and then directly calls the Second Reader's registered `loadPassage` function with the new `book`, `chapter`, and `verse`.
4.  The Second Reader then fetches this passage (with its own display settings) and updates its view.

This provides a decoupled way for components to communicate on the same page, orchestrated by the `mockMediator`.
```
