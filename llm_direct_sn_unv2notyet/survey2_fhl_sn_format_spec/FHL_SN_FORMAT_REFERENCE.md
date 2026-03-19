# FHL Strong's Number (SN) Tag Format Reference

Authoritative reference for the Strong's Number notation system used by FHL (bible.fhl.net) and implemented across this repository.

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

### 2.2 Tag Types

| Type | Format | Example | Description |
|------|--------|---------|-------------|
| Core (explicit) | `<WHdddd>` or `<WGdddd>` | `<WH0430>` | Word has a Chinese equivalent in the text |
| Prefix marker | `<WAHddddd>` | `<WAH09002>` | Inseparable Hebrew prefix attached to next word |
| Morphology | `<WTHdddd>` or `<WTGdddd>` | `<WTH8804>` | Verbal stem/tense/mood code |
| Implicit (braced) | `{<WHdddd>}` | `{<WH0853>}` | Hebrew word with NO Chinese equivalent |
| Implicit prefix | `{<WAHddddd>}` | `{<WAH05921>}` | Braced preposition, no Chinese word |

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

## 9. Known Discrepancies

| # | Issue | Components | Impact |
|---|-------|-----------|--------|
| 1 | JS uses `W[A-Z]*[HG]`, Python uses `W[ATH]*` | right_reader vs parse_verse | None — FHL only uses A and T, both match |
| 2 | SPEC morphology range `8[6-9]dd`, code accepts all `8xxx` | SPEC vs parse_verse | None — FHL only produces 8600-8900 |
| 3 | Root CLAUDE.md lists `{H1234}` and `(H1234)` formats | CLAUDE.md vs actual API | Legacy formats rarely seen in FHL data |
| 4 | Zero-padding varies: `<WH430>` vs `<WH0430>` | Model output vs FHL | FHL always zero-pads; models sometimes don't |

## 10. Edge Cases

### The 4-digit vs 5-digit 900x Trap
```
<WH0914>  → Core Strong's H914 (NOT a 900x prefix — only 4 digits)
<WH09140> → 900x prefix #9140 (5 digits starting with 09)
```
This is the most common source of bugs. The check MUST be: `len(number) == 5 AND number.startswith('09')`.

### Compound Prepositions
Some verses have multiple consecutive SN tags forming compound prepositions:
```
<04480><05921> = מֵעַל "from above" (מִן + עַל)
<09001><06440> = לִפְנֵי "before" (לְ + פָנִים)
```
These are detected via FHL's `qp.php` morphology data (wform field containing `'介系詞 מִן +'`).

### Same Number, Different Meaning
The number `01961` (היה, "to be") appears both as:
- `<WH01961>` — explicit verb "was/were"
- `<WAH01961>` — with prefix marker (e.g., וַיְהִי "and it was")

The `W` vs `WA` prefix distinguishes them.

---

*This document consolidates SN format definitions from SPECIFICATION_v1.8.md, parse_verse_v1_8.py, color_mapper.js, llm_direct_sn_unv2notyet.py, comparator.py, system_prompt_lcc.md, and the FHL API.*
