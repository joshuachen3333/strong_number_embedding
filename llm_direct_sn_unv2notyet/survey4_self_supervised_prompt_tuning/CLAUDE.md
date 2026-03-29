# survey4_annotation_consistency_test/ — Self-Supervised Prompt Evaluation

## 一句話摘要

**同語文（中文）、同譯本（UNV）、不同節。**
範例節（v1）已有 SN 標注，工作節（v2）沒有。
模型從 v1 學放置模式，對 v2 執行標注，跟 FHL ground truth 比對評分。

- v1 從 **exemplar library**（26 dims 分類篩選）選出
- v2 的 SN 號碼跟 v1 完全不同 — **模型需要自己知道每個中文字對應哪個 SN**
- 這就是 survey4 coverage 極低的根因：模型要背 13,000+ 條 Strong's Dictionary
- → survey8 在此基礎上加 qp.php 字典 + 去殼，解決這兩個問題

## Concept

Use FHL's existing UNV+SN annotations as ground truth to objectively evaluate prompt quality — without needing 3-model consensus.

### Current task (cross-lingual projection, no ground truth)

```
Input1: UNV+SN (v1)  ← source with annotations
Input2: LCC (v1)      ← target without annotations
Output: LCC+SN (v1)   ← no standard answer exists
```

### New task (same-language re-annotation, ground truth exists)

```
Few-shot example:
  Input1: UNV+SN (v1)  ← annotated verse as example
  Input2: UNV (v1)      ← same verse without annotations (shows the pattern)

Task:
  Input:  UNV (v2)      ← different verse, no annotations
  Output: UNV+SN (v2)   ← model's attempt

Evaluation:
  Compare output vs FHL's actual UNV+SN (v2) ← ground truth!
```

## What This Tests

| 能力 | 新方法能測？ | 目前 LCC 任務需要？ |
|------|-----------|------------------|
| 格式保持（zero-padding, WAH/WTH） | ✅ | ✅ |
| Implicit markers 處理 | ✅ | ✅ |
| Morphology 放置 | ✅ | ✅ |
| SN count 正確 | ✅ | ✅ |
| **跨語言對齊**（神→上帝） | ❌ | ✅ |
| **不同語序** | ❌ | ✅ |
| **不同用詞/改寫** | ❌ | ✅ |

**Necessary but not sufficient**: a prompt that fails this test is definitely bad for LCC. A prompt that passes might still fail on LCC alignment.

## Full Blueprint

### Stage 1: Build Test Set

Use UNV→UNV+SN with FHL ground truth:
- Pick representative test verses (various difficulties, various SN patterns)
- Build automatic scoring mechanism (compare with FHL ground truth)

### Stage 2: Iterate Prompt with Cheap/Free Models

Use haiku, gemini-flash, gpt-4o-mini, ollama local models:
- Run test set → auto score → revise prompt → re-run → score improves?
- Fast, cheap, massive iteration

### Stage 3: Graduate

Best prompt goes to expensive 3-model consensus (opus, gemini-pro, gpt-5.4):
- Formal production of LCC+SN gold standard

### Why This Is Better

| | 現在（Stage 3 直接做） | 新方案（Stage 1→2→3） |
|---|---|---|
| Prompt 迭代成本 | 每次改動：3 models × 18 節 回測 | 每次改動：1 cheap model × 100 節 |
| 迭代速度 | ~2hr per iteration | ~10min per iteration |
| 評分方式 | 3-model consensus（主觀） | FHL ground truth 比對（客觀） |
| 可迭代次數 | 受 quota 限制（v1.0→v1.1→v1.2 就 3 次） | 幾乎無限（cheap/free models） |
| 昂貴 models 用途 | 開發 + 生產 | **只做生產** |

## Revised Blueprint (Stage 2 Detail)

### Stage 2a: Per-Model Optimization (cheap models)

```
haiku        → haiku 最佳 prompt
gemini-flash → gemini-flash 最佳 prompt
gpt-4o-mini  → gpt-4o-mini 最佳 prompt
qwen3:32b    → qwen3 最佳 prompt

↑ Each model's best prompt may be different!
```

### Stage 2b: Cross-Model Synthesis

- Compare the best prompts, find **common improvements across all cheap models**
- Common improvements = candidate universal prompt upgrade
- Model-specific improvements = model patch (same as existing survey1 system!)

