# AI Problem Classification

## Our Task Type: Few-shot Cross-lingual Annotation Projection (標注投射) + LLM-as-Judge + LLM-Ensemble

### The Three Core Facts

1. **We provide annotated reference** (UNV+SN) — the model sees fully tagged examples in the prompt
2. **We transfer annotations to unlabeled parallel text** (LCC) — the model imitates the tagging on a new target
3. **We validate via 3-model consensus, not human judgment** — LLM-as-Judge ensemble

### Formal Classification

> **Few-shot cross-lingual annotation projection, validated by LLM-as-Judge ensemble**

| Aspect             | Our Approach                              | Academic Classification                    |
|--------------------|-------------------------------------------|--------------------------------------------|
| Example provision  | UNV+SN included in prompt                 | Few-shot In-Context Learning (ICL)         |
| Core task          | Annotated text → unlabeled parallel text  | Annotation Projection (標注投射)            |
| Evaluation method  | 3-model consensus, no human               | LLM-as-Judge + LLM-Ensemble               |
| Learning method    | No training, no fine-tuning               | Inference-time only                        |

### What It Is NOT

- **Not zero-shot** — we provide UNV+SN as reference examples in the prompt
- **Not unsupervised** — there IS an objective correct answer (SN correspondences are deterministic); we just use models instead of humans to validate
- **Not supervised learning** — no model training or fine-tuning involved

### Classical NLP Lineage — Annotation Projection (標注投射)

「標注投射」(Annotation Projection) 是一個成熟的 NLP 技術: given aligned parallel corpora where one side has linguistic annotations (POS tags, SN tags, etc.), project those annotations onto the other side. Traditional methods used statistical word alignment (e.g., GIZA++). Our approach replaces the alignment algorithm with LLM in-context reasoning.

---

## Academic Background of LLM-as-Judge and LLM-Ensemble

### LLM-as-Judge

源自 2023 年 LMSYS 團隊的論文 *"Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena"* (Zheng et al.)。核心動機：人類評估太慢太貴，用 LLM 替代。已知偏誤包括 position bias（順序影響判斷）、self-enhancement bias（偏好自己的輸出）、verbosity bias（偏好長答案）。

### LLM-Ensemble / Multi-Agent — Key References

| Technique                    | Reference              | Core Idea                                            |
|------------------------------|------------------------|------------------------------------------------------|
| **Self-Consistency**         | Wang et al., 2022      | 同一模型多次取樣，多數決 (majority vote)               |
| **Multi-Agent Debate**       | Du et al., 2023        | 多個 LLM 看到彼此輸出後辯論收斂                        |
| **Mixture of Agents**        | Wang et al., 2024      | 多模型分層聚合 (layered aggregation)                   |
| **Self-Refine**              | Madaan et al., 2023    | 模型自我批評 → 自我改進 (critique → refine loop)       |
| **Automatic Prompt Engineer**| Zhou et al., 2022      | LLM 自動搜索最優 prompt                               |

---

## Round-by-Round Strategy Mapping to Academic Patterns

### Round 1 — Cross-Model Self-Consistency

經典 Self-Consistency 是**同一模型**多次取樣再投票。我們是**三個不同模型**各一次，要求 unanimous（全票通過）。

這比原版更嚴格——不同模型有不同偏誤，unanimous 代表任務本身夠明確，模型間的差異都不影響結果。學術上叫 **cross-model agreement** 或 **inter-annotator agreement**（借用傳統 NLP 的概念：把每個模型當一個標注員）。

### Round 2 Convergence — Robustness Testing / Test-Retest Reliability

讓同一模型盲測重做，比對 R1 vs R2a。在心理測量學叫 **test-retest reliability**（再測信度）。在 ML 領域對應 **output stability / robustness verification**。

設計特點：不只測一次，而是追到「連續兩次相同」才算 stable。這比單純 self-consistency 更嚴謹。

### Round 2 Debate — Multi-Agent Debate

直接對應 Du et al. 2023 的 **Multi-Agent Debate**。每個模型看到三方的 stable output + convergence 資訊，選最佳或提供修正版。

### Round 2 Triggers — 本專案的獨創設計

| Trigger                                     | 對應概念                         | 獨創之處                                                              |
|---------------------------------------------|----------------------------------|-----------------------------------------------------------------------|
| Trigger 1 (全部不穩定 → +0.1 prompt)         | **Automatic Prompt Engineering** | 用 convergence failure 作為觸發信號，而非人工判斷                       |
| Trigger 2 (2穩1不穩 → model-specific patch)  | **Personalized Self-Refine**     | 穩定模型給回饋，不穩定模型**自己寫 patch** — cross-model peer review    |

**Trigger 2 特別之處**：學術上 Self-Refine 是模型批評自己再改進，但我們是**別的模型批評，自己改進**。這更接近 **cross-model peer review + self-improvement** 的組合，目前沒有一個標準術語。

### Round 3 — Meta-Judgment with Escape Hatch

| R3 Option                                   | 對應概念                                                                    |
|---------------------------------------------|-----------------------------------------------------------------------------|
| PICK (選贏家)                                | 標準 **LLM-as-Judge**                                                       |
| ALL_WRONG (集體錯誤 → prompt evolution)       | **Constitutional AI** 的精神 — 從錯誤中提取原則並修正系統                     |

R3 的雙軌設計（pick OR all_wrong）在文獻中沒有直接對應。大多數 ensemble 系統假設「至少一個答案是對的」，我們允許「全部都錯」這個判定，這是一個 **fail-safe meta-judgment**。

### Prompt Evolution + 回測 — Automated Prompt Engineering with Regression Gate

