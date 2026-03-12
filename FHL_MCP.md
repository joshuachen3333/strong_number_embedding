# FHL Bible MCP Server — Research Notes

Investigated 2026-03-12. Not integrated yet.

## What It Is

[ytssamuel/FHL-MCP-Server](https://github.com/ytssamuel/FHL-MCP-Server) — a local Python MCP wrapper around the same `bible.fhl.net` HTTP API we already use directly.

## Architecture

```
Claude Code ──(stdio/MCP)──> fhl_bible_mcp (local Python process)
                                    │
                                    ▼
                           https://bible.fhl.net/api/  (FHL's existing HTTP API)
```

Not a remote service. It's a local subprocess that translates MCP tool calls into HTTP requests to `bible.fhl.net/json/qb.php`, `qp.php`, `sd.php`, etc.

## 27 MCP Tools

| Category | Tools | FHL API |
|----------|-------|---------|
| Scripture | `get_bible_verse`, `get_bible_chapter`, `search_bible`, `query_verse_citation` | `qb.php`, `qsb.php` |
| Original Language | `get_word_analysis`, `lookup_strongs`, `search_by_strongs` | `qp.php`, `sd.php` |
| Commentary | `get_commentary`, `search_commentary`, `list_commentaries` | commentary endpoints |
| Topic Study | `get_topic_study` | topic endpoints |
| Apocrypha | `get_apocrypha_verse`, `search_apocrypha`, `list_apocrypha_books` | apocrypha endpoints |
| Apostolic Fathers | `get_apostolic_fathers_verse`, `search_apostolic_fathers`, `list_apostolic_fathers_books` | patristic endpoints |
| Reference | `list_bible_versions`, `get_book_list`, `get_audio_bible`, `get_footnote` | various |
| Articles | `search_fhl_articles`, `list_fhl_article_columns` | `www.fhl.net/api/json.php` |

## Our Current FHL API Usage

| Component | Endpoint | Purpose |
|-----------|----------|---------|
| `llm_direct_sn_unv2lcc.py` | `qb.php` | Fetch UNV+SN and LCC verse text |
| `fetch_text.sh` | `qb.php` + `qp.php` | Verse text + word-by-word analysis |
| `viewer_v2` | local JSON (from FHL SQLite) | Strong's dictionary tooltips |

## What The MCP Server Adds

- **Caching**: 7-day TTL for verses, permanent for Strong's dictionary
- **Book name normalization**: Chinese/English/ID auto-conversion
- **Interactive access**: Claude Code could query FHL during conversations
- **160 unit tests, 83% coverage**: Well-tested

## What It Does NOT Add

- No new data — same `bible.fhl.net` behind the scenes
- No server to host — stdio subprocess spawned by Claude Code
- No batch optimization — still one-request-at-a-time

## Installation (If Needed Later)

```bash
git clone https://github.com/ytssamuel/FHL-MCP-Server.git
cd FHL-MCP-Server
./scripts/install.sh          # creates venv, installs deps
python scripts/generate_config.py  # generates Claude Code MCP config
```

Requires Python 3.10+. Config goes into `.claude/settings.json` under `mcpServers`.

## Decision

Not integrating now. Our direct HTTP calls work fine for batch processing. May revisit if we need interactive FHL lookups during Claude Code sessions.
