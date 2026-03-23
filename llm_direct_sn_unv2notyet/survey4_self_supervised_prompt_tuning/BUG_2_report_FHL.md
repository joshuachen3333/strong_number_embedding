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

## Status

- [ ] 已回報 FHL
- [ ] FHL 已修正

---

Discovered: 2026-03-24 by survey4 dimension analysis scan.
