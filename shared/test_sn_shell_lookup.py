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
    restore_shells_positional,
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


# ── a wrong TESTAMENT letter must be overridden; nothing else ────────────────
# Regression: in naked mode the model is asked for bare numbers, but it
# sometimes adds a shell of its own — and it copies the OT worked examples, so
# on a New Testament verse it emits <WH1234> where the source says <WG1234>.
# The old regex matched bare <digits> only, so such a shell passed through
# untouched and silently poisoned the output.
#
# The override is narrow ON PURPOSE. Braces, WAH-vs-WH, and zero-padding vary
# legitimately per OCCURRENCE of the same number (§2.1 boundary), and this table
# keeps only the first occurrence's shell — so overriding those would destroy
# per-occurrence detail the model may have got right. A testament letter is
# fixed for the whole verse and can never be a per-occurrence difference.

EPH_1_8 = (
    "這<WG3739>恩典是　神用<WG1722>諸般<WG3956>智慧<WG4678>{<WG2532>}"
    "聰明<WG5428>，充充足足<WG4052><WTG5656>賞給<WG1519>我們<WG1473>的；"
)


def test_restore_overrides_model_supplied_wrong_testament_shell():
    lookup = build_shell_lookup(EPH_1_8)
    # model emitted Hebrew shells on a Greek verse (the real Eph 1:8 defect)
    got = restore_shell_lookup("這<WH3739>恩典<WH3956>智慧<WH4678>", lookup)
    assert got == "這<WG3739>恩典<WG3956>智慧<WG4678>"


def test_restore_overrides_wrong_testament_on_morphology_tag_too():
    lookup = build_shell_lookup(EPH_1_8)
    assert restore_shell_lookup("充充足足<WTH5656>", lookup) == "充充足足<WTG5656>"


def test_restore_keeps_model_braces_when_testament_agrees():
    # THE REGRESSION GUARD: 0853 appears twice in Gen 1:1, once braced. The
    # table keeps only the first shell, so overriding here would strip braces
    # the model had right. Same testament -> leave the model's shell alone.
    lookup = build_shell_lookup(GEN_1_1)
    assert restore_shell_lookup("天{<WH0853>}", lookup) == "天{<WH0853>}"
    assert restore_shell_lookup("天<WH0853>", lookup) == "天<WH0853>"


def test_restore_keeps_model_attached_prefix_class_when_testament_agrees():
    # WAH vs WH is also a per-occurrence distinction — not ours to overrule.
    lookup = build_shell_lookup(GEN_1_1)
    assert restore_shell_lookup("我們<WH0587>", lookup) == "我們<WH0587>"


def test_restore_bare_number_still_gets_full_shell_from_table():
    # The normal naked-mode path is untouched, including odd zero-padding.
    lookup = build_shell_lookup(GEN_1_1)
    assert restore_shell_lookup("起初<09002>", lookup) == "起初<WAH09002>"
    assert restore_shell_lookup("起初<9002>", lookup) == "起初<WAH09002>"


def test_restore_leaves_model_shelled_unknown_number_untouched():
    # Still a red flag: number absent from source keeps whatever it had, so the
    # anomaly stays visible instead of being masked by a plausible shell.
    lookup = build_shell_lookup(GEN_1_1)
    assert restore_shell_lookup("foo<WH9999>bar", lookup) == "foo<WH9999>bar"


def test_restore_does_not_touch_non_sn_angle_brackets():
    lookup = build_shell_lookup(GEN_1_1)
    assert restore_shell_lookup("a<b>c", lookup) == "a<b>c"


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


# --- occurrence-aware positional restore (§2.1 fix) ------------------------

def test_positional_restores_same_number_different_shell_losslessly():
    # §2.1 boundary: same number, two different shells, in order.
    # lookup (first-occurrence) collapses both to {<WH0853>}; positional keeps
    # each occurrence's own shell -> exact source.
    src = "a{<WH0853>}b<WH0853>c"
    stripped = strip_shell(src, markers=False)            # a<853>b<853>c
    assert restore_shell_lookup(stripped, build_shell_lookup(src)) != src   # lookup fails
    assert restore_shells_positional(stripped, src) == src                  # positional exact


def test_positional_identical_to_lookup_off_boundary():
    # Gen 1:1 has 0853 twice but with the SAME shell -> positional == lookup.
    stripped = strip_shell(GEN_1_1, markers=False)
    assert restore_shells_positional(stripped, GEN_1_1) == GEN_1_1


def test_positional_keeps_unknown_or_exhausted_bare_as_red_flag():
    # absent number stays bare
    assert restore_shells_positional("foo<9999>bar", GEN_1_1) == "foo<9999>bar"
    # more copies than source carries -> the extra one exhausts the queue -> bare
    src = "x<WH0776>y"   # strip_shell preserves zero-pad -> bare key is 0776
    assert restore_shells_positional("x<0776>y<0776>z", src) == "x<WH0776>y<0776>z"


def test_positional_lossless_on_full_golden_corpus_including_boundary(capsys):
    # The win: positional round-trips EVERY golden verse exactly — including the
    # §2.1 boundary verses that lookup cannot — so the human-review list empties.
    corpus = _load_corpus()
    if not corpus:
        pytest.skip("no golden corpus found")
    bad = []
    boundary = []
    for relpath, ref in corpus:
        stripped = strip_shell(ref, markers=False)
        if _same_number_different_shell(ref):
            boundary.append(relpath)
        if restore_shells_positional(stripped, ref) != ref:
            bad.append(relpath)
    with capsys.disabled():
        print(f"\n  positional round-trip over {len(corpus)} golden verses: "
              f"{len(corpus) - len(bad)}/{len(corpus)} perfect "
              f"(§2.1 boundary verses: {len(boundary)}, now lossless)")
    assert bad == [], f"positional failed on: {bad}"
