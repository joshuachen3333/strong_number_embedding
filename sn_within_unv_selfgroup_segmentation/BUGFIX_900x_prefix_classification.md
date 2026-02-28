# Bug Fix: 900x Prefix Misclassification

## Issue Date
2025-11-24

## Problem Description

The parser incorrectly classified 4-digit Strong's numbers starting with "09" as 900x prefixes, resulting in false "dangling_p900x" warnings.

### Example
- `<0914>` (בָּדַל "to separate") was misclassified as a 900x prefix
- This generated log entry: `Gen 1:4 | dangling_p900x | 900x prefix <0914> had no following Strong's number to attach to.`

### Root Cause

In `parse_verse_v1_6.py` line 82-83, the classification logic was:

```python
elif number.startswith('09') and len(number) in (4, 5):
    token['type'] = 'p900x'
```

This incorrectly accepted both 4-digit (`'0914'`) and 5-digit (`'09001'`) numbers.

## Solution

### Code Fix

**File**: `parse_verse_v1_6.py`

**Changed line 82** from:
```python
elif number.startswith('09') and len(number) in (4, 5):
```

To:
```python
elif number.startswith('09') and len(number) == 5:
```

### Specification Clarification

**File**: `SPECIFICATION_v1.6.md` (Section 2.3)

Added explicit length requirement:

```markdown
* **數字範圍**：
  - `8xxx`（4位數，8000-8999）⇒ **morph**
  - `09xxx`（5位數，09000-09999）⇒ **900x prefix**
  - 其餘（1-7999, 9000-8999 但非 09xxx 格式）⇒ **core**
  - **重要**：4位數如 `0914` 不是 900x（長度必須為5且以09開頭）
```

### Documentation Updates

Updated the following files to clarify the 900x prefix definition:

1. **CLAUDE.md** - Added explicit note about 5-digit requirement
2. **.claude/skills/unv-sn-backparse/skill.md** - Added warning about 4-digit numbers
3. **SPECIFICATION_v1.6.md** - Added detailed numeric range breakdown

## Validation

### Test Case: Genesis 1:4

**Before fix**:
- Output included: `--- UNCERTAINTY NOTES ---\n900x prefix <0914> had no following Strong's number to attach to.`

**After fix**:
- Output has no uncertainty notes
- `<0914>` correctly classified as core Strong's number (verb)
- Formatted as: `<0914>(8686) — 動詞「隔絕、分開、分別」 *2`

### Impact Assessment

**From `uncertain_or_expandable_issues.txt`**:
- Total dangling_p900x errors: 136
- Many (possibly most) were false positives from this bug
- True 900x prefixes: 09001 (ל־), 09002 (ב־), 09009 (ה־), etc.

## Correct 900x Prefix Examples

Valid 900x prefix codes (5 digits):
- `<09001>` - ל־ (preposition "to/for")
- `<09002>` - ב־ (preposition "in/with")
- `<09003>` - כ־ (preposition "like/as")
- `<09006>` - מ־ (preposition "from")
- `<09009>` - ה־ (definite article "the")
- `<09015>` - Paragraph marker (in ignored_codes)

## Incorrect Classifications (Now Fixed)

4-digit numbers that were incorrectly treated as 900x:
- `<0914>` - בָּדַל (verb "to separate")
- `<0954>` - בּוֹשׁ (verb "to be ashamed")
- Any other 4-digit number starting with "09"

## Recommendations

1. **Re-parse affected verses**: Consider re-running the parser on verses with dangling_p900x warnings to clean up logs
2. **Add unit tests**: Create test cases for:
   - 4-digit numbers starting with 09 (should be core)
   - 5-digit numbers starting with 09 (should be p900x)
3. **Log cleanup**: Previous logs contain false positives that can be filtered out

## Related Issues

This fix addresses the majority of `dangling_p900x` warnings. The remaining issue types to investigate:
- `qb_qp_mismatch` (1162 occurrences) - Data source inconsistencies
- `dangling_object_marker` (41 occurrences) - Actual parsing challenges
- `dangling_brace_prep` (27 occurrences) - Legitimate ambiguities
- `dangling_morph` (20 occurrences) - Actual orphaned morphology codes
