# Proposal: Add QP Parsing Enrichment (SPECIFICATION v1.9)

## Change ID
`add-qp-parsing-enrichment`

## Status
**Approved** — pre-approved by the QP_ENRICHMENT_PLAN review gate (`parsing/QP_ENRICHMENT_PLAN.md`, design review 2026-07-10). Proposal and implementation land in the same pass per that plan's Item 2 decision (OpenSpec route + new additive SPECIFICATION_v1.9.md).

## Summary
Introduce SPECIFICATION_v1.9.md as an additive, document-level increment over SPECIFICATION_v1.8.md, bringing FHL's qp.php parsing-code knowledge into the authoritative spec: a `lemma` annotation-only output field (S1), explicit coarse/fine two-level parsing-code terminology (S2), the verified OT/NT `pro`/`wform` field asymmetry with an OT-centric flag on current inference (S3), and a header pointer to the conceptual root `parsing/PARSING_FOUNDATIONS.md` (S4).

## Why
The FHL data model gives a verb two tags: a Strong's Number (lemma identity) and a Parsing Code (inflection). Our spec currently uses qp.php only implicitly (compound detection, `parsing_wform`), never defines the two granularities of the parsing code, does not expose the lemma (`orig`) that qp already provides, and silently assumes OT field semantics. Downstream work (LLM SN transfer, gold-standard consensus, NT expansion) needs these facts stated in the authoritative spec. Conceptual grounding: `parsing/PARSING_FOUNDATIONS.md`; operational plan: `parsing/QP_ENRICHMENT_PLAN.md` §2.

## Scope
**In scope:**
1. New file `SPECIFICATION_v1.9.md` = full copy of v1.8 + additive-only increments S1–S4 + version header bump + v1.9 changelog entry.
2. S1: `lemma: string | null` added to the standard group schema (§5.2.1) and Parsing-aux rules (§6.1). Annotation-only, sourced from qp `orig`, default `null`, never affects grouping/morph/prefixes.
3. S2: new §2.4 defining coarse (qb inline `<WTH8804>`/`<WTG5656>`, verbal-core inflection: Hebrew stem+tense; Greek tense+voice+mood) vs fine (qp `wform`, adds person/gender/number) parsing-code levels.
4. S3: new §6.1.1 recording the OT/NT `pro`/`wform` asymmetry (OT: `pro` empty, all info in `wform`; NT: part-of-speech in `pro`, inflection only in `wform`, empty for indeclinables) and flagging current inference as OT-centric.
5. S4: header blockquote + §12.1 entries pointing to `../parsing/PARSING_FOUNDATIONS.md`.
6. Minimal authoritative-pointer updates: root `CLAUDE.md`, `sn_within_unv_selfgroup_segmentation/CLAUDE.md`, `.claude/skills/unv-sn-backparse/SKILL.md`.
7. New `ONBOARDING_qp_parsing.md` in this directory.

**Out of scope:**
- ANY change to `SPECIFICATION_v1.8.md` (must remain byte-identical — `parse_verse_v1_8.py` validates it at startup).
- ANY parser code change (`parse_verse_v1_8.py`, `run_parser_temp.py`); no `PARSER_VERSION` bump; no v1.9 parser.
- Emitting `lemma` from the current parser (spec defines the field; implementation is a future change).
- Gold-pipeline / consensus changes (Item 3 of the plan, separate change).

## Alternatives Considered
1. **Edit v1.8 in place**: rejected — `parse_verse_v1_8.py` hard-validates `SPECIFICATION_v1.8.md`'s first line against `PARSER_VERSION`, and the repo's version policy (VERSION_UPGRADE_GUIDE.md) is immutable per-version files.
2. **Full v1.9 parser release**: rejected — no behavior changes; a doc-level increment avoids a pointless parser fork.
3. **Direct edit without OpenSpec**: rejected — S1 touches the output schema; repo convention requires an OpenSpec proposal for schema changes.

## Risks
**Low:** documentation-only; additive-only; v1.8-conformant output is v1.9-conformant by construction.
**Watch items:** (a) v1.8 byte-identity must be verified after apply (`git diff` empty for that path); (b) §11 changelog renumbering fixes a pre-existing duplicate "11.2" — numbering only, content untouched; (c) pointer updates must state that the v1.8 parser still loads/validates v1.8.

## Success Criteria
1. `SPECIFICATION_v1.9.md` exists; first line reads `# UNV+SN 分組規格 v1.9（完整獨立版）`.
2. `git diff` shows zero changes to `SPECIFICATION_v1.8.md`.
3. All S1–S4 content present at §5.2.1/§6.1 (S1), §2.4 (S2), §6.1.1 (S3), header + §12.1 (S4); §11.1 changelog entry describes S1–S4.
4. `python3 run_parser_temp.py --no-write 1 1` still succeeds (parser untouched, still loads v1.8).
5. `openspec validate add-qp-parsing-enrichment --strict` passes.
6. Authoritative-spec pointers updated in the three pointer files.
