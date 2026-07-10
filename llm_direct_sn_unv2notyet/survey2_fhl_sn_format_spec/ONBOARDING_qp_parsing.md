# ONBOARDING — qp.php Parsing Data (survey2)

Orientation for anyone working with FHL's **parsing code** (`qp.php`) from this format-specification directory. Ten-minute read; everything here is a pointer into deeper documents.

> **Conceptual root:** [`../../parsing/PARSING_FOUNDATIONS.md`](../../parsing/PARSING_FOUNDATIONS.md) — what "parsing" means (L1/L2/L3), the SN + Parsing Code two-tag system, and the decisive Parsing-vs-Alignment distinction.
> **Governing plan:** [`../../parsing/QP_ENRICHMENT_PLAN.md`](../../parsing/QP_ENRICHMENT_PLAN.md) — the 4-item change set feeding qp.php data into the SN-insertion pipeline.
> **Authoritative field spec:** [`FHL_SN_FORMAT_REFERENCE.md`](FHL_SN_FORMAT_REFERENCE.md) §9.2 (this directory) — always defer to it for field-level detail.

## 1. What qp.php gives you

```
GET https://bible.fhl.net/json/qp.php?engs=Gen&chap=1&sec=1
```

Per-word records of the original-language verse, in **original word order** (`wid`):

| Field | One-line meaning |
|-------|------------------|
| `wid` | word position (original word order); `wid=0` is a whole-verse overview row — **skip it** (§9.2.1) |
| `word` | the inflected Hebrew/Greek form as it stands in the verse; NT also has placeholder rows with `word: "+"`, `sn: "00000"` — **skip those too** (§9.2.1) |
| `sn` | Strong's number (zero-padded, no H/G prefix; can differ from qb.php — §11.4) |
| `orig` | **lemma / dictionary headword** — may differ from `word` (prefix stripped) |
| `pro` | **part of speech** — NT only; always empty on OT (§9.2.2) |
| `wform` | morphology in Chinese — OT: POS+morphology together (`動詞，Qal 完成式 3 單陽`); NT: inflection only, empty for indeclinables (§9.2.2) |
| `exp` | dictionary gloss |
| `remark` | compound etymology / cross-references |

Two granularities of the same parsing code exist: **coarse** inline in `qb.php?strong=1` (`<WTH8804>` / `<WTG5656>`, decode table in reference §6) and **fine** in qp.php `wform` (adds person/gender/number). qp.php is the fine-grained source.

## 2. Why these fields matter for SN insertion (the four bedrock uses)

Our task is **Alignment** — mapping each SN-tagged original word to a target-Chinese word or `null` (PARSING_FOUNDATIONS §5/§7). qp.php is the upstream evidence that turns several LLM *guesses* into *rule-decidable* facts (plan §0):

1. **Original word-order skeleton = the left side of alignment.** The `wid` sequence is the original word list; insertion becomes "qp word → target-Chinese span (or null)". This makes the **null check objective**: after skipping the `wid=0` overview and NT placeholder rows (§9.2.1), every remaining qp word must be either mapped or explicitly null.
2. **Multi-SN disambiguation.** When several SN follow one Chinese word, the record whose POS says 動詞 identifies the verb-sense SN — rule, not guess. NT: check `pro`; OT: check `wform` prefix (see the asymmetry, reference §9.2.2).
3. **Compound merge.** `wform` patterns like `介系詞 מִן + …` signal qb.php tag sequences that form one word (reference §9.4, §11.2) — already exploited by SPECIFICATION v1.8.
4. **Richer LLM context.** `orig` (lemma) + `exp` (gloss) + `wform` (morphology) triple the signal versus a bare SN.

## 3. Access paths in this repo

- **Live API:** endpoint above. Response envelope `{status, record_count, next, prev, record}`; `record_count` includes the `wid=0` row.
- **Helpers:** `survey6_original_lang_benchmark/run_survey6.py` — `fetch_qp_verse()` (prefers local SQLite, falls back to the API, skips `wid=0`) and `normalize_qp_sn()` (`"00430"` → `WH0430`).
- **Local fallback DB:** `original_text_preparation/source_sqlite/bible_parsing.db`, tables `lparsing` (OT) / `fhlwhparsing` (NT). The schema carries the full field set (`wid, word, sn, pro, wform, orig, exp, remark`), though `fetch_qp_verse()` currently SELECTs only `wid, word, sn, exp, wform`. The local DB is required for the 17 numbered books (1Sam, 2Kgs, …) that qp.php cannot serve.

## 4. Read-only discipline

This directory is a **read-only reference** — it documents what FHL produces, never what we wish it produced. Before editing `FHL_SN_FORMAT_REFERENCE.md`, verify every claim against live FHL API output (see this directory's `CLAUDE.md`), and record the probe in the reference's Appendix A revision history.
