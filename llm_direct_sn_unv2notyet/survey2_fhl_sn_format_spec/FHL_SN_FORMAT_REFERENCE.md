# FHL Strong's Number (SN) Tag Format Reference

Authoritative reference for the Strong's Number notation system used by FHL (bible.fhl.net) and implemented across this repository.

> **Conceptual companion.** For *why* these tags exist and *what task we perform* when inserting them — the three levels of "parsing", the SN + Parsing Code two-tag system, and the decisive Parsing-vs-Alignment distinction — see [`../../parsing/PARSING_FOUNDATIONS.md`](../../parsing/PARSING_FOUNDATIONS.md). This file is the mechanical tag-syntax layer; that file is the conceptual layer above it.

## 1. What is a Strong's Number?

A Strong's Number is a unique identifier assigned to each Hebrew (OT) or Greek (NT) root word in the Bible. James Strong's original concordance numbers Hebrew words H1-H8674 and Greek words G1-G5624. FHL extends this with morphology codes (8xxx) and inseparable prefix markers (09xxx).

## 2. FHL API Raw Format

FHL's API (`qb.php?strong=1`) returns Bible text with embedded SN tags. Each tag has a **W-prefix** followed by type markers and a numeric code.

### 2.1 W-Prefix Decode

```
W = base marker (always present)
H = Hebrew (Old Testament)
G = Greek (New Testament)
A = Attached (inseparable prefix marker — ל ,ב ,כ ,מ ,ה ,ו)
T = Tense/Type (morphology code)
```

Combinations:
| Prefix | Meaning | Example |
|--------|---------|---------|
| `WH` | Hebrew core Strong's | `<WH0430>` = אֱלֹהִים (God) |
| `WG` | Greek core Strong's | `<WG2316>` = θεός (God) |
| `WAH` | Hebrew with attached prefix | `<WAH09002>` = inseparable ב |
| `WAG` | Greek with attached prefix | (rare) |
| `WTH` | Hebrew morphology code | `<WTH8804>` = Qal Perfect |
| `WTG` | Greek morphology code | `<WTG5656>` = Aorist Active Indicative |

**Note on WAH scope**: `WAH` is not limited to 900x prefixes. The `A` (Attached) marker appears on any word FHL considers syntactically bound to the next word, including:
- 900x prefixes: `<WAH09002>` (בְּ), `<WAH09001>` (לְ)
- Prepositions in compounds: `<WAH04480>` (מִן), `<WAH0834>` (אֲשֶׁר)
- Negation particles: `<WAH03808>` (לֹא, Ps 23:1)
- Conjunctions: `{<WAH03588>}` (כִּי, Gen 3:5)
- Aramaic relative: `<WAH01768>` (דִּי, Dan 2:20)

**Note on Aramaic**: Daniel 2:4–7:28 and Ezra 4:8–6:18 are in Aramaic, not Hebrew. FHL uses the **same `WH` prefix** for Aramaic words — there is no separate Aramaic prefix. E.g., `<WH0426>` is Aramaic אֱלָהּ (God) in Dan 2:20, using `WH` just like Hebrew.

### 2.2 Tag Types

| Type | Format | Example | Description |
|------|--------|---------|-------------|
| Core (explicit) | `<WHdddd>` or `<WGdddd>` | `<WH0430>` | Word has a Chinese equivalent in the text |
| Prefix marker | `<WAHddddd>` | `<WAH09002>` | Inseparable Hebrew prefix attached to next word |
| Morphology | `<WTHdddd>` or `<WTGdddd>` | `<WTH8804>` | Verbal stem/tense/mood code |
| Implicit (braced) | `{<WHdddd>}` | `{<WH0853>}` | Hebrew word with NO Chinese equivalent |
| Implicit prefix | `{<WAHddddd>}` | `{<WAH05921>}` | Braced preposition, no Chinese word |
| Implicit morphology | `{<WTHdddd>}` or `{<WTGdddd>}` | `{<WTH8750>}` | Braced morphology (verb + morph both implicit) |

