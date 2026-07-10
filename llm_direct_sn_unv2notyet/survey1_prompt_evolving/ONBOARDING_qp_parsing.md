# Onboarding — QP Parsing-Code Evidence in the Gold Consensus Pipeline

How FHL's **parsing code** (qp) enters the survey1 3-model consensus, what the
deterministic morph pre-validator does, and why the flag is **DEFAULT OFF**.

- **Conceptual root**: [`../../parsing/PARSING_FOUNDATIONS.md`](../../parsing/PARSING_FOUNDATIONS.md)
  — FHL "parsing" = lemma + morphology of the original word (our UPSTREAM input);
  the task this pipeline builds a gold standard for is **Alignment**
  (word(s)-for-word(s) or `null`).
- **Governing plan**: [`../../parsing/QP_ENRICHMENT_PLAN.md`](../../parsing/QP_ENRICHMENT_PLAN.md) §3 (this dir implements Item 3).
- **Field reference**: `../survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md` §9.2.

## What qp gives us

`qp.php` (with local fallback `original_text_preparation/source_sqlite/bible_parsing.db`,
needed for the 17 numbered books) returns per-word records of the original text:
`wid` (original word order), `word` (surface form), `orig` (lemma), `sn`, `pro`
(part of speech), `wform` (the parsing code, e.g. `動詞，Qal 完成式 3 單陽`), `exp`
(gloss). Two facts make this evidence, not decoration:

1. **Word-order skeleton** — the `wid` sequence is the left side of the alignment:
   every original word maps to a Chinese span or to `null`.
2. **Verb-sense is rule-decidable** — when several SNs crowd one Chinese word, the
   record whose parsing says 動詞 is the verb-sense SN. A morphology code
   (`<WTH8xxx>` OT / `<WTG5xxx>` NT) is inflection annotation of THAT verb — never
   a separate word (PARSING_FOUNDATIONS §3/§6 rule 3).

## The three pieces (all in this dir)

| Piece | Where | What it does |
|---|---|---|
| `qp_evidence.py` | new module | `build_qp_table(book_eng, chap, sec)` (SQLite-first, qp.php fallback; wid=0 overview row skipped; Unicode `uword`/`uorig` preferred), `validate_morph_attachment(annotated_text, qp_records)` (pure deterministic pre-validator), `format_qp_evidence(...)` (renders the judge-context block). Copy-adapted from survey6's access layer — self-contained, no survey6 import. |
| `--qp-evidence` flag | `run_gold_standard.py` | DEFAULT OFF. When ON: fetches the qp table per verse into `verse_data[vk]["qp"]`, pre-validates each R1 output (console + `_qp_morph_errors` annotation in the round1 JSON), and thereby arms the judge-context injection. Guarded import + per-verse try/except: any failure degrades to pure consensus, never blocks the run. |
| Judge injection | `judge.py::_build_qp_evidence` | R2 debate + R3 prompts gain a `{qp_evidence_block}` placeholder (right after the LCC original). GUARDED like `_build_wlc_evidence`: returns `""` when there is no qp data, so with the flag off the prompts are byte-for-byte identical to before. When on, the block shows the qp word table, the verb-sense SN list, and the pre-validator verdict per candidate output (A/B/C). |

## How evidence enters consensus (data flow)

```
--qp-evidence ON
  └─ main loop: build_qp_table() ──► verse_data[vk]["qp"] = {"records": [...]}
       ├─ R1 outputs: validate_morph_attachment() → console + _qp_morph_errors (annotation only)
       └─ R2 debate / R3 judge prompts: _build_qp_evidence()
            ├─ format_qp_evidence(records)            (word/lemma/SN/parsing/gloss table)
            └─ validate_morph_attachment(stable A/B/C) (deterministic findings per output)
R1 producers and R2 convergence NEVER see qp evidence — only judges do.
```

## The pre-validator (deterministic, no LLM)

`validate_morph_attachment` enforces: **a morphology code must immediately follow
its verb-sense SN** (the SN whose qp record is a verb reading — `動詞` in
`wform`/`pro`, or NT-SQLite `pro == "v"`). Error codes: `morph_before_any_sn`,
`morph_not_adjacent` (text intervenes), `morph_after_non_verb_sn`. Chains
(`<WH01254><WTH8804><WTH8752>`) are legal. Data-gap conservatism: no qp records →
no errors; qp lists no verb at all → adjacency-only; and if ANY verb-sense record
lacks a usable `sn`, the verb-sense check is likewise skipped (adjacency-only) —
qp's `sn` may legitimately differ from the qb inline SN
(`FHL_SN_FORMAT_REFERENCE.md` §11.4 qb/qp disagreement), so the real anchor could
be invisible to us and flagging it would inject a FALSE violation into judge
context. Input must be SHELLED text — in `--naked` mode (the default) callers
restore shells first via `shared.sn_shell.restore_shell_lookup`, the same basis
as the coverage check.
Tests: `python3 -m pytest test_qp_evidence.py -v` (fixture-only; no network, no LLM).

## What it must NEVER do (AD-1)

`build_gold_standard()` in `consensus.py` is the **sole authority** for every
`resolved_at` judgment (see `ARCHITECTURE_DECISIONS.md` AD-1). QP evidence is a
pure data provider: it never writes gold, never sets `resolved_at`, never gates a
resolution path. `consensus.py` is not modified at all. Pre-validator findings
reach the gold standard only indirectly — as judge context and as `_qp_morph_errors`
annotations inside round1 result JSONs.

## Why DEFAULT OFF

1. **Unproven benefit** — whether qp evidence actually reduces consensus rounds is
   exactly the A/B question in [`QP_AB_DESIGN.md`](QP_AB_DESIGN.md) (designed, NOT
   yet run — it costs opus/gemini-3-pro/gpt-5.4 quota on the next s10 Gen batch).
2. **Cache hygiene** — `round2_results/`/`round3_results/` caches are keyed by
   verse only, not by prompt content. Flipping the flag over existing caches
   silently mixes judgments made with and without evidence. A/B protocol therefore
   requires `--force` + a separate `--gold-dir` per arm; casual flag flips on the
   canonical caches are the main foot-gun here.
3. **Judge-context contamination risk** — like WLC, qp evidence is framed
   "evidence, NOT the verdict": FHL's translation-anchored tags may legitimately
   differ from what raw morphology suggests. Until A/B shows judges use it well,
   OFF is the safe default.

## Quick start

```bash
cd llm_direct_sn_unv2notyet/survey1_prompt_evolving
python3 -m pytest test_qp_evidence.py -v          # pre-validator unit tests (free)
python3 run_gold_standard.py --help | grep qp     # the flag
# A/B experiment: read QP_AB_DESIGN.md FIRST — do not run casually (quota).
```
