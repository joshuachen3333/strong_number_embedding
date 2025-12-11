## 1. CSS Styling Updates
- [x] 1.1 Increase `.sn-dict-floating-tooltip` max-width from 280px to 400px
- [x] 1.2 Add max-height with overflow-y: auto for scrollable content
- [x] 1.3 Add `.tooltip-section` style for visual separation (border or divider)
- [x] 1.4 Add `.tooltip-pos` style for part of speech display
- [x] 1.5 Add `.tooltip-twot` style for TWOT reference
- [x] 1.6 Add `.tooltip-def-list` style for definition list container
- [x] 1.7 Add `.tooltip-def-item` and `.tooltip-subdef` styles for indented definitions
- [x] 1.8 Update CSS version query parameter for cache busting

## 2. Dictionary Extraction Functions
- [x] 2.1 Add `extractPartOfSpeech(dicText)` function to extract 詞性
- [x] 2.2 Add `extractTWOT(dicText)` function to extract TWOT reference
- [x] 2.3 Modify `extractDefinition(dicText)` to return full definitions array
- [x] 2.4 Update definition data structure to include new fields

## 3. Tooltip Rendering
- [x] 3.1 Update `showDefinitionTooltipForPanel()` to render new content sections
- [x] 3.2 Add divider/separator between header and definitions
- [x] 3.3 Render part of speech when available
- [x] 3.4 Render TWOT reference when available
- [x] 3.5 Render full definition list with proper indentation
- [x] 3.6 Update JS version query parameter for cache busting

## 4. Testing
- [x] 4.1 Test tooltip with Hebrew noun (e.g., 07225 רֵאשִׁית)
- [x] 4.2 Test tooltip with Hebrew verb (e.g., 01254 בָּרָא)
- [x] 4.3 Test tooltip with 09xxx prefix codes
- [x] 4.4 Test tooltip scrolling with long content
- [x] 4.5 Test tooltip positioning doesn't go off-screen
- [x] 4.6 Test left and right panel tooltips independently
