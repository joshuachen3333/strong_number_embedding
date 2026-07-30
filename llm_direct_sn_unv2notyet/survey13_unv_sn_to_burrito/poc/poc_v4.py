"""PoC v4: UNV+SN → WLC 對齊(Strong-number JOIN)。

v4 相對 v3 的兩個改變
─────────────────────
1. **變體表改查 FHL 自己的 qb↔qp,不再自學。**
   v3 用「殘差共現 + lift」統計學出 3212→1980 之類的等價對,8 條中 3 條是
   詞尾碎片雜訊。但這個分歧其實**存在於 FHL 內部**——qb.php 用 3212、
   qp.php 用 1980——而 SPECIFICATION_v1.9(v1.7.2 起)早已規定:
       「當 qb 與 qp 使用不同 SN 時,自動使用 qp 的 SN」
   v4 直接把該規則具體化成對照表:只採「該節恰有 1 個 qb-only core 且恰有
   1 個 qp-only core」的無歧義配對,因此不需要 lift 之類的統計啟發式。
   (詳見 ../FHL_900X_FINDINGS.md § 二之二)

2. **書卷不再寫死創世記。** `--book` 收中文或英文代碼,經 shared/data/books.json
   解析,BCV 前綴自動推導。全程走本地 SQLite,零 API 呼叫。

用法
────
    python3 poc_v4.py --book 創 --chaps 1
    python3 poc_v4.py --book 創 --chaps 1-50 --emit-json gen.json
    python3 poc_v4.py --book Dan --chaps 7          # 驗證 09004 跨卷案例
"""
import sys, re, json, argparse, io, sqlite3, warnings
from collections import defaultdict, Counter

ROOT = "/Users/joshua/work/strong_number_embedding"
sys.path.insert(0, f"{ROOT}/llm_direct_sn_unv2notyet/Alignments")
warnings.filterwarnings("ignore")
from bible_alignments.burrito import AlignmentSet, Manager, DATAPATH

QB_DB  = f"{ROOT}/original_text_preparation/source_sqlite/bible_little.db"    # UNV+SN
QP_DB  = f"{ROOT}/original_text_preparation/source_sqlite/bible_parsing.db"   # 解析/構形
BOOKS  = f"{ROOT}/shared/data/books.json"

# FHL 900x 前綴碼 → Macula(WLC.tsv)詞素 strong,供前綴依值配對。
# 來源:SPECIFICATION_v1.9 §5.1 + 本 survey 全庫實證(../FHL_900X_FINDINGS.md)。
# 規格那張表**不完整**——它是文件性的,parser 從不查它(900x 純以「5 位數且 09
# 開頭」的結構規則判定),故缺漏長期未被發現。讀那張表的下游都須自行補齊。
SEED = {
    # --- 規格 §5.1 已列 ---
    "09001": "3807",   # ל־   qb 21,023 · qp 4,423
    "09002": "871",    # ב־   qb 15,754 · qp 1,359
    "09003": "3509",   # כ־   qb  2,933 · qp    17
    "09005": "3807",   # ל־   規格列為 09001 的 alias;qb 0 · qp 27
    "09006": "4480",   # מ־   qb/qp 皆 0 —— FHL 實際改用一般 Strong <04480>
    "09009": "1886",   # ה־   qb/qp 皆 0 —— FHL 幾乎不標定冠詞
    # --- 規格未列,本 survey 實證補入 ---
    "09004": "3807",   # ל־   qb 1(但 7:12)· qp 59;qp orig=לְ,WLC 對應 A3807b
    "09013": "3807",   # ל־+動詞不定詞附屬形  qb 0 · qp 170(合併碼,僅取前綴部)
}
# 09014(qp 1,962)與 09015(qp 1,164)同為段落符號,皆不出現於 qb,故不入本表。
PARAGRAPH_CODES = {"9014", "9015"}


# ── 書卷 ─────────────────────────────────────────────────────────────────────
def load_books():
    """→ {key: (num, chi, eng)};key 同時收中文與英文代碼(英文不分大小寫)。"""
    m = {}
    for i, b in enumerate(json.load(open(BOOKS, encoding="utf-8")), start=1):
        rec = (i, b["chi"], b["eng"])
        m[b["chi"]] = rec
        m[b["eng"].lower()] = rec
    return m


# ── SN 解析 ──────────────────────────────────────────────────────────────────
def norm_num(s):
    m = re.search(r"(\d+)", s or "")
    return str(int(m.group(1))) if m else None


def classify(letters, digits):
    """SPEC v1.9 §2.1/§3.2:900x 只看數字(5 位且 09 開頭),**不看字母前綴**。

    實測依據:09001 同時以 <WAH09001>(21,020)與 <WH09001>(3)出現,
    09004 則僅以 <WH09004> 出現。以字母前綴判定會漏掉 4 個 token。
    """
    if len(digits) == 5 and digits.startswith("09"):
        return "prefix"
    if "T" in letters:
        return "morph"
    return "core"