### Stage 2c: Upward Transfer

- Test universal improvements on opus / gemini-pro / gpt-5.4
- Some transfer (also benefit expensive models) → merge into main prompt
- Some don't transfer (expensive models don't need it) → keep only for cheap models

### Isomorphism with survey1

| survey1（生產） | survey4（prompt 開發） |
|---|---|
| main prompt (v1.2) | 通用改進（跨弱模型共通） |
| model patch (opus-patch-0.1) | 模型專屬改進（只對某個弱模型有效） |
| 3-model consensus | 測試集 ground truth 評分 |
| 昂貴 models 做生產 | 便宜 models 做迭代 |

**Core insight**: 便宜模型是 prompt 的「試金石」— 它們更脆弱，所以 prompt 的瑕疵在它們身上暴露得更快。修好弱模型的問題，有一部分會自然 transfer 到強模型。但不是全部。

## Dimension Architecture

### OT vs NT Tag Format

| 特徵 | OT (Hebrew) | NT (Greek) |
|------|-------------|------------|
| Core SN | `<WH1234>` | `<WG1234>` |
| Morph | `<WTH8804>` | `<WTG5656>` |
| Prefix | `<WAH0853>` | `<WAG3588>` |
| Implicit | `{<WH0853>}` | `{<WG3767>}` |
| 900x system | `<WAH09001>` (ל,ב,כ) | 不存在 |
| Ketiv/Qere | `<WTH8675>` 雙型 | 不存在 |
| SN 帶字母 | 無 | `<WG3608a>` (variant SN) |
| SN 範圍 | H1–H8999 | G1–G5624 |
| Morph 範圍 | WTH 8xxx (4位) | WTG 5xxx (4位) |
| Prefix 數量 | WAH 大量 | WAG 極少 (Matt 全書 5 個) |

### Option 1.5 — 分層擴展 (Hybrid)

**A. 共用核心** (regex 擴展支援 `[HG]`)：
- #1-3 SN 計數 — 語言無關
- #4 Implicit 基本 — `{<...>}` 語法相同
- #8-9 Zero-padding / leading zeros — 格式問題通用
- #13 SN 在中文字後 — 位置問題通用
- #17 同號不同 prefix — 概念通用
- #19 三連續跨組 — 結構通用
- #25 FHL 異常 — 通用

**B. OT 專有** (保持原樣，只在 OT 書卷觸發)：
- #5 Implicit 900x 組合 — 希伯來不可分介詞
- #10 900x prefixes
- #15 900x prefix 在 core 前
- #16 4位 09 陷阱
- #18 三連續同組 (900x+core+morph)
- #23 Ketiv/Qere — 希伯來文本傳統特有
- #24 數目字 SN 連串

**C. 通用擴展** (morph/prefix 概念通用，regex 擴展)：
- #6, #7 Morphology — WTH/WTG 統一用 prefix-based 偵測
- #11 複合介系詞/prefix 連續
- #12 WA[HG] 非 900x
- #14 Morphology 緊跟 core SN
- #20-22 四連續子類型

**D. NT 專有** (新維度)：
- #26 字母後綴 SN (`<WG3608a>`) — variant lemma 系統

### 26 Dimensions Summary

