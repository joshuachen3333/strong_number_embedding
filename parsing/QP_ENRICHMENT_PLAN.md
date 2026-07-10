# QP-Enrichment Plan — feeding FHL Parsing Code into SN insertion

Design draft for a 4-item change set that brings FHL's **parsing code** (`qp.php`)
into our SN-insertion foundations, spec, and gold-standard pipeline.

**Status:** DRAFT — awaiting design review (advisor / owls-council) before implementation.
**Origin:** the FHL technical-group discussion distilled in
[`PARSING_FOUNDATIONS.md`](PARSING_FOUNDATIONS.md) (an FHL contributor noted "a verb carries
two tags: Strong's Number + Parsing Code"). This plan operationalizes that insight.

**Governing principle** (from PARSING_FOUNDATIONS §5/§7): our task is **Alignment**
(word-for-word or `null`); FHL parsing is **upstream input**. The parsing code is the
objective evidence that turns several LLM *guesses* into *rule-decidable* facts.

---

## 0. What the parsing code is, and how we get it (verified live)

**Endpoint** (already used in the repo by survey6/8/9):
```
GET https://bible.fhl.net/json/qp.php?engs=Gen&chap=1&sec=1
```

**Live-probed response shape** (Gen 1:1 OT, John 3:16 NT) — per-word records, `wid=0` is a
whole-verse overview row to skip:

```json
// OT
{"wid": 2, "word": "בָּרָא", "sn": "01254", "pro": "",
 "wform": "動詞，Qal 完成式 3 單陽",          // ← the Parsing Code (fine-grained)
 "orig": "בָּרָא",                            // ← lemma (dictionary headword)
 "exp": "Qal 創造；Pi‘el 砍伐；Hif‘il 肥己"}   // ← gloss
// NT
{"wid": 3, "word": "ἠγάπησεν", "sn": "00025", "pro": "動詞",
 "wform": "第一簡單過去 主動 直說語氣 第三人稱 單數",  // = V-AAI-3S
 "orig": "ἀγαπάω", "exp": "愛"}
```

**Two granularities of the same parsing code:**
- **Coarse** — inline in `qb.php?strong=1`: `<WTH8804>` / `<WTG5656>` (stem+tense only).
  Decode table already in `survey2/FHL_SN_FORMAT_REFERENCE.md` §6.
- **Fine** — `qp.php` `wform`: adds person/gender/number ("Qal 完成式 3 單陽").

**OT/NT field asymmetry** (verified): OT leaves `pro` empty and puts everything in `wform`;
NT splits part-of-speech into `pro` and puts only inflection in `wform` (empty for
indeclinables). Our current inference is OT-centric; NT expansion must handle this.

**Access, already in repo:** `survey6/run_survey6.py::fetch_qp_verse()` +
`normalize_qp_sn()` ("00430"→WH0430). Local fallback DB
`original_text_preparation/source_sqlite/bible_parsing.db` (tables `lparsing`/`fhlwhparsing`,
cols `wid, word, sn, exp, wform`) — needed for the 17 numbered books qp.php can't serve.

**Why it anchors insertion (the bedrock use):**
1. **Original word-order skeleton = the left side of alignment.** `wid` order is the original
   word sequence; insertion becomes "qp word-list → target-Chinese span (or null)". This makes
   the **null check objective**: every qp word must be either mapped or explicitly null.
2. **Multi-SN disambiguation** (PARSING_FOUNDATIONS §6 example 3): when several SN follow one
   Chinese word, the record whose `wform` says "動詞" is the verb-sense SN — rule, not guess.
3. **Compound merge** (already used by spec v1.8): `wform` "介系詞 מִן +" pattern.
4. **Richer LLM context:** `orig` (lemma) + `exp` (gloss) + `wform` (morphology) triples the
   signal vs a bare SN.

---

## 1. Item 1 — survey2 format reference doc

**File:** `llm_direct_sn_unv2notyet/survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md` §9.2

**Changes (pure doc, evidence in hand):**
- Add `orig` (lemma) and `pro` (part-of-speech) to the §9.2 field table.
- Note the `wid=0` whole-verse overview row (skip it).
- Add the OT/NT field asymmetry note (`pro` empty on OT; split on NT).

**Risk:** low. No code depends on the doc.

---

## 2. Item 2 — spec increments S1–S4

**File:** `sn_within_unv_selfgroup_segmentation/SPECIFICATION_v1.8.md` → propose **v1.9**.

| ID | Increment | Touches |
|----|-----------|---------|
| S1 | Add `lemma: string \| null` to the parsing-aux output (from qp `orig`); annotation-only, does not change grouping/morph | output schema (§5/§6.1) |
| S2 | Define the coarse/fine two-level parsing code explicitly (qb `<WTH8804>` vs qp `wform`) | §2 terminology |
| S3 | Record the OT/NT `pro`/`wform` asymmetry; flag current inference as OT-centric | §6.1 |
| S4 | One-line pointer to `parsing/PARSING_FOUNDATIONS.md` (alignment-vs-parsing framing) | header |

**Open question (for review):** S1 touches the output schema. Per repo convention
`sn_within_unv_selfgroup_segmentation/` uses **OpenSpec** for schema/breaking changes. Options:
(a) OpenSpec proposal → validate → implement; (b) direct additive v1.9 (backward-compatible,
annotation-only field). **Lean:** (a) for S1's schema touch, (b)-style additive framing so it
stays non-breaking. **Advisor to decide.**

**Risk:** medium (schema). Mitigated by additive-only, `null`-default, annotation-only.

---

## 3. Item 3 — gold pipeline qp-enrichment + deterministic morph pre-validator

**Files:** `survey1_prompt_evolving/consensus.py` (+ judge/debate context builder);
consumed by `survey10_s1_but_obe_insteadOf_oneshot/`. Neither currently uses qp/wform.

**Scope (this pass): implement the capability + write the A/B design; do NOT run the
expensive benchmark** (conserves opus / gemini-3-pro / gpt-5.4 quota).

**Capability:**
- Reuse `fetch_qp_verse()` to build a per-verse qp word-table (word/orig/sn/wform/exp).
- Inject it as **structured evidence** into Round 2/3 debate + judge context, so the judge
  arbitrates verb-attachment and null-legitimacy from morphology, not from 3-model guessing.
- Add a **deterministic pre-validator**: a morph code (8xxx) must immediately follow its
  verb-sense SN (the qp record whose `wform` contains "動詞"); violations are flagged as errors
  before consensus — saving LLM rounds.

**A/B design doc** (written, not run): same verses ± qp evidence, measure consensus rounds,
objective SN-coverage, and disagreement rate. To run later on the next s10 Gen batch.

**Risk:** high (touches consensus logic — the sole authority `build_gold_standard()` per
`ARCHITECTURE_DECISIONS.md`). Mitigation: capability behind a flag (default off), unit test for
the pre-validator, no change to `resolved_at` authority.

---

## 4. Item 4 — survey5 leaderboard ± enrichment axis

**File:** survey5 leaderboard design (spec'd in commit a082aef).

**Change:** add a benchmark axis — same model × same prompt **± qp enrichment** — turning
"does the parsing code actually help?" into a measurable proposition feeding Item 3's decision.

**Risk:** low (spec only).

---

## 5. Onboarding docs (per subdir, so future workers catch up)

`ONBOARDING_qp_parsing.md` in each touched subdir, tailored to that dir's role:
- `survey2/` — what qp fields exist and why (points to §9.2).
- `survey1_prompt_evolving/` — how qp evidence enters consensus; the pre-validator; the flag.
- `survey5_*/` — the ±enrichment axis and how to read it.
- `sn_within_unv_selfgroup_segmentation/` — v1.9 increments, lemma field, OT/NT asymmetry.
- `survey10_s1_but_obe_insteadOf_oneshot/` — s10 is a **fork** of survey1 (own
  consensus/judge/run_gold_standard copies, already diverged); qp capability landed in
  survey1 only, s10's copies untouched by design (mid-batch). Its onboarding doc records
  the porting path and that s10 is the planned track for the QP_AB_DESIGN run.
Each cross-links `parsing/PARSING_FOUNDATIONS.md` as the conceptual root.

---

## 6. Workflow shape (implementation)

Single Workflow, phases: **Draft → Review → Apply → Verify.**
- **Draft** (4 parallel, one per item): each agent produces exact edits + its onboarding doc as
  structured output. No writes yet (avoids parallel-apply hazards).
- **Review**: adversarial design-reviewer + (advisor / owls-council) gate.
- **Apply**: writes to non-overlapping paths; Item 3 also lands a unit test.
- **Verify**: spec-consistency check; run Item 3's pre-validator test; confirm no schema break.

**Open question:** parallel-direct-apply (paths are disjoint) vs draft-then-apply. **Lean:**
draft-then-apply (safer for the shared consensus file). Worktree isolation likely unnecessary
(disjoint paths). **Advisor to decide.**

---

## 7. Open questions for the reviewer (advisor)

1. **Item 2 route:** OpenSpec proposal vs direct additive v1.9?
2. **Item 3 scope:** capability + A/B design only (no benchmark run) — acceptable?
3. **Workflow apply strategy:** draft-then-apply vs parallel-direct-apply; worktree needed?
4. **Sequencing:** doc-first (1,2,4) then code (3), or all four in one workflow pass?

---

## 8. Execution order (proposed)

1. survey2 §9.2 doc (evidence in hand) — lowest risk, unblocks onboarding.
2. spec v1.9 increments S1–S4 (route per Q1).
3. gold-pipeline capability + A/B design (highest value, behind a flag).
4. survey5 ±enrichment axis.
5. onboarding docs land with each item.

Reviewed-by: _(pending advisor)_
