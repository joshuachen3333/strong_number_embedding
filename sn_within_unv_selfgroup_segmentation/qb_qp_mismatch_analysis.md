# QB-QP Mismatch Analysis Report (qb/qp 不匹配分析報告)

## 問題概述 (Problem Overview)

在 Genesis 和 Exodus 的解析過程中，發現了 **347 個 Strong's 編號不匹配** 案例。這些案例記錄在 `strong_number_from_qb.php_not_found_in_qp.php.txt` 中，錯誤訊息為：

```
Strong's number <XXXXX> from qb.php not found in qp.php records.
```

---

## 起心動念：為何需要此日誌檔案？(Why This Log File?)

### 問題發現的時間點

在實作 v1.8 解析器時，我們需要同時從兩個 FHL API 端點獲取數據：

1. **qb.php** - 提供中文譯文（UNV）+ Strong's 編號
2. **qp.php** - 提供希伯來/希臘原文的形態學分析

### 核心困境

解析器的設計邏輯是：
```
對於 qb.php 中的每個 Strong's 編號
  → 查詢 qp.php 獲取其形態學資訊（詞性、動詞形態等）
  → 生成中文輸出時需要這些資訊
```

但實際運行時發現：**qb.php 中出現的某些 Strong's 編號在 qp.php 中找不到對應記錄！**

### 初期的混亂

最初這些案例被記錄在 `uncertain_or_expandable_issues.txt` 中，與其他類型的不確定性混在一起：
- 括號介系詞附著歧義
- 懸空前綴
- qb/qp 不匹配

這造成了分析困難：**無法快速識別是數據問題還是解析邏輯問題**。

### 分離的契機（v1.8.1）

在處理 Genesis + Exodus 的 2,746 節經文後，統計顯示：
- **347 個案例（59.3%）** 是 qb/qp 不匹配
- 這是**最常見的問題類型**
- 這些案例有共同特徵：都是 FHL 數據不一致，與解析邏輯無關

**決定**：將其分離到專用日誌檔案 `strong_number_from_qb.php_not_found_in_qp.php.txt`（v1.8.1）

---

## 什麼是 qb.php 和 qp.php？(What are qb.php and qp.php?)

### qb.php - Bible Text API (聖經經文 API)

**用途**：返回指定經文的中文翻譯文本 + Strong's 編號

**參數**：
```
version=unv           // 和合本
chineses=創           // 中文書卷縮寫
chap=1                // 章
sec=1                 // 節
strong=1              // 包含 Strong's 編號
```

**返回範例**（Gen 1:1）：
```json
{
  "record": [{
    "sec": "1",
    "bible_text": "起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>..."
  }]
}
```

### qp.php - Parsing/Morphology API (原文解析 API)

**用途**：返回希伯來/希臘原文的逐詞形態學分析

**參數**：
```
engs=Gen              // 英文書卷縮寫
chap=1                // 章
sec=1                 // 節
```

**返回範例**（Gen 1:1）：
```json
{
  "record": [{
    "sn": "7225",
    "w": "בְּרֵאשִׁית",
    "wform": "介系詞 בְּ + 名詞，陰性單數附屬形",
    "exp": "開始、首要"
  }]
}
```

### 理想情況 vs. 現實

**理想情況**：
```
qb.php 中的 <WH07225> → 在 qp.php 中找到 sn=7225 的記錄 ✅
```

**實際情況**（347 個案例）：
```
qb.php 中的 <WH03212> → 在 qp.php 中找不到 sn=3212 ❌
```

---

## 根本原因分析 (Root Cause Analysis)

### 原因 1：qb.php 和 qp.php 的數據來源不同

**猜測的數據流**：
```
qb.php ← FHL 中文聖經資料庫（包含人工標註的 Strong's 編號）
qp.php ← FHL 原文聖經資料庫（BHS 希伯來文本、WH 希臘文本）
```

這兩個資料庫**不是從同一個主資料庫生成的**，而是獨立維護的。

### 原因 2：中文聖經的 Strong's 標註較為激進

中文聖經（qb.php）的標註者：
- 為了幫助中文讀者理解，盡可能為每個中文詞語標註 Strong's 編號
- 有時會標註**隱含的概念**（雖然原文中沒有明確對應的詞）
- 有時會為**補充說明的詞語**添加 Strong's 編號

