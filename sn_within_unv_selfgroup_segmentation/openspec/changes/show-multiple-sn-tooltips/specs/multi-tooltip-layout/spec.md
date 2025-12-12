# Multi-SN Tooltip Layout Specification

## ADDED Requirements

### Requirement: Display tooltips for all SNs in a group
When a user clicks on an SN group containing multiple Strong's Numbers, the system SHALL display dictionary tooltips for ALL SNs in the group.

#### Scenario: Single SN group (backwards compatibility)
Given a user clicks on an SN group with 1 SN code
When the SN Dict is enabled for the panel
Then the system SHALL display 1 tooltip positioned above or below the element

#### Scenario: Two-SN group layout
Given a user clicks on an SN group with 2 SN codes (e.g., `<09002><07225>`)
When the SN Dict is enabled for the panel
Then the system SHALL display 2 tooltips:
- First tooltip positioned ABOVE the highlighted element
- Second tooltip positioned BELOW the highlighted element
And the highlighted element SHALL remain visible between the tooltips

#### Scenario: Three-SN group layout
Given a user clicks on an SN group with 3 SN codes
When the SN Dict is enabled for the panel
Then the system SHALL display 3 tooltips distributed reasonably:
- If more space above: 2 tooltips above (horizontal), 1 below
- If more space below: 1 tooltip above, 2 tooltips below (horizontal)
And no tooltip SHALL overlap another tooltip
And the highlighted element SHALL remain visible

### Requirement: Parallel definition fetching
The system SHALL fetch all SN definitions in parallel for performance.

#### Scenario: Multi-SN fetch performance
Given a user clicks on an SN group with N SN codes
When the system needs to fetch definitions
Then all N definitions SHALL be fetched concurrently using Promise.all()
And cached definitions SHALL be reused without network requests

### Requirement: Tooltip pool management
Each panel SHALL maintain a pool of 3 reusable tooltip elements.

#### Scenario: Tooltip pool creation
Given the SN Dictionary module initializes
Then 3 tooltip elements SHALL be created for the left panel
And 3 tooltip elements SHALL be created for the right panel

#### Scenario: Tooltip cleanup on new click
Given a user clicks on a new SN group
When the previous tooltips are still visible
Then all previous tooltips SHALL be hidden before showing new ones
