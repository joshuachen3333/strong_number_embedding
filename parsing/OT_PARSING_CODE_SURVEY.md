# OT Parsing-Code Survey — how (non-)standardized is FHL's Hebrew `wform`?

> Companion to [`PARSING_FOUNDATIONS.md`](PARSING_FOUNDATIONS.md) (§2 parsing code,
> §6 insertion rules) and [`QP_ENRICHMENT_PLAN.md`](QP_ENRICHMENT_PLAN.md) (S3 OT/NT asymmetry).
> Reproduce: `python3 parsing/ot_parsing_code_survey.py` (offline; reads
> `original_text_preparation/source_sqlite/bible_parsing.db`, no API/token cost).
> Data snapshot: DB dated 2025-11-13; survey run 2026-07-18.

## TL;DR

The hearsay is **confirmed and quantified**: FHL's **NT** parsing code is a tight,
closed, machine-ready tagset; the **OT** parsing code is an open-ended Chinese *prose*
field that carries editorial notes, textual-apparatus talk, and non-exportable Hebrew
internal codes. NT is consumable as-is; **OT must be normalized before it can be a
rule-decidable signal**.

| | **NT** (`fhlwhparsing`) | **OT** (`lparsing`) |
|---|---|---|
| morphemes | 152,227 | **331,800** (39 books) |
| distinct `wform` | **776** (a bounded tagset) | **10,263** |
| avg length | 2.5 chars | 16.1 chars |
| charset | 94.6% pure `^[a-z0-9]+$` (`aai3s`, `gsf`…) | **93.0% Chinese** |
| empty `wform` | — | **23,159 = 7.0%** |

NT `wform` is Robinson/MorphGNT-style (`aai3s` = aorist-active-indicative-3rd-singular):
776 codes cover the whole NT — a **closed vocabulary**, directly convertible to `V-AAI-3S`.
OT has no such closure.

## The five non-standardization patterns in OT `wform`

### 1. Legacy embedded internal-code fragments `12<code>21` — 33.2% of rows
110,322 rows carry ≥1 fragment; **1,457 distinct** fragment tokens. The `12…21` are
sentinel delimiters wrapping a transliterated Hebrew particle/word — the **non-exportable
"中文內碼"** flagged in the FHL discussion (PARSING_FOUNDATIONS §4). Top fragments:

| fragment | count | what it is |
|---|---|---|
| `12;h21` | 30,411 | article הַ (ha-) |
| `12>w21` | 29,507 | conjunction וְ (vav) |
| `12.l21` | 19,931 | preposition לְ (le-) |
| `12.B21` | 15,731 | preposition בְּ (be-) |
| `12!im21` | 6,953 | preposition מִן (min) |
| `12hwhy21` | 5,998 | **YHWH** (יהוה, transliterated RTL as `hwhy`) |

So a real value looks like `連接詞 12>w21 + 冠詞 12;h21 + 名詞，陽性複數` — Chinese POS
words **interleaved with raw internal codes**. Any consumer must strip `12…21` first.

### 2. Editorial prose leaks into the "code" field — sentence-like text, not codes
The field sometimes holds **explanatory sentences**, not morphology:
- `這是馬所拉學者把讀型…` ("this is the Masoretic qere reading…") — 6,815 rows
- pausal-form talk `…的停頓型` — 7,971 rows
- qere/ketiv apparatus `讀型`/`寫型` — ~8,300 each; `把讀型` 7,109
- marker-words `受詞記號` (object marker) 8,723; `段落符號` (paragraph mark) 3,125

~**8,310 rows (2.5%)** contain sentence-like editorial prose (`這是`/`學者`/`按照`/`這個字`).

### 3. Mixed delimiters & whitespace noise
Fullwidth `，` in 238,369 rows **but** halfwidth `,` in 3,483; morpheme-join `+` in
125,568; double-space in 1,423; trailing-space in 163. No single enforced separator.

### 4. Binyan spelled with a curly okina `‘` (U+2018), long rare tail
`Qal` 50,105 · `Hif‘il` 9,265 · `Pi‘el` 6,437 · `Nif‘al` 4,089 · `Hitpa‘el` 828 …
down to `Histaf‘el` 169, `Hitpo‘lel` 105, `Hitpal‘pel` 12 — Latin binyan names embedded
in the Chinese, using a typographic left-quote (not ASCII `'`), which breaks naive matching.

### 5. POS is not a closed vocabulary — 91 distinct leading tokens
62k `名詞` / 60k `動詞` / 55k `介系詞` lead cleanly, but **77 of 91** leading tokens fall
outside a clean POS set (`受詞記號`, `這是馬所拉學者把讀型`, `的停頓型`, `段落符號`,
`否定的副詞`, `連接詞或副詞`, `與下一個字分成兩個字是寫型`…). The POS slot itself drifts.

### Consequence: one lemma → hundreds of distinct `wform`
E.g. SN 00935 (בּוֹא) has **312 distinct `wform` over 2,570 occurrences**. Much is
legitimate inflection, but prefix-stacking (#3) + fragment embedding (#1) + apparatus
prose (#2) inflate the surface variety far beyond the true morphological space.

## Why this matters for our work

- **NT**: `wform` is usable **as-is** as a rule-decidable morphology signal (bounded 776-code
  tagset). This is the easy side.
- **OT**: `wform` needs a **normalization pass** before it can anchor insertion decisions —
  (a) strip `12…21` internal-code fragments, (b) split editorial/apparatus prose off the
  morphology core, (c) normalize delimiters + okina, (d) handle the 7% empty rows.
- This is exactly the **OT/NT asymmetry** recorded in `SPECIFICATION_v1.9` S3 and the reason
  the qp-enrichment pre-validator (`survey1/qp_evidence.py`) is flagged **OT-centric**: its
  "verb-sense = `wform` contains 動詞" test survives the noise, but any finer OT parse must
  normalize first. A future `ot_wform_normalize()` belongs next to `qp_evidence.py`.

## Anomalies (small, but log them)
- 12 placeholder rows (`sn='00000'` or `word='+'`).
- 4,498 rows whose `wform` does not lead with a Chinese POS (prose-first or fragment-first).
