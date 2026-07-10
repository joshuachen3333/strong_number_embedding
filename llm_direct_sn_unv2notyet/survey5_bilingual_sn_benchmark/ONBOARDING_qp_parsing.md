# ONBOARDING_qp_parsing.md — survey5 的 ± qp enrichment 軸

> **概念根源**：[`parsing/PARSING_FOUNDATIONS.md`](../../parsing/PARSING_FOUNDATIONS.md) — FHL parsing（SN + parsing code）是**上游輸入**；我們做的是 **Alignment**（word-for-word 或 null）。
> **變更計畫**：[`parsing/QP_ENRICHMENT_PLAN.md`](../../parsing/QP_ENRICHMENT_PLAN.md) — 本目錄對應其中 **Item 4**。
> **本軸的正式 spec**：[`docs/superpowers/specs/2026-07-10-survey5-leaderboard-design.md`](docs/superpowers/specs/2026-07-10-survey5-leaderboard-design.md) §Third axis。

## 這個軸是什麼

leaderboard 原本兩個維度：model × prompt。Item 4 加入第三個 on/off 維度 **± qp enrichment**：

同 model × 同 prompt，兩臂對照：

| 臂 | Prompt 內容 |
|---|---|
| `off`（預設） | WLC+SN source + UNV plain（今天的路徑，一字不變） |
| `qp` | 額外附上該節的 **qp word-table** — 每個原文字一行：`word / orig`(lemma) `/ sn / wform`(parsing code) `/ exp`(中文 gloss) |

qp word-table 來自 FHL `qp.php`（欄位語義見 [`survey2 §9.2`](../survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md)），一次性凍結成 `qp_snapshot_52.json`；qp.php 不支援的帶數字書卷（OT 子集含 2Sam×4、1Chr×3、2Chr×3）用本地 `bible_parsing.db`（`lparsing` 表，五欄齊全）補。跑分時**永不 live fetch**。

它把「parsing code 到底有沒有幫助 SN 放置？」變成**可量測的命題**。

## 怎麼讀

- **Headline 指標不變**（cov/place；morph 照舊排除在排名外）。新增防護：兩臂都先把 raw output 裡的 morph-range tags（canonical H8675–H8999，即 WTH*）剝掉再進 `num_score` — 因為 enriched prompt 洩漏了 `wform`，模型可能自己吐 morph tags，不剝會讓兩臂不可比。
- leaderboard 多一個 `enrich` 欄，外加一張 **paired-delta 表**：每個同 `(model, prompt)` 的成對 cell 報 Δcov / Δplace / per-dim delta。

| Δcov | Δplace | 判讀 |
|---|---|---|
| ≥ 0 | > 0 | enrichment 有幫助 → 放行 Item 3 的 survey1 A/B |
| > 0 | ≤ 0 | 混合訊號（覆蓋升、放置沒升）→ 維持 `off`，待調查 |
| < 0 | > 0 | survey6 過載模式重演 → 維持 `off` |
| ≈ 0 | ≈ 0 | WLC+SN 已含足夠訊號 → 維持 `off` |

不符合「有幫助」那一列的任何結果，預設一律維持 `off`。

## 與 survey6 `--enrich-dict` 前例的關係

survey6 已經試過在 SN:word 字典每行附加 `exp`+`wform`（[`run_survey6.py --enrich-dict`](../survey6_original_lang_benchmark/run_survey6.py)），結論：single-pass 5-input **資訊過載 — place +7pp 但 cov −10pp**。所以先驗偏負面：本軸預設 `off`，舉證責任在 `qp` 臂。

值得重測的理由（跟 survey6 當時條件的三個差異）：
1. source 現在是 **WLC-only**（沒有 KJV 這個過載主嫌）；
2. 52 節凍結集 + 成對 cell ⇒ 受控比較，不是逸事；
3. Round-2 評分路徑 + morph 防護，不是 survey6 的舊 scorer。

本軸格式比 survey6 多了 `orig`（lemma）欄；v1 只有這一種固定五欄格式，欄位消融（orig-only / exp-only…）不在範圍內。

## 與 Item 3（survey1 gold pipeline）的關係

本軸是**便宜的 ground-truth 量測**；survey1 的 qp A/B（貴，3-model consensus，無標準答案）只有在本軸顯示 win 時才值得跑。詳見 [`../survey1_prompt_evolving/QP_AB_DESIGN.md`](../survey1_prompt_evolving/QP_AB_DESIGN.md)（同批變更由 Item 3 建立）。

分工：survey5 有 FHL ground truth，回答「qp 證據對單模型放置有沒有幫助」；survey1 回答「qp 證據能不能減少 consensus 回合 / 仲裁分歧」。前者是後者的前置濾網。

## 目前狀態

**Spec-only**：runner 尚未動 — `run_leaderboard.py`（尚未實作）、`run_iteration_set.py`（尚未改）；`--enrich` 旗標、`build_qp_snapshot.py`、`qp_snapshot_52.json` 皆待實作。預設 `off`；`qp` 臂只在明確要求的 cell 上跑（配額考量，先跑 headline models × 最佳 prompt 的短名單）。
