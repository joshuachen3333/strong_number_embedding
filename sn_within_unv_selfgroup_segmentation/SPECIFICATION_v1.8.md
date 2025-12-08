# UNV+SN 分組規格 v1.8（完整獨立版）

> 本規格定義由含 Strong 編號、形態碼、隱性語素與 900x 擴展碼的 UNV 經文（FHL `qb.php`）出發，轉為穩定、可機器處理的語義分組。v1.8 整合所有前版內容，並新增**通用複合詞檢測機制**，支持 מִן (04480) 和 לִפְנֵי (09001+06440) 等多種複合介系詞，直接從 qp.php 的 `wform` 和 `remark` 字段提取複合信息，無需維護獨立字典。

**狀態**：📝 規格定義完成（2025-11-25）

**v1.8 新增**：通用複合詞檢測，支持所有 900x 前綴組合（如 `<09001><06440>` = לִפְנֵי "before"）和跨 900x 的多 token 複合詞（如 `<04480><09001><06440>` = מִלִּפְנֵי "from before"）

---

## 1.0 摘要（Summary）

本規格完整定義 UNV+SN 解析的所有規則，包括：

### 1.1 核心功能（來自 v1.6）

* **WTH/WH 形態碼**的正規化（`<WTH8804>` ⇒ `(**8804)`）
* **brace 介詞**的決策順序（動詞左附例外優先，否則右附名詞）
* **900x** 附著時需**越過**大括號 token
* **ignored_codes** 的處理時機
* `parsing_wform` 僅作**補註**、不改原 `morph` 值
* FHL Profile 的 900x 對映、推斷分流與顯示順序
* 自動問題日誌記錄系統

### 1.2 v1.7 新增功能

* **從 qp.php 自動檢測**：直接解析 `wform` 字段中的複合介系詞信息
* **自動合併**：當檢測到 `<04480>` + 另一個 Strong's number 且 qp.php 的 `wform` 包含「介系詞 מִן +」時自動合併
* **新的輸出格式**：複合詞顯示為 `<04480><05921> — 複合介系詞 מֵעַל「...」`，並添加結構註記
* **減少誤報**：解決 94% 的 `qb_qp_mismatch` 錯誤（~1,097 個案例）
* **零維護成本**：不需要獨立字典文件，完全依賴權威數據源 qp.php
* **prep+noun 複合詞日誌**：新增 `compound_prep_plus_noun.txt` 專門記錄介系詞+名詞複合詞案例

### 1.2.1 v1.7.2 增強功能

* **多 token 複合詞支持**：檢測跨越 900x 前綴的複合介系詞（如 `<04480><09001><06440>` = מִלִּפְנֵי）
* **自動跳過 900x**：在檢測複合詞時自動越過中間的 900x 前綴，直達核心 token
* **複雜複合詞記錄**：支持 prep + 900x + prep/noun 組合的檢測與記錄
* **智能 mismatch 過濾**：增強的警告系統避免將多 token 複合詞誤報為 qb_qp_mismatch
* **範例案例**：Gen 4:16 `<04480><09001><06440>` (מִן + לְ + פָּנֶה) 正確識別為複合詞

### 1.2.2 v1.8 通用複合詞檢測

* **通用檢測機制**：不再限於 מִן (04480)，支持檢測所有複合介系詞
* **900x 起始複合詞**：檢測 `<900x><core>` 型態的複合詞（如 `<09001><06440>` = לִפְנֵי）
* **remark 字段支持**：除 wform 外，也檢查 qp.php 的 remark 字段尋找複合信息
* **自動 SN 對應**：當 qb.php 和 qp.php 使用不同 SN 時，自動使用 qp.php 的 SN
* **範例案例**：
  - Gen 6:11 `<09001><06440>` = לִפְנֵי "before" (qp.php SN: 03942)
  - Gen 4:16 `<04480><09001><06440>` = מִלִּפְנֵי "from before" (qp.php SN: 03942)
* **影響範圍**：解決額外的 qb_qp_mismatch 案例（涉及 לִפְנֵי 及類似複合詞）

### 1.3 兼容性

* 完全獨立，不依賴其他規格文檔
* 複合介系詞合併可通過配置開關控制
* 可向後兼容 v1.6 行為

---

## 2.0 標記系統全解析（Token System）

### 2.1 原始資料層（Raw Data Layer）

* **內部前綴**：`WH`, `WTH`, `WAH` 等僅為資料源元數據
* **規範**：在 **3.1 標記正規化** 中處理；解析流程不直接依賴

### 2.2 解析器內部 Token 類別

* **核心詞（Core）**：Strong 編號（1–8999 等）。出現於 `<dddd>` 或 `{<dddd>}`（隱性）
* **形態碼（Morph）**：8xxx 系列（如 8804、8738、8764、8799…）。顯性 `(**8xxx)`、隱性 `{8xxx}`
* **900x 擴展碼（Prefix）**：9xxx 系列（如 09001、09002、09009…），表示不可分詞綴（ו־、ל־、ה־…）

### 2.3 職責劃分與重疊

* **數字範圍**：
  - `8xxx`（4位數，8000-8999）⇒ **morph**
  - `09xxx`（5位數，09000-09999）⇒ **900x prefix**
  - 其餘（1-7999, 9000-8999 但非 09xxx 格式）⇒ **core**
  - **重要**：4位數如 `0914` 不是 900x（長度必須為5且以09開頭）
* **括號用途**：`<...>` ⇒ core/900x；`{<...>}` ⇒ 隱性 core；`(...)`/`{...}` ⇒ morph（8xxx）
* **不相關**：`WH/WTH/WAH` 等內部前綴與解析邏輯無關（僅正規化時處理）

---

## 3.0 核心解析規則與流程

