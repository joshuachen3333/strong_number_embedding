import json
import re
import sys
import os
from datetime import datetime

# This script implements SPECIFICATION_v1.8.md
# v1.7 adds compound preposition detection by querying qp.php wform field
# v1.7.2 enhances compound detection to skip 900x prefixes (multi-token compounds)
# v1.8 generalizes compound detection to support all compound prepositions (not just מִן)

# --- Configuration from SPECIFICATION_v1.7.md ---
PROFILE = {
    "brace_preps": ["05921", "04480", "0413", "00996"],
    "object_marker": "0853",
    "ignored_codes": ["09015"],

    # v1.7 new configuration
    "detect_compounds_from_qp": True,      # Detect compounds from qp.php wform
    "merge_prep_plus_prep": True,          # Merge prep+prep compounds (e.g., מֵעַל)
    "merge_prep_plus_noun": False,         # Optional: merge prep+noun compounds
}

# --- Logging Configuration ---
OUTPUT_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UNCERTAIN_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "uncertain_or_expandable_issues.txt")
NOTABLE_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "compatible_but_notable_issues.txt")
PREP_NOUN_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "compound_prep_plus_noun.txt")

def append_to_log(log_file, verse_ref, issue_type, message):
    """
    Append an issue to the specified log file.

    Args:
        log_file: Path to the log file (UNCERTAIN_LOG or NOTABLE_LOG)
        verse_ref: String identifying the verse (e.g., "Gen 1:1")
        issue_type: Category of issue (e.g., "uncertain", "spec_expandable", "notable")
        message: Detailed description of the issue
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {verse_ref} | {issue_type} | {message}\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

def get_qp_info(sn_value, qp_records):
    sn_value_stripped = sn_value.lstrip('0')
    for record in qp_records:
        if 'sn' in record and record['sn'].lstrip('0') == sn_value_stripped:
            return record
    return None

def detect_generic_compound(tokens, current_index, qp_records):
    """
    v1.8: Generic compound detection for all types of compound prepositions.

    Supports:
    - מִן (04480) compounds (v1.7 original)
    - 900x-starting compounds like לִפְנֵי (v1.8 new)
    - Multi-token compounds crossing 900x prefixes (v1.7.2)

    Extracts compound information from qp.php wform and remark fields.
    Returns compound_info dict if detected, None otherwise.
    """
    current_token = tokens[current_index]
    current_type = current_token.get('type')
    current_value = current_token.get('value')

    # Collect tokens starting from current position
    j = current_index + 1
    collected_tokens = [current_token]
    intervening_900x = []

    # Collect subsequent 900x and first core token
    while j < len(tokens):
        token_type = tokens[j].get('type')
        if token_type == 'p900x':
            intervening_900x.append(tokens[j]['value'])
            collected_tokens.append(tokens[j])
            j += 1
        elif token_type in ['strong', 'implicit_strong']:
            collected_tokens.append(tokens[j])
            j += 1
            break  # Stop after first core token
        else:
            break  # Stop at morph, brace, etc.

    if len(collected_tokens) < 2:
        # Need at least 2 tokens to form a compound
        return None

    # Build list of all SNs involved
    all_sns = [t.get('value') for t in collected_tokens if t.get('type') in ['strong', 'implicit_strong', 'p900x']]

    # v1.8: Search qp.php for compound indicators
    qp_record = None

    # Strategy 1: Search by any involved SN
    for record in qp_records:
        if 'sn' not in record:
            continue

        record_sn = record.get('sn', '').lstrip('0')
        wform = record.get('wform', '')
        remark = record.get('remark', '')

        # Check if this record mentions compound structure
        compound_indicators = [
            '介系詞 מִן +',
            '從介系詞 לְ +',
            '從介系詞 מִן +',
            '+ 名詞',
        ]

        has_indicator = any(ind in (wform + ' ' + remark) for ind in compound_indicators)

        # Check if remark mentions any of our SNs
        mentions_sn = any(
            (f"SN {sn.lstrip('0')}" in remark or f"SN {int(sn)}" in remark)
            for sn in all_sns if sn.isdigit()
        )

        if has_indicator and (record_sn in [s.lstrip('0') for s in all_sns] or mentions_sn):
            qp_record = record
            break

    # Strategy 2: If not found, search all records for matching patterns
    if not qp_record:
        for record in qp_records:
            wform = record.get('wform', '')
            remark = record.get('remark', '')
            combined = wform + ' ' + remark

            # Look for compound patterns mentioning our tokens
            has_compound_pattern = any(pattern in combined for pattern in [
                '介系詞', '+ 名詞', '從介系詞'
            ])

            if not has_compound_pattern:
                continue

            # Check if mentions any of our SNs
            mentions_any = any(
                str(int(sn)) in remark or sn in remark
                for sn in all_sns if sn.isdigit()
            )

            if mentions_any:
                qp_record = record
                break

    if not qp_record:
        return None

    # Determine compound type
    wform = qp_record.get('wform', '')
    remark = qp_record.get('remark', '')
    combined_text = wform + ' ' + remark

    if '介系詞 מִן +' in combined_text and '介系詞' in combined_text:
        compound_type = 'prep+prep'
    elif '介系詞' in combined_text and '名詞' in combined_text:
        compound_type = 'prep+noun'
    else:
        compound_type = 'generic_compound'

    # Determine if should merge
    should_merge = False
    if compound_type == 'prep+prep' and PROFILE['merge_prep_plus_prep']:
        should_merge = True
    elif compound_type == 'prep+noun' and PROFILE['merge_prep_plus_noun']:
        should_merge = True

    # Use qp.php's SN when available (handles qb/qp mismatches)
    main_sn = qp_record.get('sn', all_sns[-1])

    return {
        'type': compound_type,
        'components': all_sns,
        'hebrew': qp_record.get('word', ''),
        'structure': wform,
        'remark': remark,
        'meaning': qp_record.get('exp', ''),
        'main_sn': main_sn,
        'qp_sn': qp_record.get('sn'),
        'should_merge': should_merge,
        'intervening_900x': intervening_900x,
        'tokens_to_skip': len(collected_tokens) - 1
    }

def has_pronoun_suffix(sn_value, qp_records):
    """
    Check if a Strong's number has a pronoun suffix by examining qp.php wform.

    Implements SPECIFICATION_v1.7.2.md §3.4 Exception 1.
    Returns True if wform contains pronoun suffix markers like "詞尾".
    """
    qp_info = get_qp_info(sn_value, qp_records)
    if not qp_info or 'wform' not in qp_info:
        return False

    wform = qp_info['wform']
    # Check for pronoun suffix indicators
    # Examples: "介系詞 מִן + 3 單陽詞尾", "受詞記號 + 3 單陽詞尾"
    return '詞尾' in wform

def is_noun(group, qp_records):
    if not group or not group.get('_is_group'):
        return False
    qp_info = get_qp_info(group['core'], qp_records)
    if qp_info and 'wform' in qp_info:
        return '名詞' in qp_info['wform'] # Noun
    return False

def tokenize_and_classify(bible_text_raw):
    # Implements a more robust tokenization based on SPECIFICATION_v1.6.md
    tokens = []
    # Regex to find all bracketed expressions, including the outer brackets and inner content
    pattern = r'(?:\{<([^>]+)>\})|(?:<([^>]+)>)' # Group 1 for {<...>} and Group 2 for <...>
    for match in re.finditer(pattern, bible_text_raw):
        raw_content = ""
        token_type_hint = ""
        if match.group(1): # Matched {<...>}
            raw_content = match.group(1)
            token_type_hint = 'implicit'
        else: # Matched <...>
            raw_content = match.group(2)
            token_type_hint = 'explicit'
        
        # Strip WH/WTH/WAH prefix to get the number
        number_match = re.search(r'(\d{3,5})$', raw_content)
        if not number_match:
            continue # Skip if no number found
        
        number = number_match.group(1)
        token = {
            'start': match.start(), 'end': match.end(),
            'raw': match.group(0), 'value': number, 'type': ''
        }

        # --- Classification Logic ---
        if number.startswith('8') and len(number) == 4:
            token['type'] = 'morph'
        elif number.startswith('09') and len(number) == 5:
            token['type'] = 'p900x'
        elif token_type_hint == 'implicit':
            if number == PROFILE['object_marker']:
                token['type'] = 'object_marker'
            elif number in PROFILE['brace_preps']:
                token['type'] = 'brace_prep'
            else:
                token['type'] = 'implicit_strong'
        else:
            token['type'] = 'strong'

        if token['value'] not in PROFILE['ignored_codes']:
            tokens.append(token)

    return tokens

def group_and_merge(tokens, qp_records):
    # Implements the multi-pass grouping logic from SPECIFICATION_v1.7.md (3.3)

    # --- Pass 0: Compound Detection (v1.8 generic version) ---
    # Detect and mark all compound prepositions (not just מִן)
    if PROFILE['detect_compounds_from_qp']:
        i = 0
        while i < len(tokens):
            token = tokens[i]
            token_type = token.get('type')

            # v1.8: Try to detect compound starting from any core or p900x token
            should_check = (
                (token_type in ['strong', 'implicit_strong']) or
                (token_type == 'p900x')
            )

            if should_check:
                # v1.8: Generic compound detection
                compound_info = detect_generic_compound(tokens, i, qp_records)
                if compound_info:
                    if compound_info['should_merge']:
                        # Mark all involved tokens as part of compound for merging
                        tokens[i]['_compound_info'] = compound_info
                        tokens[i]['_compound_part'] = 'first'

                        # Mark all tokens in the compound
                        tokens_to_skip = compound_info['tokens_to_skip']
                        for j in range(1, tokens_to_skip + 1):
                            if i + j < len(tokens):
                                tokens[i + j]['_compound_part'] = 'middle' if j < tokens_to_skip else 'last'

                        i += tokens_to_skip + 1  # Skip all compound tokens
                        continue
                    else:
                        # Detected but not merged - mark for special logging
                        tokens[i]['_unmerged_compound'] = compound_info
            i += 1

    # --- Pass 1: Initial Grouping ---
    items = []
    i = 0
    while i < len(tokens):
        token = tokens[i]

        # v1.7/v1.7.2: Handle compound prepositions
        if token.get('_compound_info'):
            compound_info = token['_compound_info']
            # Create merged compound group
            items.append({
                "core": compound_info['components'],  # List of all SNs (including 900x)
                "compound": True,
                "compound_type": compound_info['type'],
                "compound_hebrew": compound_info['hebrew'],
                "compound_structure": compound_info['structure'],
                "compound_meaning": compound_info['meaning'],
                "implicit": False,
                "_is_group": True,
                "_token": token,
                "prefixes": [], "morph": [], "pre_brace": [], "post_brace": [],
                "warnings": [], "source_type": "compound_preposition"
            })
            # v1.7.2: Skip all tokens in compound (determined by tokens_to_skip)
            i += compound_info['tokens_to_skip'] + 1
            continue
        elif token.get('_compound_part') in ['middle', 'last']:
            # v1.7.2: This token is part of compound, already processed
            i += 1
            continue

        # Regular processing
        if token['type'] in ['strong', 'implicit_strong']:
            group = {
                "core": token['value'], "implicit": token['type'] == 'implicit_strong',
                "_is_group": True, "_token": token,
                "prefixes": [], "morph": [], "pre_brace": [], "post_brace": [],
                "warnings": [], "source_type": token['type']
            }
            # v1.7: Preserve _unmerged_compound at group level (not just in _token)
            if '_unmerged_compound' in token:
                group['_unmerged_compound'] = token['_unmerged_compound']
            items.append(group)
        else:
            items.append(token)

        i += 1

    # --- Pass 2: Attachment ---
    for i, item in enumerate(items):
        if item.get('_is_group'):
            continue

        item_type = item['type']
        is_attached = False

        if item_type == 'morph':
            for j in range(i - 1, -1, -1):
                if items[j].get('_is_group'):
                    items[j]["morph"].append(item['value'])
                    is_attached = True
                    break
        elif item_type == 'p900x':
            for j in range(i + 1, len(items)):
                if items[j].get('_is_group'):
                    items[j]["prefixes"].append(item['value'])
                    is_attached = True
                    break
        elif item_type == 'object_marker':
            # Exception 1: If object marker has pronoun suffix, left-attach to verb
            if has_pronoun_suffix(item['value'], qp_records):
                for j in range(i - 1, -1, -1):
                    if items[j].get('_is_group'):
                        items[j]["post_brace"].append(item['value'])
                        is_attached = True
                        break
            else:
                # Exception 2: Object marker normally right-attaches to noun
                for j in range(i + 1, len(items)):
                    if items[j].get('_is_group') and is_noun(items[j], qp_records):
                        items[j]["pre_brace"].append(item['value'])
                        is_attached = True
                        break
        elif item_type == 'brace_prep':
            # Exception 1: If brace prep has pronoun suffix, left-attach to verb
            if has_pronoun_suffix(item['value'], qp_records):
                for j in range(i - 1, -1, -1):
                    if items[j].get('_is_group'):
                        items[j]["post_brace"].append(item['value'])
                        is_attached = True
                        break
            else:
                # General case: Right-attach to next noun
                for j in range(i + 1, len(items)):
                    if items[j].get('_is_group') and is_noun(items[j], qp_records):
                        items[j]["pre_brace"].append(item['value'])
                        is_attached = True
                        break
        
        if is_attached:
            item['_remove'] = True
        else:
            # If not attached, convert to a group with a warning
            item['_is_group'] = True
            item['core'] = item['value']
            item['implicit'] = item_type not in ['strong', 'implicit_strong']
            item['prefixes'] = item.get('prefixes', [])
            item['morph'] = item.get('morph', [])
            item['pre_brace'] = item.get('pre_brace', [])
            item['post_brace'] = item.get('post_brace', [])
            item['warnings'] = [f"dangling_{item_type}"]
            item['source_type'] = item_type

    # --- Pass 3: Finalization ---
    final_groups = []
    for item in items:
        if item.get('_is_group'):
            item.pop('_is_group', None)
            item.pop('_token', None)
            item.pop('_remove', None)
            item.pop('_token_start', None)
            item.pop('_start', None)
            item.pop('_end', None)
            item.pop('_raw', None)
            final_groups.append(item)

    return final_groups

def render_warning_message(group, warning):
    code = group.get('core', 'UNKNOWN')
    warning_map = {
        'brace_attach_ambiguous': f"Brace preposition <{code}> could not be confidently attached to an adjacent core.",
        'dangling_morph': f"Dangling morphology code {code} found without a preceding Strong's number.",
        'dangling_p900x': f"900x prefix <{code}> had no following Strong's number to attach to.",
        'dangling_object_marker': f"Object marker <{code}> had no suitable noun to attach to.",
        'dangling_brace_prep': f"Brace preposition <{code}> had no suitable attachment point."
    }
    return warning_map.get(warning, f"Unhandled warning {warning} on token <{code}>.")

def extract_word_metadata(group, qp_records):
    qp_info = get_qp_info(group['core'], qp_records)
    word_type_pos = "未知詞性"
    chinese_meaning = "未知意義"
    wform = ""

    if qp_info:
        wform = qp_info.get('wform', "") or ""
        chinese_meaning = qp_info.get('exp', chinese_meaning)
        if wform:
            if '，' in wform:
                word_type_pos = wform.split('，', 1)[0] or wform
            elif ',' in wform:
                word_type_pos = wform.split(',', 1)[0] or wform
            else:
                word_type_pos = wform
    return qp_info, word_type_pos, chinese_meaning, wform

def format_groups_to_text(groups, bible_text_raw, qp_records, verse_ref=None):
    output_lines = ["Parsed and Formatted Text Section:"]
    morphology_notes_index = {}
    morphology_notes_entries = []
    morph_ref_counter = 1
    uncertainty_notes = []
    notable_issues = []

    for group in groups:
        # v1.7: Handle compound prepositions
        if group.get('compound'):
            # This is a compound preposition
            components = group['core']
            core_display = ''.join(f"<{code}>" for code in components)
            word_type_pos = "複合介系詞"
            chinese_meaning = group['compound_meaning']
            wform = group['compound_structure']

            # Add structure note
            structure_note = f"[註]: {group['compound_structure']}"

            prefix_display = ''.join(f"<{code}>" for code in group.get('prefixes', []))
            pre_brace_display = ''.join(f"<{code}>" for code in group.get('pre_brace', []))
            post_brace_display = ''.join(f"<{code}>" for code in group.get('post_brace', []))

            morph_codes = group.get('morph', [])
            morph_display = ''.join(f"({code})" for code in morph_codes)
            morph_ref = ""

            formatted_line = f"{prefix_display}{pre_brace_display}{core_display}{morph_display}{post_brace_display} — {word_type_pos} {group['compound_hebrew']}「{chinese_meaning}」{morph_ref}".rstrip()
            output_lines.append(formatted_line)
            output_lines.append(structure_note)
            continue

        # Regular processing
        qp_info, word_type_pos, chinese_meaning, wform = extract_word_metadata(group, qp_records)

        if not qp_info:
            # v1.7: Check if this is <04480> with an unmerged compound
            # If so, log to compound_prep_plus_noun.txt instead of uncertain log
            note = f"Strong's number <{group['core']}> from qb.php not found in qp.php records."

            # Check if this group was marked as an unmerged compound during Pass 0
            # v1.7: Check group directly (not _token, which gets removed during cleanup)
            is_prep_noun_compound = '_unmerged_compound' in group

            if is_prep_noun_compound and verse_ref:
                # This is a detected prep+noun compound that wasn't merged
                compound_info = group['_unmerged_compound']
                next_sn = compound_info['main_sn']
                detail_note = f"Prep+noun compound detected: <04480><{next_sn}> = {compound_info['hebrew']} ({compound_info['structure']}) - not merged per config"
                append_to_log(PREP_NOUN_LOG, verse_ref, "prep_noun_compound", detail_note)
                # Do NOT add to uncertainty_notes or UNCERTAIN_LOG
            elif verse_ref:
                # Regular qb_qp_mismatch
                uncertainty_notes.append(note)
                append_to_log(UNCERTAIN_LOG, verse_ref, "qb_qp_mismatch", note)
            else:
                # No verse_ref (shouldn't happen in practice)
                uncertainty_notes.append(note)

        prefix_display = ''.join(f"<{code}>" for code in group.get('prefixes', []))
        pre_brace_display = ''.join(f"{{<{code}>}}" for code in group.get('pre_brace', []))
        post_brace_display = ''.join(f"{{<{code}>}}" for code in group.get('post_brace', []))
        core_display = f"<{group['core']}>"

        morph_codes = group.get('morph', [])
        morph_display = ''.join(f"({code})" for code in morph_codes)
        morph_ref = ""

        if morph_codes and wform:
            if wform not in morphology_notes_index:
                label = f"*{morph_ref_counter}"
                morphology_notes_index[wform] = label
                morphology_notes_entries.append((label, wform))
                morph_ref_counter += 1
            morph_ref = f" {morphology_notes_index[wform]}"

        # Build formatted line with proper ordering
        # Order: prefix + pre_brace + core + morph + post_brace
        formatted_line = f"{prefix_display}{pre_brace_display}{core_display}{morph_display}{post_brace_display} — {word_type_pos}「{chinese_meaning}」{morph_ref}".rstrip()
        output_lines.append(formatted_line)

        for warning in group.get('warnings', []):
            warning_message = render_warning_message(group, warning)
            if warning_message not in uncertainty_notes:
                uncertainty_notes.append(warning_message)
                # Log warnings to appropriate file
                if verse_ref:
                    # Warnings like "dangling_*" and "brace_attach_ambiguous" are uncertain
                    if any(w in warning for w in ["dangling", "ambiguous"]):
                        append_to_log(UNCERTAIN_LOG, verse_ref, warning, warning_message)
                    else:
                        # Other warnings might be notable but compatible
                        append_to_log(NOTABLE_LOG, verse_ref, warning, warning_message)

    output_lines.append("")
    output_lines.append("Raw UNV+SN Source Text Section:")
    output_lines.append(bible_text_raw)
    output_lines.append("")

    if morphology_notes_entries:
        output_lines.append("Morphology Notes Section:")
        for label, desc in morphology_notes_entries:
            output_lines.append(f"{label}: {desc}")
        output_lines.append("")

    if uncertainty_notes:
        output_lines.append("--- UNCERTAINTY NOTES ---")
        output_lines.extend(uncertainty_notes)
        output_lines.append("")

    return "\n".join(output_lines)

def parse_verse_v1_6(qb_json_str, qp_json_str, *, output_format="text", verse_ref=None):
    qb_data = json.loads(qb_json_str)
    qp_data = json.loads(qp_json_str)

    bible_text_raw = qb_data['record'][0]['bible_text']
    qp_records = qp_data['record']

    tokens = tokenize_and_classify(bible_text_raw)
    groups = group_and_merge(tokens, qp_records)

    if output_format == "json":
        return json.dumps(groups, indent=2, ensure_ascii=False)
    return format_groups_to_text(groups, bible_text_raw, qp_records, verse_ref)

if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: python parse_verse_v1_6.py <qb_json_string> <qp_json_string> [--json]")
        sys.exit(1)
    
    qb_json_str = sys.argv[1]
    qp_json_str = sys.argv[2]

    output_format = "text"
    if len(sys.argv) == 4:
        if sys.argv[3] == "--json":
            output_format = "json"
        else:
            print(f"Unknown option: {sys.argv[3]}")
            sys.exit(1)

    result = parse_verse_v1_6(qb_json_str, qp_json_str, output_format=output_format)
    print(result)
