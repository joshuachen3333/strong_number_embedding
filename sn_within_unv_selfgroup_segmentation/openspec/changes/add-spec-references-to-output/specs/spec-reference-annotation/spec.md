# Spec: Specification Reference Annotation

## Capability
Display SPECIFICATION_v1.8 rule references in parsed output to trace which parsing rules created each semantic group

## ADDED Requirements

### Requirement: Parser SHALL verify version consistency between code and SPECIFICATION file
**Rationale:** Prevent mismatched parser-spec pairs that could produce incorrect references

#### Scenario: Parser loads matching SPECIFICATION file
**Given:** Parser declares `PARSER_VERSION = "v1.8"`
**And:** File `SPECIFICATION_v1.8.md` exists with first line containing `v1.8`
**When:** Parser loads specification metadata
**Then:**
- Version validation passes
- Parser continues initialization
- Prints success message: `✓ Loaded SPECIFICATION_v1.8.md (parser v1.8)`

#### Scenario: SPECIFICATION file not found
**Given:** Parser declares `PARSER_VERSION = "v1.8"`
**And:** File `SPECIFICATION_v1.8.md` does NOT exist
**When:** Parser attempts to load specification metadata
**Then:**
- Raises `FileNotFoundError` with message indicating missing file
- Error message includes expected filename
- Parser initialization fails immediately

#### Scenario: Version mismatch between parser and SPECIFICATION
**Given:** Parser declares `PARSER_VERSION = "v1.8"`
**And:** File `SPECIFICATION_v1.8.md` exists but first line contains `v1.9`
**When:** Parser loads specification metadata
**Then:**
- Raises `ValueError` with message indicating version mismatch
- Error message shows both parser version and spec file version
- Parser initialization fails before processing any verses

---

### Requirement: Parser output SHALL include specification version in section header
**Rationale:** Users need to know which version of the specification was used to parse the verse, as parsing rules evolve across versions

#### Scenario: User views parsed output
**Given:** Parser processes a verse using SPECIFICATION_v1.8 rules
**When:** Output is formatted as text
**Then:**
- Section header displays `Parsed and Formatted Text Section (SPECIFICATION_v1.8)`
- Version indicator appears in parentheses immediately after section name
- No other sections (Raw UNV+SN, Morphology Notes) include version indicators

---

### Requirement: Multi-token groups SHALL display spec section reference right-aligned
**Previous Behavior:** No indication of which parsing rule created each group
**New Behavior:** Groups with 2+ Strong's Numbers display spec section reference at column 80
**Rationale:** Multi-token groups result from applying grouping rules; single-token groups do not

#### Scenario: Group created by prefix attachment rule
**Given:** Group contains prefix `<09002>` and core `<07225>` (2 tokens)
**When:** Output is formatted
**Then:**
- Line displays `<09002><07225> — 介系詞 בְּ + 名詞「開始、首要」` followed by spaces and `[3.3.1]`
- Spec reference `[3.3.1]` is right-aligned at column 80
- Reference corresponds to §3.3.1 "Prefix Attachment" in SPECIFICATION_v1.8.md

#### Scenario: Group created by morphology attachment rule
**Given:** Group contains core `<01254>` and morphology code `(8804)` (2 components)
**When:** Output is formatted
**Then:**
- Line displays `<01254>(8804) — 動詞「Qal 創造...」 *1` followed by `[3.3.2]`
- Spec reference `[3.3.2]` corresponds to §3.3.2 "Morphology Attachment"
- Morphology note marker `*1` appears before spec reference

#### Scenario: Group created by object marker rule
**Given:** Group contains object marker `{<0853>}` and noun `<08064>` (2 tokens)
**When:** Output is formatted
**Then:**
- Line displays `{<0853>}<08064> — 冠詞 הַ + 名詞「天」` followed by `[3.3.3]`
- Spec reference `[3.3.3]` corresponds to §3.3.3 object marker rule (Exception 2)

#### Scenario: Single-token group
**Given:** Group contains only core `<0430>` (1 token)
**When:** Output is formatted
**Then:**
- Line displays `<0430> — 名詞「上帝、神、神明」` with NO spec reference
- No alignment padding added
- Line ends immediately after description

---

