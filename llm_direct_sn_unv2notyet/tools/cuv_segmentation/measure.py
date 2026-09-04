#!/usr/bin/env python3
"""重現 CUV_SEGMENTATION_CONTRIBUTION.md 的全部數字。

    python3 tools/cuv_segmentation/measure.py            # 全部
    python3 tools/cuv_segmentation/measure.py text       # 只跑 §2 文本比對
    python3 tools/cuv_segmentation/measure.py boundary   # 只跑 §4 邊界一致度
    python3 tools/cuv_segmentation/measure.py overmerge  # 只跑 §5 過度合併分類

執行時間約 3 分鐘（載入 FHL JSON 與 70 萬列 TSV）。
"""

import collections
import csv
import re
import sys

from _common import (ANNOTATION, CUV_DIR, TAG, comparable, load_cuv,
                     load_fhl, norm, strip_cuv_annotations)


def section_text(fhl, raw, cuv_text):
    print("=" * 68)
    print("§2  文本比對")
    same_strict = same_variant = substantive = 0
    examples = []
    for vid, (_, _) in fhl.items():
        if vid not in cuv_text:
            continue
        f_strict = norm(TAG.sub("", ANNOTATION.sub("", raw[vid])), variants=False)
        k_strict = norm(ANNOTATION.sub("", cuv_text[vid]), variants=False)
        if f_strict == k_strict:
            same_strict += 1
            continue
        if norm(TAG.sub("", ANNOTATION.sub("", raw[vid]))) == norm(
            ANNOTATION.sub("", cuv_text[vid])):
            same_variant += 1
            continue
        substantive += 1
        if len(examples) < 6:
            a = norm(TAG.sub("", ANNOTATION.sub("", raw[vid])))
            b = norm(ANNOTATION.sub("", cuv_text[vid]))
            i = next(
                (i for i in range(min(len(a), len(b))) if a[i] != b[i]),
                min(len(a), len(b)),
            )
            examples.append((vid, a[max(0, i - 6) : i + 12], b[max(0, i - 6) : i + 12]))
    print(f"  完全相同          {same_strict}")
    print(f"  僅異體字差        {same_variant}")
    print(f"  實質差異          {substantive}")
    for e in examples:
        print(f"     {e[0]}  FHL…{e[1]}  |  CUV…{e[2]}")

    all_f = "".join(TAG.sub("", t) for t in raw.values())
    all_k = "".join(cuv_text.values())
    print("\n  用字：")
    for ch in ("神", "上帝", "著", "着", "裡", "裏"):
        print(f"     {ch:<3} FHL {all_f.count(ch):>6}   CUV {all_k.count(ch):>6}")

    extra = sorted(set(cuv_text) - set(fhl))
    missing = sorted(set(fhl) - set(cuv_text))
    print(f"\n  只在 CUV 的節 {len(extra)}  例 {extra[:4]}")
    print(f"  只在 FHL 的節 {len(missing)}  例 {missing[:4]}")


