# Compatible But Notable Issues Analysis Report

## 起心動念：為何需要此日誌檔案？(Origin Story)

### 解析器的兩難：如何處理「邊界案例」？

在實作 UNV+SN 解析器時，我們面臨一個關鍵的設計問題：

**場景**：某些經文的解析雖然**技術上成功**，但存在**值得注意的特殊情況**

**兩難處境**：
- ❌ 標記為 `_uncertain` → 太嚴格，使用者會誤以為解析失敗
- ❌ 完全不記錄 → 失去質量追蹤，無法發現潛在規範改進點
- ✅ 需要第三種分類：**成功解析，但值得關注**

### 解決方案：Compatible But Notable Issues

**設計理念**：

**"Compatible"（相容）**：
- 解析**完全成功**，輸出符合規範
- 不影響使用者正常使用
- 不需要標記為 `_uncertain`

**"Notable"（值得注意）**：
- 存在特殊語言學情況
- 可能暴露規範邊界
- 有助於未來版本改進
- 值得人工審查和質量保證

**目的**：
1. 質量保證追蹤
2. 規範改進線索
3. 邊界案例文檔化
4. 未來版本參考

---

## 什麼樣的案例會記錄到此日誌？(What Gets Logged?)

### 分類決策樹

```
解析過程中遇到 Warning
         │
         ▼
   ┌──────────────┐
   │ 是否為特定   │
   │ 已知類型？   │
   └──────┬───────┘
          │
    ┌─────┴──────┐
    │            │
   YES          NO
    │            │
    ▼            ▼
┌────────────┐  ┌──────────────────┐
│ qb_qp      │  │ 其他未分類警告    │
│ mismatch?  │  │ (Other warnings)  │
└─────┬──────┘  └─────┬────────────┘
      │               │
     YES              │
      │               │
      ▼               │
  qb_qp_mismatch.txt  │
                      │
┌─────────────────────┘
│
▼
┌────────────┐
│ dangling_  │
│ p900x?     │
└─────┬──────┘
      │
 ┌────┴────┐
YES       NO
 │         │
 ▼         ▼
dangling   ┌────────────┐
_prefixes  │ 其他        │
.txt       │ dangling_* │
           │ 或 brace_  │
           │ attach_    │
           │ ambiguous? │
           └─────┬──────┘
                 │
            ┌────┴────┐
           YES       NO
            │         │
            ▼         ▼
      uncertain_or   compatible_but
      _expandable    _notable ⭐
      _issues.txt    _issues.txt
```

### 記錄標準

記錄到 `compatible_but_notable_issues.txt` 的條件：

**1. 解析成功 ✅**
- 必須有有效的輸出
- 所有 tokens 都正確分組
- 符合 SPECIFICATION 規範

**2. 存在 Warning ⚠️**
- 但 warning 不屬於已知的「問題」類別
- 不是 `dangling_*`（懸空 token）
- 不是 `brace_attach_ambiguous`（模糊附著）
- 不是 `qb_qp_mismatch`（數據不匹配）
- 不是 `prep_noun_compound`（設計選擇）

**3. 值得關注 👀**
- 邊界語言學現象
- 規範未明確覆蓋的情況
- 多種合理解釋存在
- 未來可能需要規範澄清

---

## 典型案例類型 (Typical Case Types)

### 類型 1：多義性附著（Multiple Valid Attachments）

**場景**：某個 token 理論上可以附著到左側或右側，兩者都符合語法

**範例（假設）**：Gen X:Y
```
Raw UNV+SN: ...他將{<05921>}這些話<WH01697>說給...
```

**語言學分析**：
- `{<05921>}` (עַל, upon/concerning) 可能：
  - 左附著：「he spoke-upon」（動詞的介系詞補語）
  - 右附著：「upon-these-words」（名詞的修飾語）
- 兩種解釋都合理

**解析器行為**：
- 應用規範的一般規則（例如：右附著到名詞）
- 成功輸出
- 但記錄 warning: `multiple_valid_attachments`

**日誌記錄**：
```
[timestamp] Gen X:Y | multiple_valid_attachments |
Brace preposition <05921> could attach to verb or noun;
chose noun per general rule - review recommended
```

---

### 類型 2：罕見語法結構（Rare Grammatical Constructions）

**場景**：符合規範，但在語料庫中極為罕見