**Implicit morphology** appears when a verb and its morphology code are both braced — the Hebrew/Greek word has no Chinese equivalent AND its conjugation is also implicit. Examples: `{<WH06032>}{<WTH8750>}` (Dan 2:20), `{<WG1510>}{<WTG5707>}` (John 1:1).

### 2.3 Real Examples

**Old Testament — Genesis 1:1** (Hebrew, `WH`/`WAH`/`WTH`):
```
起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>{<WH0853>}天<WH08064>{<WH0853>}地<WH0776>。
```
Breakdown:
- `<WAH09002>` — inseparable prefix ב (בְּ, "in/at")
- `<WH07225>` — רֵאשִׁית (beginning), Strong's H7225
- `<WH0430>` — אֱלֹהִים (God), Strong's H430
- `<WH01254>` — בָּרָא (create), Strong's H1254
- `<WTH8804>` — Qal Perfect 3ms (morphology code)
- `{<WH0853>}` — אֵת (direct object marker, no Chinese word) × 2
- `<WH08064>` — שָׁמַיִם (heavens), Strong's H8064
- `<WH0776>` — אֶרֶץ (earth), Strong's H776

**New Testament — Matthew 1:2** (Greek, `WG`/`WTG`):
```
亞伯拉罕<WG11>生<WG1080><WTG5656>以撒<WG2464>；{<WG1161>}以撒<WG2464>生<WG1080><WTG5656>雅各<WG2384>；
```
Breakdown:
- `<WG11>` — Ἀβραάμ (Abraham), Strong's G11
- `<WG1080>` — γεννάω (beget), Strong's G1080
- `<WTG5656>` — Aorist Active Indicative 3s (morphology)
- `{<WG1161>}` — δέ (and/but, implicit connective)

## 3. Numeric Classification

After stripping the W-prefix letters (W, H, G, A, T), the remaining digits determine the token type:

```
┌─────────────────────────────────────────────────────────────┐
│ NUMERIC CLASSIFICATION RULES                                │
├─────────────────────────────────────────────────────────────┤
│ 4-digit starting with 8 (8000-8999) → MORPHOLOGY           │
│   Example: 8804 from <WTH8804>                             │
│                                                             │
│ 5-digit starting with 09 (09000-09999) → 900x PREFIX       │
│   Example: 09002 from <WAH09002>                           │
│                                                             │
│ ⚠ CRITICAL: 4-digit 0914 is NOT a 900x prefix!            │
│   <0914> = core Strong's H914 (only 4 digits)              │
│   <09140> = 900x prefix (exactly 5 digits starting 09)     │
│                                                             │
│ Everything else (0001-7999, 9000+) → CORE STRONG'S         │
│   Example: 0430 from <WH0430>                              │
└─────────────────────────────────────────────────────────────┘
```

### Classification Order (in code)
1. Check morphology first: `len == 4` AND `startswith('8')` → morph
2. Check 900x prefix: `len == 5` AND `startswith('09')` → p900x
3. Check special braced types (0853, brace_preps) → object_marker / brace_prep
4. Fallback → core Strong's

## 4. 900x Prefix Mapping

FHL uses 5-digit codes starting with `09` for Hebrew inseparable prefixes (particles that attach directly to the next word):

| Code | Hebrew | Name | Transliteration | Meaning |
|------|--------|------|-----------------|---------|
| 09001 | לְ | Lamed | l- | to, for |
| 09002 | בְּ | Bet | b- | in, with, by |
| 09003 | כְּ | Kaf | k- | like, as |
| 09005 | (alias for 09001) | | | |
| 09006 | מִ | Mem | m- | from |
| 09009 | הַ | He | ha- | the (article) |
| 09015 | — | — | — | paragraph marker (ignored) |

These always appear with `WAH` prefix: `<WAH09001>`, `<WAH09002>`, etc.

## 5. Special Braced Numbers

These Strong's numbers frequently appear in braces `{<...>}` because they represent Hebrew grammatical words that have no Chinese equivalent:

