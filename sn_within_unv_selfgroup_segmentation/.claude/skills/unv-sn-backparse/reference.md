# UNV+SN Backparse Reference

## Quick Reference Guide

### Token Types and Ranges

| Type | Range | Format | Examples |
|------|-------|--------|----------|
| **Core (Strong's)** | 1-8999 (excluding 8xxx, 9xxx) | `<dddd>` or `{<dddd>}` | `<0430>` (God), `{<0853>}` (object marker) |
| **Morphology (8xxx)** | 8600-8999 | `(**8ddd)`, `{8ddd}` | `(8804)` Qal Perfect, `{8799}` Qal Narrative |
| **Prefixes (900x)** | 9000-9999 | `<09ddd>` | `<09001>` (ל־), `<09002>` (ב־), `<09009>` (ה־) |

### Normalization Rules (MUST DO FIRST)

```
Before:  <WH0430>        →  After: <0430>
Before:  <WTH8804>       →  After: (**8804)
Before:  <WAH09002>      →  After: <09002>
Before:  {<WH0853>}      →  After: {<0853>}
```

### Brace Preposition Decision Tree

```
Encounter {<PREP>}
    ├─ Is PREP == "0853"? → YES: Right-attach to noun (pre_brace)
    │
    └─ NO: Is qp.wform pronoun suffix OR infinitive complement?
           ├─ YES: Left-attach to verb (post_brace)
           │
           └─ NO: Is right-side token a noun (skipping 900x)?
                  ├─ YES: Right-attach to noun (pre_brace)
                  │
                  └─ NO: Keep independent + warning
```

**Brace Preps**: `["05921", "04480", "0413", "00996"]` (עַל, מִן, אֶל, בֵּין)

### Attachment Rules Summary

| Element | Direction | Target | Notes |
|---------|-----------|--------|-------|
| 900x prefixes | Right | Next core | Skip over `{<...>}` and `{8xxx}` |
| Morphology 8xxx | Left | Previous core | Always |
| `{<0853>}` | Right | Next noun | Exception 2 (highest for 0853) |
| `{<PREP>}` + pronoun | Left | Previous verb | Exception 1 |
| `{<PREP>}` general | Right | Next noun | General case |

### Output Structure (JSON Schema)

```json
{
  "core": "0430",                    // Required: Strong's number
  "implicit": false,                 // true if {<dddd>}, false if <dddd>
  "prefixes": ["09001", "09002"],    // From qb.php explicit 900x
  "morph": ["8804"],                 // Morphology codes (scan order)
  "pre_brace": ["0853"],             // Right-attached braces
  "post_brace": ["04480"],           // Left-attached braces (verb only)
  "inferred_prefixes": ["ו־", "ה־"], // From qp.wform (optional)
  "inferred": false,                 // true if any inference used
  "construct_of": "08415",           // Optional: construct state link
  "parsing_wform": "יְהוָ֥ה",         // Optional: qp.wform annotation
  "warnings": []                     // Issues: brace_attach_ambiguous, etc.
}
```

### Text Output Format

```
Section I: Parsed and Formatted Text
<NNNN> — [詞性]「[中文意義]」
<NNNN>(8xxx) — [詞性]「[中文意義]」 *N
<NNNN><MMMM> — [詞性]「[中文意義]」

Section II: Raw UNV+SN Source Text
[Original bible_text with WH/WTH/WAH prefixes]

Section III: Morphology Notes
*1: [Detailed description from qp.wform]
*2: [Another morphology description]
```

### Warning Types

| Warning Code | Meaning | When to Generate |
|--------------|---------|------------------|
| `brace_attach_ambiguous` | Cannot determine preposition attachment | Right-side not clearly noun, no pronoun suffix |
| `dangling_900x` | Prefix without core token | End of sequence with prefixes in buffer |
| `morph_without_core` | Orphaned morphology code | Morphology before any core established |
| `qb_qp_core_mismatch` | Data inconsistency | Strong's in qb.php missing from qp.php |

### File Naming Conventions

| Status | Filename | Example |
|--------|----------|---------|
| Success | `{verse}` | `output/Gen/1/1` |
| Uncertain | `{verse}_uncertain` | `output/Gen/1/3_uncertain` |

### FHL API Endpoints

**bible.fhl.net/json/qb.php**
- Returns: UNV text with Strong's numbers
- Requires: Chinese book abbreviations (chineses)
- Parameters: `version=unv`, `chineses=創`, `chap=1`, `sec=1`, `strong=1`
- Response: `{record: [{sec: "1", bible_text: "..."}]}`

**bible.fhl.net/json/qp.php**
- Returns: Parsing/morphology data
- Requires: English book abbreviations (engs)
- Parameters: `engs=Gen`, `chap=1`, `sec=1`
- Response: `{record: [{engs: "Gen", wkind: "n", wform: "בְּרֵאשִׁ֖ית", ...}]}`

### Common 900x Prefix Mappings

| Code | Hebrew | Meaning |
|------|--------|---------|
| 09001 | ל־ | to, for, at |
| 09002 | ב־ | in, at, with |
| 09003 | כ־ | like, as |
| 09006 | מ־ | from |
| 09009 | ה־ | the (definite article) |
| 09005 | alias for 09001 | |
| 09015 | (paragraph marker) | ignored |

### Common 8xxx Morphology Codes

| Code | Hebrew | Description |
|------|--------|-------------|
| 8804 | קָטַל | Qal Perfect |
| 8799 | קָטַל / יִקְטֹל | Qal Narrative (context-dependent) |
| 8800 | קְטֹל | Qal Infinitive |
| 8802 | קֹטֵל | Qal Participle |
| 8738 | נִקְטַל | Niphal Perfect |
| 8764 | מְקַטֵּל | Piel Participle |

### Book Abbreviations (Selected)

| English | Chinese | Hebrew Name |
|---------|---------|-------------|
| Gen | 創 | בראשית |
| Exo | 出 | שמות |
| Lev | 利 | ויקרא |
| Num | 民 | במדבר |
| Deu | 申 | דברים |
| 1Sam | 撒上 | שמואל א |
| 2Sam | 撒下 | שמואל ב |
| Psa | 詩 | תהלים |
| Isa | 賽 | ישעיה |
| Matt | 太 | ματθαιος |
| John | 約 | ιωαννης |
| Rom | 羅 | ρωμαιους |

Complete list: `./fetch_text.sh --list`

### Parsing State Machine (Pseudo-code)

```python
prefix_buffer = []
groups = []

for token in normalized_tokens:
    if token.is_900x():
        prefix_buffer.append(token)
        continue

    if token.is_brace_prep():
        if is_object_marker(token):  # 0853
            attach_to_next_noun(pre_brace)
        elif has_pronoun_suffix(token) or is_infinitive_complement(token):
            attach_to_prev_verb(post_brace)
        elif next_core_is_noun():
            attach_to_next_noun(pre_brace)
        else:
            create_independent_group_with_warning()
        continue

    if token.is_core():
        group = new_group(core=token, implicit=is_implicit(token))
        group.prefixes = drain(prefix_buffer)
        groups.append(group)
        continue

    if token.is_morph():
        last_group().morph.append(token)
        continue
```

### Testing Checklist

- [ ] Normalize all WH/WTH/WAH prefixes
- [ ] Convert `<WTH8xxx>` to `(**8xxx)`
- [ ] 900x skips over `{<...>}` and `{8xxx}`
- [ ] Morphology left-attaches to core
- [ ] `{<0853>}` always right-attaches
- [ ] Pronoun suffix triggers verb left-attach
- [ ] General brace prep right-attaches to noun
- [ ] Warnings generated for ambiguous cases
- [ ] Output has all three sections
- [ ] Morphology notes match *N references

### Verse Count by Chapter (Genesis)

| Chapter | Verses | Chapter | Verses |
|---------|--------|---------|--------|
| Gen 1 | 31 | Gen 26 | 35 |
| Gen 2 | 25 | Gen 27 | 46 |
| Gen 3 | 24 | Gen 28 | 22 |
| Gen 4 | 26 | Gen 29 | 35 |
| Gen 5 | 32 | Gen 30 | 43 |

(Additional chapters available in scripture references)

### Command Templates

```bash
# Single verse
python run_parser_temp.py {chapter} {verse}

# Preview only
python run_parser_temp.py --no-write {chapter} {verse}

# Batch chapter (replace {N} with verse count)
for verse in {1..{N}}; do python run_parser_temp.py {chapter} $verse; done

# Verification
ls -1 output/{Book}/{Chapter}/ | wc -l
ls -1 output/{Book}/{Chapter}/ | grep "_uncertain"

# View output
cat output/{Book}/{Chapter}/{verse}
```

### Directory Structure

```
sn_within_unv_selfgroup_segmentation/
├── fetch_text.sh                    # API wrapper
├── parse_verse_v1_6.py              # Current parser (JSON output)
├── parse_verse.py                   # Legacy parser (text output)
├── run_parser_temp.py               # Batch orchestrator
├── SPECIFICATION_v1.6.md            # Authoritative rules
├── Batch_Parsing_SOP.md             # Workflow documentation
├── UNV_SN_Output_Format_Gen_1_1.md  # Output format spec
├── CLAUDE.md                        # Project instructions
├── output/                          # Generated files
│   └── {Book}/
│       └── {Chapter}/
│           ├── {verse}
│           └── {verse}_uncertain
└── .claude/
    └── skills/
        └── unv-sn-backparse/        # This skill
            ├── SKILL.md
            ├── examples.md
            └── reference.md
```

### Implementation Status

**v1.6 Parser**: Partial implementation
- ✅ Token normalization
- ✅ Basic grouping
- ✅ Prefix attachment
- ⚠️ Brace preposition decision tree (placeholder logic exists)
- ⚠️ qp.php consultation for verb/noun detection
- ❌ Construct state linking (optional)
- ✅ Warning generation

**Legacy Parser**: Functional but does not implement full v1.6 rules

### Known Limitations

1. Brace preposition decision tree requires qp.php parsing
2. Verb/noun detection may need morphological analysis
3. Construct state linking is optional feature (v1.2-B)
4. Some morphology codes (8799) have context-dependent meanings
5. FHL API may have incomplete Strong's data for some verses

### Related Documentation

- **Parent Project**: `/Users/joshua/work/strong_number_embedding/CLAUDE.md`
- **Spec v1.6**: `SPECIFICATION_v1.6.md` (this directory)
- **Batch SOP**: `Batch_Parsing_SOP.md` (this directory)
- **Output Format**: `UNV_SN_Output_Format_Gen_1_1.md` (this directory)
- **Dual Readers**: `../dual_reader/` and `../dual_reader_right_editor/`

### Support

For questions about:
- **Parsing logic**: Consult SPECIFICATION_v1.6.md §3.3
- **Output format**: See UNV_SN_Output_Format_Gen_1_1.md
- **Batch workflow**: Read Batch_Parsing_SOP.md
- **API usage**: Check `fetch_text.sh` script
- **Project context**: Review CLAUDE.md files
