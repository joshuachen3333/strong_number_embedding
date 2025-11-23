# Issue Logging Feature for UNV+SN Parser

## Overview

The UNV+SN parser (`parse_verse_v1_6.py`) now automatically logs parsing issues to two dedicated text files in the `output/` directory. This feature helps track uncertain cases and notable patterns across batch parsing runs.

## Log Files

### 1. `output/uncertain_or_expandable_issues.txt`

**Purpose**: Logs issues that cannot be resolved with confidence

**Use Cases**:
- Cases requiring specification expansion
- Data inconsistencies between FHL APIs
- Ambiguous grammatical constructions
- Manual review needed

**Logged Issue Types**:
- `qb_qp_mismatch`: Strong's number from qb.php not found in qp.php records
- `brace_attach_ambiguous`: Cannot determine brace preposition attachment
- `dangling_900x`: Prefix code without following core token
- `dangling_morph`: Morphology code without preceding core token
- `dangling_object_marker`: Object marker (אֵת) without suitable noun
- `dangling_brace_prep`: Brace preposition without suitable attachment point

### 2. `output/compatible_but_notable_issues.txt`

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

## Log Format

Each entry follows this format:
```
[timestamp] verse_ref | issue_type | description
```

**Example**:
```
[2025-11-24 14:30:15] Gen 1:2 | qb_qp_mismatch | Strong's number <0430> from qb.php not found in qp.php records.
[2025-11-24 14:30:22] Gen 3:5 | dangling_brace_prep | Brace preposition <04480> had no suitable attachment point.
```

## Implementation Details

### Code Changes

1. **parse_verse_v1_6.py**:
   - Added `append_to_log()` function for timestamped logging
   - Updated `format_groups_to_text()` to accept `verse_ref` parameter
   - Added logging calls for uncertainty notes and warnings
   - Updated `parse_verse_v1_6()` to pass `verse_ref` through

2. **run_parser_temp.py**:
   - Changed from subprocess to direct module import of `parse_verse_v1_6`
   - Constructs `verse_ref` string (e.g., "Gen 1:1")
   - Passes `verse_ref` to parser for logging

### Log File Location

Both log files are created in:
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
tail -20 output/uncertain_or_expandable_issues.txt
tail -20 output/compatible_but_notable_issues.txt

# Search for specific verse
grep "Gen 1:2" output/uncertain_or_expandable_issues.txt

# Count total issues logged
grep -v "^#" output/uncertain_or_expandable_issues.txt | grep -c "\[20"

# View all issues for a book
grep "Gen" output/uncertain_or_expandable_issues.txt
```

### Log Maintenance

The log files append entries indefinitely. To start fresh:

```bash
# Archive old logs
mv output/uncertain_or_expandable_issues.txt output/uncertain_or_expandable_issues_$(date +%Y%m%d).txt.bak
mv output/compatible_but_notable_issues.txt output/compatible_but_notable_issues_$(date +%Y%m%d).txt.bak

# Create fresh logs (will be auto-created on next parse)
rm -f output/uncertain_or_expandable_issues.txt output/compatible_but_notable_issues.txt
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
**Version**: Based on SPECIFICATION_v1.6.md
**Implemented By**: Claude Code via skill enhancement request
