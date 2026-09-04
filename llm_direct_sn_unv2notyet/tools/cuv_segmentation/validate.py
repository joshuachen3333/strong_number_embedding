#!/usr/bin/env python3
"""驗證 project.py 的輸出：SN 無漏、文本可還原、切分確實變細。

    python3 tools/cuv_segmentation/validate.py [JSONL]

四項檢查：
  1. 文本還原   token 串接 == FHL 原文（去標點空白）
  2. SN 守恆     token.sn ∪ orphan_sn ∪ notes.sn == FHL 原文的全部核心 SN（多重集）
  3. 詞形碼守恆  同上，針對 <WT…>
  4. 切分粒度    對照純 FHL 切分，量化細了多少
"""

import collections
import json
import re
import sys
from pathlib import Path

from _common import ANNOTATION, FHL_JSON, TAG, norm

SN_PARTS = re.compile(r"<W(T?)A?([HG])(\d+[a-z]?)>")

DEFAULT = (
    Path(__file__).resolve().parents[2] / "output/_unv_sn_segmented/unv_sn.union.jsonl"
)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    data = json.loads(FHL_JSON.read_text(encoding="utf-8"))
    raw = {}
    for i, book in enumerate(data["text"]):
        for chap in book["chapters"]:
            for verse in chap["verses"]:
                raw[f"{i + 1:02d}{chap['chap']:03d}{verse['sec']:03d}"] = verse["txt"]

    bad_text = bad_sn = bad_morph = 0
    ex_text, ex_sn = [], []
    n = 0
    tok_total = fhl_groups = 0
    seg_stat = collections.Counter()

    with path.open(encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            n += 1
            vid = rec["vid"]
            src = raw[vid]
            seg_stat[rec["seg"]] += 1

            # 1. 文本還原
            got = "".join(t["t"] for t in rec["tokens"])
            # 譯註已移出正文（保存在 notes），比對時同樣扣除
            want = norm(TAG.sub("", ANNOTATION.sub("", src)), variants=False)
            if norm(got, variants=False) != want:
                bad_text += 1
                if len(ex_text) < 5:
                    ex_text.append((vid, norm(got, variants=False)[:40], want[:40]))

            # 2/3. SN 與詞形碼守恆
            want_sn = collections.Counter()
            want_m = collections.Counter()
            for t, g, num in SN_PARTS.findall(src):
                (want_m if t else want_sn)[num if t else f"{g}{num}"] += 1

            got_sn = collections.Counter()
            got_m = collections.Counter()
            seen_g = set()
            for t in rec["tokens"]:
                if t["g"] in seen_g:
                    continue  # 同群組只計一次（多 token 共用一組 SN）
                seen_g.add(t["g"])
                got_sn.update(t["sn"])
                got_m.update(t["m"])
            got_sn.update(rec.get("orphan_sn", []))
            got_m.update(rec.get("orphan_m", []))
            for note in rec.get("notes", []):
                got_sn.update(note["sn"])
                got_m.update(note.get("m", []))

            if got_sn != want_sn:
                bad_sn += 1
                if len(ex_sn) < 5:
                    ex_sn.append((vid, dict(want_sn - got_sn), dict(got_sn - want_sn)))
            if got_m != want_m:
                bad_morph += 1

            tok_total += len(rec["tokens"])
            fhl_groups += len({t["g"] for t in rec["tokens"]})

    print(f"檔案 {path}")
    print(f"節數 {n}    切分來源 {dict(seg_stat)}")
    print(f"\n1. 文本還原   不符 {bad_text} ({bad_text / n:.2%})")
    for e in ex_text:
        print(f"     {e[0]}  got…{e[1]}  |  want…{e[2]}")
    print(f"2. SN 守恆    不符 {bad_sn} ({bad_sn / n:.2%})")
    for e in ex_sn:
        print(f"     {e[0]}  漏={e[1]}  多={e[2]}")
    print(f"3. 詞形碼守恆 不符 {bad_morph} ({bad_morph / n:.2%})")
    print(f"\n4. 切分粒度   token {tok_total}   FHL 群組 {fhl_groups}"
          f"   → 細化 {tok_total / fhl_groups:.2f}×")


if __name__ == "__main__":
    main()
