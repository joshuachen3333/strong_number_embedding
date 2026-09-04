# text-align 與 MACULA 原文 TSV 勘查

> 勘查日 2026-08-25，由 text-align-obe 於 `llm_direct_sn_unv2notyet/text-align/` 內實測。
> 所有數字都是當場跑出來的，不是引用文件。與 [`ALIGNMENTS_DATA.md`](ALIGNMENTS_DATA.md)
> 互補：那份記「Alignments 從哪來、我們讀哪幾個檔」，這份記「這些檔實際長什麼樣、
> 彼此什麼關係、text-align 怎麼用它們」。

---

## A. 先分清楚三個東西（我一開始就搞混過）

| | 是什麼 | 本機位置 |
|---|---|---|
| **`Clear-Bible/Alignments`** | 語料庫 repo，1.0 GB。10 語言 / 12 譯本 / 21 個人工對齊檔 + 6 個原文 TSV | `llm_direct_sn_unv2notyet/Alignments/`（巢狀 clone，pinned `c99bd0a`，`.gitignore:70` 排除） |
| **`BibleAquifer/text-align`** | 工具鏈 repo，10 個 CLI。用 LLM **產生**對齊，不是既有對齊 | `llm_direct_sn_unv2notyet/text-align/`（巢狀 clone，父 repo 未追蹤） |
| **`~/git/Clear-Bible/alignments-<lang>/`** | Biblica 的每語言 repo，是 text-align 各 config 的 `alignments_root`，**含 `alignments-cmn`** | **本機不存在** |

第三個常被誤認成第一個。`compare-alignment` 讀的是第三個；`english_bridge.py` 讀的是第一個。
兩者的中文涵蓋狀況完全不同（見 §G）。

**人物線索**：Alignments 的 pinned commit「from Rick: split gloss2 values」的 Rick，
就是 text-align 的作者 Rick Brannan（`rbrannan@gloo.us`）。兩個 repo 同一人維護。

---

## B. 原文 TSV：六個檔，兩套分析

`Alignments/data/sources/`：

```
BGNT.tsv              8.6M   拜占庭 NT
SBLGNT.tsv           11.0M   ← text-align 帶的就是這個（差一個字，見 §F）
SBLGNT+required.tsv  11.7M
WLC.tsv              36.8M   ← 唯一有 H/A 前綴、有 lemma、有中文 gloss2 的
WLCM.tsv             28.8M   ← text-align 帶的是「這個 + morph」
WLCM+required.tsv    32.8M   ← strongs 欄已毀損，見 §D-1
```

text-align 只 bundle 兩個：`SBLGNT.tsv`、`WLCM.tsv`。

### 四個希伯來檔的關係

| 檔 | 列數 | 欄 | `strongs` | `lemma` | `morph` | `gloss2` |
|---|---:|---:|---|:-:|---|---|
| `Alignments/WLC.tsv` | 475,012 | 9 | **`H0871a`／`A…`**<br>H 467,483 · A 7,529 | ✅ | `Pp` `ncfsa` | **簡體中文** 417,931 |
| `Alignments/WLCM.tsv` | 469,476 | 8 | 裸數字 `0871a` | ❌ | **全空** | 幾乎全空 |
| `Alignments/WLCM+required.tsv` | 469,476 | 10 | **`G0871a`** ← 毀損 | 空 | 全空 | 空 |
| `text-align/WLCM.tsv` | 469,476 | 8 | 裸數字 `0871a` | ❌ | **`R` `Ncfsa` 全補齊** | 幾乎全空 |

### B-1　text-align 的 WLCM = Alignments 的 WLCM + morph

id 集合完全相同；逐欄比對後**唯一差異就是 `morph`**（Alignments 版 469,476 筆全空，
text-align 版 469,476 筆全有值），其餘每一欄零差異。

副作用：text-align 的 `CLAUDE.md`「WLCM source tokens have no `morph` field (always empty)」
描述的是**上游 Alignments 版**，它自己 bundle 的那份早就補好了。`_format_source_token`
的 `if token.morph:` 分支一直在生效，OT prompt 拿到的是 morph 碼而非 pos+gloss ——
文件與實際行為不同步。（未回報上游，見 §I）

### B-2　WLC 與 WLCM 是兩套獨立的形態分析

