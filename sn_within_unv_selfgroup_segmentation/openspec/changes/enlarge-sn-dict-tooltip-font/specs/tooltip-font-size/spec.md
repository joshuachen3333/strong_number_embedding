# SN Dictionary Tooltip Font Size Specification

## MODIFIED Requirements

### Requirement: Tooltip Font Sizes for Readability
The SN Dictionary tooltip SHALL use larger font sizes for improved readability with tighter line spacing.

#### Scenario: Base tooltip container size
Given the user clicks on an SN element with SN Dict enabled
When the tooltip displays
Then the tooltip container SHALL have:
- max-width: 500px
- max-height: 480px
- min-width: 340px
- padding: 15px 20px
- base font-size: 18px
- line-height: 1.3

#### Scenario: Strong's number display
Given the tooltip displays an SN code
Then the .tooltip-sn element SHALL have font-size: 19px

#### Scenario: Hebrew/Greek word display
Given the tooltip displays the original word
Then the .tooltip-word element SHALL have font-size: 26px

#### Scenario: Transliteration display
Given the tooltip displays transliteration
Then the .tooltip-translit element SHALL have font-size: 18px

#### Scenario: Metadata display (詞性/TWOT)
Given the tooltip displays part of speech or TWOT reference
Then the .tooltip-meta element SHALL have font-size: 16px

#### Scenario: Definition list display
Given the tooltip displays definitions
Then the .tooltip-def-list element SHALL have font-size: 18px with line-height: 1.5
And the .tooltip-subdef element SHALL have font-size: 16px
And the .tooltip-def element SHALL have font-size: 18px with line-height: 1.4
