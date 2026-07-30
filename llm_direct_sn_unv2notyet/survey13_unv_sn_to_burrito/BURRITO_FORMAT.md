# Burrito 架構格式拆解

> 以 **Alignments 專案**(`github.com/Clear-Bible/Alignments`)的真實資料逐層拆解 Scripture Burrito / AlignmentHub 對齊格式。
> 所有範例列、ID、JSON record 均直接取自 `../Alignments/data/`,非示意。撰於 2026-07-30。
>
> 指涉約定同 [`aboarding.md`](aboarding.md):**Alignments 專案** = 上游資料集;**本專案 / s13** = 本 survey。

---

## 四件套

| 檔案 | 路徑範例 | 角色 |
|---|---|---|
| **source corpus** | `data/sources/WLC.tsv` | 原文 token 表(含 Strong / lemma / morph) |
| **target corpus** | `data/eng/targets/BSB/ot_BSB.tsv` | 譯本 token 表 |
| **alignment file** | `data/eng/alignments/BSB/WLCM-BSB-manual.json` | 兩者的 token 對應 |
| **metadata** | 同名 `.toml` | 來源 / 授權 / 製程 |

> ⚠️ **alignment 檔只存 ID 對應,不存文字**——缺了任一 corpus 就完全無法解讀。這是 Burrito「三者一組」的硬約束。

---

## BCVWP token ID 解剖

**Source(12 碼 + canon 前綴)**

```
o 01 001 001 001 2
│  │   │   │   │  └─ Part    詞素序(1=前綴, 2=詞幹…)
│  │   │   │   └──── Word    詞序
│  │   │   └──────── Verse   節
│  │   └──────────── Chapter 章
│  └──────────────── Book    卷(01=創世記)
└─────────────────── Canon   o=舊約, n=新約(macula prefix)
```

**Target(11 碼,無前綴、無 part)**

```
01 001 001 003
Book Chap Verse Word
```

> ⚠️ **兩側不對稱**:原文有詞素切分(part),譯文沒有。這正是希伯來文前綴能單獨對齊的基礎。

---

# 實例一:創世記 1:1(希伯來 → 英文)

## ① source corpus 真實列(`WLC.tsv`)

```
id              text        strongs  gloss      gloss2  lemma      pos   morph
o010010010011   בְּ          H0871a   in                 בְּ         prep  Pp
o010010010012   רֵאשִׁ֖ית     H7225    beginning  起初    רֵאשִׁית    noun  ncfsa
o010010010021   בָּרָ֣א       H1254    he created 创造    ברא_1      verb  vqp3ms
o010010010031   אֱלֹהִ֑ים     H0430    God        神      אֱלֹהִים    noun  ncmpa
o010010010041   אֵ֥ת         H0853    -          -       אֵת_1      om    Po
o010010010051   הַ          H1886a   the                הַ         art   Pa
o010010010052   שָּׁמַ֖יִם     H8064    heavens    诸天    שָׁמַיִם    noun  ncmpa
o010010010061   וְ          H2050b   and        与      וְ         cj    Pc
o010010010062   אֵ֥ת         H0853    -          -       אֵת_1      om    Po
o010010010071   הָ          H1886a   the                הַ         art   Pa
o010010010072   אָֽרֶץ        H0776    earth      地      אֶרֶץ       noun  ncfsa
```

**關鍵觀察**:`בְּרֵאשִׁית`(在起初)被切成**同一個 word 的兩個 part**:

- `...0011` = `בְּ`(介系詞前綴)
- `...0012` = `רֵאשִׁית`(名詞詞幹)

### 順帶:`gloss2` 欄帶簡體中文

`gloss2` 有中文 glosses(起初 / 创造 / 神 / 诸天 / 与 / 地)。用途界線要劃清:

