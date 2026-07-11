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
    },
}

_CACHE = {}   # name -> (words {id:text}, wlc2tgt {morph_id:[tgt_id]})


def _load(name):
    if name in _CACHE:
        return _CACHE[name]
    cfg = SOURCES.get(name)
    if not cfg:
        raise ValueError(f"unknown english source '{name}' (have {list(SOURCES)})")
    words = {}
    with open(cfg["tsv"], encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if cfg["drop"](row):
                continue
            words[row["id"]] = row[cfg["text_col"]]
    m = defaultdict(list)
    with open(cfg["align"], encoding="utf-8") as f:
        for r in json.load(f).get("records", []):
            for src in r.get("source", []):
                for tgt in r.get("target", []):
                    m[src].append(tgt)
    _CACHE[name] = (words, m)
    return _CACHE[name]


def _verse_prefix(wlc_book, chap, sec):
    return f"{wlc_book}{int(chap):03d}{int(sec):03d}"


def verse_text(name, wlc_book, chap, sec):
    """The English sentence for one verse (ordered words). '' if unavailable."""
    words, _ = _load(name)
    pref = _verse_prefix(wlc_book, chap, sec)
    ids = sorted(wid for wid in words if wid.startswith(pref))
    return " ".join(words[i] for i in ids).strip()


def alignment(name, wlc_book, chap, sec):
    """{wlc_morph_id: 'aligned english words'} for the verse."""
    words, m = _load(name)
    pref = "o" + _verse_prefix(wlc_book, chap, sec)
    out = {}
    for morph_id, tgt_ids in m.items():
        if morph_id.startswith(pref):
            ws = [words[t] for t in tgt_ids if t in words]
            if ws:
                out[morph_id] = " ".join(ws)
    return out


def build_wlc_eng_source(name, wlc_tokens_with_ids, wlc_book, chap, sec, per_morph=True):
    """Render the combined WLC+<English> source block: each Hebrew<SN> morpheme with
    its aligned English gloss, plus the full English verse. WLC-only fallback if the
    English source lacks the verse."""
    align = alignment(name, wlc_book, chap, sec) if per_morph else {}
    parts = []
    for morph_id, text, num in wlc_tokens_with_ids:
        piece = f"{text}<{num}>" if num else text
        gloss = align.get(morph_id, "")
        parts.append(f"{piece} ⟨{gloss}⟩" if gloss else piece)
    wlc_line = "  ".join(parts)
    eng_line = verse_text(name, wlc_book, chap, sec)
    label = SOURCES[name]["label"]
    block = (f"WLC (Hebrew, each morpheme tagged with its FHL Strong's Number, "
             f"⟨…⟩ = {name} English gloss):\n{wlc_line}")
    if eng_line:
        block += f"\n\n{name} ({label}):\n{eng_line}"
    return block


_HEB_CACHE = {}   # (tsv_path, book) -> {(chap,sec): [row,...]}


def load_wlc_verse_with_ids(wlc_book, chap, sec, source="BSB"):
    """WLC/WLCM morphemes WITH morph id (needed to align to the English source).
    Loads from the HEBREW TSV pinned by `source` (BSB→WLCM.tsv, YLT→WLC.tsv) so the
    morph ids match that source's alignment. Returns [(morph_id, hebrew, fhl_num)]."""
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
