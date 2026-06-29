# FHL ↔ Original-Language (WLC) Divergence Log

**Purpose.** This project's gold standard is **FHL-faithful** — it transfers FHL's
Strong's-Number annotations (from UNV+SN) onto the target translation. FHL is the
authoritative SN source (see `../CLAUDE.md`). Sometimes FHL's *translation-anchored*
tag legitimately differs from the *original-language morphology* (here: Clear Bible
**WLC** Hebrew + survey5 morph bridge). Those are **not gold errors** — they are
methodology divergences. We **keep the FHL-faithful tag** in gold and record the
divergence here for:
1. **human review**, and
2. a possible **feedback note to FHL** (bible.fhl.net).

This is distinct from a format-bug report (cf.
`../survey4_self_supervised_prompt_tuning/BUG_2_report_FHL.md`): FHL is not
*malformed* here, it made a defensible-but-debatable tagging judgment.

Contest note (`survey10_…/S10_VS_S1_GOLD_EXPERIMENT.md`): the WLC-derived answer
key must classify these entries as **methodology divergence**, NOT as gold error,
or it will wrongly penalize FHL-faithful gold.

---

## D1 — Gen 2:20, second אָדָם — H0120 (FHL) vs H0121 (WLC)

- **Verse / clause**: 創 2:20 — `…只是那人<WAH09001><WH0120>沒有遇見配偶幫助他…`
  Hebrew: **וּלְאָדָם** לֹא־מָצָא עֵזֶר כְּנֶגְדּוֹ ("but for Adam/the man there was
  not found a helper as his counterpart").
- **First** אָדָם in 2:20 = `הָאָדָם` (with article) = "the man" → **H0120**, undisputed.
- **Second** אָדָם = the disputed one.
  - **FHL / current gold**: **H0120** (generic "man").
  - **WLC original-language alignment**: **H0121** ("Adam", proper name).
- **Evidence WLC marshals for H0121 (genuine, well-grounded)**:
  - `וּלְאָדָם` is pointed `lə-` (shewa), **not** `lā-` (qamats) → the preposition
    did **not** absorb a definite article → **article-less אָדָם**, the classic
    grammatical signal for the proper name "Adam".
  - **KJV, ESV, NIV all render "Adam"** here. 2:20 is the narrative hinge where
    אדם turns from "the man" into the name.
- **DECISION (Joshua, 2026-06-29): KEEP H0120 — option (a), FHL-faithful.** Rationale:
  1. The task **transfers** FHL's SN; it does not **correct** FHL with original-language
     morphology. FHL tags H0120.
  2. The Chinese word is **那人 = "the man"**, which matches H0120; H0121 ("Adam") on
     那人 would be a **tag-vs-word mismatch** (the translators did not render it 亞當).
  3. Therefore this is FHL's translation-anchored tag vs WLC's original morphology —
     a legitimate divergence, not a hallucination or error.
- **Status**: known-divergence · gold unchanged (H0120) · **FHL-feedback candidate**.
- **Found by**: s10 `eval_gold_vs_wlc.py` independent-truth check (Clear Bible WLC +
  survey5 morph bridge): 982/986 SN-inventory-consistent, **0 content-word
  hallucinations**; this was the **one** genuine judgment dispute. (The other 3
  gold-only flags — an FHL `<WH00>` artifact, a verb-doubling count, an
  את-companion 854/853 nuance — were not corrections.)