def parse_unv(text):
    """→ [(中文詞, kind, 純數字, 五位數字)]"""
    out = []
    for word, tags in re.findall(r"([一-鿿]+)((?:\{?<W[ATH]*\d+>\}?)+)", text):
        for m in re.finditer(r"<W([ATH]*)(\d+)>", tags):
            L, D = m.group(1), m.group(2)
            out.append((word, classify(L, D), str(int(D)), D.zfill(5)))
    return out


# ── 變體表:查 FHL 自己的 qb ↔ qp(取代 v3 的自學)───────────────────────────
def _verse_sn_sets():
    """→ (qb_counter_by_verse, qp_counter_by_verse);皆已濾掉 morph/900x/段落符號。"""
    qb, qp = sqlite3.connect(QB_DB), sqlite3.connect(QP_DB)
    qbv = {}
    for e, ch, se, txt in qb.execute("SELECT engs,chap,sec,txt FROM unv"):
        c = Counter()
        for m in re.finditer(r"<W([ATH]*)(\d+)>", txt or ""):
            if "T" in m.group(1):
                continue                                   # morph 不參與
            d = m.group(2)
            if len(d) == 5 and d.startswith("09"):
                continue                                   # 900x 是顆粒度差異,非變體
            c[str(int(d))] += 1
        qbv[(e, ch, se)] = c
    qpv = defaultdict(Counter)
    for e, ch, se, wid, sn in qp.execute("SELECT engs,chap,sec,wid,sn FROM lparsing"):
        if wid == 0:                                       # wid=0 為全節總覽列
            continue
        if sn and len(sn) == 5 and sn.startswith("09"):
            continue
        n = norm_num(sn)
        if n and n not in PARAGRAPH_CODES:
            qpv[(e, ch, se)][n] += 1
    return qbv, qpv


def build_variant_map(min_n=3, min_share=0.60, verbose=True):
    """把 SPEC 的「qb≠qp 時以 qp 為準」具體化成 qb_sn → qp_sn 對照表。

    只採無歧義的 1:1 殘差(該節恰 1 個 qb-only、恰 1 個 qp-only),
    故不需 lift 之類的統計啟發式。
    """
    qbv, qpv = _verse_sn_sets()
    pairs = defaultdict(Counter)
    for k, a in qbv.items():
        b = qpv.get(k)
        if not b:
            continue
        only_qb = list((a - b).elements())
        only_qp = list((b - a).elements())
        if len(only_qb) == 1 and len(only_qp) == 1:
            pairs[only_qb[0]][only_qp[0]] += 1

    vmap, rows = {}, []
    for src, c in pairs.items():
        tgt, n = c.most_common(1)[0]
        share = n / sum(c.values())
        if n >= min_n and share >= min_share:
            vmap[src] = tgt
            rows.append((src, tgt, n, share))
    if verbose:
        print("\n--- 變體對照表(來源:FHL 自己的 qb↔qp,非自學)---")
        print(f"    {len(vmap)} 條 · 門檻 n>={min_n} 且一致性>={min_share:.0%} · 僅採無歧義 1:1 殘差")
        print(f"    {'qb':>6} → {'qp':>6} {'次數':>7} {'一致性':>8}")
        for src, tgt, n, share in sorted(rows, key=lambda x: -x[2])[:15]:
            print(f"    {src:>6} → {tgt:>6} {n:>7,} {share*100:>7.0f}%")
        if len(rows) > 15:
            print(f"    …另 {len(rows)-15} 條")
    return vmap


# ── 對齊 ─────────────────────────────────────────────────────────────────────
def align_verse(bcv, unv_text, sources, stats, records, vmap, unmatched, unmatched_eg):
    unv = parse_unv(unv_text)
    parts = [(s.id, norm_num(s.strong), s.id[8:11]) for s in sources]
    occ, used, prefix_buf, tgt_i = defaultdict(int), set(), [], 0

    for (cw, kind, num, d5) in unv:
        stats[f"unv_{kind}"] += 1
        if kind == "morph":
            stats["morph_skipped"] += 1
            continue
        if kind == "prefix":
            prefix_buf.append(d5)
            continue

        tgt_i += 1
        tgt_id = f"{bcv}{tgt_i:03d}"
        hit, via_variant = None, False
        for idx, cand in enumerate([num] + ([vmap[num]] if num in vmap else [])):
            pool = [i for i, p in enumerate(parts) if p[1] == cand]
            k = occ[cand]
            if k < len(pool):
                occ[cand] += 1
                hit, via_variant = pool[k], bool(idx)
                break

        if hit is None:
            stats["core_unmatched"] += 1
            unmatched[num] += 1
            unmatched_eg.setdefault(num, (cw, bcv))
            # Burrito 慣例:未對齊的 token **不建 record**(見 ../BURRITO_FORMAT.md)
            prefix_buf = []
            continue

        used.add(hit)
        stats["core_matched_via_variant" if via_variant else "core_matched"] += 1
        src_ids = [parts[hit][0]]
        core_www = parts[hit][2]
        sib = sorted(((i, p) for i, p in enumerate(parts)
                      if p[2] == core_www and i != hit and i not in used),
                     key=lambda x: x[1][0])
        for pd5 in prefix_buf:                       # 依 SEED 值配對,退回位置
            want = SEED.get(pd5)
            pick = (next((t for t in sib if t[1][1] == want and t[0] not in used), None)
                    or next((t for t in sib if t[0] not in used), None))
            if pick:
                used.add(pick[0])
                src_ids.insert(0, pick[1][0])
                stats["prefix_matched"] += 1
            else:
                stats["prefix_overflow"] += 1
        records.append({"source": [f"o{i}" for i in src_ids],
                        "target": [tgt_id],
                        "meta": {"id": f"{bcv}.{tgt_i:03d}",
                                 "origin": "strongjoin", "status": "created"}})
        prefix_buf = []


