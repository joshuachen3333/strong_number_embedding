# Issue Logging Feature for UNV+SN Parser

## Overview

The UNV+SN parser (`parse_verse_v1_8.py`) automatically logs parsing issues to four dedicated text files in the `output/` directory. This feature helps track uncertain cases, data quality issues, and notable patterns across batch parsing runs.

## Log Files

### 1. `output/strong_number_from_qb.php_not_found_in_qp.php.txt` (NEW in v1.8.1)

**Purpose**: Dedicated log for Strong's number mismatches between qb.php and qp.php

**Use Cases**:
- Track data quality inconsistencies between FHL API endpoints
- Identify Strong's numbers that exist in UNV text but lack morphology records
- Cross-reference with KJV to determine if issue is UNV-specific or broader
- Focus on FHL database completeness rather than parsing logic

**Logged Issue Types**:
- `qb_qp_mismatch`: Strong's number from qb.php not found in qp.php records (with KJV comparison)

**Benefit**: Separates the most common issue type (117+ Genesis entries) from other parsing ambiguities

### 2. `output/uncertain_or_expandable_issues.txt`

**Purpose**: Logs parsing issues that cannot be resolved with confidence (excluding qb_qp_mismatch)

**Use Cases**:
- Cases requiring specification expansion
- Ambiguous grammatical constructions
- Manual review needed

**Logged Issue Types** (v1.8.1: no longer includes qb_qp_mismatch):
- `brace_attach_ambiguous`: Cannot determine brace preposition attachment
- `dangling_900x`: Prefix code without following core token
- `dangling_morph`: Morphology code without preceding core token
- `dangling_object_marker`: Object marker (אֵת) without suitable noun
- `dangling_brace_prep`: Brace preposition without suitable attachment point

### 3. `output/compatible_but_notable_issues.txt`

**Purpose**: Logs successfully parsed cases worth special attention

**Use Cases**:
- Edge cases in biblical text
- Unusual grammatical constructions
- Multiple valid interpretations that were resolved by spec rules
- Patterns for future specification refinements

**Benefits**:
- Quality assurance tracking
- Training data for AI/LLM integration
- Cross-reference with theological scholarship
- Identify patterns for spec enhancements

### 4. `output/compound_prep_plus_noun.txt` (Added in v1.7)

**Purpose**: Logs prep+noun compounds detected but not merged

**Use Cases**:
- Track FHL data encoding artifacts where qb.php splits מִן but qp.php shows compound
- Document intentional design choices per `merge_prep_plus_noun: False` config
- These are NOT parsing errors

**Example**: `<04480><03605>` = מִכָּל "from all" (מִן + כֹּל)

## Log Format

Each entry follows this format:
```
[timestamp] verse_ref | issue_type | description
```

**Examples**:
```
[2025-11-25 01:57:42] Gen 3:14 | qb_qp_mismatch | Strong's number <03212> from qb.php not found in qp.php records. | KJV also uses <03212>
[2025-11-25 01:50:43] Gen 3:16 | dangling_p900x | 900x prefix <09002> had no following Strong's number to attach to.
[2025-11-25 01:50:36] Gen 2:19 | prep_noun_compound | Prep+noun compound detected: <04480><08064> = הַשָּׁמַיִם (冠詞 הַ + 名詞，陽性複數) - not merged per config
```

## Implementation Details

### Code Changes

1. **parse_verse_v1_8.py** (v1.8.1 update):
   - Added `QB_QP_MISMATCH_LOG` constant for dedicated qb_qp_mismatch file
   - Updated logging logic (line 594) to route qb_qp_mismatch entries to dedicated file
   - Added `PREP_NOUN_LOG` constant for compound preposition tracking (v1.7)
   - Implemented `append_to_log()` function for timestamped logging
   - Updated `format_groups_to_text()` to accept `verse_ref` parameter
   - Added KJV cross-reference fetching for qb_qp_mismatch entries

2. **run_parser_temp.py**:
   - Changed from subprocess to direct module import of `parse_verse_v1_8`
   - Constructs `verse_ref` string (e.g., "Gen 1:1")
   - Passes `verse_ref` to parser for logging

3. **Analysis scripts** (v1.8.1 update):
   - Updated `analyze_04480_combinations.py` to read from new qb_qp_mismatch file
   - Updated `identify_compound_prepositions.py` to read from new qb_qp_mismatch file

