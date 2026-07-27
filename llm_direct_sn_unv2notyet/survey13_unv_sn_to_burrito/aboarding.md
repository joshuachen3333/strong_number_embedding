# aboarding.md — Clear Bible / WLC 背景考證

> 本檔記錄 **Alignments 專案**的組織與文本來歷,供接手者快速理解「這批資料是誰做的、原文底本從哪來」。
> 所有結論皆以 Alignments repo 內的檔案為證據,非憑記憶。撰於 2026-07-28。

## 沿襲(Lineage)

本 survey(**s13**)沿襲自 **Clear Bible 的 Alignments 專案**:

| | |
|---|---|
| **上游來源** | **`https://github.com/Clear-Bible/Alignments`** |
| 本地 checkout | `../Alignments/`(**唯讀資料源**,已重置至 `origin/main` = `c99bd0a`) |
| 沿襲內容 | Scripture Burrito / AlignmentHub 對齊格式、`sources/WLC.tsv` 與 `SBLGNT.tsv` 原文 token 表、TOML metadata 慣例、BCVWP token ID 方案 |
| 本 survey 的目標 | 依同一格式產出 **UNV** 的對齊資料,使其可成為 Alignments 的第 11 個語言(`cmn`)/ 第 13 個譯本 |

孵化階段的工作原本在 `../Alignments/` checkout 內進行,已於 2026-07-28 全數移出至本目錄;該 checkout 自此僅作唯讀資料源。

## ⚠️ 指涉約定(本檔全文適用)

本檔搬出 Alignments 後,「repo / 專案」的指涉須明確區分:

| 用語 | 指的是 | 位置 |
|---|---|---|
| **Alignments 專案** / **Alignments repo** | Clear Bible 的上游資料集 | `github.com/Clear-Bible/Alignments` |
| **本專案** / **s13** | 本 survey | `survey13_unv_sn_to_burrito/`,隸屬 `github.com/joshuachen3333/strong_number_embedding` |

> 早期段落若出現未限定的「本 repo」,一律指 **Alignments 專案**——因為那些考證都是針對它的資料所做。

---

## Clear Bible — 組織

**Clear Bible, Inc.**(clear.bible)是做**聖經翻譯計算工具與開放資料集**的機構,也是 **Alignments 專案**的擁有者(`github.com/Clear-Bible`)。

### Alignments 專案內證據

| 檔案 | 內容 | 意義 |
|---|---|---|
| `LICENSE.md` | 程式碼 © 2023 **Clear Bible, Inc**(MIT) | 原始版權方 |
| `README.md` | 程式碼 © 2024 **Biblica, Inc** | 兩份版權並存,反映 **Clear Bible 已併入 Biblica**(國際聖經協會) |
| 對齊 `*.toml` | `team = "Clear"`,`license = "CC-BY-4.0"` | 對齊工作由 Clear 團隊執行 |

### 對本專案(s13)的關鍵意義

我們 join 用到的 **SN / morph 標註,全部出自 Clear Bible 的 Macula 資料集**:

- **`macula-hebrew`**(AGENTS.md 明載)→ 舊約
- **`macula-greek`** → 新約

所以 Clear Bible 是**雙重身分**:既提供**對齊資料**,也提供**標註過的原文 token 表**。

---

## WLC — 文本

**Westminster Leningrad Codex**。四層要分清,別混為一談:

| 層 | 是什麼 |
|---|---|
| **列寧格勒抄本** | 實體手稿(Codex Leningradensis **B19A, 1008 AD**),現存最古老最完整的希伯來聖經馬索拉文本 |
| **WLC** | Westminster 的數位轉錄版,由 **J. Alan Groves Center for Advanced Biblical Research**(Westminster 神學院)製作 |
| **UXLC** | Unicode/XML 發行版,經 **tanach.us** 散布 |
| **`WLC.tsv`(Alignments 專案)** | Macula 再加標註:**H 前綴 strongs + lemma + morph** |

### TOML 直接寫死了這條鏈

```toml
identifier   = "WLC"
copyright    = "© 2023 The J. Alan Groves Center for Advanced Biblical Research"
licensenotes = "...Unicode/XML Leningrad Codex: UXLC 1.8 (26.9), Tanach.us..."
```

授權寬鬆:「所有希伯來聖經文本可無限制檢視或複製」。

