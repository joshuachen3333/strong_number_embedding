## MODIFIED Requirements

### Requirement: Dual-panel cross-panel SN Dict tooltip (right → left)

When clicking an SN in the right panel with BOTH UNV and KJV visible in the left panel, the tooltip SHALL appear on the section whose SN Dict checkbox is enabled.

#### Scenario: Both visible, only KJV SN Dict enabled shows KJV tooltip

- **GIVEN** both UNV and KJV sections are visible in the left panel
- **AND** the UNV SN Dict checkbox is unchecked
- **AND** the KJV SN Dict checkbox is checked
- **WHEN** user clicks an SN tag in the right panel
- **THEN** the left panel shows orange highlighting on both UNV and KJV SNs
- **AND** a tooltip appears near the highlighted element in the KJV section

#### Scenario: Both visible, only UNV SN Dict enabled shows UNV tooltip

- **GIVEN** both UNV and KJV sections are visible in the left panel
- **AND** the UNV SN Dict checkbox is checked
- **AND** the KJV SN Dict checkbox is unchecked
- **WHEN** user clicks an SN tag in the right panel
- **THEN** the left panel shows orange highlighting on both UNV and KJV SNs
- **AND** a tooltip appears near the highlighted element in the UNV section

#### Scenario: Both visible, both SN Dict enabled shows first available tooltip

- **GIVEN** both UNV and KJV sections are visible in the left panel
- **AND** both UNV and KJV SN Dict checkboxes are checked
- **WHEN** user clicks an SN tag in the right panel
- **THEN** the left panel shows orange highlighting on both UNV and KJV SNs
- **AND** a tooltip appears near the highlighted element in either section

#### Scenario: Both visible, neither SN Dict enabled shows no tooltip

- **GIVEN** both UNV and KJV sections are visible in the left panel
- **AND** both UNV and KJV SN Dict checkboxes are unchecked
- **WHEN** user clicks an SN tag in the right panel
- **THEN** the left panel shows orange highlighting on both UNV and KJV SNs
- **AND** no tooltip appears in the left panel

### Requirement: Section-aware element finding

The `findHighlightedElementInPanel` function SHALL check all highlighted elements and return one whose section has SN Dict enabled.

#### Scenario: Multiple highlighted elements with mixed checkbox states

- **GIVEN** multiple elements have `.clicked-remote` class in the left panel
- **AND** these elements are in different sections (UNV/KJV)
- **WHEN** finding the element for tooltip positioning
- **THEN** the function iterates through all `.clicked-remote` elements
- **AND** returns the first element whose section's SN Dict checkbox is checked