```
id 交集      466,587   （WLC 覆蓋 WLCM 的 99.38%）
只在 WLC       8,425
只在 WLCM      2,889   ← 詞素切分點本身就不同
```

99.38% 把 `ALIGNMENTS_DATA.md` 記的「創世記約 99.3% 共用 id」推廣到了全 corpus 尺度。

**但共同 id 裡只有 97.11% 的 Strong's 數字部分相同**，13,506 筆是分析歧異而非格式差異：

| id | 字形 | WLC | WLCM |
|---|---|---|---|
| `o070210120111` | אִישׁ | `H0376`（人） | `3045`（ידע 知道）|
| `o300040040041` | הַ | `H1886a`（冠詞） | `2050b`（連接詞）|
| `o130180050031` | לַ | `H3807a` | *(空)* |
| `o050100060061` | שָׁם | `H8033` | *(空)* |

連英文 `gloss` 也只有 **52.3%** 完全相同（`bank of` vs `bank`、`see!` vs `behold`、
`say` vs `saying`）。兩邊是各自跑過的編輯，不是同一份的兩種輸出。

> **對我們的意義**：現行「原文載 `WLC.tsv`、對齊那側用 WLCM id」的混搭策略仍然成立，
> 但落差不是 0.7% 的 morph 而已 —— 有 13,506 個 id 上兩邊給出不同的 SN。跨檔混用時
> 要意識到這一層。

### B-3　希伯來文是詞素級切分

WLCM：469,476 詞素 token / 305,517 詞 / 23,213 節 → **平均 1.54 詞素/詞**。
id 是 13 位 `o` + BBCCCVVVWWW**P**，最後一位是詞素序號。NT 是 12 位 `n` + BBCCCVVVWWW，無詞素位。

創 1:1（text-align 版 WLCM，含 morph）：

```
o010010010011  בְּ        0871a   preposition  R       in
o010010010012  רֵאשִׁית    7225    noun         Ncfsa   beginning
o010010010021  בָּרָא      1254    verb         Vqp3ms  created
o010010010031  אֱלֹהִים    0430    noun         Ncmpa   God
o010010010041  אֵת         0853    particle     To
o010010010051  הַ          1886a   particle     Td      the
o010010010052  שָּׁמַיִם   8064    noun         Ncmpa   heavens
o010010010061  וְ          2050b   conjunction  C       and
o010010010071  הָ          1886a   particle     Td      the
o010010010072  אָרֶץ       0776    noun         Ncbsa   earth
```

`pos` 分佈：`suffix` 47,442、`preposition` 64,316、`conjunction` 57,408、`particle` 54,403。
**這一層正對應我們處理 UNV+SN 900x 前綴的那個問題面。**

### B-4　不可分前綴用的是另一套編號，不是 FHL 的 09xxx

36% 的 OT strongs 帶字母尾綴（169,789 筆），且集中在功能詞：
conjunction 51,058 / suffix 47,237 / preposition 39,462 / particle 25,718，
實詞只有 noun 3,220 / verb 1,699。

| 形 | MACULA strongs（主要值） | 出現數 |
|---|---|---:|
| `לְ` | `3807a` | 8,154 |
| `מִ` | `4480` ← 等同古典 H4480 (מִן) | 4,186 |
| `הַ` / `הָ` | `1886a` | 17,047 / 7,930 |
| `וְ` | `2050b` | 24,460 |
| 代名詞後綴 | `2050c`(11,950) `3963a` `2967a` `3509b` … | 47,442 |

有些與古典 Strong's 對得上（מן = 4480），有些明顯不是同一套。
**這張對應表要用驗證的方式建，不要假設它等於 FHL 的 09002/09003。**

另有 5 筆用 `|` 併寫（`1886a|0725`、`1886j|2050b`、`1886a|7204a`）；
`normalize_strongs` 的處理是取 `|` 後半，並把 `[e-z]` 結尾直接砍掉（`1886j` → `1886`）。

---

## C. `gloss` / `gloss2` 的欄位語義漂移

**同一個欄名在三個檔裡意思不同**，這不是 MACULA 的統一契約，是逐檔的編輯決定：