| # | 分類 | 維度 | OT 節數 | NT 節數 |
|---|------|------|---------|---------|
| 1 | 共用 | SN count — 簡單短節 (≤8) | 1,996 | 157 |
| 2 | 共用 | SN count — 長節多 SN (>15) | 12,920 | 2,469 |
| 3 | 共用 | SN count — 重複平行結構 | 18,655 | 3,015 |
| 4 | 共用 | Implicit markers — 基本 | 12,687 | 3,352 |
| 5 | OT | Implicit — 900x 組合 | 11,455 | 0 |
| 6 | 通用 | Morphology — 單動詞 | 2,740 | 180 |
| 7 | 通用 | Morphology — 多動詞 | 18,606 | 3,564 |
| 8 | 通用 | 格式 — zero-padding (5位 core) | 23,077 | 1 |
| 9 | 通用 | 格式 — leading zeros | 23,081 | 1 |
| 10 | OT | 格式 — 900x prefixes | 17,488 | 0 |
| 11 | 通用 | 格式 — 複合介系詞/prefix 連續 | 17,766 | 0 |
| 12 | 通用 | 格式 — WA[HG] 非 900x | 20,202 | 118 |
| 13 | 共用 | 位置 — SN 在中文字後 (正常) | 23,138 | 3,623 |
| 14 | 通用 | 位置 — Morphology 緊跟 core SN | 21,294 | 3,728 |
| 15 | OT | 位置 — 900x prefix 在 core 前 | 15,365 | 0 |
| 16 | OT | 邊界 — 4位 09 陷阱 | 3,942 | 0 |
| 17 | 共用 | 格式 — 同號不同 prefix | 385 | 10 |
| 18 | OT | 三連續 — 同組 (900x+core+morph) | 4,564 | 0 |
| 19 | 共用 | 三連續 — 跨組邊界 | 1,922 | 290 |
| 20 | 通用 | 四連續 — 雙 morph 跨組 | 91 | 6 |
| 21 | 通用 | 四連續 — morph+其他 跨組 | 271 | 20 |
| 22 | 通用 | 四連續 — prefix 連串跨組 | 14 | 0 |
| 23 | OT | Ketiv/Qere — 連續雙 morph | 142 | 0 |
| 24 | OT | 數目字 SN 連串 (≥4 純 WH) | 11 | 0 |
| 25 | 共用 | FHL 資料異常 (6+ 位數 SN) | 2 | 0 |
| 26 | NT | 字母後綴 SN (variant lemma) | 0 | 183 |

### Random Seed Convention

所有 survey4 腳本的 `--seed` 預設為 **42**。

**用途**：控制 pairs 取樣的隨機順序。同一個 `--seed` + `--dim` + `--verse-pair-count` 組合永遠產出相同的 pairs，確保不同模型、不同天的跑分結果可以公平合併比較。

**首次採用**：`sample_test_set.py` 建立時（2026-03-24），之後統一套用到 `dmfs_select.py`、`run_benchmark.py`、`compare_models.py`、`round_robin.py`。

**42 的來源**：程式慣例（源自 Douglas Adams《乘客一把銀河指南》中「生命、宇宙及一切的終極答案」= 42），無特殊數學意義，僅作為固定錨點。

**使用的腳本**：
- `sample_test_set.py --seed 42`
- `dmfs_select.py --seed 42`
- `run_benchmark.py --seed 42`
- `compare_models.py --seed 42`
- `round_robin.py`（內部 `random.seed(42 + i)` per round）

**合併規則**：不同天跑的結果，只要 `--seed`、`--dim`、`--verse-pair-count` 三者相同，就能用 `compare_models.py --merge day1.json day2.json` 合併排名。

### Data Files & Tools

| 檔案 | 用途 | 備註 |
|------|------|------|
| `analyze_test_dimensions.py` | 掃描經文觸發哪些維度 | `--book --chap --summary` |
| `dim_verse_map.json` | 全量 verse↔dim 對照表 | 26,923 verses, 10.4 MB |
| `sample_test_set.py` | 從 dim_verse_map.json 取樣測試集 | `--pct 10 --out test_set.json` |
| `OT_DIMENSION_REPORT.md` | OT 39 卷跨卷對比表 | 含文體分析、極值統計 |
| `BUG_2_report_FHL.md` | FHL 資料異常回報 | 3 筆 (Josh 9:21, 1Sam 14:32, 2Chr 27:8) |

### dim_verse_map.json 格式

```json
{
  "meta": { "total_verses": 26923, "ot_verses": 23145, "nt_verses": 3778 },
  "verses": [
    {"ref": "Gen 1:1", "book": "Gen", "book_chi": "創", "chap": 1, "sec": 1,
     "testament": "OT", "tag_count": 12, "dims": [3,4,5,6,8,9,...]}
  ],
  "by_dimension": {
    "18": {"label": "...", "count": 4564, "verses": ["Gen 1:14", ...]}
  }
}
```

來源：全聖經 66 卷 (OT 39 + NT 27), 31,103 verses。

### sample_test_set.py 取樣策略

**策略 B (greedy coverage)**：目標是最小集合使每個 dim 覆蓋 ≥ N%。

