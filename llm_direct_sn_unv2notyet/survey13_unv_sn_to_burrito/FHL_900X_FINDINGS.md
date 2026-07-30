# FHL 900x 前綴標註 — 全庫實證盤點

> 測於 2026-07-31,by `survey13_unv_sn_to_burrito-obe`。
> 資料源:`original_text_preparation/source_sqlite/bible_little.db` 的 `unv` 表(帶 SN 之 UNV,**31,103 節全掃**),
> 交叉驗證:`../Alignments/data/sources/WLC.tsv`(Macula 原文 token)+ FHL `qp.php`(權威解析)。
>
> **用途**:(1) s13 自身的覆蓋率上限依據;(2) 提交 `sn_within_unv_selfgroup_segmentation/SPECIFICATION_v1.9.md`
> 擁有者評估的增補建議。**本檔不修改規格** —— 跨 survey 動規格應由擁有者決定(該目錄採 OpenSpec 流程)。

---

## 〇、先修正一個常見誤解:規格**不以 WLC 為來源**

`SPECIFICATION_v1.9.md` 全文**零次**提及 WLC / Macula / Clear Bible。其規範來源僅兩個(§12.2):

```
qb.php  → UNV 帶 SN 的經文
qp.php  → 解析 / 構形資料
```

**WLC 是 s13 外加的交叉檢查,不在規格體系內。** 討論規格自洽性時,只能拿 qb + qp 衡量。

---

## 一、全庫 900x 盤點(qb / qp 雙源)

**兩個來源各自出現的 900x 碼不同** —— 這是理解後續一切的關鍵。

| 碼 | qb.php 次數 | qp.php 次數 | 規格 `prefix_map_900x` |
|---|---:|---:|---|
| `09001` | 21,023 | 4,423 | ✅ `ל־` |
| `09002` | 15,754 | 1,359 | ✅ `ב־` |
| `09003` | 2,933 | 17 | ✅ `כ־` |
| **`09004`** | **1** | **59** | ⚠️ **未列** |
| `09005` | 0 | 27 | ✅ alias→`09001` |
| `09006` | 0 | 0 | ✅ `מ־`(死碼,見第四節) |
| `09009` | 0 | 0 | ✅ `ה־`(死碼,見第四節) |
| **`09013`** | 0 | **170** | ⚠️ **未列** |
| **`09014`** | 0 | **1,962** | ⚠️ **未列** |
| `09015` | 0 | 1,164 | ✅ `ignored_codes` |

- **qb 掃描**:`bible_little.db` 的 `unv` 表,31,103 節
- **qp 掃描**:`bible_parsing.db` 的 `lparsing` 表,331,800 列(舊約)

> ⚠️ **規格收了較少見的 `09005`(qp 27 次),卻漏了較常見的 `09004`(qp 59 次)。**

> 補充:`hfhl` 字典查 `09001`–`09009` **全無條目** —— 900x 是 FHL 自訂的**結構碼**,不是真正的 Strong 編號。

---

## 二、三個規格未列的 900x 碼

| 碼 | qp 次數 | qp 的 `orig` / `wform` | 判定 | 建議 |
|---|---:|---|---|---|
| **`09004`** | 59 | `orig=.l`、`介系詞 + 詞尾` | **= `ל־`** | 加為 `09001` 的 alias |
| **`09013`** | 170 | `介系詞 12.l21 + 動詞 Histaf'el 不定詞附屬形` | **= `ל־` + 不定詞**構造 | 加為 `09001` 的 alias(或另立複合類) |
| **`09014`** | 1,962 | **`段落符號`** | 與 `09015` **完全同類** | 併入 `ignored_codes` |

實例:

```
09004  Dan 6:2    word=!Ah.l              orig=.l        wform=介系詞 + 3 複陽詞尾
09013  1 Sam 1:3  word=tOw]x;T.vih.l      orig=h"w'x     wform=介系詞 + 動詞不定詞附屬形
09014  Deut 12:19 word=s                  orig=h'mWt.s   wform=段落符號
09015  Gen 25:18  word=p                  orig=h'xWt.P   wform=段落符號   ← 規格已列
```

> ⚠️ **`09014` 漏收的後果最實際**:它出現 **1,962 次**(比規格已列的 `09015` 的 1,164 次還多),
> 兩者 `wform` 都是「段落符號」。漏收會讓段落符號**漏過濾**,污染分組結果。

