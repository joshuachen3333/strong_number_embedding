# survey9_s1_plus_s8/ — S1 production 任務 + S8 去殼架構

## 一句話摘要

**S1 的任務（UNV+SN → LCC+SN）+ S8 的方法（去殼裸數字 + script 加殼）。Production pipeline。**

## S1 是什麼（保留原樣於 survey1/）

Survey1 = UNV+SN → LCC+SN 的 production 任務。
- 輸入：UNV+SN（已標注）+ LCC plain（目標）
- 輸出：LCC+SN
- 評分：3-model consensus（沒有 ground truth）
- 問題：LLM 同時處理語義配對 + 複雜 FHL 格式 → coverage/format 常出錯

## S8 是什麼（保留原樣於 survey8/）

Survey8 = 去殼 simplestSN benchmark。
- LLM 只插裸數字 `<7225>`，不處理格式
- Script 後處理加殼
- 結果：placement +22pp vs S5（0.78 vs 0.57）

## Survey9 = S1 + S8 的合體

```
S1 的任務:  UNV+SN → LCC+SN（中文→中文，同語系）
S8 的方法:  去殼 → LLM 只放裸數字 → script 查表加殼

合體:
  1. UNV+SN 去殼          → UNV+<裸數字>
  2. 建殼對照表            → {7225: '<WAH09002><WH07225>', 430: '<WH0430>', ...}
  3. LLM: UNV+<裸數字> + LCC plain + 原文 + 字典 → LCC+<裸數字>
  4. Script 查表加殼        → LCC+SN（完整 FHL 格式）
```

### LLM 收到的 5 個輸入

```
1. UNV+SN (stripped):   起初<09002><07225>，神<0430>創造<01254><8804><0853>天<08064><0853>地<0776>。
   → 「答案」在這裡！所有數字（含 morphology, 900x, implicit）都有
   → LLM 只需要把這些數字搬到 LCC 對應位置

2. UNV plain:           起初，神創造天地。
   → 讓模型看到 UNV 無標注的原文（輔助語義理解）

3. LCC plain:           太初，上帝創造天地。
   → 目標：在這裡插入數字

4. 原文:                בְּרֵאשִׁית בָּרָא אֱלֹהִים...
   → 第三語言錨點（輔助）

5. SN:原文字 字典:       7225: בְּרֵאשִׁית, 430: אֱלֹהִים...
   → 確認每個數字的意義（輔助）
```

### LLM 的唯一任務

**把 UNV+SN 裡的數字搬到 LCC 對應位置。**

```
UNV:  起初<09002><07225>  →  「起初」有 <09002><07225>
LCC:  太初                →  「太初」= 「起初」 → 太初<09002><07225>
```

同語系（中文→中文），語義配對最容易。所有數字都在輸入裡，不需要背、不需要猜。

### Script 後處理 pipeline

```
LLM 輸出:  太初<07225>，上帝<0430>創造<01254><8804><0853>天<08064><0853>地<0776>。
     ↓
fix_pipeline() — 迴圈補漏 + 修順序（最多 3 輪，穩定即停）
  Round 1: fix_coverage → 補回漏掉的 <09002>（插在 <07225> 前）
           fix_placement → 檢查順序（OK）
  Round 2: 無變化 → 穩定，結束
     ↓
restore_shell_lookup() — 查表加殼（零損失）
  09002 → <WAH09002>    (從 UNV+SN 查表)
  07225 → <WH07225>
  8804  → <WTH8804>
  0853  → {<WH0853>}
     ↓
最終:    太初<WAH09002><WH07225>，上帝<WH0430>創造<WH01254><WTH8804>{<WH0853>}天<WH08064>{<WH0853>}地<WH0776>。
```

**fix_coverage 只自動補 900x prefix**（位置確定），morphology/core/implicit 漏了留給 consensus。
**restore_shell_lookup 查表**（不猜），100% 正確。

### 三科考試預期

| 科目 | S5 (完整格式) | S8 benchmark | **S9 production 預期** |
|------|-------------|-------------|----------------------|
| coverage | 0.61 | 0.57 (字典缺) | **~1.00** (UNV+SN 直接給) |
| placement | 0.57 | 0.78 (去殼專注) | **≥0.78** (同語系更容易) |
| format | 0.93 | 0.35 (猜殼) | **~1.00** (查表加殼) |

## 與 S1 的關係

S1 原本的 3-model consensus 用於**沒有 ground truth** 的情況。
S9 不改變這個——S9 改變的是**每個模型怎麼做**：

```
S1 原來:  模型直接輸出 LCC+SN（完整格式）
S9 改為:  模型輸出 LCC+<裸數字>，script 查表加殼
```

3-model consensus 仍然可以用（三個模型各自輸出裸數字，比對 placement）。

## 元件來源（不修改原件）

| 元件 | 來源 | 用途 |
|------|------|------|
| `strip_shell()` | `shared/sn_shell.py` (S8) | UNV+SN 去殼 |
| `restore_shell()` | `shared/sn_shell.py` (S8) | 查表加殼（方案 A markers） |
| `fix_placement()` | `shared/sn_shell.py` (S8) | 順序校正 |
| `fetch_qp_verse()` | `survey6/run_survey6.py` | 原文 + 字典 |
| prompt framing | `survey8/prompts/survey8_v0.1.md` | 標注投射 |
| 3-model consensus | `survey1/consensus.py` | 品質保證 |

## Status

- [x] 概念設計
- [ ] `run_survey9.py` — 主程式
- [ ] `prompts/survey9_v0.1.md` — 去殼版 UNV→LCC prompt
- [ ] Gen 1 驗證（用 FHL UNV+SN → LCC，看 placement）
- [ ] 整合回 `llm_direct_sn_unv2notyet.py` 主程式
