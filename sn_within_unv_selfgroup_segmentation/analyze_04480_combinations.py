#!/usr/bin/env python3
"""
Analyze <04480> (מִן) compound preposition combinations in parsed verses.
Find what Strong's numbers appear after <04480> in qb.php data.
"""

import re
import json
import subprocess
from collections import Counter

def get_verse_refs_with_04480():
    """Extract verse references that have 04480 mismatch issues."""
    # v1.8.1: qb_qp_mismatch entries now in dedicated log file
    with open('output/strong_number_from_qb.php_not_found_in_qp.php.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    verse_refs = []
    for line in lines:
        if 'qb_qp_mismatch' in line and '04480' in line:
            # Parse: [timestamp] Gen 1:7 | qb_qp_mismatch | ...
            match = re.search(r'\] ([A-Za-z0-9]+) (\d+):(\d+) \|', line)
            if match:
                book, chap, verse = match.groups()
                verse_refs.append((book, chap, verse))

    return list(set(verse_refs))  # Remove duplicates

def fetch_verse_data(book, chap, verse):
    """Fetch qb.php data for a specific verse."""
    try:
        result = subprocess.run(
            ['./fetch_text.sh', '--engs', book, '--chap', chap, '--sec', verse],
            capture_output=True, text=True, check=True, timeout=10
        )
        output = result.stdout

        # Extract qb.php JSON
        qb_start = output.find('=== qb.php')
        qp_start = output.find('=== qp.php')

        if qb_start == -1 or qp_start == -1:
            return None

        qb_json_str = output[qb_start:qp_start].strip()
        qb_json_start = qb_json_str.find('{')
        qb_json_end = qb_json_str.rfind('}') + 1
        qb_json_str = qb_json_str[qb_json_start:qb_json_end]

        qb_data = json.loads(qb_json_str)
        bible_text = qb_data['record'][0]['bible_text']

        return bible_text
    except Exception as e:
        print(f"Error fetching {book} {chap}:{verse}: {e}")
        return None

def analyze_04480_patterns(bible_text):
    """Find what Strong's numbers appear after <04480> in the text."""
    # Pattern: <WAH04480> or <WH04480> followed by <WH####> or <WAH####>
    patterns = []

    # Find all occurrences of 04480 and the next Strong's number
    text = bible_text
    pos = 0
    while True:
        # Find next <W*H04480>
        match = re.search(r'<W[AH]*H04480>', text[pos:])
        if not match:
            break

        start_pos = pos + match.end()

        # Find the next Strong's number after 04480
        next_match = re.search(r'<W[AH]*H(\d{4,5})>', text[start_pos:])
        if next_match:
            next_strong = next_match.group(1)
            patterns.append(next_strong)

        pos = start_pos + 1

    return patterns

def main():
    print("Analyzing <04480> compound preposition patterns...")
    print("=" * 60)

    verse_refs = get_verse_refs_with_04480()
    print(f"Found {len(verse_refs)} verses with <04480> issues\n")

    # Sample first 100 verses to avoid overwhelming the API
    sample_size = min(100, len(verse_refs))
    print(f"Sampling {sample_size} verses...\n")

    combination_counter = Counter()

    for i, (book, chap, verse) in enumerate(verse_refs[:sample_size]):
        if i % 10 == 0:
            print(f"Progress: {i}/{sample_size}")

        bible_text = fetch_verse_data(book, chap, verse)
        if bible_text:
            patterns = analyze_04480_patterns(bible_text)
            for pattern in patterns:
                combination_counter[pattern] += 1

    print("\n" + "=" * 60)
    print("RESULTS: Strong's numbers that follow <04480> (מִן)\n")

    for strong_num, count in combination_counter.most_common():
        print(f"<04480><{strong_num}>: {count} occurrences")

    print("\n" + "=" * 60)
    print(f"Total unique combinations: {len(combination_counter)}")
    print(f"Total occurrences analyzed: {sum(combination_counter.values())}")

if __name__ == '__main__':
    main()
