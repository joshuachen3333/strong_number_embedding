"""CUV 詞元 vs FHL UNV+SN 隱含切分：共用載入與正規化。

兩份資料：
  FHL  = original_text_preparation/bible_text_json/bible_unv.json（神版，含 SN 標籤）
  CUV  = text-align/data/alignments/alignments-cmn/data/targets/CUV/{ot,nt}_CUV.tsv
         （上帝版，kathairo 產出的逐詞 TSV，無 SN 欄）

四項系統性差異必須先拉平，否則全本 31,103 節沒有一節文本相同：

  1. 神名      FHL 神版、CUV 上帝版          → 上帝 → 神
  2. 異體字    FHL 著/裡、CUV 着/裏          → 統一為 着/裏
  3. 標點空白  兩邊格式不同                   → 一律去除
  4. 內嵌譯註  **兩邊都有，且判定不一致**     → 各自剝除

第 1 項必須對**整串**做，不能逐詞元 —— kathairo 會把「上帝」切斷
（創 5:1 切成 `當上` + `帝`），逐詞元替換抓不到。`normalize_tokens` 負責這件事，
並把落在被合併字串內部的邊界丟掉（那本來就是切分錯誤）。

第 4 項的方向是雙向的：創 14:8 的「比拉就是瑣珥」在 CUV 是正文、在 FHL 是譯註；
創 8:21 的「人從小時心裏懷着惡念」反過來。CUV 的括號是 exclude=y 的標點，
但**括號內的文字是正常詞元**，所以必須靠括號配對來偵測，不能靠 exclude 欄。

FHL 的「隱含切分」定義：每個 SN 標籤標記其前方文字段（run）的結尾，
該位置即一個切分邊界。純標籤無中文者（如 `{<WH0853>}`）不產生邊界。
"""

import collections
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FHL_JSON = ROOT / "original_text_preparation/bible_text_json/bible_unv.json"
CUV_DIR = (
    ROOT
    / "llm_direct_sn_unv2notyet/text-align/data/alignments/alignments-cmn/data/targets/CUV"
)

TAG = re.compile(r"\{?<W[A-Z]*\d+[a-z]?>\}?")
KEEP = re.compile(r"[㐀-䶿一-鿿豈-﫿A-Za-z0-9]")
ANNOTATION = re.compile(r"（[^（）]*）|【[^【】]*】")
VARIANTS = str.maketrans("著裡", "着裏")
DEITY = ("上帝", "神")


def norm(s, variants=True):
    """去標點空白 + 上帝→神 (+ 異體字統一)。整串處理，不可逐字呼叫。"""
    s = "".join(KEEP.findall(s)).replace(*DEITY)
    return s.translate(VARIANTS) if variants else s


def normalize_tokens(tokens):
    """對整串正規化，同時把詞元邊界映射到正規化後的位置。

    回傳 (正規化字串, 邊界集合, [(start, end, 正規化詞元文字), …])。
    邊界落在被合併字串（上帝→神）內部者一律丟棄 —— 那是 kathairo 的切分錯誤。
    """
    joined = "".join(tokens)
    raw_bounds, o = [], 0
    for t in tokens:
        o += len(t)
        raw_bounds.append(o)

    out, raw2norm, i = [], {}, 0
    while i < len(joined):
        raw2norm[i] = len(out)
        if joined.startswith(DEITY[0], i):
            out.append(DEITY[1])
            i += len(DEITY[0])
            continue
        if KEEP.match(joined[i]):
            out.append(joined[i].translate(VARIANTS))
        i += 1
    raw2norm[len(joined)] = len(out)

    bounds, spans, prev = set(), [], 0
    for i, rb in enumerate(raw_bounds):
        if rb not in raw2norm:
            continue  # 邊界落在 上帝 內部，丟棄
        nb = raw2norm[rb]
        bounds.add(nb)
        if nb > prev:
            spans.append((prev, nb, "".join(out[prev:nb])))
            prev = nb
    return "".join(out), bounds, spans


def strip_cuv_annotations(texts):
    """移除 CUV 自己的 （…）/【…】 內嵌譯註，回傳保留下來的詞元索引。

    括號在 TSV 裡是 exclude=y 的標點，括號內的文字卻是正常詞元，
    所以靠括號配對偵測，不能靠 exclude 欄。未配對的括號視為正文，不動。
    """
    drop, stack = set(), []
    for i, t in enumerate(texts):
        if t in "（【":
            stack.append(i)
        elif t in "）】" and stack:
            start = stack.pop()
            drop.update(range(start, i + 1))
    return drop


def load_fhl():
    """回傳 (bounds_by_vid, raw_by_vid)。

    bounds_by_vid[vid] = (set[int] 邊界字元位移, str 正規化後純文字)，
    兩者都已剝除 FHL 的內嵌譯註。

    書卷編號取 JSON 中的正典順序 —— FHL 的 engs 縮寫與 books.json 不一致
    （'Ex' vs 'Exod'、'3 John' vs '3John'），不可用名稱對映。
    """
    data = json.loads(FHL_JSON.read_text(encoding="utf-8"))
    bounds_by_vid, raw_by_vid = {}, {}
    for i, book in enumerate(data["text"]):
        for chap in book["chapters"]:
            for verse in chap["verses"]:
                vid = f"{i + 1:02d}{chap['chap']:03d}{verse['sec']:03d}"
                raw_by_vid[vid] = verse["txt"]
                txt = ANNOTATION.sub("", verse["txt"])

                pos, runs = 0, []
                for m in TAG.finditer(txt):
                    run = txt[pos : m.start()]
                    if run or not runs or runs[-1][1]:
                        runs.append([run, True])
                    else:
                        runs[-1][1] = True
                    pos = m.end()
                if txt[pos:]:
                    runs.append([txt[pos:], False])

                bounds, off = set(), 0
                for run, tagged in runs:
                    n = norm(run)
                    off += len(n)
                    if tagged and n:
                        bounds.add(off)
                bounds_by_vid[vid] = (bounds, norm(TAG.sub("", txt)))
    return bounds_by_vid, raw_by_vid


def load_cuv():
    """回傳 vid → (正規化文本, 邊界集合, spans)。已剝除 CUV 的內嵌譯註。"""
    rows = collections.defaultdict(list)
    for name in ("ot_CUV.tsv", "nt_CUV.tsv"):
        with (CUV_DIR / name).open(encoding="utf-8") as f:
            for row in csv.DictReader(f, delimiter="\t"):
                rows[row["id"][:8]].append(row)

    out = {}
    for vid, rs in rows.items():
        texts = [r["text"] for r in rs]
        drop = strip_cuv_annotations(texts)
        kept = [
            r["text"]
            for i, r in enumerate(rs)
            if i not in drop and r["exclude"] != "y" and r["text"].strip()
        ]
        if not kept:
            continue
        text, bounds, spans = normalize_tokens(kept)
        if text:
            out[vid] = (text, bounds, spans)
    return out


def comparable(fhl, cuv):
    """逐節產出 (vid, FHL 邊界, kathairo spans)，僅限正規化文本完全相同的節。

    句尾邊界排除（兩邊必然一致，計入會虛抬分數）。
    """
    for vid, (bounds, ftxt) in fhl.items():
        entry = cuv.get(vid)
        if not entry or entry[0] != ftxt:
            continue
        _text, _b, spans = entry
        end = spans[-1][1]
        yield vid, {b for b in bounds if b < end}, spans
