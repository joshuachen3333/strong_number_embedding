# survey2_fhl_sn_format_spec/ — FHL Strong's Number Format Specification

## Purpose

Textbook-level reference for the Strong's Number notation system used by FHL (bible.fhl.net). Consolidates scattered format definitions from 10+ files across the repository into one authoritative document.

## Files

- `FHL_SN_FORMAT_REFERENCE.md` — The complete reference document covering:
  - W-prefix decode (W, H, G, A, T)
  - All tag types with real verse examples
  - Numeric classification rules
  - 900x prefix mapping with Hebrew
  - Special braced numbers
  - Morphology code table
  - Normalization pipeline
  - Cross-codebase regex reference
  - Discrepancies and edge cases

## Relationship to Other Components

This spec is **read-only reference** — it documents what FHL produces, not what we generate. All components should conform to these formats:

- `sn_within_unv_selfgroup_segmentation/` — parses these formats
- `llm_direct_sn_unv2notyet/` — transfers these formats between translations
- `survey1_prompt_evolving/` — teaches LLMs to produce these formats
- `shared/js/color_mapper.js` — renders these formats in the viewer