| 檔 | `gloss` | `gloss2` |
|---|---|---|
| `SBLGNT.tsv` | 帶上下文的英文<br>`[The] book` · `of [the] genealogy` | 去脈絡的英文核心義<br>`book` · `genealogy` |
| `WLCM.tsv` | 英文<br>`created` · `God` | 英文加點號，66.4% 空<br>`he.created` · `(et)` |
| `WLC.tsv` | 英文<br>`he created` · `God` | **簡體中文**<br>`创造` · `神` |

創 1:1 בָּרָא 並排最清楚 —— **人稱標記在兩個檔之間換了欄位**：

```
WLCM :  gloss = created       gloss2 = he.created   ← 人稱在 gloss2
WLC  :  gloss = he created    gloss2 = 创造          ← 人稱在 gloss，gloss2 換語言
```

### WLC.tsv 兩欄的字集統計（n = 475,012）

```
gloss    拉丁 457,703 (96.4%)   空 9,597 (2.0%)    純標點 7,712 (1.6%)   漢字 0
gloss2   漢字 417,931 (88.0%)   空 50,346 (10.6%)  純標點 6,720 (1.4%)   拉丁 14  混合 1
```

- `gloss` **完全沒有希伯來文**。希伯來文在 `text`（帶母音重音字形）、`altId`（字形+出現序）、
  `lemma`（字典形）三個各自的欄位。
- `gloss` 的標點幾乎都是 `-`（7,060 筆，用於 אֵת 這種不可譯的受詞記號），另有 `?` 648 筆。
- `gloss2` 的 14 筆拉丁字母是雜訊（`l`、`llllllll`、`X`、`from`…），1 筆混合值是
  `底璧 or 罗底巴`（一格塞兩個譯名選項）。
- `gloss2` 相異值 44,721 個；抽樣含簡體特徵字 25,903 筆、**含正體 0 筆** → 純簡體。

---

## D. 三個坑

### D-1　G-prefix bug：已固化進發佈的資料檔

`text-align/src/text_align/burrito/source.py:85`：

```python
prefix = "G" if is_nt else "G"      # ← 兩個分支都是 "G"
self.strong = prefix + self.strong
```

實測跑過 WLCM 全檔：**467,770 筆舊約 Strong's 全部載成 `G####`**
（`רֵאשִׁית 7225` → `G7225`，希臘 Strong's 根本沒這個號），9,110 個相異值，
**ValueError 為 0** —— 完全靜默地錯。

而 `Alignments/data/sources/WLCM+required.tsv` 裡 467,770 筆已經**寫死成 `G0871a` / `G7225`**。
那不是推論，是 Clear 自己跑過同一支 loader 再寫回磁碟發佈的產物。
`ALIGNMENTS_DATA.md`「三個會咬人的地方」記的那條坑，在資料層被固化了。

**處置**：`WLCM+required.tsv` 的 `strongs` 欄視為毀損，不使用。
需要 SN 時一律走 `WLC.tsv`（有正確的 `H`/`A` 前綴）。
在 text-align 內部這個 bug 是**潛伏的** —— grep 過整個 `src/`，`.strong` 除了
`source.py` 自己的 `__post_init__` 外沒有任何地方讀取，對齊 prompt 餵的是
text + morph/pos + gloss，不含 Strong's。它只咬「把這支 loader 拿來做 SN 工作」的人。

### D-2　13,506 筆 SN 分歧

見 §B-2。跨 WLC/WLCM 混搭時的實質風險，不是 rounding error。

### D-3　換來源會靜默換語言

`refine/semantic.py` 的規則是「`gloss2` 非空時優先用它，並把點號換成空格」——
這條邏輯是照 WLCM 的 `he.created` 量身寫的。若把 `WLC.tsv` 換進 OT 來源，
LaBSE embedding 的來源端會變成簡體中文；LaBSE 是多語模型不會報錯，但
「用英文 gloss 當橋，因為 LaBSE 的古希伯來/希臘空間不可靠」那個立論就不成立了。

目前 `refine/util.py:16` 寫死 `_CORPUS_ID = {"nt": "SBLGNT", "ot": "WLCM"}`，現況安全。
（`SourceidEnum` 雖列了 WLC / BHB / UHB / BGNT / NA27 / NA28 / UGNT 為合法 sourceid，
實際跑起來只有 SBLGNT / WLCM 兩條路。推測理由：對齊檔本來就是對 WLCM 的 id 做的，
換 WLC 會整組對不上 —— 與 `english_bridge.py` 遇到的是同一個約束。）

