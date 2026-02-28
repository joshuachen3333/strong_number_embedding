# Spec: Morphology Pattern Specificity

## MODIFIED Requirements

### Requirement: Morphology code pattern MUST only match actual morphology codes

The morphology code regex pattern SHALL only match actual morphology code formats and MUST NOT match core Strong's Numbers.

Morphology codes in the viewer have specific formats that distinguish them from core Strong's Numbers:
1. **Tagged format**: `<WTH8xxx>` where xxx are 3 digits (e.g., `<WTH8799>`)
2. **Parenthesized format**: `(8xxx)` or `(**8xxx)` where xxx are 3 digits (e.g., `(8799)`, `(**8804)`)

The regex pattern for morphology codes must:
- Match braced or unbraced WTH tags: `{<WTH8799>}` or `<WTH8799>`
- Match parenthesized codes with optional asterisks: `(8799)` or `(**8799)`
- NOT match core Strong's Numbers like `{<WH04325>}` or `{<WAH09001>}`

**Pattern specification:**
```regex
(\{?<WTH8\d{3}>\}?|\(\*?\*?8\d{3}\))?
```

Breaking down the pattern:
- `\{?<WTH8\d{3}>\}?` - Matches `{<WTH8799>}` or `<WTH8799>` (braced optional, WTH prefix required, 8 + 3 digits)
- `\(\*?\*?8\d{3}\)` - Matches `(8799)` or `(**8799)` (parentheses required, optional asterisks, 8 + 3 digits)
- `?` at the end - Makes entire morphology part optional

#### Scenario: Multi-SN group with consecutive braced tokens

**Given** a parsed output group `<WAH09001><WH04325>` containing two SNs ['09001', '04325']
**And** raw text showing `{<WAH09001>}{<WH04325>}` as consecutive braced tokens
**When** the color mapping algorithm processes the raw text
**Then** both `{<WAH09001>}` and `{<WH04325>}` must be colored with the same group color
**And** the pattern for `{<WAH09001>}` must NOT consume `{<WH04325>}` as a morphology code

#### Scenario: Morphology code following core SN

**Given** a parsed output `<WAH01961>(8799)` containing SN '01961' with morphology '8799'
**And** raw text showing `{<WAH01961>}{<WTH8799>}` as braced tokens
**When** the color mapping algorithm processes the raw text
**Then** both `{<WAH01961>}` and `{<WTH8799>}` must be matched as a single unit
**And** they must be colored with the same group color

#### Scenario: Clicking on second token in multi-SN group

**Given** a group containing ['09001', '04325'] displayed as `{<WAH09001>}{<WH04325>}` on left
**And** displayed as `<WAH09001><WH04325>` on right
**When** user clicks on `{<WH04325>}` in the left panel
**Then** the system must identify the group as ['09001', '04325']
**And** highlight the right panel's `<WAH09001><WH04325>` in orange
**And** highlight both `{<WAH09001>}` and `{<WH04325>}` in blue on the left

## Implementation Notes

**Functions requiring updates in `color_mapper.js`:**

1. `applyColorsToRawTextLegacy()` - Line ~232
2. `colorSNsInSpan()` - Line ~255
3. `applyFallbackColoring()` - Line ~273
4. `buildRegexPattern()` - Line ~140

**Pattern change in all 4 locations:**
```javascript
// OLD (greedy - matches any digits):
(\{?<W[AT]*H?\d+>\}?|\(\*?\*?\d+\))?

// NEW (specific - only matches morphology codes):
(\{?<WTH8\d{3}>\}?|\(\*?\*?8\d{3}\))?
```

**Why this works:**
- `WTH` prefix is only used for morphology codes, never for core SNs
- Morphology codes are always 4 digits starting with 8 (8000-8999 range)
- Core SNs use `WH` or `WAH` prefixes (never `WTH`)
- Core SNs have various digit lengths (1-5 digits) and ranges (0001-09999)

**Test data from Gen 1:6:**
- `{<WAH09001>}{<WH04325>}` - Should be matched as TWO separate tokens (both core SNs)
- `{<WAH01961>}{<WTH8799>}` - Should be matched as ONE token (core SN + morphology)
- `<WAH01961><WTH8799>` - Should be matched as ONE token (core SN + morphology)
- `<WAH01961>(8799)` - Should be matched as ONE token (core SN + morphology)
