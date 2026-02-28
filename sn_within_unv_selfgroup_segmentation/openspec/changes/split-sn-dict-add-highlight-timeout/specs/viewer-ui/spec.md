## ADDED Requirements

### Requirement: Panel-specific SN Dict Controls
The system SHALL provide independent Strong's Number Dictionary toggle controls for each panel (left and right).

#### Scenario: Left panel SN Dict checkbox
- **WHEN** user clicks the left panel SN Dict checkbox
- **THEN** only the left panel's SN Dict tooltip behavior is toggled
- **AND** the right panel's SN Dict state remains unchanged

#### Scenario: Right panel SN Dict checkbox
- **WHEN** user clicks the right panel SN Dict checkbox
- **THEN** only the right panel's SN Dict tooltip behavior is toggled
- **AND** the left panel's SN Dict state remains unchanged

### Requirement: Auto-show SN Dict Tooltip on Highlight
The system SHALL automatically display the SN Dict tooltip when a Strong's Number is highlighted AND that panel's SN Dict checkbox is checked.

#### Scenario: Blue highlight triggers tooltip
- **WHEN** a Strong's Number element receives blue (local) highlight
- **AND** that panel's SN Dict checkbox is checked
- **THEN** the SN Dict tooltip for that Strong's Number is displayed near the highlighted element

#### Scenario: Orange highlight triggers tooltip
- **WHEN** a Strong's Number element receives orange (remote) highlight
- **AND** that panel's SN Dict checkbox is checked
- **THEN** the SN Dict tooltip for that Strong's Number is displayed near the highlighted element

#### Scenario: Tooltip not shown when SN Dict unchecked
- **WHEN** a Strong's Number element is highlighted
- **AND** that panel's SN Dict checkbox is NOT checked
- **THEN** no SN Dict tooltip is displayed

### Requirement: Hover-style Floating Tooltip
The SN Dict tooltip SHALL be displayed as a hover-style floating tooltip (similar to Spec tooltip) rather than a popup window.

#### Scenario: Tooltip styling matches Spec tooltip
- **WHEN** the SN Dict tooltip is displayed
- **THEN** it appears as a floating element near the highlighted Strong's Number
- **AND** it uses similar visual styling to the Spec tooltip (dark background, light text)

### Requirement: Highlight and Tooltip Timeout
The system SHALL automatically clear highlights and tooltips after 10 seconds of inactivity.

#### Scenario: 10-second timeout clears highlights
- **WHEN** a highlight is active for 10 seconds without new highlight actions
- **THEN** the blue (local) highlight is cleared
- **AND** the orange (remote) highlight is cleared
- **AND** all SN Dict tooltips are hidden

#### Scenario: New highlight resets timeout
- **WHEN** a new highlight action occurs (click or keyboard navigation)
- **THEN** the 10-second timeout is reset
- **AND** the previous timeout is cancelled

#### Scenario: Synchronized cleanup order
- **WHEN** the timeout expires or highlights are manually cleared
- **THEN** blue highlights are cleared first
- **THEN** orange highlights are cleared
- **THEN** tooltips are hidden

## MODIFIED Requirements

### Requirement: Header Layout
The header-right area SHALL NOT contain the global SN Dict checkbox.

#### Scenario: Global SN Dict removed from header
- **WHEN** the viewer loads
- **THEN** no SN Dict checkbox appears in the header-right area

### Requirement: Left Panel Header Layout
The left panel header SHALL display controls in the order: `[SN Dict checkbox] [Single HL checkbox]`.

#### Scenario: Left panel header control order
- **WHEN** the left panel is rendered
- **THEN** the SN Dict checkbox appears first (leftmost)
- **AND** the Single HL checkbox appears second (to the right of SN Dict)

### Requirement: Right Panel Header Layout
The right panel header SHALL display controls in the order: `[SN Dict checkbox] [Spec checkbox] [Parsed] [Raw] [Notes]`.

#### Scenario: Right panel header control order
- **WHEN** the right panel is rendered
- **THEN** controls appear in order: SN Dict checkbox, Spec checkbox, Parsed button, Raw button, Notes button

### Requirement: Spec Control Style
The Spec control SHALL be a checkbox (not a toggle button).

#### Scenario: Spec checkbox rendering
- **WHEN** the right panel header is rendered
- **THEN** the Spec control appears as a checkbox with label
- **AND** it has the same visual style as other checkboxes (SN Dict, Single HL)

### Requirement: localStorage Persistence for Panel Settings
The system SHALL persist panel-specific SN Dict settings to localStorage.

#### Scenario: Left panel SN Dict persistence
- **WHEN** user changes the left panel SN Dict checkbox
- **THEN** the setting is saved to localStorage with key `viewer_leftSnDictEnabled`
- **AND** on page reload, the checkbox restores to the saved state

#### Scenario: Right panel SN Dict persistence
- **WHEN** user changes the right panel SN Dict checkbox
- **THEN** the setting is saved to localStorage with key `viewer_rightSnDictEnabled`
- **AND** on page reload, the checkbox restores to the saved state
