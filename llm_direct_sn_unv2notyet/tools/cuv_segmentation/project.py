#!/usr/bin/env python3
"""把 FHL UNV+SN 投影到 kathairo 的詞邊界上，產出詞級 UNV+SN。

    python3 tools/cuv_segmentation/project.py                   # 全本
    python3 tools/cuv_segmentation/project.py --book 01         # 單書
    python3 tools/cuv_segmentation/project.py --boundary fhl    # 邊界策略
    python3 tools/cuv_segmentation/project.py --out PATH

輸出 JSONL，一節一行：

    {"vid":"01001001","book":"創","chap":1,"sec":1,"seg":"union",
     "raw":"起初，神創造天地。",
     "tokens":[{"i":0,"t":"起初","g":0,"sn":["H09002","H07225"],"m":[]},
               {"i":1,"t":"神",  "g":1,"sn":["H0430"],  "m":[]}, ...],
     "notes":[{"t":"就是得的意思","sn":[]}]}

`g` 是 SN 群組序號：同一 `g` 的多個 token 共用該群組的 SN
（例如 FHL 的 `的兒子<WH01121>` 拆成 `的|兒子` 後兩者同群）。
`sn` 為核心 Strong's（H/G + 4~5 位），`m` 為詞形碼（FHL 的 <WT…>）。

邊界策略 `--boundary`：
  union  （預設）FHL ∪ kathairo，最細；`他|的|形像`
  fhl    只用 FHL 邊界，等同不引入 kathairo
  kath   只用 kathairo 邊界，FHL 的 SN 群組可能橫跨數個 token

`seg` 欄記錄該節實際用了哪種：正規化文本不相符時退回 `fhl`（見 --report）。
"""

import argparse
import collections
import json
import re
import sys
from pathlib import Path

from _common import ANNOTATION, FHL_JSON, TAG, load_cuv, norm

BOOKS_JSON = Path(__file__).resolve().parents[3] / "shared/data/books.json"
# <WH01254> / <WAH09002> / <WG4245> → ("H","01254") ；<WTH8804> 為詞形碼
SN_PARTS = re.compile(r"<W(T?)A?([HG])(\d+[a-z]?)>")


# 可掛回正文的短註：恰好 1 個核心 SN，且是「原文是…」「或譯…」這種直譯說明。
# 這類註在說「正文這個詞的原文是 X」，X 的 SN 確實屬於前一個正文詞。
# 排除「就是」類 —— （比拉就是<WAH01931>瑣珥<WH06820>）是編者的地名對照，
# 其 SN 是註本身的字，掛回去會造假。
REATTACH_HINT = ("原文", "或譯")


def split_annotations(txt, reattach=True):
    """移出 （…）/【…】 譯註。回傳 (正文, notes)。

    符合 REATTACH_HINT 條件的短註，其 SN 標籤留在原地（中文移除），
    由 chunk_verse 依一般規則掛給前一個文字段；其餘整段移出存進 notes。
    """
    notes = []

    def repl(m):
        body = m.group(0)[1:-1]
        found = SN_PARTS.findall(body)
        core = [f"{g}{n}" for t, g, n in found if not t]
        morph = [n for t, _g, n in found if t]
        plain = TAG.sub("", body)
        if reattach and len(core) == 1 and any(h in plain for h in REATTACH_HINT):
            return "".join(TAG.findall(body)) or "".join(
                m2.group(0) for m2 in TAG.finditer(body)
            )
        note = {"t": plain, "sn": core}
        if morph:
            note["m"] = morph
        notes.append(note)
        return ""

    return ANNOTATION.sub(repl, txt), notes


def chunk_verse(txt):
    """正文 → ([{text, sn, morph}], orphan_sn, orphan_morph)。

    FHL 的標籤標記其前方文字段的結尾，連續標籤同屬一段。
    純標籤無中文者（`{<WH0853>}`）併入下一段（其 SN 屬於後面的詞）。
    """
    chunks, pos, pending_sn, pending_m = [], 0, [], []
    for m in TAG.finditer(txt):
        run = txt[pos : m.start()]
        pos = m.end()
        tag = m.group(0)
        found = SN_PARTS.findall(tag)
        t, g, n = found[0] if found else ("", "", "")
        if norm(run):
            # 新的一段：先前累積的「往後掛」標籤歸給它
            chunks.append({"text": run, "sn": list(pending_sn), "morph": list(pending_m)})
            pending_sn, pending_m = [], []
        if not n:
            continue
        # 大括號 {<…>} 表示原文有、中文無對應字，依 FHL 慣例往後掛
        # （對照本專案 parser：`{<WH0853>}天<WH08064>` 同組）
        forward = tag.startswith("{")
        bucket_sn = pending_sn if (forward or not chunks) else chunks[-1]["sn"]
        bucket_m = pending_m if (forward or not chunks) else chunks[-1]["morph"]
        (bucket_m if t else bucket_sn).append(n if t else f"{g}{n}")
    tail = txt[pos:]
    if norm(tail):
        chunks.append({"text": tail, "sn": pending_sn, "morph": pending_m})
        pending_sn, pending_m = [], []
    # 節尾的括號標籤沒有後續中文可掛 —— 不硬塞給最後一個詞，另存 orphan
    return [c for c in chunks if norm(c["text"])], pending_sn, pending_m


