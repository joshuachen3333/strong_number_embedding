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
**Example for Gen 1:1:**

<09002><07225> — 介系詞片語「起初」
<0430> — 名詞「神」
<01254>(8804) — 動詞「創造」 *1
<0853> — 受詞記號
<08064> — 名詞「天」
<0853> — 受詞記號
<0776> — 名詞「地」

起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>{<WH0853>}天<WH08064>{<WH0853>}地<WH0776>。

---
**Morphology Notes:**
*1: 動詞，Qal 完成式 3 單陽 (Verb, Qal Perfect 3rd ms)