**範例（假設）**：Exod A:B
```
Raw UNV+SN: ...{<0853>}{<0853>}連續兩個受詞標記...
```

**語言學分析**：
- 連續兩個 `{<0853>}` 受詞標記
- 文法上合法（雙賓語結構）
- 但在整個聖經中可能只出現 1-2 次

**解析器行為**：
- 正確處理每個受詞標記
- 成功輸出
- 記錄 warning: `rare_construction`

**日誌記錄**：
```
[timestamp] Exod A:B | rare_construction |
Double object marker {<0853>}{<0853>} detected -
grammatically valid but statistically rare
```

---

### 類型 3：規範邊界情況（Spec Boundary Cases）

**場景**：規範未明確涵蓋，需要推斷應用規則

**範例（假設）**：Gen M:N
```
Raw UNV+SN: ...<09001><09002><09009>三個前綴疊加<WH01004>...
```

**語言學分析**：
- 三個 900x 前綴連續出現
- 規範說明前綴應附著到後續核心 token
- 但未明確說明「多個前綴」的順序處理

**解析器行為**：
- 假設：所有前綴按順序疊加到核心 token
- 成功輸出：`<09001><09002><09009><01004>`
- 記錄 warning: `spec_boundary_multiple_prefixes`

**日誌記錄**：
```
[timestamp] Gen M:N | spec_boundary_multiple_prefixes |
Three consecutive 900x prefixes stacked - all attached to
next core token per inferred rule - spec clarification may help
```

---

### 類型 4：FHL 編碼異常（但可解析）

**場景**：FHL 數據編碼異常，但解析器仍能處理

**範例（假設）**：Exod P:Q
```
Raw UNV+SN: ...<WH01234>(**8804)(**8675)兩個形態碼...
```

**語言學分析**：
- 一個核心 token 後跟**兩個**形態碼
- 通常一個動詞只有一個主要形態標記
- 可能是 FHL 編碼錯誤或特殊情況

**解析器行為**：
- 將兩個形態碼都附著到核心 token
- 成功輸出
- 記錄 warning: `multiple_morphology_codes`

**日誌記錄**：
```
[timestamp] Exod P:Q | multiple_morphology_codes |
Core token <01234> followed by two morphology codes
(**8804)(**8675) - both attached per left-attach rule -
may indicate FHL encoding anomaly
```

---

### 類型 5：上下文相依解析（Context-Dependent Parsing）

**場景**：解析決策依賴於語意上下文，純句法分析有歧義

**範例（假設）**：Gen R:S
```
Raw UNV+SN: ...神{<04480>}天上<WH08064>降下...
```

**語言學分析**：
- `{<04480>}` (מִן, from) 可能：
  - 動詞補語：「神從...降下」
  - 名詞修飾：「從天上（來的）神」
- 需要語意理解才能確定

**解析器行為**：
- 應用規範一般規則（檢查右側是否為名詞）
- 成功輸出
- 記錄 warning: `context_dependent_attachment`

**日誌記錄**：
```
[timestamp] Gen R:S | context_dependent_attachment |
Brace preposition <04480> attachment required semantic context;
applied syntactic rule - semantic review recommended
```

---

## 與其他日誌檔案的關係 (Relationship to Other Logs)

### 五層日誌系統定位

```
Issue Severity Pyramid (問題嚴重性金字塔)

    ┌─────────────────────────────────────┐
    │ qb_qp_mismatch.txt                  │ ← 數據缺失，最嚴重
    │ (Strong's number missing in qp.php) │
    └─────────────────────────────────────┘
              ▲
              │
    ┌─────────────────────────────────────┐
    │ dangling_prefixes.txt               │ ← 翻譯不匹配
    │ (900x translation artifacts)        │
    └─────────────────────────────────────┘
              ▲
              │
    ┌─────────────────────────────────────┐
    │ uncertain_or_expandable_issues.txt  │ ← 真正的不確定性
    │ (Parsing ambiguities)               │
    └─────────────────────────────────────┘
              ▲
              │
    ┌─────────────────────────────────────┐
    │ compatible_but_notable_issues.txt   │ ← 邊界案例 ⭐
    │ (Edge cases, spec boundaries)       │
    └─────────────────────────────────────┘
              ▲
              │
    ┌─────────────────────────────────────┐
    │ compound_prep_plus_noun.txt         │ ← 設計選擇，最輕微
    │ (Intentional non-merges)            │
    └─────────────────────────────────────┘
```

