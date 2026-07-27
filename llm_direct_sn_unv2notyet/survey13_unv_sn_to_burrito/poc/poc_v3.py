"""PoC v3: UNV+SN -> WLC-UNV Burrito 對齊。

v3 相對 v2 的兩個改變:
1. sourceid 改用 WLC(非壞 schema 的 WLCM)-> 拿到原生 H 前綴 + lemma
2. 用「殘差共現」學習 FHL↔Macula 變體等價表(如 3212≡1980),以 lemma 標註驗證,
   修補 v2 剩下的 3.7% 核心尾巴。
"""
import sys, re, json, argparse, io, warnings
from collections import defaultdict, Counter
sys.path.insert(0, "/Users/joshua/work/strong_number_embedding/llm_direct_sn_unv2notyet")
sys.path.insert(0, "/Users/joshua/work/strong_number_embedding/llm_direct_sn_unv2notyet/Alignments")
warnings.filterwarnings("ignore")
from llm_direct_sn_unv2notyet import fetch_chap
from bible_alignments.burrito import AlignmentSet, Manager, DATAPATH

SEED = {"09001":"3807","09005":"3807","09002":"871","09003":"3509","09009":"1886","09006":"4480"}

def norm_num(s):
    m = re.search(r'(\d+)', s or ""); return str(int(m.group(1))) if m else None

def classify(letters, digits):
    if len(digits) == 5 and digits.startswith('09'): return 'prefix'
    if 'T' in letters:                               return 'morph'
    return 'core'

def parse_unv(text):
    out = []
    for word, tags in re.findall(r'([一-鿿]+)((?:\{?<W[ATH]*\d+>\}?)+)', text):
        for m in re.finditer(r'<W([ATH]*)(\d+)>', tags):
            L, D = m.group(1), m.group(2)
            out.append((word, classify(L, D), str(int(D)), D.zfill(5)))
    return out

def load_wlc_manager():
    """WLC 只有 WLC-YLT 對齊檔;我們只取 .sources,故借 YLT 載入。"""
    _o = sys.stdout; sys.stdout = io.StringIO()
    mgr = Manager(AlignmentSet(sourceid="WLC", targetid="YLT", targetlanguage="eng",
                               langdatapath=DATAPATH/"eng", sourcedatapath=DATAPATH/"sources"))
    sys.stdout = _o
    return mgr

def align_verse(bcv, unv_text, sources, stats, variant_cooc, lemma_of, variant_map):
    unv = parse_unv(unv_text)
    parts = [(s.id, norm_num(s.strong), s.id[8:11], s.lemma, s.text) for s in sources]
    for pid, n, www, lem, txt in parts:
        if n and lem: lemma_of.setdefault(n, lem)
    occ = defaultdict(int); used = set()
    prefix_buf = []; tgt_i = 0
    unmatched_here = []
    for (cw, kind, num, d5) in unv:
        stats[f'unv_{kind}'] += 1
        if kind == 'morph':
            stats['morph_skipped'] += 1; continue
        if kind == 'prefix':
            prefix_buf.append((cw, num, d5)); continue
        tgt_i += 1
        # 先用原號,再用已學到的變體號
        tried = [num] + ([variant_map[num]] if num in variant_map else [])
        hit = None
        for cand_num in tried:
            cands = [i for i, p in enumerate(parts) if p[1] == cand_num]
            k = occ[cand_num]
            if k < len(cands):
                occ[cand_num] += 1; hit = cands[k]; break
        if hit is not None:
            used.add(hit)
            if tried.index(cand_num) > 0: stats['core_matched_via_variant'] += 1
            else:                          stats['core_matched'] += 1
        else:
            stats['core_unmatched'] += 1
            unmatched_here.append(num)
        # 前綴附著(依 SEED 值配對)
        core_www = parts[hit][2] if hit is not None else None
        sib = [(i, p) for i, p in enumerate(parts)
               if core_www and p[2] == core_www and i != hit and i not in used]
        for (pcw, pnum, pd5) in prefix_buf:
            want = SEED.get(pd5)
            pick = next((t for t in sib if t[1][1] == want and t[0] not in used), None) \
                or next((t for t in sib if t[0] not in used), None)
            if pick: used.add(pick[0]); stats['prefix_matched'] += 1
            else:    stats['prefix_overflow'] += 1
        prefix_buf = []
    # 殘差共現:本節未對上的 FHL 號 × 本節未被用掉的 Macula 號
    PARTICLES = {"2050","1886","3807","871","3509","4480","853"}   # ו ה ל ב כ מ את — 高頻虛詞,非變體候選
    leftover = [parts[i][1] for i in range(len(parts))
                if i not in used and parts[i][1] and parts[i][1] not in PARTICLES]
    if unmatched_here and leftover:
        for u in unmatched_here:
            for l in leftover:
                variant_cooc[u][l] += 1
                variant_cooc['__TOTAL__'][l] += 1   # 該 Macula 號當殘差的總次數(供正規化)

