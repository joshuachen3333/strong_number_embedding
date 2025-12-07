# Spec: Position-Aware Interleaved Text Extraction

## MODIFIED Requirements

### Requirement: Extract interleaved text from unique token occurrences

The `extract_interleaved_text()` function MUST extract text only from the specific occurrence of tokens that belong to the current group, not from earlier occurrences of the same token in previous groups.

**Related**: `interleaved-text-display` (from `add-spec-references-to-output`)

#### Scenario: Two groups with identical leading tokens

**Given** a verse with raw text `{<WH0853>}天<WH08064>{<WH0853>}地<WH0776>`

**And** Group 1 is `{<0853>}<08064>` (天)

**And** Group 2 is `{<0853>}<0776>` (地)

**When** extracting interleaved text for Group 1

**Then** the function MUST find `{<WH0853>}` at position 0 and `<WH08064>` at position 11

**And** return `::{<0853>}天<08064>::` (without prefix stripping applied)

**When** extracting interleaved text for Group 2

**Then** the function MUST skip the `{<WH0853>}` at position 0 (already consumed by Group 1)

**And** find the second `{<WH0853>}` at position 20 and `<WH0776>` at position 30

**And** return `::{<0853>}地<0776>::` (without prefix stripping applied)

**And** NOT return `::{<0853>}天<08064>{<0853>}地<0776>::`

---

#### Scenario: Three groups with identical tokens

**Given** a verse with three groups containing the same token pattern

**And** raw text contains three occurrences of token `{<WH0853>}`

**When** extracting interleaved text for Group 1, Group 2, and Group 3 sequentially

**Then** Group 1 MUST use the first occurrence

**And** Group 2 MUST skip the first occurrence and use the second occurrence

**And** Group 3 MUST skip the first and second occurrences and use the third occurrence

**And** each group's extracted text MUST NOT overlap with other groups' tokens

---

#### Scenario: No duplicate tokens (regression test)

**Given** a verse where all groups contain unique tokens

**When** extracting interleaved text with position tracking enabled

**Then** the behavior MUST be identical to extraction without position tracking

**And** all existing test cases (Gen 1:2, 1:5, 3:5, 4:16) MUST pass unchanged

---

### Requirement: Track consumed positions across groups

The formatting function MUST maintain a set of consumed character positions and pass it to each interleaved text extraction call.

#### Scenario: Initialize consumed positions tracking

**Given** the `format_groups_to_text()` function is called

**When** starting to process groups

**Then** a consumed positions set MUST be initialized as an empty set

**And** the set MUST persist across all group iterations in the same verse

---

#### Scenario: Mark positions as consumed after extraction

**Given** `extract_interleaved_text()` successfully extracts text from positions 10-25

**When** the extraction completes

**Then** the range (10, 25) MUST be added to the consumed positions set

**And** subsequent extractions MUST skip any tokens overlapping this range

---

#### Scenario: Handle failed extraction without marking positions

**Given** `extract_interleaved_text()` cannot find valid tokens (all occurrences already consumed)

**When** the extraction fails and returns None

**Then** no positions MUST be added to the consumed positions set

**And** the consumed positions set MUST remain unchanged

---

### Requirement: Skip tokens in consumed positions during search

The token search logic MUST check if a found position overlaps with any consumed range and continue searching if it does.

#### Scenario: Skip consumed token occurrence

**Given** token `{<WH0853>}` appears at positions 0 and 20

**And** consumed positions contains range (0, 15)

**When** searching for `{<WH0853>}`

**Then** the search MUST find position 0 first

**And** detect overlap with consumed range (0, 15)

**And** continue searching from position 15

**And** return position 20 (the second occurrence)

---

#### Scenario: Detect partial overlap with consumed range

**Given** a token spans positions 18-28

**And** consumed positions contains range (10, 20)

**When** checking if position 18 is consumed

**Then** the function MUST detect overlap (18 < 20 and 28 > 10)

**And** treat the position as consumed

**And** continue searching for the next occurrence

---

#### Scenario: Multiple consumed ranges

**Given** consumed positions contains ranges (0, 15), (20, 30), (40, 50)

**And** searching for a token that appears at positions 5, 25, 45, 60

**When** performing token search

**Then** position 5 MUST be skipped (overlaps 0-15)

**And** position 25 MUST be skipped (overlaps 20-30)

**And** position 45 MUST be skipped (overlaps 40-50)

**And** position 60 MUST be returned (no overlap)

---

### Requirement: Maintain backward compatibility

The modified function MUST maintain backward compatibility when consumed positions tracking is not used.

#### Scenario: Call without consumed positions parameter

**Given** `extract_interleaved_text(group, bible_text_raw)` is called without the third parameter

**When** the function executes

**Then** it MUST initialize an empty consumed positions set internally

**And** function as before without affecting other calls

**And** no positions MUST be tracked across calls

---

#### Scenario: Existing call sites continue to work

**Given** code that calls `extract_interleaved_text(group, bible_text_raw)` with two parameters

**When** the function signature changes to add optional `consumed_positions` parameter

**Then** the existing call MUST continue to work without modification

**And** the function MUST use default empty set behavior

---

### Requirement: Handle edge cases gracefully

The extraction logic MUST handle edge cases without crashing or producing incorrect results.

#### Scenario: All token occurrences already consumed

**Given** a group with tokens `{<0853>}` and `<0776>`

**And** all occurrences of both tokens are in consumed positions

**When** extracting interleaved text

**Then** the search MUST return -1 (not found)

**And** the function MUST return None

**And** no error MUST be raised

---

#### Scenario: Tokens appear in different order than groups

**Given** raw text `<WH1111>A{<WH0853>}B<WH2222>`

**And** Group 1 is `<2222>`

**And** Group 2 is `<1111>{<0853>}`

**When** processing Group 1 first (position 18-28)

**And** marking range (18, 28) as consumed

**Then** Group 2 extraction MUST find `<1111>` at position 0 and `{<0853>}` at position 8

**And** NOT be affected by Group 1's later position in the text

---

#### Scenario: Single token group (no interleaving)

**Given** a group with only one token

**When** extracting interleaved text

**Then** the function MUST return None (existing behavior)

**And** no positions MUST be added to consumed positions

**And** consumed positions tracking MUST have no effect
