# bridge_gloss.py — per-Hebrew-word English gloss from Clear Bible alignment. No LLM.
#
# Data source: ../Alignments/data/eng/ (Clear Bible alignment corpus).
#
# ylt_gloss_for_verse(wlc_book, chap, sec):
#   For each WLC (Hebrew) token in the verse, in source order, look up the
#   YLT English word(s) aligned to it via WLC-YLT-manual.json.
#
# bsb_gloss_for_verse(wlc_book, chap, sec):
#   BSB alignment keys off WLCM (a differently-tokenized copy of WLC), not WLC
#   itself, so WLC and WLCM ids do not match 1:1 even within the same verse.
#   Reconcile WLCM -> WLC per verse by ordinal position (i-th WLCM token in a
#   verse corresponds to the i-th WLC token in that verse).
import json
import os
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ALIGN = os.path.abspath(os.path.join(_HERE, "..", "Alignments", "data", "eng"))
_SOURCES = os.path.abspath(os.path.join(_HERE, "..", "Alignments", "data", "sources"))
_WLC_TSV = os.path.join(_SOURCES, "WLC.tsv")
_WLCM_TSV = os.path.join(_SOURCES, "WLCM.tsv")

_ylt_text = None
_wlc_to_ylt = None
_wlc_rows = None

_wlcm_rows = None
_wlcm_to_bsb = None
_bsb_text = None


def _verse_key(wlc_book, chap, sec):
    return f"{int(wlc_book):02d}{int(chap):03d}{int(sec):03d}"


def _load_generic_target(name):
    """id -> text lookup for an eng/targets/<NAME>/ot_<NAME>.tsv file."""
    out = {}
    path = os.path.join(_ALIGN, "targets", name, f"ot_{name}.tsv")
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idi, txi = header.index("id"), header.index("text")
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) > max(idi, txi):
                out[c[idi]] = c[txi]
    return out


def _load_ylt_text():
    global _ylt_text
    if _ylt_text is None:
        _ylt_text = _load_generic_target("YLT")
    return _ylt_text


def _load_alignment(name):
    """source-token-id -> [target-token-id, ...] from an alignments/<NAME>/*-manual.json file."""
    mapping = defaultdict(list)
    with open(name, encoding="utf-8") as f:
        data = json.load(f)
    for rec in data["records"]:
        for s in rec["source"]:
            for t in rec["target"]:
                mapping[s].append(t)
    return mapping


def _load_wlc_to_ylt():
    global _wlc_to_ylt
    if _wlc_to_ylt is None:
        path = os.path.join(_ALIGN, "alignments", "YLT", "WLC-YLT-manual.json")
        _wlc_to_ylt = _load_alignment(path)
    return _wlc_to_ylt


def _load_source_rows(tsv_path):
    """verse-key -> [(token_id, hebrew_text), ...] in file (source) order."""
    rows = defaultdict(list)
    with open(tsv_path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idi, txi = header.index("id"), header.index("text")
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) <= max(idi, txi):
                continue
            wid = c[idi]
            # id format: "o" + book(2) + chap(3) + verse(3) + word(3) + part(1)
            vkey = wid[1:9] if wid[:1].isalpha() else wid[:8]
            rows[vkey].append((wid, c[txi]))
    return rows


def _load_wlc_rows():
    global _wlc_rows
    if _wlc_rows is None:
        _wlc_rows = _load_source_rows(_WLC_TSV)
    return _wlc_rows


def _load_wlcm_rows():
    global _wlcm_rows
    if _wlcm_rows is None:
        _wlcm_rows = _load_source_rows(_WLCM_TSV)
    return _wlcm_rows


def ylt_gloss_for_verse(wlc_book, chap, sec):
    """[(hebrew_text, english_gloss)] for each WLC token in the verse (source order)."""
    ylt = _load_ylt_text()
    align = _load_wlc_to_ylt()
    rows = _load_wlc_rows()
    vkey = _verse_key(wlc_book, chap, sec)
    out = []
    for wid, heb in rows.get(vkey, []):
        eng = " ".join(ylt.get(t, "") for t in align.get(wid, [])).strip()
        out.append((heb, eng))
    return out


def bsb_gloss_for_verse(wlc_book, chap, sec):
    """[(hebrew_text, english_gloss)] for each WLC token in the verse (source order).

    BSB is aligned against WLCM (not WLC). WLCM token ids don't match WLC token
    ids 1:1 (WLCM re-tokenizes some words), so reconcile by ordinal position
    within the verse: the i-th WLCM token stands in for the i-th WLC token.
    """
    global _bsb_text, _wlcm_to_bsb
    if _bsb_text is None:
        _bsb_text = _load_generic_target("BSB")
    if _wlcm_to_bsb is None:
        path = os.path.join(_ALIGN, "alignments", "BSB", "WLCM-BSB-manual.json")
        _wlcm_to_bsb = _load_alignment(path)

    wlc_rows = _load_wlc_rows()
    wlcm_rows = _load_wlcm_rows()
    vkey = _verse_key(wlc_book, chap, sec)
    wlc_v = wlc_rows.get(vkey, [])
    wlcm_v = wlcm_rows.get(vkey, [])

    out = []
    for i, (wid, heb) in enumerate(wlc_v):
        wlcm_id = wlcm_v[i][0] if i < len(wlcm_v) else None
        eng = ""
        if wlcm_id:
            eng = " ".join(_bsb_text.get(t, "") for t in _wlcm_to_bsb.get(wlcm_id, [])).strip()
        out.append((heb, eng))
    return out
