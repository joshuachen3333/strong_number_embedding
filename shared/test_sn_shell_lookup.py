"""Round-trip fidelity tests for shell lookup/restore (验证① for naked mode).

Pins lookup (zero-loss, table-driven) vs guess (heuristic) with numbers,
classified by SN type. Canonical home of build_shell_lookup /
restore_shell_lookup is shared/sn_shell.py (extracted from the main driver's
self-contained pair; survey9's extract_tags-dependent copy is intentionally
left untouched).
"""

import glob
import json
import os
import re

import pytest

from sn_shell import (
    build_shell_lookup,
    restore_shell_lookup,
    restore_shell_guess,
    strip_shell,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_GLOB = os.path.join(
    REPO_ROOT, "llm_direct_sn_unv2notyet", "survey1_prompt_evolving",
    "gold_standard", "Gen", "**", "*.json",
)

# Genesis 1:1 — real UNV+SN, exercises every SN type in one verse:
#   <WAH09002> 900x prefix · <WH07225> core · <WTH8804> morphology
#   {<WH0853>} implicit braced (appears twice) · <WH08064> core-8xxx
GEN_1_1 = (
    "起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>"
    "{<WH0853>}天<WH08064>{<WH0853>}地<WH0776>。"
)


def test_build_shell_lookup_maps_each_bare_number_to_original_tag():
    lookup = build_shell_lookup(GEN_1_1)
    assert lookup["09002"] == "<WAH09002>"      # 900x prefix
    assert lookup["07225"] == "<WH07225>"       # core
    assert lookup["8804"] == "<WTH8804>"        # morphology
    assert lookup["0853"] == "{<WH0853>}"       # implicit braced
    assert lookup["08064"] == "<WH08064>"       # core 8xxx (not morphology)
    assert lookup["0430"] == "<WH0430>"


def test_restore_shell_lookup_roundtrips_genesis_1_1_exactly():
    stripped = strip_shell(GEN_1_1, markers=False)
    restored = restore_shell_lookup(stripped, build_shell_lookup(GEN_1_1))
    assert restored == GEN_1_1


def test_restore_shell_lookup_keeps_unknown_number_bare_as_red_flag():
    # A number the LLM emitted that isn't in the source UNV+SN must stay bare
    # (<9999>) so a judge/human sees the anomaly — guess would mask it.
    lookup = build_shell_lookup(GEN_1_1)
    assert restore_shell_lookup("foo<9999>bar", lookup) == "foo<9999>bar"


def test_build_shell_lookup_first_occurrence_wins_on_same_number():
    # §2.1 boundary: same number, different shell → keep first occurrence.
    text = "a{<WH0853>}b<WH0853>c"
    lookup = build_shell_lookup(text)
    assert lookup["0853"] == "{<WH0853>}"


# --- 验证①: corpus-level lookup vs guess, classified by SN type ------------

def _sn_type(raw_tag: str) -> str:
    """Classify an original FHL tag for error reporting."""
    braced = raw_tag.startswith("{")
    num = int(re.search(r"(\d+)", raw_tag).group(1))
    if braced:
        return "implicit_braced"
    if "WAH" in raw_tag or "WAG" in raw_tag:
        return "wah_prefix"
    if "WT" in raw_tag:
        return "morphology_8xxx"
    if 8000 <= num <= 8999:
        return "core_8xxx"
    return "core"


def _load_corpus():
    refs = []
    for fp in sorted(glob.glob(GOLDEN_GLOB, recursive=True)):
        try:
            d = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        ref = d.get("unv_sn_reference", "")
        if ref:
            refs.append((os.path.relpath(fp, REPO_ROOT), ref))
    return refs


def _same_number_different_shell(ref: str) -> dict:
    """Return {bare_num: {shells}} for numbers carrying >1 distinct shell.

    This is the §2.1 boundary: the same SN appears in the source with two
    different shells (e.g. 0776 as <WH0776> and {<WH0776>}). build_shell_lookup
    keeps first-occurrence, so it cannot reproduce both — the only case where
    lookup is not lossless.
    """
    by_num = {}
    for m in re.finditer(r"\{?<W[ATG]*[HG]\d+[a-z]?>\}?", ref):
        raw = m.group(0)
        num = strip_shell(raw, markers=False).strip("<>")
        by_num.setdefault(num, set()).add(raw)
    return {n: s for n, s in by_num.items() if len(s) > 1}


def test_lookup_is_lossless_off_boundary_and_beats_guess_on_golden_corpus(capsys):
    corpus = _load_corpus()
    if not corpus:
        pytest.skip("no golden corpus found")

    from collections import Counter
    type_total = Counter()
    lookup_bad = []          # verses where lookup != source
    boundary_verses = []     # verses hitting §2.1
    guess_ok = 0

    for relpath, ref in corpus:
        stripped = strip_shell(ref, markers=False)
        restored_lookup = restore_shell_lookup(stripped, build_shell_lookup(ref))
        restored_guess = restore_shell_guess(stripped, testament="OT")

        for m in re.finditer(r"\{?<W[ATG]*[HG]\d+[a-z]?>\}?", ref):
            type_total[_sn_type(m.group(0))] += 1

        if _same_number_different_shell(ref):
            boundary_verses.append(relpath)
        if restored_lookup != ref:
            lookup_bad.append(relpath)
        if restored_guess == ref:
            guess_ok += 1

    verses = len(corpus)
    lookup_ok = verses - len(lookup_bad)
    non_boundary = verses - len(boundary_verses)
    lookup_ok_off_boundary = sum(
        1 for r in (relpath for relpath, _ in corpus)
        if r not in lookup_bad and r not in boundary_verses
    )

    with capsys.disabled():
        print(f"\n  验证① round-trip fidelity over {verses} golden verses (Gen 1)")
        print(f"  {'─'*58}")
        print(f"  LOOKUP perfect verses : {lookup_ok}/{verses}")
        print(f"  GUESS  perfect verses : {guess_ok}/{verses}")
        print(f"  §2.1 boundary verses  : {len(boundary_verses)}/{verses} "
              f"(same number, >1 shell)")
        print(f"  LOOKUP perfect off-boundary: {lookup_ok_off_boundary}/{non_boundary}")
        print(f"  tags by type          : {dict(type_total)}")
        print(f"  LOOKUP failures occur ONLY on §2.1 boundary: "
              f"{set(lookup_bad) <= set(boundary_verses)}")
        print(f"  boundary verses (human-review list): "
              f"{[os.path.basename(v) for v in boundary_verses]}")

    # Contract 1: lookup's ONLY failures are the documented §2.1 boundary.
    assert set(lookup_bad) <= set(boundary_verses), \
        f"lookup failed off-boundary: {set(lookup_bad) - set(boundary_verses)}"
    # Contract 2: lookup is lossless on every non-boundary verse.
    assert lookup_ok_off_boundary == non_boundary
    # Contract 3: lookup strictly dominates guess (here 17 vs 0 perfect).
    assert lookup_ok >= guess_ok
