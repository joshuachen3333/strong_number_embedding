# Tasks: Add QP Parsing Enrichment (SPECIFICATION v1.9)

## 1. Create SPECIFICATION_v1.9.md base copy
- [x] `cp SPECIFICATION_v1.8.md SPECIFICATION_v1.9.md` (run inside `sn_within_unv_selfgroup_segmentation/`)
- [x] Confirm `SPECIFICATION_v1.8.md` untouched (`git status` shows it unmodified)

## 2. Header edits (title, status, v1.9 banner, S4 pointer)
- [x] Line 1: title `v1.8` → `v1.9`
- [x] Insert conceptual-foundations blockquote after the intro blockquote (S4)
- [x] Replace the `**狀態**` line with the 2026-07-10 status + `**v1.9 新增**` banner (keep the `**v1.8 新增**` line)

## 3. §1 summary edits
- [x] Insert `### 1.2.3 v1.9 文件級增量（qp-enrichment，S1–S4）` before `### 1.3 兼容性`
- [x] Append the v1.9 additive-compatibility bullet to §1.3

## 4. S2 — new §2.4 (two-level parsing code)
- [x] Insert `### 2.4 Parsing Code 的兩級顆粒度（v1.9 新增）` between the last §2.3 bullet and the `---` before §3.0
- [x] Verify the coarse/fine table, Gen 1:1 and John 3:16 examples, and the FHL_SN_FORMAT_REFERENCE.md §6 cross-link are present

## 5. S1 + S3 — schema and parsing-aux edits
- [x] §5.2.1: add the `lemma: string | null` bullet after the `parsing_wform` bullet
- [x] §6.1: add the `Lemma 補註（v1.9 新增）` bullet
- [x] §6.1: add subsection `#### 6.1.1 OT/NT pro/wform 欄位不對稱（v1.9 新增）` with the asymmetry table and the OT-centric warning

## 6. Changelog + references
- [x] §11: insert `### 11.1 v1.9 vs v1.8 變更（2026-07-10）` entry; renumber old 11.1→11.2, 11.2→11.3, duplicate 11.2→11.4
- [x] §12.1: append the PARSING_FOUNDATIONS.md and FHL_SN_FORMAT_REFERENCE.md entries

## 7. Authoritative-pointer updates
- [x] Root `CLAUDE.md` (repo root, "Authoritative spec" line): point to v1.9, note parser still loads v1.8
- [x] `sn_within_unv_selfgroup_segmentation/CLAUDE.md`: Project Overview sentence + File Responsibilities list
- [x] `.claude/skills/unv-sn-backparse/SKILL.md` References list: add v1.9 as authoritative doc line

## 8. Onboarding doc
- [x] Create `sn_within_unv_selfgroup_segmentation/ONBOARDING_qp_parsing.md` (content per this change's approved draft)

## 9. Validation
- [x] `openspec validate add-qp-parsing-enrichment --strict` passes
- [x] `git diff -- SPECIFICATION_v1.8.md` is empty
- [x] `python3 run_parser_temp.py --no-write 1 1` runs clean (parser still on v1.8)
- [x] Manual read-through: every v1.9 insertion is marked `（v1.9 新增）` and is additive-only
- [x] `proposal.md` carries the mandatory `## Status` line recording pre-approval by the QP_ENRICHMENT_PLAN review gate
