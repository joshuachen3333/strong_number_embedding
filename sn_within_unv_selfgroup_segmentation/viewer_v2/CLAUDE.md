# viewer_v2/CLAUDE.md

**MUST READ** this file before modifying any code in `viewer_v2/`.

## Component Index

Quick reference of all functions by file. Use this to find existing solutions before adding new code.

### mediator.js — Event Bus (Mediator Pattern)
| Function | Purpose |
|----------|---------|
| `subscribe(eventType, callback)` | Register callback for event type, returns unsubscribe function |
| `unsubscribe(eventType, callback)` | Remove callback from event type |
| `publish(eventType, data)` | Broadcast event to all subscribers |
| `EVENT_TYPES` | Catalog of all event names (VERSE_SELECT, SN_CLICK, COLORS_APPLY, etc.) |

### color_mapper.js — SN Coloring Engine (Position-Based)
| Function | Purpose |
|----------|---------|
| `parseGroups(parsedText)` | Extract SN groups from parsed output, returns `[{groupIndex, sns[], text}]` |
| `createSNToColorMap(groups)` | Map each SN code to a color (multi-SN groups take priority) |
| `applyColorsToRawText(text, colorMap, groups)` | **KEY**: Color raw UNV+SN text; `groups` enables position-aware coloring |
| `applyColorsToParsedText(parsedText, groups)` | Color parsed section with group-based backgrounds |
| `extractSNsFromLine(line)` | Parse SN codes from a single line (handles `<WHxxxx>`, `{<WHxxxx>}`, `(**8xxx)`) |
| `getSNGroupFromColorMap(sn, colorMap, groups, element)` | Get all SNs in same group; uses element's actual color for repeated SNs |
| `findCorrespondingElements(sns, container, selector, groups)` | **KEY**: Find DOM elements matching SNs + color |
| `getColorForGroup(index)` | Get color from 15-color palette by group index |
| `hexToRgb(hex)` | Convert hex color to rgb() for comparison |

### left_panel.js — UNV/KJV Reader
| Function | Purpose |
|----------|---------|
| `init()` | Subscribe to events, initialize toggles and checkboxes |
| `applyColorsToUNV()` | **KEY**: Color UNV text; passes `groups` for selected verse |
| `applyColorsToKJV()` | **KEY**: Color KJV text; passes `groups` for selected verse (same as UNV) |
| `handleSNClickForHighlighting(event)` | Handle SN clicks, apply highlighting to both versions |
| `highlightInContainer(container, sns, verse, className, singleHL)` | Apply highlight class using `findCorrespondingElements` |
| `addSNClickHandlers(textEl, verseNum, version)` | Attach click handlers to SN tags |
| `getCurrentPosition()` | Returns `{book, chapter, verse}` |
| `getVerseNumbers()` | Returns sorted array of verse numbers in current chapter |
| `loadKJVData()` | Fetch KJV chapter from API |
| `clearHighlighting()` | Remove all highlight classes |

### right_panel.js — Parsed Output Viewer
| Function | Purpose |
|----------|---------|
| `init()` | Subscribe to VERSE_SELECTED, initialize toggle buttons |
| `handleVerseSelected(data)` | Parse content, create color map, publish COLORS_APPLY |
| `displayParsedVerse(...)` | Render parsed output with colors |
| `render()` | Render visible sections (Parsed/Raw/Notes) |
| `addSNClickHandlersParsed()` | Attach click handlers to `.sn-group` elements |
| `addSNClickHandlersRaw()` | Attach click handlers to `.sn-tag` elements |
| `handleSNClickForHighlighting(event)` | Handle SN clicks, apply local/remote highlighting |
| `highlightParsedLocal/Remote(sns)` | Apply highlight to parsed section |
| `highlightRawLocal/Remote(sns)` | Apply highlight to raw section |
| `addSpecTooltips(text, specRefs)` | Convert `[3.x.x]` references to tooltip spans |

### data_loader.js — Data Fetching & Caching
| Function | Purpose |
|----------|---------|
| `loadManifest()` | Load `manifest.json` with caching |
| `loadParsedVerse(book, chapter, verse)` | Load parsed output file (or `_uncertain` variant) |
| `fetchChapterFromAPI(book, chapter)` | Fetch UNV chapter from FHL API |
| `fetchKJVChapterFromAPI(book, chapter)` | Fetch KJV chapter from FHL API |
| `parseSections(content)` | Split parsed output into `{parsed, raw, notes, specRefs}` |
| `getChapters(book)` | Get available chapters for a book |
| `getVerseInfo(book, chapter)` | Get verse list for a chapter |

