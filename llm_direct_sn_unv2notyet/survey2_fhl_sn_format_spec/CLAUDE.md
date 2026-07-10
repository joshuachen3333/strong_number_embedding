# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# survey2_fhl_sn_format_spec/ — FHL Strong's Number Format Specification

## Purpose

Textbook-level reference for the Strong's Number notation system used by FHL (bible.fhl.net). Consolidates scattered format definitions from 10+ files across the repository into one authoritative document.

## Files

- `FHL_SN_FORMAT_REFERENCE.md` — The complete reference document covering:
  - W-prefix decode (W, H, G, A, T) including WAH with non-900x numbers
  - All tag types with real verse examples
  - Numeric classification rules
  - 900x prefix mapping with Hebrew
  - Special braced numbers
  - Morphology code table
  - Normalization pipeline
  - Cross-codebase regex reference
  - qb.php vs qp.php: two data sources, analytic vs synthetic annotation styles
  - qp.php field structure (wid, word, sn, pro, wform, orig, exp, remark), the wid=0 overview row, NT placeholder rows, OT/NT field asymmetry, and compound indicator patterns
  - Compound prepositions: 3 structural patterns with verified Genesis examples
  - Discrepancies and edge cases (including qb/qp SN disagreement)
- `ONBOARDING_qp_parsing.md` — orientation for qp.php parsing-data work: field summary, why qp matters for SN insertion (the four bedrock uses), repo access paths, links to the conceptual root (`parsing/PARSING_FOUNDATIONS.md`) and governing plan (`parsing/QP_ENRICHMENT_PLAN.md`)

## Relationship to Other Components

This spec is **read-only reference** — it documents what FHL produces, not what we generate. All components should conform to these formats:

- `sn_within_unv_selfgroup_segmentation/` — parses these formats
- `llm_direct_sn_unv2notyet/` — transfers these formats between translations
- `survey1_prompt_evolving/` — teaches LLMs to produce these formats
- `shared/js/color_mapper.js` — renders these formats in the viewer

## Verification

To spot-check the spec against live FHL data:
```bash
# Fetch raw SN-annotated verse (Genesis 1:1)
curl 'https://bible.fhl.net/json/qb.php?version=unv&chineses=創&chap=1&sec=1&strong=1'
```

## Important

- **Do not edit `FHL_SN_FORMAT_REFERENCE.md` without verifying against actual FHL API output.** The spec documents observed behavior, not desired behavior.
- The regex cross-reference (Section 8) includes line numbers — these may drift as code changes. Verify before citing.
