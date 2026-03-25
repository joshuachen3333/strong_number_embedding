#!/usr/bin/env python3
"""Build Exemplar Library from dim_verse_map.json using 4-dim matrix selection.

For each of the 26 dimensions, selects candidate exemplars using:
  1. Gradient (tag count tiers)
  2. Genre (13 biblical genres)
  3. Purity (fewest co-triggered dims)
  4. Testament (OT/NT)

Rare dims (≤20 total verses) → select all.
Output: exemplar_library.json

Usage:
    python3 build_exemplar_library.py
    python3 build_exemplar_library.py --max-per-grade 2  # 2 per grade×genre
"""

import argparse
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Genre mapping ────────────────────────────────────────────────────────────

GENRE = {}
for b in '創 出 利 民 申'.split(): GENRE[b] = '律法'
for b in '書 士 得 撒上 撒下 王上 王下 代上 代下 拉 尼 斯'.split(): GENRE[b] = '歷史'
for b in '伯 詩 箴 傳 歌'.split(): GENRE[b] = '詩歌智慧'
for b in '賽 耶 哀 結 但 何 珥 摩 俄 拿 彌 鴻 哈 番 該 亞 瑪'.split(): GENRE[b] = '先知'
for b in '太 可 路 約'.split(): GENRE[b] = '福音'
for b in ['徒']: GENRE[b] = '敘事'
for b in '羅 林前 林後 加 弗 腓 西 帖前 帖後 門'.split(): GENRE[b] = '保羅書信'
for b in '提前 提後 多'.split(): GENRE[b] = '教牧書信'
for b in '彼前 彼後'.split(): GENRE[b] = '彼得書信'
for b in '約一 約二 約三'.split(): GENRE[b] = '約翰書信'
for b in ['雅']: GENRE[b] = '雅各書信'
for b in '來 猶'.split(): GENRE[b] = '其他書信'
for b in ['啟']: GENRE[b] = '啟示'

OT_GENRES = ['律法', '歷史', '詩歌智慧', '先知']
NT_GENRES = ['福音', '敘事', '保羅書信', '教牧書信', '彼得書信', '約翰書信', '雅各書信', '其他書信', '啟示']
ALL_GENRES = OT_GENRES + NT_GENRES

# ── Grade definitions per dim ────────────────────────────────────────────────

# Each dim has its own tag-count grade tiers
# Format: list of (grade_name, lo, hi)
DIM_GRADES = {
    1:  [('A 極短', 2, 4), ('B 中短', 5, 6), ('C 邊界', 7, 8)],
    2:  [('A 入門', 16, 20), ('B 中等', 21, 25), ('C 較長', 26, 30), ('D 很長', 31, 40), ('E 極長', 41, 99)],
    3:  [('A 短節', 3, 10), ('B 中節', 11, 20), ('C 長節', 21, 35), ('D 極長', 36, 99)],
    4:  [('A 少量', 3, 10), ('B 中等', 11, 20), ('C 多', 21, 35), ('D 密集', 36, 99)],
    5:  [('A 少量', 5, 12), ('B 中等', 13, 20), ('C 多', 21, 30), ('D 密集', 31, 99)],
    6:  [('A 極短', 2, 6), ('B 短', 7, 12), ('C 中', 13, 20), ('D 長', 21, 99)],
    7:  [('A 少morph', 8, 14), ('B 中等', 15, 22), ('C 多morph', 23, 35), ('D 密集', 36, 99)],
    8:  [('A 少', 3, 10), ('B 中', 11, 18), ('C 多', 19, 28), ('D 密集', 29, 99)],
    9:  [('A 少', 3, 10), ('B 中', 11, 18), ('C 多', 19, 28), ('D 密集', 29, 99)],
    10: [('A 少', 5, 12), ('B 中', 13, 20), ('C 多', 21, 30), ('D 密集', 31, 99)],
    11: [('A 少', 5, 12), ('B 中', 13, 20), ('C 多', 21, 30), ('D 密集', 31, 99)],
    12: [('A 少', 3, 10), ('B 中', 11, 18), ('C 多', 19, 28), ('D 密集', 29, 99)],
    13: None,  # Special: pick normal + anomaly
    14: [('A 少', 5, 12), ('B 中', 13, 20), ('C 多', 21, 30), ('D 密集', 31, 99)],
    15: [('A 少', 5, 12), ('B 中', 13, 20), ('C 多', 21, 30), ('D 密集', 31, 99)],
    16: [('A 少', 3, 12), ('B 中', 13, 22), ('C 多', 23, 35), ('D 密集', 36, 99)],
    17: None,  # Rare-ish (405), custom grouping
    18: [('A 少', 8, 15), ('B 中', 16, 24), ('C 多', 25, 35), ('D 密集', 36, 99)],
    19: [('A 少', 8, 16), ('B 中', 17, 26), ('C 多', 27, 40), ('D 密集', 41, 99)],
    20: None,  # Rare (132), no grading
    21: None,  # Rare (309), custom grouping
    22: None,  # Very rare (14), select all
    23: None,  # Rare (142), custom grouping
    24: None,  # Very rare (11), select all
    25: None,  # Very rare (2), select all
    26: [('A 少', 5, 14), ('B 中', 15, 24), ('C 多', 25, 40), ('D 密集', 41, 99)],
}

