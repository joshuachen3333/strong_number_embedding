import json
import re
import sys
import os
from datetime import datetime
import urllib.request
import urllib.parse
from functools import lru_cache

# This script implements SPECIFICATION_v1.8.md
# v1.7 adds compound preposition detection by querying qp.php wform field
# v1.7.2 enhances compound detection to skip 900x prefixes (multi-token compounds)
# v1.8 generalizes compound detection to support all compound prepositions (not just מִן)
# v1.8.5 preserves WH/WAH/WTH prefixes in :: :: markers for visual consistency with viewer

# ============================================================================
# Version and Specification Metadata
# ============================================================================

PARSER_VERSION = "v1.8"
SPEC_FILE = f"SPECIFICATION_{PARSER_VERSION}.md"

# --- Output Formatting Configuration ---
LINE_WIDTH = 80  # Target column width for spec reference alignment

# --- Configuration from SPECIFICATION_v1.8.md ---
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
QB_QP_MISMATCH_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "strong_number_from_qb.php_not_found_in_qp.php.txt")
DANGLING_PREFIXES_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "dangling_prefixes.txt")
DANGLING_BRACE_PREPS_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "dangling_brace_preps.txt")
DANGLING_OBJECT_MARKERS_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "dangling_object_markers.txt")
QP_DATA_TYPE_ERRORS_LOG = os.path.join(OUTPUT_BASE_DIR, "output", "qp_data_type_errors.txt")

# ============================================================================
# Specification Section Loading
# ============================================================================

