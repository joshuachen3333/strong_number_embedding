# 統一人類裁決中央面板 — 設計規格 v0.2

> 2026-07-25 · Joshua + `showoff_finished_4review-obe`
> 擴展 `showoff_finished_4review/` viewer,使其涵蓋**所有 surveyN 的產出與所有可能的對照結果**,
> 並成為 Joshua 提供「次要直接答案與拍板」的權威裁決介面。

---

## 1. 目的與非目的

### 目的

1. **一個面板涵蓋所有 surveyN** — s1…s11,含無結果資料者(誠實標示)。
2. **涵蓋所有可能的對照結果** — 不為每種對照寫專屬 UI,任何對照都是同一份資料的查詢。
3. **人類裁決是第一級資料** — Joshua 的判斷具權威(`secondary_direct` / `tiebreak`),可被後續 survey 讀取。
4. **可挑選 survey** — 明確選擇 s1 或 s10(或任意子集)作為裁決/對照對象。
5. **可追看並評價中間辯論過程** — R1 → R2a → R2b → … 的震盪軌跡可回放,且可對**單一 attempt 或一次轉變**打分。
6. **發散節人工複審動線** — 「發散/未定案」是**一級狀態**,不是缺資料。詳見 §11(v0.3 增補)。

### 非目的

- 不做統計儀表板/趨勢圖(s9 的 29,958 節屬統計形狀,與逐節裁決是不同使用情境)。此版只提供「按分數篩出低分節次送去裁決」的入口。
- 不跑任何 LLM、不花 token。本規格的資料全部來自已在磁碟上的產出。
- 不修改任何 survey 自己的檔案(見 §4 側車原則)。

---

## 2. 現況查核(2026-07-25 實測)

### 2.1 現有 viewer 的資料源已死

`index.html` 讀 `data_bundle.json`(4.9 MB,2026-03-13,只含 `lcc/claude` 單一組合)。
產生它的 `generate_data_bundle.py:35` 讀 `llm_direct_sn_unv2notyet/output/` —— **該目錄不存在**
(`.gitignore:22` 忽略,從未 commit)。重跑產生器會得到 `Error: output directory not found`。

### 2.2 四個比較/評分腳本完全不落地

`run_a2_wlc_eng.py`(249 行)、`run_a2_contest.py`(212 行)、`fhl_truth_delta.py`(109 行)、
`eval_gold_vs_wlc.py`(204 行)—— 以 `write_text|to_json|json.dump|open(|to_csv` 全面複查,
**四者皆無任何寫檔路徑**,只印 stdout(`eval_gold_vs_wlc.py` import 了 `json` 卻從未 dump)。

⇒ `S10_VS_S1_GOLD_EXPERIMENT.md` 中的 delta 數字(WLC-only full=0.797、conventions Δ=−0.0014)
全為終端機輸出的手抄結果。**s11/A2 目前零機器可讀資料**,這是它無法進 viewer 的根因。

### 2.3 評分結構已有事實標準

`survey4/auto_score.py:score_verse(model_output, ground_truth)` 回傳:

```jsonc
{ "exact_match": bool, "coverage": float, "placement": float, "format": float,
  "details": { "total_truth_tags": int, "total_model_tags": int,
               "missing": [str], "extra": [str], "misplaced": int,
               "format_issues": [str], "brace_mismatches": [str] } }
```

s5 / s6 / s8 / s9 全部原封不動使用。**本規格直接沿用,不重新發明。**

### 2.4 辯論軌跡已在磁碟上 — 共 2,083 個

| | s1 | s10 |
|---|---|---|
| 路徑 | `round{1,2,3}_results/{model}/{Book}/{chap}_{sec}[_convergence].json` | 同構 |
| convergence 檔數 | 1,060 | 1,023 |
| 結構 | `{stable_result, converged, attempts:[R1,R2a,R2b,…], stable_at, bailed_out}` | 同 |
| attempts 分佈 | 2:471 · 3:168 · 4:247 · 5:66 · 6:38 · 7:30 · 8:13 · 9:9 · … · **max 31** | — |
| `bailed_out` | 66 | — |
| 標籤產生 | `judge.py:_r2_label(i)` | 同 |

極端案例:`round2_results/codex/Gen/6_17_convergence.json` 有 **31 個 attempt**,
在約 8–9 種不同讀法間震盪,`stable_at: "R2l"`。(即 memory 記載的 opus/codex 結構性不收斂。)

### 2.5 Join 基數不對稱 — adapter 必須兩邊容忍

| | s1 | s10 |
|---|---|---|
| gold 節數 | 418(**正在增長**) | 425 |
| 有 R2 trace 的節 | 343 | 341 |
| **gold 但無 trace** | **81** | **84** |
| **trace 但無 gold** | **6** | 0 |
| 每節 trace 模型數 | 3:322 · 5:15 · 2:3 · 8:1 · 4:1 · 1:1 | 3:341(一致) |
| R3 trace 節數 | 17 | 19 |

### 2.6 陣容漂移 — 不可硬編模型名

- s1 `round1` 鍵集:**410×** `(agy, codex, opus)` · **8×** `(gemini-3-pro-preview, gpt-5.4, opus)`
- s10 `round1` 鍵集:425× `(agy, codex, opus)` 一致
- `round1_results/` 目錄含 patch 變體:`opus-A`、`opus-B`、`opus-C`
- 實測有 run 以 `--modelsABC opus agy gpt` 啟動 ⇒ 陣容是 per-run 可組態的

⇒ **adapter 一律走 `round1.keys()` 迭代,絕不假設任何模型名。**

### 2.7 語料是活的

