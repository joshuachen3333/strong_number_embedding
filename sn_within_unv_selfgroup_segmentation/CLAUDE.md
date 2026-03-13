<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**UNV+SN Parsing System** - Parses Chinese Union Version (UNV) biblical text with Strong's Numbers into structured semantic groups. This system processes verses from the FHL (Faith, Hope, Love) API at `bible.fhl.net`, tokenizes Strong's numbers, morphology codes, and prefixes, then outputs formatted data according to specification SPECIFICATION_v1.8.md.

## Core Architecture

The system follows a three-stage pipeline:

1. **Data Retrieval** (`fetch_text.sh`) - Fetches verse data from two FHL API endpoints:
   - `qb.php` - Returns UNV text with Strong's numbers (requires Chinese book abbreviations)
   - `qp.php` - Returns parsing/morphology data (requires English book abbreviations)

2. **Parsing** (`parse_verse_v1_8.py`) - Transforms raw API data into structured groups:
   - **Normalization**: Removes `WH/WTH/WAH` prefixes, converts `<WTH8xxx>` to `(**8xxx)`
   - **Tokenization**: Classifies tokens into core (Strong's 1-8999), morphology (8xxx), and prefixes (900x)
   - **Grouping**: Applies complex attachment rules for brace prepositions, object markers, and construct state

3. **Output Generation** (`run_parser_temp.py`) - Orchestrates parsing and file I/O:
   - Calls `fetch_text.sh` to retrieve data
   - Invokes parser with JSON payloads
   - Saves results to `output/{Book}/{Chapter}/{verse}` (text format) or `{verse}_uncertain`

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
python3 run_parser_temp.py 1 1  # Genesis 1:1 (default book is Gen)

# Just view output without writing to disk
python3 run_parser_temp.py --no-write 1 1

# Direct parser invocation (advanced)
python3 parse_verse_v1_8.py '<qb_json>' '<qp_json>' '<verse_ref>'
```

### Batch Parsing

Currently manual iteration. See `Batch_Parsing_SOP.md` for the workflow:
1. Create output directories: `mkdir -p output/{Book}/{Chapter}/`
2. Iterate verses: fetch → parse → write with uncertainty handling
3. Files named `{verse}` (success) or `{verse}_uncertain` (with warning notes)

## Token Classification System

Three distinct token types with **non-overlapping numeric ranges**:

- **Core (Strong's)**: `<dddd>` or `{<dddd>}` (implicit) - Numbers 1-8999 (excluding 8xxx, 09xxx)
- **Morphology (8xxx)**: `(**8ddd)`, `{8ddd}` - 4-digit codes 8000-8999, verbal stems and tenses (e.g., 8804 = Qal Perfect)
- **Prefixes (900x)**: `<09ddd>` - **5-digit codes 09000-09999 only**, inseparable particles (09001 = ל־, 09002 = ב־, 09009 = ה־)
  - **CRITICAL**: 4-digit numbers like `<0914>` are NOT 900x prefixes (must be exactly 5 digits starting with 09)

**Critical**: `<WTH8804>` must be normalized to `(**8804)` before tokenization to avoid misclassification as core.

## Grouping Rules (SPECIFICATION_v1.8.md §3.3)

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

**v1.8 Parser** (`parse_verse_v1_8.py`) - Text format output with automatic compound detection:

**Text Format** - Three-section Traditional Chinese output per `UNV_SN_Output_Format.md`:
```
Parsed and Formatted Text Section:
<09002><07225> — 介系詞片語「起初」
<0430> — 名詞「上帝、神、神明」
<04480><05921> — 複合介系詞 מֵעַל「從…之上」
[註]: 介系詞 מִן + 介系詞 עַל

Raw UNV+SN Source Text Section:
{<WAH0430>}就把這些光<WAH0853>擺列<WH05414><WTH8799>...

Morphology Notes Section:
*1: 動詞，Qal 完成式 3 單陽
```

**v1.8 Features**:
- Automatic compound preposition detection (מִן, לִפְנֵי, etc.)
- Multi-token compound support across 900x prefixes
- Pronoun suffix detection for Exception 1
- Four-tier issue logging system (includes dedicated dangling_prefixes.txt)

## Configuration Profile

From SPECIFICATION_v1.8.md §4.1 (hardcoded in `parse_verse_v1_8.py`):

```python
PROFILE = {
    "brace_preps": ["05921", "04480", "0413", "00996"],  # עַל, מִן, אֶל, בֵּין
    "object_marker": "0853",                              # אֵת
    "ignored_codes": ["09015"],                           # Paragraph markers

    # v1.7+ configuration
    "detect_compounds_from_qp": True,      # Detect compounds from qp.php
    "merge_prep_plus_prep": True,          # Merge prep+prep compounds
    "merge_prep_plus_noun": False,         # Optional: merge prep+noun
}
```

## File Responsibilities

- **SPECIFICATION_v1.8.md**: Authoritative parsing rules (standalone, includes all previous versions)
- **dangling_prefixes.md**: Analysis report for懸空 900x 前綴問題 (translation artifacts, not parser errors)
- **dangling_brace_preps.md**: Analysis report for懸空 brace 介系詞問題 (translation artifacts, similar to dangling_prefixes)
- **dangling_object_markers.md**: Analysis report for懸空受詞標記問題 (translation artifacts for אֵת)
- **qb_qp_mismatch_analysis.md**: Analysis report for qb.php/qp.php Strong's number mismatches
- **compound_prep_plus_noun_analysis.md**: Analysis report for prep+noun compound detection (design choice)
- **compatible_but_notable_issues_analysis.md**: Analysis report for edge cases and spec boundaries
- **fetch_text.sh**: API wrapper with English ↔ Chinese book name translation
- **parse_verse_v1_8.py**: Current parser implementing v1.8 spec (text format output)
- **run_parser_temp.py**: Batch orchestrator pointing to `parse_verse_v1_8.py`
- **Batch_Parsing_SOP.md**: Workflow for batch processing with uncertainty handling
- **UNV_SN_Output_Format_Gen_1_1.md**: Output format spec for legacy parser

## Data Sources

**FHL API** (bible.fhl.net):
- `qb.php` parameters: `version=unv`, `chineses=創`, `chap=1`, `sec=1`, `strong=1`
- `qp.php` parameters: `engs=Gen`, `chap=1`, `sec=1`

**Book Mappings**: 66 books with bidirectional English/Chinese lookup (Gen ↔ 創, Matt ↔ 太, 1Sam ↔ 撒上, etc.) embedded in `fetch_text.sh`.

## Implementation Status

**v1.8 Parser Status**:
- ✅ Implemented: מִן (04480) compound detection
- ✅ Implemented: Multi-token compounds across 900x prefixes
- ✅ Implemented: Pronoun suffix detection (Exception 1)
- ✅ Implemented: Eight-tier issue logging system (v1.8.4, includes qp_data_type_errors.txt)
- ⚠️ Partial: Generic 900x-starting compounds (needs debugging for pure לִפְנֵי cases)

**Known Issues (Not Bugs)**:
- **Dangling 900x Prefixes** (74 cases in Gen+Exod): FHL data encoding artifacts where Chinese translation adds prepositions not present as independent Strong's numbers in Hebrew. See `dangling_prefixes.md` for full analysis. Parser correctly identifies and logs these to `output/dangling_prefixes.txt`.
- **Dangling Brace Prepositions** (12 cases in Gen+Exod): FHL data encoding where implicit prepositions `{<0413>}`, `{<05921>}`, `{<04480>}` appear at syntactic boundaries without suitable attachment points. See `dangling_brace_preps.md` for full analysis. Parser correctly identifies and logs these to `output/dangling_brace_preps.txt`.
- **Dangling Object Markers** (19 cases in Gen+Exod): FHL data encoding where implicit object markers `{<0853>}` (אֵת) appear in sentence-final position, appositive structures, or coordinated objects without suitable noun attachment points. See `dangling_object_markers.md` for full analysis. Parser correctly identifies and logs these to `output/dangling_object_markers.txt`.
- **qp.php Data Type Errors** (v1.8.4): Edge cases where qp.php returns unexpected data types (e.g., `sn` field as list instead of string, or compound prepositions with list-type `core`). Parser handles these gracefully and logs to `output/qp_data_type_errors.txt`.

## Testing Strategy

**Verified Test Cases** (from SPECIFICATION_v1.8.md §7):
- Gen 1:2 - Brace preposition right-attach + construct state
- Gen 1:4 - Object marker handling with multiple `{<0853>}`
- Gen 1:5 - FHL profile mapping with inferred vs explicit prefixes
- Gen 3:5 - Verb left-attach exception for infinitive complement
- Gen 4:16 - Multi-token מִן compound מִלִּפְנֵי (v1.7.2)
- Gen 3:3 - Pronoun suffix detection and left-attachment (v1.7.2)
- Gen 5:1 - Object marker with pronoun suffix (v1.7.2)
- Gen 6:11 - לִפְנֵי compound (v1.8, needs debugging)

Run test verses with `run_parser_temp.py 1 2` and validate against expected groupings in spec §7.

## Parent Project Context

This directory is a subdirectory of the larger **Strong's Number Embedding Project** (see `/Users/joshua/work/strong_number_embedding/CLAUDE.md`). The parent project includes:
- `original_text_preparation/` - SQLite extraction toolkit
- `dual_reader/` - Web-based Bible reader with Strong's support
- `dual_reader_right_editor/` - Advanced reader with edit mode

This directory focuses exclusively on UNV parsing logic; dual readers consume processed data for visualization.

## Subdirectory Documentation

**When modifying `viewer_v2/`**:
- **MUST READ** `viewer_v2/CLAUDE.md` first
- Contains component index with all existing functions
- Documents design patterns (group-based coloring, color filtering, Mediator events)
- Lists anti-patterns to avoid (禁止疊床架屋 — no redundant components)
- Provides pre-task checklist for bug fixes

The `viewer_v2/CLAUDE.md` file is the authoritative reference for the Parsed Verse Viewer web application.