| Number | Hebrew | Name | Meaning | Frequency |
|--------|--------|------|---------|-----------|
| **0853** | אֵת | et | Direct object marker | Very frequent |
| 05921 | עַל | al | on, upon | Common |
| 04480 | מִן | min | from | Common |
| 0413 | אֶל | el | to, unto | Common |
| 00996 | בֵּין | bein | between | Occasional |

The direct object marker `{<WH0853>}` (את) is by far the most common implicit marker. It appears twice in Genesis 1:1 alone.

## 6. Morphology Codes (8xxx)

4-digit codes in the 8000-8999 range indicate verbal conjugation patterns. FHL primarily uses codes in the 8600-8900 range:

### Hebrew Verbal System (WTH)

| Code | Stem | Form | Hebrew Name |
|------|------|------|-------------|
| 8804 | Qal | Perfect | קַל שָׁלֵם |
| 8799 | Qal | Imperfect | קַל עָתִיד |
| 8798 | Qal | Imperative | קַל צִוּוּי |
| 8800 | Qal | Infinitive Construct | קַל שֵׁם הַפֹּעַל |
| 8801 | Qal | Infinitive Absolute | קַל שֵׁם הַפֹּעַל הַמֻּחְלָט |
| 8802 | Qal | Participle Active | קַל בֵּינוֹנִי פּוֹעֵל |
| 8803 | Qal | Participle Passive | קַל בֵּינוֹנִי נִפְעָל |
| 8737 | Niphal | Perfect | נִפְעַל שָׁלֵם |
| 8764 | Piel | Participle | פִּעֵל בֵּינוֹנִי |
| 8686 | Hiphil | Perfect | הִפְעִיל שָׁלֵם |

### Greek Verbal System (WTG)

| Code | Example | Description |
|------|---------|-------------|
| 5656 | `<WTG5656>` | Aorist Active Indicative |
| 5772 | `<WTG5772>` | Perfect Passive Participle |

Morphology codes always attach to the verb they describe and appear immediately after the verb's core Strong's number.

## 7. Normalization Pipeline

FHL raw format is converted to parsed output format for display:

```
FHL Raw (Layer 1)              Parsed Output (Layer 2)
─────────────────              ─────────────────────
<WH0430>                  →    <0430>          (strip WH)
<WAH09002>                →    <09002>         (strip WAH)
<WTH8804>                 →    (**8804)         (convert to morph format)
{<WH0853>}                →    {<0853>}         (strip WH, keep braces)
{<WAH05921>}              →    {<05921>}        (strip WAH, keep braces)
```

Steps:
1. Remove `W`, `A`, `T`, `H`, `G` prefix letters
2. Convert morphology `<WTH8xxx>` → `(**8xxx)` format
3. Preserve braces `{ }` for implicit markers
4. Preserve angle brackets `< >` for core and prefix tags

## 8. Regex Patterns Cross-Reference

All regex patterns used across the codebase for SN handling:

### Python

| File | Line | Pattern | Purpose |
|------|------|---------|---------|
| `parse_verse_v1_8.py` | 563 | `r'(?:\{<([^>]+)>\})\|(?:<([^>]+)>)'` | Tokenize: group 1=implicit, group 2=explicit |
| `parse_verse_v1_8.py` | 575 | `r'(\d{3,5})$'` | Extract numeric portion from tag content |
| `parse_verse_v1_8.py` | 1131 | `r'<(W[ATH]*)(\d{3,5})>'` | Extract W-prefix + number (display) |
| `llm_direct_sn_unv2notyet.py` | 1465 | `r'(?:\{)?<W[ATH]*([HG]?\d+)>(?:\})?'` | Count all SNs (explicit + implicit) |
| `comparator.py` | 22 | `r'(\{<W[ATH]*[HG]?\d+>\}\|<W[ATH]*[HG]?\d+>)'` | Extract ordered SN sequence with context |
| `unv_sn_segmenter.py` | 61 | `r'(\{<[^>]+>\}\|<[^>]+>)'` | Generic token extraction |

### JavaScript

