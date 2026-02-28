## 1. HTML Structure Changes
- [ ] 1.1 Remove "UNV+SN Text" h2 title from left panel header
- [ ] 1.2 Add UNV toggle button with id="toggle-unv" and class="toggle-btn version-toggle unv"
- [ ] 1.3 Add KJV toggle button with id="toggle-kjv" and class="toggle-btn version-toggle kjv"
- [ ] 1.4 Add UNV checkbox group (SN Dict + Single HL) with class="unv-controls"
- [ ] 1.5 Add KJV checkbox group (SN Dict + Single HL) with class="kjv-controls"
- [ ] 1.6 Restructure left panel content to support dual version display

## 2. CSS Styling
- [ ] 2.1 Add color variables for UNV (--unv-color: #3498db) and KJV (--kjv-color: #1abc9c)
- [ ] 2.2 Style UNV toggle button and checkbox labels with blue color
- [ ] 2.3 Style KJV toggle button and checkbox labels with teal color
- [ ] 2.4 Add active/inactive states for toggle buttons
- [ ] 2.5 Add conditional display rules for checkbox groups (hidden when toggle off)
- [ ] 2.6 Style stacked content sections for when both versions are active
- [ ] 2.7 Update CSS version in index.html for cache busting

## 3. Data Loader Enhancement
- [ ] 3.1 Add fetchKJVChapterFromAPI() method to data_loader.js
- [ ] 3.2 Add KJV cache (cache.kjvApiChapters)
- [ ] 3.3 Update DataLoader public API to expose KJV fetching

## 4. Left Panel JavaScript
- [ ] 4.1 Add state variables for UNV/KJV toggle (unvActive, kjvActive)
- [ ] 4.2 Add state variables for version-specific settings (unvSNDict, unvSingleHL, kjvSNDict, kjvSingleHL)
- [ ] 4.3 Initialize toggle button event listeners
- [ ] 4.4 Initialize checkbox event listeners for both version groups
- [ ] 4.5 Add renderUNVContent() function
- [ ] 4.6 Add renderKJVContent() function
- [ ] 4.7 Update handleChapterLoaded() to load both UNV and KJV data
- [ ] 4.8 Update handleColorsApply() to color SNs in both versions
- [ ] 4.9 Update highlighting functions to respect per-version Single HL settings
- [ ] 4.10 Add toggle visibility logic for checkbox groups
- [ ] 4.11 Update left panel JS version in index.html for cache busting

## 5. Highlight Timeout Change
- [ ] 5.1 Change HIGHLIGHT_TIMEOUT_MS from 10000 to 30000 in sn_dictionary.js
- [ ] 5.2 Update sn_dictionary.js version in index.html for cache busting

## 6. SN Dictionary Integration
- [ ] 6.1 Update SN Dict tooltip handling to work with both UNV and KJV panels
- [ ] 6.2 Ensure per-version SN Dict toggle controls tooltip display

## 7. Testing
- [ ] 7.1 Verify UNV toggle shows/hides UNV content and controls
- [ ] 7.2 Verify KJV toggle shows/hides KJV content and controls
- [ ] 7.3 Verify both versions can be shown simultaneously
- [ ] 7.4 Verify SN highlighting works across both versions
- [ ] 7.5 Verify per-version SN Dict toggles work independently
- [ ] 7.6 Verify per-version Single HL settings work independently
- [ ] 7.7 Verify 30-second highlight timeout works correctly
- [ ] 7.8 Verify color coding is consistent (blue for UNV, teal for KJV)
