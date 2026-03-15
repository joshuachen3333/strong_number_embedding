#!/usr/bin/env python3
"""
generate_data_bundle.py
Generate data_bundle.json for showoff_finished_4review viewer.

Reads per-version/model manifests and verse JSONs, outputs a combined bundle:
{
  "versions": {
    "lcc": {
      "models": {
        "sonnet": { "manifest": {...}, "verses": {"Gen/1": [...], ...} },
        "gemini-3-flash-preview": { ... }
      }
    },
    "rcuv2010": { ... }
  }
}

Usage:
    python3 generate_data_bundle.py                              # all versions, all models
    python3 generate_data_bundle.py --version lcc                # single version
    python3 generate_data_bundle.py --model sonnet               # single model (all versions)
    python3 generate_data_bundle.py --version lcc --model sonnet # specific combo
    python3 generate_data_bundle.py -o custom.json               # custom output path
"""

import os
import json
import sys
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPT_DIR)

OUTPUT_DIR = os.path.join(_REPO_ROOT, 'output')
DEFAULT_BUNDLE_PATH = os.path.join(_REPO_ROOT, 'showoff_finished_4review', 'data_bundle.json')


def bundle_model(model_dir):
    """Read manifest and all verse JSONs for a model. Returns (manifest, verses_dict, total)."""
    manifest_path = os.path.join(model_dir, 'manifest.json')
    if not os.path.isfile(manifest_path):
        print(f"  Warning: No manifest.json in {model_dir}, skipping")
        return None, None, 0

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    verses = {}
    total = 0

    for book, book_data in manifest.get('books', {}).items():
        for chap, chap_data in book_data.get('chapters', {}).items():
            key = f"{book}/{chap}"
            chapter_verses = []

            for sec in chap_data.get('verses', []):
                verse_path = os.path.join(model_dir, book, chap, f"{sec}.json")
                try:
                    with open(verse_path, 'r', encoding='utf-8') as f:
                        verse = json.load(f)
                    chapter_verses.append(verse)
                    total += 1
                except (json.JSONDecodeError, IOError) as e:
                    print(f"  Warning: Error reading {verse_path}: {e}")

            if chapter_verses:
                chapter_verses.sort(key=lambda v: v.get('sec', 0))
                verses[key] = chapter_verses

    return manifest, verses, total


def generate_bundle(version_filter=None, model_filter=None, output_path=None):
    """Generate the combined data bundle."""
    if output_path is None:
        output_path = DEFAULT_BUNDLE_PATH

    if not os.path.exists(OUTPUT_DIR):
        print(f"Error: {OUTPUT_DIR} directory not found")
        sys.exit(1)

    bundle = {"versions": {}}

    # Detect versions (subdirs of output/)
    versions = []
    for item in sorted(os.listdir(OUTPUT_DIR)):
        item_path = os.path.join(OUTPUT_DIR, item)
        if os.path.isdir(item_path):
            if version_filter and item != version_filter:
                continue
            versions.append(item)

    if not versions:
        print("No version directories found in output/")
        sys.exit(1)

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

        version_data = {"models": {}}
        for model in models:
            model_dir = os.path.join(version_dir, model)
            print(f"\n[{version}/{model}]")
            manifest, verses, total = bundle_model(model_dir)
            if manifest is None:
                continue
            version_data["models"][model] = {
                "manifest": manifest,
                "verses": verses
            }
            print(f"  {len(manifest.get('books', {}))} books, {total} verses bundled")

        if version_data["models"]:
            bundle["versions"][version] = version_data

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, ensure_ascii=False, indent=None)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n-> {output_path} ({size_mb:.1f} MB)")
    for ver, vdata in bundle['versions'].items():
        models_str = ', '.join(vdata['models'].keys())
        print(f"  {ver}: [{models_str}]")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate data_bundle.json for showoff viewer")
    parser.add_argument('--version', default=None,
                        help="Bundle a single version (default: all)")
    parser.add_argument('--model', default=None,
                        help="Bundle a single model (default: all)")
    parser.add_argument('-o', '--output', default=None,
                        help=f"Output path (default: {DEFAULT_BUNDLE_PATH})")
    args = parser.parse_args()
    generate_bundle(version_filter=args.version, model_filter=args.model,
                    output_path=args.output)