### 差異對比表

| 日誌檔案 | 問題類型 | 影響解析 | 需要修正 | 標記 uncertain |
|---------|---------|---------|---------|---------------|
| qb_qp_mismatch | 數據缺失 | ⚠️ 可能 | 需 FHL 修正 | ✅ 是 |
| dangling_prefixes | 編碼限制 | ❌ 否 | FHL 設計決策 | ❌ 否 |
| uncertain_or_expandable | 解析歧義 | ⚠️ 可能 | 需規範擴展 | ✅ 是 |
| **compatible_but_notable** | **邊界案例** | **❌ 否** | **質量追蹤** | **❌ 否** |
| compound_prep_plus_noun | 設計選擇 | ❌ 否 | 無需修正 | ❌ 否 |

### 關鍵區別

**uncertain_or_expandable_issues.txt** vs **compatible_but_notable_issues.txt**：

**Uncertain** (不確定)：
- 解析器**無法確定**正確附著點
- 輸出**可能不正確**
- 檔案標記為 `{verse}_uncertain`
- 需要規範明確擴展或人工判斷

**Compatible But Notable** (相容但值得注意)：
- 解析器**能夠解析**並產生合理輸出
- 輸出**符合規範**
- 檔案**不標記** `_uncertain`
- 但值得記錄以追蹤質量和改進機會

**範例對比**：

```
Uncertain 案例：
Gen 19:5 | dangling_brace_prep | Brace preposition <0413> had
no suitable attachment point.
→ 解析器無法決定如何處理 <0413>
→ 輸出可能不完整或不正確
→ 標記為 19_uncertain

Compatible But Notable 案例：
Gen X:Y | multiple_valid_attachments | Brace preposition <05921>
could attach to verb or noun; chose noun per general rule.
→ 解析器成功應用規範規則
→ 輸出完整且符合規範
→ 檔案命名為 Y（不加 _uncertain）
→ 但記錄此案例以備質量審查
```

---

## 程式碼邏輯 (Code Logic)

### 分類決策實作

```python
# 在 parse_verse_v1_8.py 的日誌邏輯（約 line 622-636）

for warning in group.get('warnings', []):
    warning_message = render_warning_message(group, warning)

    if output_lines and warning_message:
        # Log warnings to appropriate file

        # Category 1: qb/qp mismatch (highest priority)
        if warning == "qb_qp_core_mismatch":
            append_to_log(QB_QP_MISMATCH_LOG, verse_ref, warning, warning_message)

        # Category 2: Dangling 900x prefixes (translation artifacts)
        elif warning == "dangling_p900x":
            append_to_log(DANGLING_PREFIXES_LOG, verse_ref, warning, warning_message)

        # Category 3: Uncertain issues (true parsing ambiguities)
        elif any(w in warning for w in ["dangling", "ambiguous"]):
            append_to_log(UNCERTAIN_LOG, verse_ref, warning, warning_message)

        # Category 4: Compatible but notable (everything else) ⭐
        else:
            append_to_log(NOTABLE_LOG, verse_ref, warning, warning_message)
```

### 關鍵設計決策

**"Everything Else" 策略**：
- 所有不屬於已知「問題」類別的 warning
- 都歸類為 "compatible but notable"
- 確保**沒有 warning 被遺漏**

**為何這樣設計？**

**1. 保守原則**
- 寧可多記錄，不可漏記錄
- 所有異常情況都應該被追蹤

**2. 未來擴展性**
- 新類型的 warning 會自動進入 notable log
- 之後可以決定是否需要新的專用日誌

**3. 質量保證**
- 定期審查 notable log
- 發現需要規範澄清的模式
- 識別 FHL 數據改進機會

---

## 當前狀態 (Current Status)

### Genesis + Exodus 解析結果

經過 Genesis (1,533 verses) 和 Exodus (1,213 verses) 的完整解析：

**compatible_but_notable_issues.txt 狀態**：
- **檔案存在**：❌ 否
- **原因**：在當前的 2,746 節經文中，所有 warnings 都被分類到其他四個專用日誌檔

### 已記錄的 Warning 類型分佈

