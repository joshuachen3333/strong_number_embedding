# Tooltip Transparency Specification

## ADDED Requirements

### Requirement: SN dictionary tooltip has semi-transparent background
The SN dictionary floating tooltip SHALL have a semi-transparent background to allow users to see highlighted elements underneath.

#### Scenario: Default transparency level
Given the SN dictionary tooltip is displayed
When it overlaps with a highlighted SN element
Then the highlighted element SHALL be partially visible through the tooltip background

#### Scenario: Adjustable opacity via CSS variable
Given the CSS styling for the tooltip
When a developer wants to adjust transparency
Then the opacity SHALL be configurable via CSS variable `--tooltip-opacity`

#### Scenario: Text readability preserved
Given the tooltip is displayed with semi-transparent background
When the user reads the tooltip content
Then all text (SN code, Hebrew/Greek word, transliteration, definitions) SHALL remain clearly readable
