# Spec: Preserve WH/WAH Prefixes in Parsed Output Markers

## Overview

Modify the parser (`parse_verse_v1_8.py`) to preserve WH/WAH/WTH prefixes in the `:: ::` boundary markers of parsed output, ensuring visual consistency with the main SN display format.

## MODIFIED Requirements

### Requirement: Marker Format Must Match Main Display
The `:: ::` boundary markers in parsed output SHALL use the same WH/WAH/WTH prefix format as the main SN group display, not the normalized numeric form.

#### Scenario: Object Marker with Braces

**Given** a group containing `{<WH0853>}<WH08064>`

**When** generating the parsed output line

**Then** the output must be:
```
{<WH0853>}<WH08064> — 冠詞 12;h21 + 名詞「天」    ::{<WH0853>}天<WH08064>::
```

**Not:**
```
{<WH0853>}<WH08064> — 冠詞 12;h21 + 名詞「天」    ::{<0853>}天<08064>::
                                                      ^^^      ^^^
                                                      Missing WH prefix
```

#### Scenario: Verb with Morphology

**Given** a group containing `<WH01254>(8804)`

**When** generating the parsed output line

**Then** the marker must show:
```
::<WH01254>(8804)::
```

**Not:**
```
::<01254>(8804)::
```

#### Scenario: Preposition Group

**Given** a group containing `<WAH09002><WH07225>`

**When** generating the parsed output line

**Then** the marker must show:
```
::<WAH09002><WH07225>::
```

**Preserving:**
- The `WAH` prefix (not just `WH`)
- The leading zeros in `09002`
- The `WH` prefix for the second SN

---

### Requirement: Parser Must Track Original and Normalized Forms
The parser's normalization process SHALL preserve the original token text alongside the normalized numeric code for use in output formatting.

#### Scenario: Normalization Preserves Original

**Given** raw input token `{<WH0853>}`

**When** normalization extracts the Strong's Number

**Then** token data must contain:
```python
{
    'sn': '0853',              # Normalized for logic
    'original': '{<WH0853>}',   # Original for display
    'type': 'object_marker'
}
```

#### Scenario: Morphology Code Normalization

**Given** raw input token `<WTH8804>`

**When** normalization processes the morphology code

**Then** token data must contain:
```python
{
    'sn': '8804',              # Normalized
    'original': '<WTH8804>',   # Original with WTH prefix
    'type': 'morphology'
}
```

**Or** for explicit morphology:
```python
{
    'sn': '8804',
    'original': '(**8804)',    # Explicit form
    'type': 'morphology'
}
```

---

## ADDED Requirements

### Requirement: Marker Generation Uses Original Forms
The marker generation logic SHALL construct `:: ::` markers from original token forms, not normalized codes.

#### Scenario: Build Marker from Token Group

**Given** a group containing tokens:
```python
[
    {'sn': '0853', 'original': '{<WH0853>}'},
    {'sn': '08064', 'original': '<WH08064>'}
]
```

**When** `format_group_marker(group)` is called

**Then** it must return:
```
::{<WH0853>}天<WH08064>::
```

**Where:**
- Chinese characters are extracted from the raw text
- Original forms are used verbatim
- Braces, prefixes, and formatting are preserved

#### Scenario: Fallback When Original Missing

**Given** a token without `original` field (legacy data or edge case)

**When** generating marker

**Then** system must:
- Reconstruct form as `<{sn}>`
- Log warning about missing original
- Use fallback format to prevent crash

---

### Requirement: Maintain Backward Compatibility with Parsing Logic
Adding `original` field to tokens SHALL NOT affect the core parsing logic that depends on normalized `sn` codes.

#### Scenario: Grouping Logic Uses Normalized Codes

**Given** brace preposition decision tree checking if SN is in `["05921","04480","0413","00996"]`

**When** token has `original='{<WH05921>}'` and `sn='05921'`

**Then** decision tree must still use `sn` field for logic:
```python
if token['sn'] in BRACE_PREPS:  # Uses normalized '05921'
    # Brace prep logic
```

**Not:**
```python
if token['original'] in BRACE_PREPS:  # Would fail!
```

#### Scenario: Compound Detection Uses Normalized Codes

**Given** compound preposition detection checking `sn == '04480'`

**When** token has `original='<WH04480>'`

**Then** detection must use `sn` field, not `original`

---

### Requirement: Chinese Text Preservation in Markers
Markers SHALL include Chinese text between SNs to match the raw text section format.

#### Scenario: Chinese Between SNs

