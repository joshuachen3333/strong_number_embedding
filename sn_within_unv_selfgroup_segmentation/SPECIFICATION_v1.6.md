# UNV+SN 分組規格 v1.6（最終版・可實作）

> 本版為 v1.5 的「可實作」定稿：補齊 token 正規化細節、brace 介詞決策樹的優先序、900x 附著的越過規則，以及 FHL Profile 的具體對映與推斷邊界。與 v1.2/v1.5 完全相容；僅補強落地細節。

---

## 1.0 摘要（Summary）

本規格定義由含 Strong 編號、形態碼、隱性語素與 900x 擴展碼的 UNV 經文（FHL `qb.php`）出發，轉為穩定、可機器處理的語義分組。v1.6 在 v1.5 基礎上明確：

* **WTH/WH 形態碼**的正規化（`<WTH8804>` ⇒ `(**8804)`）；
* **brace 介詞**的決策順序（動詞左附例外優先，否則右附名詞）；
* **900x** 附著時需**越過**大括號 token；
* **ignored_codes** 的處理時機；
* `parsing_wform` 僅作**補註**、不改原 `morph` 值；
* FHL Profile 的 900x 對映、推斷分流與顯示順序。

---

## 2.0 標記系統全解析（Token System）

### 2.1 原始資料層（Raw Data Layer）

* **內部前綴**：`WH`, `WTH`, `WAH` 等僅為資料源元數據。
* **規範**：在 **3.1 標記正規化** 中處理；解析流程不直接依賴。

### 2.2 解析器內部 Token 類別

* **核心詞（Core）**：Strong 編號（1–8999 等）。出現於 `<dddd>` 或 `{<dddd>}`（隱性）。
* **形態碼（Morph）**：8xxx 系列（如 8804、8738、8764、8799…）。顯性 `(**8xxx)`、隱性 `{8xxx}`。
* **900x 擴展碼（Prefix）**：9xxx 系列（如 09001、09002、09009…），表示不可分詞綴（ו־、ל־、ה־…）。

### 2.3 職責劃分與重疊

* **數字範圍**：`8xxx` ⇒ **morph**；`9xxx` ⇒ **900x**；其餘 ⇒ **core**。
* **括號用途**：`<...>` ⇒ core/900x；`{<...>}` ⇒ 隱性 core；`(...)`/`{...}` ⇒ morph（8xxx）。
* **不相關**：`WH/WTH/WAH` 等內部前綴與解析邏輯無關（僅正規化時處理）。

---

## 3.0 核心解析規則與流程

### 3.1 標記正規化（必做）

1. 移除 `WH/WTH/WAH` 等**非數字**標籤。
2. **形態碼轉寫**：將 `<WTH(8ddd)>`/`<WH(8ddd)>` 等 **8xxx** 形態碼轉為 `(**8ddd)`（顯性 morph）。
3. **保留** `<09ddd>` 為 900x；其他 `<dddd>`（非 8/9xxx）為 core。
4. `{<dddd>}` 視為**隱性 core**；`{8xxx}`（無 `<`）視為**隱性 morph**。
5. 忽略中文標點／空白，不進入 token 序列。

### 3.2 Token 正則（參考實作）

* **Strong（core）**：`/<dddd>/`
* **900x（prefix）**：`/<09ddd>/`
* **隱性核心**：`/\{<dddd>\}/`
* **顯性形態碼**：`/(8[6-9]dd)/`
* **隱性形態碼**：`/\{(8[6-9]dd)\}/`（先判斷 token 不是 `{<...>}` 再比對）

### 3.3 分組與合併（Grouping & Merging）

**掃描方向**：自左往右；**忽略**標點／空白。

1. **前綴緩衝（prefix_buffer）**
   遇到 900x 先入 `prefix_buffer`；附著時需**越過** `{<...>}` 與 `{8xxx}`，直到下一個 core。

2. **建立核心組**
   遇到 core（顯性或隱性）建立新 group `G`；將 `prefix_buffer` 全部掛到 `G.prefixes[]`，然後清空緩衝。

3. **形態附著**
   遇到 morph（顯/隱）一律**左附**最近一個核心組：`G.morph += code`。

4. **brace 介詞決策樹（v1.2-A 強化版）**
   遇 `{<PREP>}` 時：

   * **特例 1（最高優先）**：若 `qp.wform` 顯示「介系詞 + 代名詞後綴」（如 מִמֶּנּוּ）或位於動詞不定詞補語語境（如 `<0398>(8800){<04480>}`），則**左附**前一動詞：`G_verb.post_brace += PREP`。
   * **特例 2**：`{<0853>}`（受詞記號 אֵת）**總是右附**到後方名詞：`G_noun.pre_brace += 0853`。
   * **一般**：若右側就近（可跨 900x）為**名詞**，則**右附**：`G_noun.pre_brace += PREP`；否則**獨立保留**並標 `warning:"brace_attach_ambiguous"`。

5. **Construct Linker（可選 v1.2-B）**
   若 `qp.wform` 指示名詞為附屬形（construct），將其與右側下一個名詞以 `construct_of: <NNNN>` 連結（可跨 `pre_brace` 與 900x）。僅標註鏈接，不改分組。

