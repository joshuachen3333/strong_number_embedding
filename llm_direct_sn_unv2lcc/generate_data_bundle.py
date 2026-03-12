#!/usr/bin/env python3
"""
generate_data_bundle.py
Generate data_bundle.json for showoff_finished_4review viewer.

Reads per-brand manifests and verse JSONs, outputs a combined bundle:
{
  "brands": {
    "claude": { "manifest": {...}, "verses": {"Gen/1": [...], ...} },
    "gemini": { ... },
    ...
  }
}

Usage:
    python generate_data_bundle.py                    # all brands
    python generate_data_bundle.py --brand claude     # single brand
    python generate_data_bundle.py -o custom.json     # custom output path
"""

import os
import json
import sys
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)

OUTPUT_DIR = os.path.join(_SCRIPT_DIR, 'output')
DEFAULT_BUNDLE_PATH = os.path.join(_REPO_ROOT, 'showoff_finished_4review', 'data_bundle.json')
KNOWN_BRANDS = ['claude', 'codex', 'gemini']


def bundle_brand(brand_dir):
    """Read manifest and all verse JSONs for a brand. Returns (manifest, verses_dict)."""
    manifest_path = os.path.join(brand_dir, 'manifest.json')
    if not os.path.isfile(manifest_path):
        print(f"  ⚠ No manifest.json in {brand_dir}, skipping")
        return None, None

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    verses = {}
    total = 0

    for book, book_data in manifest.get('books', {}).items():
        for chap, chap_data in book_data.get('chapters', {}).items():
            key = f"{book}/{chap}"
            chapter_verses = []

            for sec in chap_data.get('verses', []):
                verse_path = os.path.join(brand_dir, book, chap, f"{sec}.json")
                try:
                    with open(verse_path, 'r', encoding='utf-8') as f:
                        verse = json.load(f)
                    chapter_verses.append(verse)
                    total += 1
                except (json.JSONDecodeError, IOError) as e:
                    print(f"  ⚠ Error reading {verse_path}: {e}")

            if chapter_verses:
                # Sort by verse number
                chapter_verses.sort(key=lambda v: v.get('sec', 0))
                verses[key] = chapter_verses

    return manifest, verses, total


def generate_bundle(brand_filter=None, output_path=None):
    """Generate the combined data bundle."""
    if output_path is None:
        output_path = DEFAULT_BUNDLE_PATH

    if not os.path.exists(OUTPUT_DIR):
        print(f"Error: {OUTPUT_DIR} directory not found")
        sys.exit(1)

    bundle = {"brands": {}}

    # Detect brands
    brands = []
    for item in sorted(os.listdir(OUTPUT_DIR)):
        item_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(item_path) and item in KNOWN_BRANDS:
            if brand_filter and item != brand_filter:
                continue
            brands.append(item)

    if not brands:
        print("No brand directories found in output/")
        sys.exit(1)

    for brand in brands:
        brand_dir = os.path.join(OUTPUT_DIR, brand)
        print(f"\n[{brand}]")
        result = bundle_brand(brand_dir)
        if result[0] is None:
            continue
        manifest, verses, total = result
        bundle["brands"][brand] = {
            "manifest": manifest,
            "verses": verses
        }
        print(f"  {len(manifest.get('books', {}))} books, {total} verses bundled")

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, indent=None)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n→ {output_path} ({size_mb:.1f} MB)")
    print(f"  Brands: {', '.join(bundle['brands'].keys())}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate data_bundle.json for showoff viewer")
    parser.add_argument('--brand', choices=KNOWN_BRANDS, default=None,
                        help="Bundle a single brand (default: all)")
    parser.add_argument('-o', '--output', default=None,
                        help=f"Output path (default: {DEFAULT_BUNDLE_PATH})")
    args = parser.parse_args()
    generate_bundle(brand_filter=args.brand, output_path=args.output)
