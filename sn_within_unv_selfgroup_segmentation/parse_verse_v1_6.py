import json
import re
import sys
import os
from datetime import datetime

# This script is a refactoring of parse_verse.py to implement SPECIFICATION_v1.6.md

# --- Configuration from SPECIFICATION_v1.6.md (4.1) ---
PROFILE = {
    "brace_preps": ["05921", "04480", "0413", "00996"],
    "object_marker": "0853",
    "ignored_codes": ["09015"]
}

# --- Logging Configuration ---
OUTPUT_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UNCERTAIN_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "uncertain_or_expandable_issues.txt")
NOTABLE_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "compatible_but_notable_issues.txt")

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
        elif number.startswith('09') and len(number) in (4, 5):
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
    # Implements the multi-pass grouping logic from SPECIFICATION_v1.6.md (3.3)

    # --- Pass 1: Initial Grouping ---
    items = []
    for token in tokens:
        if token['type'] in ['strong', 'implicit_strong']:
            items.append({
                "core": token['value'], "implicit": token['type'] == 'implicit_strong',
                "_is_group": True, "_token": token,
                "prefixes": [], "morph": [], "pre_brace": [], "post_brace": [],
                "warnings": [], "source_type": token['type']
            })
        else:
            items.append(token)

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
            for j in range(i + 1, len(items)):
                if items[j].get('_is_group') and is_noun(items[j], qp_records):
                    items[j]["pre_brace"].append(item['value'])
                    is_attached = True
                    break
        elif item_type == 'brace_prep':
            # Simplified right-attachment to next noun
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
        qp_info, word_type_pos, chinese_meaning, wform = extract_word_metadata(group, qp_records)

        if not qp_info:
            note = f"Strong's number <{group['core']}> from qb.php not found in qp.php records."
            uncertainty_notes.append(note)
            # Log to uncertain_or_expandable_issues.txt
            if verse_ref:
                append_to_log(UNCERTAIN_LOG, verse_ref, "qb_qp_mismatch", note)

        prefix_display = ''.join(f"<{code}>" for code in group.get('prefixes', []))
        pre_brace_display = ''.join(f"<{code}>" for code in group.get('pre_brace', []))
        post_brace_display = ''.join(f"<{code}>" for code in group.get('post_brace', []))
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