實測當下有 3 個 gold run 在跑:

```
run_gold_standard.py --force --book 創 --chap 9 --sec 2
run_gold_standard.py --book 創 --chap 6 --sec 17 --modelsABC opus agy gpt --skip-scribe --force
auto_run_one_chapter.py --chap 6
```

走查期間 s1 gold 由 416 → 418。⇒ 索引必須**增量可重建**;`--force` 會**就地覆寫**同一候選的內容
(見 §5.1 `content_hash` 與 §5.4 陳舊裁決偵測)。

### 2.8 各 survey 可裁決存量

| survey | 實體資料 | 可裁決量 |
|---|---|---|
| **s1** prompt_evolving | `gold_standard/Gen/1-18` + round1/2/3_results | 418 節 × 至多 7 候選 + 1,060 trace |
| **s10** obe_insteadOf_oneshot | 同構 + `conventions.md` C/D ledger | 425 節 + 1,023 trace |
| **s5** bilingual | `bakeoff_*.json` `results.{A,B}[]`(含 `tiers`/`n9_placed`) | 31 節 × 2 arm |
| **s6** original_lang | `run_logs` `pass1_output`+`pass1_score`+最終 | 31 節(two-pass) |
| **s8** simplest | `run_logs` `score1_stripped`/`score2_shelled` | 31 節 × 3 run |
| **s9** s1+s8 | `run_logs` 單檔 **29,958 節** + `coverage_rate` | 按分數篩選後裁決 |
| **s4** self_supervised | `compare_all`(26 模型聚合)· `dim_verse_map`(31,103 節 × 26 維)· `exemplar_library` | 排行榜 26 模型;**dims 供全體共用** |
| **s2** fhl_format_spec | `FHL_SN_FORMAT_REFERENCE.md` | 非裁決對象 → 驅動 SN 記號圖例與格式合法性檢查 |
| **s11** gold_factory | 僅 2 份 md,腳本不落地 | **0**(補 `--emit-json` 後為 3 arm) |
| **s3 / s7** | 僅 md | registry 卡片標「無結果資料」 |

---

## 3. 三個決定「最大包容性」的設計洞見

**① 對照不是資料,是查詢。**
每個候選答案帶同一把 join key `csid = {task}:{Book}:{chap}:{sec}`。任何對照 —— s1-vs-s10、
A/B arm、26 模型排行、甚至未來才想到的組合 —— 都只是「group by csid,再按軸過濾」。
**不需為任何新對照寫 adapter。**

**② 一個泛用 `stages[]` 吃掉所有多階段管線。**
三件看似無關的事其實同構:s1/s10 的 R1→R2→R3 共識輪、s6 的 pass1→pass2、
s8/s9 的 strip→LLM→fix→shell。皆為「有序階段,每階段有產出、可能有分數」。一個欄位全包。

**③ `extra` 原封不動保留。**
任何 survey 特有欄位一律進 `extra`,viewer 以 JSON inspector 呈現。**保證零資料遺失** ——
這是「最大包容」的保險絲,不必預先想到所有欄位。

---

## 4. 側車原則(Joshua 拍板 2026-07-25)

> 裁決**獨立存放,永不改動 survey 自己的 `gold_standard/*.json`**。

- 所有新資料寫入 `llm_direct_sn_unv2notyet/adjudication/`,對 survey 目錄**唯讀**。
- 理由:gold 檔是 pipeline 會以 `--force` 重寫的(§2.7 實測正在發生);裁決寫進去會被覆蓋,
  且人機 provenance 混在同一檔。
- 裁決可**匯出**成 `adjudication/exports/human_gold/{Book}/{chap}/{sec}.json`,
  讓後續 survey 當成「另一家 gold factory」或評分真值讀取 —— 匯出是明確動作,非自動回寫。

---

## 5. 資料格式

### 5.0 目錄佈局

```
llm_direct_sn_unv2notyet/adjudication/
├── registry.json                              # 11 個 survey 的卡片資料
├── truth/{Book}/{chap}.jsonl                  # FHL 真值(跨 survey 共用)
├── candidates/{task}/{Book}/{chap}.jsonl       # 裁決單元,一行一候選
├── traces/{survey}/{Book}/{chap}.jsonl         # 辯論軌跡(與 candidates 分檔,體積大)
├── runs/{run_key}.json                        # 每次跑的 manifest + 聚合(排行榜讀這個)
├── verdicts.jsonl                             # ★ 人類裁決,append-only
├── exports/human_gold/{Book}/{chap}/{sec}.json # 匯出的人類 gold(明確動作才產生)
└── index.json                                 # 章節 → 檔案/計數 對照,供 lazy load
```

按章分片存 JSONL 是刻意的:s9 有 29,958 節,現行 4.9 MB 單一 `data_bundle.json` 的做法會撐爆。
viewer 改為按章 lazy load。

### 5.1 `task` enum — 鎖定,adapter 不得自創

純 ASCII(Joshua 拍板),同時作為檔名 slug:

| slug | 來源 → 目標 | 有 FHL 真值 |
|---|---|---|
| `unv2lcc` | UNV+SN → 呂振中 | ✗(LCC 無 SN) |
| `unv2rcuv2010` | UNV+SN → 和合本2010 | ✗ |
| `kjv2unv` | KJV+SN → UNV(去殼) | ✓ |
| `wlc2unv` | WLC(+可選英文橋) → UNV(去殼) | ✓ |
| `unv_naked2unv` | UNV 去 SN → 還原 SN | ✓ |
| `orig2unv` | 原文(QP/SBLGNT) → UNV | ✓ |