1. **Phase 1 — 稀有 dim 全選**：節數 ≤ `--rare-threshold` (預設 20) 的 dim 全部選入
2. **Phase 2 — 貪婪填充**：每輪選觸發最多「尚未達標 dim」的經節，直到所有 dim 達標

```bash
# 10% 覆蓋率（預設 seed=42）
python3 sample_test_set.py --pct 10
# → 2,677 verses (9.9%), all 26 dims ≥10% ✓

# 只取 OT，輸出 JSON
python3 sample_test_set.py --pct 10 --testament OT --out test_set_ot_10pct.json

# 更小的測試集
python3 sample_test_set.py --pct 1
```

稀有 dim 自動全選：#22 (14節), #24 (11節), #25 (2節)。

## Cheap Model Candidates

| Model | Brand | 成本 | 我們已有 CLI？ |
|-------|-------|------|-------------|
| haiku | Claude | 最便宜 | ✅ `claude --model haiku` |
| gemini-flash | Google | 免費 tier | ✅ `gemini --model gemini-3-flash-preview` |
| gpt-4o-mini | OpenAI | 很便宜 | ✅ `codex --model gpt-4o-mini` |
| qwen3:32b | Ollama | 免費（local） | ✅ `--ollama-url` |
| llama3 | Ollama | 免費（local） | ✅ |

## Academic Framing

This is a form of **Annotation Consistency Test** (自我一致性標注測試):
- Use existing annotations as self-supervised ground truth
- Measure a model's ability to reproduce known-correct annotations
- Proxy metric for the harder cross-lingual task

To be documented in `AI_PROBLEM_CLASSIFICATION.md` when finalized.

## Dimension-Matched Few-Shot (DMFS) — 同維度配對示範

### 概念

學術命名：**exemplar selection by feature-profile matching**。

不隨機挑 few-shot example，而是挑一個 dim profile 最接近 test verse 的經節作為示範。這確保模型看到的 example 包含了它即將面對的所有 SN 模式。

### 核心邏輯

```
Task 定義：
  Few-shot example:
    Input1: UNV+SN (v1)  ← 已標注的經節作為範例
    Input2: UNV (v1)      ← 同一節去掉標注（展示 input→output 模式）
  Task:
    Input:  UNV (v2)      ← 不同的經節，無標注
    Output: UNV+SN (v2)   ← 模型的嘗試
  Evaluation:
    Compare output vs FHL's actual UNV+SN (v2) ← ground truth

DMFS 配對：
  v2 (test): Gen 2:18 → dims = {2,3,4,7,8,9,10,11,12,13,14,16,18}

  從 dim_verse_map.json 找 v1 (example):
    1. 計算所有候選經節的 dim profile 與 v2 的 Jaccard similarity
    2. Jaccard(v1.dims, v2.dims) = |交集| / |聯集|
    3. 選 Jaccard 最高的經節作為 v1
    4. v1 ≠ v2（不能自己示範自己）
```

### 匹配策略

| 策略 | 說明 | 適用 |
|------|------|------|
| **Exact match** | v1.dims == v2.dims | 理想，但可能找不到 |
| **Jaccard top-1** | 最高 Jaccard similarity | 預設 |
| **Superset** | v1.dims ⊇ v2.dims | v1 涵蓋 v2 所有模式 |
| **Same-book preference** | 同書卷優先（語境更接近） | 可選 tiebreak |

### 為什麼有效

- **對照組**（隨機選 v1）：example 可能示範 v2 不需要的模式、遺漏 v2 需要的模式
- **DMFS**（配對選 v1）：example 精準示範 v2 即將面對的所有 SN 標注模式
- 26 維度覆蓋了 SN 計數、implicit markers、morphology、格式、位置、邊界、Ketiv/Qere、數目字、FHL 異常、variant lemma — 幾乎所有 LLM 需要處理的 pattern

## Exemplar Library — 維度範例庫

### 為什麼需要 Exemplar Library

DMFS 的 Jaccard matching 從 31,103 節中挑 v1，但：
- **品質不可控**：Jaccard 高不代表模型看了這個 example 就能學好
- **沒有實測驗證**：理論上 dim profile 相似 ≠ 實際上當 example 有效
- **每次重新掃描 31,103 節**：浪費計算

解法：**預先建一個經過實測驗證的小型 exemplar 候選庫**（每個 dim ~10-20 個），之後配對只從庫裡挑。