---

## E. Scripture Burrito 是什麼、不是什麼

**是一個 JSON 格式規範（對齊檔的 schema），不是程式。** 它本身不「吃輸入」。

**對齊檔裡只有 token id，沒有任何文字**：

```json
{"source": ["o010010010012"], "target": ["01001001003"],
 "meta": {"id": "01001001.1", "process": "manual"}}
```

沒有字形、沒有 gloss、沒有 Strong's、沒有 pos。要看到「רֵאשִׁית ↔ In the beginning」
必須把兩邊 id 各自 join 回 TSV。

這是刻意的設計：文字與註解留在各自的 TSV，所以 `gloss2` 換語言、`morph` 補滿，
**都不會動到任何一個對齊檔**。代價是對 tokenization 極度敏感 —— 換一套切分就全毀。

### SB 0.3 與 0.4 的差別（本專案會遇到的）

| | SB 0.3（Alignments） | SB 0.4（text-align 產出） |
|---|---|---|
| 頂層 | 扁平 `{documents, meta, roles, type, records}` | `{format, version, groups[0]{…}}` |
| meta | `{"conformsTo": "0.3", "creator": "GrapeCity"}` | `{creator: "text-align", conformsTo: "0.4", llm: {provider, model, reasoning_effort}, nonEquivalent: {source[], target[]}}` |
| 記錄擴充 | 無 | `meta.secondary.{source,target}`、`meta.is_idiom` |
| 粒度 | 一譯本一大檔（WLC-YLT 50 MB） | 一章一檔 `{corpus}-{ed}-{BB}-{CCC}-manual.json` |

`AlignmentsReader.read_alignments` 兩種都吃得下（`_make_record` 會對 source selector 跑
`macula_unprefixer` 去掉 `n`/`o` 前綴），所以 `compare-alignment` 才能直接拿 0.3 當對照。

---

## F. Alignments 語料庫盤點

**10 語言 / 12 譯本 / 21 個對齊檔**：

| 語言 | 譯本 | 對齊檔來源端 |
|---|---|---|
| arb | AVD | SBLGNT + WLCM |
| | ONAV | SBLGNT（僅新約）|
| asm | IRVAsm | SBLGNT（僅新約）|
| ben | IRVBen | SBLGNT（僅新約）|
| eng | BSB | SBLGNT + **BGNT** + WLCM |
| | YLT | SBLGNT + **WLC** ← 唯一用 WLC 的 |
| fra | LSG | SBLGNT + WLCM |
| hau | OHCB | SBLGNT + WLCM |
| hin | IRVHin | SBLGNT + WLCM |
| por | JFA11 | SBLGNT（`-transfer`，非 manual）|
| rus | RUSSYN | SBLGNT + WLCM |
| spa | RV09 | SBLGNT + WLCM |

**沒有任何中文目錄。** 所以 §C 那批簡體 gloss2 是孤立的一欄詞義註解，
沒有配套的中文譯本對齊檔，不能當 gold 用。

每個對齊檔都有 `.toml` sidecar，記 license / tokenization / process / scope / team。

**SBLGNT 兩邊差一個字**：137,741 列逐欄比對，只有 1 處內容差異 ——
加 3:15 的 `n48003015012`，Alignments 是 `adds thereto`、text-align 是 `adds there to`
（看起來是回退不是修正）。檔案大小差 137 KB 純粹是行尾：Alignments CRLF、text-align LF。

---

## G. text-align「憑什麼」做沒有人工對齊的語言

它的品質保證**不是對答案**，而是「把原則寫清楚 + 用不需要答案的訊號量自己」：

| 層 | 是什麼 | 需要外部答案？ |
|---|---|---|
| 規格 | `docs/alignment-principles-{nt,ot}[.<iso>].md`，9,622 行 | ❌ 這是**寫出來的**標準 |
| 客觀評分 | `scoring.py` 五訊號：來源覆蓋（依詞性加權）／譯文實詞覆蓋／NEQ 濫用／token smearing／章內偏離 | ❌ 純內部量測 |
| 補充檢查 | LaBSE 語意相似度、ACAI 實體未對齊、`clean.py` 結構性修復 | ❌ |
| `compare-alignment` | 跟人工對齊比 P/R/F1 | ✅ **選配** |