新增 task 需改本表,不可由 adapter 自行造字。

### 5.2 Candidate — 唯一的裁決單元

```jsonc
{
  // ── 身份(全部由磁碟路徑/內容導出,不含時鐘)──────────────
  "csid": "unv2lcc:Gen:1:1",              // 裁決單元:同 csid 者可互比
  "cid":  "s1/panelist/opus",             // 候選:{survey}/{role}/{model}[/{arm}]
  "content_hash": "sha256:9f2a…",         // sn_text 的 hash → 偵測 --force 覆寫
  "task": "unv2lcc",
  "ref":  { "book": "Gen", "book_chi": "創", "chap": 1, "sec": 1 },

  // ── 內容 ────────────────────────────────────────────────
  "source_text":   "起初<09002><7225>，　神<0430>創造<1254>…",   // 投射來源(帶 SN)
  "target_plain":  "起初上帝創造天地。",                          // 目標原文(無 SN)
  "sn_text":       "起初<09002><7225>上帝<0430>創造<1254>…",      // ★ 裁決對象
  "sn_naked":      "起初<7225>上帝<0430>…",                      // 去殼版(有才填)

  // ── 出處 ────────────────────────────────────────────────
  "provenance": {
    "survey": "s1",
    "role": "panelist",        // final|panelist|judge_corrected|arm|pass|baseline|human
    "arm": null,               // s5:"A"/"B" · s11:"B"/"B0"/"B_noeng"
    "model": "opus", "brand": "claude",
    "prompt_version": "v1.3", "conventions_version": null,
    "self_confidence": 0.97,   // 模型自報,非客觀
    "run_key": "s1-gold",      // ★ 非識別性 metadata,不進 cid
    "source_path": "survey1_prompt_evolving/gold_standard/Gen/1/1.json",
    "mtime": "2026-06-19T02:14:07"
  },

  // ── 客觀分數(有真值才有;結構 = auto_score.score_verse 原樣)──
  "score": { "exact_match": false, "coverage": 0.4444, "placement": 1.0, "format": 0.8889,
             "details": { "total_truth_tags": 9, "total_model_tags": 8,
                          "missing": ["{<H853>}","<H8804>"], "extra": ["<H853>"],
                          "misplaced": 0, "format_issues": [], "brace_mismatches": ["H853"] } },
  "score_variants": { "stripped": { /* 同上 */ }, "shelled": { /* 同上 */ } },  // s8/s9 雙評分

  // ── 泛用多階段(共識輪 / two-pass / naked 管線 通吃)────────
  "stages": [
    { "name": "R1", "role": "panelist", "output": "…", "score": null,
      "meta": { "opinion": "easy" } },
    { "name": "R2", "role": "judge", "output": null,
      "meta": { "best": "C", "corrected": "…", "sn_counts": {"A":8,"B":0,"C":9},
                "sn_count_unv": 9, "reasoning": "…" },
      "trace_ref": "s1/traces/Gen/1.jsonl#unv2lcc:Gen:1:1/opus" },   // → §5.3
    { "name": "R3", "role": "judge",
      "meta": { "verdict": "pick", "best": "C", "corrected": "…", "reasoning": "…" } }
  ],

  // ── 過濾/分組軸(扁平,viewer 據此建 facet)──────────────
  "axes": {
    "trust_tier": "c_consensus+wlc_corroborated",
    "resolved_at": "round2",   // round1|round2|round3|r2_model_patch|r2_early_evolution|d_deliberation|unresolved
    "dims": [1, 4, 13],        // s4 的 26 個難度維度(跨 survey 共用標籤)
    "tag_count": 9,
    "n9": { "placed": 1, "total": 1 },                    // 09xxx recall
    "tiers": { "wlc_only": {"placed":1,"total":1,"frac":1.0},
               "rock": {"placed":7,"total":7,"frac":1.0},
               "kjv_only": {"placed":0,"total":1,"frac":0.0} },
    "kept": { "kept_count": 7, "excluded_by_family": { "prefix_09": 2 } },
    "wlc_status": "clean",
    "coverage_rate": 0.9474,   // s8/s9
    "flags": ["has_wlc_divergence", "no_trace"]           // viewer 標紅/優先排序
  },

  // ── 需人眼的證據 ────────────────────────────────────────
  "evidence": {
    "wlc_divergences": [ { "side": "gold_only", "bare_num": "H0120", "family": "core_func",
                           "kind": "methodology", "count": 2, "wlc_lemma": "אדם",
                           "wlc_strong": "H0121", "source_token": "那人" } ],
    "notes": ["…模型自述理由…"]
  },

  "extra": { }   // survey 特有欄位原封不動,零遺失
}
```

**`cid` durability 規則(關鍵)** — `cid` 只由 `{survey}/{role}/{model}[/{arm}]` 組成,
**不含任何時鐘導出的 run_id**。理由:磁碟上沒有任何產出攜帶 run 識別碼(gold JSON 沒有,
convergence 檔沒有),若由 mtime 鑄造,重建索引可能鑄出不同值,使既有裁決的 `target.cid`
全數失聯 —— 那正好摧毀選擇側車存放要保住的性質。`run_key` 降級為 `provenance` 內的非識別性 metadata。

### 5.3 Trace — 辯論軌跡(獨立檔,因為體積大)

