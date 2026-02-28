# Left Panel Version Toggle

## ADDED Requirements

### Requirement: UNV/KJV Toggle Buttons
The left panel header SHALL display [UNV] and [KJV] toggle buttons on the right side, allowing users to show or hide each Bible version independently.

#### Scenario: User toggles UNV on
Given the left panel is displayed
When the user clicks the [UNV] toggle button
Then the UNV content section becomes visible
And the UNV checkbox controls (SN Dict, Single HL) appear in the header
And the toggle button shows active state with blue color (#3498db)

#### Scenario: User toggles KJV on
Given the left panel is displayed
When the user clicks the [KJV] toggle button
Then the KJV content section becomes visible
And the KJV checkbox controls (SN Dict, Single HL) appear in the header
And the toggle button shows active state with teal color (#1abc9c)

#### Scenario: Both versions active
Given both UNV and KJV toggles are active
Then both content sections are displayed (UNV above KJV)
And both sets of checkbox controls are visible with their respective colors

### Requirement: Color-Coded Controls
Each version SHALL have distinctly colored controls for visual association.

#### Scenario: UNV controls use blue color
Given the UNV toggle is active
Then the UNV toggle button text/border is blue (#3498db)
And the SN Dict and Single HL labels for UNV are blue

#### Scenario: KJV controls use teal color
Given the KJV toggle is active
Then the KJV toggle button text/border is teal (#1abc9c)
And the SN Dict and Single HL labels for KJV are teal

### Requirement: Independent Version Settings
Each version SHALL have independent SN Dict and Single HL checkbox settings.

#### Scenario: UNV SN Dict toggle
Given UNV is active with SN Dict enabled
When the user clicks on an SN in UNV content
Then tooltip is shown for the UNV SN
And KJV SN Dict setting does not affect UNV tooltips

#### Scenario: KJV Single HL mode
Given KJV is active with Single HL enabled
And UNV is active with Single HL disabled
When the user clicks an SN in KJV content
Then KJV highlights are cleared before new highlight
And UNV highlights accumulate (not cleared)

### Requirement: KJV Data Loading
The system SHALL fetch KJV+SN data from FHL API when KJV is activated.

#### Scenario: Load KJV chapter
Given the user has selected Genesis chapter 1
When the user activates the KJV toggle
Then the system fetches KJV data from bible.fhl.net with version=kjv and strong=1
And displays the KJV text with Strong's Numbers in the KJV content section

### Requirement: Cross-Version SN Highlighting
When an SN is clicked in the right panel, highlighting SHALL apply to all active versions in the left panel.

#### Scenario: Right panel click highlights both versions
Given UNV and KJV are both active in the left panel
When the user clicks on SN <WH0430> in the right panel parsed output
Then all occurrences of <WH0430> are highlighted in UNV content
And all occurrences of <WH0430> are highlighted in KJV content

## MODIFIED Requirements

### Requirement: Highlight Timeout Extended
The highlight/tooltip auto-clear timeout SHALL be 30 seconds instead of 10 seconds.

#### Scenario: Highlights persist for 30 seconds
Given the user has clicked on an SN and highlighting is active
When 25 seconds have passed
Then the highlighting remains visible
When 30 seconds have passed
Then the highlighting is automatically cleared

### Requirement: Left Panel Header Layout
The left panel header layout SHALL be updated to accommodate version toggles.

#### Scenario: Header without active versions
Given no version toggle is active
Then the header shows verse reference on the left
And toggle buttons [UNV] [KJV] on the right
And no checkbox controls in the middle

#### Scenario: Header with UNV only
Given only UNV toggle is active
Then the header shows: [Gen 1:4] □SN Dict □Single HL [UNV] [KJV]
And the checkbox labels are blue
And [UNV] button shows active state
