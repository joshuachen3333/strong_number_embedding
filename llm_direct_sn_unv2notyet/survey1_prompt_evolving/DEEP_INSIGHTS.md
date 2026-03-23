# Deep Insights — survey1_prompt_evolving

Accumulated observations from running Gen 1:1-28 gold standard production.
Date: 2026-03-23

---

## 1. Task Framing > Specific Rules (v1.2 breakthrough)

v1.0→v1.1 修的是具體 bug（implicit markers 被丟、zero-padding 丟失）。v1.1→v1.2 是**典範轉移**：告訴模型「你在做 Annotation Projection（標注投射）」，而不只是給規則。

結果：v1.1 時代需要的 model patches（opus-patch-0.2, gpt-5.4-patch-0.3）在 v1.2 全部不需要了。Hard verses（1:7, 1:16）從「需要 patch」變成 R1 UNANIMOUS。

**可推廣的 insight**：在 prompt engineering 中，正確命名任務類型（task framing）比堆砌具體規則更有效。模型在訓練時學過 Annotation Projection 的概念，一旦被觸發，相關能力自動啟動。

## 2. Instability is Often Random, Not Systematic

Gen 1:21（最難的一節）在 opus x3 測試中：
- 第一次：全部 Level 3 (Strong)，avg=3.0 → Trigger 1 觸發 → v1.3 自動生成
- 第二次：全部 Level 0 (Easy)，R2 debate 輕鬆解決

**同一模型、同一 prompt、同一節** — 結果完全不同。這代表某些節的「難度」有很大的隨機成分（model non-determinism），不是 prompt 的系統性缺陷。

**設計影響**：Trigger 1 應該要求**同節確認跑**（re-run confirmation）才正式觸發 prompt evolution，避免隨機噪音觸發無意義的演化。→ AD-3 待實作。

## 3. Regression Gate Proved Its Value

v1.3 由 opus x3 自動生成（clause-level alignment rules），投票 3/3 通過。但回測 17/18 passed，**Gen 1:11 FAILED**。v1.3 被自動撤回。

沒有回測閘門，一個「修好 1:21 但搞壞 1:11」的 prompt 就會上線。回測是**安全閘門**，不是形式主義。

保留失敗的 prompt（`v1.3_Gen_1_21_REGRESSION_FAILED_at_Gen_1_11.md`）也有學習價值 — 可以看到模型嘗試了什麼、為什麼失敗。

## 4. Comments in Prompts Slightly Help (Survey3)

| Metric | With comments | Without comments |
|--------|-------------|-----------------|
| R1 Unanimous | 5/12 | 3/12 |
| R2 debate | 7/12 | 8/12 |
| R3 needed | 0/12 | 1/12 |

含 # comment（evolution story、experiment results）的 prompt 稍微好一些。可能模型從 story 中學到了注意事項。至少不會傷害。保留 default 含 comment。

## 5. Same-Model Trio Has Limited Value

opus x3 在簡單節上跟混合 trio 差不多（都 UNANIMOUS）。在困難節上，三個 opus 有**相同的盲點** → 一起掙扎 → 觸發假的 Trigger 1。

同模型 trio 的真正價值是**quota 管理**（其他模型 rate limit 時可用）和**stability testing**（測試模型自身一致性），不是品質保證。

## 6. Rate-Limit ≠ Instability

Gemini rate-limited 時被誤判為 Level 3 (Strong) → 觸發了假的 Trigger 2 → 生成無用的 patch。

修正：新增 Level -1 (UNAVAILABLE)。bailed_out 的模型排除在 stability analysis 之外。偵測到 rate limit → 立刻停止 pipeline。

## 7. System Sophistication

從「3 個模型投票」發展成完整的共識協議：
- 多輪共識（R1 → R2 convergence + debate → R3）
- 4 級穩定度量表（AD-2）
- Distance-based Trigger 2 + avg-based Trigger 1
- 自我演化 prompt（3 draft → vote → 回測 → adopt/revert）
- Model self-patch（cross-model peer review → self-improvement）
- 回測安全閘門
- Rate-limit 保護
- 可配置 model trio（--modelsABC）
- Regression-failed prompts 保留學習

Cross-model peer review → self-patch 是獨創設計（未見於現有文獻）。

## 8. Production Statistics (Gen 1:1-28)

- Prompt version: v1.2 (annotation projection framing)
- R1 unanimous rate: ~30-40%
- Most disagreements: resolved at R2 debate
- R3 needed: very rare
- Trigger 1 fired: once (false alarm, random variance)
- Trigger 2 fired: several times under v1.1 (eliminated by v1.2)
- Model patches: needed under v1.1, not under v1.2
- No prompt evolution triggered by the system (only human-initiated v1.2)
- 0 unresolved verses

## 9. Pending Decisions

- **AD-3**: Trigger 1 confirmation run (同節確認跑) — 避免隨機噪音觸發假的 prompt evolution
- **Trigger 2 Option A/B**: distance=2.0 weak model validation — implemented but not battle-tested
- **Survey3 conclusion**: comments slightly help → keep default, flag available for experiments
