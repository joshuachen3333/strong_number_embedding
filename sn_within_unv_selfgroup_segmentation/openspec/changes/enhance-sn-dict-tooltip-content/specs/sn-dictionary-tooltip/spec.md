# SN Dictionary Tooltip Specification

## ADDED Requirements

### Requirement: Enhanced Tooltip Content Display
The SN Dictionary tooltip SHALL display extended dictionary content including part of speech, TWOT reference, and full definitions.

#### Scenario: Display part of speech for Hebrew noun
Given the user clicks on SN 07225 (רֵאשִׁית)
When the tooltip displays
Then it SHALL show "詞性: 陰性名詞" in the content section

#### Scenario: Display TWOT reference
Given the user clicks on SN 07225 (רֵאשִׁית)
When the tooltip displays
Then it SHALL show "TWOT: 2097e" when available in the dictionary data

#### Scenario: Display full numbered definitions
Given the user clicks on SN 00430 (אֱלֹהִים)
When the tooltip displays
Then it SHALL show all numbered definitions (1), 2), etc.) not just the first line
And sub-definitions (1a, 1b, etc.) SHALL be indented

### Requirement: Expanded Tooltip Size
The SN Dictionary tooltip SHALL have adequate size for displaying extended content.

#### Scenario: Tooltip width accommodates content
Given the user enables SN Dict and clicks on an SN element
When the tooltip displays
Then the tooltip width SHALL be at least 400px to accommodate full definitions

#### Scenario: Tooltip height with scrolling
Given the user clicks on an SN with many definitions
When the tooltip displays
Then the tooltip SHALL have a max-height with scrollable overflow
And content SHALL be scrollable without clipping

## MODIFIED Requirements

### Requirement: Definition Extraction Logic
The definition extraction SHALL be enhanced to return structured content.

#### Scenario: Extract multiple definition fields
Given dictionary data is loaded for an SN code
When the definition is extracted
Then the result SHALL include:
- orig: Hebrew/Greek word
- transliteration: phonetic rendering
- partOfSpeech: extracted from patterns like "陽性名詞", "動詞"
- twot: TWOT reference number
- definitions: array of all numbered definitions with sub-definitions