6. **資料不一致處理**
   以 `qb.php` 結構為主，`qp.php` 僅作補註。偵測到差異（如 `qb_qp_core_mismatch`）時，在輸出加入 `warnings[]`，並（可選）寫入日誌。

---

## 4.0 配置（Profile）與輸出

### 4.1 可配置表與開關（預設示例）

```yaml
brace_preps: ["05921","04480","0413","00996"]   # עַל, מִן, אֶל, בֵּין …
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
```

**推斷分流原則**：

* `prefixes[]`：僅收錄 `qb.php` 明示 900x。
* `inferred_prefixes[]`：僅收錄自 `qp.wform` 推斷的前綴（如 `ו־`、`ה־`）。
* 嚴禁將推斷結果混入 `prefixes[]`；可用 `inferred: true` 標示來源。

### 4.2 輸出資料結構（欄位約定）

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

---

## 5.0 進階規則與建議

### 5.1 Parsing 輔助（可選）

* **推斷前綴**：若 `use_parsing_inference: true`，自 `qp.wform` 抽取未於 `qb` 明示的前綴，寫入 `inferred_prefixes`（如 `ו־`、`ה־`）。
* **morph 細節補註**：對 `8799` 等粗顆粒碼，將 `qp.wform`（如「Qal 敘述式 3ms」「Qal 祈願式 3ms」）寫入 `parsing_wform`；**不更動** `morph` 值。

### 5.2 偵錯與邊界

* **一般警告**：`brace_attach_ambiguous`、`dangling_900x`、`morph_without_core`。
* **資料不一致**：`qb_qp_core_mismatch` 必須出現在 `warnings[]`，並（可選）記 log。
* **範圍驗證**：可選地驗證 Strong 號段（如舊約 ≤ 8999）。

---

## 6.0 範例（可讀版分群，與 v1.2 一致）

> 僅示意規則生效方式；實作輸出請依 4.2 欄位。以下示例均來自已驗證節：

### 6.1 創 3:5（動詞左附例外）

* `… <0398>(8800){<04480>} …` ⇒ `{<04480>}` 命中「介詞 + 代名詞後綴 / 不定詞補語」語境 → **左附動詞**（`post_brace += 04480`），而非右附後方名詞。

### 6.2 創 1:2（brace 介詞右附名詞 + construct）

* `… 淵面 {<05921>} <06440> …` ⇒ `{<05921>}` **右附**到名詞 `<06440>`（面）。
* `06440`（פְּנֵי，附屬形）→ `construct_of` 指到右側名詞：一次連到 `<08415>`（淵），另一次連到 `<04325>`（水）。

### 6.3 創 1:4（受詞記號與「在…之間」）

* `{<0853>}<0216>`：受詞記號 **總是右附**名詞。
* `{<00996>}<0216>`、`{<00996>}<02822>`：**右附**到名詞（光／暗）。

### 6.4 創 1:5（FHL Profile 與推斷分流）

* `qb` 給 `<09001><0216>`（**ל־** + 光）；`qp` 顯示 `וְ`/`הַ` 時，僅加在 `inferred_prefixes`（不進 `prefixes`）。

---

## 7.0 與 v1.5 的差異（Change Log）

1. **形態碼正規化**：新增 `<WTH/WH 8xxx>` ⇒ `(**8xxx)` 的必做轉寫；避免被誤判為 core。
2. **隱性形態碼辨識**：正則明確排除 `{<dddd>}`；防止與隱性 core 混淆。
3. **900x 附著越過規則**：附著時略過 `{<…>}` 與 `{8xxx}`，直到下一 core。
4. **brace_preps 擴充**：預設加入 `00996`（בֵּין，「在…之間」）。
5. **ignored_codes 時機**：token 化後、分組前即過濾（如 `09015` 段落符）。
6. **morph 細化方式**：`parsing_wform` 僅作補註，不改 `morph` 原值（含 `8799`）。
7. **掃描準則**：明訂忽略標點／空白、左→右掃描。
8. **決策樹優先序**：`{<0853>}` 永遠右附名詞；介詞家族先判「動詞左附例外」，否則右附名詞，否則獨立。

---

### 實作附注（Pseudo-code 片段）

```pseudo
for token in tokens:
  if token is 900x:
     prefix_buffer.push(token)
     continue

  if token is {<PREP>}:
     if qp_says_pron_suffix(token) or is_infinitive_complement(token):
        attach_to_prev_verb(post_brace+=PREP)
     elif next_core_is_noun_skipping_brace_and_900x():
        attach_to_next_noun(pre_brace+=PREP)
     else:
        keep_as_group_with_warning("brace_attach_ambiguous")
     continue

  if token is {<0853>}:
     attach_to_next_noun(pre_brace+="0853")
     continue

  if token is core (visible or hidden):
     G = new_group(core=token, implicit=hidden?)
     G.prefixes += drain(prefix_buffer)
     groups.append(G)
     continue

  if token is morph (visible or hidden):
     last_group.morph += code
     continue

filter_out(ignored_codes) # 在分組前已執行
```

> 以上即 v1.6 定稿；與 v1.2/v1.5 完全相容並可直接落地實作。必要時可附帶 FHL Profile（§4.1）與抓取腳本 `fetch_text.sh` 進行逐節驗證與回歸測試。
