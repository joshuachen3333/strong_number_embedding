#!/usr/bin/env python3
"""text-align 的 CUV 對齊能還原多少 FHL SN？

只有 3 章對齊存在（太 5、約貳 1、約參 1），所以這是抽樣而非全本結論。
做法：CUV 詞元 --對齊--> SBLGNT token --> Strong's，與 FHL 同節的核心 SN 比對。
FHL 的 <WT…> 是詞形碼（morphology）不是 SN，予以排除。

    python3 tools/cuv_segmentation/sn_check.py
"""

import collections
import csv
import glob
import json
import re

from _common import ROOT, load_fhl

TA = ROOT / "llm_direct_sn_unv2notyet/text-align"
CORE_SN = re.compile(r"<W[A-Z]*?G(\d+)[a-z]?>")


def main():
    _bounds, raw = load_fhl()

    sbl = {}
    with (TA / "data/sources/SBLGNT.tsv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            sbl[row["id"].lstrip("n")] = int(re.sub(r"\D", "", row["strongs"]))

    cuv_rows = collections.defaultdict(list)
    with (
        TA / "data/alignments/alignments-cmn/data/targets/CUV/nt_CUV.tsv"
    ).open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            cuv_rows[row["id"][:8]].append(row)

    pattern = str(TA / "data/alignments/alignments-cmn/exp/CUV/LLM-REFINED/*.json")
    tot_f = tot_a = tot_i = tot_tok = tot_hit = 0
    print(f"{'chapter':<34}{'verses':>7}{'FHL':>7}{'align':>7}{'∩':>7}"
          f"{'recall':>9}{'prec':>8}{'詞元有SN':>12}")
    for path in sorted(glob.glob(pattern)):
        group = json.loads(open(path, encoding="utf-8").read())["groups"][0]
        per_verse = collections.defaultdict(collections.Counter)
        tok_sn = collections.defaultdict(set)
        for rec in group["records"]:
            sns = [sbl[s] for s in rec["source"] if s in sbl]
            for t in rec["target"]:
                per_verse[t[:8]].update(sns)
                tok_sn[t].update(sns)

        vf = va = vi = 0
        for vid, aligned in per_verse.items():
            fhl_sn = collections.Counter(
                int(m.group(1))
                for m in CORE_SN.finditer(raw.get(vid, ""))
                if "WT" not in m.group(0)
            )
            vf += sum(fhl_sn.values())
            va += sum(aligned.values())
            vi += sum((fhl_sn & aligned).values())

        ntok = sum(
            1 for vid in per_verse for r in cuv_rows[vid] if r["exclude"] != "y"
        )
        nhit = sum(
            1
            for vid in per_verse
            for r in cuv_rows[vid]
            if r["exclude"] != "y" and tok_sn.get(r["id"])
        )
        tot_f += vf; tot_a += va; tot_i += vi; tot_tok += ntok; tot_hit += nhit
        print(f"{path.split('/')[-1]:<34}{len(per_verse):>7}{vf:>7}{va:>7}{vi:>7}"
              f"{vi / vf:>8.1%}{vi / va:>8.1%}{nhit}/{ntok:<6} ({nhit / ntok:.0%})")

    print(f"{'合計':<34}{'':>7}{tot_f:>7}{tot_a:>7}{tot_i:>7}"
          f"{tot_i / tot_f:>8.1%}{tot_i / tot_a:>8.1%}"
          f"{tot_hit}/{tot_tok:<6} ({tot_hit / tot_tok:.0%})")
    print("\nprecision 偏低是預期的：對齊會把冠詞 G3588 與 secondary 一併掛上，FHL 不標。")


if __name__ == "__main__":
    main()
