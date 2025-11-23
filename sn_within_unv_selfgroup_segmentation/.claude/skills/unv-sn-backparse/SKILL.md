---
name: unv-sn-backparse
description: Parses Chinese Union Version (UNV) biblical text with Strong's Numbers into structured semantic groups according to SPECIFICATION_v1.6.md. Use when the user requests parsing UNV+SN verses, batch processing biblical text, or analyzing Strong's number groupings.
allowed-tools: Read, Write, Bash, Grep, Glob
---

# UNV+SN Backparse Skill (Specification v1.6)

This skill parses Chinese Union Version (UNV) biblical text with Strong's Numbers into structured semantic groups according to SPECIFICATION_v1.6.md.

## When to Use This Skill

Activate this skill when the user:
- Requests parsing of specific biblical verses (e.g., "parse Genesis 1:1", "parse all verses in Exodus 2")
- Wants to batch process a range of verses
- Needs to analyze Strong's number groupings in UNV text
- Asks about the parsing results or output format
- Requests verification of parsed output

## Core Architecture

The system uses a three-stage pipeline:

1. **Data Retrieval** (`fetch_text.sh`) - Fetches from FHL API endpoints
2. **Parsing** (`parse_verse_v1_6.py` or `run_parser_temp.py`) - Transforms raw data into structured groups
3. **Output Generation** - Saves to `output/{Book}/{Chapter}/{verse}.json` or `{verse}_uncertain`

## Parsing Workflow

### Single Verse Parsing

```bash
# Parse a single verse (e.g., Genesis 1:1)
python run_parser_temp.py 1 1

# View output without writing to disk
python run_parser_temp.py --no-write 1 1
```

### Batch Parsing

Follow the Batch_Parsing_SOP.md workflow:

1. **Create Output Directories**
   ```bash
   mkdir -p output/{Book}/{Chapter}/
   ```

2. **Determine Verse Range**
   - If only book is provided, automatically determine starting point
   - For existing book: continue from last processed verse
   - For new book: start from chapter 1, verse 1

3. **Iterate and Process Each Verse**
   ```bash
   for verse in {START..END}; do
       python run_parser_temp.py {chapter} $verse
   done
   ```

4. **Handle Uncertainty**
   - Files with ambiguity are named `{verse}_uncertain`
   - Append `--- UNCERTAINTY NOTES ---` section describing issues

5. **Verification**
   - Check all output files were created
   - Verify no unexpected `_uncertain` files
   - Spot-check sample outputs for correctness

## Output Format (UNV_SN_Output_Format.md)

Each parsed verse contains three sections:

### I. Parsed and Formatted Text Section
Traditional Chinese table format with:
- Individual Strong's numbers: `<NNNN> — [詞性]「[中文意義]」`
- With morphology: `<NNNN>(8xxx) — [詞性]「[中文意義]」 *N`
- Grouped numbers: `<NNNN><MMMM> — [詞性]「[中文意義]」`

### II. Raw UNV+SN Source Text Section
Original `bible_text` with WH/WTH/WAH prefixes preserved

### III. Morphology Notes Section
Detailed grammatical explanations: `*N: [詳細描述]`

## Key Parsing Rules (SPECIFICATION_v1.6.md)

### Token Classification

Three distinct token types with non-overlapping ranges:

