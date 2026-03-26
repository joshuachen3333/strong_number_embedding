# survey5_bilingual_sn_benchmark/ — 雙語 SN 基準測試

## 概念起源

### Survey4 的問題

Survey4 要求模型從純 UNV 文字「生出」SN tags — 這等於要模型背 13,000+ 條 Strong's Dictionary。即使 deepseek-671B 也只有 cov=0.12。

根本原因：**模型不知道每個中文字對應哪個 SN 號碼**。模型的價值在於「放置」(placement)，不在於「查字典」(dictionary lookup)。

### Survey1 為什麼成功

Survey1 (UNV+SN → LCC+SN) 之所以能用，是因為 **SN 號碼已經在輸入裡了**。模型看到 `神<WH0430>` 就知道要搬 `<WH0430>` 到 LCC 的「上帝」後面。模型做的是中文↔中文語義配對，SN tags 只是跟著走的「行李」。

### Survey5 的設計

同樣的邏輯，但用 **KJV（英文）↔ UNV（中文）** 做跨語言測試，而且兩邊都有 FHL ground truth！

```
Survey1（生產）: UNV+SN → LCC+SN    ← 沒有標準答案
Survey5（測試）: KJV+SN → UNV+SN    ← 有標準答案！
                 UNV+SN → KJV+SN    ← 也有標準答案！
```

**Survey5 是 Survey1 的鏡像測試**：技能相同（跨語言 SN placement），但有自動評分。

## 主任務與輔助任務

### 主任務：KJV+SN → UNV+SN

```
Input (same verse, all three):
  KJV:    In the beginning God created the heaven and the earth.
  KJV+SN: In the beginning<WH07225> God<WH0430> created<WH01254><WTH8804>
          {<WH0853>}the heaven<WH08064>{<WH0853>}and the earth<WH0776>.
  UNV:    起初，神創造天地。

Task: 把 KJV 的 SN tags 搬到 UNV 對應位置

Expected output:
  起初<WAH09002><WH07225>，神<WH0430>創造<WH01254><WTH8804>
  {<WH0853>}天<WH08064>{<WH0853>}地<WH0776>。

Ground truth: FHL 的 UNV+SN（自動評分）
```

KJV plain + KJV+SN 是這一節的「標注鑰匙」— 讓模型看到哪個英文詞對應哪個 SN，再搬到 UNV。

模型的思考：
- KJV: `beginning` → KJV+SN: `beginning<WH07225>` → UNV: 起初 → `起初<WH07225>` ✓
- KJV: `God` → KJV+SN: `God<WH0430>` → UNV: 神 → `神<WH0430>` ✓
- KJV: `created` → KJV+SN: `created<WH01254><WTH8804>` → UNV: 創造 → `創造<WH01254><WTH8804>` ✓

### 輔助任務：UNV+SN → KJV+SN（反向）

```
Input (same verse, all three):
  UNV:    起初，神創造天地。
  UNV+SN: 起初<WAH09002><WH07225>，神<WH0430>創造<WH01254><WTH8804>...
  KJV:    In the beginning God created the heaven and the earth.

Task: 把 UNV 的 SN tags 搬到 KJV 對應位置

Ground truth: FHL 的 KJV+SN（自動評分）
```

### 反向的診斷價值

| 情況 | 正向 (KJV→UNV) | 反向 (UNV→KJV) | 說明 |
|------|----------------|----------------|------|
| 兩邊都高 | 0.85 | 0.82 | 模型真的懂跨語言對齊 ✅ |
| 正向高反向低 | 0.85 | 0.30 | 擅長讀英文寫中文，反向不行 |
| 正向低反向高 | 0.30 | 0.80 | 擅長讀中文寫英文 |
| 兩邊都低 | 0.20 | 0.15 | 跨語言能力不足 |

反向 (UNV→KJV) 跟 Survey1 (UNV→LCC) 結構完全一樣 — 都是從 UNV+SN 出發搬到另一個文本。反向測試 = **用 KJV 驗證 survey1 核心能力，且有標準答案**。

## SN 數量不一致問題（Critical）

### 問題

同一節經文，KJV+SN 和 UNV+SN 的 SN 個數**可能不同**：

```
KJV Gen 1:1: 10 個 SN tags
UNV Gen 1:1: 12 個 SN tags（UNV 多了 WAH09002 等 900x prefix）
```

原因：
- UNV 有 900x prefix 系統（ב→09002, ל→09001），KJV 可能沒有或格式不同
- 某些 implicit markers 在 KJV/UNV 中的處理方式不同
- FHL 的 KJV+SN 和 UNV+SN 標注細度可能有差異

### 處理策略