`compare-alignment` 的真正用途是拿有答案的語言（IRVHin 那種）**校準門檻**
（`score_retry_threshold: 0.25` 這類數字設得合不合理），校準完的門檻再套到沒答案的語言。
這是它唯一能「憑什麼」的地方，而且是間接的。

### 中文這條線：沒有標尺，只有規格

中文並非完全沒有人工對齊 —— `~/git/Clear-Bible/alignments-cmn` 裡有 Biblica 的 CUVMPS
與 UBS 的 CU2010T。但這條路**已被指示撤回**：

- CUVMPS 與 CUV 有實質差異（神／上帝版雙版本傳統、85.4% 節層級 token 數不符）
- CU2010T 的詞級對齊 98.8% 的否定詞顯示 unaligned，但原文每次抽查都有否定詞

重建版改為拿 **CUV** 與 **BOCCB2023T** 兩本原始經文、逐構式抽樣 12–25 節人工判讀，
**全程沒用任何對齊資料**。所以 NT/OT 中文兩份都明寫
`draft — not yet reviewed by a native Mandarin speaker`，
而阿拉伯文寫的是 `native-speaker reviewed and confirmed "very good"`。
那個標註不是謙虛，是在標記證據層級的差異。

**本機現況**：`~/git/Clear-Bible` 不存在，本 checkout 的 staging 也沒有任何
`data/alignments/` 目錄 → **`compare-alignment` 現在任何語言都跑不起來。**

### zhs 目前是英文借殼

實際註冊的 prompt 語言是 **8 個**（`nt/__init__.py` 與 `ot/__init__.py` 一致）：

```
eng  por  spa  fra  ind  hin  arb  zht
```

**沒有 `zhs`。** 但 `configs/CUVS.yaml` 與 `configs/BOCCB2023S.yaml` 寫的是
`target_language: zhs`，而 `get_nt_language_config()` 對未註冊語言碼是
**靜默 fallback 到 eng，不印任何警告**。

也就是說：現在拿這兩個 config 跑，會用**英文的對齊 prompt** 去處理簡體中文經文 ——
沒有中文無冠詞、`的` 多義、`被` 字句、`所` 名物化那一整套規則。
簡體目標資料已經 staged（`data/targets/CUVS/`、`BOCCB2023S/`），config 也已在 #85 建好，
只有 prompt 那一半還沒補。

**精確說法**：19 個 config（含 1 個範本）／9 個 `target_language` 值／
但只有 8 個有真正的 prompt config。

---

## H. 對本專案（SN embedding）可用的部分

### H-0　CUV 詞元 TSV = 我們一直缺的中文基礎斷詞（2026-09-05 已落地）

**這是本次勘查最有實用價值的發現，已做成產物。**
完整記錄見 [`CUV_SEGMENTATION_CONTRIBUTION.md`](CUV_SEGMENTATION_CONTRIBUTION.md)，
工具在 `tools/cuv_segmentation/`。摘要：

`text-align` 的 `alignments-cmn/data/targets/CUV/` 有 kathairo 產出的和合本逐詞 TSV
（572,119 個實詞詞元）。**沒有 SN 欄位** —— 但我們不缺 SN，FHL 的 UNV+SN 已涵蓋全本。
缺的是詞邊界，而這正是它提供的。

先解決文本對映，四項系統性差異全部可機械處理：

| | FHL | CUV |
|---|---|---|
| 神名 | 神版（神 4,765） | 上帝版（上帝 4,085） |
| 異體字 | `著` `裡` | `着` `裏` |
| 內嵌譯註 | 1,393 處 | **246 節（雙向，兩邊判定不一致）** |
| 節數 | 多 82 節（併節） | 多 116 節（詩篇標題編第 0 節） |

兩個非顯而易見的坑：神名替換**必須對整串做**，因為 kathairo 會把「上帝」切斷
（創 5:1 切成 `當上`+`帝`）；CUV 的譯註括號是 `exclude=y` 標點，**但括號內的文字是
正常詞元**，得靠括號配對偵測。正規化後 31,103 節中 24,426 節文本完全相同、
6,031 節僅異體字差、**僅 564 節是真版本差異**（`流便`/`呂便` 這類音譯出入）。