### Log File Location

All four log files are created in:
```
/Users/joshua/work/strong_number_embedding/sn_within_unv_selfgroup_segmentation/output/
```

The `output/` directory is automatically created if it doesn't exist.

## Usage

### Parsing with Logging (Automatic)

```bash
# Single verse - logging happens automatically
python run_parser_temp.py 1 1

# Batch parsing - all issues logged across verses
for verse in {1..25}; do python run_parser_temp.py 2 $verse; done
```

### Viewing Logs

```bash
# View recent entries (last 20 lines)
tail -20 output/strong_number_from_qb.php_not_found_in_qp.php.txt
tail -20 output/uncertain_or_expandable_issues.txt
tail -20 output/compatible_but_notable_issues.txt
tail -20 output/compound_prep_plus_noun.txt

# Search for specific verse
grep "Gen 3:14" output/strong_number_from_qb.php_not_found_in_qp.php.txt
grep "Gen 3:16" output/uncertain_or_expandable_issues.txt

# Count total issues logged
wc -l output/strong_number_from_qb.php_not_found_in_qp.php.txt
wc -l output/uncertain_or_expandable_issues.txt
wc -l output/compound_prep_plus_noun.txt

# View all issues for a book
grep "Gen" output/strong_number_from_qb.php_not_found_in_qp.php.txt

# Check issue type breakdown
cut -d'|' -f2 output/uncertain_or_expandable_issues.txt | sort | uniq -c | sort -rn
```

### Log Maintenance

The log files append entries indefinitely. To start fresh:

```bash
# Archive old logs
timestamp=$(date +%Y%m%d_%H%M%S)
mv output/strong_number_from_qb.php_not_found_in_qp.php.txt output/strong_number_from_qb.php_not_found_in_qp.php_${timestamp}.txt.bak
mv output/uncertain_or_expandable_issues.txt output/uncertain_or_expandable_issues_${timestamp}.txt.bak
mv output/compatible_but_notable_issues.txt output/compatible_but_notable_issues_${timestamp}.txt.bak
mv output/compound_prep_plus_noun.txt output/compound_prep_plus_noun_${timestamp}.txt.bak

# Fresh logs will be auto-created on next parse
```

## Integration with Skill

The `unv-sn-backparse` skill documentation has been updated to include:
- Issue logging feature description
- Log file formats and usage
- Common commands for checking logs
- Implementation status

## Future Enhancements

Potential improvements to the logging system:

1. **Severity Levels**: Add severity ratings (low/medium/high/critical)
2. **Log Rotation**: Automatic archiving when logs exceed size threshold
3. **Summary Statistics**: Generate reports of issue frequency by type/book
4. **HTML Reports**: Convert logs to browsable HTML with filtering
5. **Issue Resolution Tracking**: Mark issues as reviewed/resolved
6. **Export to CSV**: Enable analysis in spreadsheet tools
7. **Notable Pattern Detection**: Automatically flag repeated patterns

## Related Documentation

- **SPECIFICATION_v1.6.md §5.3**: Specification for issue logging
- **.claude/skills/unv-sn-backparse/SKILL.md**: Skill documentation with logging details
- **.claude/skills/unv-sn-backparse/README.md**: README with implementation status
- **Batch_Parsing_SOP.md**: Standard operating procedure for batch parsing

## Testing

The logging system has been tested with:
- Genesis 1:1 (clean parse, no issues logged)
- Genesis 1:2 (brace prepositions, parser handles correctly per spec)

To trigger logging for testing:
- Use verses with known data inconsistencies
- Test with verses having ambiguous grammatical structures
- Batch parse entire chapters to accumulate diverse cases

## Support

For questions or issues with the logging feature:
- Check SPECIFICATION_v1.6.md for authoritative parsing rules
- Review skill documentation in `.claude/skills/unv-sn-backparse/`
- Examine log file headers for format details
- Test with sample verses to verify expected behavior

---

**Feature Added**: 2025-11-24
**Last Updated**: 2025-11-25 (v1.8.1 - separate qb_qp_mismatch log)
**Version**: Based on SPECIFICATION_v1.8.md
**Implemented By**: Claude Code via skill enhancement request