### 3.1 標記正規化（必做）

1. 移除 `WH/WTH/WAH` 等**非數字**標籤
2. **形態碼轉寫**：將 `<WTH(8ddd)>`/`<WH(8ddd)>` 等 **8xxx** 形態碼轉為 `(**8ddd)`（顯性 morph）
3. **保留** `<09ddd>` 為 900x；其他 `<dddd>`（非 8/9xxx）為 core
4. `{<dddd>}` 視為**隱性 core**；`{8xxx}`（無 `<`）視為**隱性 morph**
5. 忽略中文標點／空白，不進入 token 序列

### 3.2 Token 正則（參考實作）

* **Strong（core）**：`/<dddd>/`
* **900x（prefix）**：`/<09ddd>/`
* **隱性核心**：`/\{<dddd>\}/`
* **顯性形態碼**：`/(8[6-9]dd)/`
* **隱性形態碼**：`/\{(8[6-9]dd)\}/`（先判斷 token 不是 `{<...>}` 再比對）

### 3.3 複合介系詞檢測與合併（v1.7 新增） <!-- spec:compound -->

**在分組前執行**，檢測並合併複合介系詞：

#### 3.3.1 檢測算法（v1.8 通用版本：支持所有複合詞） <!-- spec:prefix -->

```python
def detect_generic_compound_from_qp(tokens, current_index, qp_data, config):
    """
    v1.8: 通用複合詞檢測，支持所有類型的複合介系詞
    - מִן (04480) 開頭的複合詞（v1.7 原有）
    - 900x 開頭的複合詞（v1.8 新增，如 לִפְנֵי）
    - 跨越 900x 前綴的多 token 複合詞（v1.7.2 原有）
    直接從 qp.php 的 wform 和 remark 字段提取信息
    無需維護獨立字典
    """
    current_token = tokens[current_index]
    current_sn = current_token.strong_number

    # 收集從 current_index 開始的連續 tokens（包括 900x）
    j = current_index + 1
    collected_tokens = [current_token]

    # 收集後續的 900x 和第一個 core token
    while j < len(tokens):
        if tokens[j].is_900x():
            collected_tokens.append(tokens[j])
            j += 1
        elif tokens[j].is_core():
            collected_tokens.append(tokens[j])
            j += 1
            break  # 只收集到第一個 core token
        else:
            break  # 遇到其他類型（morph, brace等）停止

    if len(collected_tokens) < 2:
        # 至少需要 2 個 tokens 才能構成複合詞
        return None

    # v1.8: 在 qp.php 中搜索匹配的複合詞記錄
    # 策略 1: 嘗試用最後一個 core token 的 SN 查找
    last_core_sn = collected_tokens[-1].strong_number if collected_tokens[-1].is_core() else None

    qp_record = None
    for record in qp_data:
        if 'sn' not in record:
            continue

        wform = record.get('wform', '')
        remark = record.get('remark', '')

        # v1.8: 檢查多種複合詞模式
        compound_indicators = [
            '介系詞 מִן +',           # מִן 複合詞
            '從介系詞 לְ + 名詞',      # לִפְנֵי 類型（從 remark）
            '從介系詞 מִן +',         # 另一種 מִן 表達（從 remark）
            '+ 名詞',                 # 通用 prep+noun 模式（從 remark）
        ]

        # 檢查是否匹配複合詞模式
        has_compound_indicator = any(ind in (wform + remark) for ind in compound_indicators)

        if has_compound_indicator:
            # 找到複合詞記錄
            qp_record = record
            break

    if not qp_record:
        # 策略 2: 如果找不到，搜索所有記錄看是否有提到相關 SN
        # （處理 qb/qp SN 不一致情況）
        for record in qp_data:
            remark = record.get('remark', '')
            wform = record.get('wform', '')

            # 檢查 remark 是否提到任何 collected token 的 SN
            mentions_token = any(
                f"SN {token.strong_number.lstrip('0')}" in remark or
                f"SN {int(token.strong_number)}" in remark
                for token in collected_tokens if token.is_core()
            )

            compound_in_text = any(ind in (wform + remark) for ind in [
                '介系詞', '+ 名詞', '從介系詞'
            ])

            if mentions_token and compound_in_text:
                qp_record = record
                break

    if not qp_record:
        return None

    # 判斷複合詞類型
    wform = qp_record.get('wform', '')
    remark = qp_record.get('remark', '')
    combined_text = wform + ' ' + remark

    if '介系詞 מִן +' in combined_text and '介系詞' in combined_text:
        compound_type = 'prep_plus_prep'
    elif '介系詞' in combined_text and '名詞' in combined_text:
        compound_type = 'prep_plus_noun'
    else:
        compound_type = 'generic_compound'

    # 返回複合詞信息
    return {
        'type': compound_type,
        'involved_tokens': collected_tokens,
        'end_index': j - 1,  # 最後一個包含的 token 索引
        'structure': wform,
        'remark': remark,
        'qp_sn': qp_record.get('sn'),
        'hebrew': qp_record.get('word', ''),
        'meaning': qp_record.get('exp', ''),
        'is_compound': True,
        'should_merge': compound_type == 'prep_plus_prep' or
                       (compound_type == 'prep_plus_noun' and config.get('merge_prep_plus_noun', False))
    }
```

#### 3.3.2 合併規則（v1.8 通用版本） <!-- spec:morph -->

**觸發條件（v1.8 擴展）**：
1. 當前 token 為任何可能的複合詞起始token:
   - `<04480>` (מִן) - v1.7 原有
   - `<900x>` (任何 900x 前綴) - v1.8 新增
2. v1.7.2/v1.8: 跳過任何中間的 900x 前綴
3. qp.php 記錄的 `wform` 或 `remark` 包含複合詞指標
4. tokens 之間沒有標點或非 900x 插入內容

