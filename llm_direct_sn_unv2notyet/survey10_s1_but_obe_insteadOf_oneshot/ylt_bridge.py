#!/usr/bin/env python3
"""YLT bridge for the A2 contest — WLC (Hebrew+SN) + YLT (aligned literal English).

Joshua 2026-07-11 chose source config = **WLC + YLT** (survey11 open decision). YLT
(Young's Literal Translation) glues English to Hebrew word order, so paired with the
WLC Hebrew+FHL-SN line it gives the model a complete, KJV-free source: identity +
09xxx from WLC, disambiguating literal English from YLT. Escapes consensus
circularity (the target UNV's real FHL tags are the answer key, never shown).

Data (Clear Bible, local, manual):
  Alignments/data/eng/targets/YLT/ot_YLT.tsv        — YLT OT words (id, text, isPunc, isPrimary)
  Alignments/data/eng/alignments/YLT/WLC-YLT-manual.json — WLC morph ↔ YLT word records

ID schemes (BCVWP):
  YLT word id   : BBCCCVVVWWW           e.g. 01001001001 = Gen 1:1 word 1
  WLC morph id  : oBBCCCVVVWWWm         e.g. o010010010011 = Gen 1:1 word 1 morph 1
"""

import os
import csv
import json
from collections import defaultdict

_S10 = os.path.dirname(os.path.abspath(__file__))
_ALIGN = os.path.join(os.path.dirname(_S10), "Alignments", "data", "eng")
YLT_TSV = os.path.join(_ALIGN, "targets", "YLT", "ot_YLT.tsv")
WLC_YLT_JSON = os.path.join(_ALIGN, "alignments", "YLT", "WLC-YLT-manual.json")

_YLT_WORDS = None          # {ylt_word_id: text}
_WLC_TO_YLT = None         # {wlc_morph_id: [ylt_word_id, ...]}


def _load():
    global _YLT_WORDS, _WLC_TO_YLT
    if _YLT_WORDS is not None:
        return
    words = {}
    with open(YLT_TSV, encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            # keep real words (drop punctuation-only rows); text is the surface form.
            if row.get("isPunc", "").lower() == "true":
                continue
            words[row["id"]] = row["text"]
    _YLT_WORDS = words
    m = defaultdict(list)
    with open(WLC_YLT_JSON, encoding="utf-8") as f:
        recs = json.load(f).get("records", [])
    for r in recs:
        for src in r.get("source", []):
            for tgt in r.get("target", []):
                m[src].append(tgt)
    _WLC_TO_YLT = m


def _verse_prefix(wlc_book, chap, sec):
    """BBCCCVVV prefix shared by every YLT word id in the verse (wlc_book = '01')."""
    return f"{wlc_book}{int(chap):03d}{int(sec):03d}"


def ylt_verse_text(wlc_book, chap, sec):
    """The YLT English sentence for one verse (ordered words). '' if unavailable."""
    _load()
    pref = _verse_prefix(wlc_book, chap, sec)
    ids = sorted(wid for wid in _YLT_WORDS if wid.startswith(pref))
    return " ".join(_YLT_WORDS[i] for i in ids).strip()


def ylt_alignment(wlc_book, chap, sec):
    """{wlc_morph_id: 'aligned english words'} for the verse — the per-morpheme gloss
    the model can use to map each Hebrew<SN> morph to its literal English."""
    _load()
    pref = "o" + _verse_prefix(wlc_book, chap, sec)
    out = {}
    for morph_id, ylt_ids in _WLC_TO_YLT.items():
        if morph_id.startswith(pref):
            words = [_YLT_WORDS[t] for t in ylt_ids if t in _YLT_WORDS]
            if words:
                out[morph_id] = " ".join(words)
    return out


def build_wlc_ylt_source(wlc_tokens_with_ids, wlc_book, chap, sec, per_morph=True):
    """Render the combined WLC+YLT source block.

    `wlc_tokens_with_ids` = list of (morph_id, hebrew_text, fhl_num_or_None) — the WLC
    morphemes WITH their ids (so each can be glossed by its aligned YLT word).

    Layout:
      <hebrew><SN>  ⟨ylt gloss⟩   per morpheme   (per_morph=True)  ── tightest signal
    plus the full YLT sentence for global reading. Falls back to WLC-only if YLT is
    missing for the verse.
    """
    align = ylt_alignment(wlc_book, chap, sec) if per_morph else {}
    parts = []
    for morph_id, text, num in wlc_tokens_with_ids:
        piece = f"{text}<{num}>" if num else text
        gloss = align.get(morph_id, "")
        parts.append(f"{piece} ⟨{gloss}⟩" if gloss else piece)
    wlc_line = "  ".join(parts)
    ylt_line = ylt_verse_text(wlc_book, chap, sec)
    block = f"WLC (Hebrew, each morpheme tagged with its FHL Strong's Number, " \
            f"⟨…⟩ = literal YLT English gloss):\n{wlc_line}"
    if ylt_line:
        block += f"\n\nYLT (Young's Literal Translation, full verse):\n{ylt_line}"
    return block


def load_wlc_verse_with_ids(wlc_book, chap, sec):
    """Like run_stage2_harsh.load_wlc_verse but KEEPS the morph id (needed to align to
    YLT). Returns list of (morph_id, hebrew_text, fhl_num_or_None)."""
    from run_stage2_harsh import _WLC_CACHE, WLC_TSV, _bridge_number
    rows = _WLC_CACHE.get(wlc_book)
    if rows is None:
        rows = defaultdict(list)
        with open(WLC_TSV, encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                i = row["id"]
                if not i.startswith("o" + wlc_book):
                    continue
                rows[(int(i[3:6]), int(i[6:9]))].append(row)
        _WLC_CACHE[wlc_book] = rows
    out = []
    for row in rows.get((int(chap), int(sec)), []):
        num = _bridge_number(row["lemma"], row["strongs"], row["pos"])
        out.append((row["id"], row["text"], num))
    return out
