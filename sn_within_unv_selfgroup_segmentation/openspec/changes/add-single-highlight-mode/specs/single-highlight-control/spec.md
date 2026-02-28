# Specification: Single Highlight Mode Control

## ADDED Requirements

### Requirement: Single Highlight Mode Toggle

The system SHALL provide a checkbox control in the left panel header that allows users to toggle between single highlight mode (only one SN group highlighted at a time) and multi-highlight mode (multiple SN groups can be highlighted simultaneously).

#### Scenario: Default state is single highlight mode

**Given** the user opens the viewer_v2 application

**When** the page loads

**Then** the "Single HL" checkbox SHALL be checked (enabled)

**And** the system SHALL operate in single highlight mode (clearing previous highlights on new SN clicks)

#### Scenario: Toggle to multi-highlight mode

**Given** the user is viewing Genesis 1:4

**And** the "Single HL" checkbox is checked

**When** the user unchecks the "Single HL" checkbox

**Then** the checkbox state SHALL change to unchecked

**And** the system SHALL enter multi-highlight mode

**And** existing highlights SHALL remain visible (mode change does not clear highlights)

#### Scenario: Toggle back to single highlight mode

**Given** the system is in multi-highlight mode (checkbox unchecked)

**And** multiple SN groups are currently highlighted

**When** the user checks the "Single HL" checkbox

**Then** the checkbox state SHALL change to checked

**And** the system SHALL enter single highlight mode

**And** existing highlights SHALL remain visible until next SN click

### Requirement: Single highlight mode behavior

When Single HL mode is ON (checkbox checked), clicking a new Strong's Number SHALL clear all previous highlighting before applying new highlighting to maintain single-selection behavior.

#### Scenario: Single mode - clicking new SN clears previous

**Given** Single HL mode is ON (checkbox checked)

**And** the user has highlighted `{<0853>}<0216>` group in Gen 1:4

**When** the user clicks on a different SN group `<0430>`

**Then** the system SHALL:
- Remove all highlighting from the `{<0853>}<0216>` group
- Apply highlighting to the `<0430>` group
- Display only one highlighted group

**And** the behavior SHALL match the current (pre-feature) highlighting behavior

#### Scenario: Single mode - left panel click clears and highlights

**Given** Single HL mode is ON

**And** SN `<0216>` is highlighted with blue in left panel

**When** the user clicks `<0430>` in left panel

**Then** the system SHALL:
- Clear blue highlighting from `<0216>` in left panel
- Clear orange highlighting from `{<0853>}<0216>` in right panels
- Apply blue highlighting to `<0430>` in left panel
- Apply orange highlighting to `<0430>` in right panels

#### Scenario: Single mode - right panel click clears and highlights

**Given** Single HL mode is ON

**And** `{<0853>}<0216>` is highlighted in right Parsed section

**When** the user clicks `<0430>` in right Raw section

**Then** the system SHALL:
- Clear all highlighting from `{<0853>}<0216>` group
- Apply highlighting to `<0430>` group across all panels

### Requirement: Multi-highlight mode behavior

When Single HL mode is OFF (checkbox unchecked), clicking a new Strong's Number SHALL add highlighting without clearing previous highlights, allowing multiple SN groups to be highlighted simultaneously for comparison.

#### Scenario: Multi mode - clicking new SN keeps previous

**Given** Single HL mode is OFF (checkbox unchecked)

**And** the user has highlighted `{<0853>}<0216>` group in Gen 1:4

**When** the user clicks on a different SN group `<0430>`

**Then** the system SHALL:
- Keep all highlighting on the `{<0853>}<0216>` group
- Add highlighting to the `<0430>` group
- Display both highlighted groups simultaneously

#### Scenario: Multi mode - accumulate highlights from different panels

**Given** Single HL mode is OFF

**And** no highlights are active

**When** the user:
1. Clicks `<0216>` in left panel (left blue, right orange)
2. Then clicks `<0430>` in right Parsed section (right blue for `<0430>`, left orange)

**Then** the system SHALL display:
- Left panel: `<0216>` with blue, `<0430>` with orange
- Right Parsed: `{<0853>}<0216>` with orange, `<0430>` with blue
- Right Raw: corresponding tags highlighted with matching colors

**And** all highlighted groups SHALL remain visible simultaneously

#### Scenario: Multi mode - no limit on number of highlights

**Given** Single HL mode is OFF

**When** the user highlights 5 different SN groups sequentially

**Then** all 5 groups SHALL remain highlighted

**And** each SHALL display with appropriate blue/orange colors based on click source

### Requirement: Global clearing behavior

Regardless of Single HL mode state, certain user actions SHALL always clear all highlights to provide consistent reset mechanisms and prevent highlight state from persisting inappropriately.

#### Scenario: Click-away clears all highlights regardless of mode

**Given** Single HL mode is OFF

**And** multiple SN groups are highlighted (e.g., `<0216>` and `<0430>`)

**When** the user clicks on Chinese text, whitespace, or any non-SN element

**Then** the system SHALL remove all highlighting from all panels

**And** no highlights SHALL remain visible

#### Scenario: Click-away in single mode also clears

**Given** Single HL mode is ON

**And** one SN group is highlighted

**When** the user clicks on a non-SN element

**Then** the system SHALL clear all highlighting

#### Scenario: Verse navigation clears all highlights regardless of mode

**Given** Single HL mode is OFF

**And** multiple SN groups are highlighted in Gen 1:4

**When** the user navigates to Gen 1:5 by clicking verse 5

**Then** the system SHALL:
- Clear all highlighting before loading verse 5
- Display verse 5 with no highlights active

#### Scenario: Verse navigation in single mode also clears

**Given** Single HL mode is ON

**And** one SN group is highlighted in Gen 1:4

**When** the user navigates to Gen 1:5

**Then** the system SHALL clear the highlight before displaying verse 5

### Requirement: Visual presentation

The Single HL checkbox control SHALL be visually integrated into the left panel header with clear labeling and consistent styling.

#### Scenario: Checkbox appears in left panel header

**Given** the viewer is loaded

**When** the user looks at the left panel

**Then** the panel header SHALL contain:
- The existing "UNV+SN Text" heading
- A checkbox labeled "Single HL" positioned to the right of the heading
- Both elements horizontally aligned

#### Scenario: Checkbox is interactive and styled

**Given** the checkbox is visible

**When** the user hovers over the checkbox or label

**Then** the cursor SHALL change to pointer

**And** clicking either the checkbox or label SHALL toggle the checkbox state

#### Scenario: Checkbox label is clear and concise

**Given** the checkbox control is visible

**Then** the label text SHALL read "Single HL"

**And** the label SHALL be positioned immediately after the checkbox

**And** the label SHALL be user-selectable: none to prevent accidental text selection

## Design Constraints

1. **Default State**: Checkbox must default to checked (single mode ON) to maintain current behavior
2. **Cross-Panel Coordination**: Both left and right panels must read the same checkbox state
3. **No Highlight Limit**: Multi-mode does not impose a maximum number of simultaneous highlights
4. **Global Clears Always Work**: Click-away and verse navigation ignore mode setting
5. **No State Persistence**: Mode preference is not saved in localStorage (resets on page reload)

## Non-Requirements

- Keyboard shortcuts for toggling mode
- Visual indicator of how many groups are highlighted
- Maximum limit on simultaneous highlights in multi-mode
- Persistent mode preference across page reloads
- Separate controls for left vs right panel multi-highlight
- Animation when toggling between modes
