# Spec: Strong's Number Group Color Coherence

## Capability
Apply consistent background colors to all components of a semantic group (core numbers, morphology codes, and braced markers)

## MODIFIED Requirements

### Requirement: Color mapper SHALL apply colors to morphology codes matching their parent Strong's Number
**Previous Behavior:** Morphology codes like `(8804)` appeared without background color, visually disconnected from their Strong's number

**New Behavior:** Morphology codes MUST display the same background color as their immediately preceding Strong's number

**Rationale:** Morphology codes provide grammatical context for Strong's numbers and MUST be visually grouped together

#### Scenario: Core Strong's number with morphology code
**Given:** Verse contains `<WH01254><WTH8804>` (verb + Qal Perfect morphology)
**When:** Color mapping applies group colors
**Then:**
- Both `<WH01254>` and `<WTH8804>` display the same background color
- The morphology code `(8804)` inherits the color assigned to group containing `01254`
- HTML rendering shows both wrapped in spans with matching `background-color` styles
- Visual appearance shows unified colored block for `<WH01254>(8804)`

#### Scenario: Multiple morphology patterns
**Given:** Verse contains various morphology patterns: `(**8804)`, `(*8765)`
**When:** Color mapping processes the raw text
**Then:**
- Pattern `(**8804)` inherits color from preceding SN
- Pattern `(*8765)` inherits color from preceding SN
- All variations of morphology notation are handled consistently

#### Scenario: Morphology code without Strong's number
**Given:** Edge case where morphology code appears standalone (shouldn't happen per spec but handle gracefully)
**When:** Color mapping encounters orphaned `(**8804)`
**Then:**
- Morphology code renders without background color (no match in colorMap)
- No JavaScript errors occur
- HTML escaping still applies correctly

---

### Requirement: Color mapper SHALL apply group colors to braced Strong's number patterns
**Previous Behavior:** Braced implicit markers like `{<WH0853>}` displayed without background color

**New Behavior:** Braced patterns MUST display background color matching their Strong's number code in the group colorMap

**Rationale:** Braced markers indicate implicit words (object markers, construct state) and MUST semantically belong to the group they modify

#### Scenario: Braced object marker with following noun
**Given:** Verse contains `{<WH0853>}<WH08064>` (implicit object marker + "heaven")
**When:** Color mapping assigns both to the same semantic group
**Then:**
- Both `{<WH0853>}` and `<WH08064>` display identical background color
- The braces `{` and `}` are included within the colored span
- Visual appearance shows unified colored block

#### Scenario: Braced pattern in construct state
**Given:** Verse contains `{<05921>}<06440>` (brace preposition + noun)
**When:** Color mapping processes according to parsed groups
**Then:**
- Both components share the same background color if in same group
- OR each has distinct color if parsed as separate groups
- Consistency matches the parsed output section grouping

#### Scenario: Mixed braced and unbraced in sequence
**Given:** Verse contains `<WH0430>{<WH0853>}<WH08064>`
**When:** Color mapping applies
**Then:**
- `<WH0430>` gets group 1 color (e.g., #FFF3E0)
- `{<WH0853>}<WH08064>` get group 2 color (e.g., #E8F5E9)
- Visual distinction between groups remains clear
- All components within each group share colors

---

### Requirement: Color mapper MUST maintain color coherence with parsed output grouping
**Rationale:** Left panel (raw text) and right panel (parsed output) MUST show consistent semantic grouping

#### Scenario: Cross-panel group verification
**Given:** User selects Genesis 1:1
**When:** Parsed output shows `<01254>(8804)` as a single group with light green background
**Then:**
- Left panel raw text also shows `<WH01254><WTH8804>` with matching light green background
- User can visually correlate groups between panels
- Color consistency aids in understanding the parsing logic

#### Scenario: Complex multi-token group
**Given:** Parsed output shows `{<0853>}<08064>` as one group
**When:** Raw text renders in left panel
**Then:**
- Both `{<WH0853>}` and `<WH08064>` display the same background color
- Matches the color shown in parsed output section
- No confusion about group boundaries