**合併動作（prep+prep）**：
1. 創建新的複合組 `G_compound`
2. v1.8: `G_compound.core` 包含所有相關 tokens 的 SNs
3. v1.8: 使用 qp.php 的 SN（當 qb/qp 不一致時）
4. `G_compound.type = "compound_preposition"`
5. `G_compound.structure = wform`（從 qp.php 提取）
6. `G_compound.hebrew` = qp.php 的 `word`
7. 移除原始的所有相關 tokens
8. **不生成** `qb_qp_mismatch` 警告

**prep+noun 處理**：
- 檢測到但**不合併**（根據 `merge_prep_plus_noun: False` 配置）
- v1.8: 記錄所有相關 tokens 到 `output/compound_prep_plus_noun.txt`
- **不記錄**到 `uncertain_or_expandable_issues.txt`（避免重複）
- 這些是 FHL 數據編碼特性，非解析錯誤

**v1.8 範例**：
- מִן 複合（簡單）: `<04480><05921>` → מֵעַל (2 tokens)
- מִן 複合（複雜）: `<04480><09001><06440>` → מִלִּפְנֵי (3 tokens, 含 900x)
- לִפְנֵי 複合: `<09001><06440>` → לִפְנֵי (2 tokens, qp.php SN: 03942)

#### 3.3.3 輸出格式

**選項 B：連寫法**（當前實作）
```
<04480><05921> — 複合介系詞 מֵעַל「從…之上」
[註]: 介系詞 מִן + 介系詞 עַל
```

### 3.4 分組與合併（Grouping & Merging） <!-- spec:grouping -->

**掃描方向**：自左往右；**忽略**標點／空白。

1. **前綴緩衝（prefix_buffer）**
   遇到 900x 先入 `prefix_buffer`；附著時需**越過** `{<...>}` 與 `{8xxx}`，直到下一個 core。

2. **建立核心組**
   遇到 core（顯性或隱性）建立新 group `G`；將 `prefix_buffer` 全部掛到 `G.prefixes[]`，然後清空緩衝。

3. **形態附著**
   遇到 morph（顯/隱）一律**左附**最近一個核心組：`G.morph += code`。

4. **brace 介詞決策樹（v1.2-A 強化版）**
   遇 `{<PREP>}` 時：

   * **特例 1（最高優先）** <!-- spec:brace_left -->：若 `qp.wform` 顯示「介系詞 + 代名詞後綴」（如 מִמֶּנּוּ）或位於動詞不定詞補語語境（如 `<0398>(8800){<04480>}`），則**左附**前一動詞：`G_verb.post_brace += PREP`。
     - **檢測方法**：在 qp.php 的 wform 字段中查找「詞尾」關鍵字，如「介系詞 מִן + 3 單陽詞尾」
     - **常見模式**：`/介系詞.*詞尾/` 或 `/介系詞.*\d [單複][陽陰]詞尾/`

   * **特例 2** <!-- spec:object_marker -->：`{<0853>}`（受詞記號 אֵת）**總是右附**到後方名詞：`G_noun.pre_brace += 0853`。

   * **一般** <!-- spec:brace_right -->：若右側就近（可跨 900x）為**名詞**，則**右附**：`G_noun.pre_brace += PREP`；否則**獨立保留**並標 `warning:"brace_attach_ambiguous"`。

5. **Construct Linker（可選 v1.2-B）**
   若 `qp.wform` 指示名詞為附屬形（construct），將其與右側下一個名詞以 `construct_of: <NNNN>` 連結（可跨 `pre_brace` 與 900x）。僅標註鏈接，不改分組。

6. **資料不一致處理**
   以 `qb.php` 結構為主，`qp.php` 僅作補註。偵測到差異（如 `qb_qp_core_mismatch`）時，在輸出加入 `warnings[]`，並（可選）寫入日誌。

---

## 4.0 複合介系詞問題背景（v1.7 專題）

### 4.1 問題描述

**FHL 數據源的標註差異**：

| 數據源 | 標註方式 | 範例（מֵעַל "from above"） |
|--------|----------|---------------------------|
| **qb.php** (UNV+SN) | 分析式（拆開） | `<04480><05921>` |
| **qp.php** (希伯來文) | 整體式（合併） | `sn: 05921`, `wform: "介系詞 מִן + 介系詞 עַל"` |

**結果**：
- `<04480>` 在 qb.php 中出現，但在 qp.php 中找不到
- v1.6 會產生 `qb_qp_mismatch` 錯誤
- 用戶看到「未知詞性、未知意義」

### 4.2 影響規模

從已解析的創世記、出埃及記、利未記數據分析：
- **總 qb_qp_mismatch 錯誤**：1,162 個
- **מִן (04480) 相關**：1,097 個（94%）
- **核心複合介系詞類型**：8-10 個高頻組合

### 4.3 v1.7 解決方案

- **零字典維護**：直接從 qp.php 的 `wform` 提取複合信息
- **自動檢測**：掃描「介系詞 מִן +」模式
- **智能合併**：prep+prep 自動合併；prep+noun 記錄但不合併
- **專用日誌**：`compound_prep_plus_noun.txt` 記錄 prep+noun 案例，避免污染 uncertain 日誌

---

## 5.0 配置（Profile）與輸出

### 5.1 可配置表與開關

