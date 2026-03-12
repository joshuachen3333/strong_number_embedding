#!/usr/bin/env python3
"""
generate_manifest.py
Generate per-version/brand manifest.json from output/{version}/{brand}/ directory structure.

Scans output/{version}/{brand}/{Book}/{Chapter}/{verse}.json files, reads confidence from each,
and builds a manifest with verse lists and low-confidence classifications.

Usage:
    python generate_manifest.py                          # all versions, all brands
    python generate_manifest.py --version lcc             # single version
    python generate_manifest.py --brand claude            # single brand (all versions)
    python generate_manifest.py --version lcc --brand claude  # specific combo
"""

import os
import json
import sys
import argparse
from datetime import datetime, timezone

# Add repo root to path for shared imports
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from shared.data.book_data_loader import load_books

OUTPUT_DIR = os.path.join(_REPO_ROOT, 'output')
LOW_CONFIDENCE_THRESHOLD = 0.85
KNOWN_BRANDS = ['claude', 'codex', 'gemini']

BOOK_ORDER = load_books()["BOOK_ORDER"]


def generate_manifest_for_brand(brand_dir, brand_name):
    """Generate manifest dict for a single brand directory."""
    manifest = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'books': {}
    }

    for book in BOOK_ORDER:
        book_path = os.path.join(brand_dir, book)
        if not os.path.isdir(book_path):
            continue

        manifest['books'][book] = {'chapters': {}}

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

            for filename in os.listdir(chap_path):
                if not filename.endswith('.json'):
                    continue

                verse_num_str = filename[:-5]
                if not verse_num_str.isdigit():
                    continue

                verse_num = int(verse_num_str)
                verses.append(verse_num)

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

    return manifest


def print_summary(version, brand_name, manifest):
    """Print summary for a version/brand's manifest."""
    total_verses = 0
    total_low = 0
    for book_data in manifest['books'].values():
        for chap_data in book_data['chapters'].values():
            total_verses += len(chap_data['verses'])
            total_low += len(chap_data['low_confidence'])

    print(f"  Books: {len(manifest['books'])}, "
          f"Verses: {total_verses}, "
          f"Low confidence: {total_low}")

    for book in BOOK_ORDER:
        if book in manifest['books']:
            chapters = manifest['books'][book]['chapters']
            vc = sum(len(c['verses']) for c in chapters.values())
            lc = sum(len(c['low_confidence']) for c in chapters.values())
            low_str = f" ({lc} low)" if lc else ""
            print(f"    {book}: {len(chapters)} ch, {vc} verses{low_str}")


def generate_manifests(version_filter=None, brand_filter=None):
    """Generate manifest.json for each version/brand under output/."""
    if not os.path.exists(OUTPUT_DIR):
        print(f"Error: {OUTPUT_DIR} directory not found")
        return

    # Detect versions (subdirs of output/ that are NOT known brands — versions are like lcc, rcuv2010, etc.)
    versions = []
    for item in sorted(os.listdir(OUTPUT_DIR)):
        item_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(item_path) and item not in BOOK_ORDER:
            if version_filter and item != version_filter:
                continue
            versions.append(item)

    if not versions:
        print("No version directories found in output/")
        return

    for version in versions:
        version_dir = os.path.join(OUTPUT_DIR, version)

        # Detect brands under this version
        brands = []
        for item in sorted(os.listdir(version_dir)):
            item_path = os.path.join(version_dir, item)
            if os.path.isdir(item_path) and item in KNOWN_BRANDS:
                if brand_filter and item != brand_filter:
                    continue
                brands.append(item)

        if not brands:
            continue

        for brand in brands:
            brand_dir = os.path.join(version_dir, brand)
            manifest = generate_manifest_for_brand(brand_dir, brand)

            manifest_path = os.path.join(brand_dir, 'manifest.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            print(f"\n[{version}/{brand}] -> {manifest_path}")
            print_summary(version, brand, manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate per-version/brand manifest.json")
    parser.add_argument('--version', default=None,
                        help="Generate for a single version (default: all)")
    parser.add_argument('--brand', choices=KNOWN_BRANDS, default=None,
                        help="Generate for a single brand (default: all)")
    args = parser.parse_args()
    generate_manifests(version_filter=args.version, brand_filter=args.brand)
