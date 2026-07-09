# Parsing Foundations for SN Insertion

Conceptual foundation for the Strong's Number (SN) insertion work in this repository.
This document explains **what "parsing" means**, how it differs from **alignment**, and
why that distinction is the bedrock of our SN-transfer task.

> **Companion document.** For the *mechanical* tag syntax (`<WHdddd>`, `{<...>}`, `(...)`,
> 900x prefixes, morphology codes), see
> [`../llm_direct_sn_unv2notyet/survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md`](../llm_direct_sn_unv2notyet/survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md).
> This file is the **conceptual layer above** that reference — it explains *why* the tags
> exist and *what task we are actually performing* when we insert them.

**Provenance.** The content below distills a design discussion in the FHL technical group
among: an FHL site architect (site history & philosophy), an FHL UI engineer (implementation),
an alignment/linguistics collaborator (theory), and a contributor who supplied the operational
insertion rules. Personal identities are intentionally omitted per repo policy; only public
technical/institutional names (FHL, UBS, ClearBible, macula, clear-aligner, WeDevote) are kept.

---

## 1. Three levels of "parsing" (don't conflate them)

Most confusion in this space comes from using one word for three different granularities:

| Level | Name | Operates on | Whose term |
|-------|------|-------------|------------|
| **L1** | **Morphological parsing** | one original-language word → inflectional markers + lemma | FHL's traditional "parsing" |
| **L2** | **Lemma ↔ Strong Number** | the principle mapping a dictionary headword to a number | the theory behind SN |
| **L3** | **Sentence parsing / Treebank** | a whole sentence → tree structure (NP, VP, …) | NLP's broader "parsing" |

**Key fact:** When FHL says "parsing," it means **L1**. NLP's "parsing" also includes **L3**
(syntactic trees, e.g. the Clear Bible `macula-greek` / `macula-hebrew` treebanks). But the
operational basis of *our* SN-insertion task is a fourth thing entirely — **Alignment** (§5).

---

## 2. L1 — FHL's "parsing" = morphological analysis

FHL's philosophy is **original-text-centric**. Historically, Chinese SN annotation began
Chinese-centric (original as helper), using Strong Numbers as a stand-in when the original text
was hard to typeset — influenced by the 浸宣原文彙編 tradition. The **parsing** concept later
inverted this: analyze the original into **basic meaning (lemma) + morphological variation**, so
the reader understands scripture through the *"interpreted original."* Original-text becomes
primary; the Chinese translation becomes the helper.

> **Definition.** In the FHL sense:
> **Parsing = decomposing one original-language word into its `lemma` + `inflectional
> morphological markers`.**

---

## 3. FHL's two-tag system: SN + Parsing Code

In FHL data, a **verb usually carries two tags**:

1. **Strong's Number → "which word is this?"** (the lemma)
2. **Parsing Code → "how is it inflected here?"** (the morphology)

### Greek example (John 3:16, "loved")
```
Strong's:      G25  (agapaō — base verb "to love")   ← lemma
Parsing Code:  V-AAI-3S                               ← morphology
   V  = Verb
   A  = Aorist
   A  = Active voice
   I  = Indicative mood
   3S = 3rd Person Singular
```

### Hebrew example (Genesis 1:1, "created")
```
Strong's:      H1254 (bara — base verb "to create")   ← lemma
Parsing Code:  V-Qal-Perf-3MS                          ← morphology
   V    = Verb
   Qal  = Qal stem (simple, active)
   Perf = Perfect (completed action)
   3MS  = 3rd Person Masculine Singular
```

**Consequence for insertion.** A single verb slot in the FHL API may return **two number
streams** — a meaning-bearing SN (1–8999) and a morphology code (FHL encodes these as 8xxx /
09xxx, etc.). This is exactly the Core / Morphology / 900x-prefix trichotomy in
`SPECIFICATION_v1.8.md`. **When inserting, the morphology code is not "another word" — it is
variation info about the same word, and must never be matched to a separate Chinese token.**

---

## 4. L2 — Why lemma? Greek vs Hebrew differ structurally

The Strong Number system rests on the concept of **lemma**: one lemma → one number. All words
related **inflectionally** (tense, number, gender — *not* derivationally) share the same lemma
and thus the same number.

But the two languages implement inflection differently:

- **Greek** — inflection is almost entirely **affixation** → morphology is "attached," easy to
  segment and standardize into one code set (`V-AAI-3S`) → **cross-language convertible.**
- **Hebrew** — inflection is implemented by **internal vowel shifts** → morphology is "fused"
  into the root; and FHL historically used *Chinese* as the internal code → **hard to
  standardize, hard to export.**

This explains a real technical asymmetry acknowledged by the FHL site architect: Greek SN+parsing
data converts readily to codes usable by other languages; **Old Testament (Hebrew) data does
not.**

> **Consequence for insertion.** Expect OT morphology data to be **less regular** than NT.
> Do not assume the Hebrew stream is as clean as the Greek one — this is a structural limitation,
> not a bug in our pipeline.

---

## 5. The decisive distinction: Parsing vs Alignment ★