```yaml
# v1.6 原有配置
brace_preps: ["05921","04480","0413","00996"]   # עַל, מִן, אֶל, בֵּין …
object_marker: "0853"                                  # 受詞記號 אֵת
prefix_map_900x:
  "09001": "ל־"
  "09002": "ב־"
  "09003": "כ־"
  "09006": "מ־"
  "09009": "ה־"     # 定冠
aliases:
  "09005": "09001"  # 異名同義
ignored_codes: ["09015"] # 段落符號等；token 化後、分組前即過濾
use_construct_linker: false   # 可按需開啟
use_parsing_inference: true   # 只補註，不改分組/不動 prefixes
prefix_display_order: ["ו־","ל־","ב־","כ־","מ־","ה־"]

# v1.7 新增配置
detect_compounds_from_qp: true      # 從 qp.php 自動檢測複合介系詞
merge_prep_plus_prep: true          # 合併 prep+prep 複合詞
merge_prep_plus_noun: false         # 不合併 prep+noun（僅記錄）
compound_output_format: "consecutive"  # "consecutive" | "compound_notation" | "separated"
log_compound_prep_noun: true        # 記錄到 compound_prep_plus_noun.txt
```

**推斷分流原則**：

* `prefixes[]`：僅收錄 `qb.php` 明示 900x
* `inferred_prefixes[]`：僅收錄自 `qp.wform` 推斷的前綴（如 `ו־`、`ה־`）
* 嚴禁將推斷結果混入 `prefixes[]`；可用 `inferred: true` 標示來源

### 5.2 輸出資料結構（欄位約定）

#### 5.2.1 標準分組（v1.6）

* `core: string`（Strong，含前導 0）
* `implicit: boolean`（是否 `{<...>}`）
* `prefixes: string[]`（來自 `qb` 的 900x）
* `morph: string[]`（8xxx；順序即掃描順序）
* `pre_brace: string[]`（右附的 `{<...>}`；含 0853 與 brace_preps）
* `post_brace: string[]`（左附到動詞的不定詞/介詞）
* `inferred_prefixes: string[]`（`qp` 推斷）
* `inferred: boolean`（任一推斷屬性為 true 時）
* `construct_of: string | null`（可選）
* `parsing_wform: string | null`（可選；僅補註，不改 `morph`）
* `warnings: string[]`（如 `brace_attach_ambiguous`, `dangling_900x`, `morph_without_core`, `qb_qp_core_mismatch`）

#### 5.2.2 複合介系詞分組（v1.7）

```json
{
  "core": ["04480", "05921"],
  "compound_key": "04480+05921",
  "type": "compound_preposition",
  "hebrew": "מֵעַל",
  "meaning_zh": "從…之上",
  "structure": "介系詞 מִן + 介系詞 עַל",
  "implicit": false,
  "prefixes": [],
  "morph": [],
  "warnings": []
}
```

---

## 6.0 進階規則與建議

### 6.1 Parsing 輔助（可選）

* **推斷前綴**：若 `use_parsing_inference: true`，自 `qp.wform` 抽取未於 `qb` 明示的前綴，寫入 `inferred_prefixes`（如 `ו־`、`ה־`）
* **morph 細節補註**：對 `8799` 等粗顆粒碼，將 `qp.wform`（如「Qal 敘述式 3ms」「Qal 祈願式 3ms」）寫入 `parsing_wform`；**不更動** `morph` 值

### 6.2 偵錯與邊界

* **一般警告**：`brace_attach_ambiguous`、`dangling_900x`、`morph_without_core`
* **資料不一致**：`qb_qp_core_mismatch` 必須出現在 `warnings[]`，並（可選）記 log
* **範圍驗證**：可選地驗證 Strong 號段（如舊約 ≤ 8999）

### 6.3 問題日誌記錄系統

實作應自動記錄問題至三個日誌文件（位於 `output/` 目錄）：

#### 6.3.1 uncertain_or_expandable_issues.txt

* 無法確定解決的問題（需擴充規範或人工審查）
* 記錄類型：
  - `qb_qp_mismatch`（**排除** prep+noun 複合詞案例）
  - `brace_attach_ambiguous`
  - `dangling_*` 系列
* **重要（v1.7.1 修正）**：已檢測為 prep+noun 複合詞的 `<04480>` token **不記錄**到此日誌

#### 6.3.2 compatible_but_notable_issues.txt

* 符合規範但值得特別注意的案例
* 邊界情況、不尋常的語法結構、多重有效詮釋
* 有助識別模式，用於品質保證與未來規範改進

#### 6.3.3 compound_prep_plus_noun.txt（v1.7 新增）

* **專門記錄** prep+noun 複合詞案例
* 當檢測到 `<04480>` + 名詞且 qp.php wform 顯示「介系詞 מִן +」時記錄
* 這些**不是解析錯誤**，而是 FHL 數據編碼特性
* 根據 `merge_prep_plus_noun: false` 配置，這些詞保持分離但被記錄
* 範例：`<04480><03605>` = מִכָּל "from all" (מִן + כֹּל)

**日誌格式**：`[timestamp] verse_ref | issue_type | description`

**範例條目**：
```
[2025-11-24 14:30:15] Gen 1:2 | qb_qp_mismatch | Strong's number <0430> from qb.php not found in qp.php records.
[2025-11-24 23:40:07] Gen 2:2 | prep_noun_compound | Prep+noun compound detected: <04480><03605> = מִכָּל (介系詞 מִן + 名詞，單陽附屬形) - not merged per config
```

**v1.7.1 重要修正（2025-11-24）**：
- prep+noun 複合詞案例只記錄到 `compound_prep_plus_noun.txt`
- 不再重複記錄到 `uncertain_or_expandable_issues.txt`
- 避免將正常的 FHL 編碼特性誤報為解析問題

此功能協助：
* 追蹤批次解析中的模式
* 識別需要規範擴充的領域
* 為 AI/LLM 整合提供訓練資料
* 與神學學術交叉參照

---

## 7.0 範例（可讀版分群）

