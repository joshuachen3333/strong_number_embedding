# Verse Scroll Position Specification

## MODIFIED Requirements

### Requirement: Selected verse scrolls to top of left panel
When a verse is selected in the left panel, it SHALL scroll to the top of the visible area rather than just into view.

#### Scenario: Verse selection scrolls to top
Given the left panel is displaying a chapter
When a user clicks on a verse
Then the selected verse SHALL scroll to the top of the left panel content area
And the scroll animation SHALL be smooth
