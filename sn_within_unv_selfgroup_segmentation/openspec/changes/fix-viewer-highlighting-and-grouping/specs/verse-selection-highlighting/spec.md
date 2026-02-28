# Spec: Verse Selection Highlighting

## Capability
Visual indication of selected verses in the left panel without obscuring Strong's Number color coding

## MODIFIED Requirements

### Requirement: System SHALL use border-only highlighting for selected verses
**Previous Behavior:** Selected verses displayed light blue background (#e3f2fd) that obscured SN background colors

**New Behavior:** Selected verses MUST display deep blue vertical borders at left and right edges with no background fill

**Rationale:** Background color interferes with the semantic group color coding of Strong's Numbers, reducing readability

#### Scenario: User clicks verse in left panel
**Given:** User is viewing Genesis chapter 1
**When:** User clicks on verse 2
**Then:**
- Verse 2 shows a deep blue (#2196f3) left border (3px solid)
- Verse 2 shows a deep blue (#2196f3) right border (3px solid)
- Verse 2 has **no background color**
- All Strong's Number color backgrounds remain fully visible
- Other verses revert to default styling (no borders, no background)

#### Scenario: Keyboard navigation changes selection
**Given:** Verse 2 is currently selected
**When:** User presses down arrow key to navigate to verse 3
**Then:**
- Verse 2 borders are removed
- Verse 3 shows deep blue left and right borders
- Strong's Number colors remain visible throughout transition

#### Scenario: Uncertain verse selection preserves warning indicators
**Given:** A verse marked as uncertain exists
**When:** User selects the uncertain verse
**Then:**
- Orange warning border (#f39c12) remains visible at left edge
- Deep blue selection borders appear at right edge (or adapt to not conflict)
- Uncertain badge in right panel displays
- Strong's Number colors remain visible

---

### Requirement: System MUST use visually distinct border styling without overwhelming content
**Rationale:** Borders MUST clearly indicate selection while keeping focus on content

#### Scenario: Selected verse with long text content
**Given:** User selects Genesis 1:28 (a long verse)
**When:** Verse renders in left panel
**Then:**
- Left border visible at top of verse
- Right border spans full height of verse
- Borders do not increase verse padding or cause layout shift
- Text remains aligned with non-selected verses

#### Scenario: Multiple rapid selections
**Given:** User quickly clicks through verses 1, 2, 3, 4
**When:** Each click triggers a selection change
**Then:**
- Only the most recent selection shows borders
- No visual glitches or flickering occurs
- Transition appears smooth (CSS transitions acceptable)
