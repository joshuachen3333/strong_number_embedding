#!/usr/bin/env python3
"""Parameterized WLC↔English bridge for the A2 contest (YLT / BSB, config-driven).

Generalizes the original ylt_bridge so the readable-English source is swappable
without new code — Joshua revises the base source config (survey11: WLC+YLT →
WLC+BSB, 2026-07-11) and may again. Each source is one SOURCES[...] entry: its target
TSV (Clear Bible), the text column, a row-drop predicate (punctuation/excluded), and
its manual WLC↔target alignment JSON. Source morph ids in every alignment match the
WLC.tsv ids (o+BBCCCVVVWWWm), so the same load_wlc_verse_with_ids feeds all.

  YLT — Young's Literal: English glued to Hebrew word order (surfaces prefixes/particles).
  BSB — Berean Standard Bible: modern readable English (natural order; the new base).
"""

import os
import re
import csv
import json
from collections import defaultdict

_S10 = os.path.dirname(os.path.abspath(__file__))
_ALIGN = os.path.join(os.path.dirname(_S10), "Alignments", "data", "eng")


def _bsb_drop(row):
    return bool((row.get("exclude") or "").strip())


def _ylt_drop(row):
    return (row.get("isPunc") or "").lower() == "true"


_SOURCES_DIR = os.path.join(os.path.dirname(_S10), "Alignments", "data", "sources")

# `wlc_tsv` = the HEBREW source whose morph ids the alignment keys on, AND whose SN
# extraction `_bridge_number` understands.
#
# The BSB alignment nominally targets WLCM ids, but WLCM.tsv has an INCOMPATIBLE schema
# (no `lemma` column; strongs without the `H` prefix like `0871a`; full-word pos like
# `preposition`) that `_bridge_number` cannot parse → it would drop EVERY SN. WLC.tsv
# and WLCM.tsv share ids for ~99.3% of Genesis morphs, so loading WLC.tsv keeps SN
# extraction correct and still resolves the WLCM-BSB gloss on the shared 99.3%; only the
# ~0.7% divergent morphs miss their BSB gloss (SN inventory — the graded content —
# unaffected). So BOTH OT sources load WLC.tsv. (NT will pin SBLGNT.tsv here — the reason
# this stays a per-source field.)
SOURCES = {
    "YLT": {
        "tsv": os.path.join(_ALIGN, "targets", "YLT", "ot_YLT.tsv"),
        "text_col": "text", "drop": _ylt_drop,
        "align": os.path.join(_ALIGN, "alignments", "YLT", "WLC-YLT-manual.json"),
        "wlc_tsv": os.path.join(_SOURCES_DIR, "WLC.tsv"),
        "label": "Young's Literal Translation, full verse",
    },
    "BSB": {
        "tsv": os.path.join(_ALIGN, "targets", "BSB", "ot_BSB.tsv"),
        "text_col": "text", "drop": _bsb_drop,
        "align": os.path.join(_ALIGN, "alignments", "BSB", "WLCM-BSB-manual.json"),
        "wlc_tsv": os.path.join(_SOURCES_DIR, "WLC.tsv"),   # WLCM schema breaks _bridge_number → use WLC
        "label": "Berean Standard Bible, full verse",
        # NT (A2 cornerstone: Greek + BSB bridge). Same TSV/JSON schemas as OT, so
        # `drop`/`text_col` are reused; only the English NT target differs here — the
        # Greek source (SBLGNT critical vs BGNT Byzantine) + its alignment are selected
        # per-run via NT_GREEK below (see `greek_source`).
        "nt_tsv": os.path.join(_ALIGN, "targets", "BSB", "nt_BSB.tsv"),
    },
}

# Selectable NT Greek source (Joshua 2026-07-11 — keep the Received/Byzantine tradition
# available, not just the critical text). Same TSV schema; the BSB alignment file follows
# the pattern {greek}-{eng}-manual.json (SBLGNT-BSB-manual.json / BGNT-BSB-manual.json).
NT_GREEK = {
    "SBLGNT": {"greek_tsv": os.path.join(_SOURCES_DIR, "SBLGNT.tsv"),
               "label": "SBLGNT critical text (≈NA28/UBS family)"},
    "BGNT":   {"greek_tsv": os.path.join(_SOURCES_DIR, "BGNT.tsv"),
               "label": "Byzantine Majority text (Received-tradition family)"},
}
DEFAULT_NT_GREEK = "SBLGNT"


