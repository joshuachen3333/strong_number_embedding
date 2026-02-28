# Parsed Verse Viewer Specification

## ADDED Requirements

### Requirement: Event-Driven Architecture
The viewer SHALL use a Mediator pattern for component communication, where components publish and subscribe to events without direct references to each other.

#### Scenario: Component communication via events
- **WHEN** user clicks a verse in left panel
- **THEN** left panel publishes `verse:select` event with `{book, chapter, verse}`
- **AND** app controller subscribes and triggers data loading
- **AND** right panel subscribes and updates display

#### Scenario: Event catalog
- **WHEN** the mediator is initialized
- **THEN** it supports these event types:
  - `verse:select` — user selects a verse
  - `verse:selected` — verse data loaded and displayed
  - `chapter:load` — request to load a chapter
  - `chapter:loaded` — chapter data ready
  - `colors:apply` — apply color map to panels
  - `error:show` — display error message
  - `loading:start` / `loading:end` — toggle loading state

### Requirement: Dual-Panel Layout
The viewer SHALL display a dual-panel interface with a left panel showing UNV+SN chapter text and a right panel showing parsed output for the selected verse.

#### Scenario: Initial load with default position
- **WHEN** the viewer loads without URL hash or localStorage data
- **THEN** the left panel displays Genesis chapter 1 verses
- **AND** verse 1 is selected by default
- **AND** the right panel shows parsed output for Genesis 1:1 (if available)

#### Scenario: Load from URL hash
- **WHEN** the viewer loads with URL hash `#Gen/1/5`
- **THEN** book dropdown shows "Genesis"
- **AND** chapter dropdown shows "1"
- **AND** left panel displays Genesis chapter 1
- **AND** verse 5 is selected and highlighted

### Requirement: Manifest-Driven Navigation
The viewer SHALL use `manifest.json` to determine available books, chapters, and verses.

#### Scenario: Book dropdown population
- **WHEN** manifest is loaded successfully
- **THEN** book dropdown shows all 66 Bible books
- **AND** books with parsed data are enabled
- **AND** books without parsed data are disabled (grayed out with "[無資料]")

#### Scenario: Chapter dropdown updates
- **WHEN** user selects a book from dropdown
- **THEN** chapter dropdown populates with chapters that have parsed verses
- **AND** first available chapter is auto-selected

### Requirement: Verse Selection
The viewer SHALL allow users to select verses via click and display corresponding parsed output.

#### Scenario: Click verse to select
- **WHEN** user clicks on any verse text in left panel
- **THEN** that verse becomes selected (highlighted with blue background and left border)
- **AND** right panel updates to show parsed output for that verse
- **AND** URL hash updates to reflect new position

#### Scenario: Select unparsed verse
- **WHEN** user selects a verse that has no parsed output file
- **THEN** right panel shows "此節尚未解析 / Not yet parsed" message
- **AND** verse reference is displayed (e.g., "Gen 1:10")

### Requirement: Parsed Output Display
The viewer SHALL display parsed output in three collapsible sections.

#### Scenario: Display parsed verse with all sections
- **WHEN** parsed output file contains all three sections
- **THEN** right panel shows "Parsed and Formatted Text Section" with SN groups
- **AND** right panel shows "Raw UNV+SN Source Text Section"
- **AND** right panel shows "Morphology Notes Section" with *1, *2 notes

#### Scenario: Toggle section visibility
- **WHEN** user clicks "Parsed" toggle button
- **THEN** Parsed and Formatted Text Section hides/shows
- **AND** button visual state toggles between active (blue) and inactive

### Requirement: Color-Coded SN Groups
The viewer SHALL apply synchronized color highlighting to SN groups across both panels.

#### Scenario: Color mapping from parsed text
- **WHEN** a verse is selected with parsed output
- **THEN** each SN group line gets a distinct background color from 15-color palette
- **AND** the same color is applied to matching SN tags in left panel raw text
- **AND** colors cycle if more than 15 groups exist

#### Scenario: Color applied to raw text
- **WHEN** left panel displays UNV+SN text with tags like `<WH07225>`
- **THEN** tags matching the current verse's groups are highlighted
- **AND** tag highlighting uses the same color as corresponding parsed line

### Requirement: Keyboard Navigation
The viewer SHALL support keyboard shortcuts for efficient verse traversal.

#### Scenario: Navigate with arrow keys
- **WHEN** user presses Down arrow
- **THEN** next verse in chapter is selected
- **WHEN** user presses Up arrow
- **THEN** previous verse in chapter is selected

#### Scenario: Chapter boundary crossing with Down arrow
- **WHEN** user is at last verse of chapter (e.g., Gen 1:31)
- **AND** presses Down arrow
- **THEN** viewer loads next chapter (Gen 2)
- **AND** first verse (Gen 2:1) is selected

#### Scenario: Left/Right chapter navigation
- **WHEN** user presses Right arrow
- **THEN** next chapter loads with first verse selected
- **WHEN** user presses Left arrow
- **THEN** previous chapter loads with first verse selected

#### Scenario: Home and End keys
- **WHEN** user presses Home key
- **THEN** first verse of current chapter is selected
- **WHEN** user presses End key
- **THEN** last verse of current chapter is selected

### Requirement: Uncertain Verse Indication
The viewer SHALL visually distinguish uncertain verses requiring review.

#### Scenario: Display uncertain verse in left panel
- **WHEN** manifest indicates verse has `_uncertain` file
- **THEN** verse in left panel has orange left border indicator