### 候選挑選：四維矩陣

每個 dim 的候選按四個維度挑選，確保多樣性：

**1. 梯度**：tag 數量分級（短→中→長→極長），涵蓋不同複雜度
**2. 新舊約**：OT (Hebrew WH/WTH/WAH) vs NT (Greek WG/WTG/WAG)
**3. 純度**：觸發最少其他 dim 的優先（避免引入無關干擾）
**4. 文體**：確保不同文學體裁都有代表

文體分類（13 種）：

| 約 | 文體 | 書卷 |
|---|---|---|
| OT | 律法 | 創出利民申 |
| OT | 歷史 | 書士得撒王代拉尼斯 |
| OT | 詩歌智慧 | 伯詩箴傳歌 |
| OT | 先知 | 賽耶哀結但何珥摩俄拿彌鴻哈番該亞瑪 |
| NT | 福音 | 太可路約 |
| NT | 敘事 | 徒 |
| NT | 保羅書信 | 羅林前林後加弗腓西帖前帖後門 |
| NT | 教牧書信 | 提前提後多 |
| NT | 彼得書信 | 彼前彼後 |
| NT | 約翰書信 | 約一約二約三 |
| NT | 雅各書信 | 雅 |
| NT | 其他書信 | 來猶 |
| NT | 啟示 | 啟 |

### 同門循環賽（Round-Robin Validation）

四維矩陣只能挑出「理論上好的候選」，但**誰真的當好 example** 要靠實測。

同一個 dim 的候選們是「同門兄弟」，用 round-robin 循環賽決定誰最適合當 example：

```
Dim #4 的 16 個兄弟：A B C D E F G H I J K L M N O P

Round 1:  A 當 example → B C D E F ... P 各跑一次 → 15 個分數
Round 2:  B 當 example → A C D E F ... P 各跑一次 → 15 個分數
Round 3:  C 當 example → A B D E F ... P 各跑一次 → 15 個分數
...
Round 16: P 當 example → A B C D E ... O 各跑一次 → 15 個分數
```

每個兄弟有**兩個角色**的分數：

- **Example 品質分**（我當 example 時，別人被我教得多好）→ 越高 = 越好的 v1
- **Test 難度分**（別人當 example 時，我被教得多好）→ 越低 = 越難的 v2

產出**兩張排行榜**：

```
最佳 Example 排名（誰教得最好 → Library 首選 v1）：
  #1 Rom 16:27    教別人平均 cov=0.74  ★ 首選
  #2 Rev 18:12    教別人平均 cov=0.71  ★ 備選
  #3 1Pet 1:19    教別人平均 cov=0.68  ★ 備選
  ...
  #14 Deut 4:49   教別人平均 cov=0.25  ✗ 淘汰

最難 Test 排名（誰最難被教會 → 測試集重點關注）：
  #1 Eccl 4:8     被教後平均 cov=0.30  ← 最硬骨頭
  #2 Num 22:6     被教後平均 cov=0.35
  ...
```

**一石二鳥：Library 存「最佳 Example」，測試集收「最難 Test」。**

### 全軍覆沒 = Prompt 的問題

如果某個 dim 的 round-robin 結果**全部不及格**（所有人當 example 都教不好別人）：

```
Dim #23 (Ketiv/Qere) round-robin:
  A 教別人 avg_cov=0.10
  B 教別人 avg_cov=0.08
  C 教別人 avg_cov=0.12
  → 全軍覆沒！
```

這**不是 exemplar 的問題，是 prompt 的問題** — prompt 對這個 dim 無能為力。

回到 survey4 迭代迴圈：

```
prompt v0.1 → 建庫 round-robin → dim #23 全軍覆沒
  → prompt 不懂 Ketiv/Qere
  → 改 prompt v0.2（加 Ketiv/Qere 規則）
  → 重跑 round-robin → dim #23 有 5 個及格了
  → Library 建成
```

**Library 建不起來 = prompt 還不夠好。Library 穩定建成 = prompt 可以畢業。**

### 成本估算

每個 dim ~16 候選 × 15 對手 = 240 次 model call。
精簡版：top-8 候選 × 8 對手 = 64 次。
26 dims × 64 = ~1,664 次。用 cheap model (haiku/ollama) 可接受。