```jsonc
{
  "csid": "unv2lcc:Gen:6:17",
  "cid": "s1/trace/codex",                  // 對應 candidate 的 trace
  "survey": "s1", "model": "codex", "stage": "R2",
  "source_path": "survey1_prompt_evolving/round2_results/codex/Gen/6_17_convergence.json",

  "converged": true,
  "stable_at": "R2l",
  "bailed_out": false,
  "attempt_count": 31,

  // 原始有序序列 —— 回放用,完整保留
  "attempts": [
    { "label": "R1",  "text": "我<0589>呢，你看罷<02009>，我要使<0935><8688>洪流<03999>…" },
    { "label": "R2a", "text": "…" },
    { "label": "R2b", "text": "…" }
  ],

  // ★ 去重視圖(含重數)—— 裁決台預設呈現這個
  "distinct": [
    { "text": "…我要使<0935><8688><0853>洪流<03999>大水<04325>臨到<05921>地上",
      "labels": ["R2g","R2i","R2l","R2m","R2r","R2s","R2v","R2w","R2x"], "count": 9,
      "is_stable": true },
    { "text": "…我要使洪流<03999>大水<04325>臨到<0935><8688><0853>地上<05921>",
      "labels": ["R2h","R2o","R2u"], "count": 3, "is_stable": false }
  ],
  "oscillation": { "n_attempts": 31, "n_distinct": 9, "repeat_ratio": 0.71 }
}
```

**為何 attempt 是證據而非候選** —— Gen 6:17 的 31 個 attempt 中僅約 8–9 種不同文字
(R2g/R2i/R2l/R2m/R2r/R2s/R2v/R2w/R2x 全然相同)。若把每個 attempt 升格為可挑選的 Candidate,
裁決台會被重複列淹沒,且 s1 單獨就膨脹約 3,700 列。去重視圖才是非專家能裁決的形式:
「codex 在這 3 種讀法間震盪,其中這一種出現 9 次。」原始有序序列保留供回放。

### 5.4 Verdict — 人類裁決(append-only)

```jsonc
{
  "vid": "v_20260725_0001",

  // ── ★ 判別式 target:可指向候選、階段、或單一/一對 attempt ──
  "target": {
    "level": "attempt",                    // candidate | stage | attempt
    "csid": "unv2lcc:Gen:6:17",
    "cid": "s1/trace/codex",               // stage/attempt 必填
    "stage": "R2",                         // stage/attempt 必填
    "attempt_labels": ["R2b", "R2c"]       // attempt 專用:1 個=點評,2 個=評一次「轉變」
  },
  "target_content_hash": "sha256:9f2a…",   // 裁決當時的內容 hash → 偵測事後被 --force 改動

  // ── 答案類裁決 ──────────────────────────────────────────
  "kind": "pick",        // pick | correct | reject_all | defer | endorse | rate_process
  "picked_cid": "s1/panelist/opus",        // kind=pick
  "sn_text": null,                         // kind=correct:你給的答案
  "token_edits": [                         // 選用:token 級更正;不填即節級裁決
    { "token": "天", "op": "set", "from": ["<0853>","<8064>"], "to": ["<8064>"] }
  ],

  // ── 過程類裁決(kind=rate_process 時填)──────────────────
  "process": {
    "aspect": "oscillation",   // oscillation | convergence_quality | judge_reasoning | correction_quality
    "score": 2,                // 1–5
    "label": "pathological"
  },

  // ── 權威與心智軌跡 ──────────────────────────────────────
  "authority": "secondary_direct",  // secondary_direct(次要直接答案) | tiebreak(拍板) | opinion(僅意見)
  "confidence": "sure",             // sure | leaning | unsure
  "rationale": "LCC 用「上帝」,0430 該掛在上帝而非天。",
  "reviewer": { "email": "…", "name": "…" },
  "supersedes": null,               // 改變心意時指向舊 vid,不刪舊記錄
  "created_at": "2026-07-25T14:02:11"
}
```

四個刻意的設計:

- **`target` 判別式** —— 沒有它,`verdicts.jsonl` 永遠只能記節級勝者,Joshua 的第 5 點需求
  (評價中間過程)不可實作。這是 v0.1 草案的阻塞缺陷。
- **`kind: rate_process` 與答案類正交** —— 「這次收斂是病態的」「R3 推理正確但選錯」
  「judge 的 corrected 勝過所有 panelist」是**過程**判斷,不是「哪個答案對」。混進 `pick`/`endorse`
  會在實作中途才發現,屆時得遷移 `verdicts.jsonl`。
- **`target_content_hash`** —— §2.7 實測 `--force` 正在就地覆寫。裁決記下當時 hash,
  viewer 可標示「你判過的這個答案之後被重跑改掉了」,而非默默失效。
- **`supersedes` 而非覆寫** —— 改變心意保留完整軌跡;`kind: defer` 讓非專家能誠實跳過,
  而 defer 清單正好是該轉去問 SN 專家的名單。

### 5.5 Run — 聚合(排行榜讀這個)

```jsonc
{
  "run_key": "s4-compare_all-20260326",
  "survey": "s4", "task": "unv_naked2unv",
  "meta": { "models": [...], "source": "…", "pairs": 3, "prompt": "v1.2",
            "seed": 42, "timestamp": "2026-03-26T09:28:37", "total_time_minutes": 32.6 },
  "aggregate": [
    { "model": "qwen3:32b", "brand": "ollama", "n": 3, "errors": 0, "rate_limited": 0,
      "exact": 0.0, "coverage": 0.25, "placement": 0.75, "format": 1.0,
      "time_minutes": 0.1, "sec_per_verse": 2.3 }
  ],
  "candidate_refs": ["unv_naked2unv/Gen/1.jsonl"]
}
```

### 5.6 Registry — 涵蓋「所有 surveyN」