| File | Line | Pattern | Purpose |
|------|------|---------|---------|
| `color_mapper.js` | 59 | `/<(?:W[ATH]*H?)?(\d+)>\|\((\*?\*?\d+)\)/g` | Extract SN numbers (handles both prefixed and parsed) |
| `color_mapper.js` | 193 | `/(\{?<W[ATH]*H?\d+>\}?)/g` | Tokenize raw text tags |
| `color_mapper.js` | 346 | `/(\{?<W[ATH]*H?(\d+)>\}?)(\{?<WTH8\d{3}>\}?\|\(\*?\*?8\d{3}\))?/g` | SN + optional morphology |
| `right_reader_frontend.js` | 853 | `/<W[A-Z]*[HG]\d+>/g` | Remove SN tags from display text |
| `right_reader_frontend.js` | 855 | `/\{<W[A-Z]*[HG]\d+>\}/g` | Remove braced SN tags |

## 9. FHL's Two Data Sources: qb.php vs qp.php

FHL provides Bible data through two complementary APIs with **different annotation styles**:

| API | Purpose | Annotation Style | Example (מֵעַל "from above") |
|-----|---------|-----------------|-------------------------------|
| **qb.php** | UNV text + SN tags | **Analytic** (split into components) | `<WAH04480><WH05921>` |
| **qp.php** | Hebrew/Greek morphology | **Synthetic** (merged into one entry) | `sn: 05921`, `wform: "介系詞 מִן + 介系詞 עַל"` |

### 9.1 qb.php (UNV + Strong's Numbers)

```
GET https://bible.fhl.net/json/qb.php?version=unv&chineses=創&chap=1&sec=1&strong=1
```

Response: `{record: [{sec, bible_text}, ...]}` where `bible_text` contains the inline SN tags documented in §2.

### 9.2 qp.php (Hebrew/Greek Parsing Data)

```
GET https://bible.fhl.net/json/qp.php?engs=Gen&chap=1&sec=1
```

Response envelope: `{"status": "success", "record_count": N, "next": {...}, "prev": {...}, "record": [...]}` — `record` is the word array; `next`/`prev` carry adjacent-verse coordinates. Note that `record_count` **includes** the `wid=0` overview row (§9.2.1): Gen 1:1 returns `record_count: 8` = 1 overview + 7 words.

Key fields of each word record (`wid >= 1`):

| Field | Description | Example |
|-------|-------------|---------|
| `wid` | Word position index, in **original word order** (`wid=0` is a whole-verse overview row — see §9.2.1) | `3` |
| `word` | Hebrew/Greek word form as inflected in the verse | `מִלִּפְנֵי` |
| `sn` | Strong's number, zero-padded, no H/G prefix (may differ from qb — see §11.4) | `03942` |
| `pro` | Part of speech — NT only; always the empty string in OT, and JSON `null` on NT placeholder rows (see §9.2.1, §9.2.2) | `動詞` (John 3:16 ἠγάπησεν) |
| `wform` | Morphology in Chinese — OT: POS + morphology together; NT: inflection only (see §9.2.2) | `"介系詞 מִן + 介系詞 לִפְנֵי"` |
| `orig` | Lemma / dictionary headword. May differ from `word` — prefixes stripped (Gen 1:1: `word` בְּרֵאשִׁית → `orig` רֵאשִׁית); NT may list spelling variants space-separated (John 3:16: `"οὕτω οὕτως"`) | `בָּרָא` (Gen 1:1) |
| `remark` | Extended notes (compound etymology, dictionary cross-references like `[#2.25#]`) | `"לִפְנֵי 從介系詞 לְ + 名詞 פָּנֶה (臉, SN 6440)"` |
| `exp` | Dictionary meaning / gloss | `"在…之前"` |

Every record additionally carries verse-coordinate metadata — `id`, `engs`, `chap`, `sec` — with identical values for all records of a verse; these are omitted from the table above. Field values may carry trailing whitespace (John 3:16 wid=3 returns `wform` ending in a space) — consumers should strip before comparing; examples in this document are shown trimmed.

#### 9.2.1 The `wid=0` Whole-Verse Overview Row

