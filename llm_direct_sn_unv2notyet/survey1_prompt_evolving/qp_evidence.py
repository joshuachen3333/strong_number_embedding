#!/usr/bin/env python3
"""FHL qp parsing-code evidence for the survey1 gold consensus pipeline.

Governing plan: parsing/QP_ENRICHMENT_PLAN.md §3.  Conceptual root:
parsing/PARSING_FOUNDATIONS.md — FHL "parsing" (lemma + morphology) is our
UPSTREAM INPUT; the task the consensus panel judges is ALIGNMENT
(word(s)-for-word(s) or null).

Origin credit: the qp access layer (is_ot_book / normalize_qp_sn / _get_db /
fetch logic) is copy-adapted from
survey6_original_lang_benchmark/run_survey6.py::fetch_qp_verse().
Deliberately self-contained here (no survey6 import) so survey1 carries no
cross-survey dependency; extended to also read pro / orig / uword / uorig
(survey6 selects only wid, word, sn, exp, wform) and to KEEP words whose sn
is empty (the word-order skeleton is the alignment left side).

Data caveat (survey2 FHL_SN_FORMAT_REFERENCE.md §11.4): a qp record's sn may
legitimately DIFFER from the qb inline SN for the same word (qb/qp
disagreement, documented for compounds).  The pre-validator below therefore
treats "verb-sense record without a usable sn" as a data gap and never turns
it into a violation (see validate_morph_attachment).

Everything in this module is deterministic and LLM-free.  It NEVER touches
resolution: build_gold_standard() in consensus.py remains the sole authority
for resolved_at (ARCHITECTURE_DECISIONS.md AD-1).
"""

import json
import os
import re
import sqlite3
import urllib.parse
import urllib.request

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
REPO_ROOT = os.path.dirname(PARENT_DIR)

FHL_QP_API = "https://bible.fhl.net/json/qp.php"

_PARSING_DB = os.path.join(REPO_ROOT, "original_text_preparation",
                           "source_sqlite", "bible_parsing.db")

# Map CHI_TO_ENG book codes → SQLite engs codes (copied from survey6).
_SQLITE_BOOK_MAP = {
    # OT differences
    "Exod": "Ex", "Isa": "Is", "Jonah": "Jon",
    "1Sam": "1 Sam", "2Sam": "2 Sam",
    "1Kgs": "1 Kin", "2Kgs": "2 Kin",
    "1Chr": "1 Chr", "2Chr": "2 Chr",
    # NT differences
    "Jas": "James", "Phlm": "Philem",
    "1Cor": "1 Cor", "2Cor": "2 Cor",
    "1Thess": "1 Thess", "2Thess": "2 Thess",
    "1Tim": "1 Tim", "2Tim": "2 Tim",
    "1Pet": "1 Pet", "2Pet": "2 Pet",
    "1John": "1 John", "2John": "2 John", "3John": "3 John",
}

_books_data = None
_qp_cache = {}
_db_conn = None


def _load_book_order():
    global _books_data
    if _books_data is None:
        books_json = os.path.join(REPO_ROOT, "shared", "data", "books.json")
        with open(books_json, encoding="utf-8") as f:
            _books_data = json.load(f)
    return _books_data


def is_ot_book(book_eng: str) -> bool:
    """Return True if book_eng is an Old Testament book (Gen–Mal)."""
    books = _load_book_order()
    for i, b in enumerate(books):
        if b["eng"] == book_eng:
            return i <= 38
    return True  # default OT if unknown


def normalize_qp_sn(sn_str: str, ot: bool) -> str:
    """Convert qp 5-digit sn to FHL tag body (e.g. '00430' → 'WH0430').

    Rule (from survey6): if sn starts with '00', strip one leading zero.
    Then prepend WH (OT) or WG (NT).
    """
    s = sn_str.strip()
    if s.startswith("00"):
        s = s[1:]           # "00430" → "0430"
    prefix = "WH" if ot else "WG"
    return f"{prefix}{s}"


def _get_db():
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(_PARSING_DB)
        _db_conn.row_factory = sqlite3.Row
    return _db_conn