1. **Core (Strong's)**: `<dddd>` or `{<dddd>}` - Numbers 1-8999 (excluding 8xxx, 9xxx)
2. **Morphology (8xxx)**: `(**8ddd)`, `{8ddd}` - Verbal stems, tenses
3. **Prefixes (900x)**: `<09ddd>` - Inseparable particles (ל־, ב־, ה־, etc.)

### Normalization (§3.1)

MUST perform before parsing:
1. Remove `WH/WTH/WAH` internal prefixes
2. Convert `<WTH8xxx>` to `(**8xxx)` (morphology codes)
3. Preserve `<09ddd>` as 900x prefixes
4. Recognize `{<dddd>}` as implicit core, `{8xxx}` as implicit morph

### Grouping Rules (§3.3)

**Scan Direction**: Left-to-right, ignoring punctuation/whitespace

1. **Prefix Attachment**: 900x codes enter `prefix_buffer`, skip over `{<...>}` and `{8xxx}`, attach to next core token

2. **Morphology Attachment**: Always left-attach to most recent core group

3. **Brace Preposition Decision Tree** (for `{<PREP>}` where PREP in `["05921","04480","0413","00996"]`):
   - **Exception 1 (Highest Priority)**: If `qp.wform` shows pronoun suffix OR infinitive complement → **left-attach to verb** (`post_brace`)
   - **Exception 2**: `{<0853>}` (object marker אֵת) → **always right-attach to noun** (`pre_brace`)
   - **General Case**: If right-side token (skipping 900x) is noun → **right-attach** (`pre_brace`); else independent group with warning

4. **Construct Linker** (optional v1.2-B): Link construct state nouns to following nouns using `construct_of`

## Configuration Profile (§4.1)

Hardcoded in `parse_verse_v1_6.py`:

```python
PROFILE = {
    "brace_preps": ["05921", "04480", "0413", "00996"],  # עַל, מִן, אֶל, בֵּין
    "object_marker": "0853",                              # אֵת
    "ignored_codes": ["09015"]                            # Paragraph markers
}
```

## Data Sources

**FHL API** (bible.fhl.net):
- `qb.php`: UNV text with Strong's numbers (requires Chinese book abbreviations)
- `qp.php`: Parsing/morphology data (requires English book abbreviations)

**Book Mappings**: 66 books with bidirectional lookup (Gen ↔ 創, Matt ↔ 太, etc.)

## Error Handling

### Uncertainty Detection

Mark files as `{verse}_uncertain` when:
- Strong's number from `qb.php` missing in `qp.php`
- Ambiguous brace preposition attachment
- Data inconsistencies between APIs
- Unresolvable grouping decisions

### Warning Types

Add to `warnings[]` array:
- `brace_attach_ambiguous`: Cannot determine preposition attachment
- `dangling_900x`: Prefix without core token
- `morph_without_core`: Orphaned morphology code
- `qb_qp_core_mismatch`: Data mismatch between APIs

## Important User Presentation Rules

**CRITICAL**: When showing parsed verse results to the user:

1. **Present all three sections in order** (Parsed Text → Raw Source → Morphology Notes)
2. **Display sections as-is** with no inserted commentary
3. **After all three sections**, you MAY add English explanations if helpful
4. **DO NOT** insert English translations or bullet points within the sections
5. **DO NOT** add commentary between sections

## Testing Strategy

**Verified Test Cases** (SPECIFICATION_v1.6.md §6):
- Gen 1:2 - Brace preposition right-attach + construct state
- Gen 1:4 - Object marker handling with multiple `{<0853>}`
- Gen 1:5 - FHL profile mapping with inferred vs explicit prefixes
- Gen 3:5 - Verb left-attach exception for infinitive complement

Validate parsed output against expected groupings in spec §6.

## Common Commands

```bash
# Fetch verse data
./fetch_text.sh --engs Gen --chap 1 --sec 1

# Parse single verse
python run_parser_temp.py 1 1

# Batch parse chapter (e.g., Genesis 2, verses 1-25)
mkdir -p output/Gen/2
for verse in {1..25}; do python run_parser_temp.py 2 $verse; done

# Verify outputs
ls -1 output/Gen/2/ | wc -l
ls -1 output/Gen/2/ | grep "_uncertain"

# View sample output
cat output/Gen/2/1
```

## Files and Dependencies

**Core Files**:
- `SPECIFICATION_v1.6.md` - Authoritative parsing rules
- `Batch_Parsing_SOP.md` - Batch processing workflow
- `UNV_SN_Output_Format_Gen_1_1.md` - Output format specification
- `fetch_text.sh` - API wrapper script
- `parse_verse_v1_6.py` - Current parser (outputs JSON)
- `run_parser_temp.py` - Batch orchestrator

**Dependencies**: `curl`, `jq`, Python 3

## Step-by-Step Execution Guide

When user requests parsing:

1. **Acknowledge Request**: Confirm book, chapter, verse range
2. **Create TodoList**: Track directory creation, parsing, verification
3. **Create Directories**: `mkdir -p output/{Book}/{Chapter}/`
4. **Execute Parsing**: Run appropriate batch command or single verse
5. **Verify Results**: Check file count, look for `_uncertain` files
6. **Show Samples**: Display 1-2 sample outputs for user review
7. **Report Completion**: Confirm range processed and any issues found

## Example Execution

```
User: "Parse Genesis chapter 3"

1. Create todo list with 4 items
2. mkdir -p output/Gen/3
3. Determine verse count (24 verses in Genesis 3)
4. Run: for verse in {1..24}; do python run_parser_temp.py 3 $verse; done
5. Verify: ls -1 output/Gen/3/ | wc -l (should show 24)
6. Check: ls -1 output/Gen/3/ | grep "_uncertain" (ideally 0)
7. Display: Show sample parsed output from verse 1 and 16
8. Report: "Successfully parsed Genesis 3:1-24 (24 verses, 0 uncertain)"
```

## Notes

- Parser is in **partial implementation** status; full v1.6 features may need enhancement
- Always consult SPECIFICATION_v1.6.md for authoritative rules
- Output location: `output/{Book}/{Chapter}/{verse}` or `{verse}_uncertain`
- This is a subdirectory of the larger Strong's Number Embedding Project