Every verse's `record` array begins with a `wid=0` row that is **not a word record**:

- `word` — the full original-language verse text (line layout may be irregular)
- `exp` — a whole-verse Chinese rendering (not UNV; e.g., Gen 1:1 reads 「起初，上帝創造天和地。」 — note 上帝, not 神)
- `chineses` / `chinesef` — book-name metadata (`創` / `創世記`)
- **no `sn`, `pro`, `wform`, or `orig` keys at all**

Verified example (Gen 1:1, trimmed):

```json
{"wid": 0,
 "word": "בָּרָא אֱלֹהִים … בְּרֵאשִׁית",
 "exp": "起初，\r\n上帝創造天和地。",
 "chineses": "創", "chinesef": "創世記"}
```

**Consumers must skip this row** — iterate `wid >= 1` only. (The repo helper `survey6_original_lang_benchmark/run_survey6.py::fetch_qp_verse()` already does this.)

**NT placeholder rows.** NT data contains a second non-word record type: textual-critical omission markers with `word: "+"`, `sn: "00000"`, `pro: null`, and empty `wform`/`orig`/`exp` (verified live: Matt 3:2 wid 1, 2, 4). These pass a `wid >= 1` filter and DO carry an `sn` key, so a wid filter alone is not sufficient — consumers must also skip records with `sn == "00000"` (or `word == "+"`) before treating the remainder as alignable words.

#### 9.2.2 OT/NT Field Asymmetry (`pro` vs `wform`)

OT and NT records distribute part-of-speech and morphology **differently** (verified live, Gen 1:1 / John 3:16 / Matt 3:2, 2026-07-10):

| | OT (Hebrew/Aramaic) | NT (Greek) |
|---|---------------------|------------|
| `pro` | always the empty string `""` | part of speech: `動詞`, `名詞`, `連接詞`, `副詞`, … (`null` on placeholder rows, §9.2.1) |
| `wform` | POS **and** morphology together | inflection only; **empty string for indeclinables** |
| Example (verb) | `wform: "動詞，Qal 完成式 3 單陽"` (Gen 1:1 בָּרָא) | `pro: "動詞"`, `wform: "第一簡單過去 主動 直說語氣 第三人稱 單數"` (John 3:16 ἠγάπησεν) |
| Example (non-verb) | `wform: "介系詞 בְּ + 名詞，陰性單數"` (Gen 1:1 בְּרֵאשִׁית) — POS still leads `wform` | `pro: "副詞"`, `wform: ""` (John 3:16 Οὕτως) |

Consequences for consumers:

1. **A POS test must check both fields.** "Is this the verb-sense record?" is `pro == "動詞" or wform.startswith("動詞")`. Code that greps `wform` alone is **OT-centric** and silently misses every NT record.
2. **An empty NT `wform` on a real word record is normal** (indeclinable word), not missing data — but on the placeholder rows of §9.2.1, empty `wform` really is absent data; filter those out first.
3. The asymmetry is structural, not incidental: Hebrew inflection is fused into the root and was historically encoded in Chinese, while Greek inflection is affixal and standardized — see [`../../parsing/PARSING_FOUNDATIONS.md`](../../parsing/PARSING_FOUNDATIONS.md) §4.

### 9.3 Key Divergence: Compound Prepositions

The analytic/synthetic split matters most for compound prepositions:

- **qb.php** splits מֵעַל into `<04480>` + `<05921>` (two tags)
- **qp.php** records it as a single entry under SN 05921 with `wform: "介系詞 מִן + 介系詞 עַל"`

This means `<04480>` appears in qb.php but has **no matching record** in qp.php — it's absorbed into the compound. See §11.2 for the full compound preposition treatment.

### 9.4 qp.php Compound Indicator Patterns

FHL uses these conventions in `wform` and `remark` fields to signal compound words:

| Pattern (in `wform` or `remark`) | Type | Example |
|----------------------------------|------|---------|
| `介系詞 מִן + 介系詞 ...` | prep + prep | מֵעַל (from above) |
| `介系詞 מִן + 名詞...` | prep + noun | מִכָּל (from all) |
| `從介系詞 לְ + 名詞 ...` | prep + noun (etymology) | לִפְנֵי (before) |
| `...詞尾` (e.g., `3 單陽詞尾`) | pronoun suffix attached | מִמֶּנּוּ (from him) |