### Requirement: Spec reference format SHALL use square brackets with section number only
**Rationale:** Concise format saves horizontal space while maintaining clear reference to specification

#### Scenario: Format validation
**Given:** Any multi-token group
**When:** Spec reference is appended
**Then:**
- Format is `[d.d.d]` or `[d.d]` where d = decimal digit(s)
- No prefix text like "§" or "Section" or "SPEC"
- No parentheses or other delimiters
- Examples: `[3.3.1]`, `[3.3.2]`, `[3.3]`, `[3.4.5]`

---

### Requirement: Parser SHALL extract section mappings from SPECIFICATION markdown file
**Rationale:** Automatic extraction from authoritative source ensures single source of truth

#### Scenario: Extract sections from HTML comment tags (preferred strategy)
**Given:** SPECIFICATION_v1.8.md contains tagged sections:
```markdown
### 3.3 複合介系詞檢測與合併 <!-- spec:compound -->
#### 3.3.1 檢測算法 <!-- spec:prefix -->
```
**When:** Parser loads specification metadata
**Then:**
- Extracts mapping: `{'compound': '3.3', 'prefix': '3.3.1'}`
- Uses regex pattern to match `<!-- spec:rule_name -->`
- Ignores untagged sections
- Returns complete section mapping dict

#### Scenario: Fallback to known section numbers when tags absent
**Given:** SPECIFICATION_v1.8.md has NO HTML comment tags
**And:** Parser defines fallback mappings for v1.8
**When:** Parser loads specification metadata
**Then:**
- Tag extraction returns empty dict
- Falls back to `KNOWN_SECTIONS_V18` hardcoded mappings
- Logs warning: "No spec tags found, using fallback detection"
- Returns fallback section mapping dict

#### Scenario: Mixed tagged and untagged sections
**Given:** SPECIFICATION_v1.8.md has some sections tagged, others not
**When:** Parser loads specification metadata
**Then:**
- Extracts all tagged sections
- Does NOT attempt to infer untagged sections
- Returns partial mapping with only tagged rules
- Missing rules handled gracefully in `determine_spec_rule()` with `.get()`

---

### Requirement: System SHALL determine spec rule from group metadata
**Rationale:** Rule determination must be based on group structure, not heuristics

#### Scenario: Rule priority order
**Given:** Group may match multiple rule conditions
**When:** Determining which spec reference to display
**Then:**
- Apply priority order: compound → object marker → post-brace → pre-brace → morphology → prefix → construct → none
- Select first matching rule
- Example: Group with both prefix and morphology shows `[3.3.2]` (morphology takes priority over prefix)

#### Scenario: Compound preposition
**Given:** Group has `compound: true` metadata
**When:** Formatting output
**Then:**
- Displays spec reference `[3.3]` (compound detection section)
- Takes highest priority over other rules

#### Scenario: Brace preposition right-attach
**Given:** Group has `pre_brace: ['05921']` (not object marker)
**When:** Formatting output
**Then:**
- Displays spec reference `[3.3.4.1]` (brace prep right-attach)

#### Scenario: Brace preposition left-attach
**Given:** Group has `post_brace: ['04480']`
**When:** Formatting output
**Then:**
- Displays spec reference `[3.3.4.2]` (brace prep left-attach with pronoun suffix)

---

### Requirement: Alignment SHALL target column 80 with minimum 2-space gap
**Rationale:** Consistent visual alignment improves readability; minimum gap prevents spec reference from running into description

#### Scenario: Short description line
**Given:** Base line is `<0430> — 名詞「上帝」` (20 characters)
**When:** No spec reference needed (single token)
**Then:**
- No padding added
- Line length = 20 characters

#### Scenario: Medium description line
**Given:** Base line is `<09002><07225> — 介系詞 בְּ + 名詞「開始、首要」` (50 characters)
**When:** Spec reference `[3.3.1]` needed
**Then:**
- Padding of ~23 spaces added
- Spec reference starts at column 73-74
- Total line length ≈ 80 characters

#### Scenario: Very long description line
**Given:** Base line is 95 characters (exceeds target)
**When:** Spec reference `[3.3.1]` needed
**Then:**
- Minimum 2 spaces added before spec reference
- Total line length = 95 + 2 + 7 = 104 characters
- No line breaking or truncation occurs