def _nt_align_path(eng_name, greek_source):
    """NT alignment = eng/alignments/{eng}/{greek}-{eng}-manual.json."""
    return os.path.join(_ALIGN, "alignments", eng_name,
                        f"{greek_source}-{eng_name}-manual.json")


def _is_nt(book):
    """Book number ≥ 40 ⇒ New Testament (Greek/SBLGNT path)."""
    try:
        return int(book) >= 40
    except (TypeError, ValueError):
        return False

_CACHE = {}   # (name, testament) -> (words {id:text}, src2tgt {morph_id:[tgt_id]})


def _load(name, testament="ot", greek_source=DEFAULT_NT_GREEK):
    # OT is greek-source-agnostic; keep its cache key stable so the Hebrew path never
    # re-loads when the NT greek source changes.
    ckey = (name, testament, greek_source if testament == "nt" else None)
    if ckey in _CACHE:
        return _CACHE[ckey]
    cfg = SOURCES.get(name)
    if not cfg:
        raise ValueError(f"unknown english source '{name}' (have {list(SOURCES)})")
    if testament == "nt":
        tsv_path = cfg.get("nt_tsv")
        align_path = _nt_align_path(name, greek_source)
        if not (tsv_path and os.path.isfile(align_path)):
            raise ValueError(f"english source '{name}' has no NT data for "
                             f"greek={greek_source} ({align_path})")
    else:
        tsv_path = cfg["tsv"]
        align_path = cfg["align"]
    words = {}
    with open(tsv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if cfg["drop"](row):
                continue
            words[row["id"]] = row[cfg["text_col"]]
    m = defaultdict(list)
    with open(align_path, encoding="utf-8") as f:
        for r in json.load(f).get("records", []):
            for src in r.get("source", []):
                for tgt in r.get("target", []):
                    m[src].append(tgt)
    _CACHE[ckey] = (words, m)
    return _CACHE[ckey]


def _verse_prefix(book, chap, sec):
    return f"{book}{int(chap):03d}{int(sec):03d}"


def verse_text(name, book, chap, sec, greek_source=DEFAULT_NT_GREEK):
    """The English sentence for one verse (ordered words). '' if unavailable.

    Target ids (ot_BSB/nt_BSB) carry NO source prefix (bare BBCCCVVVWWW) in both
    testaments, so this path is prefix-agnostic — only the loaded target file differs.
    (English target is greek-source-agnostic; greek_source only affects the alignment.)
    """
    testament = "nt" if _is_nt(book) else "ot"
    words, _ = _load(name, testament, greek_source)
    pref = _verse_prefix(book, chap, sec)
    ids = sorted(wid for wid in words if wid.startswith(pref))
    return " ".join(words[i] for i in ids).strip()


def alignment(name, book, chap, sec, greek_source=DEFAULT_NT_GREEK):
    """{source_morph_id: 'aligned english words'} for the verse.

    Source ids carry a single-char prefix: 'o' (WLC/OT) or 'n' (Greek/NT). For NT the
    alignment is the {greek_source}-{name} manual alignment.
    """
    testament = "nt" if _is_nt(book) else "ot"
    words, m = _load(name, testament, greek_source)
    pref = ("n" if testament == "nt" else "o") + _verse_prefix(book, chap, sec)
    out = {}
    for morph_id, tgt_ids in m.items():
        if morph_id.startswith(pref):
            ws = [words[t] for t in tgt_ids if t in words]
            if ws:
                out[morph_id] = " ".join(ws)
    return out


def build_wlc_eng_source(name, tokens_with_ids, book, chap, sec, per_morph=True,
                         greek_source=DEFAULT_NT_GREEK):
    """Render the combined <original>+<English> source block: each tagged morpheme
    with its aligned English gloss, plus the full English verse. Source-only fallback
    if the English source lacks the verse. Testament-aware header (WLC Hebrew vs the
    selected Greek text); the per-morph tag render is identical (the num string already
    carries its testament letter for Greek, e.g. 'G976')."""
    align = alignment(name, book, chap, sec, greek_source) if per_morph else {}
    parts = []
    for morph_id, text, num in tokens_with_ids:
        piece = f"{text}<{num}>" if num else text
        gloss = align.get(morph_id, "")
        parts.append(f"{piece} ⟨{gloss}⟩" if gloss else piece)
    src_line = "  ".join(parts)
    eng_line = verse_text(name, book, chap, sec, greek_source)
    label = SOURCES[name]["label"]
    if _is_nt(book):
        header = (f"{greek_source} (Greek, each word tagged with its FHL Strong's "
                  f"Number, ⟨…⟩ = {name} English gloss):\n{src_line}")
    else:
        header = (f"WLC (Hebrew, each morpheme tagged with its FHL Strong's Number, "
                  f"⟨…⟩ = {name} English gloss):\n{src_line}")
    block = header
    if eng_line:
        block += f"\n\n{name} ({label}):\n{eng_line}"
    return block


_HEB_CACHE = {}   # (tsv_path, book) -> {(chap,sec): [row,...]}


def load_wlc_verse_with_ids(wlc_book, chap, sec, source="BSB"):
    """WLC (Hebrew) morphemes WITH morph id (needed to align to the English source).
    Both BSB and YLT load WLC.tsv (`wlc_tsv`) — NOT WLCM.tsv, whose schema breaks SN
    extraction (see SOURCES note). `source` is kept for future NT (SBLGNT) pinning.
    Returns [(morph_id, hebrew, fhl_num)]."""
    from run_stage2_harsh import _bridge_number
    tsv = SOURCES.get(source, SOURCES["BSB"])["wlc_tsv"]
    key = (tsv, wlc_book)
    rows = _HEB_CACHE.get(key)
    if rows is None:
        rows = defaultdict(list)
        with open(tsv, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                i = row["id"]
                if not i.startswith("o" + wlc_book):
                    continue
                rows[(int(i[3:6]), int(i[6:9]))].append(row)
        _HEB_CACHE[key] = rows
    out = []
    for row in rows.get((int(chap), int(sec)), []):
        num = _bridge_number(row["lemma"], row["strongs"], row["pos"])
        out.append((row["id"], row["text"], num))
    return out


# ── NT / Greek path (SBLGNT) ────────────────────────────────────────────────
# Greek is simpler than Hebrew: NO 09xxx inseparable prefixes, so no PREFIX_BRIDGE,
# no cj-waw case, no augmented (>8674) branch. The one load-bearing difference vs the
# Hebrew `_bridge_number` is that the rendered tag MUST carry a literal 'G' — the
# scorer (build_exclusion.classify) DEFAULTS testament to 'H' when no letter is
# present, so a bare '<976>' would misclassify as Hebrew H976 and never match UNV's
# <WG976>. Returning 'G976' → tag '<G976>' → key ('G','G976') = UNV truth. Zero-pad
# is moot (classify does int()); suffix letters are dropped (Hebrew-consistent).

def _bridge_number_greek(strongs):
    """SBLGNT Greek Strong's → FHL number string carrying the 'G' testament letter,
    or None if not a scorable SN. 'G0976' → 'G976'; 'G0000' (unmarked) → None."""
    m = re.match(r"G(\d+)([a-z]?)", strongs or "")
    if not m:
        return None
    n = int(m.group(1))   # strips zero-padding: 'G0976' → 976
    if n == 0:            # G0000 = unmarked (a few rows exist)
        return None
    return f"G{n}"        # MUST keep the G; drop suffix; no zero-pad (scorer int()-normalizes)


_GRK_CACHE = {}   # (tsv_path, book) -> {(chap,sec): [row,...]}


def load_greek_verse_with_ids(sbl_book, chap, sec, greek_source=DEFAULT_NT_GREEK):
    """Greek words WITH morph id (needed to align to the English source). Reads the
    Greek text tsv selected by `greek_source` (SBLGNT critical | BGNT Byzantine).
    Source ids are 'n'+BB(40..66)+CCC+VVV+WWW (offsets identical to WLC, only the prefix
    is 'n' vs 'o'). Returns [(morph_id, greek, fhl_num)] where fhl_num is e.g. 'G976'."""
    gcfg = NT_GREEK.get(greek_source)
    if not gcfg:
        raise ValueError(f"unknown greek source '{greek_source}' (have {list(NT_GREEK)})")
    tsv = gcfg["greek_tsv"]
    key = (tsv, sbl_book)
    rows = _GRK_CACHE.get(key)
    if rows is None:
        rows = defaultdict(list)
        with open(tsv, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                i = row["id"]
                if not i.startswith("n" + sbl_book):
                    continue
                rows[(int(i[3:6]), int(i[6:9]))].append(row)
        _GRK_CACHE[key] = rows
    out = []
    for row in rows.get((int(chap), int(sec)), []):
        num = _bridge_number_greek(row["strongs"])
        out.append((row["id"], row["text"], num))
    return out