---

## 二之一、`09004` 的完整查證(方法論案例)

**唯一出現處:但 7:12**(亞蘭文段落)

```
…存留<WH03052><WTH8753><WH0754><WH09004>，直到<WH05705>…
```

### 權威判定來自 `qp.php`

```
qp.php?engs=Dan&chap=7&sec=12
  wid=8  sn=09004  word=לְהוֹן  orig=לְ  exp=給、往、向、到、歸屬於
```

**`09004` = `ל־`**,與 `09001` 同義。WLC 側對應 `o270070120081 = ל (A3807b, prep)`。

### 建議

比照現有的 `09005` alias 寫法,補入:

```yaml
aliases:
  "09005": "09001"  # 異名同義
  "09004": "09001"  # 異名同義(實測:但 7:12,qp.php orig=לְ)
```

> ### ⚠️ 方法論教訓(本檔最重要的一條)
>
> 本結論經歷**兩次錯誤**才定案:
>
> 1. 初判「`09004` 未列,應補入」—— 結論對,但理由薄弱(僅憑「規格沒有」)。
> 2. 改判「是 `09002`(ב)的誤植,應標為資料異常」—— **錯**。依據是拿 WLC 的
>    **token 順序**推斷 `09004` 落在 ב 的位置。但 **UNV 的 SN 順序跟隨中文語序,
>    不跟隨希伯來文語序**,位置推斷本就不可靠。
> 3. `qp.php` 定案:`orig=לְ`,是 `ל־`。
>
> **判準:要問「FHL 這個標記是什麼意思」,唯一權威是 `qp.php`,不是 WLC 的位置對照。**
> WLC 適合驗證「語義合不合理」,不適合判定「FHL 的碼是什麼」。

---

## 二之二、qb ↔ qp 全庫一致性實測

全舊約 **23,145 節**逐節 SN 多重集比對(排除 morph `8xxx`):

| | |
|---|---:|
| 完全一致 | 4,041(**17.5%**) |
| 有差異 | 19,104(82.5%) |

**但 82.5% 的差異全是系統性的顆粒度差異,不是錯誤**:

| qb 有 / qp 無 | 次數 | | qp 有 / qb 無 | 次數 |
|---|---:|---|---|---:|
| `09001` | 16,631 | | `09014` | 1,962 |
| `09002` | 14,400 | | `09015` | 1,164 |
| `04480`(מ) | 6,230 | | `03942`(לִפְנֵי) | 1,100 |
| `09003` | 2,917 | | **`01980`** | **1,041** |
| `06440`(פָּנֶה) | 1,104 | | **`00376`** | **533** |
| **`03212`** | **1,040** | | `09013` | 170 |
| **`00582`** | **517** | | `00853` | 151 |

- **qb 獨有的 900x + `04480`**:qb 把前綴**拆出來獨立標**,qp 則**併入詞內** —— 即規格 §2.4 的「Parsing Code 兩級顆粒度」
- **qp 獨有的 `09014`/`09015`**:段落符號,qb 不輸出
- **qp 獨有的 `03942`**:`לִפְנֵי` 複合詞的合併碼 —— 規格 §1.8 已明文處理

### 🔴 重要更正:`3212≡1980` 不是「FHL vs Macula」的分歧

本 survey 早期(PoC v3)自動學到的變體等價表:

```
3212 → 1980  (הלך 行走)     582 → 376  (אִישׁ 人)
```

當時歸因為「**FHL 與 Macula 兩套獨立 Strong 標註的版本分歧**」。**這個歸因是錯的。**

實測顯示:

| 來源 | 用哪個號 |
|---|---|
| `qb.php`(UNV+SN) | `3212` / `582` |
| **`qp.php`** | **`1980` / `376`** |
| Macula `WLC.tsv` | `1980` / `376` |

**qp.php 自己就用 `1980`/`376`,與 Macula 一致。分歧存在於 FHL 內部的 qb ↔ qp 之間,不是跨機構。**

而規格對此**早有裁決規則**:

> **當 `qb.php` 和 `qp.php` 使用不同 SN 時,自動使用 `qp.php` 的 SN**(v1.7.2)

也就是說 —— **PoC 那張變體表,是在重新發現規格早已規定的東西。**

> ### 對 s13 的實作意涵
> 未來建變體對照表,**正確作法不是自己從殘差學,而是直接查 `qp.php`**。
> 自學法只能得到統計近似(前次 8 條中 3 條是雜訊),查 qp 則是權威且零猜測。

