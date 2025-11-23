# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**UNV+SN Parsing System** - Parses Chinese Union Version (UNV) biblical text with Strong's Numbers into structured semantic groups. This system processes verses from the FHL (Faith, Hope, Love) API at `bible.fhl.net`, tokenizes Strong's numbers, morphology codes, and prefixes, then outputs formatted data according to specification SPECIFICATION_v1.6.md.

## Core Architecture

The system follows a three-stage pipeline:

1. **Data Retrieval** (`fetch_text.sh`) - Fetches verse data from two FHL API endpoints:
   - `qb.php` - Returns UNV text with Strong's numbers (requires Chinese book abbreviations)
   - `qp.php` - Returns parsing/morphology data (requires English book abbreviations)

2. **Parsing** (`parse_verse_v1_6.py` or `parse_verse.py`) - Transforms raw API data into structured groups:
   - **Normalization**: Removes `WH/WTH/WAH` prefixes, converts `<WTH8xxx>` to `(**8xxx)`
   - **Tokenization**: Classifies tokens into core (Strong's 1-8999), morphology (8xxx), and prefixes (900x)
   - **Grouping**: Applies complex attachment rules for brace prepositions, object markers, and construct state

3. **Output Generation** (`run_parser_temp.py`) - Orchestrates parsing and file I/O:
   - Calls `fetch_text.sh` to retrieve data
   - Invokes parser with JSON payloads
   - Saves results to `output/{Book}/{Chapter}/{verse}.json` or `{verse}_uncertain`

## Running Commands

### Fetch Bible Verse Data

```bash
# Default (John 3:16)
./fetch_text.sh

# By English abbreviation
./fetch_text.sh --engs Gen --chap 1 --sec 1

# By Chinese abbreviation
./fetch_text.sh --chineses 創 --chap 1 --sec 1

# List all 66 book abbreviations
./fetch_text.sh --list
```

**Dependencies**: `curl`, `jq`

### Parse a Single Verse

```bash
# Using run_parser_temp.py (recommended workflow)
python run_parser_temp.py 1 1  # Genesis 1:1 (default book is Gen)

# Just view output without writing to disk
python run_parser_temp.py --no-write 1 1

# Direct parser invocation (advanced)
python parse_verse_v1_6.py '<qb_json>' '<qp_json>'
```

### Batch Parsing

Currently manual iteration. See `Batch_Parsing_SOP.md` for the workflow:
1. Create output directories: `mkdir -p output/{Book}/{Chapter}/`
2. Iterate verses: fetch → parse → write with uncertainty handling
3. Files named `{verse}` (success) or `{verse}_uncertain` (with warning notes)

## Token Classification System

Three distinct token types with **non-overlapping numeric ranges**:

- **Core (Strong's)**: `<dddd>` or `{<dddd>}` (implicit) - Numbers 1-8999 (excluding 8xxx, 9xxx)
- **Morphology (8xxx)**: `(**8ddd)`, `{8ddd}` - Verbal stems, tenses (e.g., 8804 = Qal Perfect)
- **Prefixes (900x)**: `<09ddd>` - Inseparable particles (09001 = ל־, 09002 = ב־, 09009 = ה־)

**Critical**: `<WTH8804>` must be normalized to `(**8804)` before tokenization to avoid misclassification as core.

## Grouping Rules (SPECIFICATION_v1.6.md §3.3)

**Scan Direction**: Left-to-right, ignoring punctuation/whitespace.

**Prefix Attachment**: 900x codes enter `prefix_buffer` and skip over `{<...>}` and `{8xxx}` until attaching to the next core token.

**Morphology Attachment**: Always left-attach to the most recent core group.

**Brace Preposition Decision Tree** (`{<PREP>}` where PREP in `["05921","04480","0413","00996"]`):

1. **Exception 1 (Highest Priority)**: If `qp.wform` shows pronoun suffix (e.g., מִמֶּנּוּ) OR infinitive complement context → **left-attach to verb** (`post_brace`)
2. **Exception 2**: `{<0853>}` (object marker אֵת) → **always right-attach to noun** (`pre_brace`)
3. **General Case**: If right-side token (skipping 900x) is noun → **right-attach** (`pre_brace`); else create independent group with warning

## Output Formats

**IMPORTANT - Presenting Parser Output to User**:
- When showing parsed verse results, present the **three-section output in order**:
  1. **Parsed and Formatted Text Section** (Traditional Chinese table) - display as-is, no commentary
  2. **Raw UNV+SN Source Text Section** - display as-is, no commentary
  3. **Morphology Notes Section** (with *1, *2, *3...) - display as-is
- **After all three sections are displayed**, you MAY add English explanations or commentary if helpful.
- **DO NOT insert English explanations** between or before the three sections.
- **DO NOT add bullet points or translations** in the first two sections.

**v1.6 Parser** (`parse_verse_v1_6.py`) - Supports dual output formats:

1. **Text Format (default)** - Three-section Traditional Chinese output per `UNV_SN_Output_Format.md`:
   ```
   Parsed and Formatted Text Section:
   <09002><07225> — 介系詞片語「起初」
   <0430> — 名詞「上帝、神、神明」

   Raw UNV+SN Source Text Section:
   {<WAH0430>}就把這些光<WAH0853>擺列<WH05414><WTH8799>...

   Morphology Notes Section:
   *1: 動詞，Qal 完成式 3 單陽
   ```

2. **JSON Format (optional with `--json` flag)** - Data structure per SPECIFICATION_v1.6.md §4.2:
   ```json
   [
     {
       "core": "0430",
       "implicit": false,
       "prefixes": ["09002"],
       "morph": ["8804"],
       "pre_brace": [],
       "post_brace": [],
       "warnings": []
     }
   ]
   ```

**Legacy Parser** (`parse_verse.py`): Same three-section text format as v1.6 text mode.

## Configuration Profile

From SPECIFICATION_v1.6.md §4.1 (hardcoded in `parse_verse_v1_6.py`):

```python
PROFILE = {
    "brace_preps": ["05921", "04480", "0413", "00996"],  # עַל, מִן, אֶל, בֵּין
    "object_marker": "0853",                              # אֵת
    "ignored_codes": ["09015"]                            # Paragraph markers
}
```

## File Responsibilities

- **SPECIFICATION_v1.6.md**: Authoritative parsing rules (latest version, replaces v1.4/v1.5)
- **fetch_text.sh**: API wrapper with English ↔ Chinese book name translation
- **parse_verse_v1_6.py**: Current parser implementing v1.6 spec (outputs JSON)
- **parse_verse.py**: Legacy parser (outputs human-readable text format)
- **run_parser_temp.py**: Batch orchestrator pointing to `parse_verse_v1_6.py`
- **Batch_Parsing_SOP.md**: Workflow for batch processing with uncertainty handling
- **UNV_SN_Output_Format_Gen_1_1.md**: Output format spec for legacy parser

## Data Sources

**FHL API** (bible.fhl.net):
- `qb.php` parameters: `version=unv`, `chineses=創`, `chap=1`, `sec=1`, `strong=1`
- `qp.php` parameters: `engs=Gen`, `chap=1`, `sec=1`

**Book Mappings**: 66 books with bidirectional English/Chinese lookup (Gen ↔ 創, Matt ↔ 太, 1Sam ↔ 撒上, etc.) embedded in `fetch_text.sh`.

## Implementation Status

**v1.6 Parser**: Partial implementation. `parse_verse_v1_6.py:73-110` contains placeholder logic for grouping. Full implementation requires:
- State machine for brace preposition decision tree
- qp.php consultation for verb/noun detection
- Construct state linking (optional v1.2-B feature)
- Comprehensive warning generation

**Legacy Parser**: Functional but does not implement v1.6 brace attachment rules or 900x skipping behavior.

## Testing Strategy

**Verified Test Cases** (from SPECIFICATION_v1.6.md §6):
- Gen 1:2 - Brace preposition right-attach + construct state
- Gen 1:4 - Object marker handling with multiple `{<0853>}`
- Gen 1:5 - FHL profile mapping with inferred vs explicit prefixes
- Gen 3:5 - Verb left-attach exception for infinitive complement

Run test verses with `run_parser_temp.py --no-write 1 2` and validate against expected groupings in spec §6.

## Parent Project Context

This directory is a subdirectory of the larger **Strong's Number Embedding Project** (see `/Users/joshua/work/strong_number_embedding/CLAUDE.md`). The parent project includes:
- `original_text_preparation/` - SQLite extraction toolkit
- `dual_reader/` - Web-based Bible reader with Strong's support
- `dual_reader_right_editor/` - Advanced reader with edit mode

This directory focuses exclusively on UNV parsing logic; dual readers consume processed data for visualization.