- ✅ **可作事後交叉驗證** —— join 出「起初 ↔ רֵאשִׁית」時,`gloss2` 也寫「起初」,是獨立的第二證據(同 lemma 驗證變體表之理)
- ❌ **不可作輸入** —— s11 文件明訂 *"the Chinese `gloss2` column is always dropped"*,餵進去會造成**中文答案洩漏**

## ② target corpus 真實列(`ot_BSB.tsv`)

```
01001001001  In          01001001007  heavens
01001001002  the         01001001008  and
01001001003  beginning   01001001009  the
01001001004  God         01001001010  earth      ← skip_space_after=y
01001001005  created     01001001011  .          ← exclude=y
01001001006  the
```

## ③ alignment file 真實 record

```json
{
  "source": ["o010010010011", "o010010010012"],
  "target": ["01001001001", "01001001002", "01001001003"],
  "meta":   {"id": "01001001.001", "origin": "manual", "status": "created"}
}
```

全節攤開:

| record | 原文 | ↔ | 英文 | 比例 |
|---|---|---|---|---|
| `.001` | בְּ + רֵאשִׁית | → | In the beginning | **2:3** |
| `.002` | בָּרָא | → | created | 1:1 |
| `.003` | אֱלֹהִים | → | God | 1:1 |
| **`.004`** | **(不存在)** | | | ⚠️ |
| `.005` | הַ + שָּׁמַיִם | → | the heavens | 2:2 |
| `.006` | וְ + אֵת | → | and | **2:1** |
| `.007` | הָ + אָרֶץ | → | the earth | 2:2 |

## 這一節示範的五個現象

1. **詞素獨立對齊** —— `בְּ`(part 1)與 `רֵאשִׁית`(part 2)一起對到 "In the beginning"
2. **語序重排** —— `בָּרָא`(原文第 **2** 字)對到英文第 **5** 字;`אֱלֹהִים`(第 3 字)對到英文第 **4** 字
3. **未對齊 token** —— **`.004` 整筆記錄不存在**,因為 `o010010010041` = `אֵת`(H0853 受詞記號,gloss 為 `-`)在英文無對應詞。**Burrito 的作法是乾脆不建記錄,而非建一筆空的**
4. **標點不參與對齊** —— `01001001011`(`.`,`exclude=y`)不出現在任何 record
5. **非 1:1 是常態** —— 2:3、2:1、2:2 皆有

---

# 實例二:約翰福音 3:16(希臘 → 英文)

## source(`SBLGNT.tsv`,注意 `n` 前綴)

```
n43003016001  Οὕτως      G3779  Thus            οὕτω(ς)    adv
n43003016003  ἠγάπησεν   G0025  loved           ἀγαπάω     verb
n43003016010  υἱὸν       G5207  Son             υἱός       noun
n43003016012  μονογενῆ   G3439  only begotten   μονογενής  adj
n43003016013  ἔδωκεν     G1325  He gave         δίδωμι     verb
```

## 最有代表性的 records

```json
{"source": ["n43003016012"], "target": ["43003016011","43003016012","43003016013"]}   // 1:3
{"source": ["n43003016013"], "target": ["43003016008","43003016009"]}                 // 1:2
```

| record | 希臘 | ↔ | 英文 | 現象 |
|---|---|---|---|---|
| `.012` | μονογενῆ | → | **one and only** | **1:3** 一字對三字 |
| `.013` | ἔδωκεν | → | **He gave** | **1:2** 動詞含主詞 |
| `.001` | Οὕτως(第 1 字) | → | so(第 **3** 字) | 重排 |
| `.010` | υἱὸν(第 **10** 字) | → | Son(第 **14** 字) | 重排跨 4 位 |
| `.009` | τὸν(冠詞) | → | **His** | 冠詞 → 所有格 |
| **`.004` / `.011`** | **(不存在)** | | | `ὁ` / `τὸν` 冠詞未對齊 |

> 值得注意:**同一個 `τὸν`(G3588)有時對齊有時不對齊** —— `.006`→"the"、`.009`→"His",但 `.011` 完全沒記錄。
> **這是人工判斷的痕跡,不是機械規則。**