1. **預分類**：掃描全聖經，把每節的 KJV SN 數量和 UNV SN 數量都算出來
2. **分三組**：
   - **一致組**：KJV SN 數 = UNV SN 數 → 最適合測試
   - **接近組**：差異 ≤ 2 → 可測但需注意
   - **差異組**：差異 > 2 → 先不測，或特殊處理
3. **Exemplar Library**：優先選一致組的經節

### 預處理腳本（待實作）

```bash
python3 scan_sn_mismatch.py --book 創 --chap 1-50
# 輸出每節的 KJV SN 數、UNV SN 數、差異
```

## 與 Survey4 的關係

### 26 dims 能否沿用？

部分可以：
- **共用 dims** (#1-4, #6-9, #13-14, #17, #19-22, #25)：格式/位置規則不分語言
- **OT-specific dims** (#5, #10, #15-16, #18, #23-24)：UNV 端適用，KJV 端需驗證
- **NT-specific dim** (#26 字母後綴)：KJV 可能也有

可能需要**新增 KJV-specific dims**：
- KJV 斜體字 `<FI>...<Fi>`（FHL 格式）
- KJV 的 SN tag 格式差異

### Exemplar Library 能否擴展合併？

Survey4 的 Exemplar Library 是 UNV-only 的。Survey5 需要：
- 每個 exemplar 附帶 KJV+SN 版本
- 新增 SN 數量一致性欄位
- 可以**擴展** survey4 的 library，不需要重建

## 同構對比

| | Survey1 | Survey4 | Survey5 |
|---|---|---|---|
| 輸入 | UNV+SN + LCC(plain) | UNV+SN(v1) + UNV(v1) + UNV(v2, plain) | KJV(plain) + KJV+SN + UNV(plain) |
| 輸出 | LCC+SN | UNV+SN(v2) | UNV+SN |
| SN 來源 | UNV (給了) | UNV(v1) (給了，但 v2 要自己推) | KJV+SN (給了，同節) |
| Ground truth | 無 | FHL UNV+SN(v2) | FHL UNV+SN |
| 評分 | 3-model consensus | 自動 | 自動 |
| 測的能力 | 跨語言放置 | 格式學習 + SN 推斷 | **跨語言放置** |
| 成本 | 昂貴 (3 model) | 便宜 | 便宜 |

**Survey5 = Survey1 的廉價鏡像測試。** 同樣的能力，有標準答案，自動評分。

## Pipeline 設計（草案）

```
scan_sn_mismatch.py → 分類 (一致/接近/差異)
        ↓
build_exemplar_library_v5.py → 從一致組選候選
        ↓
round_robin_v5.py → KJV+SN 為 example, UNV 為 test
        ↓
auto_score.py → 比對 FHL UNV+SN ground truth
        ↓
(反向) round_robin_v5.py → UNV+SN 為 example, KJV 為 test
        ↓
auto_score.py → 比對 FHL KJV+SN ground truth
```

## 可複用的 Survey4 資產

| Survey4 資產 | Survey5 能用？ |
|-------------|--------------|
| `dim_verse_map.json` | ✅ dims 適用（加 KJV SN 數量） |
| `analyze_test_dimensions.py` | ✅ 擴展支援 KJV |
| `auto_score.py` | ✅ 直接用 |
| `compare_models.py` | ✅ 直接用 |
| `sample_test_set.py` | ✅ 加 SN 一致性過濾 |
| `exemplar_library.json` | 🔄 擴展加 KJV 欄位 |
| `prompts/survey4_v0.1.md` | ❌ 需重寫（任務不同） |

## run_logs/ 命名格式

統一格式：`{task}_{scope}_{model}_{prompt}_{YYYYMMDD_HHMMSS}.{ext}`

| 欄位 | 說明 | 範例 |
|------|------|------|
| task | fwd (KJV→UNV) / rev (UNV→KJV) | `fwd`, `rev` |
| scope | 書卷+章節 | `gen1`, `gen1_3` |
| model | 短名 | `ds671b`, `sonnet`, `qwen32b` |
| prompt | 版本號 | `v0.1`, `v0.2` |
| timestamp | YYYYMMDD_HHMMSS | `20260327_002205` |
| ext | log (stdout) / json (結果) | `log`, `json` |

範例：
- `fwd_gen1_ds671b_v0.1_20260327_002205.log`
- `rev_gen1_sonnet_v0.1_20260327_010000.json`

`--out` 用法：
- `--out` (無值) → 自動生成檔名
- `--out path/to/file.json` → 指定路徑
- 不加 `--out` → 不存檔

## Status

- [x] 概念設計
- [ ] `scan_sn_mismatch.py` — KJV/UNV SN 數量對比掃描
- [ ] Survey5 專用 prompt
- [ ] Exemplar Library 擴展（加 KJV）
- [ ] 主任務 benchmark (KJV→UNV)
- [ ] 反向 benchmark (UNV→KJV)
