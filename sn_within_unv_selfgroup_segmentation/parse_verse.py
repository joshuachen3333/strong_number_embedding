import json
import re
import sys

def parse_verse(qb_json_str, qp_json_str):
    qb_data = json.loads(qb_json_str)
    qp_data = json.loads(qp_json_str)

    bible_text_raw = qb_data['record'][0]['bible_text']
    qp_records = qp_data['record']

    uncertainty_notes = []

    # --- 3.1 Markup Normalization ---
    bible_text_normalized = re.sub(r'(WH|WTH|WAH)', '', bible_text_raw)

    # --- Tokenization and Classification ---
    all_bracketed_expressions_with_pos = []
    for match in re.finditer(r'(<[^>]+>)|(\{[^}]+\})|(\( [^)]+\))', bible_text_normalized):
        full_match = match.group(0)
        content = full_match[1:-1] # Remove outer brackets
        
        if full_match.startswith('{<') and full_match.endswith('>}'):
            inner_content = full_match[2:-2] # Get content inside < >
            all_bracketed_expressions_with_pos.append({
                'start': match.start(),
                'end': match.end(),
                'raw': full_match,
                'content': inner_content,
                'type': 'implicit_strong_candidate'
            })
        else:
            all_bracketed_expressions_with_pos.append({
                'start': match.start(),
                'end': match.end(),
                'raw': full_match,
                'content': content,
                'type': 'candidate'
            })

    processed_tokens = []
    for item in all_bracketed_expressions_with_pos:
        content = item['content']
        raw = item['raw']
        token_type = 'unknown'
        value = content

        if item['type'] == 'implicit_strong_candidate':
            if re.match(r'\d{3,5}', content):
                token_type = 'implicit_strong'
                value = content
        elif raw.startswith('<') and raw.endswith('>'):
            if re.match(r'09\d{3}', content): # 9xxx range
                token_type = '900x'
                value = content
            elif re.match(r'8\d{3}', content): # 8xxx range (morphology in < > from qb.php)
                token_type = 'morph'
                value = content
            elif re.match(r'\d{3,5}', content): # Other numbers in < > are strong
                token_type = 'strong'
                value = content
        elif raw.startswith('(') and raw.endswith(')'):
            if re.match(r'8\d{3}', content): # 8xxx range (explicit morphology)
                token_type = 'morph'
                value = content
        elif raw.startswith('{') and raw.endswith('}'):
            if re.match(r'8\d{3}', content): # 8xxx range (implicit morphology)
                token_type = 'morph'
                value = content
            else:
                token_type = 'unknown_implicit'
                value = content
        
        if token_type != 'unknown':
            processed_tokens.append({
                'raw': raw,
                'value': value,
                'type': token_type,
                'start': item['start'],
                'end': item['end']
            })

    processed_tokens.sort(key=lambda x: x['start'])

    # --- 3.3 Grouping and Merging Rules ---
    final_parsed_units = []
    prefix_buffer = [] # For 900x codes
    morphology_notes_map = {}
    morph_ref_counter = 1

    # Helper to get qp_record info
    def get_qp_info(sn_value):
        sn_value_stripped = sn_value.lstrip('0')
        for record in qp_records:
            if 'sn' in record and record['sn'].lstrip('0') == sn_value_stripped:
                # Ensure it's a strong number (not 8xxx or 9xxx)
                if not (record['sn'].startswith('8') or record['sn'].startswith('9')):
                    return record
        return None

    for token in processed_tokens:
        if token['type'] == '900x':
            prefix_buffer.append(token)
        elif token['type'] in ['strong', 'implicit_strong']:
            current_unit = {
                'strong_token': token,
                'prefixes': prefix_buffer,
                'morphs': []
            }
            prefix_buffer = [] # Clear buffer after attaching
            final_parsed_units.append(current_unit)
        elif token['type'] == 'morph':
            if final_parsed_units: # Attach to the last strong unit
                final_parsed_units[-1]['morphs'].append(token)
            else:
                uncertainty_notes.append(f"Dangling morphology code {token['raw']} found without a preceding Strong's number.")
        elif token['type'] == 'unknown_implicit':
            uncertainty_notes.append(f"Unknown implicit token {token['raw']} encountered. Not defined in specification.")

    # --- Output Construction ---
    output_parts = []

    # I. Parsed and Formatted Text Section
    output_parts.append("Parsed and Formatted Text Section:")
    for unit in final_parsed_units:
        strong_token = unit['strong_token']
        sn_value = strong_token['value']
        qp_strong_info = get_qp_info(sn_value)

        word_type_pos = "未知詞性" # Part of speech for the main line
        chinese_meaning = "未知意義"
        full_morph_description = "" # Full morphology for notes

        if qp_strong_info:
            full_morph_description = qp_strong_info.get('wform', "")
            chinese_meaning = qp_strong_info.get('exp', chinese_meaning)
            
            # Extract part of speech from full_morph_description
            pos_match = re.match(r'^([^，]+)', full_morph_description)
            if pos_match:
                word_type_pos = pos_match.group(1)
            elif full_morph_description: # If no comma, take the whole thing as POS if it exists
                word_type_pos = full_morph_description
        else:
            uncertainty_notes.append(f"Strong's number <{sn_value}> from qb.php not found in qp.php records.")

        # Handle prefixes (900x)
        prefix_display = ""
        for p_token in unit['prefixes']:
            prefix_display += f"<{p_token['value']}>"

        morph_display = ""
        morph_ref_str = ""
        if unit['morphs'] and full_morph_description: # Only add morph info if there are morph tokens and a description
            morph_code_value = unit['morphs'][0]['value'] # Assuming one morph per strong for now
            morph_display = f"({morph_code_value})"
            
            # Add to morphology notes map and get reference
            if full_morph_description not in morphology_notes_map:
                morphology_notes_map[full_morph_description] = f"*{morph_ref_counter}"
                morph_ref_counter += 1
            morph_ref_str = f" {morphology_notes_map[full_morph_description]}"

        # Construct the formatted line
        formatted_line = f"{prefix_display}<{sn_value}>{morph_display} — {word_type_pos}「{chinese_meaning}」{morph_ref_str}"
        output_parts.append(formatted_line)
    output_parts.append("")

    # II. Raw UNV+SN Source Text Section
    output_parts.append("Raw UNV+SN Source Text Section:")
    output_parts.append(bible_text_raw)
    output_parts.append("")

    # III. Morphology Notes Section
    if morphology_notes_map:
        output_parts.append("Morphology Notes Section:")
        # Sort morphology notes by their reference number for consistent output
        sorted_morph_notes = sorted(morphology_notes_map.items(), key=lambda item: int(item[1][1:]))
        for desc, ref in sorted_morph_notes:
            output_parts.append(f"{ref}: {desc}")
        output_parts.append("")

    # IV. Uncertainty Notes Section
    if uncertainty_notes:
        output_parts.append("--- UNCERTAINTY NOTES ---")
        for note in uncertainty_notes:
            output_parts.append(note)
        output_parts.append("")

    return "\n".join(output_parts)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python parse_verse.py <qb_json_string> <qp_json_string>")
        sys.exit(1)
    
    qb_json_str = sys.argv[1]
    qp_json_str = sys.argv[2]
    
    result = parse_verse(qb_json_str, qp_json_str)
    print(result)