## 10. Known Discrepancies

| # | Issue | Components | Impact |
|---|-------|-----------|--------|
| 1 | JS uses `W[A-Z]*[HG]`, Python uses `W[ATH]*` | right_reader vs parse_verse | None — FHL only uses A and T, both match |
| 2 | SPEC morphology range `8[6-9]dd`, code accepts all `8xxx` | SPEC vs parse_verse | None — FHL only produces 8600-8900 |
| 3 | Root CLAUDE.md lists `{H1234}` and `(H1234)` formats | CLAUDE.md vs actual API | Legacy formats rarely seen in FHL data |
| 4 | Zero-padding varies: `<WH430>` vs `<WH0430>` | Model output vs FHL | FHL always zero-pads; models sometimes don't |

## 11. Edge Cases

### 11.1 The 4-digit vs 5-digit 900x Trap
```
<WH0914>  → Core Strong's H914 (NOT a 900x prefix — only 4 digits)
<WH09140> → 900x prefix #9140 (5 digits starting with 09)
```
This is the most common source of bugs. The check MUST be: `len(number) == 5 AND number.startswith('09')`.

### 11.2 Compound Prepositions

FHL's qb.php frequently splits compound prepositions into multiple consecutive SN tags. Three structural patterns exist:

**Pattern A — prep + prep (מִן-compounds):**
```
qb: 將…以下<WAH04480><WH08478>的水    (Gen 1:7)
qp: sn=08478, wform="介系詞 מִן + 介系詞 תַּחַת"
→ <04480><08478> = מִתַּחַת "from below"
```

**Pattern B — 900x + core (לִפְנֵי-type):**
```
qb: 在　神<WH0430>面前<WAH09001><WH06440>敗壞    (Gen 6:11)
qp: sn=03942, wform="介系詞", remark="לִפְנֵי 從介系詞 לְ + 名詞 פָּנֶה (臉, SN 6440)"
→ <09001><06440> = לִפְנֵי "before" (qp.php assigns different SN: 03942)
```

**Pattern C — prep + 900x + core (multi-token):**
```
qb: 耶和華<WH03068>的面<WAH04480><WAH09001><WH06440>    (Gen 4:16)
qp: sn=03942, wform="介系詞 מִן + 介系詞 לִפְנֵי"
→ <04480><09001><06440> = מִלִּפְנֵי "from before" (3 tokens, 900x in between)
```

**Verified compound examples from Genesis:**

| Verse | qb tags | Hebrew | Meaning | qp wform |
|-------|---------|--------|---------|----------|
| Gen 1:7 | `<04480><08478>` | מִתַּחַת | from below | 介系詞 מִן + 介系詞 תַּחַת |
| Gen 1:7 | `<04480><05921>` | מֵעַל | from above | 介系詞 מִן + 介系詞 עַל |
| Gen 4:16 | `<04480><09001><06440>` | מִלִּפְנֵי | from before | 介系詞 מִן + 介系詞 לִפְנֵי |
| Gen 6:11 | `<09001><06440>` | לִפְנֵי | before | (remark field) |
| Gen 24:27 | `<04480><05973>` | מֵעִם | from with | 介系詞 מִן + 介系詞 עִם |
| Gen 49:30 | `<04480><00854>` | מֵאֵת | from beside | 介系詞 מִן + 介系詞 אֵת |
| Exod 25:22 | `<04480><00996>` | מִבֵּין | from between | 介系詞 מִן + 介系詞 בֵּין |

### 11.3 Same Number, Different Meaning
The number `01961` (היה, "to be") appears both as:
- `<WH01961>` — explicit verb "was/were"
- `<WAH01961>` — with prefix marker (e.g., וַיְהִי "and it was")

The `W` vs `WA` prefix distinguishes them.

### 11.4 qb/qp SN Disagreement