### navigation.js — Keyboard & URL Navigation
| Function | Purpose |
|----------|---------|
| `init()` | Initialize keyboard handlers, panel detection |
| `handleLeftPanelKeys(e)` | Arrow keys for verse/chapter navigation |
| `handleRightPanelKeys(e)` | Arrow keys for SN group navigation |
| `selectGroup(index)` | Select and highlight SN group by index |
| `navigatePreviousVerse/NextVerse()` | Verse navigation with chapter boundary handling |
| `getInitialPosition()` | Get position from URL hash or localStorage |
| `savePosition(book, chapter, verse)` | Persist position to localStorage |

### sn_dictionary.js — Strong's Dictionary Tooltips
| Function | Purpose |
|----------|---------|
| `init()` | Initialize per-panel checkboxes, create tooltip pool |
| `handleSNHighlight(data)` | Show tooltips on SN click (respects per-panel settings) |
| `showMultipleTooltipsForPanel(panel, element, sns)` | Display up to 3 tooltips for multi-SN groups |
| `fetchDefinition(snCode)` | Load definition from JSON dictionary files |
| `loadFullDictionary(testament)` | Load OT/NT dictionary with caching |
| `findHighlightedElementInPanel(panel, sns)` | Find highlighted element for tooltip positioning |
| `resetHighlightTimeout()` | Reset 30-second auto-clear timer |

### app.js — Application Controller
| Function | Purpose |
|----------|---------|
| `init()` | Initialize all modules, load manifest, populate dropdowns |
| `handleVerseSelect(data)` | Load parsed verse, publish VERSE_SELECTED |
| `handleChapterLoad(data)` | Load chapter data |
| `loadChapter(book, chapter, versePosition)` | Orchestrate chapter loading |
| `handleGlobalClick(e)` | Clear highlighting when clicking outside SN elements |

### ui_utils.js — UI Utilities
| Function | Purpose |
|----------|---------|
| `showSpinner(container, message)` | Show loading spinner overlay |
| `hideSpinner(container)` | Hide loading spinner |
| `showError(message, type)` | Show error as banner or toast |
| `showToast(message, type, duration)` | Show temporary notification |

### book_data.js — Book Mappings
| Data | Purpose |
|------|---------|
| `BOOK_DATA[]` | Array of 66 books with eng/chi abbreviations and chapter counts |
| `BOOK_MAP_ENG{}` | Lookup by English abbreviation |
| `BOOK_MAP_CHI{}` | Lookup by Chinese abbreviation |

---

## Design Patterns

### Pattern 1: Group-Based Coloring

**Problem**: Same SN (e.g., `<0853>` אֵת) appears multiple times in a verse in different semantic groups. How to distinguish them?

**Solution**: `applyColorsToRawText(text, colorMap, groups)` — the third parameter `groups` enables position-based matching.

```javascript
// CORRECT: Selected verse uses groups for position-aware coloring
const useGroups = (verseNum === currentVerse) ? currentGroups : undefined;
ColorMapper.applyColorsToRawText(text, colorMap, useGroups);

// WRONG: Passing undefined loses position awareness
ColorMapper.applyColorsToRawText(text, colorMap, undefined);  // Legacy mode
```

**Where Applied**:
- `left_panel.js:applyColorsToUNV()` — passes `currentGroups` for selected verse
- `left_panel.js:applyColorsToKJV()` — **MUST** pass `currentGroups` for selected verse (same as UNV)
- `right_panel.js:render()` — passes `currentGroups` for raw section

**Anti-Pattern**: If Version A (UNV) has correct behavior but Version B (KJV) doesn't, **compare how they call the same function** — the fix is usually passing the same parameters.

---

### Pattern 2: Color-Based Element Filtering

**Problem**: When highlighting SNs across panels, how to highlight only the correct occurrence of a repeated SN?

**Solution**: `findCorrespondingElements(sns, container, selector, groups)` matches elements by both SN code AND background color.

```javascript
// This finds elements that match BOTH the SN codes AND the group's color
const elements = ColorMapper.findCorrespondingElements(
  groupSNs,           // SN codes to find
  container,          // DOM container to search
  '.sn-tag',          // CSS selector
  currentGroups       // Groups for color-based filtering
);
```

**Prerequisite**: The container must have group-based coloring applied (via `applyColorsToRawText` with groups). Without this, color filtering cannot work.

---

### Pattern 3: Mediator Event Flow

**Problem**: Components need to communicate without direct coupling.

**Solution**: All cross-component communication goes through `Mediator.publish/subscribe`.

```
User clicks verse → LeftPanel publishes VERSE_SELECT
                  → App handles, loads data, publishes VERSE_SELECTED
                  → RightPanel handles, parses groups, publishes COLORS_APPLY
                  → LeftPanel handles, applies colors to UNV/KJV
```

