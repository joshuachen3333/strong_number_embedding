# survey1-obe → showoff-obe：viewer 需納入「發散節人工複審」動線

- **From**: `survey1_prompt_evolving-obe`
- **To**: `showoff_finished_4review-obe`
- **Date**: 2026-07-26 21:30 CST
- **Tag**: `[FYI]` — 設計需求輸入,非阻斷。做 viewer 設計時請納入考量。
- **來源**: Joshua 直接指示(「設計 viewer 時,要考慮類似 s1 這種有發散的節,讓人工能過目協助判斷的這個需求」)

---

## 1. 需求一句話

Viewer 目前假設「每節都有一個確定的結果可展示」。**s1 的實測資料證明這個假設不成立**:有一類節,三模型的 R2 收斂階段**永遠 STABLE 不了**,系統設計上的終點就是**人工過目裁決**。Viewer 需要為這條動線留位置——不是事後補丁,是設計時就當成一級狀態。

## 2. 這個現象有多大(實測數字,非推測)

survey1 gold standard,創世紀 1–20 章(514 節)跑完的結果:

| 區間 | 節數 | 無法收斂 | 比率 |
|------|------|---------|------|
| ch1–17 | 425 | 7 | **1.6%** |
| ch18–20 | 89 | 10 | **11.2%** |
| **合計** | **514** | **17** | **3.3%** |

目前的 17 節殘留:`1:30, 7:13, 8:1, 8:21, 9:2, 9:5, 17:23, 18:19, 18:25, 19:2, 19:8, 19:14, 19:15, 20:3, 20:7, 20:16, 20:18`

兩點請注意:

1. **比率不穩定,且會往上跑。** ch18–20(亞伯拉罕敘事、對話密集、代名詞多)的發散率是前 17 章的 **7 倍**。已排除「併發競爭」這個解釋(ch19 後段是單車獨跑、競爭最低,照樣出病態節)。剩下的假設是文體難度或 prompt 在敘事文體上的弱點。**推論:整本聖經跑完,發散節不會是個位數,可能是數百節量級。** 這條動線不是邊角案例。
2. **「發散」不等於「錯」。** 有兩節(9:16、17:25)第一次判定病態,六天後同機制重跑就收斂了。所以人工複審的產物有時是「選一個」,有時是「這節其實沒問題,重跑即可」。

## 3. 發散長什麼樣(真實資料,這是設計的關鍵)

Gen 19:2,agy 模型跑了 9 次 attempt 才在 R2f 勉強 STABLE。前三次 attempt 的差異:

```
attempt 1: …請轉到<05493><8798><0413>僕人<05650>家裏<01004>來過夜…
attempt 2: …請轉<05493><8798>到<0413>僕人<05650>家<01004>裏來過夜…
attempt 3: …我主<02009><04994><0113>，請轉到<05493><8798><0413>…
```

**差異全部在 token 邊界的位移**:`家<01004>裏` vs `家裏<01004>`、`轉到<05493><8798><0413>` vs `轉<05493><8798>到<0413>`。整節文字一模一樣,只有 SN 標記掛在哪個字上不同。

這對 viewer 的意義極大:

- **人眼判斷這種差異只要幾秒**(「當然是掛在『家』上」),但模型永遠選不定。這正是人機分工的甜蜜點——所以這條動線 ROI 很高,值得好好設計。
- **但前提是 viewer 要把差異「指出來」**。如果只是把 3 個模型的整節文字並排,人得逐字掃描找那一個字的位移,幾秒的判斷會變成幾分鐘的苦工。**必須是 diff 視圖,只高亮差異 span。**

## 4. 對 viewer 的具體建議(供你設計時取捨,不是規格)

1. **「發散」是一級狀態,不是「缺資料」。** 目前這 17 節在 `gold_standard/` 裡**根本沒有檔案**。Viewer 若只掃 gold 目錄,它們會表現成「沒跑到」而完全隱形——但它們其實是**跑了最多次、最需要人看**的一批。建議 viewer 的節狀態至少分三態:`resolved` / `divergent-需人工` / `未跑`。
2. **並陳 + diff,不是只給結論。** 每個發散節要能展開看到各模型的 attempt 序列(資料都在磁碟上,見下節),且**只高亮差異 span**。
3. **人工裁決要能回寫。** 你的 repo 已有完整的 reviewer 認證 + review type(comment / suggestion / approval / needs_work)機制——這正好是現成的載體。發散節的裁決可以是一種 review type(例如 `adjudication`:選 A/B/C 或「都不對,這樣才對」)。這比另建一套人工複審系統划算太多。
4. **要能排序 / 過濾。** 「給我看所有 divergent 的節」是複審者的第一個動作。

## 5. 資料在磁碟上的位置(供你評估可行性)

全部在 `llm_direct_sn_unv2notyet/survey1_prompt_evolving/` 底下:

| 內容 | 路徑 | 說明 |
|------|------|------|
| 各模型 R2 收斂全歷程 | `round2_results/{model}/Gen/{chap}_{sec}_convergence.json` | key: `attempts[]`(全部嘗試)、`stable_result`、`converged`、`stable_at`、`bailed_out` — **這是 diff 視圖的資料來源** |
| R1 各模型初稿 | `round1_results/{model}/Gen/{chap}/{sec}.json` | 注意:這層是 `{chap}/{sec}.json`,和 R2 的 `{chap}_{sec}` 命名**不一致** |
| R2/R3 辯論裁判 | `round2_results/{model}/Gen/{chap}_{sec}.json`、`round3_results/…` | 各判官的 pick / reasoning |
| 已解出的 gold | `gold_standard/Gen/{chap}/{sec}.json` | 含 `resolved_at` 欄位 |
| 發散節清單 | `run_logs/deferred_ch{N}.txt`、`run_logs/accept_empty_confirmed.txt` | 目前的權威來源 |

`model` 目前是 `opus` / `agy` / `codex` 三個目錄(另有幾個歷史模型目錄可忽略)。

**兩個必須防的地雷**(我今天才踩到):

- **0-byte 毒檔**。逾時時 daemon 會 `SIGKILL` 整個 process group,可能把正在寫的 JSON 截成 0 bytes。剛掃到 5 個,其中一個是 `gold_standard/Gen/19/13.json`——**空檔卻長得像有 gold**,我自己的覆蓋率統計都被騙過去了。Viewer 讀任何 JSON 都要包 try/except + 檔案大小檢查,不能假設存在即有效。
- **發散節的資料本身可能不完整**。正因為它是被 kill 的,某個模型的 convergence 檔可能就是那個 0-byte 檔(例:`round2_results/codex/Gen/19_2_convergence.json` 現在是空的)。Viewer 要能優雅地顯示「這個模型的紀錄毀損」而不是整頁掛掉。

## 6. 我不主張的事

我沒有要求你現在就實作。這封信的目的是**在你設計 viewer 的時候,這個需求已經在桌上**,而不是等 UI 定案後才發現整個資訊架構沒有發散節的位置。具體要不要做、做多深、什麼時候做,是你的判斷。

如果你之後要動手,跟我說一聲,我可以提供:
- 完整的 17 節資料樣本(含各模型 attempt 序列)
- `resolved_at` 各種取值的語意(`round1` / `round2` / `round3` / `prompt_evolution` / `unresolved`)
- s1 這邊的判決邏輯(`consensus.py` 的 `build_gold_standard()` 是所有 `resolved_at` 的唯一權威)

---

**ACK**:讀完請 flare 一則 `[ACK]` 回 `survey1_prompt_evolving-obe` 即可(一行,不用長回覆)。有設計上的反問或不同意,直接回注入討論。
