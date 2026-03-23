#!/usr/bin/env python3
"""Analyze Bible verses for 17 test dimensions — no LLM calls, no tokens.

Parses UNV+SN from FHL API and classifies each verse by which test
dimensions it triggers. Outputs a report for test set curation.

Usage:
    python3 analyze_test_dimensions.py --book 創 --chap 1
    python3 analyze_test_dimensions.py --book 創 --chap 1-3
    python3 analyze_test_dimensions.py --book 創 --chap 1 --sec 1-10
"""

import argparse
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG


# ── Tag extraction ───────────────────────────────────────────────────────────

TAG_RE = re.compile(r'(\{<([^>]+)>\}|<([^>]+)>)')


def extract_tags(text):
    """Extract all SN tags from UNV+SN text.

    Returns list of dicts: {raw, content, braced, prefix, number}
    """
    tags = []
    for m in TAG_RE.finditer(text):
        raw = m.group(0)
        content = m.group(2) or m.group(3)  # inside < >
        braced = m.group(2) is not None

        # Parse W-prefix and number
        prefix_m = re.match(r'^(W[ATH]*[HG]?)(\d+)$', content)
        if prefix_m:
            prefix = prefix_m.group(1)
            number = prefix_m.group(2)
        else:
            prefix = ""
            number = content

        tags.append({
            "raw": raw,
            "content": content,
            "braced": braced,
            "prefix": prefix,
            "number": number,
        })
    return tags


# ── 17 Test Dimensions ──────────────────────────────────────────────────────

