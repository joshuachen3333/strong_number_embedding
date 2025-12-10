# Spec: Toggle Button Green Styling

## Overview

Define the visual styling for the Parsed/Raw/Notes toggle buttons in the right panel header, using green color for inactive state.

## MODIFIED Requirements

### Requirement: Inactive toggle button styling

The inactive (unchecked) toggle buttons in the right panel header SHALL display with green text and border color (`#27ae60`).

#### Scenario: Button in inactive state

**Given** a toggle button (Parsed, Raw, or Notes) in the right panel header
**When** the button is in inactive state (not checked)
**Then** the button displays:
- Text color: `#27ae60` (green)
- Border color: `#27ae60` (green)
- Background: transparent

### Requirement: Inactive toggle button hover effect

The hover effect for inactive toggle buttons SHALL use a light green tint.

#### Scenario: Hovering over inactive button

**Given** a toggle button in inactive state
**When** the user hovers over the button
**Then** the background changes to `rgba(39, 174, 96, 0.1)` (light green tint)

### Requirement: Active toggle button styling unchanged

The active (checked) toggle buttons SHALL retain the existing blue styling for clear on/off distinction.

#### Scenario: Button in active state

**Given** a toggle button in active state (checked)
**Then** the button displays:
- Background: `#3498db` (blue)
- Border color: `#3498db` (blue)
- Text color: white