def section_tokens():
    print("=" * 68)
    print("§3  CUV 詞元規模")
    total = punct = 0
    lens = collections.Counter()
    for name in ("ot_CUV.tsv", "nt_CUV.tsv"):
        with (CUV_DIR / name).open(encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                total += 1
                if row["exclude"] == "y":
                    punct += 1
                    continue
                t = norm(row["text"])
                if t:
                    lens[len(t)] += 1
    print(f"  列數 {total}（標點 exclude=y {punct}）  實詞詞元 {sum(lens.values())}")
    print("  詞元字數分佈:", dict(sorted(lens.items())))


def section_boundary(fhl, cuv):
    print("=" * 68)
    print("§4  邊界一致度")
    fb = kb = inter = ktok = verses = 0
    for _vid, bounds_in, spans in comparable(fhl, cuv):
        verses += 1
        ktok += len(spans)
        end = spans[-1][1]
        kb_in = {e for _s, e, _t in spans if e < end}
        fb += len(bounds_in)
        kb += len(kb_in)
        inter += len(bounds_in & kb_in)
    print(f"  可比節 {verses}   kathairo 詞元 {ktok}")
    print(f"  FHL 邊界 {fb}   kathairo 邊界 {kb}   交集 {inter}")
    print(f"  recall    {inter / fb:.1%}  (FHL 邊界被 kathairo 命中)")
    print(f"  precision {inter / kb:.1%}  (kathairo 邊界也是 FHL 邊界)")


def section_overmerge(fhl, cuv):
    print("=" * 68)
    print("§5  過度合併：集中度、一致性、分類")
    occ = collections.Counter()
    bad = collections.Counter()
    cutpos = collections.defaultdict(collections.Counter)
    clean = 0
    attach = collections.Counter()
    attach_ex = collections.defaultdict(collections.Counter)
    ktok = 0

    for _vid, bounds_in, spans in comparable(fhl, cuv):
        ktok += len(spans)
        for s, e, t in spans:
            occ[t] += 1
            inner = [b for b in bounds_in if s < b < e]
            if not inner:
                continue
            bad[t] += 1
            cutpos[t][tuple(b - s for b in inner)] += 1
            # 詞元結尾也是 FHL 邊界 → 乾淨切分；否則 → 歸屬不一致
            if e in bounds_in or e == spans[-1][1]:
                clean += 1
            else:
                head = t[inner[-1] - s]
                if head in "的地得":
                    key = "結構助詞 的/地/得"
                elif head in "給在到成出上下來去":
                    key = f"動補/介詞 {head}"
                else:
                    key = "其他（功能詞+代詞/名詞）"
                attach[key] += 1
                attach_ex[key][t] += 1

    tot_bad = sum(bad.values())
    print(f"  詞元 {ktok}   含 FHL 內部邊界 {tot_bad} ({tot_bad / ktok:.2%})")
    print(f"  相異詞元型 {len(occ)}   曾被判過度合併的型 {len(bad)}")
    srt = bad.most_common()
    for k in (50, 200, 500, 1000, 2000, len(srt)):
        if k <= len(srt):
            c = sum(n for _t, n in srt[:k])
            print(f"     前 {k:>5} 型覆蓋 {c:>6}/{tot_bad} = {c / tot_bad:5.1%}")
    always = sum(1 for t, n in bad.items() if occ[t] == n)
    onecut = sum(1 for t in bad if len(cutpos[t]) == 1)
    print(f"  每次出現都該切的型 {always}/{len(bad)} ({always / len(bad):.0%})")
    print(f"  切點唯一的型       {onecut}/{len(bad)} ({onecut / len(bad):.0%})")
    print("\n  高頻型（型 / 該切 / 總出現 / 切點）:")
    for t, n in srt[:12]:
        print(f"     {t:<8} {n:>4}/{occ[t]:<5} {dict(cutpos[t])}")

    tot_at = sum(attach.values())
    print(f"\n  乾淨切分   {clean} ({clean / tot_bad:.1%})")
    print(f"  歸屬不一致 {tot_at} ({tot_at / tot_bad:.1%})，細分：")
    agg = 0
    for k, n in attach.most_common():
        if k.startswith("動補"):
            agg += n
            continue
        ex = [w for w, _ in attach_ex[k].most_common(6)]
        print(f"     {k:<22} {n:>5} ({n / tot_at:5.1%})  {ex}")
    print(f"     {'動補/介詞（合計）':<22} {agg:>5} ({agg / tot_at:5.1%})")


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else "all"
    fhl, raw = load_fhl()
    cuv = load_cuv()
    if want in ("all", "text"):
        cuv_text = collections.defaultdict(str)
        for name in ("ot_CUV.tsv", "nt_CUV.tsv"):
            with (CUV_DIR / name).open(encoding="utf-8") as f:
                for row in csv.DictReader(f, delimiter="\t"):
                    cuv_text[row["id"][:8]] += row["text"]
        section_text(fhl, raw, cuv_text)
    if want in ("all", "tokens"):
        section_tokens()
    if want in ("all", "boundary"):
        section_boundary(fhl, cuv)
    if want in ("all", "overmerge"):
        section_overmerge(fhl, cuv)


if __name__ == "__main__":
    main()
