# survey4_annotation_consistency_test/ — Self-Supervised Prompt Evaluation

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

## Full Pipeline — 資料流

```
dim_verse_map.json (31,103 verses × 26 dims)
        ↓
sample_test_set.py --pct 10 → test_set (≈2,700 verses)
        ↓
dmfs_select.py → 為每個 test verse 配對一個 dim-matched example verse
        ↓
run_benchmark.py → cheap model 跑 UNV → UNV+SN (用 DMFS pairs)
        ↓
auto_score.py → 比對 FHL ground truth → 4 項分數
        ↓
改 prompt → 重跑 → 分數有進步？
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