**Given** group `{<WH0853>}<WH08064>` representing "天" (heaven)

**When** generating marker

**Then** marker must include the Chinese:
```
::{<WH0853>}天<WH08064>::
```

**Where** "天" is extracted from the corresponding position in raw UNV text

#### Scenario: No Chinese Between SNs

**Given** group `<WAH09002><WH07225>` with no Chinese between SNs

**When** generating marker

**Then** marker must be:
```
::<WAH09002><WH07225>::
```

**Without** adding spurious characters

---

## Implementation Notes

### Data Structure Changes

#### Before (v1.8):
```python
token = {
    'sn': '0853',
    'type': 'object_marker',
    'wform': '...'
}
```

#### After (proposed):
```python
token = {
    'sn': '0853',              # Normalized - for logic
    'original': '{<WH0853>}',   # Original - for display
    'type': 'object_marker',
    'wform': '...'
}
```

### Normalization Function Update

```python
def normalize_token(raw_text):
    """
    Extract both normalized and original forms.

    Args:
        raw_text: Raw token like '{<WH0853>}' or '<WAH09002>'

    Returns:
        dict with 'sn' and 'original' keys
    """
    # Match pattern with optional braces and WH/WAH/WTH prefix
    match = re.match(r'(\{)?<(W[ATH]*H?)(\d+)>(})?', raw_text)
    if match:
        return {
            'sn': match.group(3),      # Just the digits
            'original': raw_text       # Full original text
        }

    # Morphology codes
    match = re.match(r'\(\*?\*?(\d+)\)', raw_text)
    if match:
        return {
            'sn': match.group(1),
            'original': raw_text
        }

    # Fallback
    return {'sn': raw_text, 'original': raw_text}
```

### Marker Generation Function

```python
def format_group_marker(group, raw_text):
    """
    Build :: :: marker from group tokens using original forms.

    Args:
        group: Dict with 'tokens' list
        raw_text: Full raw UNV+SN text for extracting Chinese

    Returns:
        Marker string like '::{<WH0853>}天<WH08064>::'
    """
    marker_parts = []

    for i, token in enumerate(group['tokens']):
        # Use original form if available
        if 'original' in token:
            marker_parts.append(token['original'])
        else:
            # Fallback: reconstruct
            marker_parts.append(f"<{token['sn']}>")
            logging.warning(f"Token missing 'original' field: {token}")

        # Extract Chinese between this token and next
        if i < len(group['tokens']) - 1:
            chinese = extract_chinese_between(
                raw_text,
                token['original'],
                group['tokens'][i + 1]['original']
            )
            marker_parts.append(chinese)

    return '::' + ''.join(marker_parts) + '::'
```

### Chinese Text Extraction

```python
def extract_chinese_between(text, sn1, sn2):
    """
    Extract Chinese characters between two SN tags in raw text.

    Args:
        text: Full raw text
        sn1: First SN tag (e.g., '{<WH0853>}')
        sn2: Second SN tag (e.g., '<WH08064>')

    Returns:
        Chinese text between the tags, or empty string
    """
    # Escape regex special chars in sn1 and sn2
    sn1_escaped = re.escape(sn1)
    sn2_escaped = re.escape(sn2)

    # Match: sn1 + (anything) + sn2
    pattern = f'{sn1_escaped}(.*?){sn2_escaped}'
    match = re.search(pattern, text)

    if match:
        between = match.group(1)
        # Filter out other SN tags, keep only Chinese
        cleaned = re.sub(r'<[^>]+>|\([^)]+\)|\{[^}]+\}', '', between)
        return cleaned.strip()

    return ''
```

## Related Capabilities

- `position-based-color-mapping` - Colored output must match marker format
- Parser output format (SPECIFICATION_v1.8) - Markers are part of formal output spec

## Migration Path

### Phase 1: Add Original Field Without Using It

1. Update normalization to populate `original` field
2. Verify all tokens have `original` field
3. Do not change marker generation yet

### Phase 2: Update Marker Generation

1. Modify `format_group_marker()` to use `original` field
2. Test output matches expected format
3. Deploy to production

### Phase 3: Make Original Field Mandatory

1. Remove fallback logic for missing `original`
2. Add validation to ensure `original` is always present

## Success Metrics

1. **Correctness:** All `:: ::` markers use WH/WAH/WTH prefix format
2. **Consistency:** Marker format matches main SN display format
3. **Completeness:** No missing or malformed markers
4. **Backward Compatibility:** Parsing logic still works with normalized `sn` codes