```jsonc
{ "surveys": [
  { "id": "s1", "dir": "survey1_prompt_evolving", "title": "3-Model Gold Standard(prompt 演化)",
    "question": "三模型共識能否產出可信 gold?prompt 自動演化是否有效?",
    "status": "active", "adjudicable": true,
    "counts": { "candidate_sets": 418, "candidates": 2100, "traces": 1060 },
    "docs": ["ARCHITECTURE_DECISIONS.md", "DEEP_INSIGHTS.md", "FHL_DIVERGENCE_LOG.md"],
    "conclusion": "418 節 gold;312 節 wlc_corroborated,49 節 unresolved" },
  { "id": "s3", "dir": "survey3_whether_feeding_prompt_comment",
    "question": "餵 prompt 註解是否有幫助?", "status": "docs_only", "adjudicable": false,
    "counts": { "candidate_sets": 0 }, "conclusion": "無結果資料" }
] }
```

s2 特例:`adjudicable: false`,但其 `FHL_SN_FORMAT_REFERENCE.md` 驅動 viewer 的
**SN 記號圖例**與**格式合法性檢查**(`role: reference`)。

---

## 6. Adapter 規則(全部從 §2 實測導出)

1. **陣容從資料讀,不硬編** —— 迭代 `round1.keys()`。s1 有 8 個檔用舊陣容
   (`gemini-3-pro-preview`/`gpt-5.4`/`opus`),且 run 可帶 `--modelsABC` 自訂。
2. **join 兩邊都要容忍** —— gold 無 trace(s1: 81 · s10: 84)標 `axes.flags += ["no_trace"]`;
   trace 無 gold(s1: 6)仍產出 trace 記錄與 `role=panelist` 候選,`axes.resolved_at = null`。
3. **每節 trace 模型數不定** —— s1 實測有 1/2/3/4/5/8 種;含 `opus-A/B/C` patch 變體。全收。
4. **增量重建** —— 索引器比對 `source_path` 的 mtime + `content_hash`,只重建變動者。
   語料是活的(§2.7),不可假設凍結快照。
5. **唯讀** —— adapter 對 survey 目錄只讀不寫。
6. **`task` 只能取自 §5.1 鎖定清單。**
7. **未知欄位一律進 `extra`**,不得丟棄。

---

## 7. Viewer 介面

### 7.1 Survey Registry(首頁,新增)

11 張卡片:問什麼問題 · 可裁決量 · 目前結論 · 相關文件連結。`docs_only` 者誠實標示無資料。

### 7.2 Survey 選擇器(Joshua 需求 4)

控制列新增多選 survey chip(`s1` `s10` `s5` …)。選 1 個 = 單獨審閱;選 2+ = 自動進入
N-way 對照(§7.3)。與現有的 version / brand 選單並存。

### 7.3 N-way 裁決台

同 csid 的候選並排(2–7 欄),token 級 diff 上色標出彼此差異;有真值時每欄顯示
`placement / coverage / 09xxx recall`。動作:**選勝者** · **都不對** · **存疑** · **認可機器判斷**。
facet 側欄由 `axes` 自動生成(trust_tier / resolved_at / dims / flags)。

### 7.4 Trace 回放器(Joshua 需求 5)

- 縱向時間軸:R1 → R2a → R2b → …,預設呈現**去重視圖**(重複的 attempt 收攏為一列 + 重數徽章)。
- 每列顯示與**前一 attempt** 的 token 級 diff —— 一眼看出它在改什麼。
- `stable_at` 標記綠、`bailed_out` 標紅、`oscillation.repeat_ratio` 顯示為震盪指標。
- **每列與每個「轉變」都有評分控制**(1–5 + aspect),寫成 `kind: rate_process` 的 verdict。
- 「展開原始 31 個 attempt」為可選動作,預設收合。

### 7.5 更正編輯器

在 `sn_text` 上直接編輯 SN,產生 `kind: correct` 的裁決。token 級編輯為選用 ——
節級裁決已足夠(Joshua 非 SN/原文專家,強迫逐 token 判會卡住)。
以 s2 的格式參考做即時合法性檢查(四種 SN 格式、900x 必為 5 位、4 位 `<0914>` 不是 prefix)。

### 7.6 陳舊裁決標示

`target_content_hash` 與當前 `content_hash` 不符時,該裁決顯示「已變更」徽章並提供
「重看差異 / 重新裁決」。

---

## 8. 需要改動的檔案

| 檔案 | 改動 | 阻塞? |
|---|---|---|
| **新** `adjudication/build_index.py` | 索引器:呼叫各 adapter → 產出 §5.0 全部檔案;增量 | 否 |
| **新** `adjudication/adapters/s{1,10}.py` | gold + round1/2/3_results → Candidate + Trace | 否 |
| **新** `adjudication/adapters/s{4,5,6,8,9}.py` | run_logs → Candidate + Run | 否 |
| **新** `adjudication/schema.py` | 型別定義 + 驗證(`task` enum 鎖定於此) | 否 |
| `showoff_finished_4review/index.html` | registry 首頁 · survey 選擇器 · N-way 裁決台 · trace 回放器 · 更正編輯器 · 按章 lazy load | 否 |
| `start_server.py` | `GET /api/candidates?csid=` · `GET /api/traces?csid=&cid=` · `POST /api/verdicts`(沿用現有 OTP Bearer)· `GET /api/registry` | 否 |
| `generate_data_bundle.py` | **廢棄**(讀已消失的 `output/`),由 `build_index.py` 取代 | 否 |
| `run_a2_wlc_eng.py` · `run_a2_contest.py` · `fhl_truth_delta.py` · `eval_gold_vs_wlc.py` | 補 `--emit-json` 落地為 Candidate + Run | **是** — 補完仍需付費跑 arm 才有列 |

