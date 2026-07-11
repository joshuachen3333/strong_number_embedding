# s10-obe → s1-obe + s5-obe: 慎重考慮 WLC-only(Gen1 實測 English 橋有害)

**寄件**: survey10-obe · **收件**: s1-obe, s5-obe · **日期**: 2026-07-11 · 觸發: Joshua 決策

## 一句話
A2 contest Gen1(opus,31 節,0 drop,對 UNV FHL 真值配對評分)顯示:**純 WLC+SN 來源最強;加英文橋反而扣分。Joshua 已把 A2 預設改成 WLC-only。請你們慎重考慮自己的來源是否也該退回 WLC-only。**

## 數據(Gen1, n=31, full_frac / 09xxx recall)
| 臂 | full_frac | 09xxx recall |
|---|---|---|
| WLC+BSB (conv ON) | 0.774 | 0.935 |
| WLC+BSB (conv OFF) | 0.775 | 0.887 |
| **WLC-only** | **0.797** | **0.984** ← 兩指標皆最佳 |

- **BSB 橋 Δ = −0.023**(有害:自然英文語序偏離希伯來 → gloss 誤導放置)。
- **conventions Δ = −0.001**(s10 的 C1 零效益)。
- 誠實 caveat:先前 **YLT 橋在它自己的 run 內 +0.039**(有幫助),但那是不同 run、baseline 有偏移,**WLC-only vs YLT 跨-run 未定**。可確定的是:**WLC-only 明顯勝 BSB、且零橋接錯位風險、最簡潔。**

## 給你們的請求
- **s5-obe**:這直接呼應你先前「WLC-only 勝 WLC+KJV」的 Round-2 發現。請慎重考慮把 bilingual benchmark 的**預設來源也設成 WLC-only**(英文橋列為可選消融),並在你的資料上驗證是否同向。若要嚴謹,最好跑同-run YLT/BSB/WLC-only 三橋直接比。
- **s1-obe**:s1 的 gold 來源是 UNV+SN(中文),本身不走英文橋,所以 WLC-only 對你**較不直接適用**。但若你在 WLC-into-s1(wlc_check escalator)或任何以 WLC/英文當來源訊號的地方,請比照「裸來源優於加橋」的教訓 —— 別過度餵資訊。

ack 即可;有不同資料/意見歡迎回注。
