#!/usr/bin/env python3
"""
generate_manifest.py
Generate manifest.json from output/ directory structure
"""

import os
import json
import sys
from datetime import datetime

# Add repo root to path for shared imports
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.data.book_data_loader import load_books

OUTPUT_DIR = 'output'
MANIFEST_PATH = os.path.join(OUTPUT_DIR, 'manifest.json')

BOOK_ORDER = load_books()["BOOK_ORDER"]


def generate_manifest():
    """Generate manifest.json from output/ directory structure"""
    manifest = {
        'generated': datetime.utcnow().isoformat() + 'Z',
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
            uncertain = []

            # Get all verse files
            for filename in os.listdir(chap_path):
                file_path = os.path.join(chap_path, filename)
                if not os.path.isfile(file_path):
                    continue

                if filename.endswith('_uncertain'):
                    # Extract verse number from filename like "5_uncertain"
                    try:
                        sec_num = int(filename.replace('_uncertain', ''))
                        uncertain.append(sec_num)
                        if sec_num not in verses:
                            verses.append(sec_num)
                    except ValueError:
                        pass
                elif filename.isdigit():
                    # Regular verse file
                    try:
                        verses.append(int(filename))
                    except ValueError:
                        pass

            if verses:
                manifest['books'][book]['chapters'][str(chap)] = {
                    'verses': sorted(verses),
                    'uncertain': sorted(uncertain)
                }

    # Write manifest
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"Generated {MANIFEST_PATH}")
    print(f"Books: {len(manifest['books'])}")

    total_verses = 0
    total_uncertain = 0
    for book, book_data in manifest['books'].items():
        for chap, chap_data in book_data['chapters'].items():
            total_verses += len(chap_data['verses'])
            total_uncertain += len(chap_data['uncertain'])

    print(f"Total verses: {total_verses}")
    print(f"Uncertain verses: {total_uncertain}")

    # Print book summary
    print("\nBook Summary:")
    for book in BOOK_ORDER:
        if book in manifest['books']:
            chapters = list(manifest['books'][book]['chapters'].keys())
            print(f"  {book}: {len(chapters)} chapters")


if __name__ == '__main__':
    generate_manifest()
