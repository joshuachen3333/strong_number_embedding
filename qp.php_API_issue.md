# qp.php API 書卷代碼問題

## 問題

FHL 的 `qp.php`（逐字原文 API）和 `qb.php`（經文 API）使用**不同的書卷代碼**。

- `qb.php`：用 `Exod`, `1Sam`, `1Cor` 等（CHI_TO_ENG 映射表的代碼）
- `qp.php`：用 `Ex`, `James`, `Jon` 等，且**不支持任何帶數字前綴的書卷**

## API

```
GET https://bible.fhl.net/json/qp.php?engs={book}&chap={chap}&sec={sec}
```

文件參考：https://bible.fhl.net/json/ → https://bible.fhl.net/new/allreadme.html

## 匯總（66 書卷，2026-03-30 測試）

### ✅ 直接可用（44 books）

qb.php 和 qp.php 用同一個代碼：

```
Acts Amos Col Dan Deut Eccl Eph Esth Ezek Ezra Gal Gen Hab Hag Heb
Hos Jer Job Joel John Josh Jude Judg Lam Lev Luke Mal Mark Matt Mic
Nah Neh Num Obad Phil Prov Ps Rev Rom Ruth Song Titus Zech Zeph
```

### 🔄 需要映射（5 books）

| qb.php (CHI_TO_ENG) | qp.php | 中文 |
|---------------------|--------|------|
| Exod | Ex | 出 |
| Isa | Is | 賽 |
| Jonah | Jon | 拿 |
| Jas | James | 雅 |
| Phlm | Philem | 門 |

### ❌ 不支持（17 books）

全部是帶數字前綴的書卷。測試了各種格式（1Sa, 1+Samuel, I+Sam 等）均回傳 `Fail:engs error!`。

| qb.php 代碼 | 中文 | 嘗試過的 qp.php 代碼 |
|-------------|------|---------------------|
| 1Sam | 撒上 | 1Sa, 1Sm, 1Samuel, 1+Samuel, ISam |
| 2Sam | 撒下 | 同上模式 |
| 1Kgs | 王上 | 1Ki, 1Kg, 1Kings, 1+Kings |
| 2Kgs | 王下 | 同上模式 |
| 1Chr | 代上 | 1Ch, 1Chr, 1Chronicles（文件說 1Ch 可用但實測失敗）|
| 2Chr | 代下 | 同上模式 |
| 1Cor | 林前 | 1Co, 1Cor, 1Corinthians |
| 2Cor | 林後 | 同上模式 |
| 1Thess | 帖前 | 1Th, 1Thess, 1Thessalonians |
| 2Thess | 帖後 | 同上模式 |
| 1Tim | 提前 | 1Ti, 1Tim, 1Timothy |
| 2Tim | 提後 | 同上模式 |
| 1Pet | 彼前 | 1Pe, 1Pet, 1Peter |
| 2Pet | 彼後 | 同上模式 |
| 1John | 約一 | 1Jo, 1Jn, 1+John（1+John 之前測試曾成功，後來失敗）|
| 2John | 約二 | 同上模式 |
| 3John | 約三 | 同上模式 |

## 影響

- **survey6**：這 17 本書無法取得原文逐字資料（qp.php word + sn）
- **survey8**：這 17 本書無法建立 SN:原文字 字典
- **survey9**：這 17 本書跑 LLM 時缺原文/字典輸入，但 UNV+SN 的裸數字仍在，LLM 仍可搬運

## 處理方式

`run_survey6.py` 中的 `fetch_qp_verse()` 已有 `_QP_BOOK_MAP` 映射表處理 5 本需映射的書卷。17 本不支持的書卷，在 survey9 中 gracefully fallback（跳過原文/字典，仍跑 LLM）。

## 待辦

- [ ] 向 FHL 回報 qp.php 不支持帶數字書卷的問題
- [ ] 確認是否有未公開的正確代碼格式
- [ ] 如有修復，更新 `_QP_BOOK_MAP`
