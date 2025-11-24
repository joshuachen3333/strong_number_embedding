#!/usr/bin/env python3
"""
Identify compound prepositions with מִן (04480).
Parse qp.php data to find which Strong's numbers are combined with מִן.
"""

import re
import json
import subprocess
from collections import Counter, defaultdict

def get_verse_refs_with_04480():
    """Extract verse references that have 04480 mismatch issues."""
    # v1.8.1: qb_qp_mismatch entries now in dedicated log file
    with open('output/strong_number_from_qb.php_not_found_in_qp.php.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    verse_refs = []
    for line in lines:
        if 'qb_qp_mismatch' in line and '04480' in line:
            match = re.search(r'\] ([A-Za-z0-9]+) (\d+):(\d+) \|', line)
            if match:
                book, chap, verse = match.groups()
                verse_refs.append((book, chap, verse))

    return list(set(verse_refs))  # Remove duplicates

def fetch_and_parse_qp_data(book, chap, verse):
    """Fetch qp.php data and identify compound prepositions."""
    try:
        result = subprocess.run(
            ['./fetch_text.sh', '--engs', book, '--chap', chap, '--sec', verse],
            capture_output=True, text=True, check=True, timeout=10
        )
        output = result.stdout

        # Extract qp.php JSON
        qp_start = output.find('=== qp.php')
        if qp_start == -1:
            return []

        qp_json_str = output[qp_start:].strip()
        qp_json_start = qp_json_str.find('{')
        qp_json_end = qp_json_str.rfind('}') + 1
        qp_json_str = qp_json_str[qp_json_start:qp_json_end]

        qp_data = json.loads(qp_json_str)

        compounds = []
        for record in qp_data['record']:
            if 'wform' in record and 'מִן' in record.get('wform', ''):
                # This is a compound preposition with מִן
                sn = record.get('sn', '')
                wform = record.get('wform', '')
                word = record.get('word', '')
                exp = record.get('exp', '')

                compounds.append({
                    'verse': f"{book} {chap}:{verse}",
                    'word': word,
                    'sn': sn,
                    'wform': wform,
                    'meaning': exp
                })

        return compounds

    except Exception as e:
        return []

def main():
    print("Identifying compound prepositions with מִן (04480)...")
    print("=" * 80)

    verse_refs = get_verse_refs_with_04480()
    print(f"Found {len(verse_refs)} verses with <04480> issues\n")

    # Sample verses
    sample_size = min(150, len(verse_refs))
    print(f"Sampling {sample_size} verses...\n")

    all_compounds = []
    sn_counter = Counter()
    sn_examples = defaultdict(list)

    for i, (book, chap, verse) in enumerate(verse_refs[:sample_size]):
        if i % 20 == 0:
            print(f"Progress: {i}/{sample_size}")

        compounds = fetch_and_parse_qp_data(book, chap, verse)
        for comp in compounds:
            all_compounds.append(comp)
            sn = comp['sn']
            sn_counter[sn] += 1
            if len(sn_examples[sn]) < 3:  # Keep up to 3 examples per SN
                sn_examples[sn].append(comp)

    print("\n" + "=" * 80)
    print("COMPOUND PREPOSITIONS WITH מִן (04480)\n")
    print("Format: <04480> + <XXXX> = Hebrew compound\n")
    print("-" * 80)

    # Sort by frequency
    for sn, count in sn_counter.most_common():
        if not sn:
            continue

        print(f"\n<04480> + <{sn}>: {count} occurrences")

        # Show examples
        for example in sn_examples[sn][:2]:
            print(f"  Hebrew: {example['word']}")
            print(f"  Structure: {example['wform']}")
            print(f"  Meaning: {example['meaning']}")
            print(f"  Example: {example['verse']}")
            if len(sn_examples[sn]) > 1:
                print()

    print("\n" + "=" * 80)
    print("SUMMARY\n")
    print(f"Total unique Strong's numbers combined with מִן: {len(sn_counter)}")
    print(f"Total compound prepositions found: {len(all_compounds)}")

    # Filter for true prepositions (those with "介系詞" in wform)
    true_preps = [c for c in all_compounds if '介系詞' in c['wform'] and '+' in c['wform']]
    true_prep_sns = set(c['sn'] for c in true_preps)

    print(f"\nTrue compound prepositions (containing '介系詞 מִן + 介系詞'): {len(true_prep_sns)}")
    print("Strong's numbers:", sorted(true_prep_sns))

if __name__ == '__main__':
    main()
