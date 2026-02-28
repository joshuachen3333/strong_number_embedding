# Implementation Tasks

## 1. CSS Styling

- [x] 1.1 Add `.clicked-local` class for deep blue highlighting
  - Background: #1e88e5
  - Text color: white
  - Font weight: bold

- [x] 1.2 Add `.clicked-remote` class for orange highlighting
  - Background: #ff9800
  - Text color: white
  - Font weight: bold

## 2. Event System Enhancement

- [x] 2.1 Extend SN_CLICK event payload
  - Add `source` field: 'left' | 'right-parsed' | 'right-raw'
  - Add `groupSNs` field: array of all SNs in the clicked group
  - Maintain existing `element` and `snCode` fields for backwards compatibility

## 3. Left Panel Highlighting

- [x] 3.1 Subscribe to SN_CLICK event in left_panel.js
  - Handle clicks from own panel (source='left')
  - Handle clicks from right panels (source='right-*')

- [x] 3.2 Implement clearHighlighting() function
  - Remove all `.clicked-local` and `.clicked-remote` classes

- [x] 3.3 Implement highlightLocal() function
  - Apply `.clicked-local` to clicked SN tag(s)
  - Find and highlight all instances of same SN in current verse

- [x] 3.4 Implement highlightRemote() function
  - Apply `.clicked-remote` to corresponding SN tag(s)
  - Use groupSNs from event payload to find all related SNs

- [x] 3.5 Update SN_CLICK publisher to include source='left'

## 4. Right Panel Parsed Section Highlighting

- [x] 4.1 Add click handlers to `.sn-group` elements in Parsed section
  - Currently only Raw section has click handlers
  - Extract SN codes from clicked group
  - Publish SN_CLICK with source='right-parsed'

- [x] 4.2 Subscribe to SN_CLICK event in right_panel.js
  - Handle clicks from own sections
  - Handle clicks from left panel

- [x] 4.3 Implement clearHighlighting() for right panel
  - Clear both Parsed and Raw sections

- [x] 4.4 Implement highlightParsedLocal() function
  - Apply `.clicked-local` to clicked Parsed section group
  - Also highlight corresponding Raw section groups (blue)

- [x] 4.5 Implement highlightParsedRemote() function
  - Apply `.clicked-remote` to Parsed section groups
  - Also highlight corresponding Raw section groups (orange)

## 5. Right Panel Raw Section Highlighting

- [x] 5.1 Update existing click handlers in Raw section
  - Add source='right-raw' to SN_CLICK event
  - Include all SNs in the semantic group

- [x] 5.2 Implement highlightRawLocal() function
  - Apply `.clicked-local` to clicked Raw section tag(s)
  - Also highlight corresponding Parsed section groups (blue)

- [x] 5.3 Implement highlightRawRemote() function
  - Apply `.clicked-remote` to Raw section tag(s)
  - Also highlight corresponding Parsed section groups (orange)

## 6. Group Mapping Logic

- [x] 6.1 Create getSNGroupFromColorMap() utility
  - Input: single SN code, colorMap, groups
  - Output: array of all SNs in same semantic group
  - Use existing color_mapper.js parseGroups() data

- [x] 6.2 Create findCorrespondingElements() utility
  - Input: array of SN codes, target section
  - Output: array of DOM elements matching those SNs
  - Handle both `.sn-tag` (Raw/Left) and `.sn-group` (Parsed)

## 7. Click-Away Handling

- [x] 7.1 Add global click handler to clear highlighting
  - Listen for clicks outside SN elements
  - Call clearHighlighting() in all panels

- [x] 7.2 Clear highlighting on verse change
  - Subscribe to VERSE_SELECTED event
  - Clear highlighting before displaying new verse

## 8. Testing

- [ ] 8.1 Test left panel → right panels highlighting
  - Click SN in left panel
  - Verify left panel shows blue
  - Verify right Parsed and Raw show orange
  - Verify correct SNs are highlighted (use colorMap grouping)

- [ ] 8.2 Test right Parsed → other panels highlighting
  - Click SN group in right Parsed section
  - Verify right Parsed and Raw show blue
  - Verify left panel shows orange

- [ ] 8.3 Test right Raw → other panels highlighting
  - Click SN tag in right Raw section
  - Verify right Raw and Parsed show blue
  - Verify left panel shows orange

- [ ] 8.4 Test with repeated SNs (e.g., Gen 1:4 with <0216>)
  - Verify all instances of same SN are highlighted together
  - Verify "first occurrence wins" color strategy works correctly

- [ ] 8.5 Test click-away behavior
  - Click SN to highlight
  - Click elsewhere in page
  - Verify highlighting clears

- [ ] 8.6 Test verse navigation
  - Click SN in Gen 1:4
  - Navigate to Gen 1:5
  - Verify highlighting cleared in new verse

- [ ] 8.7 Test dictionary tooltip compatibility
  - Click SN to highlight
  - Verify dictionary tooltip still appears
  - Verify both features work together without conflicts

## 9. Documentation

- [ ] 9.1 Update viewer README with highlighting feature
- [ ] 9.2 Add comments in code explaining highlighting logic
- [ ] 9.3 Document color scheme and UX rationale

## Dependencies

- Task 2 must complete before tasks 3-5 (event payload changes needed first)
- Task 6 must complete before tasks 3-5 (utilities needed for group mapping)
- Tasks 3-5 can be done in parallel after dependencies met
- Task 7 depends on tasks 3-5 being complete
- Task 8 depends on all implementation tasks being complete
