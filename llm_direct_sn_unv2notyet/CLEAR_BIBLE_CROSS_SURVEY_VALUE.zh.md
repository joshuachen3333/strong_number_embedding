# Clear Bible —— 跨-survey 價值(s1 / s9 / s10)

> 緣起:survey5-obe 於 2026-06-26 接手 **Clear Bible** 對齊資料
> (`survey5_bilingual_sn_benchmark/CLEAR_BIBLE_HANDOVER_from_s10obe.md`)。本文記錄
> 它**對 survey5 以外的價值** —— 對 s1(共識 gold)、s9(production 去殼)、
> s10(慣例 + C/D 對照賽)的槓桿。由 survey10-obe 撰寫;survey5 的整合本身由
> survey5-obe 負責。英文平行版見 `CLEAR_BIBLE_CROSS_SURVEY_VALUE.md`。

## Clear Bible 是什麼(資料)

`…/llm_direct_sn_unv2notyet/Alignments/data/`(Scripture Burrito 格式):
- `sources/WLC.tsv` —— 原文希伯來,每個詞素都帶自己的 Strong's(含 09xxx 不可分
  前綴);新約希臘文為 `sources/SBLGNT*`。
- `{lang}/targets/{TRANS}/…` + `{lang}/alignments/{TRANS}/WLCM-{TRANS}-manual.json`
  —— 10+ 語言(arb asm ben eng fra hau hin por rus spa)× 多種譯本,對希伯來/
  希臘源 token 的**人工**逐詞對齊。**不含中文。**

## 它帶來三樣別處沒有的東西

1. **獨立的人工真值。** 它是人工逐詞對齊 —— 非 FHL、非任何 LLM。目前 s1/s9/s10
   全部都對著**單一** FHL 源(UNV+SN)驗證,有循環風險(LLM 共識 ≠ 真值)。
   Clear Bible 是**第二個獨立真值,能驗證「驗證者」。**
2. **完整的原文源。** WLC 帶**每一個** SN,含 KJV/英文丟掉的 —— 09xxx 前綴、
   第二個 את、希伯來功能詞。(Stage-1 量到 KJV 在創 1 漏掉 **31%** 的 UNV 標籤。)
3. **10+ 語言。** 可測跨語言 / 跨約(舊約↔新約)的泛化,不再只有中文一條線。

## 逐 survey 槓桿

### S1(共識 gold)
- **打破循環、當第四位「裁判」。** S1 現在 R2/R3 三模吵架時只有 LLM 互投。
  Clear Bible 的人工對齊可當**非-LLM 仲裁者**:原文希伯來這個詞到底綁在哪,
  human gold 說了算 —— 直接補強 R3 的「選贏家 / 判集體錯」。
- **驗證 S1 的 gold 是否真對。** 把 S1 產出的 gold 拿去和 Clear Bible 對齊比 →
  量化「共識 = 真值嗎」。這是 S1 一直缺的外部 sanity check。
- ⚠️ **survey6 教訓**:把 WLC 當額外 one-shot 餵進去**可能反而過載**(survey6 就死
  於資訊過載:placement +7pp 但 coverage −10pp)。要測,不能假設。

### S10(慣例 + C/D)—— 受益最大
- **更公平/更強的對照賽源。** A2 對照賽本來用 KJV(漏 31%,不公平)。換
  **WLC/BSB 當源**就消掉 count-mismatch → s1-vs-s10 比較更乾淨。**Stage-2 已經
  在用 WLC**(`run_stage2_harsh.py`,09xxx recall 已驗證)。
- **D-deliberation 的證據。** s10 遇到真模糊節進 D 仲裁時,Clear Bible 的人工對齊
  就是「原文到底怎麼綁」的**客觀證據**,讓 D 不再只是 LLM 再吵一次。
- **慣例的外部驗證。** scribe 抽出的慣例,可拿「10 種語言怎麼對齊同一個現象」
  來背書 —— 慣例若跨語言一致,可信度大增;若只在中文成立,就是過擬合訊號
  (餵回 `CONVENTIONS_PIPELINE.md` 第 5 步)。

### S9(production 去殼)
- **獨立品質天花板。** s9 的產出目前只能對 FHL 自洽性評分。Clear Bible 給一個
  外部真值,能說「s9 達到的不只是 FHL 一致,而是和人工原文對齊一致」。
- **難節的額外參照。** UNV+SN 本身模糊的節,WLC 原文可當 s9 naked 流程的補充
  reference,幫 `fix_pipeline` 確認哪些 09xxx 是真的。
- **多語言外推。** s9 的去殼法本身語言無關;Clear Bible 的 10 語言讓「同一套
  方法搬到非中文目標」有真值可驗。

## 一句話 + 誠實限制

**Clear Bible 對三者的共同價值 = 一個獨立人工真值 + 完整原文源,把「大家都只對
FHL 一個源驗證」的循環打破,並讓 KJV-source 的實驗(尤其 s10 對照賽)變公平。**

**限制:Clear Bible 沒有中文**(10 語言不含中文),所以它**不能直接當 UNV/LCC 的
答案卷** —— 它的力量在**源端(原文/他語)和交叉驗證**,不是中文目標端的 truth。
`gloss2` 有中文詞義但**會洩題**,只能當受控變量,絕不可當 UNV-target 測試的輸入。

**排名:** 最大贏家 **S10**(對照賽直接吃 WLC),其次 **S1**(多一個非-LLM 裁判
破循環),再來 **S9**(拿到外部品質天花板)。

## 可重用 artifacts(已建好)
- `survey10_…/run_stage2_harsh.py` —— WLC loader(`load_wlc_verse`、
  `build_wlc_source`)+ 權威 lemma→FHL-09xxx bridge(`PREFIX_BRIDGE`,剝 niqqud
  後對裸子音)。gloss2 預設剝除。
- `survey10_…/build_exclusion.py` —— kept-set(UNV∩source)+ 09xxx 偵測
  (號碼整數值 ≥ 9000)。
- `survey5_…/CLEAR_BIBLE_HANDOVER_from_s10obe.md` —— 資料清單 + Tier-1(WLC 源)/
  Tier-2(alignment 推導多語言)建構計畫。
