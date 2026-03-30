# survey8_simplest_sn_benchmark/ — 去殼(simplestSN) + 同版本不同節 + 原文與字:號碼對照

## 一句話摘要

**同語言（中文）、同版本（UNV）；不同節。Survey4 的架構（同版本不同節）+ survey6 原文與 SN:原文字對照 + 去殼簡化 LLM 核心，程式套殼。**

## 工作原理

### LLM 收到什麼（去殼後的 5 個輸入）

```
1. 範例節 UNV+SN（去殼）:  起初<09002><07225>，神<0430>創造<01254><8804>天<08064>地<0776>。
   → 從 survey4 的 26 dims exemplar library 選出，讓模型學「數字放在中文字後面」的模式

2. SN:原文字 字典:        07225: בְּרֵאשִׁית
                          0430: אֱלֹהִים
                          01254: בָּרָא
   → 來自 qp.php，告訴模型每個數字對應哪個原文字

3. 原文經文:              בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ
   → 輔助模型理解原文字順序

4. 工作節 UNV（純文字）:   地是空虛混沌，淵面黑暗...
   → 模型要在這裡插入數字

5. Prompt (v0.1, 989 chars): 標注投射 framing + 規則
```

### LLM 做什麼

**只做一件事：把字典的數字放在對應的中文字後面。**

```
字典: 0776=אֶרֶץ(earth) → 找「地」→ 地<0776>
字典: 01961=הָיָה(was)  → 找「是」→ 是<01961>
```

不需要知道 WH/WG/WAH/braces/zero-padding。不需要背 SN 字典。只做語義配對。

### Script 做什麼（後處理 pipeline）

```
LLM 輸出:  起初<07225>，上帝<0430>創造<01254><0853>天<08064>...
     ↓
     ↓ fix_pipeline() — 迴圈修補直到穩定（最多 3 輪逃離）
     │   ↓ fix_coverage() — 補漏：比對 input vs output tags
     │   │   • 900x prefix 漏了 → 插回配對的 core SN 前面
     │   │   • morphology/core/implicit 漏了 → 不動（留給人工/consensus）
     │   ↓ fix_placement() — 修順序：
     │       • orphan morphology 在 core 前 → 交換
     │       • 900x prefix 在 core 後 → 交換
     │   ↓ result == prev? → 穩定就結束，否則再跑一輪
     ↓
     ↓ restore_shell_guess() — 加殼（benchmark 用猜的）
     或 restore_shell_lookup() — 加殼（production 用查表）
最終輸出:  起初<WAH09002><WH07225>，上帝<WH0430>創造<WH01254>...
```

### fix_pipeline 迴圈機制

```
Round 1: fix_coverage 補漏 → fix_placement 修順序
Round 2: 還有要補/修的嗎？→ 沒有 → 穩定，結束
（最多 3 輪強制結束，實測都是 1-2 輪）
```

**fix_coverage 的設計原則**：
- **只自動補 900x prefix** — 位置確定（在配對的 core SN 前面，參照 input tag 順序）
- **不自動補 morphology/core/implicit** — 位置靠猜不可靠，留給人工或 consensus
- 配對邏輯：在 input_tags 中找 900x 後面緊跟的非 prefix tag → 那就是它的 core SN

**fix_placement 的兩條規則**：
- Rule 1: orphan morphology（前面沒有 core）在 core 前 → 交換
- Rule 2: 900x prefix 在 core 後 → 交換

## 為什麼 S8 比 S5 好

```
考試三科：coverage（數字全不全）、placement（位置對不對）、format（殼穿對不對）

S5 做法：LLM 同時考三科 → cov=0.61 place=0.57（三科都普通）
S8 做法：LLM 只考 placement → place=0.78（專注一科，高 22pp）
          coverage → production 時 UNV+SN 直接給答案（送分）
          format   → script 查表加殼（送分）

S8 Gen 1-10 (211 節, DeepSeek-671B): placement=0.78, exact=7
S5 Gen 1-10 (同範圍): placement=0.57, exact≈0
```

## 評分指標

| 指標 | 量什麼 | 白話 |
|------|--------|------|
| **cov** (coverage) | 該有的數字有沒有出現 | 「漏了幾個？多了幾個？」 |
| **place** (placement) | 數字出現了，位置對不對 | 「放對地方了嗎？」 |
| **fmt** (format) | 格式對不對（zero-padding、braces、prefix） | 「殼穿對了嗎？」 |

### S8 方案 B 雙重分數

- **S1**：去殼比（裸數字 vs 裸數字）→ 量 LLM 純放置能力
- **S2**：加殼後比（FHL 格式 vs FHL 格式）→ 量 LLM + script 組合
- **S1 − S2 差距** = restore_shell_guess 猜錯造成的損失

