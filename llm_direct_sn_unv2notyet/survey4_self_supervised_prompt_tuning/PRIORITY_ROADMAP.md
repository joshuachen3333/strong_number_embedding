# Priority Roadmap — Resource Transition Plan

Claude Max 訂閱即將到期。在資源緊縮前，需要建立用便宜/免費模型繼續開發的基礎設施。
一旦費率、成本、耗時速率估算到位 → 向出資方請款 → 用最好的商用模型 production run。

## Priorities

| 優先度 | 任務 | 為什麼趁現在做 |
|--------|------|--------------|
| **P0** | 建立 survey4 測試集 + 自動評分腳本 | 到期後用 cheap models 迭代 prompt 的基礎設施 |
| **P0** | 用 opus 跑一次 survey4 benchmark baseline | 留下「最強模型的分數」作為天花板參考 |
| **P0** | 建立耗費參數估算（cost/verse, time/verse, 各模型費率） | 向出資方請款的依據 |
| **P1** | 確認 haiku / gemini-flash / ollama 的 CLI 都能正常跑 | 到期前驗證替代方案可用 |
| **P1** | 用 cheap models 跑 survey4 benchmark | 建立弱模型 baseline 分數，跟 opus 比較差距 |
| **P2** | 用 opus+gemini_pro+gpt5.4 完成 Gen 1-3 gold standard | 請款前的 demo 成果，刷卡跑完 chap 1-3 |
| **P3** | 請款後：用商用模型 production run 大量跑 | 費率到位 → 請款 → 全速生產 |

## Gold Standard Production Plan

Gen chap 1-3 with ABC = opus, gemini-3-pro-preview, gpt-5.4:
- Gen 1:1-28 done (v1.2 prompt)
- Gen 1:29-31 pending (3 verses)
- Gen 2 pending (25 verses)
- Gen 3 pending (~24 verses)
- Total remaining: ~52 verses

## Cost/Rate Estimation (survey5 備忘)

→ 將另立 survey5 建立完整的成本模型：
- cost per verse per model (API token pricing)
- time per verse per model (latency)
- R2 convergence overhead (multiplier per verse difficulty)
- Total cost estimate for Gen 1-50 (or full OT)
- 向出資方的請款報告模板

This is a **memo only** — full implementation in a future survey.
