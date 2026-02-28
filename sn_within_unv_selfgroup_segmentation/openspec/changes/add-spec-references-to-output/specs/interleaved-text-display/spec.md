# Spec: Interleaved Text Display

## Capability
Display original text arrangement when Strong's Number tokens have Chinese characters interleaved between them

## ADDED Requirements

### Requirement: System SHALL detect interleaved text patterns in multi-token groups
**Rationale:** Some groups have tokens separated by Chinese text in the original verse (e.g., `{<0853>}天<08064>`); showing this helps users understand token positioning

#### Scenario: Object marker with interleaved noun
**Given:** Group contains `{<0853>}<08064>` with raw text `{<WH0853>}天<WH08064>`
**When:** Checking for interleaved pattern
**Then:**
- Detects Chinese character `天` between tokens `{<WH0853>}` and `<WH08064>`
- Identifies this as an interleaved pattern
- Marks group for interleaved text display

#### Scenario: Adjacent tokens without interleaving
**Given:** Group contains `<09002><07225>` with raw text `<WAH09002><WH07225>`
**When:** Checking for interleaved pattern
**Then:**
- Detects tokens are adjacent (no Chinese characters between)
- Does NOT identify as interleaved pattern
- No interleaved text display needed

#### Scenario: Token followed by Chinese
**Given:** Group contains `<01254>(8804)` with raw text `創造<WH01254><WTH8804>`
**When:** Checking for interleaved pattern
**Then:**
- Chinese `創造` appears before tokens, not between them
- Does NOT identify as interleaved pattern
- No interleaved text display needed

---

### Requirement: Interleaved text SHALL be extracted from raw UNV+SN source
**Rationale:** Parser-normalized tokens may not preserve original text arrangement; raw source is authoritative

#### Scenario: Extract object marker interleaved text
**Given:** Group `{<0853>}<08064>` with raw text containing `{<WH0853>}天<WH08064>`
**When:** Extracting interleaved snippet
**Then:**
- Locates `{<WH0853>}` in raw text
- Locates `<WH08064>` in raw text
- Extracts substring from first token start to last token end: `{<WH0853>}天<WH08064>`
- Strips internal prefixes: `{<0853>}天<08064>`
- Returns cleaned snippet

#### Scenario: Extraction failure fallback
**Given:** Group has interleaved pattern but raw text cannot be reliably extracted (e.g., duplicate SNs)
**When:** Extraction fails or returns ambiguous result
**Then:**
- Returns `None` for interleaved text
- Does not display interleaved section
- Does not fail entire line formatting
- Logs warning to debug output (optional)

---

### Requirement: Interleaved text SHALL be displayed with double-colon delimiters
**Rationale:** Delimiters visually distinguish interleaved text from main description and spec reference

#### Scenario: Display interleaved text with delimiters
**Given:** Extracted interleaved text is `{<0853>}天<08064>`
**When:** Formatting output line
**Then:**
- Displays `::{<0853>}天<08064>::` with leading 4 spaces after description
- Double colons on both sides clearly mark the snippet
- Example: `{<0853>}<08064> — 冠詞 הַ + 名詞「天」    ::{<0853>}天<08064>::               [3.3.3]`

#### Scenario: Line without interleaved text
**Given:** Group has no interleaved pattern
**When:** Formatting output line
**Then:**
- No `::` delimiters displayed
- No extra spacing added for interleaved section
- Example: `<09002><07225> — 介系詞 בְּ + 名詞「開始、首要」                              [3.3.1]`

---

### Requirement: Interleaved text SHALL only display for groups with 2+ tokens
**Rationale:** Single-token groups cannot have interleaving by definition

#### Scenario: Single-token group
**Given:** Group contains only `<0430>`
**When:** Checking for interleaved pattern
**Then:**
- Skips interleaved detection (insufficient tokens)
- No interleaved text displayed
- Line format: `<0430> — 名詞「上帝、神、神明」`

#### Scenario: Two-token group with morphology code
**Given:** Group contains `<01254>(8804)` where `(8804)` is morphology code attached to `<01254>`
**When:** Checking for interleaved pattern
**Then:**
- Morphology codes are part of the same token as preceding SN
- Treats as effectively 1 semantic token
- Only checks if multiple separate SN tokens exist with Chinese between them

---

### Requirement: Internal prefixes SHALL be stripped from interleaved text
**Rationale:** Output uses canonical SN codes without WH/WAH/WTH prefixes for consistency

#### Scenario: Strip WH prefix
**Given:** Raw text snippet is `<WH08064>`
**When:** Cleaning for display
**Then:**
- Removes `WH` prefix
- Returns `<08064>`

#### Scenario: Strip WAH prefix
**Given:** Raw text snippet is `{<WAH0853>}`
**When:** Cleaning for display
**Then:**
- Removes `WAH` prefix from inside braces
- Returns `{<0853>}`

#### Scenario: Strip WTH prefix (morphology marker)
**Given:** Raw text snippet is `<WTH8804>`
**When:** Cleaning for display
**Then:**
- Removes `WTH` prefix
- Converts to morphology notation if needed: `(8804)` or `(**8804)`
- Note: This scenario may not occur in interleaved text (morphology codes don't interleave)

---

### Requirement: Interleaved text positioning SHALL not break spec reference alignment
**Rationale:** Adding interleaved text should not disrupt right-alignment of spec references

#### Scenario: Line with both interleaved text and spec reference
**Given:** Base line is `{<0853>}<08064> — 冠詞 הַ + 名詞「天」` (35 chars)
**And:** Interleaved text is `::{<0853>}天<08064>::` (16 chars with spacing)
**And:** Spec reference is `[3.3.3]` (7 chars)
**When:** Formatting complete line with 80-char target
**Then:**
- Components: base (35) + interleaved (16) + padding (~22) + spec (7) = ~80 chars
- Spec reference still right-aligned at column ~73-80
- Visual example:
  ```
  {<0853>}<08064> — 冠詞 הַ + 名詞「天」    ::{<0853>}天<08064>::               [3.3.3]
  ```

#### Scenario: Long line with interleaved text exceeding 80 chars
**Given:** Base line + interleaved text = 85 characters
**And:** Spec reference needs to be added
**When:** Formatting line
**Then:**
- Uses minimum 2-space gap before spec reference
- Total line length = 85 + 2 + 7 = 94 characters
- Spec reference appears at column 87
- No truncation or line wrapping occurs
