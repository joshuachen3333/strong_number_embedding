#!/usr/bin/env python3
"""Analyze Bible verses for 26 test dimensions — no LLM calls, no tokens.

Supports both OT (Hebrew WH/WTH/WAH) and NT (Greek WG/WTG/WAG) tag formats.
Dimensions are organized as: shared core, OT-specific, NT-specific, universal.

Parses UNV+SN from FHL API and classifies each verse by which test
dimensions it triggers. Outputs a report for test set curation.

Usage:
    python3 analyze_test_dimensions.py --book 創 --chap 1
    python3 analyze_test_dimensions.py --book 創 --chap 1-3
    python3 analyze_test_dimensions.py --book 太 --chap 1-28
    python3 analyze_test_dimensions.py --book 創 --chap 1 --sec 1-10
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG


# ── Tag extraction ───────────────────────────────────────────────────────────

TAG_RE = re.compile(r'(\{<([^>]+)>\}|<([^>]+)>)')

# General tag pattern for regex — matches both OT and NT tags
# Captures: (prefix, number_part) where number_part may include letter suffix
ANY_TAG = r'<(W[ATG]*[HG]?)(\d+[a-z]?)>'
ANY_TAG_RAW = r'<W[ATG]*[HG]?\d+[a-z]?>'


def extract_tags(text):
    """Extract all SN tags from UNV+SN text.

    Returns list of dicts: {raw, content, braced, prefix, number, lang, is_morph}
    Handles both Hebrew (WH/WTH/WAH) and Greek (WG/WTG/WAG) tags,
    including letter-suffixed SN like <WG3608a>.
    """
    tags = []
    for m in TAG_RE.finditer(text):
        raw = m.group(0)
        content = m.group(2) or m.group(3)  # inside < >
        braced = m.group(2) is not None

        # Parse W-prefix and number (allow letter suffix like 3608a)
        prefix_m = re.match(r'^(W[ATG]*[HG]?)(\d+[a-z]?)$', content)
        if prefix_m:
            prefix = prefix_m.group(1)
            number = prefix_m.group(2)
        else:
            prefix = ""
            number = content

        # Detect language and morph status from prefix
        lang = "G" if prefix.endswith("G") or "G" in prefix else "H"
        is_morph = prefix.startswith("WT")  # WTH (Hebrew) or WTG (Greek)

        tags.append({
            "raw": raw,
            "content": content,
            "braced": braced,
            "prefix": prefix,
            "number": number,
            "lang": lang,
            "is_morph": is_morph,
        })
    return tags


# ── Helper predicates ────────────────────────────────────────────────────────

def _is_morph_tag(tag):
    """Morph tag: WTH (Hebrew) or WTG (Greek)."""
    return tag["is_morph"]


def _is_morph_num(prefix, num):
    """Check if a (prefix, num) pair from regex is a morph tag."""
    return prefix.startswith("WT")


def _is_900x(tag):
    """Hebrew 900x prefix: WAH + 5-digit number starting with 09."""
    return (tag["number"].startswith("09") and len(tag["number"]) == 5
            and "A" in tag["prefix"] and tag["lang"] == "H")


def _is_900x_num(num):
    return num.startswith("09") and len(num) == 5


def _has_prefix(tag):
    """Tag has A-prefix (WAH or WAG)."""
    return "A" in tag["prefix"]


def _has_letter_suffix(tag):
    """SN has letter suffix like 3608a."""
    return tag["number"] and tag["number"][-1].isalpha()


# ── 26 Test Dimensions ──────────────────────────────────────────────────────

def analyze_verse(text, tags):
    """Check which of 26 test dimensions this verse triggers.

    Returns dict of {dimension_id: bool}
    Dimensions:
      #1-4:    Shared core (language-agnostic)
      #5,10,15,16,18,23,24: OT-specific (Hebrew)
      #26:     NT-specific (Greek)
      #6-9,11-14,17,19-22,25: Universal (expanded for both H and G)
    """
    results = {}
    numbers = [t["number"] for t in tags]
    prefixes = [t["prefix"] for t in tags]

    # Count categories
    sn_count = len(tags)
    morph_tags = [t for t in tags if _is_morph_tag(t)]
    implicit_tags = [t for t in tags if t["braced"]]
    p900x_tags = [t for t in tags if _is_900x(t)]
    prefix_tags = [t for t in tags if _has_prefix(t)]

    # ── Shared core (#1-4) — language-agnostic ──

    # 1. SN count — simple short (≤ 8 tags)
    results[1] = sn_count <= 8

    # 2. SN count — long (> 15 tags)
    results[2] = sn_count > 15

    # 3. SN count — repeated parallel (same SN number appears 2+ times)
    num_counts = Counter(numbers)
    results[3] = any(c >= 2 for c in num_counts.values())

    # 4. Implicit markers — basic ({<...>})
    results[4] = len(implicit_tags) > 0

    # ── OT-specific (#5, #10, #15, #16, #18, #23, #24) ──

    # 5. [OT] Implicit markers — 900x combo ({<WAH...>} with A prefix)
    implicit_wah = [t for t in implicit_tags if _has_prefix(t) and t["lang"] == "H"]
    results[5] = len(implicit_wah) > 0

    # 10. [OT] Format — 900x prefixes
    results[10] = len(p900x_tags) > 0

    # 15. [OT] Position — 900x prefix before core (<WAH09xxx> followed by <WH>)
    prefix_before_core = re.findall(r'<WAH09\d{3}><WH\d+>', text)
    results[15] = len(prefix_before_core) > 0

    # 16. [OT] Edge — 4-digit number starting with 09 (like 0914, NOT a 900x)
    four_digit_09 = [t for t in tags if t["number"].startswith("09")
                     and len(t["number"]) == 4]
    results[16] = len(four_digit_09) > 0

    # 18. [OT] Triple consecutive — same group (900x+core+morph)
    triple_re = re.compile(ANY_TAG + r'\s*' + ANY_TAG + r'\s*' + ANY_TAG)
    triples = triple_re.findall(text)
    has_18 = False
    for t3 in triples:
        p1, n1, p2, n2, p3, n3 = t3
        if (_is_900x_num(n1) and "A" in p1
                and not _is_morph_num(p2, n2) and _is_morph_num(p3, n3)):
            has_18 = True
            break
    results[18] = has_18

    # 23. [OT] Ketiv/Qere — consecutive morph tags with no core SN between them
    double_morph_ot = re.findall(r'<WTH\d+>\s*<WTH\d+>', text)
    wah_morph_variant = re.findall(r'<WTH\d+>\s*<WAH0867[56]>', text)
    results[23] = len(double_morph_ot) > 0 or len(wah_morph_variant) > 0

    # 24. [OT] Number chain — 4+ consecutive pure WH core tags
    num_chain = re.findall(r'(<WH\d+>\s*<WH\d+>\s*<WH\d+>\s*<WH\d+>)', text)
    has_24 = False
    for chain in num_chain:
        chain_tags = re.findall(r'<(W[ATH]*[HG]?)(\d+)>', chain)
        if all(p == 'WH' for p, n in chain_tags):
            if not any(n.startswith("8") and len(n) == 4 for p, n in chain_tags):
                has_24 = True
                break
    results[24] = has_24

    # ── Universal (expanded for both H and G) ──

    # 6. Morphology — single verb (exactly 1 morph tag)
    results[6] = len(morph_tags) == 1

    # 7. Morphology — multi verb (2+ morph tags)
    results[7] = len(morph_tags) >= 2

    # 8. Format — zero-padding (5-digit core number like 07225)
    core_tags = [t for t in tags if not t["braced"]
                 and not _is_morph_tag(t) and not _is_900x(t)]
    results[8] = any(len(t["number"].rstrip('abcdefghijklmnopqrstuvwxyz')) == 5
                     and t["number"][0] == "0"
                     and not t["number"].startswith("09") for t in core_tags)

    # 9. Format — leading zeros (any number with leading 0)
    results[9] = any(n.startswith("0") for n in numbers if n and n[0].isdigit())

    # 11. Format — compound preposition (consecutive tags, first has A-prefix)
    consecutive = re.findall(
        r'(' + ANY_TAG_RAW + r')\s*(' + ANY_TAG_RAW + r')', text)
    compound = [c for c in consecutive
                if "A" in re.match(r'<(W[ATG]*)', c[0]).group(1)]
    results[11] = len(compound) > 0

    # 12. Format — prefix (WAH/WAG) non-900x
    prefix_non900x = [t for t in prefix_tags
                      if not (_is_900x_num(t["number"]) and len(t["number"]) == 5)]
    results[12] = len(prefix_non900x) > 0

    # 13. Position — SN after Chinese (check for anomalies)
    sn_before_chinese = re.search(r'^<W', text)
    results[13] = sn_before_chinese is None

    # 14. Position — Morphology after core SN (<W[HG]xxxx><WT[HG]xxxx> sequence)
    morph_sequence = re.findall(
        r'<W[AG]*[HG]?\d+[a-z]?><WT[HG]\d+>', text)
    results[14] = len(morph_sequence) > 0

    # 17. Format — same number with different prefix
    number_prefixes = {}
    for t in tags:
        n = t["number"]
        p = t["prefix"]
        if n not in number_prefixes:
            number_prefixes[n] = set()
        number_prefixes[n].add(p)
    same_num_diff_prefix = {n: ps for n, ps in number_prefixes.items()
                           if len(ps) >= 2}
    results[17] = len(same_num_diff_prefix) > 0

    # 19. Triple consecutive — cross-boundary (前組尾+後組頭)
    has_19 = False
    for t3 in triples:
        p1, n1, p2, n2, p3, n3 = t3
        # Everything that's NOT a same-group OT triple (#18)
        is_ot_same = (_is_900x_num(n1) and "A" in p1
                      and not _is_morph_num(p2, n2) and _is_morph_num(p3, n3))
        if not is_ot_same:
            has_19 = True
            break
    results[19] = has_19

    # 20-22. Quad consecutive sub-types — always cross-boundary
    quad_re = re.compile(
        ANY_TAG + r'\s*' + ANY_TAG + r'\s*' + ANY_TAG + r'\s*' + ANY_TAG)
    quads = quad_re.findall(text)

    has_20 = False  # 雙動詞 morph: core+morph+core+morph
    has_21 = False  # 動詞 morph+其他: core+morph then other
    has_22 = False  # 介系詞/prefix 連串: multiple A-prefix tags

    for q in quads:
        p1, n1, p2, n2, p3, n3, p4, n4 = q
        m = [_is_morph_num(p, n) for p, n in
             [(p1, n1), (p2, n2), (p3, n3), (p4, n4)]]
        w = ["A" in p for p in [p1, p2, p3, p4]]

        if m[1] and m[3] and not m[0] and not m[2]:
            has_20 = True
        elif sum(w) >= 3:
            has_22 = True
        else:
            for i in range(3):
                if not m[i] and m[i+1]:
                    has_21 = True
                    break

    results[20] = has_20
    results[21] = has_21
    results[22] = has_22

    # 25. FHL data anomaly — SN with 6+ digits or non-parseable content
    pure_digits = [t["number"].rstrip('abcdefghijklmnopqrstuvwxyz')
                   for t in tags if t["prefix"]]
    results[25] = any(len(d) >= 6 for d in pure_digits)

    # ── NT-specific (#26) ──

    # 26. [NT] Letter-suffixed SN (variant lemma, e.g. <WG3608a>)
    results[26] = any(_has_letter_suffix(t) for t in tags)

    return results


# ── Uncovered patterns (candidates for new rules) ────────────────────────────

def find_uncovered(text, tags):
    """Look for patterns not covered by the 26 dimensions."""
    uncovered = []

    for t in tags:
        # Very long number (7+ digits)
        pure = t["number"].rstrip('abcdefghijklmnopqrstuvwxyz')
        if len(pure) >= 7:
            uncovered.append(f"Unusually long number: {t['raw']}")
        # Empty or single-digit number
        if len(pure) <= 1 and t["prefix"]:
            uncovered.append(f"Very short number: {t['raw']}")

    # Nested braces
    if "{{" in text or "}}" in text:
        uncovered.append("Double braces found")

    # 5+ consecutive tags
    quint_re = re.compile(
        r'(' + ANY_TAG_RAW + r')\s*(' + ANY_TAG_RAW + r')\s*('
        + ANY_TAG_RAW + r')\s*(' + ANY_TAG_RAW + r')\s*(' + ANY_TAG_RAW + r')')
    quint_consecutive = quint_re.findall(text)
    if quint_consecutive:
        uncovered.append(f"Quint consecutive tags: {quint_consecutive[0]}")

    return uncovered


# ── Dimension labels ─────────────────────────────────────────────────────────

DIM_LABELS = {
    # Shared core
    1:  "SN count — 簡單短節 (≤8)",
    2:  "SN count — 長節多 SN (>15)",
    3:  "SN count — 重複平行結構",
    4:  "Implicit markers — 基本",
    # OT-specific
    5:  "[OT] Implicit — 900x 組合",
    10: "[OT] 格式 — 900x prefixes",
    15: "[OT] 位置 — 900x prefix 在 core 前",
    16: "[OT] 邊界 — 4位 09 陷阱",
    18: "[OT] 三連續 — 同組 (900x+core+morph)",
    23: "[OT] Ketiv/Qere — 連續雙 morph",
    24: "[OT] 數目字 SN 連串 (≥4 純 WH)",
    # Universal (both OT and NT)
    6:  "Morphology — 單動詞",
    7:  "Morphology — 多動詞",
    8:  "格式 — zero-padding (5位 core)",
    9:  "格式 — leading zeros",
    11: "格式 — 複合介系詞/prefix 連續",
    12: "格式 — WA[HG] 非 900x",
    13: "位置 — SN 在中文字後 (正常)",
    14: "位置 — Morphology 緊跟 core SN",
    17: "格式 — 同號不同 prefix",
    19: "三連續 — 跨組邊界 (前組尾+後組頭)",
    20: "四連續 — 雙 morph 跨組 (c+m|c+m)",
    21: "四連續 — morph+其他 跨組 (c+m|…)",
    22: "四連續 — prefix 連串跨組",
    25: "FHL 資料異常 (6+ 位數 SN)",
    # NT-specific
    26: "[NT] 字母後綴 SN (variant lemma)",
}

ALL_DIMS = sorted(DIM_LABELS.keys())
MAX_DIM = max(ALL_DIMS)


# ── Main ─────────────────────────────────────────────────────────────────────

def parse_range(s):
    result = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-", 1)
            result.extend(range(int(a), int(b) + 1))
        else:
            result.append(int(part))
    return result


def parse_sec_arg(sec_args):
    """Parse flexible --sec format: 1 2 3, 1,2,3, 1-10, 1,2,5-13,17,19."""
    result = []
    for arg in sec_args:
        for part in re.split(r'[,\s]+', arg.strip()):
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                result.extend(range(int(a), int(b) + 1))
            else:
                result.append(int(part))
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Analyze UNV+SN verses for 26 test dimensions (no LLM calls)")
    parser.add_argument("--chineses", "--book", default="創", dest="book",
                        help="Chinese book abbreviation (e.g., 創 出 詩 太 約)")
    parser.add_argument("--chap", default="1",
                        help="Chapter: single (1), range (1-10), or 'all'")
    parser.add_argument("--sec", nargs="*", default=None,
                        help="Verse(s): 1 2 3, 1,2,3, 1-10, 1,2,5-13,17,19")
    parser.add_argument("--summary", action="store_true",
                        help="Show dimension summary only")
    parser.add_argument("--uncovered", action="store_true",
                        help="Show uncovered patterns only")
    args = parser.parse_args()

    book_chi = args.book
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    if args.chap.lower() == "all":
        chapters = []
        for c in range(1, 151):
            try:
                d = fetch_chap_cached(book_chi, c, "unv", strong=1)
                if d:
                    chapters.append(c)
            except Exception:
                break
    else:
        chapters = parse_range(args.chap)
    sec_range = set(parse_sec_arg(args.sec)) if args.sec else None

    # Dimension counters
    dim_counts = {i: 0 for i in ALL_DIMS}
    dim_verses = {i: [] for i in ALL_DIMS}
    all_uncovered = []
    total_verses = 0

    for chap in chapters:
        chap_data = fetch_chap_cached(book_chi, chap, "unv", strong=1)
        secs = sorted(chap_data.keys())
        if sec_range:
            secs = [s for s in secs if s in sec_range]

        for sec in secs:
            text = chap_data[sec]
            tags = extract_tags(text)
            dims = analyze_verse(text, tags)
            uncovered = find_uncovered(text, tags)
            total_verses += 1

            verse_ref = f"{book_eng} {chap}:{sec}"

            if not args.summary and not args.uncovered:
                triggered = [i for i in ALL_DIMS if dims[i]]
                print(f"{verse_ref:15s} [{len(tags):2d} tags] "
                      f"dims: {','.join(str(d) for d in triggered)}")

            for i in ALL_DIMS:
                if dims[i]:
                    dim_counts[i] += 1
                    dim_verses[i].append(verse_ref)

            if uncovered:
                for u in uncovered:
                    all_uncovered.append((verse_ref, u))
                if not args.summary:
                    for u in uncovered:
                        print(f"  ⚠ UNCOVERED: {u}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  Dimension Coverage Summary — {book_eng} ({total_verses} verses)")
    print(f"{'='*60}")
    for i in ALL_DIMS:
        pct = dim_counts[i] / total_verses * 100 if total_verses > 0 else 0
        examples = dim_verses[i][:3]
        example_str = ", ".join(examples) if examples else "none"
        print(f"  #{i:2d} {DIM_LABELS[i]:45s} {dim_counts[i]:4d} ({pct:5.1f}%)  e.g. {example_str}")

    if all_uncovered:
        print(f"\n  {'─'*50}")
        print(f"  UNCOVERED PATTERNS ({len(all_uncovered)}) — candidates for new rules")
        print(f"  {'─'*50}")
        for verse_ref, pattern in all_uncovered:
            print(f"    {verse_ref}: {pattern}")
    else:
        print(f"\n  No uncovered patterns found.")


if __name__ == "__main__":
    main()