def project_verse(chunks, cuv_entry, strategy):
    """回傳 (tokens, seg)。tokens = [{"t":文字,"g":群組序,"sn":[…],"m":[…]}]"""
    kept = []  # (正規化字元, 原字元)
    for ci, c in enumerate(chunks):
        for ch in c["text"]:
            n = norm(ch)
            if n:
                kept.append((n, ch, ci))

    fhl_b, off = set(), 0
    for c in chunks:
        off += len(norm(c["text"]))
        fhl_b.add(off)
    total = off

    seg = "fhl"
    bounds = set(fhl_b)
    if cuv_entry and cuv_entry[0] == "".join(k[0] for k in kept):
        kb = set(cuv_entry[1])
        if strategy == "union":
            bounds = fhl_b | kb
        elif strategy == "kath":
            bounds = set(kb)
        seg = "union" if strategy == "union" else strategy
    elif strategy == "kath":
        seg = "fhl"  # 文本不符，無法用 kathairo 邊界

    tokens, start = [], 0
    for b in sorted(bounds | {total}):
        if b <= start:
            continue
        piece = kept[start:b]
        ci = piece[0][2]
        tokens.append(
            {
                "i": len(tokens),
                "t": "".join(p[1] for p in piece),
                "g": ci,
                "sn": chunks[ci]["sn"],
                "m": chunks[ci]["morph"],
            }
        )
        start = b
    return tokens, seg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boundary", choices=("union", "fhl", "kath"), default="union")
    ap.add_argument("--book", help="兩位書卷編號，如 01；省略則全本")
    ap.add_argument("--out", default=None)
    ap.add_argument("--report", action="store_true", help="只印統計，不寫檔")
    ap.add_argument("--no-reattach", action="store_true",
                    help="短註的 SN 不掛回正文，一律存進 notes")
    args = ap.parse_args()

    books = json.loads(BOOKS_JSON.read_text(encoding="utf-8"))
    cuv = load_cuv()
    data = json.loads(FHL_JSON.read_text(encoding="utf-8"))

    out_path = Path(args.out) if args.out else (
        Path(__file__).resolve().parents[2]
        / f"output/_unv_sn_segmented/unv_sn.{args.boundary}.jsonl"
    )
    if not args.report:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fh = out_path.open("w", encoding="utf-8")

    stat = collections.Counter()
    tok_total = tok_with_sn = grp_multi = 0
    for bi, book in enumerate(data["text"]):
        bnum = f"{bi + 1:02d}"
        if args.book and bnum != args.book:
            continue
        meta = books[bi]
        for chap in book["chapters"]:
            for verse in chap["verses"]:
                vid = f"{bnum}{chap['chap']:03d}{verse['sec']:03d}"
                body, notes = split_annotations(verse["txt"], not args.no_reattach)
                chunks, orph_sn, orph_m = chunk_verse(body)
                if not chunks:
                    stat["空節"] += 1
                    continue
                tokens, seg = project_verse(chunks, cuv.get(vid), args.boundary)
                stat[seg] += 1
                stat["節"] += 1
                if notes:
                    stat["含譯註"] += 1
                if orph_sn:
                    stat["節尾孤兒 SN"] += 1
                    stat["孤兒 SN 個數"] += len(orph_sn)
                tok_total += len(tokens)
                tok_with_sn += sum(1 for t in tokens if t["sn"])
                per_g = collections.Counter(t["g"] for t in tokens)
                grp_multi += sum(1 for _g, n in per_g.items() if n > 1)
                if not args.report:
                    rec = {
                        "vid": vid,
                        "book": meta["chi"],
                        "chap": chap["chap"],
                        "sec": verse["sec"],
                        "seg": seg,
                        "raw": TAG.sub("", verse["txt"]),
                        "tokens": tokens,
                    }
                    if notes:
                        rec["notes"] = notes
                    if orph_sn or orph_m:
                        rec["orphan_sn"] = orph_sn
                        if orph_m:
                            rec["orphan_m"] = orph_m
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if not args.report:
        fh.close()
    print(f"邊界策略 {args.boundary}", file=sys.stderr)
    applied = stat.get(args.boundary, 0) if args.boundary != "fhl" else stat["節"]
    print(f"  節 {stat['節']}   套用 {args.boundary} 邊界 {applied}"
          f"   文本不符退回純 FHL {stat['節'] - applied}", file=sys.stderr)
    print(f"  含譯註的節 {stat['含譯註']}", file=sys.stderr)
    print(f"  token {tok_total}   有 SN {tok_with_sn} ({tok_with_sn / tok_total:.1%})",
          file=sys.stderr)
    print(f"  跨多 token 的 SN 群組 {grp_multi}", file=sys.stderr)
    print(f"  節尾孤兒 SN：{stat['節尾孤兒 SN']} 節 / {stat['孤兒 SN 個數']} 個",
          file=sys.stderr)
    if not args.report:
        print(f"  → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