> 僅示意規則生效方式；實作輸出請依 5.2 欄位。以下示例均來自已驗證節：

### 7.1 創 3:5（動詞左附例外 - 特例 1）

* `… <0398>(8800){<04480>} …` ⇒ `{<04480>}` 命中「介詞 + 代名詞後綴 / 不定詞補語」語境 → **左附動詞**（`post_brace += 04480`），而非右附後方名詞
* qp.php wform: "介系詞 מִן + 3 單陽詞尾"（מִמֶּנּוּ）

### 7.2 創 1:2（brace 介詞右附名詞 + construct）

* `… 淵面 {<05921>} <06440> …` ⇒ `{<05921>}` **右附**到名詞 `<06440>`（面）
* `06440`（פְּנֵי，附屬形）→ `construct_of` 指到右側名詞：一次連到 `<08415>`（淵），另一次連到 `<04325>`（水）

### 7.3 創 1:4（受詞記號與「在…之間」）

* `{<0853>}<0216>`：受詞記號 **總是右附**名詞
* `{<00996>}<0216>`、`{<00996>}<02822>`：**右附**到名詞（光／暗）

### 7.4 創 1:5（FHL Profile 與推斷分流）

* `qb` 給 `<09001><0216>`（**ל־** + 光）；`qp` 顯示 `וְ`/`הַ` 時，僅加在 `inferred_prefixes`（不進 `prefixes`）

### 7.5 創 1:7（v1.7 複合介系詞）

**原始 qb.php 文本**：
```
將<WAH0834>空氣<WAH09001><WH07549>以下<WAH04480><WH08478>的水...
空氣<WAH09001><WH07549>{<WH0834>}以上<WAH04480><WH05921>的水...
```

**v1.6 輸出**（問題）：
```
<04480> — 未知詞性「未知意義」
<08478> — 介系詞 מִן + 介系詞 תַּחַת「1. 名詞：位置、地方；2. 介系詞：在…之下...」
...
<04480> — 未知詞性「未知意義」
<05921> — 介系詞 מִן + 介系詞 עַל「在…上面、在旁邊...」
```

**v1.7 輸出**（修正）：
```
<04480><08478> — 複合介系詞 מִתַּחַת「從…之下」
[註]: 介系詞 מִן + 介系詞 תַּחַת
...
<04480><05921> — 複合介系詞 מֵעַל「從…之上」
[註]: 介系詞 מִן + 介系詞 עַל
```

**其他測試案例**：
- **Gen 24:27**: `<04480><05973>` → מֵעִם "from with"
- **Gen 49:30**: `<04480><00854>` → מֵאֵת "from beside"
- **Exod 25:22**: `<04480><00996>` → מִבֵּין "from between"

### 7.6 創 3:3（特例 1 實例 - 代名詞後綴）

**問題**：`{<04480>}` 被誤報為 `dangling_brace_prep`

**qb.php**：`你們不可<WAH03808>吃<WH0398><WTH8799>{<WAH04480>}`

**qp.php wid 10**：
```json
{
  "word": "מִמֶּנּוּ",
  "sn": "04480",
  "wform": "介系詞 מִן + 3 單陽詞尾"
}
```

**正確處理（特例 1）**：
- 檢測到 wform 包含「詞尾」關鍵字
- `{<04480>}` 應**左附到動詞** <0398>
- 正確輸出：`<0398>(8799){<04480>} — 動詞「吃」+ 介系詞 מִמֶּנּוּ "from it"`

### 7.7 創 4:16（v1.7.2 多 token 複合詞）

**問題**：`<04480>` 被誤報為 `qb_qp_mismatch`

**qb.php**：`耶和華<WH03068>的面<WAH04480><WAH09001><WH06440>`
- Strong's: `<04480>` (מִן) + `<09001>` (לְ 900x prefix) + `<06440>` (פָּנֶה "face")

**qp.php wid 3**：
```json
{
  "word": "מִלִּפְנֵי",
  "sn": "03942",
  "wform": "介系詞 מִן + 介系詞 לִפְנֵי"
}
```

**v1.7.2 正確處理**：
- 檢測到 `<04480>` 後跳過 900x 前綴 `<09001>`
- 找到核心 token `<06440>`，其 qp.wform 顯示「介系詞 מִן +」
- 識別為 3-token 複合詞：`<04480><09001><06440>` = מִלִּפְנֵי "from before"
- 記錄到 `compound_prep_plus_noun.txt`（因含名詞 פָּנֶה）
- **不記錄**到 `uncertain_or_expandable_issues.txt`
- 輸出：`<04480><09001><06440> — 複合介系詞 מִלִּפְנֵי「從…之前」`
- 註記：介系詞 מִן + (介系詞 לְ + 名詞 פָּנֶה)

### 7.8 創 6:11（v1.8 通用複合詞 - לִפְנֵי）

**問題**：`<06440>` 被誤報為 `qb_qp_mismatch`

**qb.php**：`在　神<WH0430>面前<WAH09001><WH06440>敗壞`
- Strong's: `<09001>` (לְ 900x prefix) + `<06440>` (פָּנֶה "face")

**qp.php wid 3**：
```json
{
  "word": "לִפְנֵי",
  "sn": "03942",
  "wform": "介系詞",
  "remark": "לִפְנֵי 從介系詞 לְ + 名詞 פָּנֶה (臉, SN 6440) 的複陽附屬形而來。"
}
```

**v1.7.2 限制**：
- v1.7.2 只檢測 מִן (04480) 開頭的複合詞
- 無法處理 900x 開頭的複合詞
- qp.php 的 remark 字段包含複合信息，但 v1.7.2 未檢查