@lru_cache(maxsize=1)
def load_spec_sections():
    """
    Load SPECIFICATION metadata (version and section mappings) from markdown file.

    This function is called once at module load and cached for performance.
    It implements a dual-strategy approach:
    1. Preferred: Extract HTML comment tags <!-- spec:rule_name -->
    2. Fallback: Use known section mappings for v1.8

    Returns:
        dict: {
            'version': 'v1.8',
            'spec_file': 'SPECIFICATION_v1.8.md',
            'sections': {
                'compound': '3.3',
                'prefix': '3.3.1',
                'morph': '3.3.2',
                'object_marker': '3.3.3',
                'brace_right': '3.3.4.1',
                'brace_left': '3.3.4.2',
                'grouping': '3.4',
            }
        }

    Raises:
        FileNotFoundError: If SPECIFICATION file not found
        ValueError: If version mismatch between parser and spec file
    """
    if not os.path.exists(SPEC_FILE):
        raise FileNotFoundError(
            f"{SPEC_FILE} not found. "
            f"Parser {PARSER_VERSION} requires {SPEC_FILE} in the same directory."
        )

    with open(SPEC_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract and verify version from first line
    first_line = content.split('\n')[0]
    version_match = re.search(r'v(\d+\.\d+)', first_line)
    if not version_match:
        raise ValueError(f"Cannot extract version from {SPEC_FILE} first line: {first_line}")

    spec_version = version_match.group(0)
    if spec_version != PARSER_VERSION:
        raise ValueError(
            f"Version mismatch: parser expects {PARSER_VERSION}, "
            f"but {SPEC_FILE} has {spec_version}"
        )

    # Strategy 1: Try to extract HTML comment tags (preferred)
    sections = _extract_spec_tags(content)

    # Strategy 2: Fallback to known section mappings for missing rules
    # Always apply fallback for rules not found in tags
    fallback_sections = {
        'compound': '3.3',
        'prefix': '3.3.1',
        'morph': '3.3.2',
        'object_marker': '3.3.3',  # Object marker (special case in 3.4.4)
        'brace_right': '3.4.4',    # General brace prep right-attach
        'brace_left': '3.4.4',     # Brace prep left-attach (pronoun suffix)
        'grouping': '3.4',
    }

    # Merge: tags take precedence, fallback fills in missing keys
    for key, value in fallback_sections.items():
        if key not in sections:
            sections[key] = value

    if not sections:
        print(f"ℹ️  No spec tags found in {SPEC_FILE}, using fallback mappings")
    elif len(sections) < len(fallback_sections):
        print(f"ℹ️  Using {len(sections)} tagged sections + fallback for remaining")

    return {
        'version': spec_version,
        'spec_file': SPEC_FILE,
        'sections': sections
    }

def _extract_spec_tags(content):
    """
    Extract spec tags from HTML comments in markdown content.
    Pattern: ### 3.3.1 Title <!-- spec:rule_name -->

    Args:
        content: Full markdown file content

    Returns:
        dict: Mapping from rule_name to section_number
    """
    sections = {}

    # Pattern matches: ##+ section_number anything <!-- spec:rule_name -->
    pattern = r'^###+\s+(\d+(?:\.\d+)*)\s+[^<]*<!--\s*spec:(\w+)\s*-->'

    for match in re.finditer(pattern, content, re.MULTILINE):
        section_num = match.group(1)
        rule_name = match.group(2)
        sections[rule_name] = section_num

    return sections

# Load specification metadata at module import
try:
    SPEC_META = load_spec_sections()
    SPEC_SECTIONS = SPEC_META['sections']
    print(f"✓ Loaded {SPEC_META['spec_file']} (parser {PARSER_VERSION})")
    print(f"  Mapped {len(SPEC_SECTIONS)} section rules")
except Exception as e:
    print(f"✗ ERROR: Failed to load specification metadata")
    print(f"  {e}")
    raise

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

def fetch_kjv_strongs(verse_ref, target_sn):
    """
    Fetch KJV text with Strong's numbers and check if target_sn appears in it.

    Args:
        verse_ref: String like "Gen 12:1"
        target_sn: Strong's number like "03212"

    Returns:
        String indicating KJV usage, or None if fetch fails
    """
    try:
        # Parse verse_ref
        parts = verse_ref.split()
        if len(parts) < 2:
            return None
        book = parts[0]
        chap_verse = parts[1].split(':')
        if len(chap_verse) < 2:
            return None
        chap = chap_verse[0]
        sec = chap_verse[1]

        # Map book name to Chinese abbreviation (FHL API requires chineses param)
        book_map = {
            'Gen': '創', 'Exod': '出', 'Lev': '利', 'Num': '民', 'Deut': '申',
            'Josh': '書', 'Judg': '士', 'Ruth': '得', '1Sam': '撒上', '2Sam': '撒下',
            '1Kgs': '王上', '2Kgs': '王下', '1Chr': '代上', '2Chr': '代下',
            'Ezra': '拉', 'Neh': '尼', 'Esth': '斯', 'Job': '伯', 'Ps': '詩',
            'Prov': '箴', 'Eccl': '傳', 'Song': '歌', 'Isa': '賽', 'Jer': '耶',
            'Lam': '哀', 'Ezek': '結', 'Dan': '但', 'Hos': '何', 'Joel': '珥',
            'Amos': '摩', 'Obad': '俄', 'Jonah': '拿', 'Mic': '彌', 'Nah': '鴻',
            'Hab': '哈', 'Zeph': '番', 'Hag': '該', 'Zech': '亞', 'Mal': '瑪',
            'Matt': '太', 'Mark': '可', 'Luke': '路', 'John': '約', 'Acts': '徒',
            'Rom': '羅', '1Cor': '林前', '2Cor': '林後', 'Gal': '加', 'Eph': '弗',
            'Phil': '腓', 'Col': '西', '1Thess': '帖前', '2Thess': '帖後',
            '1Tim': '提前', '2Tim': '提後', 'Titus': '多', 'Phlm': '門',
            'Heb': '來', 'Jas': '雅', '1Pet': '彼前', '2Pet': '彼後',
            '1John': '約一', '2John': '約二', '3John': '約三', 'Jude': '猶', 'Rev': '啟'
        }

        chineses = book_map.get(book)
        if not chineses:
            return None

        # Construct API URL
        url = f"https://bible.fhl.net/json/qb.php?version=kjv&chineses={urllib.parse.quote(chineses)}&chap={chap}&sec={sec}&strong=1"

        # Fetch with timeout
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data.get('status') != 'success' or not data.get('record'):
            return None

        kjv_text = data['record'][0].get('bible_text', '')

        # Check if target_sn appears in KJV text
        if f"<WH{target_sn}>" in kjv_text or f"<WG{target_sn}>" in kjv_text:
            return f"KJV also uses <{target_sn}>"
        else:
            # Extract all Strong's numbers from KJV text
            kjv_sns = re.findall(r'<W[HG](\d+)>', kjv_text)
            if kjv_sns:
                return f"KJV uses different SN(s): {', '.join(set(kjv_sns[:10]))}"  # Limit to first 10 unique
            else:
                return "KJV has no Strong's numbers"

    except Exception as e:
        return f"KJV fetch failed: {str(e)[:50]}"

def get_qp_info(sn_value, qp_records, verse_ref=None):
    """
    Look up a Strong's number in qp.php records.

    Handles edge case where record['sn'] may be a list instead of string
    (qp.php data type inconsistency). Logs these cases to qp_data_type_errors.txt.
    """
    sn_value_stripped = sn_value.lstrip('0')
    for record in qp_records:
        if 'sn' not in record:
            continue
        sn_field = record['sn']
        # Handle qp.php data type inconsistency: 'sn' may be list instead of string
        if isinstance(sn_field, list):
            # Log this data type error
            if verse_ref:
                error_detail = f"qp.php 'sn' field is list instead of string: {sn_field}"
                append_to_log(QP_DATA_TYPE_ERRORS_LOG, verse_ref, "qp_sn_is_list", error_detail)
            # Try to match against first element if it's a string
            if sn_field and isinstance(sn_field[0], str):
                if sn_field[0].lstrip('0') == sn_value_stripped:
                    return record
            continue
        # Normal case: sn is string
        if sn_field.lstrip('0') == sn_value_stripped:
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

        # Handle qp.php data type inconsistency: 'sn' may be list instead of string
        sn_field = record.get('sn', '')
        if isinstance(sn_field, list):
            record_sn = sn_field[0].lstrip('0') if sn_field and isinstance(sn_field[0], str) else ''
        else:
            record_sn = sn_field.lstrip('0') if isinstance(sn_field, str) else ''
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

def has_pronoun_suffix(sn_value, qp_records, verse_ref=None):
    """
    Check if a Strong's number has a pronoun suffix by examining qp.php wform.

    Implements SPECIFICATION_v1.8.md §3.4 Exception 1.
    Returns True if wform contains pronoun suffix markers like "詞尾".
    """
    qp_info = get_qp_info(sn_value, qp_records, verse_ref)
    if not qp_info or 'wform' not in qp_info:
        return False

    wform = qp_info['wform']
    # Check for pronoun suffix indicators
    # Examples: "介系詞 מִן + 3 單陽詞尾", "受詞記號 + 3 單陽詞尾"
    return '詞尾' in wform

def is_noun(group, qp_records, verse_ref=None):
    if not group or not group.get('_is_group'):
        return False
    core = group['core']
    # Handle compound prepositions where core is a list of SNs
    if isinstance(core, list):
        # For compounds, check the last (main) SN
        core = core[-1] if core else None
    if not core:
        return False
    qp_info = get_qp_info(core, qp_records, verse_ref)
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

def group_and_merge(tokens, qp_records, verse_ref=None):
    # Implements the multi-pass grouping logic from SPECIFICATION_v1.8.md (3.3)

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
            if has_pronoun_suffix(item['value'], qp_records, verse_ref):
                for j in range(i - 1, -1, -1):
                    if items[j].get('_is_group'):
                        items[j]["post_brace"].append(item['value'])
                        is_attached = True
                        break
            else:
                # Exception 2: Object marker normally right-attaches to noun
                for j in range(i + 1, len(items)):
                    if items[j].get('_is_group') and is_noun(items[j], qp_records, verse_ref):
                        items[j]["pre_brace"].append(item['value'])
                        is_attached = True
                        break
        elif item_type == 'brace_prep':
            # Exception 1: If brace prep has pronoun suffix, left-attach to verb
            if has_pronoun_suffix(item['value'], qp_records, verse_ref):
                for j in range(i - 1, -1, -1):
                    if items[j].get('_is_group'):
                        items[j]["post_brace"].append(item['value'])
                        is_attached = True
                        break
            else:
                # General case: Right-attach to next noun
                for j in range(i + 1, len(items)):
                    if items[j].get('_is_group') and is_noun(items[j], qp_records, verse_ref):
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

def extract_word_metadata(group, qp_records, verse_ref=None):
    qp_info = get_qp_info(group['core'], qp_records, verse_ref)
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

def _is_position_consumed(pos, length, consumed_positions):
    """
    Check if a position range overlaps with any consumed range.

    Args:
        pos: Start position of the token
        length: Length of the token
        consumed_positions: Set of (start, end) tuples representing consumed ranges

    Returns:
        bool: True if position overlaps any consumed range, False otherwise

    Examples:
        >>> _is_position_consumed(5, 5, {(0, 8)})
        True  # (5, 10) overlaps (0, 8)
        >>> _is_position_consumed(5, 5, {(10, 15)})
        False  # (5, 10) doesn't overlap (10, 15)
    """
    end_pos = pos + length
    for consumed_start, consumed_end in consumed_positions:
        # Check overlap: [pos, end_pos) overlaps [consumed_start, consumed_end)
        if pos < consumed_end and end_pos > consumed_start:
            return True
    return False

def _find_next_unused_position(text, search_token, consumed_positions, start_from=0):
    """
    Find the next occurrence of search_token that doesn't overlap with consumed positions.

    Args:
        text: Text to search in
        search_token: Token to find
        consumed_positions: Set of (start, end) tuples representing consumed ranges
        start_from: Position to start searching from (default: 0)

    Returns:
        int: Position of next unused occurrence, or -1 if none found

    Examples:
        >>> _find_next_unused_position("AB AB AB", "AB", {(0, 2)}, 0)
        3  # Skips first "AB" at 0, returns second at 3
    """
    pos = start_from
    token_length = len(search_token)

    while True:
        pos = text.find(search_token, pos)
        if pos == -1:
            return -1

        # Check if this position overlaps with any consumed range
        if not _is_position_consumed(pos, token_length, consumed_positions):
            return pos

        # Try next occurrence
        pos += 1

def extract_interleaved_text(group, bible_text_raw, consumed_positions=None):
    """
    Extract original text showing SN-Chinese-SN arrangement when tokens are
    interleaved with Chinese characters.

    Args:
        group: Group dict
        bible_text_raw: Raw UNV+SN source text
        consumed_positions: Set of (start, end) tuples marking already-used positions.
                           Modified in-place when extraction succeeds. If None, creates
                           a new empty set (default behavior for backward compatibility).

    Returns:
        str: Interleaved snippet like "{<0853>}天<08064>" or None if not interleaved
    """
    # Initialize consumed_positions if not provided (backward compatibility)
    if consumed_positions is None:
        consumed_positions = set()
    # Only extract for multi-token groups
    token_count = 0
    tokens_to_find = []

    # Collect prefixes
    if group.get('prefixes'):
        for prefix in group['prefixes']:
            tokens_to_find.append(f"<{prefix}>")
            token_count += 1

    # Collect pre_brace
    if group.get('pre_brace'):
        for code in group['pre_brace']:
            tokens_to_find.append(f"{{<{code}>}}")
            token_count += 1

    # Core token
    if group.get('core'):
        tokens_to_find.append(f"<{group['core']}>")
        token_count += 1

    # post_brace
    if group.get('post_brace'):
        for code in group['post_brace']:
            tokens_to_find.append(f"{{<{code}>}}")
            token_count += 1

    # Need at least 2 tokens for interleaving
    if token_count < 2:
        return None

    # Try to find tokens in raw text
    # We need to detect if Chinese chars exist between tokens
    try:
        # Find all token positions (skip consumed positions)
        positions = []
        for token in tokens_to_find:
            # Search with WH/WAH/WTH prefixes
            if token.startswith('{<'):
                # For braced tokens like {<0853>}
                for prefix_variant in ['{<WH', '{<WAH', '{<WTH']:
                    search_token = token.replace('{<', prefix_variant)
                    pos = _find_next_unused_position(bible_text_raw, search_token, consumed_positions)
                    if pos != -1:
                        positions.append((pos, search_token))
                        break
            else:
                # For regular tokens like <09002>
                for prefix_variant in ['<WAH', '<WTH', '<WAT', '<WH']:
                    search_token = token.replace('<', prefix_variant)
                    pos = _find_next_unused_position(bible_text_raw, search_token, consumed_positions)
                    if pos != -1:
                        positions.append((pos, search_token))
                        break

        if len(positions) < 2:
            return None

        # Sort by position
        positions.sort()

        # Check if there are Chinese characters between first and last token
        first_pos, first_token = positions[0]
        last_pos, last_token = positions[-1]

        # Extract substring between first and last token
        snippet_end = last_pos + len(last_token)
        snippet = bible_text_raw[first_pos:snippet_end]

        # Check if Chinese characters exist in the snippet
        has_chinese = any('\u4e00' <= ch <= '\u9fff' for ch in snippet)

        if not has_chinese:
            return None

        # v1.8.5: Preserve WH/WAH/WTH prefixes in markers for visual consistency
        # (Previous versions stripped these prefixes, causing format mismatch)
        # Return the snippet as-is with original prefixes intact

        # Mark this range as consumed (in-place mutation)
        consumed_positions.add((first_pos, snippet_end))

        return snippet

    except Exception:
        # If extraction fails, return None gracefully
        return None

def determine_spec_rule(group):
    """
    Determine which SPECIFICATION rule created this group.

    Args:
        group: Group dict with keys like 'core', 'prefixes', 'morph', etc.

    Returns:
        str: Section number (e.g., '3.3.1') or None for single-token groups
    """
    # Count distinct tokens (excluding morph which is part of same token)
    token_count = 0
    if group.get('prefixes'):
        token_count += len(group['prefixes'])
    if group.get('pre_brace'):
        token_count += len(group['pre_brace'])
    if group.get('core'):
        token_count += 1
    if group.get('post_brace'):
        token_count += len(group['post_brace'])

    # Single-token groups don't need spec references
    if token_count <= 1 and not group.get('morph'):
        return None

    # Priority order (first match wins)
    if group.get('compound'):
        return SPEC_SECTIONS.get('compound')

    if '0853' in group.get('pre_brace', []):
        return SPEC_SECTIONS.get('object_marker')

    if group.get('post_brace'):
        return SPEC_SECTIONS.get('brace_left')

    if group.get('pre_brace'):
        return SPEC_SECTIONS.get('brace_right')

    if group.get('morph'):
        return SPEC_SECTIONS.get('morph')

    if group.get('prefixes'):
        return SPEC_SECTIONS.get('prefix')

    if group.get('construct_of'):
        return SPEC_SECTIONS.get('construct')

    return None

def format_line_with_annotations(base_line, interleaved_text=None, spec_ref=None, line_width=LINE_WIDTH):
    """
    Format output line with optional interleaved text and spec reference.

    Args:
        base_line: The main formatted line
        interleaved_text: Optional interleaved snippet (e.g., "{<0853>}天<08064>")
        spec_ref: Optional spec section reference (e.g., "3.3.1")
        line_width: Target width for right-alignment (default: 80)

    Returns:
        str: Formatted line with annotations
    """
    parts = [base_line]

    # Add interleaved text with :: delimiters
    if interleaved_text:
        parts.append(f"    ::{interleaved_text}::")

    # Add right-aligned spec reference
    if spec_ref:
        current_length = sum(len(p) for p in parts)
        ref_text = f"[{spec_ref}]"
        padding_needed = line_width - current_length - len(ref_text)

        if padding_needed > 0:
            parts.append(' ' * padding_needed)
        else:
            # Minimum 2-space gap
            parts.append('  ')

        parts.append(ref_text)

    return ''.join(parts)

def extract_complete_tags_mapping(bible_text_raw):
    """
    Extract complete Strong's number tags (with prefixes) from bible_text_raw.

    Args:
        bible_text_raw: Original text with complete tags like <WAH05921>, <WH0430>, <WTH8804>

    Returns:
        dict: Mapping from numeric code to complete tag
              e.g., {'05921': '<WAH05921>', '0430': '<WH0430>', '8804': '<WTH8804>'}
    """
    tag_mapping = {}

    # Pattern to match all Strong's number tags with optional prefixes
    # Matches: <WH0430>, <WAH05921>, <WTH8804>, {<WAH05921>}, etc.
    pattern = r'<(W[ATH]*H?)(\d+)>'

    for match in re.finditer(pattern, bible_text_raw):
        prefix = match.group(1)  # e.g., 'WH', 'WAH', 'WTH'
        numeric_code = match.group(2)  # e.g., '0430', '05921', '8804'
        complete_tag = f'<{prefix}{numeric_code}>'

        # Store mapping (numeric code -> complete tag)
        # Keep the first occurrence if duplicate codes exist
        if numeric_code not in tag_mapping:
            tag_mapping[numeric_code] = complete_tag

    return tag_mapping

def format_groups_to_text(groups, bible_text_raw, qp_records, verse_ref=None):
    output_lines = [f"Parsed and Formatted Text Section (SPECIFICATION_{PARSER_VERSION}):"]
    morphology_notes_index = {}
    morphology_notes_entries = []
    morph_ref_counter = 1
    uncertainty_notes = []
    notable_issues = []

    # Extract complete Strong's number tags from bible_text_raw
    tag_mapping = extract_complete_tags_mapping(bible_text_raw)

    # Track consumed positions across all groups for interleaved text extraction
    consumed_positions = set()

    for group in groups:
        # v1.7: Handle compound prepositions
        if group.get('compound'):
            # This is a compound preposition
            components = group['core']
            core_display = ''.join(tag_mapping.get(code, f"<{code}>") for code in components)
            word_type_pos = "複合介系詞"
            chinese_meaning = group['compound_meaning']
            wform = group['compound_structure']

            # Add structure note
            structure_note = f"[註]: {group['compound_structure']}"

            prefix_display = ''.join(tag_mapping.get(code, f"<{code}>") for code in group.get('prefixes', []))
            pre_brace_display = ''.join(tag_mapping.get(code, f"<{code}>") for code in group.get('pre_brace', []))
            post_brace_display = ''.join(tag_mapping.get(code, f"<{code}>") for code in group.get('post_brace', []))

            morph_codes = group.get('morph', [])
            morph_display = ''.join(f"({code})" for code in morph_codes)
            morph_ref = ""

            formatted_line = f"{prefix_display}{pre_brace_display}{core_display}{morph_display}{post_brace_display} — {word_type_pos} {group['compound_hebrew']}「{chinese_meaning}」{morph_ref}".rstrip()

            # Add spec reference and interleaved text
            spec_rule = determine_spec_rule(group)
            interleaved = extract_interleaved_text(group, bible_text_raw, consumed_positions)
            formatted_line = format_line_with_annotations(formatted_line, interleaved, spec_rule)

            output_lines.append(formatted_line)
            output_lines.append(structure_note)
            continue

        # Regular processing
        qp_info, word_type_pos, chinese_meaning, wform = extract_word_metadata(group, qp_records, verse_ref)

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
                # Do NOT add to uncertainty_notes or QB_QP_MISMATCH_LOG
            elif verse_ref:
                # Regular qb_qp_mismatch - fetch KJV for comparison and log to dedicated file
                kjv_info = fetch_kjv_strongs(verse_ref, group['core'])
                if kjv_info:
                    note_with_kjv = f"{note} | {kjv_info}"
                else:
                    note_with_kjv = note
                uncertainty_notes.append(note)
                # Log to dedicated qb_qp_mismatch file
                append_to_log(QB_QP_MISMATCH_LOG, verse_ref, "qb_qp_mismatch", note_with_kjv)
            else:
                # No verse_ref (shouldn't happen in practice)
                uncertainty_notes.append(note)

        prefix_display = ''.join(tag_mapping.get(code, f"<{code}>") for code in group.get('prefixes', []))
        pre_brace_display = ''.join(f"{{{tag_mapping.get(code, f'<{code}>')}}}" for code in group.get('pre_brace', []))
        post_brace_display = ''.join(f"{{{tag_mapping.get(code, f'<{code}>')}}}" for code in group.get('post_brace', []))
        core_display = tag_mapping.get(group['core'], f"<{group['core']}>")

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

        # Add spec reference and interleaved text
        spec_rule = determine_spec_rule(group)
        interleaved = extract_interleaved_text(group, bible_text_raw, consumed_positions)
        formatted_line = format_line_with_annotations(formatted_line, interleaved, spec_rule)

        output_lines.append(formatted_line)

        for warning in group.get('warnings', []):
            warning_message = render_warning_message(group, warning)
            if warning_message not in uncertainty_notes:
                uncertainty_notes.append(warning_message)
                # Log warnings to appropriate file
                if verse_ref:
                    # Dangling 900x prefixes go to dedicated log (translation artifact, not parser error)
                    if warning == "dangling_p900x":
                        append_to_log(DANGLING_PREFIXES_LOG, verse_ref, warning, warning_message)
                    # Dangling brace prepositions go to dedicated log (similar to dangling_p900x)
                    elif warning == "dangling_brace_prep":
                        append_to_log(DANGLING_BRACE_PREPS_LOG, verse_ref, warning, warning_message)
                    # Dangling object markers go to dedicated log (similar to dangling_brace_prep)
                    elif warning == "dangling_object_marker":
                        append_to_log(DANGLING_OBJECT_MARKERS_LOG, verse_ref, warning, warning_message)
                    # Other "dangling_*" and "brace_attach_ambiguous" warnings are uncertain
                    elif any(w in warning for w in ["dangling", "ambiguous"]):
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

    # Handle empty record from FHL API (verse not found in database)
    if not qb_data.get('record'):
        error_msg = f"qb.php returned empty record (verse not found in FHL UNV database)"
        if verse_ref:
            append_to_log(QP_DATA_TYPE_ERRORS_LOG, verse_ref, "qb_empty_record", error_msg)
        raise ValueError(error_msg)

    bible_text_raw = qb_data['record'][0]['bible_text']
    qp_records = qp_data['record']

    tokens = tokenize_and_classify(bible_text_raw)
    groups = group_and_merge(tokens, qp_records, verse_ref)

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
