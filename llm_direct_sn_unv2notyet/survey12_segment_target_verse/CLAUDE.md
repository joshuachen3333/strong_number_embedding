# survey12_segment_target_verse

> Seeded 2026-07-28 by `Alignments-obe`, from the **s13 incubation session**.
> This file captures the design ideas that emerged while building s13 — it is a
> **plan of record, not a report of completed work**. No code exists here yet.

## What this survey does

**循著已進入 Burrito 的 UNV+SN,逐節逐節地分詞目標經文**(LCC、RCUV2010 …)。

The chain:

```
原文 (WLC/SBLGNT tokens)
      │  ← s13 建立此層(Strong-number JOIN,非語義猜測)
      ▼
UNV+SN  ──Burrito 對齊層──►  逐節錨點
      │
      ▼  ← s12 在此工作
目標譯本(LCC …)逐節分詞
```

## Upstream dependency — **s13 is the foundation**

**[`survey13_unv_sn_to_burrito/`](../survey13_unv_sn_to_burrito/)** produces the alignment
layer this survey consumes. Despite the higher number, **s13 is upstream of s12**.

Read **[`../survey13_unv_sn_to_burrito/aboarding.md`](../survey13_unv_sn_to_burrito/aboarding.md)**
before working here — it holds the Clear Bible / WLC provenance, the full glossary, and
the Burrito rationale.

### The interface contract: Scripture Burrito

s13's deliverable is **Burrito-format** data, and that format *is* the contract between
the two surveys. Three files, all required — an alignment file cannot be interpreted
without its corpora:

| File | Produced by | Content |
|---|---|---|
| **source corpus** `sources/WLC.tsv` | Clear Bible (existing) | 原文 token + Strong + lemma + morph |
| **target corpus** `targets/cmn/UNV/{ot,nt}_UNV.tsv` | **s13 (未完成)** | UNV token,BCVWP 12 碼 ID |
| **alignment file** `alignments/UNV/WLC-UNV-*.json` | **s13 (未完成)** | source↔target token 對應 |

> ⚠️ **s13 現況**:對齊方法已驗證(創世記核心 97.4%),但 **target corpus 與 alignment
> 檔尚未產出**。s12 開工前需先確認 s13 這兩塊完成。

### ⚠️ 未決:s12 的產出要掛哪一種對齊?

LCC 在 `WLC → UNV → LCC` 這條鏈的末端,因此 s12 的成果有兩種表達法:

| 路線 | s12 產出 | 取捨 |
|---|---|---|
| **A** 掛回原文 | `WLC-LCC-*.json` | 與其他 12 譯本一致、可貢獻上游;丟失「經由 UNV 推導」的事實 |
| **B** 兩層對齊 | **`UNV-LCC-*.json`** | 忠實記錄推導鏈;**保留人工審核最需要的「相對 UNV 誤差」** |

**這直接決定 s12 要產什麼檔**,尚未定案。技術上 B 可行(`SourceidEnum.get_canon()`
對未登錄 source 回傳 `'X'` 而非報錯)。傾向兩者都做:B 為工作真相,A 由 B 合成。

詳見 [`../survey13_unv_sn_to_burrito/BURRITO_FORMAT.md` §未決:A / B 兩條對齊路線](../survey13_unv_sn_to_burrito/BURRITO_FORMAT.md)。

## Why this route works

UNV 的每個 SN 一旦錨定到原文 token,**目標譯本的分詞就有了原文級的參照框架**——不再是
盲目的中文斷詞,而是「這一段中文對應原文的哪幾個 token」。這正是 `chinese_term_segmentation/`
裡 `BoundaryCorrector` 的思路(以 UNV+SN 邊界修正目標分詞),差別在於 s12 拿到的是
**經過原文校準**的邊界,而非僅 UNV 自身的邊界。

## Known traps — inherited from the s13 incubation

這些是 s13 孵化過程中實測踩到的,**s12 會撞到同樣的坑**:

### 1. `WLC.tsv` 才是正解,不是 `WLCM.tsv`

`WLCM.tsv` 缺 `lemma`、strongs 無 `H` 前綴 → 經 `Manager` 讀取時 **reader 會一律補
`G`**,把希伯來文標成希臘文,H/G 判別徹底毀損。

> `docs/formats.md` 官方寫「WLCM 是 WLC 的 Macula 版本」,但**實際檔案內容相反**。
> **只信 `sources/*.tsv` 的實際 schema。**

### 2. `AlignmentSet` 的 `sourceid` 綁死兩條路徑 ⚠️

```python
sourcepath    = sources/{sourceid}.tsv
alignmentpath = alignments/{targetid}/{sourceid}-{targetid}-{alternateid}.json
```

想讀 **BSB 的舊約對齊**就被迫寫 `sourceid="WLCM"`(因為檔名是 `WLCM-BSB-manual.json`),
**而那會連帶載入壞掉的 `WLCM.tsv`**。兩者無法分離。

s13 的繞法:改用 **YLT**(唯一命名為 `WLC-YLT-manual.json` 者)。若 s12 需要 BSB,
得手動覆寫 `sourcepath` 或建 `WLC-BSB-manual.json` symlink。

### 3. SN 三分類必須分開處理(SPEC v1.8)

| 類 | 判準 | 處理 |
|---|---|---|
| **core** | 其餘 | 對齊主體 |
| **prefix** | **5 位數且 `09` 開頭** | 附著到後續 core;`09001 ל→3807`、`09002 ב→871`、`09003 כ→3509` |
| **morph** | `<WTH8ddd>` | **略過** —— 構形碼不對應任何原文 token |

> 陷阱:4 位數的 `<0914>` **不是** 900x 前綴。s13 曾因 `'A' in letters` 誤把
> `0853`(את)、`4480`(מן)、`5921`(על)判成前綴,污染整張前綴表。

### 4. FHL 與 Macula 是兩套獨立 Strong 標註

同一個希伯來字兩邊編號可能不同,需**變體等價表**。s13 用殘差共現 + lift 正規化自動學到
(以 WLC 的 `lemma` 欄交叉驗證):

| FHL | Macula | lemma |
|---|---|---|
| 3212 | 1980 | הלך(行走) |
| 582 | 376 | אִישׁ(人) |
| 7462 | 7473 | רעה_1(牧養) |
| 6948 | 6945 | קָדֵשׁ_1 |
| 2425 | 2421 | חיה(活) |

> ⚠️ 學習器**必須**排除高頻虛詞(ו ה ל ב כ מ את)並做 lift 正規化,否則所有未對上的號
> 都會被 וְ 吸走,產生**假的**高覆蓋率。s13 第一版即栽在此(假 97.9% → 真 97.4%)。

### 5. 覆蓋率預期

創世記實測:**核心 97.4%**、前綴 ~86%、morph 全略過(正確)。s12 應預期
**~2.6% 的目標詞沒有原文錨點**,需有 fallback 策略。

## Data source policy

`../Alignments/` 是 **Clear-Bible/Alignments 的第三方 checkout**,定位 **唯讀資料源**:
只讀、不寫、不 commit。s13 已於 2026-07-28 將其重置至 `origin/main`(`c99bd0a`)。

## Licensing

FHL 的 SN 標註授權由 **Joshua(FHL 卸任董事)確認無虞**,可用於本專案並以 CC-BY-4.0
產出。TOML 須將 FHL 列為 SN 標註出處。

## Status

**尚未實作。** 開工前置條件:s13 產出 target corpus + alignment 檔。