def run(chaps, mgr, variant_map, label):
    stats = Counter(); cooc = defaultdict(Counter); lemma_of = {}; nv = 0
    for ch in chaps:
        try: unv_ch = fetch_chap("創", ch, version="unv", strong=1)
        except Exception: continue
        for sec in sorted(unv_ch):
            bcv = f"01{ch:03d}{sec:03d}"
            if bcv not in mgr: continue
            align_verse(bcv, unv_ch[sec], list(mgr[bcv].sources),
                        stats, cooc, lemma_of, variant_map)
            nv += 1
    tot = stats['core_matched'] + stats['core_matched_via_variant'] + stats['core_unmatched']
    ok  = stats['core_matched'] + stats['core_matched_via_variant']
    print(f"\n[{label}] 節數 {nv}  核心 {ok}/{tot} = {100*ok/max(tot,1):.1f}%"
          f"  (原號 {stats['core_matched']}, 變體 {stats['core_matched_via_variant']}, 未對 {stats['core_unmatched']})")
    print(f"           前綴 {stats['prefix_matched']}/{stats['prefix_matched']+stats['prefix_overflow']}"
          f"  morph略過 {stats['morph_skipped']}")
    return stats, cooc, lemma_of

ap = argparse.ArgumentParser(); ap.add_argument("--chaps", default="1-50")
a = ap.parse_args()
lo, hi = (a.chaps.split("-") + [a.chaps])[:2] if "-" in a.chaps else (a.chaps, a.chaps)
chaps = range(int(lo), int(hi)+1)

mgr = load_wlc_manager()
print("="*70); print(f"PoC v3 — sourceid=WLC(原生 H 前綴 + lemma)  創世記 {a.chaps}"); print("="*70)
s1 = mgr["01001001"].sources
print("驗證來源:", " ".join(f"{x.strong}" for x in s1[:4]), "... lemma:", s1[1].lemma)

# Pass 1: 無變體表
st1, cooc, lemma_of = run(chaps, mgr, {}, "Pass1 無變體表")

# 學習變體表:殘差共現取每個 FHL 號的最強對應
TOT = cooc.pop('__TOTAL__', Counter())
learned = {}; scored = []
for fhl, c in cooc.items():
    # lift = P(此 mac | 此 fhl 未對) / P(此 mac 為殘差) ;剔除高頻普遍殘差
    best = None
    denom_all = sum(c.values())
    for mac, n in c.items():
        if n < 3: continue
        share = n / denom_all
        lift  = share / max(TOT[mac] / max(sum(TOT.values()), 1), 1e-9)
        if share >= 0.30 and lift >= 5:
            if best is None or lift > best[2]: best = (mac, n, lift, share)
    if best:
        learned[fhl] = best[0]; scored.append((fhl, *best))
print(f"\n--- 學到的變體等價表({len(learned)} 條,門檻 n>=3、佔比>=30%、lift>=5)---")
print(f"{'FHL':>6} -> {'Macula':>7} {'次數':>5} {'佔比':>6} {'lift':>7}  Macula lemma")
for fhl, mac, n, lift, share in sorted(scored, key=lambda x: -x[2])[:20]:
    print(f"{fhl:>6} -> {mac:>7} {n:>5} {share*100:>5.0f}% {lift:>7.1f}  {lemma_of.get(mac,'')}")

# Pass 2: 套用變體表
st2, _, _ = run(chaps, mgr, learned, "Pass2 套用變體表")
