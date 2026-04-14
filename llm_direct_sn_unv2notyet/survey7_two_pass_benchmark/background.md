# Survey7: Two-Pass Benchmark — 背景與設計動機

## 從 Survey5/6 到 Survey7 的演化

### Survey5 的成果與瓶頸

Survey5 (KJV+SN → UNV+SN) 建立了跨語言 SN transfer 的自動評分框架。
S5 v0.2 (Annotation Projection framing) 是穩定的 baseline：

| 模型 | Coverage | Placement | 備註 |
|------|----------|-----------|------|
| DeepSeek-671B Gen 1 | 0.59 | 0.51 | 穩定，免費 |
| DeepSeek-671B Gen 2 | 0.65 | 0.68 | 章節間差異大 |
| Sonnet Gen 1 | 0.43 | 0.48 | 不穩定，偶爾 exact match |

S5 的瓶頸：模型只有英中語義配對一條線索，遇到詞序差異大或一詞多義時
placement 容易錯。

### Survey6 的嘗試與發現

Survey6 加入原文 (Hebrew/Greek) + SN:word 字典作為第三語言錨點。

**Single-pass 結果**：placement 確實提升 (+7pp)，但 coverage 嚴重下降 (-10pp)。
5 個輸入太多，模型被資訊量壓垮，產出的 tag 更少。
後續嘗試 tag inventory checklist (v0.2) 更糟 (cov=0.39)。

**關鍵發現**：原文字典對 placement 有幫助，但不能跟主任務混在一起。

### Two-pass 架構的誕生

分離兩個能力：
```
Pass 1 (S5 v0.2): KJV plain + KJV+SN + UNV plain → UNV+SN draft
  → 3 inputs，模型專注放 tag，coverage 強

Pass 2 (refine):  draft + Original + SN:word dict + KJV+SN → corrected UNV+SN
  → 4 inputs，模型專注校正位置，tag 已在，只需移動
```

每一步的認知負擔都比 S6 single-pass 小。

## Two-pass 的實驗結果

### DeepSeek-671B (private ollama host)

迭代了 refine prompt v0.1→v0.5：

| Refine 版本 | Gen 1 cov | Gen 1 place | sum | 不退步率 | 特性 |
|------------|-----------|-------------|-----|---------|------|
| (S5 only, no P2) | 0.59 | 0.51 | 1.10 | — | baseline |
| v0.1 | 0.57 | 0.54 | 1.10 | ~71% | P2 會刪 tag (WAH09002) |
| v0.2 | 0.59 | 0.49 | 1.09 | 100% | 太保守，幾乎不動 |
| v0.3 | 0.64 | 0.47 | 1.10 | 100% | 微好，仍保守 |
| **v0.4** | **0.57** | **0.57** | **1.14** | ~71% | **最佳 sum** |
| v0.5 | 0.54 | 0.51 | 1.05 | — | 退步 |

v0.4 在 Gen 1 上是最好的組合分數，但 Gen 2 上 two-pass 不如 S5 (1.25 vs 1.33)。
P2 有時破壞 P1 已經正確的 placement（把 P1 place=1.00 的 tag 搬壞）。

### Sonnet (claude CLI)

Sonnet 跑 two-pass 遇到兩個問題：

**問題 1：模型輸出夾帶解釋文字**

Sonnet 不遵守 "no JSON, no explanation, no markdown"，在 annotated text 後面
附加 "Projection notes:", "Correction made:" 等解釋段落。auto_score 把整個
輸出（含解釋）跟 ground truth 比對，tag 位置全亂，coverage 歸零。

**臨時解法**：`strip_explanation()` 後處理，只取第一段中文+tag，丟掉後面的
英文解釋。這是 band-aid——靠 pattern matching 截斷，不是根本解決。

**問題 2：P2 非確定性極高**

同一節同一 prompt，sonnet 的 P2 輸出有時乾淨、有時整段重寫、有時 tag 格式
全改。導致同一測試跑兩次結果差很大（1:4 有時 cov=0.86，有時 cov=0.00）。

**解法**：tag count guard——若 P2 的 tag 數跟 P1 差超過 50%，自動 fallback
回 P1。確保 two-pass 最壞情況 = P1（不會比 S5 差）。

## 核心問題：Production 可行性

### 「沒有 ground truth 怎麼判斷 P2 好不好？」

在 benchmark（survey5/6）中，我們有 FHL ground truth 可以比對 P1 vs P2。
但在 production（survey1: UNV→LCC）中**沒有標準答案**。

