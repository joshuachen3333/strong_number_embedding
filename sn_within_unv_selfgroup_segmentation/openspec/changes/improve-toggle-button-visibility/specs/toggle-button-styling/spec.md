# Toggle Button Styling

## MODIFIED Requirements

### Requirement: Toggle Button Inactive State Visibility

Toggle buttons (Parsed, Raw, Notes) in the right panel header SHALL have sufficient visual contrast in their inactive state to be clearly distinguishable from the panel header background.

#### Scenario: Inactive toggle button on light gray panel header

**Given** a toggle button is in the inactive (unchecked) state
**And** the button is displayed on the right panel header with background color `#ecf0f1`
**When** the user views the panel header
**Then** the button must have a white background (`#ffffff`)
**And** the button must have a blue border (`#3498db`)
**And** the button must have blue text (`#3498db`)
**And** the button must be clearly distinguishable from the panel header background

#### Scenario: Active toggle button appearance unchanged

**Given** a toggle button is in the active (checked) state
**When** the user views the panel header
**Then** the button must have a blue background (`#3498db`)
**And** the button must have white text
**And** the active state appearance must remain unchanged from current behavior

#### Scenario: Hover state on inactive button

**Given** a toggle button is in the inactive state
**When** the user hovers over the button
**Then** the button must show a light blue tint (`rgba(52, 152, 219, 0.1)`)
**And** the visual feedback must indicate the button is interactive
