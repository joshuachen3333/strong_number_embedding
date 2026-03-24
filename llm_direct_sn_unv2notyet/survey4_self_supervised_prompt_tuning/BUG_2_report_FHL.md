# BUG Report — FHL UNV+SN Data Anomaly

## Summary

約書亞記 9:21 的 UNV+SN 資料中有一個 6 位數的 Strong's Number `<WAH019691>`，應為 5 位數 `<WAH01961>`。

## Details

### 問題經節

**Josh 9:21** (書 9:21)

UNV+SN (`qb.php?version=unv&chineses=書&chap=9&sec=21&strong=1`):
```
...全<WAH09001><WAH03605>會眾<WH05712>作了<WAH019691>劈<WH02404><WTH8802>柴...
```

`<WAH019691>` — 6 位數，不符合 FHL SN 格式規範（最多 5 位）。

### 正確值

`qp.php?engs=Josh&chap=9&sec=21` 的 wid=5 記錄：
```json
{
  "wid": 5,
  "word": "וַיִּהְיוּ",
  "sn": "01961",
  "wform": "動詞，Qal 敘述式 3 複陽",
  "orig": "הָיָה",
  "exp": "是、成為、臨到"
}
```

正確 SN = **01961** (הָיָה = 是、成為)，應為 `<WAH01961>`。

### KJV 對照

KJV 的同節無此問題（KJV `qb.php` 中此字對應的 SN 為標準格式）。

### 錯誤分析

`019691` 看起來是 `01961` 後面多插入了一個 `9`，可能是資料庫寫入時的 typo 或數據遷移錯誤。

## 影響

- 下游系統（如 LLM-based SN transfer）解析此 tag 時會因格式異常而出錯
- 模型可能嘗試「修正」此異常，導致不可預期的輸出

## 發現方式

使用 `analyze_test_dimensions.py` 掃描約書亞記全書時，uncovered pattern detector 偵測到 "Unusually long number"，經 `qp.php` 交叉驗證確認為資料錯誤。

## 建議修正

將 `qb.php` 中書 9:21 的 `<WAH019691>` 修正為 `<WAH01961>`。

---

## BUG 2: Morph Code with WAH Prefix (1Sam 14:32)

### Summary

撒母耳記上 14:32 的 Ketiv/Qere 標記使用了 `<WAH08675>` (WAH prefix + 5 位數零填充)，而非標準格式 `<WTH8675>` (WTH prefix + 4 位數)。

### Details

**1Sam 14:32** (撒上 14:32)

UNV+SN:
```
...百姓<WH05971>就飛<WH05860><WTH8799><WAH08675>奔上前去<WH06213><WTH8799>...
```

同一個 morph code 8675 (infinitive absolute) 在不同經節格式不一致：

| 經節 | 標記 | Prefix | 位數 |
|------|------|--------|------|
| Exod 16:7 | `<WTH8675>` | WTH (正確) | 4 位 |
| 1Sam 14:32 | `<WAH08675>` | WAH (異常) | 5 位零填充 |

### qp.php 確認

`qp.php?engs=1 Sam&chap=14&sec=21` wid=1:
```json
{
  "wid": 1,
  "word": "וַיַּעַשׂ",
  "sn": "05860",
  "wform": "這是寫型，其讀型為 וַיַּעַט。按讀型，它是動詞，Qal 敘述式 3 單陽",
  "orig": "עִיט",
  "remark": "如按寫型 וַיַּעַשׂ，它是動詞 עָשָׂה (做, SN 6213)，Qal 敘述式 3 單陽。"
}
```

確認為 Ketiv/Qere：讀型 עִיט (SN 05860) vs 寫型 עָשָׂה (SN 06213)。morph 8675 是 infinitive absolute 標記，應使用 WTH prefix。

### 影響

- 格式不一致導致 morph code 偵測邏輯需要額外處理 WAH prefix 變體
- `<WAH08675>` 語法上與正常 SN 8675 (WAH prefix + zero-padded) 無法區分

### 建議修正

將 `qb.php` 中撒上 14:32 的 `<WAH08675>` 修正為 `<WTH8675>`。

---

---

## BUG 3: 6-Digit SN in 2Chr 27:8 (031961)

### Summary

歷代志下 27:8 的 UNV+SN 資料中有一個 6 位數的 Strong's Number `{<WAH031961>}`，應為 5 位數 `{<WAH01961>}`。

### Details

**2Chr 27:8** (代下 27:8)

UNV+SN:
```
{<WAH031961>}他登基<WAH09002><WH04427><WTH8800>的時候...
```

`{<WAH031961>}` — 6 位數 `031961`，不符合 FHL SN 格式規範。

### qp.php 確認

`qp.php?engs=2 Chr&chap=27&sec=8` wid=5:
```json
{
  "wid": 5,
  "word": "הָיָה",
  "sn": "01961"
}
```

正確 SN = **01961** (הָיָה = 是、成為)。`031961` 看起來是 `03` + `1961` 被黏在一起。

### KJV 對照

KJV 同節無 הָיָה 的 SN（KJV 跳過此字），確認這是 UNV 專有的資料錯誤。

### 與 BUG 1 的關聯

兩個 bug 都涉及 SN 01961 (הָיָה)：
- Josh 9:21: `<WAH019691>` (多插入一個 9)
- 2Chr 27:8: `{<WAH031961>}` (前面多了 03)

可能是同一個資料遷移問題的不同表現。

### 建議修正

將 `qb.php` 中代下 27:8 的 `{<WAH031961>}` 修正為 `{<WAH01961>}`。

---

## Status

- [ ] BUG 1 (Josh 9:21 `<WAH019691>`) 已回報 FHL
- [ ] BUG 2 (1Sam 14:32 `<WAH08675>`) 已回報 FHL
- [ ] BUG 3 (2Chr 27:8 `{<WAH031961>}`) 已回報 FHL
- [ ] FHL 已修正

---

Discovered: 2026-03-24 by survey4 dimension analysis scan.