## fix_placement() — 規則校正 LLM 放置錯誤

`shared/sn_shell.py` 中的 `fix_placement()` 用結構性規則修正 LLM 輸出中明顯的順序錯誤。這不是湊答案——這兩條規則是希伯來/希臘 SN 系統的語法結構，適用於任何經節任何語言。

### Rule 1: Morphology 跟在 core SN 後面

```
LLM 輸出: 創造<8804><1254>    ← morphology(8804) 跑到 core(1254) 前面
修正後:   創造<1254><8804>    ← 正確：core 在前，morphology 在後
```

### Rule 2: 900x prefix 在 core SN 前面

```
LLM 輸出: 起初<7225><9002>    ← core(7225) 跑到 prefix(9002) 前面
修正後:   起初<9002><7225>    ← 正確：prefix 在前，core 在後
```

### Production 時更準

Production 有 UNV+SN 的映射表，能精確知道哪個是 morphology、哪個是 core。Benchmark 時靠 `core_sns`（qp.php）區分。

## 核心想法

**分離 LLM 的語義能力和格式規則。**

之前所有 survey 都要求 LLM 同時做兩件事：
1. **語義對齊**：判斷哪個 SN 號碼對應哪個中文字（需要語言理解）
2. **格式套用**：正確使用 `<WH>`, `<WAH>`, `{<>}`, zero-padding 等（純規則）

LLM 不擅長格式規則——survey5 的 coverage/format 損失大量來自格式錯誤
（WH vs WAH、缺 braces、zero-padding 錯），不是語義放錯。

Survey8 的解法：**去殼 (strip shell)**，LLM 只處理裸數字，格式交給 script。

## 從 Survey4/5/6/7 的教訓

| Survey | 問題 | 根因 |
|--------|------|------|
| Survey4 | cov 極低 | 模型要從記憶背 SN 號碼（沒有字典）|
| Survey5 | cov=0.60 place=0.55 | 格式錯誤 + KJV/UNV SN 不一致 |
| Survey6 | 5-input 壓垮模型 | 輸入太多太複雜 |
| Survey7 | P2 不穩定 (68%) | LLM 不擅長「只移不刪」的精細操作 |

Survey8 同時解決這些問題：
- **有字典** → 不需要背號碼（解決 survey4 問題）
- **去殼** → 輸入更短更乾淨（解決 survey6 問題）
- **不依賴 KJV** → 沒有跨文本傳統 SN 不一致（解決 survey5 問題）
- **格式交給 script** → 不需要 LLM 精細操作（解決 survey7 問題）

## 架構

### 去殼 (strip_shell)

```
FHL 完整格式           →  裸數字
<WH07225>              →  7225
<WH0430>               →  430
<WAH09002>             →  9002
<WTH8804>              →  8804
{<WH0853>}             →  853
<WAH0905>              →  905
```

所有 prefix（WH, WG, WAH, WTH, WTG）、angle brackets、braces、zero-padding
全部去掉，只留數字。OT/NT 不影響去殼（都是數字）。

### LLM 的任務

```
輸入：
  1. UNV plain:     地是空虛混沌，淵面黑暗...
  2. 原文 (Heb):    וְהָאָרֶץ הָיְתָה תֹהוּ וָבֹהוּ...
  3. SN:word dict:  776: אָרֶץ
                    1961: הָיָה
                    8414: תֹּהוּ
                    922: בֹּהוּ

輸出：
  地776是1961空虛8414混沌922...
```

LLM 只做一件事：**把字典裡的數字放在對應的中文字後面**。
不需要知道 WH/WG、不需要加 brackets、不需要判斷 implicit。

### 加殼 (restore_shell)

Script 後處理，用規則把裸數字轉回 FHL 格式：

```python
def restore_shell(num, testament, context):
    if 9000 <= num <= 9999:
        return f"<WAH0{num}>"          # 900x prefix
    elif 8000 <= num <= 8999:
        prefix = "WTH" if testament == "OT" else "WTG"
        return f"<{prefix}{num}>"       # morphology
    else:
        prefix = "WH" if testament == "OT" else "WG"
        padded = zero_pad(num)          # 按 FHL 規則補零
        return f"<{prefix}{padded}>"    # core SN
```

### Implicit markers `{}`

去殼時 `{}` 也去掉。加殼時怎麼判斷？

方案 A：**規則表**。某些 SN 號碼（如 853=את）在 UNV 中幾乎總是 implicit。
維護一個常見 implicit SN 列表。