```
Genesis + Exodus 總計：
- qb_qp_mismatch:         347 cases → qb_qp_mismatch.txt
- dangling_p900x:          74 cases → dangling_prefixes.txt
- prep_noun_compound:     134 cases → compound_prep_plus_noun.txt
- dangling_brace_prep:     12 cases → uncertain_or_expandable_issues.txt
- dangling_object_marker:  19 cases → uncertain_or_expandable_issues.txt
- compatible_but_notable:   0 cases → (none logged)
```

### 這表示什麼？

**正面解讀** ✅：
- 解析器的規範覆蓋率**非常好**
- 所有遇到的情況都有明確分類
- 沒有「未知類型」的 warnings

**潛在考量** 🤔：
- 可能存在**未被檢測到**的邊界案例
- 規範可能還有**未被觸發**的邊界情況
- 需要更大的語料庫（如整本舊約）來發現

---

## 未來可能的案例 (Potential Future Cases)

雖然當前沒有實際案例，但以下是**理論上可能**記錄到此日誌的情況：

### 潛在案例 1：超長前綴鏈

**場景**：
```
<09001><09002><09009><09003><04480><05921>...
```

**分析**：
- 五個或更多連續前綴/介系詞
- 規範未明確說明「超長鏈」的處理
- 解析器可能成功處理，但值得記錄

**可能的 Warning**：
```
[timestamp] Book C:V | excessive_prefix_chain |
Five consecutive prefix/prep tokens detected - all attached
per stacking rule - unusual construction may warrant review
```

---

### 潛在案例 2：Brace Prep 與隱式 Token 交互

**場景**：
```
...{<05921>}{<04480>}連續兩個 brace prepositions...
```

**分析**：
- 規範說明 brace prep 的附著規則
- 但未明確說明「連續 brace preps」的情況
- 可能兩者都右附著到同一名詞？

**可能的 Warning**：
```
[timestamp] Book C:V | consecutive_brace_preps |
Two brace prepositions {<05921>}{<04480>} in sequence - both
right-attached to noun per general rule - spec clarification recommended
```

---

### 潛在案例 3：形態碼與前綴的異常組合

**場景**：
```
<09001>(**8804)<01234>...
```

**分析**：
- 形態碼 (**8804) 出現在 900x 前綴和核心 token 之間
- 規範說明「900x 跳過 {<...>} 和 {8xxx}」
- 但未明確說明**顯式** (**8xxx) 的處理

**可能的 Warning**：
```
[timestamp] Book C:V | morphology_between_prefix_and_core |
Morphology code (**8804) found between 900x prefix and core token -
prefix skipped over morph code per inferred rule
```

---

### 潛在案例 4：受詞標記的特殊位置

**場景**：
```
{<0853>}在句首，後面沒有明顯的名詞...
```

**分析**：
- `{<0853>}` 通常右附著到名詞
- 但若出現在句首或其他特殊位置
- 可能需要依賴語意上下文

**可能的 Warning**：
```
[timestamp] Book C:V | object_marker_unusual_position |
Object marker {<0853>} in sentence-initial position - attachment
followed general rule but semantic context may affect interpretation
```

---

## 使用指南 (Usage Guidelines)

### 何時應該產生 compatible_but_notable warning？

**開發者指南**（在擴展解析器時）：

**應該記錄** ✅：
- 規範有一般規則，但案例有特殊性
- 多種解釋都合理，選擇了其中一種
- 符合規範，但統計上罕見
- 推斷應用規則（規範未明確涵蓋）

**不應記錄** ❌：
- 完全符合規範且無特殊性 → 正常處理
- 解析失敗或無法確定 → uncertain log
- 已知的數據問題 → 對應的專用日誌
- 刻意的設計選擇 → compound_prep_plus_noun log

**判斷標準**：
```
問自己：「這個案例值得人工審查嗎？」
- 是，且解析成功 → compatible_but_notable
- 是，且解析不確定 → uncertain
- 否 → 不記錄
```

---

### 如何審查此日誌？

**質量保證流程**：

**1. 定期審查**（每處理 5-10 卷書）
```bash
# 檢查日誌內容
cat output/compatible_but_notable_issues.txt

# 統計 warning 類型
grep -o " | [a-z_]* | " output/compatible_but_notable_issues.txt | \
    sort | uniq -c | sort -rn
```

**2. 模式識別**
- 找出高頻的 warning 類型
- 判斷是否需要規範明確化
- 考慮是否應該創建新的專用日誌