---

## WLCM 的 metadata 缺陷(支持 survey10-obe 的更正)

查 TOML 時撿到的證據,說明 **`WLCM` 不是獨立來源資料集**:

1. **`WLCM-BSB-manual.toml` 裡 `identifier = "WLC"`**
   檔名叫 WLCM,但 metadata 自己承認來源是 **WLC**。
   → **最硬的證據:WLCM 純粹是檔名產物。**

2. **同一個檔 `scope = "NT"`**
   但 WLCM-BSB 明明是**舊約**對齊。metadata 標錯。

### 其他已知 metadata 錯誤

| 檔案 | 問題 |
|---|---|
| `WLCM-OHCB-manual.json` | 內部 source `docid` 誤標成 **`SBLGNT`**(實為 OT 來源) |
| `WLCM-RV09-manual.json` | 內部 docid 為**小寫 `wlcm`** |
| `WLC-YLT-manual.json` | 命名不一致(其餘 OT 對齊皆用 `WLCM-` 前綴) |

**結論:這批 OT 對齊檔的 metadata 有系統性品質問題。應以 `sources/*.tsv` 的實際 schema 為準,不要相信對齊檔名或 TOML 的 `identifier` / `scope` 欄。**

### WLC.tsv vs WLCM.tsv 實測差異

| | `WLC.tsv`(9 欄,**正解**) | `WLCM.tsv`(8 欄,壞 schema) |
|---|---|---|
| `strongs` | **`H0871a`**(有 H 前綴)✅ | `0871a`(無前綴)⚠️ |
| `lemma` | **有**(`בְּ`)✅ | **無此欄** ⚠️ |
| `pos` | `prep`(縮寫) | `preposition`(全字) |
| `morph` | `Pp`(碼) | 空 |

> ⚠️ **關鍵陷阱**:`WLCM.tsv` 經 `Manager` 讀出來會變成 **`G0871a`** —— reader 對無前綴的 strongs **一律補 `G`**,把希伯來文標成希臘文,**H/G 判別徹底毀損**。這比「無前綴」更糟,是主動污染。

---

## 統一基石措辭

| Canon | 書卷 | 來源 | 底本 | SN / morph 出處 |
|---|---|---|---|---|
| OT | 01–39 | **`WLC.tsv`** | 列寧格勒抄本(馬索拉文本) | macula-hebrew(`H0871a` + lemma) |
| NT | 40–66 | **`SBLGNT.tsv`** | 希臘文新約校勘本 | macula-greek(`G0976`,morph `N-NSF`) |

**BSB 英文橋貫穿;ground truth 仍是 FHL。**

---

## 一句話總結

**Clear Bible 是做這套東西的組織(含 Macula 標註),WLC 是它採用的舊約原文底本(列寧格勒抄本的 Westminster 數位版)。**

我們的 UNV+SN 逆向 join,本質就是把 **FHL 的中文側標註**,接到 **Clear Bible 的 Macula 原文側標註**。

---

# 名詞解釋(Glossary)

> 標 ✅ 者為 **Alignments 專案**內檔案直接佐證;未標者為通識背景。

## A. 機構 / 組織

| 名稱 | 中文 | 角色 | 證據 |
|---|---|---|---|
| **Clear Bible, Inc.** | — | **Alignments 專案**擁有者;Macula 標註產出方 | ✅ `LICENSE.md` © 2023;TOML `team="Clear"` |
| **Biblica** | **國際聖經協會**(前 International Bible Society) | 承接方;ONAV / OHCB 譯本出版者;NIV 出版者 | ✅ `README.md` © 2024;TOML `team="Biblica"` |
| **United Bible Societies (UBS)** | **聯合聖經公會** | 各國聖經公會的聯合組織(1946 創立);OHCB 版權方 | ✅ OHCB TOML © 2024 |
| **American Bible Society (ABS)** | **美國聖經公會** | 1816 年創立的美國機構 | ⚠️ **Alignments 專案完全未出現**(grep 無命中) |
| **Society of Biblical Literature (SBL)** | 聖經文學學會 | SBLGNT 出版者 | ✅ 每個 SBLGNT TOML |
| **Logos Bible Software** | — | SBLGNT 共同版權方(Faithlife) | ✅ 同上 |
| **J. Alan Groves Center** | Groves 高等聖經研究中心(隸屬 **Westminster 神學院**,費城) | **WLC 數位化製作方** | ✅ WLC TOML © 2023 |
| **BiblioNexus** | — | 部分對齊資料建置者 | ✅ OHCB TOML;BSB `creator` |
| **FHL 信望愛** | — | UNV+SN 的 SN 標註來源(本專案 s13 的 ground truth) | Alignments 專案外部 |

