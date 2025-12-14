## MODIFIED Requirements

### Requirement: Cross-panel SN Dict tooltip (right → left)

When clicking an SN in the right panel, if the corresponding SN is highlighted in the left panel, the tooltip SHALL appear based on the highlighted section's SN Dict checkbox state.

#### Scenario: Right click with UNV SN Dict enabled shows tooltip

- **GIVEN** the UNV section is visible in the left panel
- **AND** the UNV SN Dict checkbox is checked
- **WHEN** user clicks an SN tag in the right panel
- **THEN** the left panel shows orange highlighting on the corresponding SN
- **AND** a tooltip appears near the highlighted element in the left panel

#### Scenario: Right click with UNV SN Dict disabled hides tooltip

- **GIVEN** the UNV section is visible in the left panel
- **AND** the UNV SN Dict checkbox is unchecked
- **WHEN** user clicks an SN tag in the right panel
- **THEN** the left panel shows orange highlighting on the corresponding SN
- **AND** no tooltip appears in the left panel

#### Scenario: Right click with KJV SN Dict enabled shows tooltip

- **GIVEN** the KJV section is visible in the left panel
- **AND** the KJV SN Dict checkbox is checked
- **WHEN** user clicks an SN tag in the right panel
- **THEN** the left panel shows orange highlighting on the corresponding SN in KJV section
- **AND** a tooltip appears near the highlighted element in the left panel

### Requirement: Per-section checkbox lookup

The SN Dict tooltip for cross-panel highlighting SHALL determine enabled state by checking the checkbox of the section containing the highlighted element.

#### Scenario: Element in UNV section uses UNV checkbox

- **GIVEN** an orange-highlighted element is inside `.unv-section`
- **WHEN** determining if tooltip should show
- **THEN** the `unv-sn-dict-toggle` checkbox state is used

#### Scenario: Element in KJV section uses KJV checkbox

- **GIVEN** an orange-highlighted element is inside `.kjv-section`
- **WHEN** determining if tooltip should show
- **THEN** the `kjv-sn-dict-toggle` checkbox state is used
