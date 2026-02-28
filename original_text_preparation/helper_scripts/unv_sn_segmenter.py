#!/usr/bin/env python3
# unv_sn_segmenter.py — FHL UNV+SN segmenter (v1.2 rules) with CN gloss output
# Default: prints only the "SN grouping (readable+CN gloss)".
# Use -d/--debug to also print qb/qp raw JSON payloads.

import argparse, json, re, sys, urllib.request, urllib.parse
from collections import defaultdict, OrderedDict

BOOK_MAP = [
    ("Gen","創"),("Exod","出"),("Lev","利"),("Num","民"),("Deut","申"),
    ("Josh","書"),("Judg","士"),("Ruth","得"),("1Sam","撒上"),("2Sam","撒下"),
    ("1Kgs","王上"),("2Kgs","王下"),("1Chr","代上"),("2Chr","代下"),("Ezra","拉"),
    ("Neh","尼"),("Esth","斯"),("Job","伯"),("Ps","詩"),("Prov","箴"),
    ("Eccl","傳"),("Song","歌"),("Isa","賽"),("Jer","耶"),("Lam","哀"),
    ("Ezek","結"),("Dan","但"),("Hos","何"),("Joel","珥"),("Amos","摩"),
    ("Obad","俄"),("Jonah","拿"),("Mic","彌"),("Nah","鴻"),("Hab","哈"),
    ("Zeph","番"),("Hag","該"),("Zech","亞"),("Mal","瑪"),
    ("Matt","太"),("Mark","可"),("Luke","路"),("John","約"),("Acts","徒"),
    ("Rom","羅"),("1Cor","林前"),("2Cor","林後"),("Gal","加"),("Eph","弗"),
    ("Phil","腓"),("Col","西"),("1Thess","帖前"),("2Thess","帖後"),
    ("1Tim","提前"),("2Tim","提後"),("Titus","多"),("Phlm","門"),
    ("Heb","來"),("Jas","雅"),("1Pet","彼前"),("2Pet","彼後"),
    ("1John","約一"),("2John","約二"),("3John","約三"),("Jude","猶"),("Rev","啟"),
]
ENG2CH = {e:c for e,c in BOOK_MAP}
CH2ENG = {c:e for e,c in BOOK_MAP}

# ---------- Profile (configuration, NOT rules) ----------
PREFIX_900X = {
    "09001": "ל־",  # l-
    "09002": "ב־",  # b-
    "09003": "כ־",  # k-
    "09006": "מ־",  # m-
    "09009": "ה־",  # ha-
}
ALIASES = {"09005": "09001"}              # some sources may use 09005 for ל-
BRACE_PREPS = {"05921","04480","0413","00996"}  # brace preps → right-attach to following noun (v1.2-A)
OBJECT_MARKER = "0853"                    # אֵת
USE_CONSTRUCT_LINKER = True               # v1.2-B (annotation only)
USE_PARSING_INFERENCE = True              # only annotate inferred prefixes (not used in printing lines here)

# ---------- HTTP ----------
def _get(url, params):
    q = urllib.parse.urlencode(params)
    full = url + ("?" + q if q else "")
    with urllib.request.urlopen(full, timeout=20) as r:
        data = r.read().decode("utf-8")
    return json.loads(data)

def fetch_qb(chineses, chap, sec):
    return _get("https://bible.fhl.net/json/qb.php", {
        "chineses": chineses, "chap": chap, "sec": sec, "version":"unv", "strong":"1"
    })

def fetch_qp(engs, chap, sec):
    return _get("https://bible.fhl.net/json/qp.php", {
        "engs": engs, "chap": chap, "sec": sec
    })

# ---------- Tokenization ----------
TOKEN_RE = re.compile(r'(\{<[^>]+>\}|<[^>]+>)')

def _digits(s):
    m = re.search(r'(\d{3,5})', s)
    return m.group(1) if m else None

def normalize_900x(n):
    return ALIASES.get(n, n)

def tokenize_qb(bible_text):
    out = []
    for m in TOKEN_RE.finditer(bible_text):
        raw = m.group(1)
        is_brace = raw.startswith("{")
        num = _digits(raw) or ""
        if is_brace:
            if num in BRACE_PREPS or num == OBJECT_MARKER:
                out.append({"kind":"brace", "num":num})
            else:
                out.append({"kind":"brace_core", "num":num})  # implicit core {<0430>}
            continue
        if num.startswith("09"):
            out.append({"kind":"prefix900", "num":normalize_900x(num)})
        elif num.startswith("8") and len(num)==4:
            out.append({"kind":"morph", "num":num})
        else:
            out.append({"kind":"core", "num":num})
    return out