### 上線使用：Library 查詢

Library 建好後，給定任一 v2：

```
v2: Gen 2:18 → dims = {2,3,4,7,8,9,10,11,12,13,14,16,18}

1. 從 v2 的每個 dim 的 Library 收集候選 exemplars（去重）
2. 對候選做 Jaccard matching，選 top-1
3. 如果最高 Jaccard < 0.6 → fallback 到全量 31,103 池
```

候選池從 31,103 縮到 ~200-300 個預驗證 exemplars，又快又穩。

## Full Pipeline — 資料流（更新版）

```
dim_verse_map.json (31,103 verses × 26 dims)
        ↓
四維矩陣挑選 → 每 dim ~16 候選
        ↓
round-robin 循環賽（cheap model）→ 淘汰不及格
        ↓                           ↓
Exemplar Library（最佳 example）   Hard Test Set（最難 test）
        ↓                           ↓
sample_test_set.py → test_set      （合併 hard cases）
        ↓
dmfs_select.py → 從 Library 配對 v1（Jaccard matching）
        ↓
run_benchmark.py → model 跑 UNV → UNV+SN
        ↓
auto_score.py → 比對 FHL ground truth → 4 項分數
        ↓
分數不夠 → 改 prompt → 重跑 round-robin → Library 更新
分數穩定 → prompt 畢業 → 交給昂貴模型生產
```

### dmfs_select.py

```bash
python3 dmfs_select.py --pct 10 --out dmfs_pairs.json
python3 dmfs_select.py --test-set test_set_10pct.json --strategy superset --same-book
```

實測結果（10%）：avg Jaccard 0.96, 52.3% exact match, 最差 0.78。

輸出格式：
```json
{
  "pairs": [
    {
      "test": {"ref": "Gen 2:18", "dims": [2,3,4,7,...]},
      "example": {"ref": "Gen 1:6", "dims": [2,3,4,5,7,...], "jaccard": 0.85},
      "shared_dims": [2,3,4,7,...],
      "test_only_dims": [16],
      "example_only_dims": [5,15]
    }
  ]
}
```

### compare_models.py — 模型海選淘汰賽

**目的**：從 20+ 個 ollama 模型中，用最少 API calls 選出最適合 survey4 任務的模型。

**分組**（按參數量級距）：

| 級距 | 代表模型 |
|------|---------|
| 1-2B | llama3.2:1b, smollm2:1.7b |
| 3-4B | qwen3:4b, gemma3:4b, phi4-mini:3.8b |
| 7-8B | qwen3:8b, llama3.1:8b, mistral:7b |
| 12-14B | gemma3:12b, qwen3:14b, phi4:14b |
| 30-35B | qwen3:32b, aya:35b |
| 70B+ | llama3.3:70b, qwen2.5:72b |
| cloud | deepseek-v3.1:671b-cloud, devstral-2:123b-cloud |

**淘汰規則 — 條件驅動，不寫死輪數**：

```
Round 1: 全部模型 × 3 pairs（快篩）
  → 組內排名
  → 整組最佳 cov < 0.05 → 整組剔除（記錄到淘汰名單）
  → 組內吊車尾（落後組內最佳 > 50%）→ 淘汰

Round 2+: 存活者 × pairs 加倍（上輪的 2 倍）
  → 組內差距 > 10% → 直接決出冠軍，不用下一輪
  → 組內差距 ≤ 10% → 加倍 pairs 再跑一輪
  → 分數穩定不再變化 → 停止

最終: 每個存活組至少保留 1 個首選
      前 3 差距 ≤ 10% → 都保留
```

**停止條件**：
1. 組內差距 > 10% → 該組決出，不再加輪
2. 連續兩輪分數變化 < 2% → 穩定，停止
3. pairs 達到 50 → 上限，強制停止

**最終輸出**：

```
存活模型（每組至少 1 個）:
  4B 冠軍:   qwen3:4b     cov=0.30  5s/v   ← 最快最便宜
  14B 冠軍:  gemma3:12b   cov=0.55  15s/v  ← 甜蜜點
  32B 冠軍:  qwen3:32b    cov=0.65  45s/v  ← 高品質
  cloud 冠軍: deepseek-671b cov=0.80  90s/v ← 天花板

淘汰紀錄:
  1-2B 組: 全軍覆沒 (best cov=0.05)，整組剔除
  7-8B 組: qwen3:8b 留，其餘淘汰
```

