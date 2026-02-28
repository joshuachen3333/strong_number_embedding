# Context-Aware Hotkeys Specification

## ADDED Requirements

### Requirement: REQ-HOTKEY-PANEL-DETECTION

The viewer MUST track which panel (left or right) is currently active based on user interaction.

**Acceptance Criteria:**
- Left panel becomes active when mouse enters the left panel area
- Right panel becomes active when mouse enters the right panel area
- Clicking on a verse or SN tag in left panel sets left panel as active
- Clicking on an SN group in right panel's parsed section sets right panel as active
- Default active panel on page load is left panel

#### Scenario: Mouse hover switches active panel
Given the viewer is loaded with a verse displayed
When the user hovers the mouse over the right panel
Then the right panel becomes the active panel
And keyboard hotkeys should use right panel behavior

#### Scenario: Click on left panel SN sets left panel active
Given the right panel is currently active
When the user clicks on an SN tag in the left panel
Then the left panel becomes active
And keyboard hotkeys should use left panel behavior

---

### Requirement: REQ-HOTKEY-LEFT-PANEL

When the left panel is active, hotkeys MUST navigate verses and chapters as currently implemented.

**Key Bindings:**
| Key | Action |
|-----|--------|
| ↑ | Previous verse (wraps to previous chapter/book) |
| ↓ | Next verse (wraps to next chapter/book) |
| ← | Previous chapter (wraps to previous book) |
| → | Next chapter (wraps to next book) |
| Home | First verse of current chapter |
| End | Last verse of current chapter |

#### Scenario: Arrow down navigates to next verse in left panel mode
Given the left panel is active
And the current verse is Genesis 1:1
When the user presses the down arrow key
Then the viewer navigates to Genesis 1:2
And verse 2 is highlighted as selected

#### Scenario: Arrow left navigates to previous chapter in left panel mode
Given the left panel is active
And the current verse is Genesis 2:5
When the user presses the left arrow key
Then the viewer navigates to Genesis 1:1
And chapter 1 is loaded

---

### Requirement: REQ-HOTKEY-RIGHT-PANEL

When the right panel is active, hotkeys MUST navigate SN groups within **Section 1: "Parsed and Formatted Text Section"** only. The Raw UNV+SN section and Morphology Notes section are NOT included in keyboard navigation.

**Key Bindings:**
| Key | Action |
|-----|--------|
| ↑ | Previous SN group; if at first group, go to previous verse and select last group |
| ↓ | Next SN group; if at last group, go to next verse and select first group |
| ← | Previous verse |
| → | Next verse |
| Home | First SN group in current verse |
| End | Last SN group in current verse |

#### Scenario: Arrow down selects next SN group in right panel mode
Given the right panel is active
And the first SN group is currently selected
And there are 5 SN groups in the parsed section
When the user presses the down arrow key
Then the second SN group becomes selected
And the second SN group displays a keyboard selection highlight

#### Scenario: Arrow down at last SN group navigates to next verse
Given the right panel is active
And the last SN group (group 5 of 5) is currently selected
And the current verse is Genesis 1:1
When the user presses the down arrow key
Then the viewer navigates to Genesis 1:2
And the first SN group of Genesis 1:2 is automatically selected

#### Scenario: Arrow up at first SN group navigates to previous verse
Given the right panel is active
And the first SN group is currently selected
And the current verse is Genesis 1:2
When the user presses the up arrow key
Then the viewer navigates to Genesis 1:1
And the last SN group of Genesis 1:1 is automatically selected

#### Scenario: Home key selects first SN group
Given the right panel is active
And the third SN group is currently selected
When the user presses the Home key
Then the first SN group becomes selected

#### Scenario: End key selects last SN group
Given the right panel is active
And the first SN group is currently selected
And there are 5 SN groups total
When the user presses the End key
Then the fifth (last) SN group becomes selected

---

### Requirement: REQ-HOTKEY-GROUP-HIGHLIGHT

When an SN group is selected via keyboard navigation, it MUST display a distinct visual highlight.

**Visual Requirements:**
- Selected group has a visible border or outline (e.g., 2px solid blue)
- Selection highlight is distinct from hover highlight
- Only one group can be keyboard-selected at a time
- Selection persists until user selects another group or changes verse

#### Scenario: Keyboard selected group shows visual highlight
Given the right panel is active
When the user presses down arrow to select an SN group
Then the selected SN group displays a keyboard selection highlight
And the highlight is visually distinct from the background color

#### Scenario: Selecting new group clears previous selection
Given an SN group is currently keyboard-selected
When the user presses down arrow to select the next group
Then the previous group's keyboard selection highlight is removed
And the new group displays the keyboard selection highlight

---

### Requirement: REQ-HOTKEY-BIDIRECTIONAL

When an SN group is selected via keyboard, corresponding SN tags in the left panel MUST also highlight.

#### Scenario: Keyboard selection triggers bidirectional highlighting
Given the right panel is active
And the current verse is Genesis 1:1
When the user keyboard-selects an SN group containing codes [09002, 07225]
Then the corresponding SN tags in the left panel highlight with matching colors
And both panels show synchronized highlighting for the selected group