方案 B：**位置推斷**。如果一個 SN 數字出現在輸出中但前後沒有對應的中文字
（即數字緊鄰數字或標點），推斷為 implicit，加 `{}`。

方案 C：**字典標記**。qp.php 的資料可能能判斷是否 implicit。

### WAH vs WH 判斷

同一個 SN（如 430）有時用 `<WH0430>` 有時用 `<WAH0430>`。
加殼時的判斷規則：

- 900x 號碼 → 一定用 `<WAH09xxx>`
- 其他號碼 → 預設 `<WH>`，但如果 ground truth 中這個 SN 在同位置用 WAH
  → 需要從 UNV+SN 的統計 pattern 推斷

這是加殼最難的部分，可能需要 per-SN 的統計表。

## 雙重評分

### Score 1: 去殼比對（量 LLM 的純放置能力）

```
LLM output (stripped):    地776是1961空虛8414混沌922...
GT (stripped):            地776是1961 8804空虛8414混沌922...
→ 只看數字有沒有、位置對不對
→ 預期分數很高（LLM 只需配對數字和中文字）
```

### Score 2: 加殼比對（量 script 的格式還原能力）

```
Script output (shelled):  地<WH0776>是<WH01961><WTH8804>空虛<WH08414>混沌<WH0922>...
GT (original):            地<WH0776>是<WH01961><WTH8804>空虛<WH08414>混沌<WH0922>...
→ 完整 FHL 格式比對
```

### 差異分析

Score 1 − Score 2 = **後處理造成的損失**。

可以逐步加殼，定位問題：

| 步驟 | 加什麼 | 量什麼 |
|------|--------|--------|
| Step 0 | 裸數字 | LLM 放置能力 |
| Step 1 | `<WH>`/`<WG>` prefix | OT/NT 判斷 |
| Step 2 | zero-padding | 補零規則 |
| Step 3 | `{}` braces | implicit 判斷 |
| Step 4 | WAH/WTH 區分 | prefix type 推斷 |
| Step 5 | 900x/8xxx 位置微調 | 位置後處理 |

## 資料來源

- **UNV+SN**: FHL API `qb.php`（ground truth）
- **原文 + SN:word 字典**: FHL API `qp.php`（`word` + `sn` 欄位）
- **OT/NT 判斷**: `shared/data/books.json`

## 與其他 Survey 的關係

```
Survey4:  UNV+SN(v1) → UNV+SN(v2)     ← 沒字典，要背號碼
Survey5:  KJV+SN → UNV+SN              ← 有號碼但格式複雜 + KJV/UNV 不一致
Survey6:  KJV+SN + 原文 + dict → UNV+SN ← 5-input 太多
Survey8:  原文 + dict(裸數字) → UNV+裸數字  ← 最簡，格式交 script
```

Survey8 的 strip_shell / restore_shell 可以被其他 survey 共用：
- Survey5 可以加 `--simplest` flag，去殼後跑、加殼後評分
- restore_shell 的規則可以獨立成 `shared/sn_shell.py`

## Prompt Framing — 跨經節標注投射

Survey8 的 Annotation Projection 不是跨語言（沒有 KJV），而是**跨經節**：

```
v1 (範例節): UNV+裸數字 — 已標注，讓模型學習「數字放在中文字後面」的模式
v2 (測試節): UNV plain + 原文 + SN:word 字典 — 模型要標注這一節
```

Prompt 第一段必須寫：
- 這是 Annotation Projection 任務
- v1 是範例（學習放置模式）
- v2 是目標（用字典確認每個數字放在哪個中文字後面）
- 字典是 ground truth — 不要猜號碼，字典有什麼就放什麼

v1 的選擇：從 survey4 的 exemplar library（26 dims）中選同維度的範例。

## 方案 A vs B

**方案 A（commit 93f4063）**：LLM 輸出帶 markers（`<P9002>`, `<M8804>`, `<I853>`）。
加殼完美但 S1=S2，雙重評分無差異。LLM 負擔稍重。

**方案 B（目前）**：LLM 只輸出裸數字（`<9002>`, `<8804>`, `<853>`）。
Script 用規則猜 marker。S1>S2 可定位 script 猜錯的地方。LLM 最簡。
難點：8xxx 數字歧義（8064=天 是 core SN，8804 是 morphology）。

## Status

- [x] 概念設計
- [ ] `shared/sn_shell.py` — strip_shell() / restore_shell()
- [ ] `run_survey8.py` — 主程式
- [ ] `prompts/survey8_v0.1.md` — 去殼版 prompt（預期非常短）
- [ ] 雙重評分框架
- [ ] Gen 1 baseline
