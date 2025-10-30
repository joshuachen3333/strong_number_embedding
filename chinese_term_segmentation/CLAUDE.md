# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Chinese Term Segmentation** - A sub-project of the Strong's Number Embedding Project focused on segmenting and analyzing Chinese biblical terms for accurate Strong's number alignment.

## Parent Project Context

This directory is part of the larger **Strong's Number Embedding Project** located at:
```
/Users/joshua/work/strong_number_embedding/
```

**See**: `../CLAUDE.md` for the parent project overview, which includes:
- Original text preparation (data extraction from FHL Bible databases)
- Dual Bible readers (basic and advanced variants)
- Project-wide API integration and architecture patterns

## Purpose

This sub-project addresses the challenge of word-level alignment between Chinese Bible translations and original Hebrew/Greek texts with Strong's Numbers. Key goals:

1. **Term Segmentation**: Accurately segment Chinese biblical text into meaningful terms
2. **Strong's Alignment**: Map Chinese terms to corresponding Strong's Numbers
3. **Training Data Generation**: Create datasets for AI/LLM-based Strong's number embedding
4. **Manual Annotation Support**: Provide tools to assist human translators in Strong's number placement

## Development Workflow: OpenSpec

This project uses **OpenSpec** for spec-driven development.

### Key OpenSpec Concepts

**Specs** (`openspec/specs/`) - Current truth, what IS built
- Each capability has its own directory with `spec.md` and optional `design.md`

**Changes** (`openspec/changes/`) - Proposals, what SHOULD change
- Each change includes `proposal.md`, `tasks.md`, optional `design.md`, and spec deltas

**Archive** (`openspec/changes/archive/`) - Completed changes after deployment

### Essential Commands

```bash
# List and explore
openspec list                    # List active changes
openspec list --specs            # List existing capabilities/specs
openspec show [change-id]        # Show change details
openspec show [spec-id] --type spec  # Show spec details

# Development workflow
openspec validate [change-id] --strict   # Validate before implementing
openspec diff [change-id]        # See what will change

# After deployment
openspec archive [change-id] --yes   # Archive completed change
```

### Three-Stage Workflow

**Stage 1: Planning (Create Change Proposal)**
1. Review existing specs: `openspec list --specs`
2. Choose unique `change-id` (kebab-case, verb-led: `add-*`, `update-*`)
3. Scaffold proposal files in `openspec/changes/[change-id]/`
4. Write spec deltas with requirements and scenarios
5. Validate: `openspec validate [change-id] --strict`
6. **Wait for approval before implementing**

**Stage 2: Implementation**
1. Read `proposal.md` - understand what's being built
2. Read `design.md` (if exists) - review technical decisions
3. Read `tasks.md` - get implementation checklist
4. Implement tasks sequentially
5. Update `tasks.md` checkboxes after completion

**Stage 3: Archiving**
1. After deployment, archive the change
2. Update specs if capabilities changed
3. Run `openspec archive [change-id] --yes`
4. Validate: `openspec validate --strict`

### When to Create Proposals

**Create proposal for:**
- New features or capabilities
- Breaking changes (API, data format)
- Architecture changes
- Performance optimizations that change behavior
- Security pattern updates

**Skip proposal for:**
- Bug fixes (restore intended behavior)
- Typos, formatting, comments
- Non-breaking dependency updates
- Configuration changes
- Tests for existing behavior

## Project Conventions

**See**: `openspec/project.md` for detailed conventions including:
- Code style preferences
- Architecture patterns
- Testing strategy
- Git workflow
- Domain-specific knowledge
- Technical constraints

## Integration with Parent Project

This sub-project may integrate with:

**Data Sources**:
- Bible text JSON from `../original_text_preparation/bible_text_json/`
- Strong's dictionaries from `../original_text_preparation/strong_dict_json/`
- FHL API (`https://bible.fhl.net/json/qb.php`)

**Potential Outputs**:
- Segmented Chinese terms with Strong's mappings
- Training datasets for AI/LLM models
- Annotation tools for manual Strong's number placement
- Integration with dual reader applications for word-level highlighting

## Domain Context

**Chinese Biblical Text Challenges**:
- No word boundaries in Chinese text (unlike English)
- Multiple Chinese Bible versions with different translation styles
- Need to align translated terms with original Hebrew/Greek words
- Strong's Numbers are unique identifiers for Hebrew (H1-H8674) and Greek (G1-G5624) root words

**Key Bible Versions** (from parent project):
- UNV (和合本) - Chinese Union Version with Strong's
- LCC (呂振中譯本) - Lü Zhènzhōng Translation
- RCUV2010 (和合本2010) - Revised Chinese Union Version 2010

**Strong's Number Formats**:
- `<WH1234>` / `<WG5678>` - FHL Hebrew/Greek format
- `{H1234}` / `{G5678}` - Simple format
- `(H1234)` / `(G5678)` - Parentheses format

## Current Status

This is a newly initialized sub-project. The codebase will be developed following OpenSpec's spec-driven methodology:

1. First, create specs defining capabilities
2. Then, create change proposals for new features
3. Finally, implement based on approved proposals

Check `openspec list --specs` to see what capabilities have been defined.

## Important Notes

**OpenSpec Managed Blocks**: Do not manually edit content between `<!-- OPENSPEC:START -->` and `<!-- OPENSPEC:END -->` markers. Use `openspec update` to refresh these blocks.

**Proposal Approval**: Never start implementation without proposal approval. This ensures alignment on approach before coding.

**Sequential Implementation**: Follow tasks in `tasks.md` in order. Update checkboxes only after completion to maintain accurate status.

**Validation**: Always run `openspec validate --strict` before requesting approval or after making changes to ensure spec integrity.