**耗時→性價比權衡**：最終表格附帶 `s/v`（秒/節），讓使用者在品質和速度之間選擇。

**合併不同天的結果**：

```bash
# 今天跑 6 個
python3 compare_models.py --dim 1 --verse-pair-count 3 --seed 42 \
  --models model1 model2 ... --out day1.json

# 明天新模型下載完，補跑同組 pairs
python3 compare_models.py --dim 1 --verse-pair-count 3 --seed 42 \
  --models new_model --out day2.json

# 合併排名
python3 compare_models.py --merge day1.json day2.json --out merged.json
```

關鍵：`--seed 42 --dim 1 --verse-pair-count 3` 三者相同 → 同一組 pairs → 公平合併。

### auto_score.py

4 項評分指標：
1. **Exact match** — 整節完全一致（最嚴格）
2. **SN coverage** — (missing + extra) / total SNs
3. **Placement accuracy** — SN 存在但放錯位置
4. **Format compliance** — zero-padding, braces, prefix markers

Ground truth：FHL API (`fetch_chap_cached` with `strong=1`)。
Self-test verified: Gen 1 + Matt 1 + Ps 119 全部 100%。

```bash
python3 auto_score.py --self-test --book 創 --chap 1
python3 auto_score.py --input model_results.json
```

### run_benchmark.py（待實作）

**做什麼**：整個 survey4 pipeline 到目前為止都是「準備工作」— 分維度、選測試集、配對 example、寫評分器。`run_benchmark.py` 是「讓模型動手」的環節。

對每一組 DMFS pair：
1. 從 FHL 取 example verse (v1) 的 UNV+SN ← 有標注的範例
2. 把 v1 的 SN 去掉，得到純 UNV (v1) ← 展示 input 長什麼樣
3. 從 FHL 取 test verse (v2) 的純 UNV ← 去掉 SN 的測試題
4. 組成 prompt：「這是標注範例... 現在請對以下經文做同樣的標注...」
5. 呼叫 cheap model (haiku / gemini-flash / ollama)
6. 收到模型輸出的 UNV+SN
7. 存檔 → `auto_score.py` 自動打分

**為什麼用 cheap model**：

| | survey1（生產） | survey4 benchmark |
|---|---|---|
| 模型 | opus + gemini-pro + gpt-5.4 | haiku / gemini-flash / ollama |
| 每節成本 | 高 | 幾乎免費 |
| 評分方式 | 3-model consensus（主觀） | FHL ground truth（客觀） |
| 用途 | 生產 gold standard | **迭代 prompt** |

便宜模型跑得快、不花錢，可以大量迭代：改 prompt → 跑 benchmark → 分數變高了嗎？→ 再改 → 再跑。找到最好的 prompt 後，才交給昂貴模型做正式生產。

### 便宜模型迭代邏輯 (Prompt Iteration Loop)

```
Round 0: 拿現有 prompt v1.2 跑 benchmark → baseline 分數
         例如 haiku: exact 30%, coverage 0.75, placement 0.80

Round 1: 看哪些維度的經節分數最差
         → 例如 #23 Ketiv/Qere exact 0%, #18 三連續 exact 15%
         → 針對弱項改 prompt（加規則、加範例說明）
         → 重跑 benchmark → 分數有進步 ✓

Round 2: 再看新的弱項 → 再改 → 再跑 → ...

Round N: 分數趨於穩定 → 這個 prompt 對 haiku 的極限到了
```

每個 cheap model 各自迭代：

```
haiku        → prompt-haiku-best
gemini-flash → prompt-flash-best
ollama       → prompt-ollama-best
```

然後 **Stage 2b 跨模型提煉**：
- 三個 best prompt 的**共通改進** → 通用 prompt 升級（可能 transfer 到 opus）
- 各自特有的改進 → model-specific patch（只對那個弱模型有效）

這跟 survey1 的 `main prompt + model patch` 完全同構。

**26 維度在迭代中的角色**：不只看「整體分數」，還看「**哪些維度的經節失分**」。因為 dim_verse_map 記錄了每節觸發哪些 dims，可以做按維度分組的分數分析：