def analyze_verse(text, tags):
    """Check which of 17 test dimensions this verse triggers.

    Returns dict of {dimension_id: bool}
    """
    results = {}
    numbers = [t["number"] for t in tags]
    prefixes = [t["prefix"] for t in tags]
    raw_tags = [t["raw"] for t in tags]

    # Count categories
    sn_count = len(tags)
    morph_tags = [t for t in tags if t["number"].startswith("8") and len(t["number"]) == 4]
    implicit_tags = [t for t in tags if t["braced"]]
    p900x_tags = [t for t in tags if t["number"].startswith("09") and len(t["number"]) == 5]
    wah_tags = [t for t in tags if "A" in t["prefix"]]

    # 1. SN count — simple short (≤ 8 tags)
    results[1] = sn_count <= 8

    # 2. SN count — long (> 15 tags)
    results[2] = sn_count > 15

    # 3. SN count — repeated parallel (same SN number appears 2+ times)
    from collections import Counter
    num_counts = Counter(numbers)
    results[3] = any(c >= 2 for c in num_counts.values())

    # 4. Implicit markers — basic ({<WH...>})
    results[4] = len(implicit_tags) > 0

    # 5. Implicit markers — 900x combo ({<WAH...>} with A prefix)
    implicit_wah = [t for t in implicit_tags if "A" in t["prefix"]]
    results[5] = len(implicit_wah) > 0

    # 6. Morphology — single verb (exactly 1 WTH tag)
    results[6] = len(morph_tags) == 1

    # 7. Morphology — multi verb (2+ WTH tags)
    results[7] = len(morph_tags) >= 2

    # 8. Format — zero-padding (5-digit core number like 07225)
    core_tags = [t for t in tags if not t["braced"]
                 and not (t["number"].startswith("8") and len(t["number"]) == 4)
                 and not (t["number"].startswith("09") and len(t["number"]) == 5)]
    results[8] = any(len(t["number"]) == 5 and t["number"][0] == "0"
                     and not t["number"].startswith("09") for t in core_tags)

    # 9. Format — leading zeros (any number with leading 0)
    results[9] = any(n.startswith("0") for n in numbers if n)

    # 10. Format — 900x prefixes
    results[10] = len(p900x_tags) > 0

    # 11. Format — compound preposition (consecutive SN tags in raw text)
    # Look for patterns like <WAH04480><WH05921> or <WAH09001><WH06440>
    consecutive = re.findall(r'(<W[ATH]*[HG]?\d+>)\s*(<W[ATH]*[HG]?\d+>)', text)
    # Filter: first tag should be WAH (preposition)
    compound = [c for c in consecutive if "A" in re.match(r'<(W[ATH]*)', c[0]).group(1)]
    results[11] = len(compound) > 0

    # 12. Format — WAH non-900x (WAH with number NOT starting with 09)
    wah_non900x = [t for t in wah_tags
                   if not (t["number"].startswith("09") and len(t["number"]) == 5)]
    results[12] = len(wah_non900x) > 0

    # 13. Position — SN after Chinese (always true in FHL format, check for anomalies)
    # Look for tags that appear before any Chinese character
    sn_before_chinese = re.search(r'^<W', text)
    results[13] = sn_before_chinese is None  # True = normal (SN after Chinese)

    # 14. Position — Morphology after verb SN (<WHxxxx><WTHxxxx> sequence)
    morph_sequence = re.findall(r'<W[AH]*H?\d+><WTH\d+>', text)
    results[14] = len(morph_sequence) > 0

    # 15. Position — 900x prefix before core (<WAH09xxx> followed by <WH>)
    prefix_before_core = re.findall(r'<WAH09\d{3}><WH\d+>', text)
    results[15] = len(prefix_before_core) > 0

    # 16. Edge — 4-digit number starting with 09 (like 0914, NOT a 900x)
    four_digit_09 = [t for t in tags if t["number"].startswith("09")
                     and len(t["number"]) == 4]
    results[16] = len(four_digit_09) > 0

    # 17. Format — same number with WH vs WAH (different prefix)
    number_prefixes = {}
    for t in tags:
        n = t["number"]
        p = t["prefix"]
        if n not in number_prefixes:
            number_prefixes[n] = set()
        number_prefixes[n].add(p)
    same_num_diff_prefix = {n: ps for n, ps in number_prefixes.items() if len(ps) >= 2}
    results[17] = len(same_num_diff_prefix) > 0

    # ── Consecutive tag analysis (3+ tags with no Chinese between them) ──
    # Parse all consecutive runs of tags
    TAG_PAT = r'<(W[ATH]*[HG]?)(\d+)>'
    TAG_RAW = r'<W[ATH]*[HG]?\d+>'

    def is_morph(num):
        return num.startswith("8") and len(num) == 4

    def is_900x(num):
        return num.startswith("09") and len(num) == 5

    def is_wah(prefix):
        return "A" in prefix

    # Classify each triple: same-group vs cross-boundary
    # Same-group triple: <WAH09xxx><WHxxxx><WTHxxxx> (900x prefix + core + morph)
    #   All three describe one verbal unit with inseparable preposition
    # Cross-boundary: anything else (tail of group A + head of group B)
    triple_re = re.compile(
        TAG_PAT + r'\s*' + TAG_PAT + r'\s*' + TAG_PAT)
    triples = triple_re.findall(text)

    has_18 = False  # same-group triple (900x + core + morph)
    has_19 = False  # cross-boundary triple

    for t3 in triples:
        p1, n1, p2, n2, p3, n3 = t3
        # Same-group: 900x prefix + non-morph core + morph
        if is_900x(n1) and is_wah(p1) and not is_morph(n2) and is_morph(n3):
            has_18 = True
        else:
            has_19 = True

    results[18] = has_18
    results[19] = has_19

    # ── Quad consecutive sub-types (#20-#22) — always cross-boundary ──
    quad_re = re.compile(
        TAG_PAT + r'\s*' + TAG_PAT + r'\s*' + TAG_PAT + r'\s*' + TAG_PAT)
    quads = quad_re.findall(text)

    has_20 = False  # 雙動詞 morph: verb+morph+verb+morph (groupA|groupB)
    has_21 = False  # 動詞 morph 後接其他: verb+morph|prefix/core (groupA|groupB)
    has_22 = False  # 介系詞/prefix 連串: multiple WAH (groupA tail|groupB head)

    for q in quads:
        p1, n1, p2, n2, p3, n3, p4, n4 = q
        m = [is_morph(n) for n in [n1, n2, n3, n4]]
        w = [is_wah(p) for p in [p1, p2, p3, p4]]

        # #20: verb+morph+verb+morph (positions 2,4 are morph)
        if m[1] and m[3] and not m[0] and not m[2]:
            has_20 = True
        # #22: 3+ WAH-prefix tags among the 4 (preposition/prefix chain)
        elif sum(w) >= 3:
            has_22 = True
        # #21: contains a verb+morph pair + other tags
        else:
            for i in range(3):
                if not m[i] and m[i+1]:
                    has_21 = True
                    break

    results[20] = has_20
    results[21] = has_21
    results[22] = has_22

    # 23. Ketiv/Qere — consecutive morph tags with no core SN between them
    # Pattern: <WTHxxxx><WTHxxxx> (two morph tags in a row)
    # Caused by Hebrew Ketiv/Qere (寫型/讀型) dual encoding
    double_morph = re.findall(r'<WTH\d+>\s*<WTH\d+>', text)
    results[23] = len(double_morph) > 0

    # 24. Number chain — 4+ consecutive pure WH core tags (no morph, no WAH)
    # Hebrew numerals expressed word-by-word, compressed in Chinese translation
    # e.g. 十五萬一千<WH03967><WH0505><WH02572><WH0259><WH0505>
    num_chain = re.findall(
        r'(<WH\d+>\s*<WH\d+>\s*<WH\d+>\s*<WH\d+>)', text)
    # Filter: all tags must be pure WH (not WAH, not WTH)
    has_24 = False
    for chain in num_chain:
        chain_tags = re.findall(r'<(W[ATH]*[HG]?)(\d+)>', chain)
        if all(p == 'WH' for p, n in chain_tags):
            # Exclude if any tag is morph (8xxx 4-digit)
            if not any(n.startswith("8") and len(n) == 4 for p, n in chain_tags):
                has_24 = True
                break
    results[24] = has_24

    # 25. FHL data anomaly — SN number with 6+ digits (data corruption)
    # e.g. <WAH019691> should be <WAH01961> (Josh 9:21)
    anomaly_tags = [t for t in tags if len(t["number"]) >= 6]
    results[25] = len(anomaly_tags) > 0

    return results


