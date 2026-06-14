# NAKED_SHELL_UPGRADE.md — 把 s1 三模型互評升級到「去殼路線」

> Status: **DESIGN / 待實作**。本文記錄升級洞見、選定的去殼法、接點與驗證計畫。
> 實作前請先讀 [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md)(`build_gold_standard()` 是 `resolved_at` 的唯一權威)。

## 0. 一句話

s1 目前是「**三模型互評,但帶殼做完整工作**」。升級目標 = 「**三模型互評 + 去殼**」(consensus-on-naked):
讓三個模型只在**裸數字 placement** 上競爭,format(殼)從來源 UNV+SN **查表原樣還原**,
把 format 雜訊從 consensus 的分歧裡徹底拿掉。

## 1. 為什麼要做(洞見)

### 1.1 四格矩陣:現況只有三角,缺「互評 + 去殼」這格

| | 多模型互評 | 去殼 |
|---|---|---|
| 主程式 `llm_direct_sn_unv2notyet.py` | ❌(單模型) | ✅ `--naked`(opt-in) |
| **s1** `run_gold_standard.py` | ✅ R1/R2/R3 | ❌(帶殼) |
| s8 `run_survey8.py` | ❌ | ✅(`restore_shell_guess` 用猜的) |
| s9 `run_survey9.py` | ❌ | ✅(`restore_shell_lookup` 查表零損失) |

「s9 = s1 + s8」裡的 **s1 指的是「任務」(UNV+SN→LCC+SN),不是互評機制**。
所以「互評 + 去殼」這個品質與可信度都封頂的組合,三套程式都沒有。本升級就是填這格。

### 1.2 去殼為什麼能幫到 consensus 本身

s1 的硬骨頭是 **placement**(每個 SN 放到 LCC 哪個詞)。coverage 與 format 是機械性的:
- coverage:來源 UNV+SN 已列出所有 SN(可由 `fix_pipeline` 補漏)。
- format:可由查表零損失還原。

但 s1 現在讓三個模型**連 format 一起扛**,於是 survey1 早期那些「掉 `{<WH0853>}`、掉 `<WAH09002>`、補零不一致」的 bug,
會在 `comparator.texts_match` 裡被當成**分歧**,觸發本來不必要的 R2/R3 升級與 prompt 進化。
**這些分歧大多是 format 雜訊,不是真正的 placement 爭議。**

去殼後:三模型輸出裸數字 → `texts_match` 在裸態比對 → 分歧 100% 是 placement 之爭。
預期效果:**R1 全體一致率↑、R2/R3 升級次數↓、假觸發的 prompt 進化↓**,
且留下來的分歧才是真正該送人工的「黃金疑點」。

## 2. 選定的去殼法:**lookup(原樣),不是 guess**

對 s1 的任務,**`restore_shell_lookup`(s9 法)勝過 `restore_shell_guess`(s8 法)**,理由是結構性的:

1. **來源就在手上。** 任務是把 UNV+SN 的 SN 搬到 LCC,每個 SN 的原始殼**本來就印在來源 UNV+SN**。
   lookup 從來源建表 `{'07225':'<WH07225>', '0853':'{<WH0853>}', '09002':'<WAH09002>'}` 照原樣貼回(零損失);
   guess 把這份現成資訊丟掉、用規則重建,是「明明有答案卻用猜的」。
2. **guess 依賴啟發式清單會漏。** `restore_shell_guess` 的隱性 marker 靠寫死的 `KNOWN_IMPLICIT_OT/NT`;
   清單沒收錄的就猜錯。lookup 逐字抓來源,無此問題。
3. **golden 情境的加分:lookup 暴露異常,guess 掩蓋異常。**
   若 LLM 搬出來源沒有的 SN(幻覺/拆錯),`restore_shell_lookup` 查無 → 留成裸 `<num>`(現行 `return m.group(0)`),
   剛好變紅旗讓裁判/人工看到;guess 會幫它套一個看似合理的殼,把問題藏起來。做黃金標準要的是前者。

### 2.1 lookup 的唯一邊界(需處理)

`build_shell_lookup` 只存 SN 第一次出現的殼(註解:"they should have the same shell format")。
若同一節同一 SN 出現兩次但殼不同(一次 `<WH0853>`、一次隱性 `{<WH0853>}`),會把第二次也貼成第一種。
→ 此邊界 guess 同樣處理不了(更沒依據),故 lookup 不輸;但實作時應 **log 這種「同號異殼」節點**,列入人工複查清單。
參考 `survey9_s1_plus_s8/fix_pipeline_edge.md`(已知 v2 邊界)。

## 3. 接點(s1 程式碼具體要改哪裡)

去殼管線 = `strip → [三模型 placement + 互評] → fix_pipeline → restore_shell_lookup`。
restore 是 deterministic 後處理,**跟互評解耦**,所以改動集中在「輸入剝殼」「比對在裸態」「存檔還殼」三處:

