# Redesign brief — adopt Q1-E (external conventions memory) → s10 can rival s1 for gold

**from** `survey1_prompt_evolving-obe` **to** `survey10_…-obe` · **2026-06-24**
**為 Joshua 指示** · 配套文件:同目錄 [`Original_Design_Decisions.md`](Original_Design_Decisions.md)(Q1/Q2/Q3 完整選項×後果表)

> Joshua 要你**依此重做 s10 設計**。核心:把 D1 從 A(`/compact`)改成 **E(外部慣例記憶)**,並據此**重審 Q2/Q3**,目標是讓 **s10 從「便宜傳播引擎」升級成「有資格與 s1 競爭 gold verses 生產」**。先讀 `Original_Design_Decisions.md`,再依下面重寫 `SURVEY10_DESIGN.md`。

---

## 1. D1 → 改選 Q1-E:External「慣例」外部記憶(中文詳述)

**核心**:把「模型學到的東西」從「對話 context 視窗」抽離。不靠原始對話累積(撐爆視窗、逼你做有損 `/compact`),而是維護一份精煉、結構化的**「已確立慣例」文件 `conventions.md`**,每處理一節就把它**重新注入**。學的是「規則」存外部檔案,不是把整段對話塞進模型腦裡。

**運作**:
1. 每個 panel session 的原始 context 保持**短**(只放當前節任務+必要參考)。
2. 另存 `conventions.md` 記錄已 settle 的可重用規則(隱性標記放法、同號 מִן 重複綁定…)——從已定案節**蒸餾的原則**,不是逐節答案。
3. 處理新節時把 `conventions.md` prepend 進 prompt。
4. 定案後判斷有無新慣例 → 更新 `conventions.md`(經 regression gate / 人工**審查**才寫入)。

**好處**:
1. **學習與視窗脫鉤** → context 永不脹爆,不需 `/compact`、不會壓縮丟失慣例,可無限長跑不退化。
2. **可審查可稽核** → 慣例是人類可讀文件,能在影響面板**前**先看先改先刪。
3. **直接緩解 Q3 錯誤傳播** → 蒸餾+審查關卡讓錯答案不會自動變慣例;E 一手同解 Q1(視窗)+ Q3(污染)。
4. **泛化而非死記** → 存規則比存答案更能遷移,避免 per-verse overfitting。

**挑戰 / 代價**:
1. 多一個 **curation 層**(誰蒸餾、何時更新、自動萃取 vs 人工)。
2. 慣例**衝突**需協調/版本化。
3. 注入成本隨慣例增長(但遠小於累積對話、可控)。
4. 失去「自然連續對話」感(本節內審議仍正常)。

**附帶大禮**:E 讓 **Q1 變簡單** —— 跨節知識 externalize 後,每個 session 可**每節 reset**(永遠短 context),**根本不需 `/compact`、不需 40-50% 門檻、不需 per-leg 視窗管理**。Q1 從「管理超長對話」退化成「維護一份好的慣例文件」;等於把原 D1(壓縮)+D3(回饋)合併成「維護可審查的 `conventions.md`」這**一個**較乾淨的工程問題。

---

## 2. 與 s1 競爭 golden verses 的細節(為什麼 E 是關鍵轉折)

s10 原本被降格成「便宜傳播引擎、不配當 gold 權威」,**唯一根本原因**:
> 要累積專業(s10 賣點)→ 只能靠 stateful session → 犧牲 panel 獨立性 → 共識不再是 N 個獨立證人 → 不可信。

「累積專業」與「失去獨立」原本**綁死**。**E 的本質就是把這兩件事解綁**:累積走外部 `conventions.md`(可審查),不走 session 累積;既然跨節知識在外部檔案,每個 session 能**每節 reset、保持新鮮 → R1 可重新做到「三模型互不相見、獨立作答」(就像 s1)**。E 把獨立性還給 R1,而 R1 獨立性正是 gold 可信度的地基。

**但 E 一個人不夠 —— 要配 Q2/Q3:**

| | 維持原選(全 stateful + 灌原始答案) | 配合 E 改選 |
|---|---|---|
| R1 | 被跨節記憶錨定 | **獨立**(每節 reset) |
| R2 | deliberation 互相影響 → groupthink | 可 blind(s1 式)或 **sealed-bid**(先封閉作答再議) |
| 回饋 | 原始答案灌回 → 錯誤系統傳播 | 只灌**蒸餾+審查過的慣例**(Q3-D) |
| 結果 | 只能傳播 | **有資格競爭 gold** |

→ **能競爭 gold 的組合 = Q1-E + Q2(獨立 R1:blind 或 sealed-bid)+ Q3-D(蒸餾審查慣例)。**

**不只競爭——有機會贏過 s1**:同樣獨立性下,s10 多了 s1 沒有的「全 panel 共享同一份 settle 慣例」。去殼洞見指出**很多 s1 分歧其實是 format/慣例雜訊造成的假分歧**(§2.1、3:11 隱性標記)。s10 事先注入對齊慣例後:
- 假分歧消失 → 剩下分歧 **100% 是真 placement 歧義** → 共識更乾淨、真難節更清楚浮現。
- panel **越跑越聰明**(慣例累積);s1 失憶永遠不會。
- 仍**更便宜**(慣例 settle 後 re-roll 變少)。

**代價(要誠實面對)**:`conventions.md` 變成**新的單一信任點**,寫錯一條規則所有節都繼承。但這其實就是 **s1 的 prompt 換形態** —— 靠**同一套 regression gate** 守(就像 3:11 那個 v1.3 被擋下、REGRESSION_FAILED);差別是 conventions **細粒度可逐條增刪**,比整包 prompt +0.1 更精準、更不易像 v1.3 一改就 regress 8 節。等於把「prompt 進化」升級成「**慣例累積**」。

---

## 3. 要你重做的事(具體)

1. **改 `SURVEY10_DESIGN.md`**:D1 從 A(`/compact`)改為 **E(外部 `conventions.md` + 每節 reset)**;據此重審 D2/D3 —— 推薦 **Q2 守 R1 獨立**(blind 或 sealed-bid)、**D3 改 Q3-D**(只回饋蒸餾審查過的慣例,不灌原始答案)。
2. **設計 conventions pipeline**:慣例**萃取**(orchestrator 或專職「書記」)+ **regression 審查**(複用 s1 regression gate 思路)+ 版本化。
3. **規劃「與 s1 競爭 gold」的實驗**:s10(E 版)與 s1 並列產 gold,用 **survey4/5 的 FHL ground truth** 客觀裁判每條慣例與最終 gold 的對錯。
4. 把上述決策過程(新的選項權衡)記進 `Original_Design_Decisions.md` 或續篇,維持可追溯。

完成後 flare 一個 `[STATUS]` 回 `survey1_prompt_evolving-obe`(window 1314 / ttys002)。這是長任務,開工與完成各 flare 一次。
