# ONBOARDING — qp parsing 增補與 survey10 的關係

> 概念根基:[`parsing/PARSING_FOUNDATIONS.md`](../../parsing/PARSING_FOUNDATIONS.md)
> 變更計畫:[`parsing/QP_ENRICHMENT_PLAN.md`](../../parsing/QP_ENRICHMENT_PLAN.md)
> qp 欄位定義:[`survey2 §9.2`](../survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md)

## 為什麼 survey10 需要這份文件

survey10 是 survey1 的 **fork**(自帶 `consensus.py` / `judge.py` /
`run_gold_standard.py` 複本,三檔皆已與 survey1 分流:231/463/267 diff 行)。
2026-07-10 的 qp 增補(commit `8d818d3`)只落在 **survey1** 的複本上,
**survey10 的複本尚未擁有 qp-evidence 能力** — 這是刻意的:s10 正在跑
gold 批次,中途不動它的管線。

## survey1 已落地、s10 尚缺的能力

1. **`qp_evidence.py`**(survey1 目錄)— 自包含模組:
   - `build_qp_table(book_eng, chap, sec)`:每詞 qp 記錄
     (wid/word/orig/sn/wform/exp,跳過 wid=0),qp.php + 本地
     `bible_parsing.db` fallback(17 本帶數字書卷)。
   - `format_qp_evidence()`:給 LLM 上下文的緊湊詞表(動詞標 `[VERB]`)。
   - `validate_morph_attachment()`:決定論 pre-validator — morph 碼(8xxx)
     必須緊跟動詞字義 SN(qp `wform` 含「動詞」者);qp 缺 sn 時保守跳過
     (不誤報)。純函式、無 LLM、無網路依賴(DB 在手時)。
2. **`--qp-evidence` flag**(survey1 `run_gold_standard.py`,**預設 OFF**);
   開啟時僅注入 R2/R3 辯論與裁決上下文,關閉時 prompt 位元組級不變。
3. **`QP_AB_DESIGN.md`**(survey1 目錄)— A/B 實驗設計,**計畫在 s10 的
   下一輪 Gen 批次上跑**:同 verses ± qp evidence,量測共識輪數、
   objective SN coverage、分歧率。s10 是這個 A/B 的預定跑道。

## 若要把能力移植到 s10(未來工作)

- `qp_evidence.py` 是自包含的:直接 `import`(加 survey1 目錄到 path)或
  複製一份到 s10(檔頭已註明出處)。
- 注入點對應 s10 自己的 builder:`build_r2_debate_prompt`(judge.py:307)
  與 `build_r3_prompt`(judge.py:425)——比照 survey1 的做法,flag off 時
  必須位元組級不變(用 survey1 的 byte-identity smoke 驗法)。
- **鐵律不變**:s10 的 `consensus.py::build_gold_standard()` 仍是
  `resolved_at` 唯一權威,qp evidence 只能當 judge 的參考證據,
  不得進入 resolution 邏輯(見 survey1 `ARCHITECTURE_DECISIONS.md`)。
- 參考單測:survey1 `test_qp_evidence.py`(16 例,fixture、無網路)。

## 與 s10 現況的交界

- s10 目前 Gen 6:17 批次(16/17,accept-empty FINAL)完全不受影響 —
  qp 增補沒有動 s10 的任何檔案。
- 下一輪 s10 批次開跑前,先決定要不要按 `QP_AB_DESIGN.md` 排 A/B;
  要跑才做上面的移植。