# ── 主流程 ───────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="UNV+SN → WLC Burrito 對齊 PoC v4")
    ap.add_argument("--book", default="創", help="中文或英文書卷代碼(創 / Gen / Dan)")
    ap.add_argument("--chaps", default="1", help="1 或 1-50")
    ap.add_argument("--emit-json", default="", help="輸出 Burrito alignment JSON")
    a = ap.parse_args()

    books = load_books()
    key = a.book if a.book in books else a.book.lower()
    if key not in books:
        sys.exit(f"未知書卷:{a.book}")
    bnum, chi, eng = books[key]
    if bnum > 39:
        sys.exit(f"{eng} 屬新約;本 PoC 目前只支援舊約(來源 WLC.tsv)")

    lo, hi = a.chaps.split("-") if "-" in a.chaps else (a.chaps, a.chaps)
    chaps = range(int(lo), int(hi) + 1)

    print("=" * 74)
    print(f"PoC v4 — {chi}({eng},卷 {bnum:02d}) 第 {a.chaps} 章   sourceid=WLC   全程離線")
    print("=" * 74)

    vmap = build_variant_map()

    _o = sys.stdout
    sys.stdout = io.StringIO()                      # Manager 會噴大量 badrecord 警告
    mgr = Manager(AlignmentSet(sourceid="WLC", targetid="YLT", targetlanguage="eng",
                               langdatapath=DATAPATH / "eng",
                               sourcedatapath=DATAPATH / "sources"))
    sys.stdout = _o

    qb = sqlite3.connect(QB_DB)
    stats, records, nv = Counter(), [], 0
    unmatched, unmatched_eg = Counter(), {}
    for ch in chaps:
        for sec, txt in qb.execute(
                "SELECT sec,txt FROM unv WHERE engs=? AND chap=? ORDER BY sec", (eng, ch)):
            bcv = f"{bnum:02d}{ch:03d}{sec:03d}"
            if bcv not in mgr:
                continue
            align_verse(bcv, txt, list(mgr[bcv].sources), stats, records, vmap,
                        unmatched, unmatched_eg)
            nv += 1

    ok = stats["core_matched"] + stats["core_matched_via_variant"]
    tot = ok + stats["core_unmatched"]
    ptot = stats["prefix_matched"] + stats["prefix_overflow"]
    print("\n--- 結果 ---")
    print(f"  節數 {nv:,}   對齊 record {len(records):,}")
    print(f"  核心   {ok:,}/{tot:,} = {100*ok/max(tot,1):.1f}%"
          f"   (原號 {stats['core_matched']:,} · 變體 {stats['core_matched_via_variant']:,}"
          f" · 未對 {stats['core_unmatched']:,})")
    print(f"  前綴   {stats['prefix_matched']:,}/{ptot:,}"
          f" = {100*stats['prefix_matched']/max(ptot,1):.1f}%"
          f"   morph 略過 {stats['morph_skipped']:,}")
    if unmatched:
        print(f"\n--- 未對上核心 top10(共 {sum(unmatched.values()):,} 個,{len(unmatched)} 種)---")
        for num, c in unmatched.most_common(10):
            cw, bv = unmatched_eg[num]
            print(f"    {num:>6} ×{c:<6} 例 {cw} @ {bv}")
    if a.emit_json:
        json.dump({"documents": [{"docid": "WLC", "scheme": "BCVWP"},
                                 {"docid": "UNV", "scheme": "BCVW"}],
                   "meta": {"conformsTo": "0.3", "creator": "strongjoin-poc-v4"},
                   "roles": ["source", "target"], "type": "translation",
                   "records": records},
                  open(a.emit_json, "w"), ensure_ascii=False, indent=2)
        print(f"\n✅ Burrito JSON: {a.emit_json}  ({len(records):,} records)")


main()