# ---------- Build POS & lexicon from qp ----------
def build_pos_lex(qp_json):
    noun, verb, prep = set(), set(), set()
    wform_by_sn = {}
    exp_by_sn = {}
    recs = qp_json.get("record", [])
    for r in recs:
        sn = (r.get("sn") or "").zfill(5)
        if not sn.strip("0"):  # wid=0 header lines
            continue
        wform = (r.get("wform") or "").strip()
        exp = (r.get("exp") or "").strip()
        wform_by_sn[sn] = wform
        exp_by_sn[sn] = exp
        if "名詞" in wform: noun.add(sn)
        if "動詞" in wform: verb.add(sn)
        if "介系詞" in wform: prep.add(sn)
    return noun, verb, prep, wform_by_sn, exp_by_sn

# ---------- v1.2 segmentation ----------
def segment(tokens, noun_set, verb_set, wform_by_sn):
    groups = []
    warnings = []
    prefix_buf = []
    pending_pre_brace = {}  # core_index -> [braceSN]

    def schedule_pre_brace(target_idx, sn):
        pending_pre_brace.setdefault(target_idx, []).append(sn)

    def find_next_core(i):
        for j in range(i+1, len(tokens)):
            if tokens[j]["kind"] == "core":
                return j
        return None

    def last_group():
        return groups[-1] if groups else None

    i = 0
    while i < len(tokens):
        t = tokens[i]; k = t["kind"]
        if k == "prefix900":
            prefix_buf.append(t["num"])
        elif k == "morph":
            g = last_group()
            if g: g["morph"].append(t["num"])
            else: warnings.append(f"morph_without_core@{i}:{t['num']}")
        elif k == "core":
            g = {"core": t["num"], "implicit": False,
                 "prefixes": prefix_buf[:], "morph": [],
                 "pre_brace": [], "post_brace": []}
            prefix_buf.clear()
            if i in pending_pre_brace:
                g["pre_brace"].extend(pending_pre_brace.pop(i))
            groups.append(g)
        elif k == "brace":
            sn = t["num"]
            if sn == OBJECT_MARKER:
                j = find_next_core(i)
                if j is not None:
                    schedule_pre_brace(j, sn)  # right-attach to next core (noun preferred)
                else:
                    warnings.append(f"dangling_object_marker@{i}")
            else:
                gprev = last_group()
                prev_is_inf = bool(gprev and any(m == "8800" for m in gprev["morph"]))
                prev_is_verb = bool(gprev and (gprev["core"] in verb_set))
                # Left-attach exception if previous is verb infinitive; otherwise right-attach to next noun/core:
                if prev_is_inf and gprev:
                    gprev["post_brace"].append(sn)
                else:
                    j = find_next_core(i)
                    if j is not None:
                        schedule_pre_brace(j, sn)
                    else:
                        warnings.append(f"dangling_brace_prep@{i}")
        elif k == "brace_core":
            g = {"core": t["num"], "implicit": True,
                 "prefixes": prefix_buf[:], "morph": [],
                 "pre_brace": [], "post_brace": []}
            prefix_buf.clear()
            groups.append(g)
        i += 1

    if prefix_buf:
        warnings.append("dangling_900x_prefixes:" + ",".join(prefix_buf))
    return groups, warnings

# ---------- Heuristics for CN gloss ----------
CJK = re.compile(r'[\u4e00-\u9fff]+')

def pick_cn_gloss(exp_text:str) -> str:
    """
    From qp.exp like "上帝、神、神明" choose a concise headword.
    Heuristics: split by [、；，/ , ;], filter CJK terms, prefer length 1-2, else shortest, else first.
    """
    if not exp_text: return ""
    cand = re.split(r'[、;/；，,\s]+', exp_text)
    cand = [x for x in cand if CJK.search(x)]
    if not cand: return ""
    short = [x for x in cand if 1 <= len(x) <= 2]
    if short: 
        # prefer single char first (e.g., 神、光)
        singles = [x for x in short if len(x)==1]
        if singles: return singles[0]
        return short[0]
    # otherwise pick the shortest
    cand.sort(key=len)
    return cand[0]

def pos_label(wform:str) -> str:
    if not wform: return ""
    for key in ("名詞","動詞","形容詞","副詞","介系詞","代名詞","數詞","連接詞","介詞"):
        if key in wform:
            return key
    return wform.split("，")[0] if "，" in wform else wform

