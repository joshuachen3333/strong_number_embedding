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

## Test Set Coverage

17 個測試維度（合併能力 × 類別 × survey2 edge cases）：

| # | 測試維度 | 代表經節 | 測什麼 |
|---|---------|---------|--------|
| 1 | SN count — 簡單短節 | Gen 1:5, 1:19 | 基本 SN 放置，數量不多不少 |
| 2 | SN count — 長節多 SN | Gen 1:21, 1:28 | 大量 tag 不漏不亂 |
| 3 | SN count — 重複平行結構 | Gen 1:11, 1:12 | 各從其類 ×2，不重複不遺漏 |
| 4 | Implicit markers — 基本 | Gen 1:1, 1:4 | {<WH0853>} 保留 |
| 5 | Implicit markers — 900x 組合 | Gen 1:2 | {<WAH05921>} implicit + prefix 合體 |
| 6 | Morphology — 單動詞 | Gen 1:1, 1:3 | <WTH8804> 附著在動詞上 |
| 7 | Morphology — 多動詞 | Gen 1:21, 1:28 | 多個 <WTH> 各附著正確動詞 |
| 8 | 格式 — zero-padding | Gen 1:1 | <WH07225> not <WH7225> |
| 9 | 格式 — leading zeros 規則 | Gen 1:1 | FHL 一律補零至 4-5 位，模型不得刪除 |
| 10 | 格式 — 900x prefixes | Gen 1:5, 1:6 | <WAH09002> 保留不丟 |
| 11 | 格式 — 複合介系詞 | Gen 1:7 | <WAH04480><WH05921> 連續 tag |
| 12 | 格式 — WAH 非 900x | Gen 1:7, 1:21 | <WAH0853>, <WAH0834> — WAH 不只用於 900x |
| 13 | 位置 — SN 在對應中文字後 | Gen 1:1 | 神<WH0430> 不是 <WH0430>神 |
| 14 | 位置 — Morphology 緊跟動詞 SN | Gen 1:1, 1:3 | 創造<WH01254><WTH8804> 不是 創造<WTH8804><WH01254> |
| 15 | 位置 — 900x prefix 在對應字前 | Gen 1:1 | 起初<WAH09002><WH07225> prefix 先於 core |
| 16 | 邊界 — 4位 vs 5位 900x 陷阱 | (含 <WH0914> 的經節) | <WH0914> 是 core 不是 900x，不能誤判 |
| 17 | 格式 — 同號不同意（WH vs WAH） | Gen 1:3 | <WH01961> vs <WAH01961> 同號碼不同 prefix |

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