Tag count guard 只抓災難（P2 大幅丟 tag），抓不到「tag 數一樣但位置搬錯」
的情況。沒有 ground truth 就無法逐節判斷 P2 是改善還是搞砸。

### P2 的價值鏈

```
Benchmark 階段（有答案）:
  跑完整本 Genesis (1-50) → 統計 P2 不退步率
  如果 >90% → P2 是「大概率安全的改善」
  如果 >95% → 可以有信心直接用在 production

Production 階段（沒答案）:
  帶著 benchmark 的統計信心直接用 two-pass
  不需要逐節判斷，因為統計上已證明值得
  類似藥物臨床試驗：Phase III 通過 → 上市
```

**目前的數據不足以支持 production 部署**：
- DeepSeek Gen 1 不退步率 ~71%（太低）
- DeepSeek Gen 2 上 two-pass 整體不如 S5
- Sonnet 不穩定，需要大量 guard 才能用

### 噪音排除策略

大規模 benchmark 前必須先解決模型噪音：

**A. 換模型**：DeepSeek-671B 在 refine 上比 sonnet 穩定（不亂加解釋、
不整段重寫）。sai 上免費跑，適合大規模驗證。

**B. 針對崩掉的 fallback**（現有 + 可加強）：
- tag count 偏差 >50% → fallback（已實作）
- 中文字元數不一致 → fallback
- 出現英文句子（解釋） → fallback
- strip 後仍有多行 → fallback

兩個方向不衝突：用 DeepSeek 跑主力 benchmark，同時加強 guard 讓 sonnet
也能用。

## Survey7 的任務

### 核心問題

**「加入原文 + SN:word 字典作為 Pass 2 refine，是否能在大規模 benchmark
上達到 >90% 不退步率？」**

如果答案是 Yes → 帶著信心推向 survey1 production。
如果答案是 No → 放棄 two-pass，回到 S5 單次 prompt 繼續進化。

### 子問題

1. 最佳 refine prompt 是什麼？（v0.1-v0.5 已初步探索）
2. 不退步率是否因書卷/模型/章節而異？
3. P2 改善的節有什麼共同特徵？（可用 survey4 的 26 dims 分析）
4. 最終推向 production 時，guard 機制夠不夠？

### 與 Survey1 的關係

Survey7 的終極目標是為 survey1 (UNV→LCC production) 提供信心：

```
Survey7 驗證 (KJV→UNV, 有答案):
  two-pass 不退步率 >90%  →  信心足夠

Survey1 部署 (UNV→LCC, 沒答案):
  套用相同的 two-pass 架構
  Pass 1: UNV+SN + LCC plain → LCC+SN draft
  Pass 2: draft + Original + SN:word dict → corrected LCC+SN
```

跨語言 SN placement 是同一種能力，KJV↔UNV 的 benchmark 結果
可以推廣到 UNV→LCC 的 production。

## 大規模 Benchmark 結果（2026-03-28）

### Gen 1-10, DeepSeek-671B, refine v0.4

| 範圍 | 節數 | 改善 | 不動 | 退步 | 不退步率 |
|------|------|------|------|------|---------|
| Gen 1 | 31 | ~7 | ~17 | ~7 | 77% |
| Gen 2-10 | 236 | 46 (19.5%) | 115 (48.7%) | 75 (31.8%) | **68.2%** |

Per-chapter 不退步率（Gen 2-10）：
- 最好：Gen 2 (80%), Gen 4 (81%)
- 最差：Gen 5 (50%), Gen 9 (52%)
- Gen 10（族譜）：0 improved, 8 degraded

### Enriched dict (--enrich-dict) 實驗

Gen 1 加入 qp.php 的 `exp`（中文字義）和 `wform`（詞形分析）：
- 無 enrich: cov=0.5632 place=0.5846 sum=1.1478
- 有 enrich: cov=0.5679 place=0.5646 sum=1.1325
- 差異不顯著，enriched dict 沒有明顯幫助

### 結論

**Two-pass 不退步率 68% 遠低於 90% production 門檻。**

P2 (refine) 對約 20% 的節有改善，但對約 32% 的節造成退步。
重複性章節（族譜 Gen 5/9/10）退步尤其嚴重。

**決定：放棄 two-pass 路線，回到 S5 單次 prompt 改進。**

Two-pass 的價值發現保留作為參考：
- 原文字典確實能改善 placement（S6 v0.1 證實）
- 但無法同時維持 coverage（資訊過載問題未解）
- refine pass 的「不亂動」約束對 LLM 太難遵守
