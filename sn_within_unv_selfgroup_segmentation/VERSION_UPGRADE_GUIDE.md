# Parser Version Upgrade Guide

This guide explains how to upgrade the UNV+SN parser to a new version (e.g., from v1.8 to v1.9).

## Version Control Architecture

The system uses **immutable version files** - each parser version is a separate Python file that remains unchanged once released. This allows:
- Easy rollback to previous versions
- Side-by-side comparison of parser versions
- Historical preservation of parsing logic

## Files That Manage Version Numbers

### 1. Parser Script (`parse_verse_vX_Y.py`)
**Location**: Line 19
```python
PARSER_VERSION = "v1.8"  # Update this when creating new parser version
```

**What it does**:
- Defines the parser version in `vX.Y` format (e.g., `v1.8`, `v1.9`)
- Automatically constructs spec file path: `SPECIFICATION_{PARSER_VERSION}.md`
- Dynamically includes version in output: `Parsed and Formatted Text Section (SPECIFICATION_v1.8):`
- Validates that spec file version matches parser version on startup

### 2. Orchestrator Script (`run_parser_temp.py`)
**Location**: Line 14
```python
PARSER_VERSION = "v1_8"  # Update this to use new parser version
```

**What it does**:
- Defines which parser version to use in `vX_Y` format (underscore-separated for Python module names)
- Dynamically constructs parser script path: `parse_verse_{PARSER_VERSION}.py`
- Dynamically imports parser module at runtime

## Upgrade Steps

When you need to upgrade from v1.8 to v1.9:

### Step 1: Create New Specification File
```bash
# Create SPECIFICATION_v1.9.md based on v1.8
cp SPECIFICATION_v1.8.md SPECIFICATION_v1.9.md

# Edit SPECIFICATION_v1.9.md
# - Update first line: # UNV+SN Parsing Specification v1.9
# - Document new features/changes
```

### Step 2: Create New Parser File
```bash
# Create parse_verse_v1_9.py based on v1_8
cp parse_verse_v1_8.py parse_verse_v1_9.py

# Edit parse_verse_v1_9.py line 19:
PARSER_VERSION = "v1.9"  # Changed from "v1.8"

# Implement new parsing logic as needed
```

### Step 3: Update Orchestrator to Use New Parser
```bash
# Edit run_parser_temp.py line 14:
PARSER_VERSION = "v1_9"  # Changed from "v1_8"
```

### Step 4: Test New Parser
```bash
# Test single verse
python run_parser_temp.py --no-write 1 1

# Verify output shows: "Parsed and Formatted Text Section (SPECIFICATION_v1.9):"
```

### Step 5: Regenerate Output Files (Optional)
If you want to regenerate all parsed verses with the new parser:
```bash
# Batch parse with new version
./batch_parse_genesis.sh  # Or your preferred batch script
```

### Step 6: Update Viewer (If Needed)
The viewer automatically handles version numbers in section headers, so no changes needed unless you modify the section title format itself.

## Version Format Notes

**IMPORTANT**: Parser version uses different formats in different contexts:

1. **Spec file name**: `SPECIFICATION_v1.8.md` (dot-separated)
2. **Parser file name**: `parse_verse_v1_8.py` (underscore-separated)
3. **Parser constant**: `PARSER_VERSION = "v1.8"` (dot-separated string)
4. **Orchestrator constant**: `PARSER_VERSION = "v1_8"` (underscore-separated string)

The system handles conversion automatically.

## Rollback Procedure

To rollback to a previous parser version:

```bash
# Edit run_parser_temp.py line 14:
PARSER_VERSION = "v1_8"  # Rollback to v1.8

# Old parser file (parse_verse_v1_8.py) and spec (SPECIFICATION_v1.8.md)
# are still in the directory, so it will work immediately
```

## Version Validation

The parser automatically validates on startup:
- Checks if `SPECIFICATION_{PARSER_VERSION}.md` exists
- Extracts version from spec file's first line
- Raises `ValueError` if parser version doesn't match spec version

This prevents accidentally using mismatched parser/spec combinations.

## Example: Complete v1.8 → v1.9 Upgrade

```bash
# 1. Create spec
cp SPECIFICATION_v1.8.md SPECIFICATION_v1.9.md
# Edit first line: # UNV+SN Parsing Specification v1.9

# 2. Create parser
cp parse_verse_v1_8.py parse_verse_v1_9.py
# Edit line 19: PARSER_VERSION = "v1.9"

# 3. Update orchestrator
# Edit run_parser_temp.py line 14: PARSER_VERSION = "v1_9"

# 4. Test
python run_parser_temp.py --no-write 1 1

# Output should show:
# Parsed and Formatted Text Section (SPECIFICATION_v1.9):
```

## Files That DON'T Need Manual Updates

Thanks to dynamic version management, these files automatically adapt:
- **Viewer** (`viewer_v2/js/data_loader.js`) - parses section headers dynamically
- **Parser output** - version number in header comes from `PARSER_VERSION` constant
- **Batch scripts** - they just call `run_parser_temp.py`, which handles versioning

## Summary Checklist

When upgrading to a new parser version:

- [ ] Create `SPECIFICATION_vX.Y.md` (dot-separated)
- [ ] Create `parse_verse_vX_Y.py` (underscore-separated)
- [ ] Update `PARSER_VERSION` in new parser file (line 19, dot-separated: `"vX.Y"`)
- [ ] Update `PARSER_VERSION` in `run_parser_temp.py` (line 14, underscore-separated: `"vX_Y"`)
- [ ] Test with `--no-write` flag first
- [ ] Regenerate parsed files if needed
- [ ] Keep old parser files for rollback capability