**3. 規範改進**
- 將常見模式加入規範
- 提供明確的處理規則
- 減少未來的「notable」案例

**4. 文檔化**
- 將特殊案例加入測試集
- 在規範中添加案例研究
- 更新 CLAUDE.md 說明

---

## 設計哲學 (Design Philosophy)

### 「寧可多記錄，不可漏記錄」原則

**核心理念**：

**1. 透明度優先**
- 所有異常情況都應該被記錄
- 即使可能是「誤報」（false positive）
- 事後可以判斷是否值得關注

**2. 質量追蹤**
- 長期追蹤有助於發現系統性模式
- 即使單一案例不重要，累積數據可能揭示問題

**3. 未來擴展性**
- 今天看似正常的案例，明天可能需要特殊處理
- 記錄在案便於回溯分析

**4. 使用者信心**
- 完整的日誌系統展現解析器的嚴謹性
- 使用者知道「沒有被忽視的異常」

---

### 分層記錄策略

**五層日誌的設計理由**：

**層級 1-2（數據問題）**：
- qb_qp_mismatch, dangling_prefixes
- 這些不是解析器的錯
- 需要 FHL 或數據改進

**層級 3（解析不確定）**：
- uncertain_or_expandable_issues
- 解析器無法確定正確答案
- 需要規範擴展或人工判斷

**層級 4（邊界案例）**：⭐
- compatible_but_notable_issues
- 解析器成功，但值得關注
- 質量保證和規範改進線索

**層級 5（設計選擇）**：
- compound_prep_plus_noun
- 完全符合預期的刻意決策
- 透明記錄設計選擇

---

## 與規範版本的關係 (Relation to Spec Versions)

### v1.8 的日誌系統演進

**v1.0-v1.6**：
- 單一日誌或無日誌
- 所有問題混在一起

**v1.7**：
- 引入三層日誌系統
- qb_qp_mismatch 分離
- uncertain vs notable 初步分離

**v1.8**：
- 四層日誌系統
- 新增 compound_prep_plus_noun 專用日誌

**v1.8.1**：
- **五層日誌系統** ✅
- 新增 dangling_prefixes 專用日誌
- compatible_but_notable 定位更清晰

---

### 未來版本考量 (v2.0+)

**可能的擴展**：

**1. 子分類**
- compatible_but_notable 可能需要進一步細分
- 例如：
  - `rare_constructions.txt`
  - `spec_boundary_cases.txt`
  - `context_dependent_parses.txt`

**2. 嚴重性分級**
- 在日誌中添加嚴重性欄位
- `[timestamp] verse | warning_type | SEVERITY | message`
- 方便優先級排序

**3. 自動化審查**
- 開發腳本自動分析 notable log
- 識別高頻模式
- 生成規範改進建議

**4. 統計儀表板**
- 視覺化各類日誌的分佈
- 追蹤版本間的改進
- 展示解析器質量趨勢

---

## 結論與建議 (Conclusion & Recommendations)

### 當前狀態評估 ✅

**compatible_but_notable_issues.txt 的設計是必要的**，原因：

**1. 完整的質量追蹤**
- 填補了「成功但特殊」案例的記錄空白
- 確保沒有異常情況被忽視

**2. 規範改進線索**
- 識別需要明確化的規範邊界
- 發現未來版本的改進方向

**3. 合理的嚴重性分級**
- 不誇大問題（不標記為 uncertain）
- 不忽視特殊性（仍然記錄）

**4. 可擴展的架構**
- 為未來的日誌細分留有空間
- 支援長期質量追蹤

---

### 建議行動 ✅

**立即行動**：

1. **保持當前日誌結構**
   - ✅ 五層日誌系統設計合理
   - ✅ 繼續使用 "everything else" 策略

2. **文檔完善**
   - ✅ 本文檔 `compatible_but_notable_issues_analysis.md` 已創建
   - ✅ 在 SPECIFICATION 中說明分類邏輯
   - ✅ 在 CLAUDE.md 中添加審查指南

3. **監控日誌生成**
   - 繼續處理更多經卷（利未記、民數記、申命記等）
   - 觀察是否有案例進入 compatible_but_notable log
   - 分析實際案例模式

**中期考量**：

4. **擴展測試集**
   - 處理整本舊約（39 卷書）
   - 處理新約（27 卷書）
   - 收集足夠大的語料庫

