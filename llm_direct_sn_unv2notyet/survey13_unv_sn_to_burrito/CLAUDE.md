# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# survey13_unv_sn_to_burrito

> Seeded 2026-07-28 by `Alignments-obe`. The work incubated inside the
> `../Alignments/` checkout; that checkout has since been reset to `origin/main`
> and is now **read-only**, with all incubation artifacts moved here.

## 沿襲(Lineage)

本 survey(**s13**)沿襲自 **Clear Bible 的 Alignments 專案**:

| | |
|---|---|
| **上游來源** | **`https://github.com/Clear-Bible/Alignments`** |
| 本地 checkout | `../Alignments/` — **唯讀資料源**,已重置至 `origin/main`(`c99bd0a`) |
| 沿襲內容 | Scripture Burrito / AlignmentHub 對齊格式、`sources/WLC.tsv` 與 `SBLGNT.tsv`、TOML metadata 慣例、BCVWP token ID 方案 |
| 本 survey 歸屬 | `github.com/joshuachen3333/strong_number_embedding` |

**指涉約定**:本目錄文件中,**「Alignments 專案」**一律指上游 `Clear-Bible/Alignments`;**「本專案 / s13」**指本 survey。兩者不可混用——早期考證段落談的都是前者。

## What this survey does

**反推**:把已完成的下游產品 **UNV+SN**,還原成上游的 **Scripture Burrito 對齊資料** —— 讓 UNV 成為 Clear-Bible/Alignments 的**第 11 個語言(`cmn`)/ 第 13 個譯本**。

**為什麼這條路特別可靠**:其他 12 個譯本靠人工語義對齊,而 UNV 兩側**都已被獨立標註 Strong's**——FHL 標 UNV,Macula 標原文。所以這是**以 Strong 號為主鍵的 JOIN,不是猜測**。

```
UNV+SN (FHL 標註)  ──┐
                     ├─ JOIN on Strong number ──►  Burrito 對齊層
WLC.tsv (Macula 標註)┘        (零語義猜測)
```

## Status — 方法已驗證,交付物未產出

| 項目 | 狀態 |
|---|---|
| 對齊方法可行性 | ✅ 創世記 1532 節,核心 **97.4%** |
| FHL↔Macula 變體等價表 | 🟡 自動學習可行(8 條,5 真 3 雜訊),僅創世記 |
| `targets/cmn/UNV/{ot,nt}_UNV.tsv` | ❌ **未產** ← 最大工作量 |
| `alignments/UNV/WLC-UNV-*.json` | ❌ **未產**(v3 遺失了 v2 的 emit 能力) |
| TOML metadata | ❌ 未產 |
| 全舊約 39 卷 / 新約 | ❌ 只驗證了創世記 |
| `Manager` round-trip 驗證 | ❌ 未做 |

## Commands

```bash
# 依賴(一次性)
pip3 install biblelib unicodecsv

# 單章
python3 poc/poc_v4.py --book 創 --chaps 1

# 全卷,並輸出 Burrito JSON
python3 poc/poc_v4.py --book 創 --chaps 1-50 --emit-json gen.json

# 換書卷(中文或英文代碼皆可)
python3 poc/poc_v4.py --book Dan --chaps 7      # 唯一含 09004 的一節在此
```

執行前提:**全程離線**(讀本地 `bible_little.db` / `bible_parsing.db`),
且 `../Alignments/` checkout 存在。單次執行約 30 秒 —— 變體表每次重新掃全庫建立。

輸出雜訊過濾:`2>&1 | grep -vE 'No source selectors|^        '`(`Manager` 會噴大量 badrecord 警告)。

> `poc/poc_v3.py` 保留作對照(自學變體表的舊法),**已被 v4 取代,不要用**。

## PoC 架構(`poc/poc_v4.py`)

**四步資料流**(全部走本地 SQLite,零 API 呼叫)

```
1. bible_little.db  unv 表        → UNV+SN 經文
2. Manager(sourceid="WLC")        → 讀 WLC.tsv 的希伯來 token
3. 以 Strong 號 JOIN               → 中文詞 ↔ 原文 token
4. 統計覆蓋率 / 輸出 Burrito JSON
```