原文資料庫（qp.php）：
- 只記錄**實際存在於原文中的詞語**
- 不包含翻譯過程中添加的補充詞語

### 原因 3：版本更新不同步

可能的時間線：
```
某個時間點：qb.php 的 Strong's 標註被更新或修正
另一個時間點：qp.php 的原文分析保持原樣
結果：兩者出現不一致
```

### 原因 4：某些 Strong's 編號在原文資料庫中根本不存在

有些 Strong's 編號可能是：
- 後來添加的補充編號
- 特殊用途的標記（如段落標記 09015）
- 中文聖經特有的編碼

---

## 統計數據 (Statistics)

### 總體分佈
- **Genesis（創世記）**：234 個案例
- **Exodus（出埃及記）**：113 個案例
- **總計**：347 個案例
- **佔所有問題的比例**：59.3% (347/585)

### 影響評估
- **是最常見的問題類型**（比其他所有問題加起來還多）
- **不影響解析器核心功能**（仍能生成輸出）
- **影響輸出質量**（缺少形態學資訊）

---

## 典型案例詳解 (Case Studies)

### 案例 1：Gen 3:14 - 常見動詞案例

**qb.php 輸出**：
```
Raw UNV+SN: ...你必用肚子<WH01512>行走<WH03212><WTH8799>...
```

**問題**：
- Strong's <03212> 出現在 qb.php 中
- 在 qp.php 的所有記錄中找不到 sn=3212

**解析器行為**：
```
<03212>(8799) — 未知詞性「未知意義」 *N
*N: 動詞，Qal 未完成式 2 單陽
```
- 仍然能從 `<WTH8799>` 獲取形態學資訊（8799 = Qal 未完成式）
- 但無法獲取中文意義「行走」
- 標記為「未知詞性」和「未知意義」

**KJV 交叉參照**：
```
KJV: ...upon thy belly shalt thou go<03212><8799>...
```
- KJV 也使用 <03212>
- 說明這不是 UNV 特有的問題
- 這個 Strong's 編號是有效的（意思是「行走、去」）

### 案例 2：Gen 5:29 - 專有名詞案例

**qb.php 輸出**：
```
Raw UNV+SN: ...給他起名<WH08034>叫<WAH0853>挪亞<WH05146>...
```

**問題**：
- Strong's <05146> (挪亞/Noah) 在 qp.php 中找不到

**分析**：
- 專有名詞在原文資料庫中可能被省略
- 或者使用不同的編碼方式
- 專有名詞的形態學分析相對簡單（通常就是「專有名詞」）

### 案例 3：Gen 12:5 - 補充詞語案例

**qb.php 輸出**：
```
Raw UNV+SN: ...他們在迦南<WH03667>地<WAH09002><WH0776>所<WAH0834>得<WH07408><WTH8804>的財物...
```

**問題**：
- 某些助詞或補充詞語在 qb.php 中被標註
- 但原文中可能沒有對應的獨立詞語

---

## KJV 交叉參照功能 (KJV Cross-Reference Feature)

### 為何添加 KJV 參照？

在 v1.8.1 中，我們為每個 qb/qp 不匹配的案例添加了 KJV 交叉參照：

```
Strong's number <03212> from qb.php not found in qp.php records. | KJV also uses <03212>
```

### 設計理念

**目的**：判斷問題的範圍
- 如果 **KJV 也使用同一個 Strong's 編號** → 說明這個編號是有效的，問題出在 qp.php 資料庫不完整
- 如果 **KJV 使用不同的編號** → 可能是 UNV 的特殊標註方式

### 實作細節

```python
def fetch_kjv_strongs(verse_ref, target_sn):
    """
    獲取 KJV 經文並檢查是否使用相同的 Strong's 編號

    Returns:
        "KJV also uses <XXXXX>" - 找到相同編號
        "KJV uses different Strong's numbers" - 使用不同編號
        None - 無法獲取 KJV 數據
    """
```

**優點**：
1. **快速判斷**：一眼看出是 FHL 資料庫問題還是 UNV 特有問題
2. **幫助除錯**：如果大多數案例 KJV 也使用，說明是 qp.php 不完整
3. **提供線索**：為後續改進提供方向