# ── Uncovered patterns (candidates for rule 18+) ────────────────────────────

def find_uncovered(text, tags):
    """Look for patterns not covered by the 17 dimensions."""
    uncovered = []

    # Check for unusual tag formats
    for t in tags:
        # WTG (Greek morphology in OT?)
        if t["prefix"].startswith("WTG"):
            uncovered.append(f"Greek morphology in OT: {t['raw']}")
        # WAG (Greek prefix in OT?)
        if "AG" in t["prefix"]:
            uncovered.append(f"Greek prefix marker: {t['raw']}")
        # Very long number (7+ digits? — 6-digit is now dim #25)
        if len(t["number"]) >= 7:
            uncovered.append(f"Unusually long number: {t['raw']}")
        # Empty or single-digit number
        if len(t["number"]) <= 1:
            uncovered.append(f"Very short number: {t['raw']}")

    # Check for nested braces or unusual structures
    if "{{" in text or "}}" in text:
        uncovered.append("Double braces found")

    # Check for 5+ consecutive tags (quad is now dims #19-21)
    quint_consecutive = re.findall(
        r'(<W[ATH]*[HG]?\d+>)\s*(<W[ATH]*[HG]?\d+>)\s*(<W[ATH]*[HG]?\d+>)\s*(<W[ATH]*[HG]?\d+>)\s*(<W[ATH]*[HG]?\d+>)', text)
    if quint_consecutive:
        uncovered.append(f"Quint consecutive tags: {quint_consecutive[0]}")

    return uncovered


# ── Dimension labels ─────────────────────────────────────────────────────────

DIM_LABELS = {
    1:  "SN count — 簡單短節 (≤8)",
    2:  "SN count — 長節多 SN (>15)",
    3:  "SN count — 重複平行結構",
    4:  "Implicit markers — 基本",
    5:  "Implicit markers — 900x 組合",
    6:  "Morphology — 單動詞",
    7:  "Morphology — 多動詞",
    8:  "格式 — zero-padding (5位 core)",
    9:  "格式 — leading zeros",
    10: "格式 — 900x prefixes",
    11: "格式 — 複合介系詞",
    12: "格式 — WAH 非 900x",
    13: "位置 — SN 在中文字後 (正常)",
    14: "位置 — Morphology 緊跟動詞 SN",
    15: "位置 — 900x prefix 在 core 前",
    16: "邊界 — 4位 09 陷阱",
    17: "格式 — 同號不同 prefix",
    18: "三連續 — 同組 (900x+core+morph)",
    19: "三連續 — 跨組邊界 (前組尾+後組頭)",
    20: "四連續 — 雙動詞 morph 跨組 (v+m|v+m)",
    21: "四連續 — 動詞 morph+其他 跨組 (v+m|…)",
    22: "四連續 — 介系詞/prefix 連串跨組",
    23: "Ketiv/Qere — 連續雙 morph 無 core SN",
    24: "數目字 SN 連串 (≥4 純 WH core 連續)",
    25: "FHL 資料異常 (6+ 位數 SN)",
}


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
        description="Analyze UNV+SN verses for 17 test dimensions (no LLM calls)")
    # Same CLI args as llm_direct_sn_unv2notyet.py
    parser.add_argument("--chineses", "--book", default="創", dest="book",
                        help="Chinese book abbreviation (e.g., 創 出 詩)")
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
        # Fetch chap 1 to discover max chapter (rough heuristic: try up to 150)
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
    dim_counts = {i: 0 for i in range(1, 26)}
    dim_verses = {i: [] for i in range(1, 26)}
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
                triggered = [i for i in range(1, 26) if dims[i]]
                print(f"{verse_ref:15s} [{len(tags):2d} tags] "
                      f"dims: {','.join(str(d) for d in triggered)}")

            for i in range(1, 26):
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
    for i in range(1, 26):
        pct = dim_counts[i] / total_verses * 100 if total_verses > 0 else 0
        examples = dim_verses[i][:3]
        example_str = ", ".join(examples) if examples else "none"
        print(f"  #{i:2d} {DIM_LABELS[i]:40s} {dim_counts[i]:3d} ({pct:5.1f}%)  e.g. {example_str}")

    if all_uncovered:
        print(f"\n  {'─'*50}")
        print(f"  UNCOVERED PATTERNS ({len(all_uncovered)}) — candidates for rule 18+")
        print(f"  {'─'*50}")
        for verse_ref, pattern in all_uncovered:
            print(f"    {verse_ref}: {pattern}")
    else:
        print(f"\n  No uncovered patterns found.")


if __name__ == "__main__":
    main()
