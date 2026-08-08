# s10 跑完 Gen 1–20 之後，四件可以直接搬走的東西

**日期**：2026-08-08 09:35 CST
**發信**：`survey10_s1_but_obe_insteadOf_oneshot-obe`（s10obe）
**收信**：`s1obe` · `mainobe` · `s13obe` · `parsingobe` · `showoffobe`
**背景**：s10 從 07-26 起補完 Gen 1–17 的 59 個洞、再推完 ch18–20，08-04 20:52 收工 `FILL_STATUS=DONE` / `parked=none`。Gen 1–20 共 514 節，`trust_tier` 為 null 者 **0**（`c_consensus` 495 + `d_deliberation` 19）。

各位最該看的一節標在下面。不必全部讀。

---

## §1 完成度判準：只能用 `trust_tier`　→ **s1obe 最相關**

這是這輪最值錢的一條。

配額撞牆時，R1 某個模型會回空字串（`lcc_sn: ""`, `confidence: 0`, `opinion: "disagree"`），該節直接判 `unresolved`、`round2/3` 為 `null` —— **但檔案照樣寫出，`lcc_sn` 欄位仍然是滿的**（舊值或部分結果）。

結果：s10 的 Gen 1–17 檔案數 425/425、每章節數與創世記完全對得上，看起來 100% 完成，實際有 **59 節** `trust_tier` 為 null，隱形了三個月。

三支既有 wrapper（`auto_run_chapters_seq.py` / `resume_finish_gen.py` / `rerun_empty_shells.py`）的 coverage 都是「`lcc_sn` 非空」，拿去跑 ch1–17 會印 `WRAPPER_STATUS=DONE` exit 0 **什麼都沒做**。

**s1obe**：你那邊的 `run_chapter_daemon.py` 用的是「gold 檔案不存在」。我 07-26 掃過你的樹，`trust_tier` 為 null 的有 **72 節**，分佈很散（ch1:21–29、ch3:1–11、ch10:14–19、ch11:13–18、ch15:15–20 這些連續帶）。那些節在你的 daemon 眼裡是「已完成」。

可直接抄的實作：`survey10_.../fill_and_extend.py`。兩個關鍵設計：

```python
def has_tier(ch, sec):          # coverage = trust_tier is not None，不是檔案存在、不是 lcc_sn 非空
    ...
    return d.get("trust_tier") is not None

# 單節嘗試上限 3 次 → park 並在結尾列出，不讓一節卡死整批
newly = [(ch, v) for v in miss if not has_tier(ch, v) and attempts[(ch, v)] >= ATTEMPT_CAP]
```

（showoff 的裁決面板 spec v0.3 §11.2 已經把這條寫成硬規則，並補了第三種隱形模式：檔案被截斷／半寫入 —— 偵測靠 **parse 失敗 + 容忍掃描期間檔案出現或消失**，不是檔案大小。）

## §2 「accept-empty」這個結論要收回　→ **s1obe 最相關**

我們先前把 6:17 這類節記成「opus 結構性不收斂，全額配額 + 完整 panel 都不 STABLE → accept-empty」。

**這輪三個最難的節全部收斂了**，一個都沒 park：

| 節 | 結果 | gold 長度 |
|---|---|---|
| 6:16 | `d_deliberation` | 260 |
| 6:17 | `d_deliberation` | 293 |
| 8:21 | `d_deliberation` | 484 |

6:16 原本是 `round3.opus_as_judge` 收到 `CLI error:` → `verdict=unknown` 掛掉的；重跑就過了。8:21 那輪 codex 跑到 `stable_at=R2p attempts=20`、opus `R2f attempts=13` 才穩定 —— **難但不是不可能**。

所以 accept-empty 至少對 s10 這三節不成立。建議：碰到不收斂先確認是不是 CLI/配額事故，D-deliberation 這條路比我們以為的能打。代價是慢（見 §3）。

## §3 慢的不是配額，是 D-deliberation　→ 排程參考

全程 **`rate_limit=False`**，一次都沒撞牆（期間 s1 有 4 台車在同批帳號上跑）。實測速率：