---

## 解析器行為評估 (Parser Behavior Assessment)

### 當前解析器的處理方式 ✅

當遇到 qb/qp 不匹配時：

1. **檢測**：嘗試在 qp.php 記錄中查找對應的 Strong's 編號
2. **降級處理**：如果找不到
   - 詞性顯示為「未知詞性」
   - 中文意義顯示為「未知意義」
   - 仍然顯示 Strong's 編號和形態學代碼（如果有）
3. **記錄日誌**：記錄到 `strong_number_from_qb.php_not_found_in_qp.php.txt`
4. **繼續解析**：不中斷，繼續處理後續 token

### 輸出範例

**有 qp.php 資料的正常輸出**：
```
<07225> — 名詞「開始、首要」
```

**qb/qp 不匹配的降級輸出**：
```
<03212> — 未知詞性「未知意義」
```

**仍然可以顯示形態學**（如果有 8xxx 代碼）：
```
<03212>(8799) — 未知詞性「未知意義」 *1
*1: 動詞，Qal 未完成式 2 單陽
```

### 這不是解析器的錯誤 ✅

解析器**正確地處理了數據缺失的情況**：
1. **優雅降級**：不會因為缺少數據而崩潰
2. **提供可用資訊**：盡可能顯示從其他來源獲取的資訊
3. **清晰標記**：明確標示為「未知」
4. **完整記錄**：記錄所有不匹配案例供後續分析

---

## 影響評估 (Impact Assessment)

### 對解析結果的影響

#### 影響程度：中等 🟡

1. **不影響結構**：
   - Strong's 編號的分組邏輯仍然正確
   - 900x 前綴附著正常
   - 括號介系詞處理正常

2. **影響語義資訊**：
   - 缺少中文意義說明
   - 缺少詞性資訊
   - 影響使用者理解

3. **部分補償**：
   - 如果有 8xxx 形態學代碼，仍能提供部分資訊
   - Strong's 編號本身是正確的，使用者可以查詢 Strong's 字典

### 對使用者體驗的影響

**好的方面**：
- ✅ 解析不會失敗
- ✅ 仍能看到 Strong's 編號
- ✅ 結構分組正確

**不好的方面**：
- ❌ 「未知詞性」和「未知意義」不夠友善
- ❌ 需要額外查詢 Strong's 字典
- ❌ 對新手不友善

---

## 解決方案與改進建議 (Solutions and Improvements)

### 短期方案（已實作 ✅）

#### 1. 專用日誌檔案（v1.8.1）
```
strong_number_from_qb.php_not_found_in_qp.php.txt
```
- 清晰分類
- 便於統計和分析
- 與其他問題類型分離

#### 2. KJV 交叉參照（v1.8.1）
```
| KJV also uses <03212>
```
- 快速判斷問題性質
- 提供額外驗證

#### 3. 優雅降級
```
<03212> — 未知詞性「未知意義」
```
- 不中斷解析
- 顯示可用資訊

### 中期方案（建議實施）

#### 1. 建立本地 Strong's 字典快取

**概念**：
```python
# 預先下載完整的 Strong's 字典
STRONGS_DICT = {
    "03212": {
        "pos": "動詞",
        "meaning": "行走、去、來",
        "transliteration": "halak"
    },
    # ...
}

# 當 qp.php 缺少資料時，回退到本地字典
if sn not in qp_records:
    info = STRONGS_DICT.get(sn, {})
    return info.get("meaning", "未知意義")
```

**優點**：
- 大幅改善使用者體驗
- 不依賴 FHL API
- 解析結果更完整

**來源**：
- OpenScriptures Strong's dictionary (開源)
- STEPBible (CC BY 4.0)
- Blue Letter Bible API

#### 2. 改進輸出格式

**當前**：
```
<03212> — 未知詞性「未知意義」
```

**改進後**：
```
<03212> — 動詞「行走、去」[註：資料來自 Strong's 字典，非 qp.php]
```

### 長期方案（未來考慮）

#### 1. 向 FHL 反饋

整理完整的不匹配列表，提交給 FHL：
```
"以下 347 個 Strong's 編號在 qb.php 中出現但 qp.php 中缺少：
<03212>, <05146>, <07408>, ..."
```