**v1.8 正確處理**：
- 檢測到 `<09001>` (900x) 後收集下一個 core token `<06440>`
- 在 qp.php 中搜索，找到 SN 03942 的記錄
- remark 字段顯示「從介系詞 לְ + 名詞 פָּנֶה (臉, SN 6440)」
- 識別為 2-token 複合詞：`<09001><06440>` → לִפְנֵי "before"
- 使用 qp.php 的 SN (03942) 而非 qb.php 的 (09001+06440)
- **不記錄**到 `uncertain_or_expandable_issues.txt`
- 輸出：`<09001><06440> — 複合介系詞 לִפְנֵי「在…之前」`
- 註記：介系詞 לְ + 名詞 פָּנֶה

**影響**：解決所有 לִפְנֵי 相關的 qb_qp_mismatch 案例

---

## 8.0 實作指南

### 8.1 解析流程概覽

```python
# 完整解析流程
def parse_verse(qb_text, qp_data):
    # 1. 標記正規化（§3.1）
    tokens = tokenize(qb_text)
    tokens = normalize_tokens(tokens)  # WTH8xxx -> (**8xxx)

    # 2. 過濾 ignored_codes（§5.1）
    tokens = filter_ignored(tokens, PROFILE['ignored_codes'])

    # 3. v1.8 通用複合詞檢測（§3.3）
    tokens = detect_and_merge_generic_compounds(tokens, qp_data, PROFILE)

    # 4. 分組與合併（§3.4）
    groups = []
    prefix_buffer = []

    for i, token in enumerate(tokens):
        if token.is_900x():
            prefix_buffer.append(token)
            continue

        if token.is_brace_prep():
            # 決策樹（§3.4 rule 4）
            handle_brace_prep(token, groups, qp_data)
            continue

        if token.is_core():
            G = create_group(token, prefix_buffer)
            groups.append(G)
            prefix_buffer = []
            continue

        if token.is_morph():
            attach_morph_to_last_group(token, groups)
            continue

    # 5. Construct linking（可選，§3.4 rule 5）
    if PROFILE['use_construct_linker']:
        link_constructs(groups, qp_data)

    # 6. 推斷補註（可選，§6.1）
    if PROFILE['use_parsing_inference']:
        add_inference(groups, qp_data)

    # 7. 驗證與警告（§6.2）
    validate_and_warn(groups, qb_text, qp_data)

    return groups
```

### 8.2 brace 介詞決策實作

```pseudo
def handle_brace_prep(token, groups, qp_data):
    prep_sn = token.strong_number

    # 特例 1: 檢查代名詞後綴（§3.4 rule 4）
    qp_record = find_qp_record(token, qp_data)
    if qp_record and has_pronoun_suffix(qp_record.wform):
        # 例如：wform = "介系詞 מִן + 3 單陽詞尾"
        last_verb = find_prev_verb(groups)
        if last_verb:
            last_verb.post_brace.append(prep_sn)
            return

    # 特例 1: 檢查不定詞補語語境
    if is_infinitive_complement_context(groups, token):
        last_verb = find_prev_verb(groups)
        if last_verb:
            last_verb.post_brace.append(prep_sn)
            return

    # 特例 2: 受詞記號（§3.4 rule 4）
    if prep_sn == "0853":
        next_noun = find_next_noun_skipping_900x(groups, token)
        if next_noun:
            next_noun.pre_brace.append(prep_sn)
            return

    # 一般情況（§3.4 rule 4）
    next_noun = find_next_noun_skipping_900x(groups, token)
    if next_noun:
        next_noun.pre_brace.append(prep_sn)
    else:
        # 獨立保留並警告
        create_standalone_group(token, warning="brace_attach_ambiguous")

def has_pronoun_suffix(wform):
    """檢測 qp.wform 是否包含代名詞後綴"""
    # 匹配模式如：
    # "介系詞 מִן + 3 單陽詞尾"
    # "介系詞 + 2 複陽詞尾"
    patterns = [
        r'介系詞.*詞尾',
        r'介系詞.*\d [單複][陽陰]詞尾'
    ]
    return any(re.search(p, wform) for p in patterns)
```

### 8.3 複合介系詞檢測實作

```python
def detect_and_merge_compounds(tokens, qp_data, profile):
    """
    v1.7.2 複合介系詞檢測與合併（支持多 token）
    直接從 qp.php wform 提取信息
    """
    if not profile.get('detect_compounds_from_qp', True):
        return tokens

    result = []
    i = 0

    while i < len(tokens):
        current = tokens[i]

        # 只檢測 <04480> (מִן)
        if current.strong_number != "04480":
            result.append(current)
            i += 1
            continue

        # v1.7.2: 跳過 900x 前綴，找到下一個 core token
        j = i + 1
        intervening_900x = []

        while j < len(tokens) and tokens[j].is_900x():
            intervening_900x.append(tokens[j])
            j += 1

        if j >= len(tokens):
            # 沒有找到下一個 core token
            result.append(current)
            i += 1
            continue

        next_core_token = tokens[j]
        next_qp = find_qp_record(next_core_token, qp_data)

        if not next_qp:
            result.append(current)
            i += 1
            continue

        wform = next_qp.get('wform', '')

        # 檢測 prep+prep 複合詞
        if '介系詞 מִן +' in wform and '介系詞' in wform:
            if profile.get('merge_prep_plus_prep', True):
                # v1.7.2: 合併所有相關 tokens（包括中間的 900x）
                involved_tokens = [current] + intervening_900x + [next_core_token]
                compound = create_compound_token_multi(
                    involved_tokens, wform, 'prep_plus_prep_complex' if intervening_900x else 'prep_plus_prep'
                )
                result.append(compound)
                i = j + 1  # 跳過所有已處理的 tokens
                continue

        # 檢測 prep+noun 複合詞
        if '介系詞 מִן +' in wform and '名詞' in wform:
            involved_tokens = [current] + intervening_900x + [next_core_token]

            if profile.get('log_compound_prep_noun', True):
                log_prep_noun_compound_multi(involved_tokens, wform)

            if profile.get('merge_prep_plus_noun', False):
                # 可選合併
                compound = create_compound_token_multi(
                    involved_tokens, wform, 'prep_plus_noun_complex' if intervening_900x else 'prep_plus_noun'
                )
                result.append(compound)
                i = j + 1
                continue
            else:
                # 不合併，保持分離但已記錄
                result.append(current)
                i += 1
                continue

        # 不是複合詞
        result.append(current)
        i += 1

    return result

def log_prep_noun_compound_multi(involved_tokens, wform):
    """
    v1.7.2: 記錄 prep+noun 複合詞到專用日誌（支持多 token）
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    verse_ref = get_current_verse_ref()

    # 構建 token 序列字符串
    token_seq = ''.join([f"<{t.strong_number}>" for t in involved_tokens])
    token_count = len(involved_tokens)
    compound_type = "prep_noun_compound" if token_count == 2 else "prep_noun_complex"

    log_entry = (
        f"[{timestamp}] {verse_ref} | {compound_type} | "
        f"Prep+noun compound detected ({token_count} tokens): {token_seq} = "
        f"{extract_hebrew(wform)} ({wform}) - not merged per config\n"
    )

    with open('output/compound_prep_plus_noun.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)
```