The FHL "parsing" concept traces back to **UBS (United Bible Societies)**, who go further —
they don't even use SN; they work **directly with the original text**. The alignment collaborator
named the underlying model precisely:

> **Alignment** = the basis of original↔translation correspondence, "simply put:
> **word(s) for word(s) or null**." (ClearBible's model; tooling: `clear-aligner`, macula
> treebanks. WeDevote used this Alignment model.)

Two conceptual models therefore stand in contrast:

| | **Parsing model (FHL)** | **Alignment model (UBS / ClearBible / WeDevote)** |
|---|---|---|
| Core idea | original-centric; extract meaning + morphology | **word-for-word** correspondence between original ↔ translation |
| Base unit | one original word's lemma + morphology | **word(s)-for-word(s), or null (no correspondence)** |
| Product | the "interpreted original" | an alignment table (which translated word ← which original word) |
| Tooling | FHL's SN + Parsing Code | `clear-aligner`, `miklal`, macula treebank |

NLP's broader **L3 parsing** (full syntactic trees: NP/VP levels, the `macula-greek` /
`macula-hebrew` treebanks) sits above both but is **out of scope** for current FHL/insertion work
— it requires heavy linguistic annotation we are not producing today.

> **Bottom line.** FHL "parsing" (L1) is our **upstream input** — SN and morphology are already
> tagged by FHL. **What our SN-insertion task actually performs is Alignment** — mapping each
> SN-tagged original word onto a word (or `null`) in a target Chinese translation (LCC,
> RCUV2010, …).

---

## 6. Operational insertion rules ★ (the alignment spec, in plain form)

The single most directly-actionable part of the discussion — this *is* the alignment model,
worked out as rules. Four examples exhaust the main cases:

**Flow:** fetch SN-tagged text from the API → analyze the Chinese → map to the SN.

| # | Case | Example | Rule |
|---|------|---------|------|
| 1 | General | `我的<1473>弟兄們<80>` | "我的" → 1473. **SN follows the Chinese word it belongs to.** |
| 2 | Punctuation boundary | `…百般<4164>試煉<3986>中，都<3956>…` | "都" → 3956, **not** "中，都". **Punctuation is a hard segmentation boundary.** ("百般"→4164, "試煉"→3986) |
| 3 | Consecutive SN | `也當<2192>(5720)成功<5046><2041>…` | "成功" → 5046. When multiple SN follow one word, **pick the meaning SN**; `(5720)` is a morphology code, not a word. |
| 4 | Braces = untranslated | `…，使<2443>你們{<1510>}{(5725)}成全<5046>` | "你們" → **null** (no correspondence), **not** 1510. **Braces `{<...>}` mean the original exists but the translation didn't render it.** |

Distilled rules:

1. **SN follows the Chinese word it belongs to.**
2. **Punctuation is a hard boundary** — a correspondence unit may not cross it.
3. **Parenthesized `(dddd)` = parsing/morphology code**, not a meaning SN — never mapped to a
   Chinese token on its own.
4. **Braced `{<dddd>}` = original present, translation absent → the correspondence is `null`.**
   Never force it onto a neighboring Chinese word.
5. When a slot has multiple SN, **anchor only the meaning-bearing SN** to Chinese; treat
   morphology codes as annotation.

These five rules and `SPECIFICATION_v1.8.md`'s token classification are two expressions of the
same thing: the rules above are the "plain-language spec"; the specification is the "formalized"
version.

---

## 7. What this means for our SN-insertion work (the bedrock)

1. **Our task is Alignment, not Parsing.** FHL's L1 parsing is *given* upstream data. We map
   SN-tagged originals onto a target Chinese translation — word(s)-for-word(s) **or null**.
   "Now is the time" (AI-accelerated alignment) describes exactly what we are building.

2. **`null` is a first-class answer.** The braces case proves that "no correspondence" is a
   *correct* output, not a failure. The most dangerous LLM error is forcing an original-present /
   translation-absent word onto a neighboring token. Forbid this explicitly in prompts. (This
   mirrors the s10 accept-empty policy — an empty SN shell is sometimes right.)

3. **Morphology code ≠ meaning.** The two-tag system means the API's number stream mixes
   lemma-SN and parsing-code. Anchor **only** meaning SN; morphology codes are annotation. (Hence
   the strict spec rule that a 4-digit `<0914>` is *not* a 900x prefix.)

4. **Punctuation-first segmentation.** Segment by punctuation before mapping SN.

5. **OT is structurally harder than NT.** Internal-vowel-shift inflection + a legacy Chinese
   internal-code mean OT morphology data is less standardized — be more tolerant of format noise
   for the Old Testament.

6. **Upward path to treebanks exists.** If we later need phrase/syntax-level correspondence rather
   than word-level, the open-source `macula-greek` / `macula-hebrew` treebanks are a ready data
   source. Not needed now — noted for the roadmap.

---

### One-sentence summary

> FHL "parsing" = morphological analysis of the original (lemma + morphology), which is our
> **upstream input**. What SN insertion actually does is **alignment** — mapping each SN-tagged
> original word to a Chinese word or to `null`. The four insertion examples in §6 are the most
> precise operational spec of that alignment task.