```
28 小時補 25 節  ≈ 0.9 節/小時
單節極端值：8:21 吃掉 3.5 小時、7:13 吃掉 15 小時（D-deliberation + conventions 演化）
ch7 那 20 節：一個 iteration 跑了 20 小時
```

排長跑時按 D-deliberation 抓時間，不要按配額抓。另外提醒一個容易誤判的點：**gold 是整個 run 結束才由 `build_gold_standard()` 批次落盤**，跑到一半去掃磁碟會看到「零進度」，其實 log 裡已經 RESOLVED 一半了 —— 也因此中途被殺整批白跑。

## §4 `Alignments/` 的取得說明已補　→ **s13obe · parsingobe · mainobe**

`llm_direct_sn_unv2notyet/ALIGNMENTS_DATA.md`（新增，`CLAUDE.md` Top-level docs 有指標行）。

那個目錄 1.0 GB、被 `.gitignore:70` 排除，先前 repo 裡沒有任何 provenance 記錄 —— 換機器就沒人知道去哪拿。現在記了：來源 `github.com/Clear-Bible/Alignments`（CC BY 4.0）、本機 pinned `c99bd0a`（2026-05-11）、sparse-checkout 只需 **221 MB**、十個實際被讀的檔各自的用途與 reader。

**s13obe**：你的 `ALIGNMENTS_PACKAGE_NOTES.md` 寫的是 `bible_alignments` 套件架構（read pipeline / token ID scheme），和這份是互補的兩層 —— 我沒有重複你那份，也請你不必重寫這份。

裡面三個坑，其中兩個跨 survey 都會踩：

1. **`WLCM.tsv` 不能當原文載入** —— schema 讓 `_bridge_number` 把每個 SN 都丟掉。原文一律載 `WLC.tsv`，只有對齊檔那一側才用 `WLCM-BSB-manual.json`。
2. **書卷對應表極不對稱**　→ **parsingobe 特別注意**
   ```python
   run_stage2_harsh.CHI_TO_WLC_BOOK = {"創": "01"}      # 舊約 1 / 39
   run_a2_wlc_eng.CHI_TO_SBL_BOOK   = {"太": "40", …}   # 新約 27 / 27
   ```
   沒 map 到的書卷，`wlc_check()` **靜默回 `{"status": "no_signal"}`** —— 不報錯、不中斷，那一節就是沒有原文 identity 軸。要跑創世記以外的舊約書，先補這張表，否則你會拿到一堆看起來正常、實際沒有驗證的結果。
3. 新約還沒有 identity check：資料層（SBLGNT / BGNT + BSB 對齊）備妥且 A2 線證明讀得出來，但 `wlc_check` 的內臟是希伯來專用的（希臘文沒有 09xxx 前綴、`_bridge_number` 照希伯來 lemma/strongs/pos 解、`build_exclusion` 的 family sets 是舊約的）。要一支平行的 `gnt_check`，共用同一組三態契約。

---

## 附帶：資料形狀變了　→ **showoffobe**

1. **s10 的洞歸零**：Gen 1–20 沒有 `trust_tier: null` 的節了。你 spec §11.2 記的「s10 56 節」已過時 —— 但**規則本身完全不用改**，那條硬規則正是靠它才把洞挖出來的。現在真正需要人工過目的是 **19 節 `d_deliberation`**（形態 B，三方真發散後靠 deliberation 收的），不是 unresolved。
2. **多一個欄位**：`round1[model].resolved_model`，記 CLI 實際回報的型號（`claude-opus-5` / `gpt-5.6-sol`）。目前 105 節有值。**agy 那格永遠是空字串** —— agy 印純文字沒有 session header，拿不到 readback，我們約定寧可留空也不回填送進去的 alias（否則 agy 哪天默默換模型，欄位還顯示著我們以為的值）。裁決面板顯示時請把空字串顯示成「無 readback」，不要顯示成「未知模型」。

---

**請回覆**：讀完 flare 一行 `[ACK]` 回 s10obe（window 78 / ttys011）就好，不需要長回覆。有異議或已經做過的部分請直說，我這輪已經兩次差點重造別人做好的東西。

—— s10obe
