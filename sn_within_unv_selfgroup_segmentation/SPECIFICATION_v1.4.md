## UNV+SN 分組規格 v1.4 (最終版)

### 摘要

本規格旨在定義一個穩定的解析流程，將包含 Strong 編號、形態碼、隱性語素及擴展碼的 UNV 經文純文字，轉換為結構化的語義分組。v1.4 版本在 v1.3 基礎上，新增了對「忽略代碼」的處理、將 `parsing_wform` 補註規則化，並加入了可選的資料驗證建議，使規格更為周全與穩健。

### 一、標記正規化

從 `qb.php` 的 `bible_text` 中，會看到像 `<WAH03588>`、`<WTH8802>` 這種包字母的標記。
**規則：** 抽出裡面的數字即可（WAH/WH/WTH… 全忽略）；保留前導零。

### 二、符號語義與角色

1.  **核心詞／Strong：`<NNNN>`**
    *   角色：建立一個新組（group），成為組的「核心詞」。
2.  **形態碼／Morph：`(8xxx)`**
    *   角色：附在它前面最近的核心詞組上（左附），不單獨成組。
3.  **隱性語素：`{<NNNN>}`**
    *   角色：預設獨立成組，但可按 §四-D 的決策樹與相鄰組合併。
4.  **擴展 Strong：`<09xxx>`**
    *   角色：作為前綴，與其後的第一個「核心詞」合併在同一組（右附）。
5.  **忽略代碼 (Ignored Codes) (v1.4 新增)：**
    *   角色：某些代碼（如段落符號 `09015`）不具備語義分組價值，解析器在掃描到時應直接忽略。

### 三、Token 正則

*   **Strong：** `/<\d{3,5}>/`
*   **900x：** `/<09\d{3}>/`
*   **隱性：** `/\{<\d{3,5}>\}/`
*   **形態：** `/\((?:8[6-9]\d{2})\)/`
*   **忽略：** 中文標點與空白。

### 四、分組（Grouping）與合併規則

(與 v1.3 相同，此處從略)
A) **前綴緩衝 (prefix_buffer)**
B) **建立核心組**
C) **形態附著**
D) **隱性介詞附著決策樹**
E) **Construct Linker 演算法**

### 五、可配置表與開關 (Profile)

*   `brace_preps: [ "05921", "04480", "0413", "00996" ]`
*   `object_marker: "0853"`
*   `prefix_map_900x`: (如 `09001: "ל־"`, `09009: "ה־"`, etc.)
*   `aliases`: (如 `09005: "09001"`)
*   `ignored_codes: ["09015"]` **(v1.4 新增)**
*   `use_construct_linker: true|false`
*   `use_parsing_inference: true|false`

### 六、輸出資料結構

(與 v1.3 相同，包含 `core`, `implicit`, `prefixes`, `morph`, `pre_brace`, `post_brace`, `inferred_prefixes`, `inferred`, `hebrew_order`, `construct_of`, `parsing_wform`)

### 七、（可選）Parsing 輔助規則

1.  **推斷前綴：** 若 `use_parsing_inference: true`，可依 `qp.php` 的 `wform` 補齊 `inferred_prefixes`（如 `הַ` 定冠詞、`וְ` 連接詞），並標記 `inferred: true`。
2.  **補註形態細節 (v1.4 新增規則化)：** 對於已知的粗顆粒形態碼（如 `8799`），引擎 **SHOULD** 在 `qp.php` 可用時，補上 `parsing_wform` 欄位，以提供更豐富的語言學資訊。

### 八、偵錯與邊界建議

(與 v1.3 相同，包含 `brace_attach_ambiguous`, `dangling_900x`, `morph_without_core`, `qb_qp_core_mismatch` 等)

### 九、實作邏輯偽代碼

(與 v1.3 相同)

### 十、資料驗證建議 (v1.4 新增)

本節為可選的後處理步驟，不屬於核心分組規則，但建議實作以提高系統穩健性。

1.  **Strong 編號範圍驗證：**
    *   引擎可選地對 `core` 欄位的 Strong 編號進行範圍驗證（例如，舊約編號應在 1-8999 之間）。若超出範圍，可標記 `warning:"invalid_strong_number"`。
