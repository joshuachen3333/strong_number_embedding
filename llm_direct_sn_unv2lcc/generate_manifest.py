#!/usr/bin/env python3
"""
generate_manifest.py
Generate manifest.json from llm_direct_sn_unv2lcc output/ directory structure.

Scans output/{Book}/{Chapter}/{verse}.json files, reads confidence from each,
and builds a manifest with verse lists and low-confidence classifications.
"""

import os
import json
import sys
from datetime import datetime, timezone

# Add repo root to path for shared imports
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.data.book_data_loader import load_books

OUTPUT_DIR = 'output'
MANIFEST_PATH = os.path.join(OUTPUT_DIR, 'manifest.json')
LOW_CONFIDENCE_THRESHOLD = 0.85

BOOK_ORDER = load_books()["BOOK_ORDER"]


def generate_manifest():
    """Generate manifest.json from output/ directory structure"""
    manifest = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'books': {}
    }

    if not os.path.exists(OUTPUT_DIR):
        print(f"Error: {OUTPUT_DIR} directory not found")
        return

    for book in BOOK_ORDER:
        book_path = os.path.join(OUTPUT_DIR, book)
        if not os.path.isdir(book_path):
            continue

        manifest['books'][book] = {'chapters': {}}

        # Get all chapter directories
        chapters = []
        for item in os.listdir(book_path):
            item_path = os.path.join(book_path, item)
            if os.path.isdir(item_path) and item.isdigit():
                chapters.append(int(item))

        chapters.sort()

        for chap in chapters:
            chap_path = os.path.join(book_path, str(chap))
            if not os.path.isdir(chap_path):
                continue

            verses = []
            low_confidence = []

            # Get all verse JSON files
            for filename in os.listdir(chap_path):
                if not filename.endswith('.json'):
                    continue

                verse_num_str = filename[:-5]  # strip .json
                if not verse_num_str.isdigit():
                    continue

                verse_num = int(verse_num_str)
                verses.append(verse_num)

                # Read confidence from JSON
                file_path = os.path.join(chap_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    confidence = data.get('confidence', 0.0)
                    if confidence < LOW_CONFIDENCE_THRESHOLD:
                        low_confidence.append(verse_num)
                except (json.JSONDecodeError, IOError):
                    low_confidence.append(verse_num)

            if verses:
                manifest['books'][book]['chapters'][str(chap)] = {
                    'verses': sorted(verses),
                    'low_confidence': sorted(low_confidence)
                }

    # Write manifest
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"Generated {MANIFEST_PATH}")
    print(f"Books: {len(manifest['books'])}")

    total_verses = 0
    total_low_confidence = 0
    for book, book_data in manifest['books'].items():
        for chap, chap_data in book_data['chapters'].items():
            total_verses += len(chap_data['verses'])
            total_low_confidence += len(chap_data['low_confidence'])

    print(f"Total verses: {total_verses}")
    print(f"Low confidence (<{LOW_CONFIDENCE_THRESHOLD}): {total_low_confidence}")

    # Print book summary
    print("\nBook Summary:")
    for book in BOOK_ORDER:
        if book in manifest['books']:
            chapters = manifest['books'][book]['chapters']
            verse_count = sum(len(c['verses']) for c in chapters.values())
            low_count = sum(len(c['low_confidence']) for c in chapters.values())
            low_str = f" ({low_count} low confidence)" if low_count else ""
            print(f"  {book}: {len(chapters)} chapters, {verse_count} verses{low_str}")


if __name__ == '__main__':
    generate_manifest()
