# UNV+SN Backparse Skill

**Skill Name**: `unv-sn-backparse`

**Version**: 1.0 (Based on SPECIFICATION_v1.6.md)

## Purpose

This skill enables Claude Code to automatically parse Chinese Union Version (UNV) biblical text with Strong's Numbers into structured semantic groups. It implements the complete v1.6 parsing specification with proper token classification, grouping rules, and output formatting.

## Automatic Activation

Claude will automatically activate this skill when users:
- Request parsing of biblical verses (e.g., "parse Genesis 1:1")
- Want to batch process chapters or verse ranges
- Ask about Strong's number groupings or morphology
- Need to verify or analyze parsed output

## Files in This Skill

- **SKILL.md** - Main skill definition with parsing workflow and rules
- **examples.md** - 10 comprehensive examples showing different use cases
- **reference.md** - Quick reference guide with tables, schemas, and checklists
- **README.md** - This file

## Key Features

### Token Classification
- **Core Strong's Numbers** (1-8999, excluding 8xxx/9xxx)
- **Morphology Codes** (8xxx series for verb stems, tenses)
- **Prefix Codes** (900x for inseparable particles like ל־, ב־, ה־)

### Grouping Intelligence
- Brace preposition decision tree with 3-level priority
- Object marker special handling (`{<0853>}`)
- Prefix attachment with skip-over logic
- Morphology left-attachment
- Warning generation for ambiguous cases

### Output Format
Three-section output per verse:
1. **Parsed and Formatted Text** (Traditional Chinese)
2. **Raw UNV+SN Source Text** (with WH/WTH/WAH prefixes)
3. **Morphology Notes** (detailed grammatical explanations)

## Usage Examples

### Single Verse
```
User: "Parse Genesis 1:1"
→ Claude activates skill, runs parser, displays three-section output
```

### Batch Chapter
```
User: "Parse all verses in Genesis chapter 2"
→ Claude creates todo list, sets up directories, parses 25 verses, verifies results
```

### Verification
```
User: "Check the parsing output for Genesis 1"
→ Claude reviews output files, checks for uncertainties, shows samples
```

## Dependencies

- **Core Scripts**: `fetch_text.sh`, `parse_verse_v1_6.py`, `run_parser_temp.py`
- **Documentation**: `SPECIFICATION_v1.6.md`, `Batch_Parsing_SOP.md`, `UNV_SN_Output_Format_Gen_1_1.md`
- **System Tools**: `curl`, `jq`, Python 3

## Related Skills

This skill is part of the Strong's Number Embedding Project. For other project components:
- Dual Bible readers: `../dual_reader/` and `../dual_reader_right_editor/`
- Data extraction: `../original_text_preparation/`

## Skill Metadata

**Allowed Tools**: Read, Write, Bash, Grep, Glob
**Project-Specific**: Yes (located in `.claude/skills/` within project)
**Auto-Discovery**: Enabled via comprehensive description field

## Testing the Skill

To verify the skill is working:

1. Ask Claude to "parse Genesis 3:16"
2. Check that it automatically uses the skill
3. Verify output follows three-section format
4. Confirm todo list tracking for batch operations

## Implementation Status

- ✅ Full v1.6 token normalization rules
- ✅ Complete grouping workflow
- ✅ Output format specification
- ✅ Batch processing SOP
- ✅ Error handling and uncertainty detection
- ⚠️ Brace preposition decision tree (parser has placeholder logic)
- ❌ Construct state linking (optional v1.2-B feature)

## Future Enhancements

1. Complete brace preposition decision tree implementation in parser
2. Add construct state linking support
3. Enhance qp.php morphological analysis
4. Add cross-reference validation
5. Implement JSON output mode support

## Support Documentation

- **Main Skill Instructions**: SKILL.md
- **Detailed Examples**: examples.md (10 scenarios)
- **Quick Reference**: reference.md (tables, schemas, command templates)
- **Project Context**: ../CLAUDE.md

---

**Created**: 2025-11-23
**Based on**: SPECIFICATION_v1.6.md
**For**: Strong's Number Embedding Project
