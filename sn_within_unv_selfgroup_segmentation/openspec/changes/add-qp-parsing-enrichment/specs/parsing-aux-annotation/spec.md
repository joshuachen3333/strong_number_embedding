# Specification: Parsing Aux Annotation (qp-enrichment, SPECIFICATION v1.9)

Defines qp.php-sourced annotation knowledge in the authoritative parsing specification: lemma annotation field, two-level parsing-code terminology, OT/NT field asymmetry, and conceptual-foundations linkage.

## ADDED Requirements

### Requirement: Lemma annotation-only output field
The specification SHALL define a `lemma: string | null` annotation-only field in the standard group output schema, sourced from the qp.php `orig` field, defaulting to `null`, and never affecting grouping, morph, or prefix decisions.

**Rationale:** qp.php already provides the dictionary headword (`orig`); exposing it enriches downstream LLM/alignment context at zero behavioral cost.

#### Scenario: qp record available for a word
**Given:** SPECIFICATION_v1.9.md §5.2.1 and §6.1, and a group whose core SN has a matching qp.php record with `orig` = "בָּרָא"
**When:** an implementation emits the v1.9 output schema with qp assistance enabled
**Then:**
- The group MAY carry `lemma: "בָּרָא"`
- `lemma` never alters `core`, `prefixes`, `morph`, `pre_brace`, `post_brace`, or any merge decision

#### Scenario: qp record unavailable or qp assistance disabled
**Given:** a group with no matching qp record, or qp assistance turned off
**When:** the v1.9 output schema is emitted
**Then:**
- `lemma` is `null` (the default)
- Output is otherwise identical to v1.8 output for the same verse

#### Scenario: v1.8 output evaluated against v1.9
**Given:** any output conforming to SPECIFICATION_v1.8.md §5.2.1
**When:** validated against SPECIFICATION_v1.9.md
**Then:** it conforms (absent `lemma` is read as `null`); the schema change is strictly additive

### Requirement: Coarse and fine two-level parsing code terminology
The specification SHALL define the two granularities of the FHL parsing code: the coarse level (qb.php inline `<WTH8804>`/`<WTG5656>` tokens carrying verbal-core inflection — Hebrew stem+tense, Greek tense+voice+mood) and the fine level (qp.php `wform` strings adding person/gender/number).

**Rationale:** The same morphological information appears at two granularities in FHL data; the spec must name both to prevent conflation.

#### Scenario: Reader looks up an inline morph token (coarse)
**Given:** SPECIFICATION_v1.9.md §2.4 and the qb.php inline token `<WTH8804>` for Gen 1:1 בָּרָא
**When:** the reader consults §2.4
**Then:** the token is identified as the COARSE level (verbal-core inflection only, = the spec's morph 8xxx token), with the decode table referenced in FHL_SN_FORMAT_REFERENCE.md §6

#### Scenario: Reader looks up a qp wform string (fine)
**Given:** the qp.php `wform` value 「動詞，Qal 完成式 3 單陽」 (OT) or 「第一簡單過去 主動 直說語氣 第三人稱 單數」 (NT, = V-AAI-3S)
**When:** the reader consults §2.4
**Then:** the string is identified as the FINE level: coarse content plus person/gender/number, surfaced in the spec via the `parsing_wform` annotation

### Requirement: OT and NT pro/wform field asymmetry documentation
The specification SHALL record the verified OT/NT asymmetry of the qp.php `pro` and `wform` fields and SHALL flag the current parsing inference rules as OT-centric.

**Rationale:** Verified live behavior: OT leaves `pro` empty and packs everything into `wform`; NT splits part-of-speech into `pro`. Current spec inference assumes OT semantics; undocumented, this breaks NT expansion silently.

#### Scenario: OT qp record
**Given:** an OT qp.php record, e.g. `{"pro": "", "wform": "動詞，Qal 完成式 3 單陽"}`
**When:** interpreted per SPECIFICATION_v1.9.md §6.1.1
**Then:** part-of-speech and inflection are BOTH read from `wform`; `pro` is expected empty

#### Scenario: NT qp record
**Given:** an NT qp.php record, e.g. `{"pro": "動詞", "wform": "第一簡單過去 主動 直說語氣 第三人稱 單數"}`
**When:** interpreted per §6.1.1
**Then:** part-of-speech is read from `pro`; `wform` carries inflection only, and MAY be empty for indeclinable words

#### Scenario: Implementer extends wform pattern matching to the NT
**Given:** the existing OT-centric rules (§6.1 inferred prefixes, §3.3 compound detection via wform patterns like 「介系詞 מִן +」)
**When:** the implementer consults §6.1.1
**Then:** a ⚠️ note states these rules are OT-centric and NT handling must branch on `pro` first

### Requirement: Conceptual foundations linkage
The specification SHALL link the conceptual foundations document `parsing/PARSING_FOUNDATIONS.md` from its header and from its related-documents section.

**Rationale:** The alignment-vs-parsing framing (`parsing/PARSING_FOUNDATIONS.md`) is the conceptual root of the SN-insertion task; the authoritative spec must anchor to it.

#### Scenario: Reader opens SPECIFICATION_v1.9.md
**Given:** the file header and §12.1
**When:** the reader looks for conceptual grounding
**Then:**
- A header blockquote links `../parsing/PARSING_FOUNDATIONS.md` and states the task is Alignment (word(s)-for-word(s) or null) with FHL parsing as upstream input
- §12.1 lists both `../parsing/PARSING_FOUNDATIONS.md` and `../llm_direct_sn_unv2notyet/survey2_fhl_sn_format_spec/FHL_SN_FORMAT_REFERENCE.md`

### Requirement: Additive versioning with v1.8 immutable
The specification versioning SHALL remain additive: SPECIFICATION_v1.9.md is a new standalone file and SPECIFICATION_v1.8.md SHALL remain byte-identical to its pre-change state.

**Rationale:** `parse_verse_v1_8.py` validates `SPECIFICATION_v1.8.md` at startup; the repo uses immutable per-version spec files.

#### Scenario: v1.9 introduced alongside v1.8
**Given:** SPECIFICATION_v1.9.md is added to the repository
**When:** `python3 run_parser_temp.py --no-write 1 1` runs
**Then:**
- `SPECIFICATION_v1.8.md` is byte-identical to its pre-change state
- The parser still loads and validates SPECIFICATION_v1.8.md successfully
- SPECIFICATION_v1.9.md §11.1 documents S1–S4 as additive-only
