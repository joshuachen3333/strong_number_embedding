# survey6_original_lang_benchmark/ — 原文錨定 SN 基準測試

## 一句話摘要

**不同語言（英→中）、不同版本（KJV→UNV）；同一節。在 survey5 基礎上加入原文（希伯來/希臘原文）+ SN:word 原文與 SN 對照。**

- Single-pass 5-input 導致資訊過載：placement +7pp 但 coverage -10pp
- Two-pass 嘗試（P1=S5 coverage, P2=refine placement）移交 survey7 驗證
- 結論：原文字典對 placement 有價值，但無法在不犧牲 coverage 下使用
- → survey8 用去殼解決資訊過載，只保留字典的數字部分

## 評分指標

| 指標 | 量什麼 | 白話 |
|------|--------|------|
| **cov** (coverage) | 該有的數字有沒有出現 | 「漏了幾個？多了幾個？」 |
| **place** (placement) | 數字出現了，位置對不對 | 「放對地方了嗎？」 |
| **fmt** (format) | 格式對不對（zero-padding、braces、prefix） | 「殼穿對了嗎？」 |

## 概念

Survey5 的問題：KJV 和 UNV 的 SN 數量常常不一致（因 900x prefix 等），模型只能依賴英中語義配對。

Survey6 的改進：**加入原文（希伯來文/希臘文）作為第三語言錨點**，並提供 SN:原文字典，讓模型透過「原文」確認每個 SN 對應哪個 UNV 詞。

## 主任務：5 inputs → UNV+SN

```
Input (同一節，全部 5 個):
  1. KJV plain         In the beginning God created the heaven and the earth.
  2. Original (Heb/Grk) בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ
  3. KJV+SN            In the beginning<WH07225> God<WH0430> created<WH01254><WTH8804>...
  4. SN:word dict      WH07225: בְּרֵאשִׁית
                       WH01254: בָּרָא
                       WH0430: אֱלֹהִים
  5. UNV plain         起初，神創造天地。

Output: UNV+SN (比對 FHL UNV+SN 為 ground truth)
```

原文和 SN:word 字典都從 **FHL qp.php** 拉取，只取 `word` 和 `sn` 欄位。

## qp.php 資料來源

```
GET https://bible.fhl.net/json/qp.php?engs=Gen&chap=1&sec=1
```

Response: 逐字記錄陣列，每筆有 `wid`, `word`, `sn`, `wform`, `remark`, `exp` 等欄位。

Survey6 只取：
- `word` — 希伯來/希臘原文字形
- `sn` — Strong's 編號（5位數，如 "00430", "07225"）

**跳過 wid=0**（節摘要記錄）。

### SN 正規化規則

qp.php 回傳 5 位數 sn，需轉換成 FHL tag 格式：

```python
if sn.startswith('00'):
    sn = sn[1:]     # "00430" → "0430"
# 其他不變: "07225" → "07225", "01254" → "01254"
prefix = "WH" if is_ot else "WG"
tag = f"{prefix}{sn}"
# 結果: WH0430, WH07225, WH01254
```

### OT/NT 判斷

books.json 中 index 0–38 = OT（Gen–Mal），index 39–65 = NT（Matt–Rev）。
OT 用 `WH` prefix，NT 用 `WG` prefix。

## 與 Survey5 的關係

| | Survey5 | Survey6 |
|---|---|---|
| Inputs | KJV plain + KJV+SN + UNV plain | + Original text + SN:word dict |
| SN 來源 | KJV+SN | KJV+SN (+ dict 輔助) |
| 字典 | 無 | qp.php SN:word |
| Ground truth | FHL UNV+SN | FHL UNV+SN |
| 評分 | 自動 | 自動 |
| 假設 | 模型靠英中語義配對 | 原文字→SN→UNV 三角確認 |

## 可複用的 Survey5 資產

- `auto_score.py` ✅ 直接用
- `analyze_test_dimensions.py` ✅ 直接用
- `run_benchmark.py` (call_ollama, call_claude_cli, call_gemini_cli) ✅ 直接用
- `prompts/survey5_v0.1.md` ❌ 需重寫（5-input 格式）
- `run_survey5.py` 🔄 已改編為 `run_survey6.py`

## run_logs/ 命名格式

統一格式：`{task}_{scope}_{model}_{prompt}_{YYYYMMDD_HHMMSS}.{ext}`

| 欄位 | 說明 | 範例 |
|------|------|------|
| task | s6fwd (KJV+Orig→UNV) | `s6fwd` |
| scope | 書卷+章節 | `gen1`, `gen1_3` |
| model | 全名，特殊字元換 - | `deepseek-v3.1-671b-cloud` |
| prompt | 版本號 | `v0.1` |
| timestamp | YYYYMMDD_HHMMSS | `20260327_120000` |

`--out` 用法（同 survey5）：
- `--out` (無值) → 自動生成檔名
- `--out path/to/file.json` → 指定路徑
- 不加 `--out` → 不存檔

## 用法

```bash
# 單節
python3 run_survey6.py --book 創 --chap 1 --sec 1 --model sonnet

# 整章
python3 run_survey6.py --book 創 --chap 1 --model sonnet --out

# Ollama
python3 run_survey6.py --book 創 --chap 1 \
    --model deepseek-v3.1:671b-cloud --ollama-url http://<ollama-host>:11434 --out

# Dry run (看輸入格式，不呼叫模型)
python3 run_survey6.py --book 創 --chap 1 --sec 1 --dry-run

# 只跑 KJV/UNV SN 數量一致的節
python3 run_survey6.py --book 創 --chap 1 --match-only --out
```

## Benchmark 結果（2026-03-28）

### DeepSeek-671B, Gen 1 比較

| 方案 | Coverage | Placement | Sum | 備註 |
|------|----------|-----------|-----|------|
| **S5 v0.2（單次）** | **0.5904** | 0.5127 | 1.1031 | baseline |
| S6 v0.1（single-pass, 5-input） | 0.4944 | **0.5838** | 1.0782 | placement +7pp, coverage -10pp |
| S6 v0.2（+ tag inventory） | 0.3939 | 0.5698 | 0.9637 | 更多輸入 → 更差 |
| S6 two-pass refine v0.4 | 0.5744 | 0.5665 | **1.1409** | 最高 sum，但不穩定 |

### 關鍵發現

1. **原文字典確實提升 placement**（+7pp），但 single-pass 5-input 導致 coverage 崩潰（-10pp）。
   模型被資訊量壓垮，放出更少 tag。
2. **加更多輸入（tag inventory）反而更差**（cov 0.49→0.39），證實「資訊過載」是根本問題。
3. **Two-pass 架構**（P1=S5 coverage, P2=refine placement）在 Gen 1 上 sum 最高，
   但大規模測試（Gen 2-10, 236 節）不退步率僅 68%，遠低於 90% production 門檻。
   → 詳見 survey7_two_pass_benchmark/background.md

### 結論

- 原文資訊有價值（placement 改善），但目前無法在不犧牲 coverage 的前提下使用
- Two-pass 無法達到 production 所需的穩定性
- **回到 S5 單次 prompt 作為主力改進方向**

## Status

- [x] 概念設計
- [x] `survey6_v0.1.md` — 5-input prompt（標注投射 framing）
- [x] `run_survey6.py` — fetch_qp_verse(), SN 正規化, build_survey6_prompt()
- [x] 基準測試結果（Gen 1，DeepSeek-671B + Sonnet）
- [x] 與 survey5 對比分析 → 原文提升 placement 但犧牲 coverage
- [x] Two-pass 實驗 → 移交 survey7，結論：放棄（不退步率 68%）