### 8.4 警告系統更新（v1.7.2 增強）

```python
def check_qb_qp_mismatch(strong_number, qp_data, compound_log, tokens, current_index):
    """
    v1.7.2: 檢查 qb/qp 不匹配，考慮複合詞情況（含多 token）
    """
    if strong_number not in qp_data:
        # v1.7.2: 檢查是否為多 token 複合詞序列的開頭
        if strong_number == "04480":
            # 查找下一個非 900x token
            j = current_index + 1
            while j < len(tokens) and tokens[j].is_900x():
                j += 1

            if j < len(tokens):
                next_core = tokens[j]
                next_qp = find_qp_record(next_core, qp_data)
                if next_qp and '介系詞 מִן +' in next_qp.get('wform', ''):
                    # 這是複合詞序列，已記錄到 compound 日誌
                    return None

        # v1.7: 檢查是否為已記錄的 prep+noun 複合詞
        if is_logged_prep_noun_compound(strong_number, compound_log):
            return None  # 不記錄到 uncertain 日誌（已在 compound 日誌中）

        # v1.7: 檢查是否為已合併的 prep+prep 複合詞
        if is_resolved_compound(strong_number):
            return None  # 不生成警告

        # v1.6 原有邏輯：生成 mismatch 警告
        return f"qb_qp_mismatch: <{strong_number}> not found in qp.php"

    return None
```

---

## 9.0 向後兼容與遷移

### 9.1 從 v1.6 遷移到 v1.7

**配置更新**：
```yaml
# 在現有 v1.6 配置中添加
detect_compounds_from_qp: true      # 啟用複合詞檢測
merge_prep_plus_prep: true          # 合併 prep+prep
merge_prep_plus_noun: false         # 不合併 prep+noun
log_compound_prep_noun: true        # 記錄 prep+noun
```

**代碼更新**：
```python
# 在 normalize 和 filter 之後添加
tokens = detect_and_merge_compounds(tokens, qp_data, PROFILE)
```

**日誌文件**：
- 新增 `output/compound_prep_plus_noun.txt`
- `uncertain_or_expandable_issues.txt` 中的 prep+noun 相關 mismatch 會減少

### 9.2 關閉 v1.7 功能（回退到 v1.6）

```yaml
detect_compounds_from_qp: false     # 關閉複合詞檢測
```

設置後，解析器行為完全回到 v1.6。

---

## 10.0 實作附注（Pseudo-code 完整版）

```pseudo
# 完整解析流程（包含 v1.7 新增步驟）
for token in tokens:
  # 900x 前綴處理
  if token is 900x:
     prefix_buffer.push(token)
     continue

  # brace 介詞決策樹
  if token is {<PREP>}:
     # 特例 1: 代名詞後綴或不定詞補語（§3.4 rule 4）
     if qp_says_pron_suffix(token) or is_infinitive_complement(token):
        attach_to_prev_verb(post_brace+=PREP)
     # 特例 2: 受詞記號
     elif PREP == "0853":
        attach_to_next_noun(pre_brace+="0853")
     # 一般情況
     elif next_core_is_noun_skipping_brace_and_900x():
        attach_to_next_noun(pre_brace+=PREP)
     else:
        keep_as_group_with_warning("brace_attach_ambiguous")
     continue

  # 核心詞處理
  if token is core (visible or hidden):
     G = new_group(core=token, implicit=hidden?)
     G.prefixes += drain(prefix_buffer)
     groups.append(G)
     continue

  # 形態碼處理
  if token is morph (visible or hidden):
     last_group.morph += code
     continue

# 在分組前已執行
filter_out(ignored_codes)  # §3.1 step 5
detect_and_merge_compounds()  # §3.3 (v1.7)
```

---

## 11.0 版本歷史與差異

### 11.1 v1.7.2 vs v1.7 變更（2025-11-25）

1. **多 token 複合詞支持**（§3.3.1, §8.3）
   - 檢測跨越 900x 前綴的複合介系詞
   - 自動跳過中間的 900x，直達核心 token
   - 支持 3+ token 複合詞（如 `<04480><09001><06440>` = מִלִּפְנֵי）

2. **增強的警告系統**（§8.4）
   - 智能檢測多 token 複合詞序列
   - 避免將複雜複合詞誤報為 qb_qp_mismatch
   - 支持 token 索引追蹤