---

## 三、⚠️ 字母前綴不可作為 900x 判定依據

實測前綴分布:

| token | 次數 |
|---|---:|
| `<WAH09001>` | 21,020 |
| `<WAH09002>` | 15,754 |
| `<WAH09003>` | 2,933 |
| **`<WH09001>`** | **3** |
| **`<WH09004>`** | **1** |

**同一個 `09001` 同時以 `WAH` 與 `WH` 出現。** 四個 `WH` 前綴的異常 token:

| 位置 | token | WLC 對應 |
|---|---|---|
| 利 19:34 | `<WH09001>` | `ל` (H3807a, prep) ✅ 確為 ל־ |
| 士 19:29 | `<WH09001>` ×2 | — |
| 但 7:12 | `<WH09004>` | `ל` (A3807b, prep) ✅ |

分布橫跨希伯來文(利、士)與亞蘭文(但),**不是語言差異,是標註不一致**。

### 這驗證了規格的設計是對的

`SPECIFICATION_v1.9.md` §2.1 已明訂「`WH`/`WTH`/`WAH` 等內部前綴與解析邏輯無關」、判定依據是「**5 位數且 `09` 開頭**」。

**若有實作圖方便改用 `WAH` 判定,會漏掉這 4 個 token。** 建議在 §2.1 或 §3.2 補一句實證註記:

> ⚠️ 實測(全庫 31,103 節):`09001` 同時以 `<WAH09001>`(21,020)與 `<WH09001>`(3)出現;
> `09004` 僅以 `<WH09004>` 出現。**切勿以字母前綴判定 900x**,必須用「5 位數且 `09` 開頭」。

---

## 四、`09006` / `09009` 為何是死碼 —— 查明原因

不是資料缺漏,是 **FHL 根本用別的方式標**:

| 詞素 | WLC 端數量(依 pos) | FHL 的標法 | 對應 900x |
|---|---:|---|---|
| **מ**(H4480) | 7,559(prep) | **用一般 Strong `<04480>`**,7,548 次 | `09006` **0 次** |
| **ה** 冠詞(H1886*) | **30,287**(art) | **幾乎不標**(`<01886>` 僅 4 次) | `09009` **0 次** |

實例(利 19:34):

```
UNV:  看他如本地人<WAH09003><WH0249>{<WAH04480>}一樣
WLC:  כְּ(→09003 ✅)  אֶזְרָח(→H0249 ✅)  מִ(→用 04480,非 09006)
```

**建議**:將 `09006` / `09009` / `09015` 標註為「**防禦性保留;現行 FHL 資料源未使用**」,並註明 `מ` 實際以 `04480` 標記 —— 免得後人以為解析漏了。

---

## 五、🆕 結構性上限 — FHL 不標 `ו` 與 `ה`

這是本次盤點對 **s13 最重要的發現**:

| 詞素 | WLC 端(依 pos) | UNV 端 |
|---|---:|---:|
| **ו** 連接詞(H2050*) | **51,004**(cj) | `<02050>` **僅 4 次** |
| **ה** 冠詞(H1886*) | **30,287**(art) | `<01886>` **僅 4 次** |

**合計 8 萬多個原文詞素,FHL 完全沒有標註。**

### 對 s13 的意義

我們 PoC 的「前綴覆蓋率」天花板**不是演算法問題,是來源標註問題**:

- UNV 側**根本沒有**這些詞素的 SN 標記 → 無從 join
- 這些詞素在 WLC 側**確實存在**且有獨立 token → 對齊時會成為**永久未對齊的 source token**

**這是正常的**,不是缺陷 —— 比照 Burrito 的既有慣例:未對齊的 source token **乾脆不建 record**(見 [`BURRITO_FORMAT.md`](BURRITO_FORMAT.md) 創 1:1 的 `.004` 缺席)。

> **s13 產出對齊檔時,不應為 ו / ה 這類 token 強行建立記錄。**

---

## 六、建議彙總(交規格擁有者評估)

