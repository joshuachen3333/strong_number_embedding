#!/usr/bin/env python3
"""Repair SN shells in existing output/ using each verse's stored UNV reference.

Why this exists instead of a re-run: the defect was never in the placement the
LLM produced, only in the *shell* wrapped around each number. In naked mode the
model is asked for bare numbers but sometimes adds a shell of its own, copying
the OT worked examples — so on a NT verse it emitted `<WH1234>` where the source
says `<WG1234>`. `restore_shell_lookup` used to match bare `<digits>` only, so
those passed through untouched (fixed 2026-07-27 in shared/sn_shell.py).

Every output JSON stores `unv_sn_reference`, which is the authority for every
shell. So the repair is deterministic and free — no LLM call, no FHL call.

SAFETY INVARIANT: the bare-number sequence must be byte-identical before and
after. This repair may only change shells (prefix class, zero-padding, braces);
if a file's numbers or their order would change, it is SKIPPED and reported.
That keeps the model's actual work — which number sits on which token — intact.

Usage:
    python3 repair_shell_from_reference.py                      # dry run, all models
    python3 repair_shell_from_reference.py --model deepseek-v3.1_671b-cloud
    python3 repair_shell_from_reference.py --apply               # write changes
    python3 repair_shell_from_reference.py --apply --backup      # .bak alongside
"""

import argparse
import json
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, REPO_ROOT)

from shared.sn_shell import (  # noqa: E402
    build_shell_lookup, restore_shell_lookup, extract_bare_numbers,
)

OUTPUT_DIR = os.path.join(REPO_ROOT, "output")

NT_BOOKS = {
    "Matt", "Mark", "Luke", "John", "Acts", "Rom", "1Cor", "2Cor", "Gal", "Eph",
    "Phil", "Col", "1Thess", "2Thess", "1Tim", "2Tim", "Titus", "Phlm", "Heb",
    "Jas", "1Pet", "2Pet", "1John", "2John", "3John", "Jude", "Rev",
}

REPAIR_NOTE = ("shell repaired from unv_sn_reference "
               "(restore_shell_lookup fix 2026-07-27; numbers unchanged)")


def iter_files(model_filter=None):
    if not os.path.isdir(OUTPUT_DIR):
        return
    for version in sorted(os.listdir(OUTPUT_DIR)):
        vdir = os.path.join(OUTPUT_DIR, version)
        if not os.path.isdir(vdir):
            continue
        for model in sorted(os.listdir(vdir)):
            if model_filter and model != model_filter:
                continue
            mdir = os.path.join(vdir, model)
            if not os.path.isdir(mdir):
                continue
            for root, _dirs, files in os.walk(mdir):
                for fn in sorted(files):
                    if fn.endswith(".json"):
                        yield version, model, os.path.join(root, fn)


def repair_text(sn_text, reference):
    """Returns (repaired, safe). `safe` is False when the bare-number sequence
    would change, which must never happen for a shell-only repair."""
    lookup = build_shell_lookup(reference)
    out = restore_shell_lookup(sn_text, lookup)
    return out, extract_bare_numbers(out) == extract_bare_numbers(sn_text)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default=None, help="only this model dir")
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument("--backup", action="store_true", help="keep <file>.bak when writing")
    ap.add_argument("--limit", type=int, default=0, help="stop after N files (probing)")
    args = ap.parse_args()

    stats = Counter()
    changed_by_model = Counter()
    changed_nt = Counter()
    unsafe, unparseable, samples = [], [], []

    for version, model, path in iter_files(args.model):
        if args.limit and stats["seen"] >= args.limit:
            break
        stats["seen"] += 1
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            unparseable.append(path)
            stats["unparseable"] += 1
            continue

        ref = data.get("unv_sn_reference") or ""
        tv = data.get("target_version") or version
        sn_field = f"{tv}_sn"
        sn = data.get(sn_field) or ""
        if not ref or not sn:
            stats["no_data"] += 1
            continue

        fixed, safe = repair_text(sn, ref)
        if fixed == sn:
            stats["already_ok"] += 1
            continue
        if not safe:
            unsafe.append(path)
            stats["unsafe_skipped"] += 1
            continue

        stats["changed"] += 1
        changed_by_model[f"{version}/{model}"] += 1
        if data.get("book") in NT_BOOKS:
            changed_nt["NT"] += 1
        else:
            changed_nt["OT"] += 1
        if len(samples) < 3:
            samples.append((path, sn[:80], fixed[:80]))

        if args.apply:
            data[sn_field] = fixed
            notes = data.setdefault("notes", [])
            if isinstance(notes, list) and REPAIR_NOTE not in notes:
                notes.append(REPAIR_NOTE)
            try:
                if args.backup and not os.path.exists(path + ".bak"):
                    os.replace(path, path + ".bak")
                tmp = path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, path)   # atomic: never leaves a truncated JSON
                stats["written"] += 1
            except OSError as e:
                print(f"  WRITE FAILED {path}: {e}")
                stats["write_failed"] += 1

    mode = "APPLIED" if args.apply else "DRY RUN (nothing written)"
    print(f"\n=== shell repair — {mode} ===")
    for k in ("seen", "already_ok", "changed", "written", "unsafe_skipped",
              "no_data", "unparseable", "write_failed"):
        if stats[k]:
            print(f"  {k:16s} {stats[k]}")
    if changed_nt:
        print(f"  changed by testament: {dict(changed_nt)}")
    if changed_by_model:
        print("  changed by model:")
        for k, v in changed_by_model.most_common():
            print(f"    {k:38s} {v}")
    if samples:
        print("\n  samples (before → after):")
        for p, before, after in samples:
            print(f"    {os.path.relpath(p, REPO_ROOT)}")
            print(f"      - {before}")
            print(f"      + {after}")
    if unsafe:
        print(f"\n  ⚠️  {len(unsafe)} file(s) SKIPPED — repair would have changed the "
              f"numbers, not just the shells. Inspect these by hand:")
        for p in unsafe[:10]:
            print(f"    {os.path.relpath(p, REPO_ROOT)}")
        if len(unsafe) > 10:
            print(f"    … and {len(unsafe)-10} more")
    if unparseable:
        print(f"\n  {len(unparseable)} unparseable file(s):")
        for p in unparseable[:5]:
            print(f"    {os.path.relpath(p, REPO_ROOT)}")
    if not args.apply and stats["changed"]:
        print(f"\n  → re-run with --apply to write {stats['changed']} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
