# SN Dictionary Tooltip Font Size Specification

## MODIFIED Requirements

### Requirement: Tooltip Font Sizes for Readability
The SN Dictionary tooltip SHALL use larger font sizes for improved readability.

#### Scenario: Base tooltip container size
Given the user clicks on an SN element with SN Dict enabled
When the tooltip displays
Then the tooltip container SHALL have:
- max-width: 520px
- max-height: 500px
- min-width: 340px
- padding: 16px 20px
- base font-size: 15px

#### Scenario: Strong's number display
Given the tooltip displays an SN code
Then the .tooltip-sn element SHALL have font-size: 16px

#### Scenario: Hebrew/Greek word display
Given the tooltip displays the original word
Then the .tooltip-word element SHALL have font-size: 24px

#### Scenario: Transliteration display
Given the tooltip displays transliteration
Then the .tooltip-translit element SHALL have font-size: 15px

#### Scenario: Metadata display (詞性/TWOT)
Given the tooltip displays part of speech or TWOT reference
Then the .tooltip-meta element SHALL have font-size: 14px

#### Scenario: Definition list display
Given the tooltip displays definitions
Then the .tooltip-def-list element SHALL have font-size: 15px
And the .tooltip-subdef element SHALL have font-size: 14px
