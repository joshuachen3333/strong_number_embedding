# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Strong's Number Embedding Project** — A system using AI/LLMs to (semi)automate the insertion of Strong's Numbers into Bible translations. Strong's Numbers are unique identifiers for Hebrew (OT) and Greek (NT) root words. UNV (Chinese Union Version) and KJV already have Strong's annotations from FHL (bible.fhl.net) and serve as reference data. All bible.fhl.net API usage is authorized for this project.

## Components

### `sn_within_unv_selfgroup_segmentation/` — UNV+SN Parser (Python)

Parses UNV text with Strong's Numbers into structured semantic groups. Three-stage pipeline: `fetch_text.sh` → `parse_verse_v1_8.py` → `run_parser_temp.py`. Output goes to `output/{Book}/{Chapter}/{verse}`.

```bash
# Single verse (Genesis 1:1)
python3 run_parser_temp.py 1 1
python3 run_parser_temp.py --no-write 1 1   # preview without saving

# Fetch raw data
./fetch_text.sh --engs Gen --chap 1 --sec 1
./fetch_text.sh --list                      # list all 66 book codes

# Batch parsing
./batch_parse_book.sh Gen                   # full book

# Generate manifest for viewer
python3 generate_manifest.py
```

**Authoritative spec**: `SPECIFICATION_v1.8.md` (standalone, self-contained).