對應 Zhou et al. 2022 的 Automatic Prompt Engineer，但加了一個關鍵差異：**regression gate**（回測門檻）。學術上的 APE 純粹優化 forward performance，我們要求新 prompt 不能讓過去的 gold standard 退步。這更像軟體工程的 **CI regression testing** 應用到 prompt 上。

回測取樣率設計：

| Category                      | Target % | Min count to start sampling |
|-------------------------------|----------|-----------------------------|
| Trigger (caused this change)  | 100%     | always all                  |
| Past Round 3 verses           | 80%      | ≥ 5 → sample, else all     |
| Past Round 2 verses           | 50%      | ≥ 10 → sample, else all    |
| Past Round 1 unanimous        | 20%      | ≥ 20 → sample, else all    |

---

## Design Decisions

### `--max-r2-retries=0` 意為 Unlimited（非 0 次重試）

CLI 的 `--max-r2-retries` default=0，程式碼中 0 被當作 unlimited sentinel（hard cap 702）。這**不是 bug**。

| CLI 參數值                      | 實際行為                               |
|---------------------------------|----------------------------------------|
| `--max-r2-retries 0` (default)  | unlimited（最多 702 次，a-z + aa-zz）   |
| `--max-r2-retries 2`            | R2a + 最多 2 次重試 = R2a, R2b, R2c    |

### Unlimited Retries 和 Easy/Hard Threshold 是獨立機制

| 機制                            | 職責                 | 問的問題                         |
|---------------------------------|----------------------|----------------------------------|
| `max-r2-retries` (unlimited)    | **找到穩定輸出**      | 「這個模型最終能收斂到什麼？」    |
| `is_easy_convergence()` (R2a)   | **判定是否需要 patch** | 「這個模型掙扎了嗎？」           |

Easy/Hard 分界線固定在 R2a：

| stable_at | 模型產出過程           | Unique outputs | 判定 |
|-----------|------------------------|----------------|------|
| R1        | R1=X, R2a=X           | 1              | Easy |
| R2a       | R1=X, R2a=Y, R2b=Y    | 2              | Easy |
| R2b       | R1=X, R2a=Y, R2b=Z, R2c=Z | 3         | Hard |
| R2c+      | 4+ 種不同輸出才收斂    | 4+             | Hard |
| unstable  | 從未收斂               | all different  | Hard |

R2a 分界線的根據：R1 測「能不能一次做對」，R2a 測「重做一次能不能收斂」。如果連重做一次都產出不同結果（3 種以上），就是 genuine instability，值得做 patch。

### Instability Score → Patch 力度分級（已實作）

Hard 目前是 binary，但不同程度的不穩定應有不同力度的 patch。引入 **instability score** = unique outputs count：

| Score | stable_at  | Level        | Patch 行為                                                                                      |
|-------|------------|--------------|-------------------------------------------------------------------------------------------------|
| 3     | R2b        | **mild**     | 現行做法：兩個穩定模型各給 feedback，不穩定模型自寫 patch                                        |
| 4     | R2c        | **moderate** | feedback 附上**完整 attempt history**（搖擺軌跡），patch 要求包含 **root cause analysis**          |
| 5+    | R2d+/unstable | **strong** | 以上全部 + 附上**過去同模型 trigger2 記錄**，patch 要求 prescriptive 明確規則（非 hint）           |

Feedback prompt 差異示例：

- **Mild**: 「你的輸出和我們不同，以下是正確版本和你的版本，請改進。」
- **Moderate**: 「你產出了 4 種不同結果：[R1] [R2a] [R2b] [R2c]。你在以下 SN 上搖擺：... 請分析為什麼搖擺，並寫出明確規則避免。」
- **Strong**: 「你在過去 N 節經文中都觸發了 trigger2。共同模式：... 請寫出 prescriptive 規則。」

Patch 回測範圍也隨力度調整：

| Level    | 回測範圍                                     |
|----------|----------------------------------------------|
| mild     | 10% past gold standard                       |
| moderate | 20% past gold standard                       |
| strong   | 30% + 所有過去同模型 trigger2 verses          |

---

## Summary

> 本系統是 **Multi-Agent Debate + Cross-Model Self-Consistency + Automated Prompt Engineering with Regression Gate** 的組合。
> 其中 Trigger 2 的 cross-model peer review → self-patch 機制是一個較新穎的設計。

### Key Terms (關鍵字)

| Term                                        | Description                                                         |
|---------------------------------------------|---------------------------------------------------------------------|
| **Annotation Projection (標注投射)**         | 從已標注平行語料投射標注到未標注文本                                   |
| **Few-shot In-Context Learning**            | 在 prompt 中提供少量範例引導模型                                      |
| **LLM-as-Judge**                            | 用 LLM 替代人類做品質評判                                            |
| **LLM-Ensemble**                            | 多個 LLM 各自獨立產出，再透過投票/共識機制整合結果                     |
| **Self-Consistency**                        | 同一模型多次取樣，多數決                                              |
| **Multi-Agent Debate**                      | 多個 LLM 互相看到輸出後辯論收斂                                      |
| **Self-Refine**                             | 模型自我批評 → 自我改進                                              |
| **Automatic Prompt Engineering (APE)**      | LLM 自動搜索/演化最優 prompt                                        |
| **Regression Gate (回測門檻)**               | 新 prompt 必須通過對過去 gold standard 的回歸測試                     |
| **Cross-Model Peer Review**                 | 穩定模型給不穩定模型回饋，後者自行改進（本專案獨創）                    |
| **Test-Retest Reliability (再測信度)**       | 同一模型盲測重做，驗證輸出穩定性                                      |
| **Fail-safe Meta-Judgment**                 | 允許「全部都錯」的判定，而非強制從現有答案中選一個                      |
