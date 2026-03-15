#!/usr/bin/env python3
"""
One-time migration: Rename output/{version}/{brand}/ to output/{version}/{model}/

Reads the "model" field from each verse JSON to determine the correct model directory.
Falls back to brand name if no model field exists.

Usage:
    python3 migrate_output_brand_to_model.py          # dry run (default)
    python3 migrate_output_brand_to_model.py --apply   # actually move files
"""

import os
import json
import shutil
import argparse

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")


def sanitize_model(model: str) -> str:
    return model.replace(":", "_")


def migrate(dry_run=True):
    if not os.path.isdir(OUTPUT_DIR):
        print(f"No output/ directory found at {OUTPUT_DIR}")
        return

    moves = {}  # (src, dest) pairs
    errors = []

    for version in sorted(os.listdir(OUTPUT_DIR)):
        version_dir = os.path.join(OUTPUT_DIR, version)
        if not os.path.isdir(version_dir):
            continue

        for brand_or_model in sorted(os.listdir(version_dir)):
            subdir = os.path.join(version_dir, brand_or_model)
            if not os.path.isdir(subdir):
                continue

            # Walk all JSON files to detect models
            model_set = set()
            json_count = 0
            for root, dirs, files in os.walk(subdir):
                for f in files:
                    if not f.endswith(".json") or f == "manifest.json":
                        continue
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", encoding="utf-8") as fh:
                            data = json.load(fh)
                        model = data.get("model", "")
                        if model:
                            model_set.add(model)
                        json_count += 1
                    except (json.JSONDecodeError, IOError):
                        pass

            if not model_set:
                # No model field — use brand_or_model as-is (already a model name or unknown)
                print(f"  [{version}/{brand_or_model}] {json_count} files, no model field — keeping as-is")
                continue

            if len(model_set) == 1:
                model = model_set.pop()
                sanitized = sanitize_model(model)
                dest_dir = os.path.join(version_dir, sanitized)

                if subdir == dest_dir:
                    print(f"  [{version}/{brand_or_model}] {json_count} files, already at correct path")
                    continue

                if os.path.exists(dest_dir):
                    print(f"  [{version}/{brand_or_model}] -> {sanitized} (CONFLICT: dest exists, {json_count} files)")
                    errors.append(f"{version}/{brand_or_model} -> {sanitized}: destination exists")
                    continue

                print(f"  [{version}/{brand_or_model}] -> {sanitized} ({json_count} files)")
                moves[(subdir, dest_dir)] = (version, brand_or_model, sanitized, json_count)
            else:
                # Multiple models in one brand dir — need to split
                print(f"  [{version}/{brand_or_model}] MIXED: {json_count} files from {len(model_set)} models: {model_set}")
                for root, dirs, files in os.walk(subdir):
                    for f in files:
                        if not f.endswith(".json") or f == "manifest.json":
                            continue
                        fpath = os.path.join(root, f)
                        try:
                            with open(fpath, "r", encoding="utf-8") as fh:
                                data = json.load(fh)
                            model = data.get("model", brand_or_model)
                            sanitized = sanitize_model(model)
                            rel = os.path.relpath(fpath, subdir)
                            dest = os.path.join(version_dir, sanitized, rel)
                            moves[(fpath, dest)] = (version, brand_or_model, sanitized, 1)
                        except (json.JSONDecodeError, IOError):
                            pass

    print(f"\n{'DRY RUN' if dry_run else 'APPLYING'}: {len(moves)} moves, {len(errors)} conflicts")

    if not dry_run and moves:
        for (src, dest), (version, old, new, count) in moves.items():
            if os.path.isdir(src):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(src, dest)
                print(f"  MOVED: {version}/{old} -> {version}/{new}")
            elif os.path.isfile(src):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(src, dest)

    if errors:
        print(f"\nConflicts (manual resolution needed):")
        for e in errors:
            print(f"  {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate output/ from brand to model structure")
    parser.add_argument("--apply", action="store_true", help="Actually move files (default: dry run)")
    args = parser.parse_args()
    migrate(dry_run=not args.apply)
