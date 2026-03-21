# Architecture Decisions — survey1_prompt_evolving

## AD-1: 統一判定原則 (Single Source of Truth for Gold Standard)

**日期**: 2026-03-20
**狀態**: 已確認，待實作

### 原則

> **`build_gold_standard()` 是所有 `resolved_at` 判定的唯一來源。**
> main loop (`run_gold_standard.py`) 只負責呼叫模型、收集資料。
> 任何 resolution path（R1 unanimous, R2 debate, R2 Trigger 1/2, R3 pick/all_wrong）
> 的最終判定都必須經過 `build_gold_standard()`，不得在 main loop 直接存 gold standard。

### 為什麼

從 Bug 1-3 學到的教訓：

**Bug 1 (Trigger 1 → unresolved)**：Trigger 1（三模型全不穩定）把節加到 `all_disagreed`，但跳過了 R2 debate 和 R3。`build_gold_standard()` 看到這節在 `disagreed` 列表中，卻找不到 R2/R3 資料，只能標記為 `"unresolved"`。正確應為 `"r2_early_evolution"`。

**Bug 2 (Trigger 2 → summary 少算)**：Trigger 2（2 穩定一致 + 1 不穩定）直接呼叫 `save_gold_standard()` 存到硬碟，跳過 `build_gold_standard()`。結果 summary 的 `gold_standard` dict 不包含這些節，計數不完整。

**Bug 3 (R3 prompt_evolution 重複)**：main loop 和 `build_gold_standard()` 各自收集 `prompt_evolutions`，最後合併時同一節出現兩次。

### 根因

三個 bug 的根因相同：**resolution 邏輯散落在兩個地方**（main loop + build_gold_standard），破壞了 Single Source of Truth。

### 修法

| 現況 | 改為 |
|------|------|
| Trigger 1 直接存 gold standard + 加到 `all_disagreed` | 收集到 `all_trigger1`，傳給 `build_gold_standard()` |
| Trigger 2 直接存 gold standard | 收集到 `all_trigger2`，傳給 `build_gold_standard()` |
| main loop 收集 `all_prompt_evolutions` | 刪除。只由 `build_gold_standard()` 回傳 |
| `print_summary()` 拼接多個來源 | 只用 `build_gold_standard()` 的回傳值 |

### 未來擴充守則

1. **新增任何 resolution path 時**（例如 R4、新的 Trigger 類型），**不得**在 main loop 直接呼叫 `save_gold_standard()`
2. 應收集資料到適當的列表，傳給 `build_gold_standard()` 統一處理
3. `resolved_at` 的值只在 `build_gold_standard()` 裡設定
4. `print_summary()` 只依賴 `build_gold_standard()` 的回傳

---

## AD-2: 其他已知問題

### Bug 4 (Trigger 1 重複加到 all_disagreed)

Line 730（DISAGREED 時）和 Trigger 1 區塊各加一次 `all_disagreed.append(verse_key)`。
被 AD-1 修法自動解決：Trigger 1 不再加到 `all_disagreed`。

### Bug 5 (R3 unresolved 無 continue)

R3 unresolved 後沒有明確的 `continue`，靠 fall-through 到 loop 尾端。功能正確但與其他路徑不一致。應加 `continue` 保持風格統一，避免未來在 loop 尾端加 code 時被 fall-through 影響。

---

## AD-2: Unified 4-Level Stability Scale

**日期**: 2026-03-21
**狀態**: 已確認，待實作

### 取代舊的二分系統

之前有兩套分開的系統：Easy/Hard（二分，控制 Trigger 2 是否觸發）+ mild/moderate/strong（三級，控制 feedback 力度）。現統一為一個 4 級量表：

```
Level 0: Easy     — stable at R1 or R2a (≤2 unique outputs)
Level 1: Mild     — stable at R2b (3 unique outputs)
Level 2: Moderate — stable at R2c-R2d (4 unique outputs)
Level 3: Strong   — stable at R2e+ or never converged (5+ unique outputs)
```

### Trigger 2 — Distance-Based

觸發條件：2 models agree (`texts_match`) AND **distance ≥ 2**

**Distance = weak model's level − agreed models' average level**

| Agreed | Weak | Avg | Distance | Trigger 2? |
|--------|------|-----|----------|------------|
| 0, 0 | 2 | 0.0 | 2.0 | Yes |
| 0, 0 | 3 | 0.0 | 3.0 | Yes |
| 0, 1 | 3 | 0.5 | 2.5 | Yes |
| 1, 1 | 3 | 1.0 | 2.0 | Yes |
| 0, 0 | 1 | 0.0 | 1.0 | No |
| 1, 1 | 2 | 1.0 | 1.0 | No |
| 1, 2 | 3 | 1.5 | 1.5 | No |
| 2, 2 | 3 | 2.0 | 1.0 | No |

### Trigger 1 — All Struggling (Average-Based)

| 全體平均 | 狀態 | 行動 |
|---------|------|------|
| avg < 1 | 至少有人 easy | 不算 all struggling |
| 1 ≤ avg < 2 | 全部偏難但不嚴重 | normal debate（不觸發 Trigger 1，讓 debate 解決）|
| avg ≥ 2 | 全部嚴重掙扎 | **Trigger 1**（prompt +0.1）|

### Trigger 2 — Weak Model Voice (Distance-Based)

| Distance | Action |
|----------|--------|
| = 2.0 | Ask weak model to validate → if disagrees, route to debate |
| ≥ 3.0 | Direct auto-resolve (no validation needed) |

Patch is always generated regardless. See `TRIGGER2_DESIGN_REVIEW.md` for full rationale.

### Full Flow

```
R1 → UNANIMOUS → done
R1 → DISAGREED → R2 convergence → classify Level 0-3
  → Trigger 1? (avg ≥ 2 → auto-evolve prompt +0.1 → 回測 → stop)
  → Trigger 2? (2 agree + distance ≥ 2)
    → distance ≥ 3? → direct auto-resolve + patch
    → distance = 2? → ask weak model to validate
      → agrees → auto-resolve + patch (3/3 with reasoning)
      → disagrees → route to normal R2 debate (patch still generated)
  → Neither → normal R2 debate (2/3 majority)
    → No 2/3 → R3 (dual: pick OR all_wrong)
      → pick 2/3 → gold standard
      → all_wrong 2/3 → auto-evolve prompt +0.1 → 回測
      → no consensus → unresolved (human)
```