**Token classification** (non-overlapping):
- Core (Strong's 1–8999): `<dddd>` or `{<dddd>}`
- Morphology (8xxx, 4-digit): `(**8ddd)` or `{8ddd}` — verbal stems/tenses
- 900x prefixes (5-digit 09000–09999 ONLY): `<09ddd>` — inseparable particles
- CRITICAL: 4-digit `<0914>` is NOT a 900x prefix — must be exactly 5 digits starting with `09`

**Output format**: Three sections in order (Parsed Text → Raw UNV+SN → Morphology Notes). Never insert commentary between sections.

**Hybrid architecture**: Rule-based parser handles ~80-90%; `ai_resolver.py` handles uncertain cases via Claude API; human review for AI confidence ≤ 0.85.

### `sn_within_unv_selfgroup_segmentation/viewer_v2/` — Parsed Verse Viewer (HTML/JS)

Event-driven web viewer with Mediator pattern, in-memory caching, Strong's Dictionary tooltips, group-based color coding.

```bash
cd sn_within_unv_selfgroup_segmentation
./viewer_v2/start_viewer.sh    # starts python http.server on port 8000
```

**MUST READ `viewer_v2/CLAUDE.md` before ANY code change.** It contains the Component Index for all JS modules and is enforced by a git pre-commit hook.

**Git pre-commit hook**: If you stage `viewer_v2/js/*.js` files without also staging `viewer_v2/CLAUDE.md`, the commit will be blocked. Always update the Component Index in `viewer_v2/CLAUDE.md` when modifying JS files. If no CLAUDE.md changes are needed, stage it anyway.

**File load order** (immutable, in index.html):
1. `mediator.js`, `ui_utils.js`, `book_data.js`
2. `data_loader.js`, `color_mapper.js`, `sn_dictionary.js`
3. `left_panel.js`, `right_panel.js`, `navigation.js`
4. `app.js` (last)

**Key pattern — group-based coloring**: Always pass `currentGroups` for position-aware coloring. Applies to both UNV AND KJV in `left_panel.js`. If one version works but the other doesn't, compare how they call the same coloring function.

**Event flow**: `VERSE_SELECT → App loads data → VERSE_SELECTED → RightPanel parses → COLORS_APPLY → LeftPanel colors`

### `llm_direct_sn_unv2notyet/` — LLM-Direct SN Transfer (Python)

Uses LLMs to transfer Strong's Number annotations from UNV to other Chinese translations (LCC, etc.). Supports 4 brands: Claude CLI, Gemini CLI, Codex CLI, and local Ollama models.

```bash
# Basic usage (default: sonnet, LCC)
python3 llm_direct_sn_unv2notyet.py --book 創 --chap 1

# With specific model/brand
python3 llm_direct_sn_unv2notyet.py --book 創 --chap 1 --model gemini-3-flash-preview
python3 llm_direct_sn_unv2notyet.py --book 創 --chap 1 --model qwen3:32b --ollama-url http://sai.fhl.net:11434

# Model reference
python3 llm_direct_sn_unv2notyet.py --model --help
```

**Key docs**:
- [CONFIDENCE_BASIS.md](llm_direct_sn_unv2notyet/CONFIDENCE_BASIS.md) — How confidence scores work (LLM self-reported vs objective SN coverage check)
- [OSS_MODEL.md](llm_direct_sn_unv2notyet/OSS_MODEL.md) — Open-source/local model benchmark results on sai.fhl.net

### `chinese_term_segmentation/` — Chinese Segmentation Framework (Python)

Segments Chinese biblical text and maps terms to Strong's Numbers using pluggable NLP engines.

```bash
cd chinese_term_segmentation
pip install -r requirements.txt

# Segment a verse
python3 segment.py --verse "Gen 1:3" --version unv
python3 segment.py --verse "創 1:1" --version unv --seg jieba

# SN-based boundary correction
python3 segment.py --engs gen --chap 3 --sec 3 --version lcc \
  --seg pkuseg --correct-with-sn --use-refinement --semantic-engine edit-distance

# Run tests
pytest tests/ -v
pytest tests/ --cov=src --cov-report=term-missing
```

**Plugin architecture**: jieba, pkuseg, LAC, Stanza segmenters. `BoundaryCorrector` uses UNV+SN boundaries as reference to correct target text segmentation.

### `dual_reader/` — Basic Dual Bible Reader (HTML/JS)

Side-by-side synchronized Bible reading. `open dual_reader/index.html` (no server needed).

### `dual_reader_right_editor/` — Advanced Dual Reader with Edit Mode (HTML/JS)

Extends `dual_reader/` with edit mode, localStorage persistence, undo/redo, A1 word highlighting, and on-click group-based verse coloring (requires `start_server.py`).

```bash
# With group coloring (requires server for parsed verse data):
python3 start_server.py                    # from repo root, port 8080
# Open http://localhost:8080/dual_reader_right_editor/

# Without server (basic mode, no group coloring):
open dual_reader_right_editor/index.html  # all features except group coloring
```

**MUST READ `dual_reader_right_editor/CLAUDE.md` before modifying.** Contains critical rules about immutable initialization sequences, state management, and anti-patterns learned from debugging.

Key rules:
- HTML checkbox is Single Source of Truth for edit mode state — never let `editModeToggle.checked` diverge from `isEditMode`
- Three-tier loading: JSON → localStorage → API fallback. Never skip API to load directly from localStorage.
- Follow checkbox logic: checked = follower, unchecked = main. Parent-child: "FL Ver Scrl" requires "FL TxT Sel". Last checkbox wins.

### `hebrew_lesson/` — Biblical Hebrew Study Resource (HTML/JS)

Flashcard app for Hebrew alphabet with Strong's Number examples. `open hebrew_lesson/alphabet_cards/index.html`. See `hebrew_lesson/CLAUDE.md` for reference tables.

### `original_text_preparation/` — Data Extraction Pipeline (Bash/SQLite)

Extracts Bible texts and Strong's dictionaries from FHL SQLite databases into JSON.

```bash
cd original_text_preparation/bible_text_json/
./extract_whole_bible_db2json2.sh -f ../source_sqlite/bible_kjv.db -d kjv
./extract_whole_bible_db2json2.sh -f ../source_sqlite/bible_little.db -d unv

cd ../strong_dict_json/
./batch_extract_strong_dictionary_words2.sh 1 9015 ot   # Old Testament
./batch_extract_strong_dictionary_words2.sh 1 1768 nt   # New Testament
```

## Architecture Patterns

### Shared Libraries (`shared/js/`)

Reusable JavaScript modules shared across multiple web applications. All web apps reference these via relative paths (e.g., `../shared/js/color_mapper.js`).

| File | Purpose | Used By |
|------|---------|---------|
| `color_mapper.js` | Group-based SN coloring engine (token pipeline, color palette, group parsing) | `viewer_v2`, `dual_reader_right_editor` |

**Convention**: When a module is needed by 2+ web apps, move it to `shared/js/`. Create symlinks at original locations for backward compatibility. Document in this table.

### Development Server (`start_server.py`)

Lightweight Python server (port 8080) that serves static files from repo root and provides an on-demand verse parsing API. Required for features that access parsed verse data (group coloring in `dual_reader_right_editor`).

```bash
python3 start_server.py              # default port 8080
python3 start_server.py --port 9000  # custom port
```

API: `GET /api/parse?chineses=創&chapter=1&verse=1` — returns parsed verse content (from pre-parsed files or on-demand parsing).

### Mediator Pattern (all web apps)

All web applications use a central event bus (MockMediator or Mediator). Components communicate ONLY through publish/subscribe — never direct calls between components.

```javascript
// CORRECT
MockMediator.publish('eventName', data);
// WRONG — never do this
rightReader.someFunction(data);
```

### Strong's Number Formats

Four formats from FHL API (all must be handled):
- `<WH1234>` / `<WG5678>` — FHL Hebrew/Greek
- `{<WH1234>}` / `{<WG5678>}` — Wrapped
- `{H1234}` / `{G5678}` — Simple
- `(H1234)` / `(G5678)` — Parentheses

### API Integration

**Bible Text**: `https://bible.fhl.net/json/qb.php?version=unv&chineses=創&chap=1&strong=1`
- Chinese abbreviations required regardless of Bible version (e.g., "創" for Genesis, "太" for Matthew)
- Response: `{record: [{sec, bible_text}, ...]}`

### OpenSpec Workflow

Used in `sn_within_unv_selfgroup_segmentation/` and `chinese_term_segmentation/` for feature planning. Proposals required before implementing new features, breaking changes, or architecture changes. Skip for bug fixes, typos, tests.

```bash
openspec list                          # active changes
openspec validate [change-id] --strict # validate before implementing
openspec archive [change-id] --yes     # after deployment
```

## Supported Bible Versions

| Code | Name | Strong's? |
|------|------|-----------|
| UNV | 和合本 (Chinese Union Version) | Yes |
| KJV | King James Version | Yes |
| ESV | English Standard Version | No |
| RCUV2010 | 和合本2010 | No |
| LCC | 呂振中譯本 | No |
| BHS | Biblia Hebraica Stuttgartensia | Hebrew OT source |
| FHLWH | FHL Westcott-Hort | Greek NT source |

## Internationalization

Web apps support English (default) and 正體中文 (Traditional Chinese). Language persists in localStorage. Dynamic UI updates via `translations` object in `app.js`.

## No Build System

All web applications are pure client-side HTML/JS/CSS — open `index.html` directly in browser. The only server requirement is `python3 -m http.server` for `viewer_v2/` (due to fetch API CORS restrictions on local files). Python components have no packaging — run scripts directly.