以 FHL 的 SN 標籤位置為隱含切分基準，在 30,456 個可比節上：

| 指標 | 值 |
|---|---:|
| recall（FHL 邊界被 kathairo 命中） | **89.1%** |
| precision（kathairo 邊界也是 FHL 邊界） | 58.4% |
| kathairo 過度合併的詞元 | 35,478 / 558,686 = **6.35%** |

precision 低是因為 **kathairo 切得更細**，這對我們是優點：FHL 常把一個 SN 掛在
多詞片語上（`的兒子`、`的神`），kathairo 拆成 `的|兒子`。

**投影已完成並通過驗證**（`project.py` + `validate.py`，全本約 4 秒）：

| 邊界策略 | token | 細化 | SN 守恆 | 詞形碼守恆 |
|---|---:|---:|---:|---:|
| 只用 FHL | 384,788 | 1.00× | 0% 不符 | 0% 不符 |
| 只用 kathairo | 566,307 | 1.58× | **50.4% 不符** | 13.1% 不符 |
| **聯集（採用）** | **604,252** | **1.57×** | **0% 不符** | **0% 不符** |

聯集是唯一同時做到「無損」與「比 FHL 細 1.57 倍」的策略。產物
`output/_unv_sn_segmented/unv_sn.union.jsonl`，31,061 節、**30,456 節（98.1%）
套用了 kathairo 邊界**，96.9% 的 token 帶 SN，SN 與詞形碼的**多重集**逐節守恆。
其中 309 條短註（1 個 SN 且含「原文」「或譯」）的 SN 已掛回正文。

投影過程另外確認了一條 FHL 標註慣例：**帶大括號的 `{<WH0853>}` 往後掛**
（原文有、中文無對應字），與本專案 parser 的 `{<WH0853>}天<WH08064>` 一致。
最初寫成往前掛，被創 1:1 抓出來。

### H-1　其餘可用之處

1. **`WLC.tsv` 是現成的「希伯來詞素 → 英文 + 簡體中文」對照表**，以 WLC id 為鍵，
   含正確 `H`/`A` 前綴的 strongs 與 lemma。要正體需一道簡→繁轉換，
   並注意 44,721 個相異值裡的異體與人地名譯法（存在 `底璧 or 罗底巴` 這種一格兩選項）。
2. **詞素層（`pos=suffix` 47,442、`preposition` 64,316）直接對應我們的 900x 前綴議題**，
   但編號體系不同（§B-4），對應表必須驗證後才能用。
3. **方法可借**：兩段式成本分層（便宜模型全跑 → 客觀評分挑出問題節 → 貴模型 blank-slate 重跑）、
   不呼叫 LLM 的評分器、把語言類型學寫進 prompt。與 survey9 的 naked mode 同一類思路 ——
   都是把 LLM 只用在它真正擅長的那一小塊判斷上。
4. **反面教材**：`.strong` 的 G-prefix bug 示範了「靜默錯誤」的代價 ——
   9,110 個相異值零例外地錯，而且不拋任何 exception。我們自己的 `wlc_check()`
   回 `no_signal` 的那個坑是同一類問題。

---

## I. 未決事項

- [ ] text-align `CLAUDE.md` 的「WLCM has no morph, always empty」已過時（§B-1）——
      要不要回報上游？Joshua 不是該 repo 的 committer。
- [ ] `burrito/source.py:85` 的 `prefix = "G" if is_nt else "G"` —— 同上，
      要不要開 issue？（在 text-align 內部是潛伏的，但會咬下游使用者。）
- [ ] `cost_estimate.py:31` docstring 寫 `_NO_DATA_OUTPUT_MULTIPLIER`「default 6x」，
      第 72 行實際是 `2.0`，README 也寫 2.0 —— docstring 過時。
- [ ] `docs/alignment_principles-nt.por.md` 用底線，與其餘 13 個 `alignment-principles-*`
      兄弟檔命名不一致（可能因此漏掉搜尋）。
- [ ] MACULA 前綴編號 ↔ FHL 09xxx 的對應表尚未建立（§B-4）。
- [ ] CUV 投影的後續（958 節文本不符、844 條帶 SN 的譯註、簡體 CUVS）見 `CUV_SEGMENTATION_CONTRIBUTION.md` §8。
