## MODIFIED Requirements

### Requirement: Left Panel SN Dict Tooltip

The SN Dict tooltip for left panel (UNV/KJV) SHALL use the `snDictEnabled` flag from the SN_CLICK event instead of a separate checkbox state.

#### Scenario: UNV SN Dict enabled shows tooltip

- **GIVEN** the UNV SN Dict checkbox is checked
- **WHEN** user clicks an SN tag in the UNV section
- **THEN** the SN_CLICK event contains `snDictEnabled: true`
- **AND** sn_dictionary.js shows a tooltip for that SN

#### Scenario: KJV SN Dict enabled shows tooltip

- **GIVEN** the KJV SN Dict checkbox is checked
- **WHEN** user clicks an SN tag in the KJV section
- **THEN** the SN_CLICK event contains `snDictEnabled: true`
- **AND** sn_dictionary.js shows a tooltip for that SN

#### Scenario: SN Dict disabled hides tooltip

- **GIVEN** the UNV/KJV SN Dict checkbox is unchecked
- **WHEN** user clicks an SN tag in that version's section
- **THEN** the SN_CLICK event contains `snDictEnabled: false`
- **AND** sn_dictionary.js does NOT show a tooltip

### Requirement: Right Panel SN Dict unchanged

The right panel SN Dict checkbox behavior SHALL remain unchanged, using its own `right-sn-dict-toggle` checkbox state.

## REMOVED Requirements

### Requirement: Left panel global SN Dict checkbox (REMOVED)

The single `left-sn-dict-toggle` checkbox is REMOVED. Each version (UNV/KJV) now has its own checkbox controlling tooltip display.