---

# TOML metadata 真實全文

```toml
[source]
identifier   = "WLC"                    # ⚠️ 檔名是 WLCM,metadata 自承來源是 WLC
copyright    = "© 2023 The J. Alan Groves Center for Advanced Biblical Research"
license      = "Custom"
licensenotes = "...Unicode/XML Leningrad Codex: UXLC 1.8 (26.9), Tanach.us..."

[target]
identifier   = "BSB"
license      = "Public domain"
name.eng     = "Berean Standard Bible"
url          = "https://www.bereanbible.com/"

[alignment]
identifier   = "WLCM-BSB-manual"
format       = "grapecity"
license      = "CC-BY-4.0"
process      = "manual"                 # manual / transfer(自動移轉)
scope        = "NT"                     # ⚠️ 標錯,這是舊約對齊
team         = "Clear"
```

三節結構固定:**誰是原文、誰是譯本、對齊本身怎麼來的**。

> `process` 欄值得注意 —— **本專案(s13)的產出應標成 `strongjoin` 之類,誠實反映非人工**。
> 另須將 **FHL 列為 SN 標註出處**(比照 `[source]` 標註 Groves Center 的作法)。

---

# 對照:s13 要為 UNV 產什麼

UNV 創 1:1 原始資料(FHL):

```
起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>{<WH0853>}天<WH08064>{<WH0853>}地<WH0776>。
```

## 要產的 target corpus(`targets/cmn/UNV/ot_UNV.tsv`)

```
01001001001  01001001  起初
01001001002  01001001  ，        ← exclude=y
01001001003  01001001  神
01001001004  01001001  創造
01001001005  01001001  天
01001001006  01001001  地
01001001007  01001001  。        ← exclude=y
```

## 要產的 alignment(`alignments/UNV/WLC-UNV-strongjoin.json`)

| record | 原文 | ↔ | 中文 | 比例 |
|---|---|---|---|---|
| `.001` | בְּ + רֵאשִׁית | → | 起初 | **2:1** |
| `.002` | אֱלֹהִים | → | 神 | 1:1 |
| `.003` | בָּרָא | → | 創造 | 1:1 |
| `.004` | הַ + שָּׁמַיִם | → | 天 | **2:1** |
| `.005` | הָ + אָרֶץ | → | 地 | **2:1** |

## 中文的比例正好反轉

英文是 **2:3**(`בְּרֵאשִׁית` → "In the beginning"),中文是 **2:1**(→「起初」)。

中文更緊湊,**多對一是常態** —— 這對對齊演算法反而是**好事**(候選空間更小)。

## 但中文有個獨有難點

**英文靠空格就能切 token,中文不行。**

上表的 target corpus 看似簡單,實際上「起初 / 神 / 創造 / 天 / 地」這個切法是從 **FHL 的 SN 標籤邊界**反推出來的 —— SN 貼在哪個字後面,就切在哪裡。

**這正是 [s12](../survey12_segment_target_verse/) 存在的理由**:一旦 UNV 的 token 邊界被原文錨定,`LCC`、`RCUV2010` 這些**沒有 SN** 的譯本就有了原文級的分詞參照框架,不必盲目斷詞。

---

## 資料出處

本檔所有範例均可重現:

```bash
A=../Alignments/data

# source corpus
awk -F'\t' '$1 ~ /^o01001001/' $A/sources/WLC.tsv
awk -F'\t' '$1 ~ /^n43003016/' $A/sources/SBLGNT.tsv

# target corpus
awk -F'\t' '$1 ~ /^01001001/'  $A/eng/targets/BSB/ot_BSB.tsv

# alignment records
python3 -c "import json;d=json.load(open('$A/eng/alignments/BSB/WLCM-BSB-manual.json'));[print(r) for r in d['records'] if r['meta']['id'].startswith('01001001')]"
```
