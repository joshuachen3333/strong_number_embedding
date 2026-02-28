# showoff_finished_4review/CLAUDE.md

Single-file showcase viewer for the LCC + Strong's Numbers AI transfer results.

## How to Start

```bash
# 1. Regenerate manifest (if output files changed)
cd llm_direct_sn_unv2lcc && python generate_manifest.py && cd ..

# 2. Start server
./showoff_finished_4review/start.sh
# Or manually:
python3 -m http.server 8989

# 3. Open browser
open http://localhost:8989/showoff_finished_4review/
```

No build step, no npm, no dependencies. Just a Python HTTP server for fetch API CORS.

### Remote sharing via ngrok

```bash
ngrok http 8989
# Share the https://xxx.ngrok-free.dev/showoff_finished_4review/ URL
```

**ngrok free-tier gotcha**: The free tier injects an interstitial "Visit Site" warning page for every HTTP request. Clicking through it in the browser only covers the initial page load — JavaScript `fetch()` calls for `data_bundle.json` and `books.json` also get intercepted and receive HTML instead of JSON, causing `載入失敗`. The fix is the `ngrok-skip-browser-warning: 1` header on all fetch requests (already applied in `FETCH_OPTS`).

## Data Source

All verse data is pre-bundled in `data_bundle.json` (1.5 MB) so the viewer works without access to `../llm_direct_sn_unv2lcc/output/`. To regenerate the bundle after output files change, run:

```bash
cd llm_direct_sn_unv2lcc && python generate_manifest.py && cd ..
# Then re-run the bundling script (see init() in index.html)
```

Each verse JSON contains:

| Field | Purpose |
|-------|---------|
| `unv_sn_reference` | UNV text with Strong's Numbers (left panel) |
| `lcc_sn` | LCC text with AI-inserted Strong's Numbers (right panel) |
| `lcc_original` | Plain LCC text without SN (shown in italic below right panel verses) |
| `confidence` | 0.0–1.0 AI confidence score |
| `notes` | Array of AI reasoning strings |
| `model` | LLM model used (`sonnet` or `opus`) |

The manifest (embedded in `data_bundle.json`) indexes available books/chapters/verses and low-confidence flags (threshold: 0.85).

## Architecture — Single File `index.html`

Everything lives in one HTML file: structure, styling, and logic inlined.

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ header: title | stats | lang-select                     │
├─────────────────────────────────────────────────────────┤
│ controls: book-select | chap-select                     │
├───────────────────────────┬─────────────────────────────┤
│ left panel (50%)          │ right panel (50%)           │
│ UNV+SN reference          │ LCC+SN AI output            │
│                           │ + confidence badge          │
│                           │ + model tag                 │
│                           │ + lcc_original (italic)     │
├───────────────────────────┴─────────────────────────────┤
│ notes-panel: <details> with AI reasoning per verse      │
└─────────────────────────────────────────────────────────┘
```

### i18n System

Three languages: 正體中文 (default), English, 简体中文. Controlled by `I18N` object with `t(key)` accessor.

| Mechanism | Details |
|-----------|---------|
| Static labels | `data-i18n` attribute on `<span>` elements, updated by `applyI18n()` |
| Dynamic text | `t('key')` called during render (stats, chapter labels, headings) |
| Function-type keys | `stats`, `chapLabel`, `bookName`, `chapHeadingLeft/Right` are functions that accept parameters |
| Persistence | `localStorage.showoff_lang` |
| Re-render on switch | `onLangChange()` re-populates dropdowns and re-renders current verses without re-fetching |

### Key Functions

| Function | Purpose |
|----------|---------|
| `init()` | Fetch manifest + books.json, populate dropdowns, apply i18n |
| `onLangChange()` | Switch language, re-apply all UI text, re-render current chapter |
| `applyI18n()` | Update all static i18n elements (title, headers, notes summary, `data-i18n` spans) |
| `populateBookSelect(restoreValue?)` | Fill book dropdown from manifest, optionally restore selection |
| `onBookChange()` | Fill chapter dropdown for selected book |
| `onChapChange()` | Read verses from bundle, render |
| `parseSN(text)` | Regex pipeline converting 4 SN formats to `<span class="sn">` elements |
| `snSpan(lang, num)` | Build a single SN span with `data-strong` attribute |
| `renderVerses(data, book, chap)` | Build HTML for both panels from verse data array |
| `attachSNHandlers()` | Hover = temporary highlight, Click = sticky highlight across both panels |
| `highlightSN(strong, on)` | Toggle `.highlight` on all `.sn[data-strong="..."]` (skipped if sticky active) |
| `clearStickyHighlights()` | Remove all `.highlight` + `.highlight-sticky` classes |
| `attachVerseClickHandlers(data)` | Click verse = select on both sides + show notes |
| `attachScrollSync()` | Ratio-based scroll sync between left and right panels |

### Strong's Number Parsing

`parseSN()` handles four FHL formats in order (most specific first):

1. `{<WAH09002>}`, `{<WH1234>}` — wrapped, optional prefix letters
2. `<WAH09002>`, `<WH1234>`, `<WTH8804>` — bare, optional prefix letters
3. `{H1234}`, `{G5678}` — simple wrapped
4. `(H1234)`, `(G5678)` — parenthesized

All produce: `<span class="sn" data-strong="H1234">` — the `data-strong` attribute enables cross-panel highlighting.

### SN Highlighting

Two modes:
- **Hover**: `mouseenter`/`mouseleave` toggles `.highlight` on all matching `data-strong` spans across both panels. Suppressed when sticky highlight is active.
- **Click**: Toggles `.highlight-sticky` — persists until another SN is clicked or a verse is clicked.

### Confidence Badges

| Class | Range | Color |
|-------|-------|-------|
| `.high` | >= 0.85 | Green |
| `.medium` | 0.70–0.84 | Yellow |
| `.low` | < 0.70 | Red |

### Caching

- `verseCache["Book/Chap"]` — in-memory cache of fetched verse arrays per chapter. Prevents re-fetching on book/chapter re-selection or language switch.
- `bookMap[eng]` — lookup from English book code to `{chi, chiLong, engLong}` from `shared/data/books.json`.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Single-file viewer (HTML + CSS + JS) |
| `data_bundle.json` | Pre-bundled manifest + all verse data (1.5 MB) |
| `start.sh` | Convenience launcher (`python3 -m http.server 8989` from repo root) |
| `CLAUDE.md` | This file |