---

## 9. 分期

**Phase 1 — 立即可做,零 token 成本(涵蓋 843 節 + 2,083 trace)**
schema + s1/s10 adapter + 索引器 + registry + survey 選擇器 + N-way 裁決台 + trace 回放器
+ verdict API。這是 Joshua 最具體的兩個需求(選 survey、評中間過程),且資料**全部已在磁碟上**。

**Phase 2 — benchmark adapter**
s4/s5/s6/s8/s9。s9 的 29,958 節以 `coverage_rate` 篩選後才進裁決佇列。

**Phase 3 — 阻塞於 contest 執行**
四個 A2 腳本的 `--emit-json`。**先補 patch 不會產生任何一列** —— 要有人付費跑 arm 才有資料。
因此排最後,但 schema 已為它預留 `arm` / `score` / `tiers` 欄位。

---

## 10. 風險與未決

1. **`cid` 碰撞** —— 若同一 survey 同一 role 同一 model 在同一 csid 有多筆(例如 `opus-A` 與
   `opus` 視為同模型),需以 patch 變體名進 `model` 欄位區分。已知 s1 有 `opus-A/B/C`,
   實作時須確認它們在 gold JSON 的 `round1` 鍵中如何呈現。
2. **s9 規模** —— 單檔 29,958 節,索引時須串流讀取,不可整檔載入記憶體。
3. **活語料競態** —— 索引進行中 gold run 正在寫檔。索引器須容忍讀到半寫入的 JSON
   (s1 已有前例:`0fd576f` 修過 kill -9 造成的 0-byte convergence cache)。
4. **裁決權威的下游消費** —— 匯出 `human_gold/` 後,哪個 survey 以何種方式讀取,本規格未定義。
   刻意留待實際需要時再設計,避免過早抽象。

---

# 11. v0.3 增補 — 發散節人工複審動線

> 來源:兩封 sibling Obe 信件(2026-07-26),皆源自 Joshua 直接指示
> 「設計 viewer 時,要考慮類似 s1/s10 這種有發散的節,讓人工能過目協助判斷的這個需求」
> - `showoff_finished_4review/docs/20260726_2119_from_survey10-obe_to_showoff-obe_divergence_human_adjudication_ui.md`
> - `showoff_finished_4review/docs/20260726_2130_from_survey1-obe_to_showoff-obe_divergent_verse_human_review.md`
>
> 本節數字全部經 showoff-obe 於 2026-07-26 21:4x 獨立實測複核,與信中數字有出入者以本節為準
> (語料是活的,兩邊測量時點不同)。

## 11.1 這條動線的量級 — 不是邊角案例

s1 實測(創 1–20,514 節):**17 節** 三模型 R2 永遠 STABLE 不了 = 3.3%。
但比率**極不穩定且往上跑**:ch1–17 為 1.6%(7/425),**ch18–20 為 11.2%(10/89)—— 7 倍**。
s1-obe 已排除「併發競爭」解釋(ch19 後段單車獨跑、競爭最低,照樣出病態節),
剩下的假設是文體難度(亞伯拉罕敘事、對話密集、代名詞多)。

⇒ **推論:全本聖經跑完,發散節是數百節量級。** 這條動線必須是一級設計,不是事後補丁。

另有一個反直覺事實:**「發散」不等於「錯」** —— 有兩節(9:16、17:25)首次判定病態,
六天後同機制重跑就收斂了。所以人工複審的產物有時是「選一個」,有時是**「這節其實沒問題,重跑即可」**。
⇒ Verdict 需要一個 `kind: rerun_suggested`(見 §11.5)。

## 11.2 ★ 三種隱形模式 — 完成度絕不能靠「檔案存在」

這是本增補最重要的結論。**兩封信各自只看到一種隱形模式,實際上有三種**,全經實測確認:

| 隱形模式 | 實測 | 掃 gold 目錄的表象 | 偵測判準 |
|---|---|---|---|
| **A. 檔案在,但 `trust_tier: null`** | s10 **56** 節 · s1 **72** 節 | 像正常成品(`lcc_sn` 欄位是**滿的**,舊值或部分結果) | `trust_tier is None` |
| **B. 完全沒有檔案** | s1 那 17 節,**17/17 實測確認無檔** | 表現成「沒跑到」,而它們是**跑最多次**的一批 | 需外部經節普查(§11.3) |
| **C. 檔案被截斷/半寫入** | 掃描當下 **0** 個(已被 s1-obe 的 sweep 清除) | parse 失敗 | **`try/except` on parse** |

**對 C 的判準 — size 不足,必須用 parse 失敗**(結論經 s1-obe 2026-07-26 覆信確認並採納):

信中原建議「try/except + **檔案大小檢查**」。**size-based 偵測會整批漏掉截斷檔** ——
`SIGKILL` 截斷不必然截到 0 bytes,寫到一半的 JSON 可以有數百 bytes 卻 parse 失敗。
⇒ 正確判準是 **parse 失敗**,並**容忍掃描期間檔案出現/消失**。
s1-obe 已將其 sweep 從 `find -size 0` 改為 parse-fail。

