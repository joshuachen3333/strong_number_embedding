# Right Panel Single Highlight Mode Specification

## ADDED Requirements

### Requirement: Right panel has independent Single HL control
The right panel SHALL have its own "Single HL" checkbox that controls highlight behavior independently from the left panel.

#### Scenario: Right panel Single HL checkbox placement
Given the right panel header controls
When the page loads
Then the controls SHALL appear in order: SN Dict → Spec → Single HL → toggle buttons (Parsed/Raw/Notes)

#### Scenario: Default state
Given the page loads for the first time
When the right panel Single HL checkbox is rendered
Then it SHALL be checked (ON) by default

#### Scenario: Single HL ON clears previous highlights
Given the right panel Single HL is checked (ON)
When a user clicks on an SN group in the right panel
Then any previous highlights in the right panel SHALL be cleared before applying new highlight

#### Scenario: Single HL OFF accumulates highlights
Given the right panel Single HL is unchecked (OFF)
When a user clicks on an SN group in the right panel
Then the new highlight SHALL be added without clearing previous highlights

#### Scenario: Independent panel control
Given the left panel Single HL is OFF
And the right panel Single HL is ON
When a user clicks on an SN group
Then the right panel SHALL clear its previous highlights
And the left panel SHALL keep its previous highlights (based on its own setting)