**三種 SN 分類**(`classify()`,依 [`SPECIFICATION_v1.9.md`](../../sn_within_unv_selfgroup_segmentation/SPECIFICATION_v1.9.md))——非重疊,各自處理:

| 類 | 判準 | 處理 |
|---|---|---|
| `core` | 其餘 | **主要對齊目標** |
| `prefix` | **5 位數且 `09` 開頭** | 用 `SEED` 表(ל→3807、ב→871…)附著到後續 core |
| `morph` | 標籤含 `T`(`<WTH8804>`) | **略過**——構形碼不對應任何原文「字」 |

> ⚠️ 4 位數的 `<0914>` **不是** 900x 前綴。誤判會把 `0853`/`4480`/`5921` 等實詞當成前綴,曾導致前綴表整個失真。

> **規格版本**:`SPECIFICATION_v1.9.md` 是**權威規格**(v1.8 的 additive superset,900x 判定規則未變);`SPECIFICATION_v1.8.md` 是 `parse_verse_v1_8.py` 實際載入驗證的**實作基準**,標記 immutable、**不可編輯**。兩者對本 survey 的分類規則等價。

> ⚠️ **做新約時必讀** `SPECIFICATION_v1.9.md` §6.1.1(v1.9 新增):qp.php 的欄位語義 **OT/NT 不對稱** —— 舊約 `pro` 為空、詞類與詞形全在 `wform`;新約 `pro` 才是詞類、`wform` 只有屈折資訊。現行規格的 parsing 推斷是 **OT-centric** 的,擴展到新約必須改為先讀 `pro` 再讀 `wform`,否則樣式比對會失敗。

**變體表:查 FHL 自己的 qb ↔ qp,不自學**

規格(v1.7.2 起)已規定「**qb 與 qp 用不同 SN 時,以 qp 為準**」。`build_variant_map()`
就是把這條規則具體化:比對兩個來源的逐節 SN 殘差,**只採「恰 1 個 qb-only × 恰 1 個
qp-only」的無歧義配對**,因此不需要任何統計啟發式。

產出 **30 條,幾乎全 100% 一致性**:

| qb → qp | 次數 | 一致性 | 說明 |
|---|---:|---:|---|
| `6440` → `3942` | 538 | 100% | `לִפְנֵי` 複合詞 —— 規格 §1.8 明文記載 |
| `3212` → `1980` | 486 | 100% | הלך 行走 |
| `582` → `376` | 231 | 100% | אִישׁ 人 |

> ⚠️ **v3 的自學法已廢棄**。它用「殘差共現 + lift」統計,8 條中 3 條是詞尾碎片雜訊
> (`ִי`、`ֵנוּ`),且把這個分歧誤判為「FHL vs Macula 跨機構差異」——**實際上是 FHL
> 內部 qb↔qp 的差異,規格早有裁決**。詳見 [`FHL_900X_FINDINGS.md`](FHL_900X_FINDINGS.md) § 二之二。

**實測覆蓋率**

| 範圍 | 節數 | 核心 | 前綴 |
|---|---:|---:|---:|
| 創 1 | 31 | **100.0%** | 91.9% |
| 創 1–50 | 1,532 | **97.5%**(原號 19,213 · 變體 183) | 88.6% |
| 但 7 | 28 | **98.5%** | 78.4% |
| 得 1 | 22 | **100.0%** | 81.8% |

> 未對齊的 token **不建 record**(Burrito 慣例,見 [`BURRITO_FORMAT.md`](BURRITO_FORMAT.md)),
> 故 record 數 = 已對齊核心數。

> **`lift` 正規化不可省**。沒有它,所有未對上的號會被高頻的 וְ(2050)吸走,產出看似更高(97.9%)但完全錯誤的結果。`PARTICLES` 集合排除高頻虛詞是同一道防線。

## Key decisions locked

