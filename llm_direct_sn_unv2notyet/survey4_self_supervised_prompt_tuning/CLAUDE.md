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

### Data Files

- `dim_verse_map.json` — 全量 verse↔dim 對照 (26,923 verses, 10.4 MB)
- `OT_DIMENSION_REPORT.md` — OT 39 卷跨卷對比表
- `BUG_2_report_FHL.md` — FHL 資料異常 3 筆 (Josh 9:21, 1Sam 14:32, 2Chr 27:8)

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

## Scoring Metrics (proposed)

1. **Exact match rate**: output == FHL ground truth (strictest)
2. **SN coverage score**: missing + extra SNs / total SNs
3. **Placement accuracy**: SN present but wrong position
4. **Format compliance**: zero-padding, braces, prefix markers

## Status

Concept stage. Implementation pending.
