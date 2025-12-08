# Spec Delta: Parser Output Format

## ADDED Requirements

### Requirement: Complete Strong's Number Tag Preservation in Parsed Section

The parser SHALL preserve complete Strong's number tags (including WAH/WH/WTH prefixes) in the Parsed and Formatted Text Section output, matching the format used in the Raw UNV+SN Source Text Section.

#### Scenario: Regular Strong's number with WH prefix
- **GIVEN** a verse contains `<WH0430>` in the raw text
- **WHEN** the parser generates the Parsed section
- **THEN** the output SHALL display `<WH0430>` (not `<0430>`)

#### Scenario: Strong's number with WAH conjunction prefix
- **GIVEN** a verse contains `<WAH05921>` in the raw text
- **WHEN** the parser generates the Parsed section
- **THEN** the output SHALL display `<WAH05921>` (not `<05921>`)

#### Scenario: Strong's number with WTH tense prefix
- **GIVEN** a verse contains `<WTH8804>` in the raw text
- **WHEN** the parser generates the Parsed section
- **THEN** the output SHALL display `<WTH8804>` (not `<8804>` or `(8804)`)

#### Scenario: Braced pattern with prefixed Strong's numbers
- **GIVEN** a verse contains `{<WAH05921>}<WH06440>` in the raw text
- **WHEN** the parser generates the Parsed section
- **THEN** the output SHALL display `{<WAH05921>}<WH06440>` (not `{<05921>}<06440>`)

#### Scenario: Compound preposition with multiple components
- **GIVEN** a verse contains a compound preposition like `<WAH04480><WH05921>`
- **WHEN** the parser generates the Parsed section
- **THEN** each component SHALL preserve its complete prefix (e.g., `<WAH04480><WH05921>`)

### Requirement: Format Consistency Between Sections

The parser SHALL ensure Strong's number tag format is identical between the Parsed and Formatted Text Section and the Raw UNV+SN Source Text Section.

#### Scenario: Cross-section format matching
- **GIVEN** a parsed verse with both Parsed and Raw sections
- **WHEN** comparing Strong's number tags between sections
- **THEN** the same Strong's number SHALL appear with identical prefix format in both sections
- **AND** numeric codes SHALL match exactly (e.g., `<WAH05921>` in Parsed matches `<WAH05921>` in Raw)

#### Scenario: Visual consistency in viewer display
- **GIVEN** the viewer displays both Parsed and Raw sections side-by-side
- **WHEN** a user views a Strong's number group
- **THEN** the tag format SHALL be visually identical between sections
- **AND** color highlighting SHALL be consistent for matching tags

## MODIFIED Requirements

None - This is a new formatting requirement that doesn't modify existing parsing logic or grouping rules.

## REMOVED Requirements

None - No functionality is being removed, only format is being enhanced.
