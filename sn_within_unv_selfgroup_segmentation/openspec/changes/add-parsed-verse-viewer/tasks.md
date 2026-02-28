# Implementation Tasks

## 1. Core Structure
- [ ] 1.1 Create `viewer/` directory structure
- [ ] 1.2 Create `viewer/index.html` with dual-panel layout
- [ ] 1.3 Create `viewer/css/styles.css` with all styling
- [ ] 1.4 Create `viewer/start_viewer.sh` launch script

## 2. Mediator Module (Event Bus)
- [ ] 2.1 Create `viewer/js/mediator.js`
- [ ] 2.2 Implement `subscribe(event, callback)` method
- [ ] 2.3 Implement `publish(event, data)` method
- [ ] 2.4 Implement `unsubscribe(event, callback)` method
- [ ] 2.5 Define event catalog constants

## 3. Book Data Module
- [ ] 3.1 Create `viewer/js/book_data.js` with 66 books
- [ ] 3.2 Include English/Chinese abbreviations (eng, chi)
- [ ] 3.3 Include long names (chiLong, engLong)
- [ ] 3.4 Include chapter counts
- [ ] 3.5 Create lookup maps (BOOK_MAP_ENG, BOOK_MAP_CHI)

## 4. UI Utilities Module
- [ ] 4.1 Create `viewer/js/ui_utils.js`
- [ ] 4.2 Implement `showSpinner(container)` function
- [ ] 4.3 Implement `hideSpinner(container)` function
- [ ] 4.4 Implement `showError(message, type)` function (banner, toast)
- [ ] 4.5 Implement `showToast(message, duration)` function
- [ ] 4.6 Add CSS for spinner animation and toast styles

## 5. Data Loader Module (with Caching)
- [ ] 5.1 Create `viewer/js/data_loader.js`
- [ ] 5.2 Implement in-memory cache object
- [ ] 5.3 Implement `loadManifest()` with caching
- [ ] 5.4 Implement `hasBookData()` and `getChapters()` helpers
- [ ] 5.5 Implement `loadParsedVerse()` with cache check
- [ ] 5.6 Implement `fetchChapterFromAPI()` with caching
- [ ] 5.7 Implement `parseSections()` to extract 3 sections
- [ ] 5.8 Subscribe to `loading:start/end` events for fetch operations

## 6. Color Mapper Module
- [ ] 6.1 Create `viewer/js/color_mapper.js`
- [ ] 6.2 Define 15-color GROUP_COLORS palette
- [ ] 6.3 Implement `parseGroups()` to extract SN groups
- [ ] 6.4 Implement `createSNToColorMap()` for SN-to-color mapping
- [ ] 6.5 Implement `applyColorsToRawText()` for left panel
- [ ] 6.6 Implement `applyColorsToParsedText()` for right panel
- [ ] 6.7 Publish `colors:apply` event when colors assigned

## 7. Strong's Dictionary Module
- [ ] 7.1 Create `viewer/js/sn_dictionary.js`
- [ ] 7.2 Implement dictionary cache
- [ ] 7.3 Implement `fetchDefinition(snCode)` (local → API fallback)
- [ ] 7.4 Implement `showTooltip(element, snCode)` function
- [ ] 7.5 Implement `hideTooltip()` function
- [ ] 7.6 Add CSS for tooltip styling
- [ ] 7.7 Handle click events on SN tags (event delegation)
- [ ] 7.8 Handle click-outside to close tooltip

## 8. Left Panel Module
- [ ] 8.1 Create `viewer/js/left_panel.js`
- [ ] 8.2 Subscribe to `chapter:loaded` event
- [ ] 8.3 Implement `renderChapter()` with loading spinner
- [ ] 8.4 Implement `selectVerse()` with highlighting
- [ ] 8.5 Subscribe to `colors:apply` event
- [ ] 8.6 Add uncertain verse indicator (orange border)
- [ ] 8.7 Publish `verse:select` on click
- [ ] 8.8 Wire up SN tag click to dictionary tooltip

## 9. Right Panel Module
- [ ] 9.1 Create `viewer/js/right_panel.js`
- [ ] 9.2 Implement `initToggleButtons()` for section toggles
- [ ] 9.3 Subscribe to `verse:selected` event
- [ ] 9.4 Implement `displayParsedVerse()` with loading state
- [ ] 9.5 Implement `displayNotParsed()` for missing verses
- [ ] 9.6 Add uncertain verse styling (yellow background, warning)
- [ ] 9.7 Implement color-coded group display
- [ ] 9.8 Wire up SN tag click to dictionary tooltip

## 10. Navigation Module
- [ ] 10.1 Create `viewer/js/navigation.js`
- [ ] 10.2 Implement keyboard handler (arrows, Home, End)
- [ ] 10.3 Publish `verse:select` or `chapter:load` on key press
- [ ] 10.4 Implement chapter/book boundary crossing
- [ ] 10.5 Implement URL hash update and parsing
- [ ] 10.6 Subscribe to `verse:selected` to update hash
- [ ] 10.7 Implement localStorage save/load position

## 11. App Controller
- [ ] 11.1 Create `viewer/js/app.js`
- [ ] 11.2 Initialize Mediator
- [ ] 11.3 Subscribe to `verse:select` and orchestrate loading
- [ ] 11.4 Subscribe to `chapter:load` and orchestrate
- [ ] 11.5 Subscribe to `error:show` and display errors
- [ ] 11.6 Implement `init()` with load sequence
- [ ] 11.7 Populate book/chapter dropdowns
- [ ] 11.8 Wire up dropdown change to publish events

## 12. Manifest Generator
- [ ] 12.1 Create `generate_manifest.py` at project root
- [ ] 12.2 Scan `output/` directory structure
- [ ] 12.3 Handle uncertain files (`{verse}_uncertain`)
- [ ] 12.4 Output `output/manifest.json` with proper format
- [ ] 12.5 Print summary statistics

## 13. Testing with Chrome DevTools MCP
- [ ] 13.1 Start viewer with `start_viewer.sh`
- [ ] 13.2 Test initial load (Genesis 1:1 default)
- [ ] 13.3 Test verse selection via click
- [ ] 13.4 Test color synchronization between panels
- [ ] 13.5 Test keyboard navigation (arrows, Home, End)
- [ ] 13.6 Test chapter boundary crossing
- [ ] 13.7 Test URL hash (refresh with #Gen/1/5)
- [ ] 13.8 Test localStorage persistence
- [ ] 13.9 Test loading spinners appear during fetch
- [ ] 13.10 Test error display on network failure
- [ ] 13.11 Test Strong's dictionary tooltip on SN click
- [ ] 13.12 Test toggle buttons for sections
- [ ] 13.13 Test uncertain verse display
- [ ] 13.14 Test responsive layout (resize viewport)