3. **改進的日誌記錄**（§8.3）
   - `log_prep_noun_compound_multi()` 記錄所有相關 tokens
   - 日誌條目包含 token 計數信息
   - 區分簡單 (2 tokens) 和複雜 (3+ tokens) 複合詞

4. **新增範例**（§7.7）
   - Gen 4:16 展示多 token 複合詞檢測
   - 完整的 qb.php/qp.php 數據對比

### 11.2 v1.7 vs v1.6 變更（2025-11-24）

1. **新增複合介系詞檢測**（§3.3）
   - 直接從 qp.php wform 提取信息
   - 自動合併 prep+prep 複合詞
   - 記錄但不合併 prep+noun 複合詞

2. **新增日誌文件**（§6.3.3）
   - `compound_prep_plus_noun.txt` 專門記錄 prep+noun
   - 避免污染 uncertain 日誌

3. **警告系統增強**（§8.4）
   - 檢查已記錄的 prep+noun 複合詞
   - 避免重複報告 mismatch

4. **配置擴展**（§5.1）
   - 新增 5 個複合詞相關配置項

5. **輸出格式擴展**（§5.2.2）
   - 新增複合介系詞 JSON 結構

### 11.2 v1.6 vs v1.5 變更

1. **形態碼正規化**：新增 `<WTH/WH 8xxx>` ⇒ `(**8xxx)` 的必做轉寫
2. **隱性形態碼辨識**：正則明確排除 `{<dddd>}`
3. **900x 附著越過規則**：附著時略過 `{<…>}` 與 `{8xxx}`
4. **brace_preps 擴充**：預設加入 `00996`（בֵּין）
5. **ignored_codes 時機**：token 化後、分組前即過濾
6. **morph 細化方式**：`parsing_wform` 僅作補註
7. **決策樹優先序**：特例 1 最高優先，明確代名詞後綴檢測

---

## 12.0 參考資料與工具

### 12.1 相關文檔

- **分析報告**：`COMPOUND_PREPOSITION_ANALYSIS.md`（v1.7 複合詞分析）
- **Bug 修復記錄**：
  - `BUGFIX_900x_prefix_classification.md`（900x 分類修正）
  - `V1.7.1_BUGFIX_DUPLICATE_LOGGING.md`（prep+noun 重複記錄修正）
- **輸出格式**：`UNV_SN_Output_Format_Gen_1_1.md`
- **批次處理**：`Batch_Parsing_SOP.md`

### 12.2 數據源 API

**FHL API** (bible.fhl.net):
- `qb.php`: UNV text with Strong's numbers
  - Parameters: `version=unv`, `chineses=創`, `chap=1`, `sec=1`, `strong=1`
- `qp.php`: Parsing/morphology data
  - Parameters: `engs=Gen`, `chap=1`, `sec=1`

**Book Mappings**: 66 books with bidirectional lookup (Gen ↔ 創, Matt ↔ 太, etc.)

### 12.3 工具腳本

- `fetch_text.sh`: API wrapper with book name translation
- `parse_verse_v1_7.py`: Current parser implementation
- `run_parser_temp.py`: Batch orchestrator
- `batch_parse_pentateuch_first_three.sh`: Batch parsing for Genesis, Exodus, Leviticus
- `monitor_progress.sh`: Progress monitoring

---

## 13.0 常見問題（FAQ）

### Q1: v1.7 是否需要字典文件？

**不需要**。v1.7 直接從 qp.php 的 `wform` 字段提取複合信息，零維護成本。

### Q2: prep+noun 複合詞為什麼不合併？

根據設計決策（`merge_prep_plus_noun: false`），這些詞保持分離以：
1. 保留原始 qb.php 結構
2. 便於後續語義分析
3. 這些不是編碼錯誤，僅是 FHL 的標註風格差異

### Q3: 如何判斷 brace 介詞是否有代名詞後綴？

檢查 qp.php 的 `wform` 字段，查找「詞尾」關鍵字：
- "介系詞 מִן + 3 單陽詞尾"
- "介系詞 + 2 複陽詞尾"
- 正則：`/介系詞.*詞尾/`

### Q4: v1.7.2 與 v1.7/v1.6 輸出兼容嗎？

**兩種模式**：
- 啟用複合詞檢測：輸出包含複合詞信息（v1.7.2 增強版，支持多 token）
- 關閉檢測（`detect_compounds_from_qp: false`）：完全兼容 v1.6

**v1.7.2 向後兼容**：現有 v1.7 功能完全保留，只是增加了多 token 檢測能力。

### Q5: 三個日誌文件的區別？

1. **uncertain_or_expandable_issues.txt**: 真正的解析問題
2. **compatible_but_notable_issues.txt**: 符合規範但值得注意
3. **compound_prep_plus_noun.txt**: prep+noun 複合詞記錄（v1.7），v1.7.2 增強支持多 token

### Q6: v1.7.2 如何處理 Gen 4:16 的情況？

Gen 4:16 中的 `<04480><09001><06440>` 是一個 3-token 複合詞：
- v1.7.2 自動跳過中間的 900x 前綴 `<09001>`
- 檢測核心 token `<06440>` 的 qp.wform 包含「介系詞 מִן +」
- 記錄到 `compound_prep_plus_noun.txt`，不記錄到 `uncertain_or_expandable_issues.txt`

---

**版本**：v1.7.2（完整獨立版）
**日期**：2025-11-25
**狀態**：✅ 生產就緒

> 本規格完整獨立，無需參考其他版本文檔。所有 v1.5/v1.6/v1.7 內容已整合，v1.7.2 新增多 token 複合詞檢測功能已包含。可直接用於實作與測試。
