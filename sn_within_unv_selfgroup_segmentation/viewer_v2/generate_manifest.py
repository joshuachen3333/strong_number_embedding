#!/usr/bin/env python3
"""
generate_manifest.py
Generate manifest.json from output/ directory structure
"""

import os
import json
from datetime import datetime

OUTPUT_DIR = 'output'
MANIFEST_PATH = os.path.join(OUTPUT_DIR, 'manifest.json')

# List of all 66 books in order
BOOK_ORDER = [
    'Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', 'Ruth',
    '1Sam', '2Sam', '1Kgs', '2Kgs', '1Chr', '2Chr', 'Ezra', 'Neh',
    'Esth', 'Job', 'Ps', 'Prov', 'Eccl', 'Song', 'Isa', 'Jer',
    'Lam', 'Ezek', 'Dan', 'Hos', 'Joel', 'Amos', 'Obad', 'Jonah',
    'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
    'Matt', 'Mark', 'Luke', 'John', 'Acts', 'Rom', '1Cor', '2Cor',
    'Gal', 'Eph', 'Phil', 'Col', '1Thess', '2Thess', '1Tim', '2Tim',
    'Titus', 'Phlm', 'Heb', 'Jas', '1Pet', '2Pet', '1John', '2John',
    '3John', 'Jude', 'Rev'
]


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

        for chapter in chapters:
            chapter_path = os.path.join(book_path, str(chapter))
            if not os.path.isdir(chapter_path):
                continue

            verses = []
            uncertain = []

            # Get all verse files
            for filename in os.listdir(chapter_path):
                file_path = os.path.join(chapter_path, filename)
                if not os.path.isfile(file_path):
                    continue

                if filename.endswith('_uncertain'):
                    # Extract verse number from filename like "5_uncertain"
                    try:
                        verse_num = int(filename.replace('_uncertain', ''))
                        uncertain.append(verse_num)
                        if verse_num not in verses:
                            verses.append(verse_num)
                    except ValueError:
                        pass
                elif filename.isdigit():
                    # Regular verse file
                    try:
                        verses.append(int(filename))
                    except ValueError:
                        pass

            if verses:
                manifest['books'][book]['chapters'][str(chapter)] = {
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
        for chapter, chapter_data in book_data['chapters'].items():
            total_verses += len(chapter_data['verses'])
            total_uncertain += len(chapter_data['uncertain'])

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