```
auto_score 結果 + dim_verse_map → 按維度分組

  #1 短節:     exact 50%, coverage 0.90  ← 簡單，模型做得好
  #23 K/Q:    exact  0%, coverage 0.40  ← 難，模型完全不會
  #18 三連續:  exact 10%, coverage 0.60  ← 中等，可改善
```

這告訴你 prompt 該加什麼規則 — 針對弱維度補強。

### Survey4 vs Survey1 — 根本區別

| | Survey1（生產線） | Survey4（prompt 試金石） |
|---|---|---|
| 模型數量 | 3 個昂貴模型投票 consensus | **1 個便宜模型就夠** |
| 任務 | UNV+SN → LCC+SN（跨語言） | UNV → UNV+SN（同語言，有標準答案） |
| 評分 | 主觀 consensus | 客觀 FHL ground truth |
| Prompt | v1.2 + model patches | v1.2 作 baseline → 迭代改進 |
| 產出 | gold standard | **更好的 prompt** |

**不需要 ABC 三模型。** 一個模型就是一面鏡子：同一個模型反覆跑不同 prompt，分數差異 = prompt 品質差異。

**Model patch 不在 survey4 裡用。** Patch 是 survey1 的「某個模型專用補丁」。Survey4 改的是**主 prompt 本身**。

### 具體操作流程（以 qwen-32b 為例）

```bash
# Step 1: 產生測試集
python3 sample_test_set.py --pct 1 --out test_set.json          # ~310 節

# Step 2: DMFS 配對
python3 dmfs_select.py --test-set test_set.json --out pairs.json

# Step 3: 跑 benchmark（用 prompt v1.2 作 baseline）
python3 run_benchmark.py --pairs pairs.json \
  --prompt ../survey1_prompt_evolving/prompts/v1.2_joshua.md \
  --model qwen3:32b --ollama-url http://sai.fhl.net:11434 \
  --out results_qwen_v1.2.json

# Step 4: 自動評分
python3 auto_score.py --input results_qwen_v1.2.json
# → exact 25%, coverage 0.70, placement 0.75, format 0.80

# Step 5: 按維度分析弱項 → #23 K/Q 0%, #18 三連續 10%

# Step 6: 改 prompt → v1.2-exp-a.md（加 Ketiv/Qere 規則）

# Step 7: 重跑 Step 3-4 用新 prompt
python3 run_benchmark.py --pairs pairs.json \
  --prompt prompts/v1.2-exp-a.md \
  --model qwen3:32b --ollama-url http://sai.fhl.net:11434 \
  --out results_qwen_v1.2-exp-a.json
# → exact 30% → 進步！

# Step 8: 繼續迭代 → v1.2-exp-b → v1.2-exp-c → ...
```

### 跟 prompt v1.2 和 patch 的關係

```
prompt v1.2（現有 survey1 主 prompt）
    ↓
作為 baseline 在 survey4 跑一輪 → baseline 分數
    ↓
根據弱維度改善 → v1.2-exp-a, v1.2-exp-b, ...
    ↓
分數穩定 → 最佳版本可能成為 v1.3
```

### 多模型提煉（後期）

先用一個模型跑通 pipeline。之後可以換模型驗證：

```
qwen-32b  迭代完 → prompt-best-from-qwen
haiku     迭代完 → prompt-best-from-haiku
flash     迭代完 → prompt-best-from-flash

Stage 2b: 比較三個 best prompt
  共通改進 → 合併到主 prompt（大概率 transfer 到 opus）
  各自特有 → 只在那個弱模型有用，不合併
```

## Status

- [x] 26 維度定義 (Option 1.5 分層架構)
- [x] OT 39 卷全掃 + OT_DIMENSION_REPORT.md
- [x] NT 27 卷全掃 (66 卷 31,103 節)
- [x] dim_verse_map.json 全量資料
- [x] sample_test_set.py 取樣腳本
- [x] OT 回測 PASS (NT 擴展未破壞舊約結果)
- [x] dmfs_select.py — DMFS 配對（avg Jaccard 0.96）
- [x] auto_score.py — 自動評分（self-test 100%）
- [ ] run_benchmark.py — cheap model benchmark
- [ ] 用 cheap models 大量迭代 prompt (Stage 2)
