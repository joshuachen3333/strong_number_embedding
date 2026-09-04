# `Alignments/` — 外部原文與對齊語料的取得說明

`llm_direct_sn_unv2notyet/Alignments/` **不在本 repo 裡**（`.gitignore:70` 排除，本機約 1.0 GB）。
它是 Clear Bible 的公開對齊語料，被 clone 進來當作原文真值層使用。這份文件記錄它從哪來、
我們用到哪幾個檔、以及重建時的注意事項 —— 沒有這份記錄，換機器後沒有人知道該去哪裡拿。

## 來源

| 項目 | 值 |
|---|---|
| Repo | <https://github.com/Clear-Bible/Alignments> |
| 授權 | CC BY 4.0（對齊資料由各方提供並持有版權） |
| 本機 pinned commit | `c99bd0a`（2026-05-11，"from Rick: split gloss2 values"） |
| 本機取得日 | 2026-06-18 |

它自己是一個獨立的 git repo（巢狀 clone），所以 `git -C Alignments log` 隨時可查目前停在哪個 commit。

> **延伸**：[`TEXT_ALIGN_SURVEY.md`](TEXT_ALIGN_SURVEY.md)（2026-08-25 實測）記錄這批 TSV
> 的逐欄解剖 —— WLC vs WLCM 的 13,506 筆 SN 分歧、`gloss2` 在三個檔裡是三種語義、
> `WLCM+required.tsv` 的 strongs 欄已被 G-prefix bug 固化、以及 `BibleAquifer/text-align`
> 這套工具鏈怎麼用它們。本文管「從哪來、讀哪幾個」，那份管「長什麼樣、怎麼咬人」。

## 重建

全 clone 約 1.0 GB，但我們實際只用到 **221 MB**。若磁碟或頻寬吃緊，用 sparse checkout：

```bash
cd llm_direct_sn_unv2notyet
git clone --filter=blob:none --sparse https://github.com/Clear-Bible/Alignments
cd Alignments
git sparse-checkout set data/sources data/eng/targets data/eng/alignments
git checkout c99bd0a          # 對齊本機版本；要跟上游就省略這行
```

不介意大小就直接 `git clone https://github.com/Clear-Bible/Alignments`。

## 誰在用

讀這份語料的是 **survey5 / survey10 / survey13**。**主驅動 `llm_direct_sn_unv2notyet.py`
本身不讀 `Alignments/`** —— 它跑創世記以外的書卷不受本文件任何限制影響（mainobe 2026-08-08
實跑利 1:1–3 正常）。

## 我們實際讀的檔

| 檔案 | 大小 | 用途 | 誰讀 |
|---|---|---|---|
| `data/sources/WLC.tsv` | 35.1 MB | 舊約希伯來原文 + Strong's | `run_stage2_harsh.load_wlc_verse` → `wlc_check` / `english_bridge` |
| `data/sources/SBLGNT.tsv` | 10.5 MB | 新約希臘（critical，≈NA28/UBS 家族） | `english_bridge`（A2 NT 預設） |
| `data/sources/BGNT.tsv` | 8.2 MB | 新約希臘（Byzantine／公認經文傳統） | `english_bridge`（`--nt-source BGNT`） |
| `data/eng/targets/BSB/ot_BSB.tsv` · `nt_BSB.tsv` | 18.4 + 5.8 MB | Berean Standard Bible 英文（現行 A2 基準） | `english_bridge.SOURCES["BSB"]` |
| `data/eng/targets/YLT/ot_YLT.tsv` | 25.2 MB | Young's Literal（貼希伯來語序，凸顯前綴質詞） | `english_bridge.SOURCES["YLT"]` |
| `data/eng/alignments/BSB/WLCM-BSB-manual.json` | 40.9 MB | 舊約↔BSB 人工對齊 | `english_bridge` |
| `data/eng/alignments/BSB/SBLGNT-BSB-manual.json` | 15.3 MB | 新約↔BSB 人工對齊（critical） | `english_bridge` |
| `data/eng/alignments/BSB/BGNT-BSB-manual.json` | 13.3 MB | 新約↔BSB 人工對齊（Byzantine） | `english_bridge` |
| `data/eng/alignments/YLT/WLC-YLT-manual.json` | 48.0 MB | 舊約↔YLT 人工對齊 | `english_bridge` |