For compound prepositions, qp.php sometimes assigns a **completely different SN** than what qb.php uses. Example: qb has `<09001><06440>` but qp records `sn: 03942` (לִפְנֵי as a standalone lexeme). Parsers must handle this SN mismatch gracefully.

---

## Appendix A. Revision History

### A.1 Initial Version (2026-03-20)

Created as a textbook-level consolidation of SN format definitions scattered across 10+ files in the repository. Sources: `parse_verse_v1_8.py`, `color_mapper.js`, `llm_direct_sn_unv2notyet.py`, `comparator.py`, `system_prompt_lcc.md`, and the FHL API.

### A.2 SPECIFICATION Merge & Live API Verification (2026-03-20)

Merged format-level facts from `sn_within_unv_selfgroup_segmentation/SPECIFICATION_v1.4.md` through `SPECIFICATION_v1.8.md` into this reference. Parser-specific logic (grouping rules, brace-prep decision tree, config profiles, pseudo-code, logging system, FAQ) was intentionally excluded — those belong in the SPECIFICATION files.

Additionally, 11 real verses were fetched from the live FHL API (Genesis 1:1–1:7, 3:5; Matthew 1:2; John 1:1; Psalm 23:1; Daniel 2:4, 2:20, 7:9; Ezra 4:8) to verify completeness against actual output. This uncovered three undocumented patterns.

**Changes made:**

| Addition                                                         | Section       | Source                                       |
|------------------------------------------------------------------|---------------|----------------------------------------------|
| Braced morphology `{<WTHdddd>}` / `{<WTGdddd>}`                | §2.2          | Live API (Dan 2:20, John 1:1)                |
| WAH scope expanded — negation, conjunctions, Aramaic relative   | §2.1 note     | SPEC v1.8 examples + live API verification   |
| Aramaic uses `WH` — no separate prefix                          | §2.1 note     | Live API (Dan 2:4–7:28)                      |
| qb.php vs qp.php — two data sources, analytic vs synthetic      | New §9        | SPEC v1.8 §4.0–4.1                          |
| qp.php field structure (`wform`, `remark`, `sn`, `word`, etc.)  | §9.2          | SPEC v1.8 §3.3, §7.6–7.8                    |
| qp.php compound indicator patterns                              | §9.4          | SPEC v1.8 §3.3.1                            |
| 3 compound preposition structural patterns with real qb+qp data | §11.2         | SPEC v1.8 §7.5–7.8                          |
| qb/qp SN disagreement edge case                                 | §11.4         | SPEC v1.8 §7.8                              |

Document grew from 237 to 335 lines. Not merged (parser-specific, not format): grouping rules, brace-prep decision tree, config profiles, pseudo-code, logging system, FAQ.

### A.3 qp.php Field Enrichment — orig, pro, wid=0, OT/NT Asymmetry (2026-07-10)

Enriched §9.2's field documentation from fresh live API probes (Genesis 1:1 OT; John 3:16 and Matthew 3:2 NT), per Item 1 of [`../../parsing/QP_ENRICHMENT_PLAN.md`](../../parsing/QP_ENRICHMENT_PLAN.md).

**Changes made:**

| Addition                                                         | Section       | Source                                       |
|------------------------------------------------------------------|---------------|----------------------------------------------|
| `orig` (lemma) and `pro` (part of speech) rows in field table   | §9.2          | Live API (Gen 1:1, John 3:16)                |
| Response envelope (`next`/`prev`); `record_count` includes the overview row; per-record verse-coordinate metadata; trailing-whitespace caveat | §9.2 | Live API |
| `wid=0` whole-verse overview row — consumers must skip it       | New §9.2.1    | Live API                                     |
| NT placeholder rows (`word: "+"`, `sn: "00000"`, `pro: null`) — skip alongside `wid=0` | New §9.2.1 | Live API (Matt 3:2) |
| OT/NT field asymmetry (`pro` empty on OT; POS split on NT; empty `wform` for NT indeclinables) | New §9.2.2 | Live API |

Document grew from 362 to 423 lines.