def build_qp_table(book_eng: str, chap: int, sec: int) -> list:
    """Per-word qp parsing records for one verse — SQLite first, qp.php fallback.

    Returns a list of dicts in ORIGINAL word order (wid ascending; the wid=0
    whole-verse overview row is skipped):
      wid   — original-language word index
      word  — surface form (Unicode: SQLite uword preferred over legacy word)
      orig  — lemma / dictionary headword (uorig preferred); None if absent
      sn    — normalized FHL tag body ("00430" → "WH0430"); None when qp
              carries no SN for the word (word KEPT: the word-order skeleton
              is the alignment left side — every word maps to a Chinese span
              or to null)
      pro   — part of speech (OT: empty; NT qp.php: "動詞"…; NT SQLite: "v"…)
      wform — parsing code (OT: "動詞，Qal 完成式 3 單陽"; NT SQLite: "aai3s")
      exp   — gloss

    Cached per (book_eng, chap, sec).  Returns [] when no data is available
    (callers treat [] as "no qp evidence this verse").
    """
    key = (book_eng, chap, sec)
    if key in _qp_cache:
        return _qp_cache[key]

    ot = is_ot_book(book_eng)

    def _mk(wid, word, orig, sn_raw, pro, wform, exp):
        return {
            "wid": wid,
            "word": word,
            "orig": orig or None,
            "sn": normalize_qp_sn(sn_raw, ot) if sn_raw else None,
            "pro": pro or None,
            "wform": wform or None,
            "exp": exp or None,
        }

    records = []

    # Try local SQLite first (also serves the 17 numbered books qp.php can't).
    if os.path.exists(_PARSING_DB):
        db = _get_db()
        table = "lparsing" if ot else "fhlwhparsing"
        sqlite_book = _SQLITE_BOOK_MAP.get(book_eng, book_eng)
        cursor = db.execute(
            f"SELECT wid, word, uword, sn, pro, wform, orig, uorig, exp "
            f"FROM {table} WHERE engs=? AND chap=? AND sec=? ORDER BY wid",
            (sqlite_book, chap, sec))
        for row in cursor.fetchall():
            if row["wid"] == 0:
                continue
            word = ((row["uword"] or "").strip()
                    or (row["word"] or "").strip())
            if not word:
                continue
            records.append(_mk(
                row["wid"], word,
                (row["uorig"] or "").strip() or (row["orig"] or "").strip(),
                (row["sn"] or "").strip(),
                (row["pro"] or "").strip(),
                (row["wform"] or "").strip(),
                (row["exp"] or "").strip()))
        if records:
            _qp_cache[key] = records
            return records

    # Fallback to qp.php API (spaced-name books unsupported there).
    qp_book = _SQLITE_BOOK_MAP.get(book_eng, book_eng)
    if " " in qp_book:
        _qp_cache[key] = []
        return []
    params = urllib.parse.urlencode({"engs": qp_book, "chap": chap, "sec": sec})
    req = urllib.request.Request(
        f"{FHL_QP_API}?{params}",
        headers={"User-Agent": "StrongNumberEmbedding/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = json.loads(resp.read().decode("utf-8"))
    for entry in raw.get("record", raw) if isinstance(raw, dict) else raw:
        wid = int(entry.get("wid") or 0)   # defensive: API may return "0" str
        if wid == 0:
            continue
        word = (entry.get("word") or "").strip()
        if not word:
            continue
        records.append(_mk(
            wid, word,
            (entry.get("orig") or "").strip(),
            (entry.get("sn") or "").strip(),
            (entry.get("pro") or "").strip(),
            (entry.get("wform") or "").strip(),
            (entry.get("exp") or "").strip()))

    _qp_cache[key] = records
    return records


def is_verb_record(rec: dict) -> bool:
    """True when this qp record is the VERB-SENSE reading of its word.

    OT (SQLite and qp.php) and NT qp.php mark verbs with 動詞 in wform/pro;
    NT SQLite abbreviates pro to "v" (vs "ra" article, "c" conj, "d" adv…).
    """
    wform = rec.get("wform") or ""
    pro = rec.get("pro") or ""
    if "動詞" in wform or "動詞" in pro:
        return True
    p = pro.strip().lower()
    return p == "v" or p.startswith("v-")


def _bare(sn_tag) -> int:
    """'WH01254' / '<WH01254>' / '01254' → 1254; shell/zero-pad-proof compare."""
    m = re.search(r"(\d+)", sn_tag or "")
    return int(m.group(1)) if m else None


# One annotated-text token: optional braces, W + letter cluster + H/G + digits.
# A 'T' in the letter cluster (WTH/WTG) marks a MORPHOLOGY code; everything
# else (WH/WG meaning SN, WAH 900x prefix) is a meaning-stream token.
# (Same tag family as consensus.py's _restore_gold_shells regex, line 158.)
_TOKEN_RE = re.compile(r"\{?<W([A-Z]*)([HG])(\d{1,5})[a-z]?>\}?")


def validate_morph_attachment(annotated_text: str, qp_records: list) -> list:
    """Deterministic pre-validator: a morphology code (<WTH8xxx>/<WTG5xxx>)
    must IMMEDIATELY follow its verb-sense SN — the SN whose qp record is a
    verb reading (is_verb_record).  Pure function: no LLM, no network, no I/O.

    annotated_text MUST be in shelled FHL form.  In --naked mode restore the
    shells first (shared.sn_shell.restore_shell_lookup against the UNV+SN
    reference — the same basis as run_gold_standard._coverage()).

    Checks, per morph token (chains allowed — a morph token may directly
    follow another morph token hanging off the same anchor SN):
      morph_before_any_sn    — no meaning SN precedes it at all
      morph_not_adjacent     — text intervenes between it and the previous tag
      morph_after_non_verb_sn — the anchoring meaning SN is not verb-sense per
        qp.  SKIPPED when qp lists no verb record at all, AND ALSO when any
        verb-sense record lacks a usable sn (data gap / §11.4 qb-qp SN
        disagreement: the verb the morph really anchors to may be invisible
        to us, so flagging would inject a FALSE violation into judge context).
        Adjacency is still enforced in both skip cases; verb-sense is simply
        not judged.

    Returns [] when clean, else a list of structured error dicts:
      {"code": str, "morph": str, "attached_to": str|None, "gap": str|None,
       "expected_verb_sns": [str], "message": str}
    """
    verb_sns = {}
    has_snless_verb = False
    for r in qp_records or []:
        if is_verb_record(r):
            if r.get("sn"):
                verb_sns[_bare(r["sn"])] = r["sn"]
            else:
                has_snless_verb = True
    expected = sorted(verb_sns.values())
    judge_verb_sense = bool(verb_sns) and not has_snless_verb

    errors = []
    anchor_num = None   # bare int of the meaning SN anchoring the current chain
    anchor_tag = None
    prev_end = None     # end offset of the previous tag (meaning or morph)

    for m in _TOKEN_RE.finditer(annotated_text or ""):
        letters, num = m.group(1), int(m.group(3))
        tag = m.group(0)
        if "T" not in letters:               # meaning token → new chain anchor
            anchor_num, anchor_tag = num, tag
            prev_end = m.end()
            continue
        # morphology token
        if anchor_num is None:
            errors.append({
                "code": "morph_before_any_sn",
                "morph": tag, "attached_to": None, "gap": None,
                "expected_verb_sns": expected,
                "message": (f"morph code {tag} appears before any meaning SN "
                            f"— it must immediately follow its verb-sense SN"),
            })
        elif m.start() != prev_end:
            gap = annotated_text[prev_end:m.start()]
            errors.append({
                "code": "morph_not_adjacent",
                "morph": tag, "attached_to": anchor_tag, "gap": gap,
                "expected_verb_sns": expected,
                "message": (f"morph code {tag} is separated from {anchor_tag} "
                            f"by {gap!r} — it must be immediately adjacent"),
            })
        elif judge_verb_sense and anchor_num not in verb_sns:
            errors.append({
                "code": "morph_after_non_verb_sn",
                "morph": tag, "attached_to": anchor_tag, "gap": None,
                "expected_verb_sns": expected,
                "message": (f"morph code {tag} follows {anchor_tag}, which qp "
                            f"does not mark as a verb; valid anchors: "
                            f"{expected}"),
            })
        prev_end = m.end()
    return errors


def format_qp_evidence(qp_records: list, morph_findings: dict = None) -> str:
    """Render the compact qp evidence block for R2/R3 judge context.

    Contract with judge.py templates: returns "" when there are no records
    (the prompt stays byte-for-byte identical to the no-evidence prompt);
    otherwise returns a block that STARTS and ENDS with a newline.

    morph_findings: optional {output_label: [error dicts]} from
    validate_morph_attachment, one entry per candidate output (A/B/C).
    An empty/None dict renders no pre-validator section at all.
    """
    if not qp_records:
        return ""
    lines = [
        "",
        "=== ORIGINAL-LANGUAGE PARSING EVIDENCE (FHL qp parsing code — "
        "evidence, NOT the verdict) ===",
        "Per-word morphology of the original text, in ORIGINAL word order — "
        "the alignment",
        "skeleton: every word below maps to a Chinese span or to null.  "
        "[VERB] marks the",
        "verb-sense records: a morphology code (<WTH8xxx>/<WTG5xxx>) is "
        "inflection annotation",
        "of THAT verb, never a separate word — it must sit immediately after "
        "the verb-sense SN",
        "and must never be matched to its own Chinese token.",
        "",
        "wid | original | lemma | SN | parsing | gloss",
    ]
    for r in qp_records:
        flag = " [VERB]" if is_verb_record(r) else ""
        parsing = r.get("wform") or r.get("pro") or "-"
        lines.append(
            f"  {r['wid']:>2} | {r['word']} | {r.get('orig') or '-'} | "
            f"{r.get('sn') or '-'} | {parsing}{flag} | {r.get('exp') or '-'}")
    verbs = sorted({r["sn"] for r in qp_records
                    if r.get("sn") and is_verb_record(r)})
    lines.append("")
    lines.append(f"Verb-sense SNs (the only valid morph-code anchors): "
                 f"{', '.join(verbs) if verbs else '(none listed by qp)'}")
    if morph_findings:
        lines.append("")
        lines.append("Deterministic morph pre-validator on the candidate "
                     "outputs (rule-based, no LLM):")
        for label in sorted(morph_findings):
            errs = morph_findings[label]
            if not errs:
                lines.append(f"  Output {label}: OK")
            else:
                lines.append(f"  Output {label}: {len(errs)} violation(s)")
                for e in errs:
                    lines.append(f"    - {e['message']}")
    return "\n".join(lines) + "\n"
