# ONBOARDING — qp-enrichment 與 SPECIFICATION v1.9（本目錄視角）

> 給後續在 `sn_within_unv_selfgroup_segmentation/` 工作的 agent / 開發者：本文說明 FHL parsing code（qp.php）如何進入本目錄的規格層，v1.9 增量是什麼、`lemma` 欄位怎麼理解、OT/NT 不對稱為何重要、OpenSpec 提案在哪裡。
>
> **概念根文檔**：[`../parsing/PARSING_FOUNDATIONS.md`](../parsing/PARSING_FOUNDATIONS.md)（Parsing vs Alignment 框架 — 先讀這份）
> **執行計畫**：[`../parsing/QP_ENRICHMENT_PLAN.md`](../parsing/QP_ENRICHMENT_PLAN.md)（qp-enrichment 四項變更的總計畫；本目錄對應其 Item 2）

---

## 1. 一句話背景

FHL 資料中一個動詞帶兩個標籤：**Strong's Number（這是哪個詞 = lemma）** + **Parsing Code（此處如何變化 = 詞形）**。本目錄的解析器一直在消費這兩者（morph 8xxx token、`parsing_wform` 補註、v1.7+ 複合詞檢測），但規格文件從未把 parsing code 的來源與顆粒度講清楚。**SPECIFICATION_v1.9.md** 補上這一層。

## 2. v1.9 是什麼（S1–S4，全部 additive-only）

| ID | 增量 | 位置 |
|----|------|------|
| S1 | `lemma: string \| null` 補註欄位（取自 qp.php `orig`） | §5.2.1、§6.1 |
| S2 | 粗/細兩級 Parsing Code 術語 | §2.4 |
| S3 | OT/NT `pro`/`wform` 欄位不對稱 + OT-centric 警示 | §6.1.1 |
| S4 | 概念基礎指標（→ PARSING_FOUNDATIONS.md） | 文件頭、§12.1 |

**鐵律**：`SPECIFICATION_v1.8.md` 一個 byte 都不能動 — `parse_verse_v1_8.py` 啟動時會按檔名載入並驗證其第一行版本。v1.9 是獨立新檔（`cp` v1.8 後做錨定插入），純文件級增量，沒有 v1.9 parser。任何 v1.8 合規輸出自動是 v1.9 合規輸出。

## 3. `lemma` 欄位怎麼理解

- **來源**：qp.php 每詞記錄的 `orig` 欄位 = 字典原形（例：創 1:1 בָּרָא 的 `orig` 也是 בָּרָא；約 3:16 ἠγάπησεν 的 `orig` 是 ἀγαπάω）。
- **契約**：與既有 `parsing_wform` 完全同級 — **僅補註（annotation-only）**，預設 `null`，嚴禁影響分組、`morph`、`prefixes` 或任何合併決策。
- **現狀**：v1.9 只「定義」此欄位；現行 parser 尚未輸出它（未來另開變更實作）。

## 4. 兩級 Parsing Code（S2，§2.4）

- **粗顆粒**：qb.php 行內 `<WTH8804>` / `<WTG5656>` — 僅動詞核心變化（希伯來：語幹+時態；希臘：時態+語態+語氣）；就是本規格的 morph 8xxx token。解碼表：[`../llm_direct_sn_unv2notyet/survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md`](../llm_direct_sn_unv2notyet/survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md) §6。
- **細顆粒**：qp.php `wform` — 粗顆粒之上加人稱/性/數（「動詞，Qal 完成式 3 單陽」；新約「…第三人稱 單數」= V-AAI-3S）。
- 兩級都是**同一個詞的變化資訊**，永不對應獨立中文詞（規格 §2.3 的老規則不變）。

## 5. OT/NT 不對稱（S3，§6.1.1）— NT 擴展前必讀

| | `pro` | `wform` |
|---|---|---|
| OT | 空 | 詞類+全部詞形（「動詞，Qal 完成式 3 單陽」） |
| NT | 詞類（「動詞」） | 只有屈折；不變化詞為空 |

⚠️ 本目錄現行的 qp 推斷（推斷前綴、複合詞 `wform` 樣式比對「介系詞 מִן +」）**假設 OT 語義**。要擴到新約，必須先讀 `pro` 再讀 `wform`，否則樣式比對靜默失敗。另：qp 回應中 `wid=0` 是全節總覽列，一律跳過。

## 6. OpenSpec 提案在哪

[`openspec/changes/add-qp-parsing-enrichment/`](openspec/changes/add-qp-parsing-enrichment/proposal.md)（proposal.md / tasks.md / design.md / specs/parsing-aux-annotation/spec.md）。驗證：在本目錄執行 `openspec validate add-qp-parsing-enrichment --strict`。歸檔（部署後）：`openspec archive add-qp-parsing-enrichment --yes`。

## 7. 相關檔案速查

- [`SPECIFICATION_v1.9.md`](SPECIFICATION_v1.9.md) — 權威規格（additive superset）
- [`SPECIFICATION_v1.8.md`](SPECIFICATION_v1.8.md) — parser 實作基線（immutable，勿改）
- `parse_verse_v1_8.py` / `run_parser_temp.py` — 現行實作（本輪未動）
- [`VERSION_UPGRADE_GUIDE.md`](VERSION_UPGRADE_GUIDE.md) — 版本檔案不可變政策的出處
- [`../parsing/PARSING_FOUNDATIONS.md`](../parsing/PARSING_FOUNDATIONS.md) — 概念根（Alignment vs Parsing）
- [`../parsing/QP_ENRICHMENT_PLAN.md`](../parsing/QP_ENRICHMENT_PLAN.md) — 四項變更總計畫（本目錄 = Item 2）