**期望結果**：
- FHL 補充 qp.php 資料庫
- 或說明這些編號的特殊性質

#### 2. 替代數據源

如果 FHL 無法改進，考慮：
- 使用其他聖經原文資料庫（如 OSHB, OGNT）
- 建立自己的形態學資料庫
- 整合多個數據源

---

## 日誌格式與使用 (Log Format and Usage)

### 日誌格式

```
[timestamp] verse_ref | qb_qp_mismatch | description | KJV_reference
```

### 實際範例

```
[2025-11-25 01:57:42] Gen 3:14 | qb_qp_mismatch | Strong's number <03212> from qb.php not found in qp.php records. | KJV also uses <03212>
[2025-11-25 02:01:15] Gen 5:29 | qb_qp_mismatch | Strong's number <05146> from qb.php not found in qp.php records. | KJV also uses <05146>
[2025-11-25 02:05:33] Gen 12:5 | qb_qp_mismatch | Strong's number <07408> from qb.php not found in qp.php records. | KJV uses different Strong's numbers
```

### 如何使用日誌

#### 統計分析
```bash
# 總共有多少不匹配案例
wc -l output/strong_number_from_qb.php_not_found_in_qp.php.txt

# 找出特定書卷的案例
grep "Gen " output/strong_number_from_qb.php_not_found_in_qp.php.txt

# 統計哪些 Strong's 編號最常出現問題
grep -o '<[0-9]*>' output/strong_number_from_qb.php_not_found_in_qp.php.txt | sort | uniq -c | sort -rn
```

#### 生成 Strong's 字典需求清單
```bash
# 提取所有缺少的 Strong's 編號
grep -o '<[0-9]*>' output/strong_number_from_qb.php_not_found_in_qp.php.txt | sort -u > missing_strongs.txt
```

#### KJV 一致性分析
```bash
# 有多少案例 KJV 也使用同樣的編號
grep "KJV also uses" output/strong_number_from_qb.php_not_found_in_qp.php.txt | wc -l

# 有多少案例 KJV 使用不同編號
grep "KJV uses different" output/strong_number_from_qb.php_not_found_in_qp.php.txt | wc -l
```

---

## 結論 (Conclusion)

### 問題本質

**qb/qp 不匹配是 FHL 數據編碼的系統性問題**：
- 兩個 API 端點的資料庫不同步
- qb.php 的標註比 qp.php 更完整（或更激進）
- 影響 347 個案例（佔所有問題的 59.3%）

### 解析器行為

**解析器的處理是正確的**：
- ✅ 檢測到問題
- ✅ 優雅降級（不崩潰）
- ✅ 記錄到專用日誌
- ✅ 提供 KJV 交叉參照

### 不需要規範更新 ✅

**理由**：
1. 這是**數據問題**，不是解析邏輯問題
2. 解析器已經正確處理了這種情況
3. 無法通過修改規範來解決
4. 需要的是**數據補充**，不是**邏輯修改**

### 建議的改進路徑

**優先級排序**：
1. **高優先級**：建立本地 Strong's 字典快取（大幅改善使用者體驗）
2. **中優先級**：向 FHL 反饋問題列表
3. **低優先級**：考慮替代數據源（如果 FHL 無法改進）

---

## 相關文檔 (Related Documentation)

- **SPECIFICATION_v1.8.md** - 主要規範文檔
- **CLAUDE.md** - 專案說明文檔
- **parse_verse_v1_8.py** - v1.8 解析器實作
- **dangling_prefixes.md** - 懸空前綴分析（類似的數據問題）

---

## 版本歷史 (Version History)

- **v1.8** - qb/qp 不匹配案例混雜在 uncertain_or_expandable_issues.txt 中
- **v1.8.1** - 分離到專用日誌 `strong_number_from_qb.php_not_found_in_qp.php.txt`，添加 KJV 交叉參照
- **分析範圍** - 2,746 節經文（Genesis 1,533 + Exodus 1,213）
- **文檔創建日期** - 2025-11-25

---

**總結**：347 個 qb/qp 不匹配案例反映了 FHL 兩個 API 端點之間的數據不同步問題。解析器正確識別並優雅處理這些案例。建議透過建立本地 Strong's 字典快取來改善使用者體驗，而不是修改解析器規範。