#### Scenario: Display uncertain parsed output
- **WHEN** user selects an uncertain verse
- **THEN** right panel has yellow background
- **AND** warning badge "Uncertain" is displayed in panel header
- **AND** warning message explains uncertainty at top of content

### Requirement: Position Persistence
The viewer SHALL save and restore user position across sessions.

#### Scenario: Save position to localStorage
- **WHEN** user selects a verse
- **THEN** position is saved to localStorage key `parsedViewerLastPosition`
- **AND** stored as JSON: `{"book": "Gen", "chapter": 1, "verse": 5}`

#### Scenario: Restore position on reload
- **WHEN** viewer loads without URL hash
- **AND** localStorage has saved position
- **THEN** viewer navigates to saved position

### Requirement: Loading States
The viewer SHALL display visual feedback during async operations.

#### Scenario: Show loading spinner during chapter load
- **WHEN** user selects a new chapter
- **THEN** left panel shows spinner overlay
- **AND** spinner disappears when data is ready

#### Scenario: Show loading state during verse load
- **WHEN** user selects a verse
- **THEN** right panel shows skeleton/loading indicator
- **AND** content appears when parsed output is loaded

#### Scenario: Show loading during API fallback
- **WHEN** local file is missing and API fetch starts
- **THEN** loading indicator remains visible
- **AND** disappears only after API response received

### Requirement: Error Handling
The viewer SHALL display user-friendly error messages in the UI.

#### Scenario: Manifest load failure
- **WHEN** manifest.json fails to load
- **THEN** error banner appears at top of page
- **AND** message explains: "無法載入清單檔案，請確認 manifest.json 存在"
- **AND** navigation is disabled

#### Scenario: API fallback failure
- **WHEN** both local file and API fallback fail
- **THEN** verse text shows error message instead of content
- **AND** message: "無法載入經文資料"

#### Scenario: Network error during operation
- **WHEN** network error occurs during any fetch
- **THEN** toast notification appears briefly
- **AND** error is logged for debugging

### Requirement: Data Caching
The viewer SHALL cache fetched data in memory to reduce redundant requests.

#### Scenario: Cache parsed verse files
- **WHEN** a parsed verse file is loaded
- **THEN** content is stored in memory cache
- **AND** subsequent requests for same verse use cache

#### Scenario: Cache API responses
- **WHEN** chapter is fetched from FHL API
- **THEN** response is cached by book+chapter key
- **AND** navigating back to same chapter uses cache

#### Scenario: Cache dictionary lookups
- **WHEN** Strong's definition is fetched
- **THEN** result is cached by SN code
- **AND** same SN lookup returns cached result

### Requirement: Strong's Dictionary Preview
The viewer SHALL display Hebrew/Greek definitions when user clicks on a Strong's Number.

#### Scenario: Click SN tag to show tooltip
- **WHEN** user clicks on a Strong's Number tag (e.g., `<WH07225>`)
- **THEN** tooltip appears near the clicked element
- **AND** tooltip shows: SN code, Hebrew/Greek word, transliteration, definition

#### Scenario: Tooltip content format
- **WHEN** tooltip displays for Hebrew SN (H-prefix, 1-8999)
- **THEN** shows Hebrew characters and definition
- **WHEN** tooltip displays for Greek SN (G-prefix)
- **THEN** shows Greek characters and definition

#### Scenario: Close tooltip
- **WHEN** user clicks outside tooltip
- **THEN** tooltip closes
- **WHEN** user clicks another SN tag
- **THEN** previous tooltip closes and new one opens

#### Scenario: Dictionary data source
- **WHEN** dictionary data is needed
- **THEN** viewer first checks local JSON files in `strong_dict_json/`
- **AND** falls back to FHL API if local not available

### Requirement: API Fallback for UNV Text
The viewer SHALL fetch UNV+SN text from FHL API when local data is incomplete.

#### Scenario: Load chapter with mixed data
- **WHEN** chapter has some parsed verses and some not
- **THEN** parsed verses show raw text from parsed output Section 2
- **AND** unparsed verses fetch from FHL API `bible.fhl.net/json/qb.php`

#### Scenario: API fallback format
- **WHEN** fetching from API for book "Gen" chapter 1
- **THEN** request uses Chinese abbreviation: `chineses=創`
- **AND** includes parameters: `version=unv&strong=1`

### Requirement: Manifest Generation
The system SHALL provide a script to generate `manifest.json` from output directory.

#### Scenario: Generate manifest from output
- **WHEN** running `python generate_manifest.py`
- **THEN** script scans `output/` directory structure
- **AND** creates `output/manifest.json` with books, chapters, verses, and uncertain lists
- **AND** outputs summary: book count and total verse count

#### Scenario: Manifest format
- **WHEN** manifest is generated for a chapter with uncertain verses
- **THEN** JSON structure includes:
  - `generated`: ISO timestamp
  - `books.{Book}.chapters.{Chapter}.verses`: array of verse numbers
  - `books.{Book}.chapters.{Chapter}.uncertain`: array of uncertain verse numbers

### Requirement: Launch Script
The system SHALL provide a convenient script to start the viewer.

#### Scenario: Start viewer with script
- **WHEN** running `./start_viewer.sh` from viewer directory
- **THEN** Python HTTP server starts on port 8000 (or uses existing)
- **AND** browser opens to `http://localhost:8000/viewer/`

#### Scenario: Port already in use
- **WHEN** port 8000 is already in use
- **THEN** script detects this and opens browser without starting new server
- **AND** displays informative message