> **事實勘誤(showoff-obe 自我修正 2026-07-26)**:本節初稿寫「那個毒檔從來不是 0 bytes,
> 是被截斷的非零檔」—— **這是錯的**。`gold_standard/Gen/19/13.json` 當時**確實是 0 bytes**,
> 由 s1-obe 以 `find -size 0 -print -delete` 掃出並刪除(BSD `find -size 0` 只匹配真正
> 0 bytes,1-byte 檔不匹配,已實測驗證)。它在我前後兩次檢查之間消失是**因為被刪除**;
> 我的 `find -size 0` 掃描發生在刪除**之後**,故掃不到。我從「掃不到」推論「從未是 0 bytes」
> 是未經驗證的推斷 —— 該檔存在時我從未 stat 其大小(當時只知 `json.load` 拋
> `JSONDecodeError`,而 0-byte 檔正是拋這個)。
> 方法結論不受影響,但理由改為上段的「截斷不必然到 0 bytes」。
> 附帶教訓:掃描期間的檔案增刪不只來自 pipeline,**也來自 sibling agent 的清理作業**。

**s10-obe 的警告成立且必須寫入實作規則**:s10 Gen 1–17 檔案數 425/425、每章節數與創世記完全對得上,
看起來 100% 完成,但其中 56 節 `trust_tier` 為 null。若 viewer 用「有沒有檔」或「經文有沒有 SN」
畫完成度,會畫出**一張全綠但不真實的圖**。

## 11.3 因此:必須有外部經節普查(census)

**權威的經節清單不能來自 gold 目錄本身** —— 模式 B 在其中結構性不可見。索引器必須:

1. 從正典經節數(`books.json` / `dim_verse_map.json` 的 31,103 節)取得**應有**的經節全集;
2. 對每節計算 `verse_state`(§11.4),缺檔即 `divergent_or_not_run`;
3. 以 `run_logs/deferred_ch{N}.txt` 與 `run_logs/accept_empty_confirmed.txt` 區分
   「發散(跑過且放棄)」與「單純沒跑」。

**發散節權威清單格式**(已實測):

```
run_logs/deferred_ch18.txt          # sec 在行首,chap 來自檔名
  19  deferred-pathological (per-verse timeout, opus non-convergent)  2026-07-26 04:38
  25  deferred-pathological (per-verse timeout, opus non-convergent)  2026-07-26 05:58

run_logs/accept_empty_confirmed.txt # chap:sec 格式
  1:30  newly-pathological (漏網 verse timed out on first clean run)  2026-07-25 19:29
  8:1   accept-empty CONFIRMED (2nd fresh-quota run, still non-convergent)  2026-07-25 21:03
```

## 11.4 `verse_state` — 新增的一級狀態欄位

加入 `axes.verse_state`,取值如下。**這是熱度圖與完成度統計的唯一依據**:

| 值 | 判定 | 顏色 | 需人工 |
|---|---|---|---|
| `resolved` | `trust_tier` 為 `c_consensus*` | 綠 | 否 |
| `resolved_deliberated` | `trust_tier == "d_deliberation"` | 黃綠 | 值得抽看 |
| `resolved_over_wlc_divergence` | `trust_tier == "c_consensus_over_wlc_divergence"` | 黃 | 值得抽看 |
| `unsettled_blank_ballot` | 檔案在 · `trust_tier` null · R1 有人交白卷 | 橙 | **是**(形態 A) |
| `unsettled_true_divergence` | 檔案在 · `trust_tier` null · 三方皆有答案但不一致 | 紅 | **是**(形態 B) |
| `unsettled_judge_error` | 檔案在 · `trust_tier` null · R3 判官 `error`/`verdict:"unknown"` | 紅 | **是**(形態 C) |
| `divergent_no_file` | 無檔 · 在 deferred/accept_empty 清單中 | 深紅 | **是**(模式 B) |
| `not_run` | 無檔 · 不在任何清單中 | 灰 | 否 |
| `corrupt` | 檔案存在但 parse 失敗 | 紫 | 標示,不掛頁 |

## 11.5 三種形態的實測分佈與各自要看的東西

以 `trust_tier is None` 的節分類(showoff-obe 實測 2026-07-26):

| 形態 | s1 | s10 | 人工要看什麼 | 動線 |
|---|---|---|---|---|
| **A 有人交白卷** | **50** | **54** | 另外兩個模型是否一致?一致即可直接採納(降級為雙數共識) | 兩欄 diff + 第三欄灰掉標「未作答」 |
| **B 三方真發散** | **22** | **1** | A/B/C 三版並排 diff,選一個或自己改 | 三欄 token diff |
| **C 判官掛掉** | 0 | **1**(Gen 6:16) | 另一判官已給完整 pick + reasoning,要不要直接採納 | 顯示健全判官的判決 + 標示掛掉者 |

**交白卷模型分佈(這是配額事故,不是意見)**:
s1 = `opus 46 · agy 12 · codex 2 · gpt-5.4 1 · gemini-3-pro-preview 1`;
s10 = `codex 38 · agy 16`(信中提到 codex 在 Gen 7:6–24 連 19 節、agy 在 Gen 17:15–27 連 13 節整批交白卷)。

⇒ **UI 硬規則**:交白卷的模型必須顯示為**灰掉 + 「未作答」**,
絕不可呈現為「這個模型認為答案是空的」—— 那是配額撞牆,不是判斷。

## 11.6 ★ diff 必須是 token 級,不是並排全文

s1-obe 提供的 Gen 19:2 實例(agy 跑 9 次才在 R2f 勉強 STABLE),前三次 attempt:

```
attempt 1: …請轉到<05493><8798><0413>僕人<05650>家裏<01004>來過夜…
attempt 2: …請轉<05493><8798>到<0413>僕人<05650>家<01004>裏來過夜…
attempt 3: …我主<02009><04994><0113>，請轉到<05493><8798><0413>…
```