5. **模式分析**
   - 若 compatible_but_notable 案例累積到 50+ 個
   - 進行模式分析，考慮是否需要子分類

6. **規範細化**
   - 將常見的「notable」案例加入規範
   - 提供明確的處理規則
   - 減少未來的邊界模糊

**長期規劃 (v2.0+)**：

7. **日誌系統重構**
   - 考慮引入嚴重性分級
   - 考慮引入子分類
   - 考慮引入統計儀表板

8. **自動化質量保證**
   - 開發自動審查工具
   - 生成質量報告
   - 追蹤解析器改進趨勢

---

## 技術細節：日誌格式 (Log Format)

### 標準格式

```
[timestamp] verse_ref | warning_type | description
```

### 欄位說明

**[timestamp]**：
- 格式：`[YYYY-MM-DD HH:MM:SS]`
- 例如：`[2025-11-25 14:30:45]`

**verse_ref**：
- 格式：`Book Chapter:Verse`
- 例如：`Gen 3:14`, `Exod 20:17`

**warning_type**：
- 描述性的警告類型名稱
- 例如：`multiple_valid_attachments`, `rare_construction`, `spec_boundary_case`

**description**：
- 詳細描述異常情況
- 說明解析器的處理方式
- 建議（如果有）

### 範例（假設）

```
[2025-11-25 14:30:45] Gen 50:26 | rare_construction |
Triple consecutive brace prepositions {<05921>}{<04480>}{<0413>}
detected - all right-attached to following noun per general rule -
statistically rare pattern (1 in 1,533 verses)

[2025-11-25 15:12:33] Exod 40:38 | spec_boundary_case |
Morphology code (**8804) appeared between 900x prefix <09001> and
core token <01234> - prefix skipped over morph per inferred rule -
spec does not explicitly cover this sequence

[2025-11-25 16:45:20] Lev 12:8 | multiple_valid_attachments |
Brace preposition {<04480>} could attach to preceding verb or
following noun - chose noun per general right-attach rule -
context suggests verb attachment might be more appropriate
```

---

## 相關文檔 (Related Documentation)

- **SPECIFICATION_v1.8.md** - 完整解析規範
- **qb_qp_mismatch_analysis.md** - 數據不匹配分析
- **dangling_prefixes.md** - 懸空前綴分析
- **compound_prep_plus_noun_analysis.md** - Prep+noun 複合結構分析
- **CLAUDE.md** - 專案總體說明
- **Batch_Parsing_SOP.md** - 批次解析標準作業程序
- **parse_verse_v1_8.py** - 當前解析器實作

---

## 版本歷史 (Version History)

- **v1.7** (2024) - 初步引入分層日誌系統
  - 分離 qb_qp_mismatch
  - 區分 uncertain vs notable

- **v1.8** (2025-11) - 擴展為四層日誌
  - 新增 compound_prep_plus_noun 專用日誌
  - 細化 notable 的定位

- **v1.8.1** (2025-11-25) - 優化為五層日誌 ✅
  - 新增 dangling_prefixes 專用日誌
  - 本分析文檔創建
  - 明確 compatible_but_notable 的設計理念和使用場景

---

## 總結 (Summary)

**compatible_but_notable_issues.txt** 日誌檔案代表了解析器設計的**質量保證哲學**：

**1. 完整性**
- 所有異常情況都應該被追蹤
- 即使是「成功解析但有特殊性」的案例

**2. 透明性**
- 使用者和開發者都能看到完整的解析過程
- 沒有「被忽視的異常」

**3. 可改進性**
- 長期追蹤有助於識別規範改進機會
- 邊界案例是規範細化的寶貴資源

**4. 嚴謹性**
- 合理的嚴重性分級
- 不誇大問題，也不忽視特殊性

雖然當前在 Genesis + Exodus 中沒有實際案例，但這個日誌檔案的存在本身就體現了解析器設計的**前瞻性和嚴謹性**。隨著更多經卷的處理，它將成為質量保證和規範改進的重要工具。

---

**版本**: v1.8.1 分析文檔
**創建日期**: 2025-11-25
**分析範圍**: Genesis (1,533 verses) + Exodus (1,213 verses)
**當前狀態**: 0 個實際案例（日誌檔案架構已就緒，等待實際觸發）
