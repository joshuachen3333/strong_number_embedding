# Viewer Settings Capability

## ADDED Requirements

### Requirement: SN Tooltip Toggle
The viewer SHALL provide a checkbox control labeled "SN Dict" that enables or disables the Strong's Number Dictionary Tooltip feature. The default state SHALL be OFF (unchecked).

#### Scenario: SN Tooltip disabled by default
- **WHEN** a user visits the viewer for the first time (no saved settings)
- **THEN** the "SN Dict" checkbox SHALL be unchecked
- **AND** clicking on Strong's Numbers SHALL NOT display a dictionary tooltip

#### Scenario: SN Tooltip enabled by user
- **WHEN** the user checks the "SN Dict" checkbox
- **THEN** clicking on Strong's Numbers SHALL display the dictionary tooltip
- **AND** the setting SHALL be saved to localStorage

#### Scenario: SN Tooltip state persisted
- **WHEN** the user has enabled the SN Tooltip and refreshes the page
- **THEN** the "SN Dict" checkbox SHALL remain checked
- **AND** clicking on Strong's Numbers SHALL display the dictionary tooltip

### Requirement: Section Toggle Persistence
The viewer SHALL persist the Parsed/Raw/Notes section toggle states to localStorage. The default states SHALL be: Parsed ON, Raw OFF, Notes OFF.

#### Scenario: Default toggle states on first visit
- **WHEN** a user visits the viewer for the first time (no saved settings)
- **THEN** the "Parsed" toggle button SHALL be active (section visible)
- **AND** the "Raw" toggle button SHALL be inactive (section hidden)
- **AND** the "Notes" toggle button SHALL be inactive (section hidden)

#### Scenario: Toggle state persistence
- **WHEN** the user toggles a section (e.g., enables Raw, disables Parsed)
- **AND** the user refreshes the page
- **THEN** the toggle states SHALL match the user's previous configuration
- **AND** the visible sections SHALL correspond to the toggle states

#### Scenario: Toggle state preserved on verse navigation
- **WHEN** the user has configured specific toggle states
- **AND** the user navigates to a different verse
- **THEN** the toggle states SHALL remain unchanged
- **AND** the visible sections SHALL correspond to the toggle states

### Requirement: localStorage Error Handling
The viewer SHALL gracefully handle localStorage errors (e.g., in private browsing mode) by falling back to default values without displaying errors.

#### Scenario: localStorage unavailable
- **WHEN** localStorage is not available or throws an error
- **THEN** the viewer SHALL use default settings (Parsed ON, Raw OFF, Notes OFF, SN Dict OFF)
- **AND** no error messages SHALL be displayed to the user
- **AND** the viewer SHALL remain fully functional

#### Scenario: Corrupted localStorage data
- **WHEN** localStorage contains invalid data for a setting
- **THEN** the viewer SHALL use the default value for that setting
- **AND** subsequent saves SHALL overwrite the corrupted data
