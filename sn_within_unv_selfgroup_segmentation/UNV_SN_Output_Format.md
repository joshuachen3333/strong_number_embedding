---
**Parsed and Raw UNV+SN Output Specification:**

This output format consists of three main sections: the parsed and formatted text, the raw UNV+SN source text, and a morphology notes section.

**I. Parsed and Formatted Text Section:**

*   Each significant linguistic unit (Strong's number, grouped Strong's numbers) is presented on a new line.
*   **Individual Strong's Numbers:**
    *   Format: `<Strong's Number> — [詞性]「[中文意義]」`
    *   Example: `<0430> — 名詞「神」`
*   **Strong's Numbers with Morphology Codes:**
    *   Format: `<Strong's Number>(Morphology Code) — [詞性]「[中文意義]」 *N`
    *   `*N` is a sequential reference number (e.g., `*1`, `*2`) pointing to a detailed explanation in the "Morphology Notes" section.
    *   The "詞性" (Word Type) and "中文意義" (Chinese Meaning) are derived from the `wform` and `exp` fields of the `qp.php` response, respectively.
    *   Example: `<0559>(8799) — 動詞「說」 *1`
*   **Grouped Strong's Numbers (e.g., brace prepositions):**
    *   Format: `<Strong's Number 1><Strong's Number 2> — [詞性]「[中文意義]」`
    *   Individual Strong's number tags are concatenated without any additional outer brackets `<<...>>`.
    *   Example: `<04480><08478> — 介系詞「從…之下」`

**II. Raw UNV+SN Source Text Section:**

*   This section contains the original `bible_text` string as retrieved from the `qb.php` API, including all `WH`, `WTH`, `WAH` prefixes.

**III. Morphology Notes Section:**

*   This section appears at the very end of the output, after the raw UNV+SN text.
*   It lists the detailed grammatical information for each morphology code referenced in the parsed text.
*   Format: `*N: [Detailed description from the wform field of qp.php]`
    *   Example: `*1: 動詞，Qal 完成式 3 單陽 (Verb, Qal Perfect 3rd ms)`

---
**Example for Gen 1:9:**

<0430> — 名詞「神」
<0559>(8799) — 動詞「說」 *1
<08064> — 名詞「天」
<04480><08478> — 介系詞「從…之下」
<04325> — 名詞「水」
<06960>(8735) — 動詞「聚集」 *2
<0413> — 介系詞「向／到」
<0259> — 形容詞「一」（數目的「一」）
<04725> — 名詞「地方／處」
<03004> — 名詞「旱地」
<07200>(8735) — 動詞「顯現／被看見」 *3
<03651> — 副詞「這樣／如此」
<01961>(8799) — 動詞「成為／是」 *4

神<WH0430>說<WH0559><WTH8799>：「天<WH08064>下<WAH04480><WAH08478>的水<WH04325>要聚<WH06960><WTH8735>在<WH0413>一<WH0259>處<WH04725>，使旱地<WH03004>露出來<WH07200><WTH8735>。」事就這樣<WAH03651>成了<WAH01961><WTH8799>

---
**Morphology Notes:**
*1: 動詞，Qal 敘述式 3 單陽 (Verb, Qal Narrative 3rd ms)
*2: 動詞，Nif‘al 祈願式 3 複陽 (Verb, Niphal Jussive 3rd mp)
*3: 連接詞 וְ + 動詞，Nif‘al 祈願式 3 單陰 (Conjunction + Verb, Niphal Jussive 3rd fs)
*4: 動詞，Qal 敘述式 3 單陽，短型式 (Verb, Qal Narrative 3rd ms, short form)