| # | 建議 | 類型 | 風險 |
|---|---|---|---|
| **1a** | `aliases` 補 **`"09004": "09001"`**(qp 59 次,`orig=.l`) | 資料補全 | 低(additive) |
| **1b** | `aliases` 補 **`"09013": "09001"`**(qp 170 次,`ל־`+不定詞) | 資料補全 | 低 |
| **1c** | `ignored_codes` 補 **`"09014"`**(qp **1,962** 次,段落符號,與已列的 `09015` 同類) | **資料補全,影響過濾** | 低但**應優先** |
| 2 | §2.1 / §3.2 補「切勿以字母前綴判定 900x」實證註記 | 文件澄清 | **零**(不改行為) |
| 3 | `09006`/`09009` 標為「防禦性保留,現行未使用」,並註明 `מ` 實際用 `04480` | 文件澄清 | 零 |
| 4 | FAQ 補「900x 在 Strong 字典無條目,是 FHL 自訂結構碼」 | 文件澄清 | 零 |
| 5 | 在 §2.4(兩級顆粒度)補實測數據:全庫 23,145 節僅 17.5% 完全一致,差異全屬顆粒度 | 文件佐證 | 零 |

**優先序建議**:`1c`(`09014` 漏過濾,1,962 次,有實際污染風險)> `1a`/`1b`(對照表完整性)> `2`–`5`(文件澄清)。

**不建議**:把 `09004` 當資料異常上報 FHL。qp.php 顯示它是 FHL 有意使用的碼,
不同於 [`BUG_2_report_FHL.md`](../survey4_self_supervised_prompt_tuning/BUG_2_report_FHL.md)
記錄的 `<WAH019691>`(6 位數,確為格式錯誤)。**這是我方規格的缺漏,不是 FHL 的 bug。**

---

## 重現指令

```bash
cd /Users/joshua/work/strong_number_embedding

# 全庫 900x 盤點
python3 - <<'EOF'
import sqlite3, re, collections
con=sqlite3.connect('original_text_preparation/source_sqlite/bible_little.db')
c=collections.Counter()
for (txt,) in con.execute("SELECT txt FROM unv"):
    for m in re.finditer(r'<(W[A-Z]*?)(09\d{3})>', txt or ''):
        c[(m.group(1), m.group(2))] += 1
for k, v in sorted(c.items()):
    print(f"<{k[0]}{k[1]}>: {v:,}")
EOF

# qp 端 900x 盤點(離線鏡像)
python3 - <<'EOF'
import sqlite3, collections
qp = sqlite3.connect('original_text_preparation/source_sqlite/bible_parsing.db')
c = collections.Counter(); samp = {}
for e, ch, se, wid, w, sn, pro, wf, o in qp.execute(
        "SELECT engs,chap,sec,wid,word,sn,pro,wform,orig FROM lparsing"):
    if sn and sn.startswith('09'):
        c[sn] += 1
        samp.setdefault(sn, (e, ch, se, w, o, wf))
for sn, n in sorted(c.items()):
    e, ch, se, w, o, wf = samp[sn]
    print(f"{sn}: {n:>6,}   例 {e} {ch}:{se} word={w} orig={o} wform={wf[:30]}")
EOF

# qb ↔ qp 逐節一致性
python3 - <<'EOF'
import sqlite3, re, collections
qb = sqlite3.connect('original_text_preparation/source_sqlite/bible_little.db')
qp = sqlite3.connect('original_text_preparation/source_sqlite/bible_parsing.db')
def norm(s):
    m = re.search(r'(\d+)', s or ''); return str(int(m.group(1))) if m else None
qbv = {}
for e, ch, se, txt in qb.execute("SELECT engs,chap,sec,txt FROM unv"):
    qbv[(e, ch, se)] = collections.Counter(
        str(int(m.group(2))) for m in re.finditer(r'<W([ATH]*)(\d+)>', txt or '')
        if 'T' not in m.group(1))
qpv = collections.defaultdict(collections.Counter)
for e, ch, se, wid, sn in qp.execute("SELECT engs,chap,sec,wid,sn FROM lparsing"):
    if wid == 0: continue
    n = norm(sn)
    if n: qpv[(e, ch, se)][n] += 1
common = [k for k in qbv if k in qpv]
exact = sum(1 for k in common if qbv[k] == qpv[k])
print(f"交集 {len(common):,} 節,完全一致 {exact:,} ({100*exact/len(common):.1f}%)")
EOF

# 權威判定(FHL 自己的解析)
curl -s "https://bible.fhl.net/json/qp.php?engs=Dan&chap=7&sec=12" | python3 -m json.tool | grep -A2 '09004'
```