**Key Events**:
- `VERSE_SELECT` — Request to select a verse
- `VERSE_SELECTED` — Verse data loaded and ready
- `COLORS_APPLY` — Color map ready for application
- `SN_CLICK` — Strong's Number clicked (triggers highlighting + tooltip)

---

## Anti-Patterns (禁止事項)

### 1. 疊床架屋 (Redundant Components)

**FORBIDDEN**: Adding new functions when existing ones can be extended.

Before adding ANY new function, ask:
1. "Does another version (UNV/KJV) already solve this?"
2. "Can I compare how UNV calls vs KJV calls the same function?"
3. "Is the fix just passing the correct parameters?"

**Example** (from 2024-12-14 bug fix):
```
BUG: KJV highlighting wrong SNs
WRONG: Add new position-tracking functions
CORRECT: Pass `currentGroups` to KJV's applyColorsToRawText (same as UNV)
```

### 2. Direct Component Calls

**FORBIDDEN**: Calling functions between modules directly.

```javascript
// WRONG
RightPanel.highlightSN(snCode);

// CORRECT
Mediator.publish(Mediator.EVENT_TYPES.SN_CLICK, { snCode, ... });
```

### 3. Bypassing Color Filtering

**FORBIDDEN**: Highlighting SNs without respecting group colors.

```javascript
// WRONG: Highlights ALL occurrences of the SN
container.querySelectorAll('.sn-tag').forEach(el => {
  if (el.textContent.includes(snCode)) el.classList.add('clicked');
});

// CORRECT: Highlights only the matching color group
const elements = ColorMapper.findCorrespondingElements(sns, container, '.sn-tag', groups);
elements.forEach(el => el.classList.add('clicked'));
```

---

## Pre-Task Checklist

Before fixing ANY bug in viewer_v2:

- [ ] **If Version B is broken but Version A works**: Compare how A and B call the same function
- [ ] **Search for similar code**: `grep -r "functionName" viewer_v2/js/`
- [ ] **Check if fix already exists elsewhere**: Read this CLAUDE.md component index
- [ ] **Before adding new function**: Explain why existing functions cannot solve it

When adding a parallel component (e.g., KJV viewer alongside UNV):

- [ ] **Feature parity check**: Diff the new component against the original to ensure ALL behaviors are replicated
- [ ] **UX details matter**: Scroll behavior, focus states, animations — not just "core" functionality

---

## File Load Order

Scripts must load in this order (defined in `index.html`):

1. **Core**: `mediator.js`, `ui_utils.js`, `book_data.js`
2. **Services**: `data_loader.js`, `color_mapper.js`, `sn_dictionary.js`
3. **UI Components**: `left_panel.js`, `right_panel.js`, `navigation.js`
4. **Controller**: `app.js` (initializes everything)

---

## Maintenance Rule (維護規則)

**本文件必須與程式碼同步。** 這不是建議，是強制要求。

### 機制一：Git Pre-Commit Hook

已安裝 `hooks/pre-commit`，當你修改 `viewer_v2/js/*.js` 但沒有同時修改 `viewer_v2/CLAUDE.md` 時，**commit 會被阻止**。

安裝方式（已完成）：
```bash
ln -sf ../../sn_within_unv_selfgroup_segmentation/viewer_v2/hooks/pre-commit .git/hooks/pre-commit
```

### 機制二：Session 結束前檢查

**Claude 必須在每次 session 結束前執行：**

如果本次 session 修改了 `viewer_v2/js/*.js`，回答以下問題：

| 檢查項目 | 是/否 | 若「是」的動作 |
|---------|------|---------------|
| 新增了函數？ | | 加到 Component Index 表格 |
| 刪除了函數？ | | 從 Component Index 移除 |
| 改變了函數簽名或行為？ | | 更新對應描述 |
| 發現了新的設計模式？ | | 加到 Design Patterns |
| 踩到了新的坑（反模式）？ | | 加到 Anti-Patterns |

**任一項為「是」但未更新本文件 → 不得結束 session 或 commit。**

### 為什麼這麼嚴格？

2024-12-14 的教訓：KJV 高亮 bug 本可一行修復（複用 UNV 的 `groups` 參數），但因為沒有查閱現有元件索引，導致疊床架屋寫了三個不必要的函數，浪費時間且增加維護成本。

**文件與程式碼同步 = 避免重複造輪子的基礎。**

---

## Quick Debugging Commands

```bash
# Find all uses of a function
grep -rn "applyColorsToRawText" viewer_v2/js/

# Compare UNV vs KJV implementations
grep -A5 "applyColorsToUNV\|applyColorsToKJV" viewer_v2/js/left_panel.js

# Find event publishers/subscribers
grep -rn "Mediator.publish\|Mediator.subscribe" viewer_v2/js/
```