| 階段 | 檔案 / 函式 | 改動 |
|---|---|---|
| **A. 輸入剝殼** | `run_gold_standard.py` 組 prompt 處 + `cli_caller.call_llm`(production mode) | 餵模型的 UNV+SN 範例改為 `strip_shell(unv_sn, markers=False)`;prompt 改成「搬裸數字」;模型回傳裸 `lcc_sn`。 |
| **B. 裸態比對** | `comparator.texts_match`(:26)、被 `judge.py` R2 收斂(:238/:247)、R3 共用 | **核心**:比對對象已是裸文字,format 雜訊自然消失。確認 `texts_match` 的 normalize 不需再特別處理殼。 |
| **C. fix(可選)** | 引入 `shared.sn_shell.fix_pipeline` | 對勝出的裸文字補漏 + 修順序(沿用 s9 用法)。 |
| **D. 存檔還殼** | `consensus.build_gold_standard`(:34,唯一權威) | 存 `lcc_sn` 前:用 `vdata["unv_sn"]`(已存為 `unv_sn_reference`)建 lookup → `restore_shell_lookup(winning_text, lookup)` → 還原成最終帶殼 `lcc_sn`。**裸態存一份、帶殼存一份**,方便對照與除錯。 |

要點:
- **lookup 來源用 UNV+SN(來源語殼),對搬到 LCC 的 SN 仍有效**——殼由 SN 本身(WH/WG/WAH/marker)決定,與譯本無關;且 LCC 出現的 SN 必然來自 UNV,故 lookup 覆蓋完整。
- `build_shell_lookup` / `restore_shell_lookup` 目前在 `run_survey9.py` 內,**應抽到 `shared/sn_shell.py`** 成共用函式,s1/s9/主程式同享(s9 已用、主程式 `--naked` 也用同一套)。
- **不要動 `build_gold_standard` 的 `resolved_at` 判決邏輯**;只在「決定 winning_text 之後、寫檔之前」加還殼一步。

### 3.1 建議用 `--naked` 旗標 opt-in,別直接改預設

- 比照主程式 `--naked` / `--shell-off`,在 `run_gold_standard.py` 加旗標(預設 **off**)。
- 既有 `gold_standard/Gen/`(目前 28 節,帶殼跑的)先不動;驗證通過後再 `--force --naked` 統一重跑。
- 驗證夠了再考慮把預設翻成 on。

## 4. 能不能驗證「哪個去殼法好」——能,而且很便宜

關鍵:**還殼是 deterministic 後處理,跟互評解耦,所以不必花三模型 token 就能定案 lookup vs guess。**

### 驗證①:還殼保真度(純 round-trip,零模型、零 consensus,秒級)
拿一批 UNV+SN 原文 → `strip_shell(markers=False)` → 分別用 `restore_shell_lookup` / `restore_shell_guess` 還殼 → 跟原文逐字比對。
- 預期 lookup ~100%(只在 §2.1 同號異殼邊界掉幾個);guess 量出實際錯誤率,**按 SN 類型分類**(隱性 marker / WAH 前綴 / 8xxx 詞法 / 補零)。
- 這一步直接量出兩者全部差異(差異只在還殼這步),把「哪個好」一翻兩瞪眼定案。
- 先做這個,零成本、立刻有數字。

### 驗證②:去殼有沒有幫到 consensus(需 token + 需 ground truth)
s1 的 UNV→LCC **沒有標準答案**(所以才要 consensus),不能直接對答案。改用**有 FHL 答案的鏡像任務**:
- survey5(KJV+SN→UNV+SN)或 survey4(同語言重標),在三模型 consensus 下跑「帶殼 vs 去殼」,對 FHL 打 coverage/placement/format 分。
- 外加 **s1 內部訊號**(在 s1 本身就能量,不需答案):R1 全體一致率、R2/R3 升級次數、prompt 進化觸發次數。去殼若有效 → R1 一致率↑、升級↓。

## 5. 實作順序建議

1. 抽 `build_shell_lookup` + `restore_shell_lookup` 進 `shared/sn_shell.py`(+ round-trip 測試 = 驗證①)。
2. `run_gold_standard.py` 加 `--naked`:接點 A(輸入剝殼)→ B(裸態比對,多半免改,只需確認)→ D(存檔還殼)。
3. 小批回歸:`--book 創 --chap 1 --naked --force -v`,比對 R1 一致率 vs 舊帶殼跑的 28 節。
4. 跑驗證②(survey5 鏡像)確認去殼確實抬升 consensus 品質。
5. 通過後再考慮翻預設 / 擴大 scope 重建 golden set。

---
*本文由設計討論定稿:lookup(原樣)為選定去殼法;互評骨架與 `--modelsABC` 陣容選擇 s1 已具備,缺的只是把去殼接進 A/B/D 三接點。*
