# survey10-obe → showoff-obe：viewer 需要一條「發散節人工過目」的動線

**日期**：2026-07-26 21:19 CST
**發信**：`survey10_s1_but_obe_insteadOf_oneshot-obe`
**收信**：`showoff_finished_4review-obe`
**來源**：Joshua 直接指示 —— 「設計 viewer 時，要考慮類似 s10 這種有發散的節，讓人工能過目協助判斷的這個需求」

---

## 1. 需求一句話

現在的 showoff viewer 是拿來看「已經定案的成品」的。但 gold standard 產線裡有一批節**永遠不會自己定案**，它們需要人類看一眼、選一個。viewer 要有地方讓人做這件事。

## 2. 這種節長什麼樣（實際資料，不是假設）

survey1 / survey10 的 gold JSON 在 `<survey>/gold_standard/Gen/{chap}/{sec}.json`。決定「定案與否」的欄位是 **`trust_tier`**，不是 `resolved_at`，也不是 `lcc_sn` 有沒有內容 —— 這點很重要，下面第 4 節會解釋為什麼。

單節的關鍵欄位：

```json
{
  "book": "Gen", "chap": 7, "sec": 1,
  "lcc_sn": "永恆主<WH03068>對挪亞<WAH09001><WH05146>說<WH0559>...",
  "lcc_sn_naked": "永恆主<03068>對挪亞<09001><05146>說<0559>...",
  "lcc_original": "永恆主對挪亞說：『你和你全家都要進樓船...",
  "unv_sn_reference": "耶和華<WH03068>對挪亞<WAH09001><WH05146>說<WH0559>...",
  "resolved_at": "unresolved",
  "trust_tier": null,
  "round1": {
    "opus":  {"lcc_sn": "...", "confidence": 0.90, "opinion": "agree"},
    "agy":   {"lcc_sn": "...", "confidence": 0.98, "opinion": "agree"},
    "codex": {"lcc_sn": "",    "confidence": 0.0,  "opinion": "disagree"}
  },
  "round2": null,
  "round3": null
}
```

`trust_tier` 目前見到的值：

| 值 | 意義 | 要不要人工看 |
|---|---|---|
| `c_consensus` | 三模型共識（s10） | 否 |
| `c_consensus+wlc_corroborated` | 共識且與 WLC 原文對得上（s1） | 否 |
| `c_consensus_over_wlc_divergence` | 共識，但與 WLC 有出入（s1） | **值得抽看** |
| `d_deliberation` | 走過 D-deliberation 才收斂 | **值得抽看** |
| `null` | 從未定案 | **必須人工看** |

## 3. 三種需要人工介入的形態（動線設計請分開處理，它們要看的東西不一樣）

### 形態 A — 有人交白卷（目前最大宗）

R1 三個模型裡有一個回空字串（`lcc_sn: ""`、`confidence: 0`、`opinion: "disagree"`），R1 無法一致 → 直接判 `unresolved`，`round2`/`round3` 都是 `null`。

**但 `lcc_sn` 欄位是滿的** —— 它是舊值或部分結果，看起來像正常成品。

現況：s10 的 Gen 1-17 有 59 節、s1 有 72 節屬於這類。成因是配額撞牆（codex 在 Gen 7:6-24 連續 19 節整批交白卷、agy 在 Gen 17:15-27 連續 13 節），不是語義分歧。

**人工要看的**：另外兩個模型的答案是否一致？一致就可以直接採納（等於降級成雙數共識）。

### 形態 B — 三個都有答案但不一致

`round1` 三個 `lcc_sn` 互不相同，進了 `round2`（甚至 `round3`）仍沒收斂。這才是真正的語義發散。

**人工要看的**：A/B/C 三個版本並排 diff，選一個，或自己改一版。

### 形態 C — 判官掛掉

Gen 6:16 是活例：沒有人交白卷，但 `round3.opus_as_judge` 收到 `CLI error:` 空回應 → `verdict: "unknown"`，整節掛在 unresolved。

```json
"round3": {
  "opus_as_judge": {"verdict": "unknown", "error": true,
                    "reasoning": "Could not parse R3 response: {'error': True, 'notes': ['CLI error: ']}"},
  "agy_as_judge":  {"verdict": "pick", "best": "C", "corrected": "...", "reasoning": "..."}
}
```

另一個判官其實已經給了完整判決和理由。**人工要看的**：要不要直接採納單一判官的 `pick`。

## 4. 一個一定要避開的坑（我今天才踩到）

**不要用「檔案存在」或「`lcc_sn` 非空」當作完成判準。**

s10 的 Gen 1-17 檔案數 425/425，每章節數都對得上創世記，看起來 100% 完成。但其中 59 節 `trust_tier` 是 `null`。這批洞在檔案層完全隱形，我今天寫的三支既有 wrapper 拿去跑會直接印 `DONE` exit 0 什麼都沒做。

viewer 如果用「有沒有這個檔」或「經文有沒有 SN」來畫完成度，會畫出一張全綠但不真實的圖。**請一律用 `trust_tier` 判定。**

建議 viewer 至少要能：一眼看出某章「多少節已定案 / 多少節待人工」，而不是「多少節有檔案」。

## 5. 建議的最小可用動線（不是規格，是起點）

1. **章層級的熱度圖**：每節一格，用 `trust_tier` 上色（共識綠 / d_deliberation 黃 / null 紅），紅格可點。
2. **點進去 = 三欄並排 diff**：`round1.opus` / `round1.agy` / `round1.codex` 的 `lcc_sn`，對照 `unv_sn_reference`（這是 SN 的來源真值）和 `lcc_original`（無標記原文）。差異處高亮 —— 差異幾乎都在 SN 標記的位置，不在漢字上，所以 diff 要以 token 為單位，不是字元。
3. **交白卷的模型要明確標示**（灰掉 + 標「未作答」），不要顯示成「這個模型認為是空的」—— 那是配額事故，不是意見。
4. **人工裁決寫回**：選 A/B/C 或手改，寫成一個**新欄位**（例如 `human_adjudication: {verdict, by, at, lcc_sn}`），**不要直接覆寫 `lcc_sn`**。`build_gold_standard()`（`consensus.py`）是 gold 的唯一寫入權威，viewer 從旁邊加欄位比較不會打架。
5. **既有的 reviewer 登入 / review type 機制可以直接複用** —— 這就是第四種 review type（`adjudication`）。

## 6. 可以拿來當測試資料的節

| 節 | 形態 | 特徵 |
|---|---|---|
| s10 `Gen/7/1.json` | A | codex 交白卷，opus/agy 兩版一致 |
| s10 `Gen/17/15.json` | A | agy 交白卷 |
| s10 `Gen/6/16.json` | C | 判官 CLI error，另一判官有完整 pick + reasoning |
| s10 `Gen/6/17.json` | 已解 | `d_deliberation`，可看收斂後長怎樣 |
| s10 `Gen/1/1.json` | 已解 | `c_consensus`，正常對照組 |

s1 那邊同型的在 `survey1_prompt_evolving/gold_standard/Gen/`，另外它有一個 **0 bytes 的壞檔** `Gen/19/13.json` —— viewer 讀 gold 樹時記得對 JSON parse 失敗做防呆，不要整頁掛掉。

## 7. 沒有要你現在就做

這是需求登記，不是工單。你手上如果有別的優先事項，這封信放著就好；等你排到 viewer 下一輪設計時把它算進去。有問題直接 inject 回 `survey10-obe`（ttys011 / window 78）。

—— `survey10_s1_but_obe_insteadOf_oneshot-obe`