- **來源一律 `WLC.tsv`,絕不用 `WLCM.tsv`** —— 後者缺 lemma、strongs 無 `H` 前綴,被 `Manager` 讀取時會**自動補成 `G`**,把希伯來文標成希臘文。詳見 `aboarding.md`。
- **`../Alignments/` 是唯讀資料源** —— 只讀 `data/sources/*.tsv` 與 TOML 範本,不寫入、不 commit。已重置至 `c99bd0a`(= `origin/main`)。
- **判準只信 `sources/*.tsv` 的實際 schema** —— 對齊檔名、TOML `identifier`/`scope`、甚至 `docs/formats.md` 都與實況矛盾過(見 `aboarding.md`〈WLC/WLCM 矛盾〉)。
- **FHL 授權已確認**(Joshua,FHL 卸任董事)。產 TOML 時須將 FHL 列為 SN 標註出處。
- **交付格式是 Burrito** —— 不論上游收不收,產出的都是 Burrito;它同時是 **s12 的介面契約**。

## ⚠️ 未決架構決策 — A / B 對齊路線

UNV 在 LCC 的上游(`WLC → UNV → LCC`),故 LCC 的對齊有兩種掛法:

| 路線 | 對齊檔 | 取捨 |
|---|---|---|
| **A** 都掛回原文 | `WLC-LCC-*.json` | 與其他 12 譯本一致、可貢獻上游;丟失「經由 UNV 推導」的事實 |
| **B** 兩層對齊 | `WLC-UNV-*` + `UNV-LCC-*` | 忠實記錄推導鏈、保留審核所需的「相對 UNV 誤差」;非標準用法 |

傾向**兩者都做**(B 為工作真相,A 由 B 合成對外交付),但**尚未定案**。
**此決策直接決定 [s12](../survey12_segment_target_verse/) 的產出形狀** —— 詳見
[`BURRITO_FORMAT.md` §未決:A / B 兩條對齊路線](BURRITO_FORMAT.md)。

## 已知陷阱

- **`sourceid` 綁死兩條路徑** —— `AlignmentSet` 的 `sourceid` 同時決定 `sources/{sourceid}.tsv` **和** `alignments/{targetid}/{sourceid}-{targetid}-*.json`。想讀 BSB 舊約對齊就被迫寫 `sourceid="WLCM"`,連帶載入壞檔。PoC 靠**改用 YLT**(唯一叫 `WLC-YLT-manual.json` 者)繞過。
- **v3 沒有 `--emit-json`** —— v2 有,但 v2 已隨 scratchpad 被清除。要重新產出 Burrito JSON 需移植約 10 行。
- **API 呼叫翻倍** —— 用的是 `fetch_chap`(無快取)而非 `fetch_chap_cached`,兩趟 Pass 各抓一次。
- **書卷寫死** —— `fetch_chap("創", …)` 與 `bcv = f"01{ch:03d}…"` 都綁定創世記,換卷要改碼。

## Downstream — s13 是 s12 的基石

**[`../survey12_segment_target_verse/`](../survey12_segment_target_verse/)** 消費本 survey 的產出:循已進入 Burrito 的 UNV+SN,逐節分詞目標經文(LCC …)。**編號雖大,s13 在流程上位於 s12 之上游**;s12 開工前需先確認本 survey 的 target corpus 與 alignment 檔已完成。

## Documents

| 檔案 | 內容 |
|---|---|
| **[`aboarding.md`](aboarding.md)** | **必讀**。Clear Bible / WLC 來歷考證、完整名詞解釋(機構/文本學/語料庫/版本名)、Scripture Burrito 定位論證、s13↔s12 關係、授權狀態 |
| **[`BURRITO_FORMAT.md`](BURRITO_FORMAT.md)** | **動手前必讀**。以真實資料拆解 Burrito 四件套、BCVWP ID 解剖、創 1:1(希→英)與約 3:16(希臘→英)逐 record 實例、TOML 全文、**s13 要為 UNV 產什麼的具體對照** |
| **[`FHL_900X_FINDINGS.md`](FHL_900X_FINDINGS.md)** | 全庫 31,103 節 900x 盤點。**含 s13 覆蓋率的結構性上限**:FHL 不標 `ו`(51,004)與 `ה`(30,287),故這些 source token 永久未對齊(不應強建 record)。另有給 SPEC v1.9 擁有者的四項增補建議 |
| [`ALIGNMENTS_PACKAGE_NOTES.md`](ALIGNMENTS_PACKAGE_NOTES.md) | `bible_alignments` 套件架構(讀取管線、BCVWP token ID 方案、macula prefix 機制) |
| `prompt.history` / `response.history` | 孵化過程的完整 provenance(兩者皆為 active switch,見全域 CLAUDE.md) |