> ### ⚠️ 三個「聖經公會」不可混同
> - **Biblica** = 國際聖經協會(前 IBS,總部科羅拉多)— Alignments 專案中有
> - **United Bible Societies** = 聯合聖經公會 — Alignments 專案中有
> - **American Bible Society** = **美國聖經公會** — **Alignments 專案中沒有**
>
> 三者是**各自獨立的機構**。若文件中看到「美國聖經公會」,多半是把 Biblica 或 UBS 記混了。

## B. 文本學術語

| 術語 | 說明 |
|---|---|
| **馬索拉文本**(Masoretic Text, MT) | 猶太**馬索拉學者(Masoretes)**約 7–10 世紀確立的希伯來聖經標準文本。他們為原本只有輔音的經文,加上**母音符號**(nikkud)與**誦讀重音**(cantillation),使讀法固定下來 |
| **馬索拉學者**(Masoretes) | 提比里亞等地的猶太抄經學者群體,以極嚴謹的計數校勘法保存經文 |
| **列寧格勒抄本** | Codex Leningradensis **B19A**(**1008 AD**),現存**最古老且完整**的 MT 抄本,藏於俄羅斯國家圖書館(聖彼得堡) |
| **亞勒坡抄本**(Aleppo Codex) | 年代更早(約 930 AD)但**殘缺**(部分佚失),故現代版本多改採列寧格勒抄本 |
| **BHS** | *Biblia Hebraica Stuttgartensia*,學界標準希伯來聖經印本,**即以列寧格勒抄本為底本** |
| **校勘本**(critical edition) | 比對眾多抄本異文後重建的學術文本;新約各版(SBLGNT / NA)屬此類 |
| **lemma** | 詞元、字典形(如 בָּרָא 的 lemma 為 `ברא_1`) |
| **morph** | 構形碼(如 `Pp` = 介系詞;`N-NSF` = 名詞-主格-單數-陰性) |
| **Strong's Number** | 原文字彙編號系統(H=希伯來,G=希臘);本專案(s13)的核心 join key |

## C. 語料庫 / 資料集 / 格式

