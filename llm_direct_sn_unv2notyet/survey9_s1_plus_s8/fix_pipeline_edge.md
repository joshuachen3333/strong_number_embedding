# fix_pipeline 邊界分析

## 第一章 — Gen 1 驗證後定邊界

fix_pipeline v2 到邊界了。剩下漏的是 core SN 和 implicit — 都是「LLM 不知道放哪」的情況。自動插會猜位置，違反不過度工程原則。

剩下的交給 consensus（多模型比對）或人工。

### fix_pipeline v2 能補的

| 類型 | 依據 | 邊界內？ |
|------|------|---------|
| 900x prefix | input 配對（prefix→core 相鄰） | ✅ 自動補 |
| morphology | input 配對（core→morph 相鄰） | ✅ 自動補 |
| core SN | 需要語義判斷（放哪個中文字後面） | ❌ 不補 |
| implicit | 需要語義判斷（要不要放、放哪） | ❌ 不補 |

## 第二章 — Gen 2 驗證確認邊界

Gen 2:6 實測（tags=11→6, cov=55%）：

fix_pipeline v2 補回了 `8799` 和 `8689`（兩個 morphology）。但 `03605`、`06440`（core SN）和 `0853`（implicit）沒補 — 這正是邊界外的。

問題是 LLM 本身漏了 6 個 tag（input 11 → output 6）。fix_pipeline 補回 2 個（morphology），最終 8/11。

LLM 漏 core SN 的原因：UNV 說「遍地」用了 `<03605><06440>` 兩個 tag，但 LCC 說「地面」只有一個詞。LLM 不知道「地面」要放兩個 tag。

**這不是 prompt 能解決的** — 是 UNV 和 LCC 的詞粒度不同造成的結構性問題。prompt v0.3 改不了這個。

**結論**：fix_pipeline v2 已經在做正確的事（補 morphology/900x），Gen 2:6 的 55% 主要是 LLM 漏 core SN（邊界外）。沒有 v0.3 可迭代的空間了。
