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

# 單章快速驗證
python3 poc/poc_v3.py --chaps 1

# 全卷創世記(學變體表 + 前後對照)
python3 poc/poc_v3.py --chaps 1-50
```

執行前提:**需要網路**(FHL `qb.php` 取 UNV+SN)且 `../Alignments/` checkout 存在。
輸出雜訊過濾:`2>&1 | grep -vE 'No source selectors|^        '`(`Manager` 會噴大量 badrecord 警告)。

## PoC 架構(`poc/poc_v3.py`)

**四步資料流**

```
① fetch_chap("創", ch, strong=1)      → FHL API 取 UNV+SN
② Manager(sourceid="WLC")             → 讀 WLC.tsv 的希伯來 token
③ 以 Strong 號 JOIN                    → 中文詞 ↔ 原文 token
④ 統計覆蓋率                           → 印報告
```

**三種 SN 分類**(`classify()`,依 `SPECIFICATION_v1.8`)——非重疊,各自處理:

| 類 | 判準 | 處理 |
|---|---|---|
| `core` | 其餘 | **主要對齊目標** |
| `prefix` | **5 位數且 `09` 開頭** | 用 `SEED` 表(ל→3807、ב→871…)附著到後續 core |
| `morph` | 標籤含 `T`(`<WTH8804>`) | **略過**——構形碼不對應任何原文「字」 |

> ⚠️ 4 位數的 `<0914>` **不是** 900x 前綴。誤判會把 `0853`/`4480`/`5921` 等實詞當成前綴,曾導致前綴表整個失真。

**兩趟 Pass + 變體表學習**

1. **Pass 1** 純用原號 join(基準 96.6%),同時記錄「未對上的 FHL 號 × 節內剩餘的 Macula 號」共現。
2. **學習**:用 `lift` 正規化評分挑出真正的等價對,並以 **WLC 的 lemma 欄交叉驗證**。
3. **Pass 2** 套用變體表重跑 → 97.4%。

已學到的真實等價對(lemma 驗證):`3212≡1980`(הלך 行走)、`582≡376`(אִישׁ 人)、`7462≡7473`、`6948≡6945`、`2425≡2421`。

> **`lift` 正規化不可省**。沒有它,所有未對上的號會被高頻的 וְ(2050)吸走,產出看似更高(97.9%)但完全錯誤的結果。`PARTICLES` 集合排除高頻虛詞是同一道防線。

## Key decisions locked

- **來源一律 `WLC.tsv`,絕不用 `WLCM.tsv`** —— 後者缺 lemma、strongs 無 `H` 前綴,被 `Manager` 讀取時會**自動補成 `G`**,把希伯來文標成希臘文。詳見 `aboarding.md`。
- **`../Alignments/` 是唯讀資料源** —— 只讀 `data/sources/*.tsv` 與 TOML 範本,不寫入、不 commit。已重置至 `c99bd0a`(= `origin/main`)。
- **判準只信 `sources/*.tsv` 的實際 schema** —— 對齊檔名、TOML `identifier`/`scope`、甚至 `docs/formats.md` 都與實況矛盾過(見 `aboarding.md`〈WLC/WLCM 矛盾〉)。
- **FHL 授權已確認**(Joshua,FHL 卸任董事)。產 TOML 時須將 FHL 列為 SN 標註出處。
- **交付格式是 Burrito** —— 不論上游收不收,產出的都是 Burrito;它同時是 **s12 的介面契約**。

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
| [`ALIGNMENTS_PACKAGE_NOTES.md`](ALIGNMENTS_PACKAGE_NOTES.md) | `bible_alignments` 套件架構(讀取管線、BCVWP token ID 方案、macula prefix 機制) |
| `prompt.history` / `response.history` | 孵化過程的完整 provenance(兩者皆為 active switch,見全域 CLAUDE.md) |
