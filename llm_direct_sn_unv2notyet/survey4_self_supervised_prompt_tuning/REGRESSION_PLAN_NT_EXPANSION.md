# OT Regression Test Plan — NT Expansion Impact

## 背景 (Context)

`analyze_test_dimensions.py` 從 25 維度 (OT-only) 重構為 26 維度混合架構 (Option 1.5 OT+NT)。部分維度的偵測邏輯因支援希臘文 (WG/WTG/WAG) 而改動。需要驗證這些改動沒有破壞舊約的既有結果。

## 哪些維度被改動了 (Which dims changed)

### 需要回測 (NEEDS_REGRESSION) — 8 個維度

| Dim | 改動內容 | 風險 |
|-----|---------|------|
| **#6, #7** | Morph 偵測方式改變：舊版用「數字開頭 8 且長度 4」，新版用「prefix 開頭 WT」 | **中等** — 核心邏輯改變 |
| **#5** | Implicit WAH 篩選加了 `lang == "H"` 條件 | 低 — OT tag 的 lang 本來就是 H |
| **#10** | 900x 偵測加了 `lang == "H"` 和 `"A" in prefix` 條件，比舊版更嚴格 | 中等 |
| **#18, #19** | 三連續 tag 的 morph 判斷改用新版 prefix-based（從 #6/#7 連鎖） | 中等 |
| **#20, #21** | 四連續 tag 的 morph 判斷改用新版 prefix-based（從 #6/#7 連鎖） | 中等 |

**核心風險**：#6/#7 的 morph 偵測邏輯改變會連鎖影響 #18, #19, #20, #21。

### 未改動或安全 (UNCHANGED / TRIVIALLY_SAFE) — 18 個維度

#1-4, #8-9, #11-14, #15-17, #22-26 — 邏輯完全相同，或只加了 NT 專用模式（OT 不會觸發）。

## 改動細節 (Change Details)

### #6/#7 Morph 偵測（影響最大）

```python
# 舊版 (OT-only): 用數字範圍判斷
morph_tags = [t for t in tags
              if t["number"].startswith("8") and len(t["number"]) == 4]

# 新版 (hybrid): 用 prefix 判斷
morph_tags = [t for t in tags if _is_morph_tag(t)]
# where _is_morph_tag = tag["prefix"].startswith("WT")
```

**為什麼改**：OT morph 用 WTH + 8xxx，NT morph 用 WTG + 5xxx。數字範圍判斷無法跨語言，prefix 判斷可以。

**OT 等效條件**：若所有 OT 的 WTH tag 的數字都是 8xxx 4位，且所有 8xxx 4位數字的 tag 都用 WTH prefix → 新舊完全等效。

**潛在風險**：
- `<WH8033>` (שָׁם = 那裡) — 舊版會誤判為 morph（8 開頭 4 位），新版正確不判為 morph（WH prefix，非 WT）
- 若這種情況存在，新版反而**更正確**，但數值會跟舊版不同

### #5 Implicit WAH

```python
# 舊版
implicit_wah = [t for t in implicit_tags if "A" in t["prefix"]]

# 新版
implicit_wah = [t for t in implicit_tags
                if _has_prefix(t) and t["lang"] == "H"]
```

**為什麼改**：排除 NT 的 WAG tag。`lang == "H"` 在 OT 永遠為 True。

### #10 900x

```python
# 舊版
p900x_tags = [t for t in tags
              if t["number"].startswith("09") and len(t["number"]) == 5]

# 新版
p900x_tags = [t for t in tags if _is_900x(t)]
# where _is_900x = number starts "09" AND len==5 AND "A" in prefix AND lang=="H"
```

**為什麼改**：新版更嚴格，多了 prefix 和 lang 條件。純 OT 應該不影響。

## 回測方法 (Regression Approach)

### Step 1 — 窮舉 morph 偵測比對（不需取樣，直接全掃）

掃描所有 OT tag，比較舊版與新版的 morph 偵測結果：

```python
old_morph = tag["number"].startswith("8") and len(tag["number"]) == 4
new_morph = tag["prefix"].startswith("WT")
```

若**零分歧** → #6, #7, #18, #19, #20, #21 全部保證等效。

若有分歧 → 列出哪些 tag 造成差異，分析是「新版更正確」還是「新版漏抓」。

### Step 2 — 驗證 OT tag 的 `lang` 欄位

檢查所有 OT 帶 prefix 的 tag 是否都有 `lang == "H"`。若全部為 True → #5, #10 保證等效。

### Step 3 — 若有分歧：5% 經節級回測

用 `sample_test_set.py --pct 5 --testament OT` 取約 1,200 節。對每節同時跑舊版和新版邏輯，比較 8 個維度的結果。報告每個維度的差異數。

## 通過標準 (Pass Criteria)

| Step | 條件 | 通過 |
|------|------|------|
| 1 | 所有 OT tag 的 morph 偵測舊新一致（或新版更正確） | ✓ |
| 2 | 所有 OT prefix tag 的 lang == "H" | ✓ |
| 1+2 通過 | → 8 個維度全部保證等效 | **REGRESSION PASS** |
| 有分歧 | → Step 3 跑 5% 取樣，報告 delta | 視 delta 判斷 |

## 實作方式 (Implementation)

Inline python（不建新檔案）。從 dim_verse_map.json 讀 OT 經節列表，重新 fetch + extract_tags，逐 tag 比較舊新 morph 偵測。純唯讀驗證，不修改任何檔案。
