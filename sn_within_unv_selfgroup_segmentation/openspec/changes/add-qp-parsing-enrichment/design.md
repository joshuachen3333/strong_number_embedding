# Design: Add QP Parsing Enrichment (SPECIFICATION v1.9)

## Decision 1 — New additive file, not in-place edit
`parse_verse_v1_8.py` (`PARSER_VERSION = "v1.8"`) loads `SPECIFICATION_v1.8.md` by exact name and validates the first line contains `v1.8` (see VERSION_UPGRADE_GUIDE.md). The repo's version policy is immutable per-version spec files. Hence v1.9 is a NEW file created as `cp v1.8 → v1.9` plus targeted anchored insertions; v1.8 stays byte-identical and the running parser is unaffected.

## Decision 2 — Document-level version, no parser fork
S1–S4 change no behavior: S2/S3/S4 are terminology/documentation; S1 defines an optional, `null`-default annotation field. A v1.9 parser file would duplicate 1000+ lines for zero behavioral delta. The spec version therefore advances ahead of the parser version; pointer files state this explicitly so nobody "fixes" the mismatch by editing v1.8.

## Decision 3 — lemma is annotation-only, sibling of parsing_wform
`lemma` mirrors the existing `parsing_wform` contract exactly: sourced from qp.php (field `orig`), written as a side annotation, default `null`, forbidden from influencing grouping/token classification. This keeps the v1.6→v1.9 output schema strictly backward compatible (consumers that ignore unknown fields see no change).

## Decision 4 — Changelog renumbering inside the new file only
v1.8's §11 contains two subsections both numbered "11.2" (pre-existing typo). In the new v1.9 file the history becomes 11.1 (new, v1.9) / 11.2 / 11.3 / 11.4 — numbering only, entry content untouched. v1.8 keeps its typo, per byte-identity.

## Decision 5 — OT/NT asymmetry placed under §6.1 (Parsing 輔助)
The asymmetry matters exactly where qp data is consumed (inferred prefixes, wform pattern matching, future lemma extraction), so it lives as §6.1.1 next to those rules rather than in §2 terminology. §2.4 (coarse/fine) is terminology and lives in the Token System chapter.

## Decision 6 — Coarse-level wording is language-aware
The coarse level (`<WTH8804>` / `<WTG5656>`) is defined as "verbal-core inflection" — Hebrew: stem+tense; Greek: tense+voice+mood — rather than the Hebrew-only "stem+tense", so the §2.4 table is consistent with its own John 3:16 example.

## Non-goals
- No implementation of lemma emission in this change.
- No change to `build_gold_standard()` / consensus logic (plan Item 3, separate change).
- No NT parsing support — S3 only documents the asymmetry and flags OT-centrism.
