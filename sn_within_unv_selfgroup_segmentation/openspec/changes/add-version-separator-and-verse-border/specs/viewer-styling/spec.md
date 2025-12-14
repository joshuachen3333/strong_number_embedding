## ADDED Requirements

### Requirement: Version Section Separator

When both UNV and KJV sections are visible in the left panel, there SHALL be a thick horizontal separator line between them with version-specific colors.

#### Scenario: Both versions visible shows two-tone separator

- **WHEN** both UNV and KJV toggles are active
- **THEN** a horizontal separator line appears between the two sections
- **AND** the separator has blue color (#3498db) on the UNV side (bottom border of UNV section)
- **AND** the separator has teal color (#1abc9c) on the KJV side (top border of KJV section)
- **AND** the combined separator width is approximately 8-10px total

#### Scenario: Single version visible shows no separator

- **WHEN** only one version toggle is active
- **THEN** no separator line is visible

### Requirement: Version-Specific Selected Verse Border

The selected verse SHALL display a full rectangular border in the color matching its version's toggle button.

#### Scenario: UNV selected verse has blue border

- **WHEN** a verse is selected in the UNV section
- **THEN** the verse displays a blue (#3498db) rectangular border on all four sides
- **AND** the border width is approximately 4px

#### Scenario: KJV selected verse has teal border

- **WHEN** a verse is selected in the KJV section
- **THEN** the verse displays a teal (#1abc9c) rectangular border on all four sides
- **AND** the border width is approximately 4px

#### Scenario: Both versions show same selected verse

- **WHEN** both UNV and KJV sections are visible
- **AND** a verse is selected
- **THEN** the same verse number is highlighted in both sections
- **AND** UNV shows blue border
- **AND** KJV shows teal border

## MODIFIED Requirements

### Requirement: Selected Verse Visual Distinction

The selected verse SHALL be visually distinct with a full rectangular border instead of only left and right borders.

#### Scenario: Selected verse has rectangular border

- **WHEN** a verse is selected
- **THEN** the verse displays a border on all four sides (top, right, bottom, left)
- **AND** the border color matches the version's theme color
- **AND** the border width (4px) is slightly thicker than the previous styling (3px) but thinner than the version separator