**差異全部在 SN token 的邊界位移**:`家<01004>裏` vs `家裏<01004>`、
`轉到<05493><8798><0413>` vs `轉<05493><8798>到<0413>`。漢字一模一樣,只有標記掛在哪個字上不同。

這對 UI 是決定性的:**人眼判這種差異只要幾秒**(「當然掛在『家』上」),模型卻永遠選不定 ——
這正是人機分工的甜蜜點,ROI 極高。**但前提是 viewer 要把差異「指出來」**;
若只並排三段全文,人得逐字掃描找那一個字的位移,幾秒的判斷會變成幾分鐘苦工。

⇒ **硬規則:diff 以 token 為單位(漢字 + 其後綴 SN 串為一個 token),只高亮差異 span。**
這同時確認了 §7.3 / §7.4 既有的 token 級 diff 決定,並將其升為不可妥協項。

## 11.7 對既有章節的修正

| 章節 | 修正 |
|---|---|
| §2.5 join 表 | 「gold 但無 trace」不是唯一缺口;**還有「連 gold 都沒有」的模式 B**,且它結構性地不在任何 gold 掃描結果裡 |
| §5.2 `axes` | 新增 `verse_state`(§11.4);它取代任何以檔案存在為基礎的完成度計算 |
| §5.4 Verdict `kind` | 新增 **`rerun_suggested`**(§11.1:發散≠錯,有時正解是「重跑即可」)。`adjudication` 作為第四種 review type 併入現有 reviewer 機制 |
| §6 adapter 規則 | 新增規則 8:**經節全集來自外部普查,不來自 gold 目錄**;規則 9:parse 失敗與掃描期間檔案增刪皆須容忍(**不可用 size 判毒檔**) |
| §7 viewer 介面 | 新增 §11.8 章層級熱度圖 |
| §10 風險 | 風險 3(活語料競態)升級:實測到檔案在兩次檢查之間**消失**,不只是半寫入 |

## 11.8 新增介面 — 章層級熱度圖(複審者的入口)

- 每節一格,依 `verse_state`(§11.4)上色;格內顯示節號。
- 標題列顯示**真實**完成度:`已定案 N / 待人工 M / 未跑 K`,**絕不顯示「有檔案 X 節」**。
- 點紅/橙/深紅格 → 直接進入對應形態的裁決動線(A/B/C 三種佈局不同,§11.5)。
- 頂層過濾器第一順位:**「只看待人工的節」** —— 這是複審者的第一個動作。
- `corrupt` 格顯示為紫並標「紀錄毀損」,不阻斷整頁。

## 11.9 路徑陷阱 — R1 與 R2 命名不一致(已實測確認)

```
round1_results/{model}/Gen/{chap}/{sec}.json      ← 巢狀目錄
round2_results/{model}/Gen/{chap}_{sec}.json      ← 底線連接
round2_results/{model}/Gen/{chap}_{sec}_convergence.json
round3_results/{model}/Gen/{chap}_{sec}.json
```

這解釋了為何 glob `round1_results/*/Gen/*.json` 掃不到任何檔案。adapter 兩種命名都要處理。

## 11.10 與側車原則的衝突 — 已依 Joshua 拍板解決

s10-obe 信件 §5.4 建議「人工裁決寫成 gold JSON 裡的**新欄位** `human_adjudication`,
不要覆寫 `lcc_sn`」。**此建議與 §4 側車原則衝突,依 Joshua 2026-07-25 拍板不採用。**

但兩者意圖一致,且側車是同一意圖的**更強形式**:
s10-obe 的理由是「`build_gold_standard()`(`consensus.py`)是 gold 的唯一寫入權威,
從旁邊加欄位比較不會打架」—— 正因為它是唯一權威且會以 `--force` 整檔重寫
(§2.7 實測當下就有 3 個 run 在跑),**在該檔案內加欄位仍會被清掉**。
側車存放完全不觸碰該檔案,才真正達成「不打架」。

信中另一項建議「複用既有 reviewer 認證 + review type 機制,發散節裁決作為第四種
review type(`adjudication`)」**採用** —— 與 §8 的 `POST /api/verdicts` 沿用現有 OTP Bearer 一致。

## 11.11 測試節清單(sibling 提供 + 實測校正)

| 節 | 形態 | 特徵 |
|---|---|---|
| s10 `Gen/7/1.json` | A | codex 交白卷,opus/agy 兩版一致 → 可直接採納的典型 |
| s10 `Gen/17/15.json` | A | agy 交白卷 |
| s10 `Gen/6/16.json` | **C** | 判官 CLI error(`verdict:"unknown"`, `error:true`),另一判官有完整 pick + reasoning |
| s10 `Gen/8/21.json` | **B** | s10 唯一的三方真發散 |
| s10 `Gen/6/17.json` | 已解 | `d_deliberation`;codex trace 有 **31 個 attempt**(震盪回放的極端案例) |
| s10 `Gen/1/1.json` | 已解 | `c_consensus`,正常對照組 |
| s1 `Gen/19/2.json` | **模式 B** | 無檔;agy 跑 9 次 R2f 勉強 STABLE;§11.6 的 token 位移實例 |
| s1 那 17 節 | 模式 B | `1:30 7:13 8:1 8:21 9:2 9:5 17:23 18:19 18:25 19:2 19:8 19:14 19:15 20:3 20:7 20:16 20:18` |

## 11.12 分期調整

**本增補全部併入 Phase 1** —— 資料全在磁碟上,零 token 成本,且這是 Joshua 直接指示的需求。
`verse_state` + census + 熱度圖是 Phase 1 的**前置**(沒有它,完成度統計是錯的),
優先於 §7.3 的 N-way 裁決台。