## 三個會咬人的地方

**1. `WLCM.tsv` 不能拿來當原文載入。** 它的 schema 和 `WLC.tsv` 不同，`_bridge_number`
解不出 Strong's（會把每個 SN 都丟掉）。`WLC.tsv` 與 `WLCM.tsv` 在創世記約 99.3% 的 morph
共用 id，所以**原文一律載 `WLC.tsv`**，只有對齊檔那一側才用 `WLCM-BSB-manual.json`
（名字帶 WLCM 是因為對齊本來就是對 WLCM id 做的）。剩下 ~0.7% 分歧的 morph 拿不到 BSB
gloss，但 SN 清單——也就是被評分的內容——不受影響。詳見 `english_bridge.py` 的 SOURCES 註解。

> **這個混搭只在自己讀檔時成立。** `english_bridge.py` 直接開 tsv / json，所以能一邊載
> `WLC.tsv`、一邊用 `WLCM-BSB-manual.json`。若改用 Clear Bible 的 `bible_alignments`
> 套件就做不到 —— `AlignmentSet` 的 `sourceid` 同時決定 `sourcepath` 與 `alignmentpath`，
> 兩者綁死。而該套件的 Manager 讀 WLCM 時會把無前綴的 strongs 一律補 `G`，H/G 判別直接毀損。
> （s13obe 實測，詳見 `survey13_unv_sn_to_burrito/FHL_900X_FINDINGS.md`。）
>
> **2026-08-25 追認**：這個 G-prefix bug 不只在套件裡 —— `Alignments/data/sources/`
> 底下的 `WLCM+required.tsv` 已經把 467,770 筆希伯來 Strong's **寫死成 `G0871a`/`G7225`**，
> 是 Clear 自己跑過那支 loader 再寫回磁碟發佈的產物。該檔 strongs 欄請直接當毀損看待。
> `BibleAquifer/text-align` vendored 的 `burrito/source.py:85` 同樣是
> `prefix = "G" if is_nt else "G"`，原封不動。詳見 `TEXT_ALIGN_SURVEY.md` §D-1。

**2. 書卷對應表：已修好，但要知道它壞掉時的樣子。**

`run_stage2_harsh.CHI_TO_WLC_BOOK` 原本是手打的 `{"創": "01"}`（39 卷裡只有 1 卷）。
危險之處在於**未 map 的書卷不會報錯** —— `wlc_check()` 回 `{"status": "no_signal"}`，
那一節安靜地失去原文 identity 軸，跑出來的結果看起來正常、其實從沒被檢查過。

2026-08-08 起改為從 `shared/data/books.json` 前 39 筆自動建表（`survey5/wlc_bridge.py:26`
早就是這個寫法）。實測 `wlc_check('利', 1, 1, …)` 由 `no_signal` 變成 `match` / coverage 1.0，
創世記無回歸。新約仍不在此表（`CHI_TO_SBL_BOOK` 才是，見坑 3）。

新寫任何「書卷 → 編號」的對應時，一律從 `books.json` 導出，不要手打。

**3. 新約還沒有對應的 identity check。** `wlc_check.py` 的內臟是希伯來專用的：希臘文沒有
09xxx 那類不可分前綴、`_bridge_number` 照希伯來 lemma/strongs/pos 解、`build_exclusion`
的 family sets 也是舊約的。新約要進 gold 產線需要一支平行的 `gnt_check`，共用同一組三態
契約（`match` / `divergence` / `no_signal`），內臟另寫。資料層（SBLGNT/BGNT + BSB 對齊）
已經備妥且 A2 線證明讀得出來，不是從零開始。
