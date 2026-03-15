#!/usr/bin/env python3
"""
generate_manifest.py
Generate per-version/model manifest.json from output/{version}/{model}/ directory structure.

Scans output/{version}/{model}/{Book}/{Chapter}/{verse}.json files, reads confidence from each,
and builds a manifest with verse lists and low-confidence classifications.

Usage:
    python3 generate_manifest.py                          # all versions, all models
    python3 generate_manifest.py --version lcc             # single version
    python3 generate_manifest.py --model sonnet            # single model (all versions)
    python3 generate_manifest.py --version lcc --model sonnet  # specific combo
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

BOOK_ORDER = load_books()["BOOK_ORDER"]


def generate_manifest_for_model(model_dir, model_name):
    """Generate manifest dict for a single model directory."""
    manifest = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'books': {}
    }

    for book in BOOK_ORDER:
        book_path = os.path.join(model_dir, book)
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


def print_summary(version, model_name, manifest):
    """Print summary for a version/model's manifest."""
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


def generate_manifests(version_filter=None, model_filter=None):
    """Generate manifest.json for each version/model under output/."""
    if not os.path.exists(OUTPUT_DIR):
        print(f"Error: {OUTPUT_DIR} directory not found")
        return

    # Detect versions (subdirs of output/)
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

        # Detect models under this version (all subdirs)
        models = []
        for item in sorted(os.listdir(version_dir)):
            item_path = os.path.join(version_dir, item)
            if os.path.isdir(item_path):
                if model_filter and item != model_filter:
                    continue
                models.append(item)

        if not models:
            continue

        for model in models:
            model_dir = os.path.join(version_dir, model)
            manifest = generate_manifest_for_model(model_dir, model)

            manifest_path = os.path.join(model_dir, 'manifest.json')
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)

            print(f"\n[{version}/{model}] -> {manifest_path}")
            print_summary(version, model, manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate per-version/model manifest.json")
    parser.add_argument('--version', default=None,
                        help="Generate for a single version (default: all)")
    parser.add_argument('--model', default=None,
                        help="Generate for a single model (default: all)")
    args = parser.parse_args()
    generate_manifests(version_filter=args.version, model_filter=args.model)
