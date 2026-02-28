# Specification: SN Click Highlighting

## ADDED Requirements

### Requirement: Visual feedback for clicked Strong's Numbers

When a user clicks on any Strong's Number (SN) element in viewer_v2, the system SHALL provide immediate visual feedback by highlighting both the clicked element and its corresponding elements in other panels using a consistent color scheme.

#### Scenario: User clicks SN in left panel

**Given** the user is viewing Gen 1:4 which contains `{<WH0853>}光<WH0216>`

**When** the user clicks on `<WH0216>` in the left panel

**Then** the system SHALL:
- Apply deep blue highlighting (#1e88e5) to the clicked `<WH0216>` element in left panel
- Apply deep blue highlighting to any other instances of `<WH0216>` in the left panel (e.g., second occurrence)
- Apply orange highlighting (#ff9800) to `{<WH0853>}<WH0216>` group in right Parsed section
- Apply orange highlighting to all `<WH0216>` tags in right Raw section

**And** all highlighted elements SHALL have white text color and bold font weight

**And** the dictionary tooltip for `<WH0216>` SHALL still appear

#### Scenario: User clicks SN group in right Parsed section

**Given** the user is viewing Gen 1:2 which contains `{<WAH05921>}<WH06440>` in Parsed section

**When** the user clicks on the `{<WAH05921>}<WH06440>` group element

**Then** the system SHALL:
- Apply deep blue highlighting to the clicked group in right Parsed section
- Apply deep blue highlighting to all `<WAH05921>` and `<WH06440>` tags in right Raw section
- Apply orange highlighting to all `<WAH05921>` and `<WH06440>` tags in left panel

**And** if the same SNs appear multiple times in Raw section or left panel, all instances SHALL be highlighted

#### Scenario: User clicks SN tag in right Raw section

**Given** the user is viewing Gen 1:1 which contains `<WAH09002><WH07225>` in Raw section

**When** the user clicks on `<WH07225>` tag in right Raw section

**Then** the system SHALL:
- Apply deep blue highlighting to clicked `<WH07225>` and related `<WAH09002>` tags in right Raw section
- Apply deep blue highlighting to corresponding `<WAH09002><WH07225>` group in right Parsed section
- Apply orange highlighting to all `<WAH09002>` and `<WH07225>` tags in left panel

**And** the system SHALL identify related SNs using the color grouping from Parsed section

### Requirement: Semantic group identification

The system SHALL identify all Strong's Numbers belonging to the same semantic group and highlight them together, using the existing colorMap and groups data structures from color_mapper.js.

#### Scenario: Identifying group members from clicked SN

**Given** the colorMap contains `{'0853': '#E8F5E9', '0216': '#E8F5E9'}`

**And** the groups array contains `{ groupIndex: 2, sns: ['0853', '0216'], text: '{<WH0853>}<WH0216>...' }`

**When** the user clicks on SN `0216`

**Then** the system SHALL identify that SNs `['0853', '0216']` belong to the same group

**And** the system SHALL highlight all elements containing either `0853` or `0216` in the target panel

#### Scenario: Handling repeated SNs with first-occurrence color strategy

**Given** Gen 1:4 contains `<0216>` in two different groups:
- Group 2: `{<0853>}<0216>` (color #E8F5E9)
- Group 7: `<0216>` (color #EFEBE9)

**And** the colorMap uses "first occurrence wins" strategy, assigning `0216` → #E8F5E9

**When** the user clicks any `<0216>` element

**Then** the system SHALL use Group 2's SNs `['0853', '0216']` for highlighting

**And** both occurrences of `<0216>` SHALL be highlighted together

### Requirement: Highlight clearing

The system SHALL provide mechanisms to clear highlighting when the user's focus changes or context switches.

#### Scenario: Click away to clear highlighting

**Given** SN `<WH0430>` is currently highlighted with deep blue in left panel

**When** the user clicks on any non-SN element (Chinese text, whitespace, or background)

**Then** the system SHALL remove all `.clicked-local` and `.clicked-remote` classes

**And** all previously highlighted elements SHALL return to their original color-grouped background colors

#### Scenario: Verse navigation clears highlighting

**Given** SN `<WH0216>` is highlighted in Gen 1:4

**When** the user navigates to Gen 1:5 by clicking verse 5 in left panel

**Then** the system SHALL clear all highlighting before displaying Gen 1:5

**And** no highlighting SHALL remain from the previous verse

#### Scenario: Clicking different SN replaces highlighting

**Given** SN `<WH0430>` is currently highlighted

**When** the user clicks on a different SN `<WH0216>`

**Then** the system SHALL:
- Remove highlighting from `<WH0430>` and its corresponding elements
- Apply highlighting to `<WH0216>` and its corresponding elements

**And** only one SN group SHALL be highlighted at any time

### Requirement: Event system integration

The system SHALL extend the existing SN_CLICK event to include source panel information and semantic group data needed for bidirectional highlighting.

#### Scenario: Publishing SN_CLICK event from left panel

**Given** the user clicks `<WH0216>` in left panel

**And** the semantic group for `0216` is `['0853', '0216']`

**When** the left panel publishes the SN_CLICK event

**Then** the event payload SHALL include:
```javascript
{
  source: 'left',
  snCode: '0216',
  groupSNs: ['0853', '0216'],
  element: <DOM reference>
}
```

**And** all subscribers (left_panel, right_panel, sn_dictionary) SHALL receive the event

#### Scenario: Publishing SN_CLICK event from right Parsed section

**Given** the user clicks `{<WAH05921>}<WH06440>` group in right Parsed section

**When** the right panel publishes the SN_CLICK event

**Then** the event payload SHALL include:
```javascript
{
  source: 'right-parsed',
  snCode: '06440',          // primary SN
  groupSNs: ['05921', '06440'],
  element: <DOM reference>
}
```

#### Scenario: Publishing SN_CLICK event from right Raw section

**Given** the user clicks `<WH07225>` tag in right Raw section

**When** the right panel publishes the SN_CLICK event

**Then** the event payload SHALL include:
```javascript
{
  source: 'right-raw',
  snCode: '07225',
  groupSNs: ['09002', '07225'],  // identified from colorMap
  element: <DOM reference>
}
```

### Requirement: Click handler for Parsed section

The system SHALL add click event handlers to SN group elements in the right Parsed section, which currently lack such handlers.

#### Scenario: Making Parsed section groups clickable

**Given** the right Parsed section contains `<span class="sn-group"><WH0430></span>`

**When** the Parsed section is rendered

**Then** the system SHALL attach click event handlers to all `.sn-group` elements

**And** clicking a group SHALL:
- Extract all SN codes from the group's text content
- Publish SN_CLICK event with source='right-parsed'
- Show dictionary tooltip for the primary (first) SN

### Requirement: Backward compatibility

The system SHALL maintain backward compatibility with the existing dictionary tooltip feature which also subscribes to SN_CLICK events.

#### Scenario: Dictionary tooltip continues to work with highlighting

**Given** the user clicks `<WH0430>` in left panel

**When** the SN_CLICK event is published

**Then** the highlighting system SHALL apply appropriate color classes

**And** the dictionary system SHALL display the tooltip for `<WH0430>`

**And** both features SHALL work simultaneously without conflicts

## Design Constraints

1. **Color Scheme**: Deep blue (#1e88e5) for local, orange (#ff9800) for remote - matching dual_reader_right_editor
2. **Single Selection**: Only one SN group can be highlighted at a time
3. **CSS Priority**: Use `!important` to override existing semantic color backgrounds
4. **Event Source**: Must distinguish between 'left', 'right-parsed', and 'right-raw' sources
5. **Performance**: Highlighting should apply within 100ms for smooth UX

## Non-Requirements

- Multi-select highlighting (Ctrl+click for multiple SNs)
- Persistent highlighting across page reloads
- Customizable highlight colors
- Cross-verse highlighting
- Highlight animation effects
