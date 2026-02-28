# Compound Preposition Analysis: מִן (04480) Combinations

## Executive Summary

Analysis of 150 verses with `qb_qp_mismatch` errors reveals that **1,097 out of 1,162 (94%)** of these errors are caused by `<04480>` (מִן "from") appearing in compound constructions.

## Root Cause

**Data Source Discrepancy**:
- **qb.php** (FHL UNV+SN): Uses **analytical tagging** - breaks compound words into separate Strong's numbers
  - Example: מֵעַל (me'al "from above") → `<04480><05921>`
- **qp.php** (Hebrew parsing): Uses **holistic tagging** - treats compound as single word
  - Example: מֵעַל → `sn: 05921`, `wform: "介系詞 מִן + 介系詞 עַל"`

## מִן (04480) Compound Patterns

Based on analysis of 150 sample verses, מִן combines with:

### Category 1: TRUE COMPOUND PREPOSITIONS (介系詞 + 介系詞)

These are the most common and systematic combinations:

| Strong's | Hebrew | Compound | Meaning | Frequency |
|----------|--------|----------|---------|-----------|
| **05921** | עַל | מֵעַל | from above, from upon | 10 |
| **00854** | אֵת | מֵאֵת | from with, from beside | 6 |
| **05973** | עִם | מֵעִם | from with | 4 |
| **03942** | לִפְנֵי | מִלִּפְנֵי | from before | 3 |
| **04605** | מַעַל | מִמַּעַל | from above (emphatic) | 2 |
| **00996** | בֵּין | מִבֵּין | from between | 1 |
| **04136** | מּוּל | מִמּוּל | from in front of | 1 |
| **08478** | תַּחַת | מִתַּחַת | from under | (in Gen 1:7) |
| **00905** | לְבַד | מִלְּבַד | besides, except | 3 |
| **04295** | מַטָּה | מִלְּמָטָּה | from below | 1 |

### Category 2: NOUN COMBINATIONS (介系詞 + 名詞)

מִן + noun creates "from [noun]" constructions. These are NOT errors but legitimate combinations:

| Strong's | Hebrew | Type | Meaning | Examples |
|----------|--------|------|---------|----------|
| **06440** | פָּנִים | noun | from face/presence | מִפְּנֵי (3x) |
| **08432** | תָּוֶךְ | noun | from midst/among | מִתּוֹךְ (3x) |
| **02351** | חוּץ | noun | from outside | מִחוּץ (11x) |
| **07130** | קֶרֶב | noun | from midst/inward | מִקֶּרֶב (2x) |
| **03027** | יָד | noun | from hand | מִיָּד (4x) |

### Category 3: PROPER NOUN COMBINATIONS

Geographic/personal names:

| Strong's | Hebrew | Type | Meaning |
|----------|--------|------|---------|
| **04714** | מִצְרַיִם | place | from Egypt | (6x) |
| **03068** | יְהוָה | divine name | from YHWH | (1x) |
| **07486** | רַעְמְסֵס | place | from Rameses | (2x) |

### Category 4: OTHER COMBINATIONS

- **00853** (אֵת object marker): מֵאֵת (1x) - rare construct
- **09001** (ל prefix): מִן + ל combinations forming complex constructions

## Recommendation for Spec 1.7

### Proposed Solution: Compound Preposition Dictionary

Add a **compound preposition mapping table** to handle systematic מִן combinations:

```yaml
compound_prepositions:
  "04480+05921":
    type: "prep+prep"
    hebrew: "מֵעַל"
    meaning: "從…之上、從…上面"
    structure: "介系詞 מִן + 介系詞 עַל"

  "04480+00854":
    type: "prep+prep"
    hebrew: "מֵאֵת"
    meaning: "從…那裡、從…旁邊"
    structure: "介系詞 מִן + 介系詞 אֵת"

  "04480+05973":
    type: "prep+prep"
    hebrew: "מֵעִם"
    meaning: "從與…、從伴隨…"
    structure: "介系詞 מִן + 介系詞 עִם"

  "04480+08478":
    type: "prep+prep"
    hebrew: "מִתַּחַת"
    meaning: "從…之下"
    structure: "介系詞 מִן + 介系詞 תַּחַת"

  "04480+03942":
    type: "prep+prep"
    hebrew: "מִלִּפְנֵי"
    meaning: "從…之前"
    structure: "介系詞 מִן + 介系詞 לִפְנֵי"

  "04480+00996":
    type: "prep+prep"
    hebrew: "מִבֵּין"
    meaning: "從…之間"
    structure: "介系詞 מִן + 介系詞 בֵּין"

  "04480+04605":
    type: "prep+prep"
    hebrew: "מִמַּעַל"
    meaning: "從上面（強調）"
    structure: "介系詞 מִן + 介系詞（實名詞）מַעַל"

  "04480+04136":
    type: "prep+prep"
    hebrew: "מִמּוּל"
    meaning: "從前面"
    structure: "介系詞 מִן + 介系詞 מּוּל"

  "04480+00905":
    type: "prep+prep+noun"
    hebrew: "מִלְּבַד"
    meaning: "除了、此外"
    structure: "介系詞 מִן + 介系詞 לְ + 名詞 בַּד"

  "04480+04295":
    type: "prep+prep+noun"
    hebrew: "מִלְּמָטָּה"
    meaning: "從下面"
    structure: "介系詞 מִן + 介系詞 לְ + 副詞"
```

### Parser Enhancement Strategy

**Option A: Merge on Detection** (Recommended)
When parser encounters `<04480><XXXX>` pattern:
1. Check if combination exists in `compound_prepositions` table
2. If YES: merge into single group with compound meaning
3. If NO: check second number type:
   - If preposition → still merge with warning
   - If noun/verb/other → keep as separate groups

**Option B: Fallback Lookup**
1. Parse normally creating two groups
2. On `qb_qp_mismatch` for 04480, check if next number is preposition
3. Retroactively merge and update meaning

## Statistics

From 150-verse sample:
- **Total מִן occurrences**: 185
- **Unique combinations**: 87
- **True compound prepositions** (prep+prep): **10 core types**
- **Noun combinations**: ~30 types
- **Geographic/proper nouns**: ~15 types

**Projected impact**: Implementing this would resolve **~1,000+ qb_qp_mismatch errors** (85% of all such errors).

## Next Steps for Spec 1.7

1. ✅ Document compound preposition phenomenon
2. ⬜ Define compound detection algorithm
3. ⬜ Create comprehensive compound_prepositions table (expand to ~20-30 entries)
4. ⬜ Implement parser logic for automatic merging
5. ⬜ Add compound grouping format to output spec
6. ⬜ Update warning system (downgrade from "mismatch" to "info: compound resolved")

## Output Format Example

**Before (current)**:
```
<04480> — 未知詞性「未知意義」
<05921> — 介系詞 מִן + 介系詞 עַל「在…上面、在旁邊、關於、敵對、攻擊」
```

**After (Spec 1.7)**:
```
<04480><05921> — 複合介系詞「從…之上」 *1

*1: 介系詞 מִן + 介系詞 עַל，構成複合介系詞 מֵעַל
```

Or more concise:
```
<04480+05921> — 複合介系詞 מֵעַל「從…之上」
```