# Dims that are OT-only
OT_ONLY_DIMS = {5, 10, 15, 16, 18, 23, 24}
# Dims that are NT-only
NT_ONLY_DIMS = {26}
# Very rare dims → select all
SELECT_ALL_DIMS = {22, 24, 25}

RARE_THRESHOLD = 20  # dims with ≤ this many verses → select all


def select_for_dim(dim, verses, max_per_grade_genre=1):
    """Select exemplar candidates for one dimension.

    Returns list of selected verse dicts with added 'genre' and 'grade' fields.
    """
    # Filter verses that trigger this dim
    pool = [v for v in verses if dim in v['dims']]

    # Add genre
    for v in pool:
        v['_genre'] = GENRE.get(v['book_chi'], '?')

    # Very rare → select all
    if dim in SELECT_ALL_DIMS or len(pool) <= RARE_THRESHOLD:
        for v in pool:
            v['_grade'] = 'ALL'
        return pool

    # Determine applicable genres
    if dim in OT_ONLY_DIMS:
        genres = OT_GENRES
    elif dim in NT_ONLY_DIMS:
        genres = NT_GENRES
    else:
        genres = ALL_GENRES

    grades = DIM_GRADES.get(dim)

    # Special dims without standard grading
    if grades is None:
        # For rare-ish dims (#17, #20, #21, #23): group by OT/NT, pick purest per genre
        selected = []
        for genre in genres:
            g_pool = [v for v in pool if v['_genre'] == genre]
            if not g_pool:
                continue
            g_pool.sort(key=lambda v: (len(v['dims']), v['tag_count']))
            for v in g_pool[:max_per_grade_genre * 2]:  # take more for ungrouped
                v['_grade'] = 'ungrouped'
                selected.append(v)
        return selected

    # Standard graded selection
    selected = []
    for grade_name, lo, hi in grades:
        grade_pool = [v for v in pool if lo <= v['tag_count'] <= hi]
        for genre in genres:
            g_pool = [v for v in grade_pool if v['_genre'] == genre]
            if not g_pool:
                continue
            # Sort by purity (fewest dims), then tag count
            g_pool.sort(key=lambda v: (len(v['dims']), v['tag_count']))
            for v in g_pool[:max_per_grade_genre]:
                v['_grade'] = grade_name
                selected.append(v)

    # Special for dim #13: also add anomaly verses (NOT triggering #13)
    if dim == 13:
        anomalies = [v for v in verses if 13 not in v['dims'] and v['tag_count'] >= 2]
        for v in anomalies:
            v['_genre'] = GENRE.get(v['book_chi'], '?')
        anomalies.sort(key=lambda v: (len(v['dims']), v['tag_count']))
        for v in anomalies[:6]:
            v['_grade'] = 'ANOMALY'
            selected.append(v)

    return selected


def main():
    parser = argparse.ArgumentParser(
        description="Build Exemplar Library using 4-dim matrix selection")
    parser.add_argument("--max-per-grade-genre", type=int, default=1,
                        help="Max candidates per grade×genre cell (default: 1)")
    parser.add_argument("--map", default=os.path.join(SCRIPT_DIR, "dim_verse_map.json"))
    parser.add_argument("--out", default=os.path.join(SCRIPT_DIR, "exemplar_library.json"))
    args = parser.parse_args()

    with open(args.map, encoding="utf-8") as f:
        data = json.load(f)

    verses = data["verses"]
    all_dims = sorted(int(d) for d in data["by_dimension"].keys())

    library = {}
    total_candidates = 0

    for dim in all_dims:
        selected = select_for_dim(dim, verses, args.max_per_grade_genre)

        # Deduplicate by ref
        seen = set()
        deduped = []
        for v in selected:
            if v['ref'] not in seen:
                seen.add(v['ref'])
                deduped.append({
                    "ref": v["ref"],
                    "book": v["book"],
                    "book_chi": v["book_chi"],
                    "chap": v["chap"],
                    "sec": v["sec"],
                    "testament": v["testament"],
                    "tag_count": v["tag_count"],
                    "dims": v["dims"],
                    "genre": v["_genre"],
                    "grade": v["_grade"],
                    "purity": len(v["dims"]),
                })
                seen.add(v['ref'])

        library[str(dim)] = {
            "dim": dim,
            "label": data["by_dimension"][str(dim)]["label"],
            "total_in_dim": data["by_dimension"][str(dim)]["count"],
            "candidates": len(deduped),
            "verses": deduped,
        }
        total_candidates += len(deduped)

        print(f"  #{dim:2d} {data['by_dimension'][str(dim)]['label']:45s} "
              f"{len(deduped):3d} candidates (from {data['by_dimension'][str(dim)]['count']:5d})")

    # Summary
    all_refs = set()
    for d_info in library.values():
        for v in d_info["verses"]:
            all_refs.add(v["ref"])

    output = {
        "meta": {
            "total_candidates": total_candidates,
            "unique_verses": len(all_refs),
            "max_per_grade_genre": args.max_per_grade_genre,
            "generated": "2026-03-25",
        },
        "library": library,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=1)

    print(f"\n  Total: {total_candidates} candidates, {len(all_refs)} unique verses")
    print(f"  Saved to {args.out}")


if __name__ == "__main__":
    main()