| 名稱 | 說明 |
|---|---|
| **Macula**(`macula-hebrew` / `macula-greek`) | **Clear Bible 的原文標註語料庫**。Alignments 專案所有 SN + lemma + morph 皆出自此。GitHub: `Clear-Bible/macula-hebrew` |
| **UXLC** | *Unicode/XML Leningrad Codex*,列寧格勒抄本的 Unicode/XML 發行版,經 **tanach.us** 散布(TOML 載明版本 **UXLC 1.8 (26.9)**) |
| **WLC** | **Westminster Leningrad Codex** —— 列寧格勒抄本的 Westminster 數位轉錄版(`docs/formats.md` 官方定義) |
| **WLCM** | **WLC 的 Macula 版本**(`docs/formats.md` 官方定義:*"`WLCM` for the Macula version of this"*)⚠️ 但**實際檔案內容與此定義相反**——見〈WLC/WLCM 矛盾〉節;實務上一律用 `WLC.tsv` |
| **Scripture Burrito** | **經文資料的封裝格式標準**(<https://docs.burrito.bible/>)。名稱取自墨西哥捲餅的比喻:**把經文本體、後設資料、版本與授權資訊全部「捲」進同一個自足的包裹**。要解決的痛點是——經文一包、標註一包、授權說明又一包,彼此對不起來。Working Group 正在制定 **Scripture Alignments flavor**,**Alignments 專案即該標準的試作場**(其 README 載明) |
| **AlignmentHub Format** | Clear Bible 對其發布格式的正式稱呼。`docs/formats.md`:*"publish in a standard format we call AlignmentHub Format. This **implements the Scripture Burrito standard**…"* 即 **AlignmentHub Format = Burrito 標準 + Clear Bible 額外慣例** |
| **corpus file** | TSV,一行一 token 的經文檔;分 **source file**(原文,源自 Macula)與 **target file**(譯本) |
| **alignment file** | source↔target 的 token 對應 JSON;**必須**搭配 source/target corpus 才能正確解讀 |
| **vline / vref** | vline = 一行一節的純文字;vref = 同結構但內容為經文參照(USFM 慣例);**vref-vline** 為兩欄 TSV 混合式 |
| **BCVWP** | Book-Chapter-Verse-Word-Part,**12 碼 token ID 方案**(`BBCCCVVVWWWP`) |
| **grapecity** | TOML `format` 欄標示的對齊產製格式標籤 |

## D. 版本名

### 來源(原文文本)

| ID | 全名 | Canon | 實體資料檔? |
|---|---|---|---|
| **WLC** | **Westminster Leningrad Codex** | OT 01–39 | ✅ `WLC.tsv` — 實際帶完整 Macula 標註,**用這個** |
| WLCM | **WLC 的 Macula 版本**(官方定義) | OT | ⚠️ `WLCM.tsv` — 實際為降級匯出(缺 lemma / 缺 `H` 前綴),**勿用** |
| **SBLGNT** | SBL Greek New Testament(2010,ed. M. W. Holmes) | NT 40–66 | ✅ `SBLGNT.tsv` |
| **BGNT** | Berean Greek New Testament | NT | ✅ `BGNT.tsv` |
| NA27 / NA28 | Nestle-Aland *Novum Testamentum Graece* 第 27/28 版 | NT | ❌ **僅列於 `SourceidEnum`,無資料檔** |

### 目標(譯本 — 12 個,涵蓋 10 語言)

| ID | 全名 | 語言 |
|---|---|---|
| **BSB** | Berean Standard Bible | eng |
| **YLT** | Young's Literal Translation | eng |
| **AVD** | Van Dyck(范戴克譯本) | arb |
| **ONAV** | Biblica® Open New Arabic Version 2012 | arb |
| **IRVAsm** | Indian Revised Version (IRV) Assamese 2019 | asm |
| **IRVBen** | Indian Revised Version (IRV) Bengali 2019 | ben |
| **IRVHin** | Indian Revised Version (IRV) Hindi 2019 | hin |
| **LSG** | Louis Segond 1910 | fra |
| **OHCB** | Biblica® Open Hausa Contemporary Bible 2020 | hau |
| **JFA11** | A Bíblia Sagrada, Edição Revista e Corrigida(Almeida 1911) | por |
| **RUSSYN** | Russian Synodal Bible(俄文聖經公會譯本) | rus |
| **RV09** | Reina Valera 1909 | spa |

> 全本聖經(OT+NT)覆蓋:AVD、BSB、YLT、LSG、OHCB、IRVHin、RUSSYN、RV09(8 個)
> 僅新約:ONAV、IRVAsm、IRVBen、JFA11(4 個)

### 本專案(s13)相關中文版本(**不在 Alignments 專案**)

| ID | 全名 | 有 SN? |
|---|---|---|
| **UNV** | 和合本(Chinese Union Version) | ✅ FHL 標註 |
| **LCC** | 呂振中譯本 | ❌(本專案目標) |
| **RCUV2010** | 和合本 2010 | ❌(本專案目標) |
| **KJV** | King James Version | ✅ FHL 標註 |

---

# Scripture Burrito — 為什麼它才是真正的產出格式

## Burrito 是什麼

**Scripture Burrito** 是一種**經文資料的封裝格式標準**(spec: <https://docs.burrito.bible/>)。

名稱取自墨西哥捲餅的比喻:**把經文本體、後設資料、版本資訊等全部「捲」進同一個包裹裡**,交付時是完整自足的一份,不會散落。這正是它要解決的問題——經文資料常常文字一包、註解一包、授權說明又一包,彼此對不起來。

Alignments 專案的 `README.md` 說明了它與本專案(s13)的關係:

> The **Scripture Burrito Working Group** is creating a **Scripture Alignments flavor**, which will be a standard for exchanging alignment data. This repository reflects a working proposal…

也就是說:**Alignments 專案本身就是 Burrito 對齊標準的試作場**。

## 精確用語:AlignmentHub Format

`docs/formats.md` 定義了 repo 實際採用的格式名稱:

> …publish in a standard format we call **AlignmentHub Format**. This **implements the Scripture Burrito standard** for alignment data, with some additional practices and conventions.

所以嚴格說是:**AlignmentHub Format = Scripture Burrito 標準 + Clear Bible 的額外慣例**。

## 為什麼「Burrito」才是我們真正的產出

這是本 survey 的定位核心:

1. **它是唯一必然為真的描述。** 不論上游 Clear-Bible 收不收我們的貢獻,我們產出的東西**就是 Burrito 格式的對齊資料**。「進入 Clear Bible」是一個*期望的去向*;「產出 Burrito」是一個*已確定的事實*。
2. **它同時服務兩條路。** 對內自用(當 SN transfer 的驗證基準)與對外貢獻,吃的是同一份 Burrito 產出,不必做兩套。
3. **它是下游的介面契約。** 見下節 s13 → s12。

## Burrito 的檔案類型術語(`docs/formats.md`)

這正是本 survey 要產出的東西清單:

| 類型 | 說明 | s13 要做? |
|---|---|---|
| **corpus file** | TSV,一行一 token 的經文 | — |
| ├ **source file** | 原文(希伯來/希臘),源自 Macula | ❌ 用現成的 `WLC.tsv` |
| └ **target file** | 譯本經文 | ✅ **要產** `targets/cmn/UNV/{ot,nt}_UNV.tsv` |
| **alignment file** | source↔target 的 token 對應(JSON) | ✅ **要產** |
| **vline** | 一行一節的純文字 | 中間產物 |
| **vref** | 同 vline 但內容是經文參照 | 中間產物 |

> alignment file **必須**搭配 source/target corpus 檔才能正確解讀 —— 三者是一組,缺一不可。

## ⚠️ 又一個 WLC/WLCM 矛盾(來自官方文件)

`docs/formats.md` 官方說法:

> For the Hebrew Bible, **`WLC`** for the Westminster Leningrad Codex, and **`WLCM`** for the **Macula version of this**.

**但實際檔案內容正好相反**:帶完整 Macula 標註(lemma + `H` 前綴 strongs + morph 碼)的是 **`WLC.tsv`**;`WLCM.tsv` 反而是缺 lemma、缺 H 前綴的降級匯出。

**結論不變:仍以 `WLC.tsv` 為準。** 但這說明連上游自己的文件都與資料實況不符,再次驗證「以 `sources/*.tsv` 的實際 schema 為唯一判準」這條原則。

---

# 本 survey(s13)的定位

## 與 s12 的關係:s13 是 s12 的基石

```
s13(本 survey)                        s12_segment_target_verse
────────────────────                   ────────────────────────
UNV+SN  ──Strong join──►  Burrito  ──► 循已入 Burrito 的 SN(UNV)
                          對齊層         逐節分詞目標經文(如 LCC)
```

**編號雖大,但在流程上位於 s12 之上游。** s13 把 UNV 的 SN 錨定到原文 token 之後,s12 才能依這個對齊逐節推進目標譯本的分詞。因此 s13 的產出格式(Burrito)實質上是 **s12 的介面契約** —— 這也是為何格式比「去向」更關鍵。

## Alignments checkout 的定位:唯讀資料源

`llm_direct_sn_unv2notyet/Alignments/` 是 **Clear-Bible/Alignments 的第三方 checkout**,定位為 **唯讀資料源**:

- ✅ 讀取:`data/sources/WLC.tsv`、`SBLGNT.tsv`、既有對齊與 TOML 範本
- ❌ **不在其中工作**、不寫入、不 commit
- 已於 2026-07-28 重置至 `origin/main`(`c99bd0a`),與 remote 完全一致
- 所有孵化產物(本檔、PoC、prompt/response history)均移出至本 survey 目錄

## 授權狀態:已釐清 ✅

FHL 的 Strong 標註授權由 **Joshua(FHL 卸任董事)確認無虞**,可用於本專案(s13)並以 CC-BY-4.0 形式產出對齊資料。

產 TOML 時須將 **FHL 列為 SN 標註出處**,比照現有檔案標註 Groves Center 的作法:

```toml
[source]
identifier   = "WLC"
copyright    = "© 2023 The J. Alan Groves Center for Advanced Biblical Research"
# 我們的 target 端另需標註 FHL 為 SN 標註來源
```