# ---------- Render ----------
def render_readable(groups, wform_by_sn, exp_by_sn):
    lines = []
    morph_notes = OrderedDict()  # morph_code -> list of " <SN> → wform"
    for g in groups:
        # Build token form with braces/prefix/morphs (same visual as before)
        pre = "".join("{<%s>}"%b for b in g.get("pre_brace", []))
        prefixes = "".join("<%s>"%p for p in g.get("prefixes", []))
        core = ("{<%s>}"%g["core"]) if g.get("implicit") else "<%s>"%g["core"]
        morphs = "".join("(%s)"%m for m in g.get("morph", []))
        postb = "".join("{<%s>}"%b for b in g.get("post_brace", []))
        left = f"{pre}{prefixes}{core}{morphs}{postb}"

        # Chinese POS + gloss from qp
        wform = wform_by_sn.get(g["core"], "")
        gloss = pick_cn_gloss(exp_by_sn.get(g["core"], ""))
        pos = pos_label(wform)
        right_main = ""
        if pos and gloss:
            right_main = f"{pos}「{gloss}」"
        elif pos:
            right_main = pos
        elif gloss:
            right_main = f"「{gloss}」"

        # Morph code note
        morph_codes = g.get("morph", [])
        if morph_codes:
            # record detailed notes per (morph, SN)
            for m in morph_codes:
                morph_notes.setdefault(m, [])
                note = wform or "(無 wform 註解)"
                morph_notes[m].append(f"<{g['core']}> → {note}")
            right = f"{right_main}；{''.join(morph_codes)}（詳見下方 morph 註）" if right_main else f"{''.join(morph_codes)}（詳見下方 morph 註）"
        else:
            right = right_main

        lines.append(f"{left} — {right}" if right else f"{left}")
    return lines, morph_notes

# ---------- main ----------
def main():
    ap = argparse.ArgumentParser(description="UNV+SN segmenter (v1.2 rules) — readable CN gloss")
    ap.add_argument("--chineses","-b", help="中文卷名（如 創/約/撒上）")
    ap.add_argument("--engs", help="英文縮寫（如 Gen/John/1Sam）")
    ap.add_argument("--chap","-c", default="3")
    ap.add_argument("--sec","-s", default="16")
    ap.add_argument("-d","--debug", action="store_true", help="同時輸出 qb/qp 的 JSON 原始資料")
    args = ap.parse_args()

    # resolve book ids
    if not args.chineses and not args.engs:
        engs = "John"; chineses = ENG2CH[engs]
    elif args.chineses and not args.engs:
        chineses = args.chineses
        engs = CH2ENG.get(chineses)
        if not engs:
            print("Unknown chineses; use abbreviations like 創/約/撒上。", file=sys.stderr); sys.exit(1)
    elif not args.chineses and args.engs:
        engs = args.engs
        chineses = ENG2CH.get(engs)
        if not chineses:
            print("Unknown engs; use Gen/John/1Sam。", file=sys.stderr); sys.exit(1)
    else:
        if CH2ENG.get(args.chineses) != args.engs:
            print("卷名不一致：--chineses 與 --engs 不相符", file=sys.stderr); sys.exit(1)
        engs = args.engs; chineses = args.chineses

    chap, sec = str(args.chap), str(args.sec)

    qb = fetch_qb(chineses, chap, sec)
    qp = fetch_qp(engs, chap, sec)

    if args.debug:
        print(f"=== qb.php（UNV + strong=1）— {chineses} {chap}:{sec} ===")
        print(json.dumps(qb, ensure_ascii=False, indent=2)); print()
        print(f"=== qp.php（parsing）— {chineses} {chap}:{sec}（engs={engs}） ===")
        print(json.dumps(qp, ensure_ascii=False, indent=2)); print()

    if not qb.get("record") or not qb["record"]:
        print("No qb record."); return
    bible_text = qb["record"][0].get("bible_text","")

    noun_set, verb_set, prep_set, wform_by_sn, exp_by_sn = build_pos_lex(qp)
    toks = tokenize_qb(bible_text)
    groups, warnings = segment(toks, noun_set, verb_set, wform_by_sn)

    # Construct linker (annotation only)
    if USE_CONSTRUCT_LINKER:
        for idx, g in enumerate(groups):
            wform = wform_by_sn.get(g["core"], "")
            if "附屬形" in wform:
                for j in range(idx+1, len(groups)):
                    if groups[j]["core"] in noun_set:
                        g["construct_of"] = groups[j]["core"]
                        break

    title = f"{chineses} {chap}:{sec}"
    print(f"=== SN grouping（可讀 + 中文詞性/釋義）— {title} ===")
    lines, morph_notes = render_readable(groups, wform_by_sn, exp_by_sn)
    for i, line in enumerate(lines, 1):
        print(f"{i}. {line}")
    if warnings:
        print("\n[WARN]", "; ".join(warnings))

    if morph_notes:
        print("\n— Morph 註解 —")
        for m, pairs in morph_notes.items():
            uniq = []
            seen = set()
            for p in pairs:
                if p not in seen:
                    uniq.append(p); seen.add(p)
            print(f"{m}: " + "； ".join(uniq))

if __name__ == "__main__":
    main()
