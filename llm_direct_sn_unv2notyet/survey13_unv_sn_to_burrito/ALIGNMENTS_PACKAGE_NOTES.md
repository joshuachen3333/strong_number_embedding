# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

@AGENTS.md

`AGENTS.md` (imported above) covers the **data model and how to *read* alignments** as a consumer. The notes below cover **developing this package itself** — the parts that require reading multiple files to understand.

## What this repo is

Two things share one repo: (1) a Python package, `bible_alignments`, for reading/validating word-level Bible alignments, and (2) the alignment **data** under `data/` (Scripture Burrito format: JSON records + TOML metadata + TSV source/target token tables). The published PyPI distribution is `bible-alignments`; `biblealignlib` (referenced in AGENTS.md) is a separate, same-API package — in *this* checkout the importable package is `bible_alignments`.

## Dev commands

Tooling is Poetry + tox (Python `>=3.9,<3.12`). There is no Makefile; commands are run directly.

```bash
poetry install                          # install deps + package (editable)

# Tests (pytest, with doctests — many modules carry doctest examples in module docstrings)
poetry run pytest --doctest-modules tests
poetry run pytest tests/bible_alignments/burrito/test_manager.py        # one file
poetry run pytest tests/bible_alignments/burrito/test_manager.py -k name # one test
poetry run pytest --cov=bible_alignments --cov-report=term-missing      # coverage

mypy                                    # type-check (strict: disallow_untyped_defs)
poetry run tox                          # full matrix: install + doctest pytest + mypy
poetry run mkdocs serve                 # docs site locally
```

Style: **black** line-length 120, **isort** (black profile), flake8 config in `tox.ini`. `mypy` is strict — every new function needs full type annotations.

## Package architecture (`bible_alignments/`)

Almost all consumer-facing code lives in the **`burrito/`** subpackage; the top-level package only holds shared constants, the Strong's helper, and the catalog generator.

- **`bible_alignments/__init__.py`** — path constants (`ROOT`, `DATAPATH`, `SOURCES`) and `SourceidEnum`. `SourceidEnum.get_canon()` is the single source of truth for mapping a `sourceid` → `"ot"`/`"nt"`/`"X"`; canon drives file paths and book ranges everywhere. New source texts must be added to this enum.
- **`bible_alignments/strongs.py`** — standalone Strong's-number normalization (`normalize_strongs`), independent of the burrito reader.
- **`bible_alignments/catalog.py`** — generates `data/catalog.tsv` by scanning the data tree.

### The read pipeline (the core flow to understand)

`AlignmentSet` → `Manager` → `{VerseData, AlignmentGroup}`, assembled from three readers:

1. **`AlignmentSet`** (`AlignmentSet.py`) — pure path/identity computation, no I/O until `check_files()`. From `(sourceid, targetid, targetlanguage, langdatapath, alternateid)` it derives `identifier` (`"{sourceid}-{targetid}-{alternateid}"`) and the four file paths (`sourcepath`, `targetpath`, `alignmentpath`, `tomlpath`). **All path layout conventions live here** — e.g. target TSV is `targets/{targetid}/{canon}_{targetid}.tsv`, alignment JSON is `alignments/{targetid}/{identifier}.json`. Change directory layout → change `__post_init__`.
2. **`Manager`** (`manager.py`) — a `UserDict` keyed by 8-char BCV (`BBCCCVVV`) → `VerseData`. Orchestrates `SourceReader` (`source.py`), `TargetReader` (`target.py`), and `AlignmentsReader` (`alignments.py`), groups records by verse, and **cleans bad records by default** (`keepbadrecords=False`) into `mgr.badrecords` (typed by `BadRecord`/`Reason`). `keeptargetwordpart=False` drops the 12th (part) char of *target* token IDs only.
3. **`AlignmentGroup`** (`AlignmentGroup.py`) — the serialization model: `Document` + `Metadata` + `list[AlignmentRecord]`, each record mapping source↔target selectors via `AlignmentReference`. This is what round-trips to/from the Burrito JSON.

### Token ID scheme — the subtle part

BCVWP = `BBCCCVVVWWWP` (12 chars). Two transformations are easy to get wrong:

- **Part index**: source tokens are stored as 11 chars (no part); target part index is dropped unless `keeptargetwordpart=True`.
- **Macula prefix**: in JSON, source tokens carry a canon prefix — `'o'` for OT (books 01–39), `'n'` for NT (40–66). It is **stripped on read, re-added on write** via `macula_prefixer()` / `macula_unprefixer()` in `source.py`. When comparing or constructing source IDs in code, work with the *unprefixed* form.

`BaseToken.py` is the shared base for `Source`/`Target` (also exports `asbool`, `bare_id`).

## Data layout note

`data/` is organized by ISO-639-3 language code (`eng/`, `hin/`, `arb/`, …), each containing `targets/` and `alignments/` subtrees, plus shared `sources/` (the Greek/Hebrew token TSVs) and `vref/`. `legacy/` holds pre-Burrito data. When a `Manager` is built, `langdatapath` points at one language's `data/{lang}` folder while `sourcedatapath` points at the shared `data/sources`. The `.github/workflows/publish-data.yml` action packages the data for release — code and data are versioned/released together but installed separately (`pip install` gets code only, not data).
