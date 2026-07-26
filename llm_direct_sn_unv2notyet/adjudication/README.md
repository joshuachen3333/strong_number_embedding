# adjudication/ — 鬼打牆節人工裁決

MVP(2026-07-27)。範圍**只有 s1 + s10 永遠不定案的節** —— 那些設計上的終點就是人類看一眼。
完整願景(涵蓋所有有輸出經文的 surveyN、所有對照結果)見
[`docs/superpowers/specs/2026-07-25-unified-adjudication-viewer-design.md`](../../docs/superpowers/specs/2026-07-25-unified-adjudication-viewer-design.md)。

## 怎麼用

```bash
# 1. 產生索引(唯讀掃描 s1/s10,零 token 成本,零 FHL 負載)
cd llm_direct_sn_unv2notyet
python3 adjudication/build_stuck_index.py

# 2. 起伺服器
./showoff_finished_4review/start.sh          # 或 python3 start_server.py --port 8989

# 3. 開頁面
open http://localhost:8989/showoff_finished_4review/adjudication.html
```

語料是活的(gold run 隨時在寫),所以**每次要看新狀態就重跑步驟 1**。

## 完成度判準:`trust_tier`,永遠不是「檔案存在」

這是整個設計的地基。s10 的 Gen 1–17 檔案數 425/425、每章節數與創世記完全對得上,
看起來 100% 完成 —— 但其中有數十節 `trust_tier` 為 `null`。而 s1 最需要人看的那批節
**連檔案都沒有**。用檔案存在畫完成度會得到一張全綠但不真實的圖。

三種隱形模式全部處理:

| 形態 `form` | 判定 | 人工要看什麼 |
|---|---|---|
| `blank_ballot` | 檔案在 · `trust_tier` null · R1 有模型回空字串 | 另外兩個模型是否一致?一致即可採納(降級為雙數共識) |
| `true_divergence` | 檔案在 · `trust_tier` null · 三方都有答案但不一致 | 高亮處選一個,或自己給答案 |
| `judge_error` | 檔案在 · `trust_tier` null · R3 判官 `error`/`verdict:"unknown"` | 健全判官可能已給完整 pick — 考慮直接採納 |
| `no_file` | 無 gold 檔 · 在 `deferred_ch*.txt` / `accept_empty_confirmed.txt` | 同 true_divergence;這是跑最多次的一批 |
| `corrupt` | 檔案在但 parse 失敗 | 僅標示,不阻斷整頁 |

## 三個非顯而易見的實作規則

**1. 陣容從資料讀,絕不硬編。** s1 有 8 個 gold 檔用舊陣容(`gemini-3-pro-preview` / `gpt-5.4`),
`round1_results/` 還有 `opus-A/B/C` patch 變體,而 run 可以帶 `--modelsABC` 自訂。
adapter 一律迭代 `round1.keys()`。實測有節次因此出現 5 個候選、4 個 trace。

**2. 毒檔判準是 parse 失敗,不是檔案大小。** `SIGKILL` 截斷不必然截到 0 bytes ——
寫到一半的 JSON 可以有數百 bytes 卻 parse 失敗,size 檢查會整批漏掉。
且掃描期間檔案會增刪(來源不只 pipeline,**也包括 sibling agent 的清理 sweep**),
`_load_json_safe()` 對 missing / 0-byte / 截斷 / 掃描中被刪一律容忍。

**3. attempt 是證據,不是候選。** Gen 6:17 的 codex 有 31 個 attempt 但只約 9 種不同讀法。
把每個 attempt 都變成可挑選的候選會淹沒裁決台,所以索引產出**去重視圖 + 重數**
(`traces[].distinct`),原始有序序列(`traces[].attempts`)保留供回放。

## 路徑陷阱:R1 與 R2 命名不一致

```
round1_results/{model}/{Book}/{chap}/{sec}.json      ← 巢狀目錄
round2_results/{model}/{Book}/{chap}_{sec}.json      ← 底線連接
round2_results/{model}/{Book}/{chap}_{sec}_convergence.json
round3_results/{model}/{Book}/{chap}_{sec}.json
```

這是為什麼 glob `round1_results/*/Gen/*.json` 掃不到任何檔案。

## 側車原則 — 永不改動 survey 的 gold 檔

裁決寫入 `verdicts.jsonl`(append-only),**絕不觸碰 `*/gold_standard/*.json`**。
理由:`consensus.py:build_gold_standard()` 是 gold 的唯一寫入權威,且會以 `--force` 整檔重寫
(實測當下常有多個 run 在跑),在該檔內加欄位仍會被清掉。側車才真正達成「不打架」。

改變心意用新記錄疊加,不刪舊的 —— 心智軌跡完整保留。

## 檔案

| 檔案 | 說明 | 進 git? |
|---|---|---|
| `build_stuck_index.py` | 唯讀掃描 s1/s10 → `stuck_index.json` | ✅ |
| `stuck_index.json` | 衍生資料(~1.2 MB),語料會長,每次重跑 | ❌ gitignored |
| `verdicts.jsonl` | 人類裁決,含 reviewer email | ❌ gitignored(同 `reviews.json` 政策) |
| `../../showoff_finished_4review/adjudication.html` | 裁決頁(單檔) | ✅ |

## API(在 `start_server.py`)

| Method | Path | Auth | 說明 |
|---|---|---|---|
| GET | `/api/verdicts[?csid=&survey=]` | 無 | 公開讀取;容忍被截斷的最後一行 |
| POST | `/api/verdicts` | Bearer | 記錄一筆裁決;沿用現有 OTP session |

`kind`: `pick` · `correct` · `rerun_suggested` · `reject_all` · `defer`
`authority`: `secondary_direct`(我確定就是這樣)· `tiebreak`(看不出誰對但我拍板)· `opinion`

`rerun_suggested` 的存在是因為**發散不等於錯** —— s1 有兩節(9:16、17:25)首次判定病態,
六天後同機制重跑就收斂了。所以人工的產物有時是「這節其實沒問題,重跑即可」。

## 尚未做(MVP 刻意留白)

- 對**單一 attempt 或一次轉變**打分(spec §11.4 的 `rate_process` / `target.level`)——
  目前 trace 只能看,不能逐步評分
- 章層級熱度圖與正典普查(現在的清單只涵蓋已知鬼打牆節,不顯示「完全沒跑」的節)
- token 級 `token_edits` 結構化更正(現在 `correct` 是整句文字)
- `content_hash` 陳舊裁決偵測
- s4/s5/s6/s8/s9 與 s11 的 adapter
