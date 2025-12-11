# Parsed Verse Viewer — Specification

Version: 1.0
Date: 2025-12-06

## 1. Overview

A dual-panel web viewer for reviewing UNV+SN parsed output verse by verse. The left panel displays UNV text with Strong's Numbers, the right panel shows the parsed/grouped result. Both panels use synchronized color-coding for SN groups.

### 1.1 Purpose
- Review parser output quality
- Verify SN groupings are correct
- Identify uncertain or problematic verses
- Navigate through parsed Bible text efficiently

### 1.2 Non-Goals
- No editing capability (view-only)
- No multiple Bible versions (UNV only)
- No Strong's dictionary lookup (future enhancement)

---

## 2. Architecture

### 2.1 Directory Structure
```
viewer/
├── index.html           # Main HTML structure
├── css/
│   └── styles.css       # All styling
├── js/
│   ├── app.js           # Main controller, initialization
│   ├── left_panel.js    # Left panel (UNV reader) logic
│   ├── right_panel.js   # Right panel (parsed output) logic
│   ├── color_mapper.js  # Group-to-color mapping
│   ├── data_loader.js   # Fetch from local files & API
│   ├── navigation.js    # Keyboard & URL navigation
│   └── book_data.js     # 66 books with English/Chinese mappings
├── start_viewer.sh      # Launch script (HTTP server + browser)
└── SPEC.md              # This file
```

### 2.2 Related Files (Outside viewer/)
```
output/
├── manifest.json        # Generated list of available verses
├── Gen/1/1              # Parsed verse files
├── Gen/1/1_uncertain    # Uncertain verse files
└── ...

generate_manifest.py     # Script to create manifest.json
```

### 2.3 Dependencies
- Python 3 (for HTTP server)
- Modern browser (Chrome, Firefox, Safari)
- No build tools required

---

## 3. Data Sources

### 3.1 Primary: Local Parsed Files
- Path: `output/{Book}/{Chapter}/{verse}`
- Format: Plain text with 3 sections (see §5.2)
- Uncertain files: `{verse}_uncertain` suffix

### 3.2 Secondary: FHL API (Fallback)
- Endpoint: `https://bible.fhl.net/json/qb.php`
- Parameters: `version=unv&chineses={book}&chap={chapter}&sec={verse}&strong=1`
- Used when: Local file not found, or loading full chapter UNV text

### 3.3 Manifest File
Location: `output/manifest.json`

```json
{
  "generated": "2025-12-06T12:00:00Z",
  "books": {
    "Gen": {
      "chapters": {
        "1": {
          "verses": [1, 2, 3, ..., 31],
          "uncertain": [5, 12]
        },
        "2": {
          "verses": [1, 2, ..., 25],
          "uncertain": []
        }
      }
    },
    "Exod": { ... }
  }
}
```

---

## 4. User Interface

### 4.1 Layout
```
+----------------------------------------------------------+
| [Book ▼] [Chapter ▼]    Parsed Verse Viewer    [toggles] |
+---------------------------+------------------------------+
|                           |                              |
|   LEFT PANEL              |   RIGHT PANEL                |
|   (UNV + SN Text)         |   (Parsed Output)            |
|                           |                              |
|   All verses of chapter   |   Selected verse result      |
|   Click to select         |   Color-coded groups         |
|   Scrollable              |                              |
|                           |                              |
+---------------------------+------------------------------+
```

### 4.2 Header Controls
- **Book dropdown**: All 66 books, shows only books with parsed data highlighted
- **Chapter dropdown**: Dynamic based on selected book
- **Toggle buttons** (right side):
  - `[Parsed]` — show/hide Parsed Text section
  - `[Raw]` — show/hide Raw UNV+SN section
  - `[Notes]` — show/hide Morphology Notes section

### 4.3 Left Panel
- Displays all verses of selected chapter
- Each verse is a clickable block:
  ```html
  <div class="verse" data-verse="1">
    <span class="verse-num">1</span>
    <span class="verse-text">起初<span class="sn-group-1">&lt;WAH09002&gt;&lt;WH07225&gt;</span>，...</span>
  </div>
  ```
- Selected verse has highlight style (e.g., light blue background)
- Verses without parsed data: normal text, no color-coding
- Uncertain verses: orange left border indicator

### 4.4 Right Panel
- Shows parsed output for selected verse
- Three collapsible sections:

**Section 1: Parsed and Formatted Text**
```
<09002><07225> — 介系詞 בְּ + 名詞「開始、首要」
<0430> — 名詞「上帝、神、神明」
<01254>(8804) — 動詞「Qal 創造...」 *1
```
Each line color-coded by group.

**Section 2: Raw UNV+SN Source Text**
```
起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>...
```
SN tags color-coded to match Section 1 groups.

**Section 3: Morphology Notes**
```
*1: 動詞，Qal 完成式 3 單陽
```

**Uncertain Verse Display:**
- Yellow background on entire right panel
- Warning badge: ⚠️ at top
- Warning notes displayed prominently

**Not Parsed Display:**
- Gray text: "此節尚未解析 / Not yet parsed"
- Shows verse reference

---

## 5. Color System

### 5.1 Fixed Palette (15 colors)
```javascript
const GROUP_COLORS = [
  '#E3F2FD', // Light Blue
  '#FFF3E0', // Light Orange
  '#E8F5E9', // Light Green
  '#FCE4EC', // Light Pink
  '#F3E5F5', // Light Purple
  '#E0F7FA', // Light Cyan
  '#FFFDE7', // Light Yellow
  '#EFEBE9', // Light Brown
  '#ECEFF1', // Light Gray-Blue
  '#F1F8E9', // Light Lime
  '#FBE9E7', // Light Deep Orange
  '#E8EAF6', // Light Indigo
  '#E0F2F1', // Light Teal
  '#FFF8E1', // Light Amber
  '#F9FBE7', // Light Yellow-Green
];
```

### 5.2 Color Assignment
- Parse right panel to extract groups (one per line in Parsed Text section)
- Assign colors in order: Group 1 → color[0], Group 2 → color[1], ...
- If more than 15 groups, cycle: Group 16 → color[0]
- Same color applied to matching SN codes in left panel

### 5.3 Group-to-SN Mapping Algorithm
```javascript
// From right panel parsed text line:
// "<09002><07225> — 介系詞..."
// Extract SNs: ['09002', '07225']

function extractSNsFromLine(line) {
  const match = line.match(/^(<[^>]+>)+/);
  if (!match) return [];
  const snPattern = /<(\d+)>/g;
  const sns = [];
  let m;
  while ((m = snPattern.exec(match[0])) !== null) {
    sns.push(m[1]);
  }
  return sns;
}
```

---

## 6. Navigation

### 6.1 Mouse
- Click anywhere on verse text → select that verse
- Click verse number → same behavior

### 6.2 Keyboard
| Key | Action |
|-----|--------|
| ↑ Up | Previous verse (crosses chapter boundary if at verse 1) |
| ↓ Down | Next verse (crosses chapter boundary if at last verse) |
| ← Left | Previous chapter |
| → Right | Next chapter |
| Home | First verse of chapter |
| End | Last verse of chapter |

### 6.3 URL Hash
- Format: `#Book/Chapter/Verse` (e.g., `#Gen/1/5`)
- Updated on verse selection
- Parsed on page load to restore position
- Browser back/forward buttons work

### 6.4 localStorage
- Key: `parsedViewerLastPosition`
- Value: `{"book": "Gen", "chapter": 1, "verse": 5}`
- Saved on each verse selection
- Used when URL has no hash on initial load

### 6.5 Chapter Boundary Crossing
**Down arrow at Gen 1:31:**
1. Check manifest for Gen chapter 2
2. If exists, go to Gen 2:1
3. If not, check next book (Exod 1:1)
4. If end of Bible, stay at current verse

**Up arrow at Gen 2:1:**
1. Go to Gen 1:31 (last verse of previous chapter)

---

## 7. Data Loading

### 7.1 Initialization Sequence
```
1. Load manifest.json
2. Populate book dropdown (highlight books with data)
3. Check URL hash OR localStorage for position
4. If position found:
   a. Set dropdowns
   b. Load chapter UNV text (local first, then API)
   c. Load parsed output for selected verse
5. If no position:
   a. Default to Gen 1:1
```

### 7.2 Chapter Load
```javascript
async function loadChapter(book, chapter) {
  // 1. Try local: fetch all verses from manifest
  const verses = manifest.books[book].chapters[chapter].verses;

  // 2. For each verse, try local file first
  for (const v of verses) {
    const local = await tryFetch(`output/${book}/${chapter}/${v}`);
    if (local) {
      // Extract raw UNV+SN from Section 2
      verseData[v] = parseRawSection(local);
    }
  }

  // 3. For missing verses, fetch from API
  const missing = verses.filter(v => !verseData[v]);
  if (missing.length > 0) {
    const apiData = await fetchFromAPI(book, chapter);
    // Merge API data
  }

  // 4. Render left panel
  renderLeftPanel(verseData);
}
```

### 7.3 Verse Selection
```javascript
async function selectVerse(book, chapter, verse) {
  // 1. Update selection state
  currentVerse = { book, chapter, verse };

  // 2. Try load parsed output
  const parsed = await tryFetch(`output/${book}/${chapter}/${verse}`);
  const uncertain = await tryFetch(`output/${book}/${chapter}/${verse}_uncertain`);

  // 3. Render right panel
  if (parsed) {
    renderParsedOutput(parsed, false);
  } else if (uncertain) {
    renderParsedOutput(uncertain, true);
  } else {
    renderNotParsed(book, chapter, verse);
  }

  // 4. Apply color-coding to both panels
  applyGroupColors();

  // 5. Update URL and localStorage
  updateURL();
  savePosition();

  // 6. Scroll left panel to show selected verse
  scrollToVerse(verse);
}
```

---

## 8. Parsed Output Format

### 8.1 Three Sections
The parser outputs text with this structure:
```
Parsed and Formatted Text Section:
<SN_GROUP> — description
<SN_GROUP> — description
...

Raw UNV+SN Source Text Section:
Chinese text with <WH...> tags...

Morphology Notes Section:
*1: note
*2: note
...
```

### 8.2 Parsing Right Panel Content
```javascript
function parseParsedOutput(text) {
  const sections = {
    parsed: '',
    raw: '',
    notes: ''
  };

  const lines = text.split('\n');
  let currentSection = null;

  for (const line of lines) {
    if (line.includes('Parsed and Formatted Text Section:')) {
      currentSection = 'parsed';
    } else if (line.includes('Raw UNV+SN Source Text Section:')) {
      currentSection = 'raw';
    } else if (line.includes('Morphology Notes Section:')) {
      currentSection = 'notes';
    } else if (currentSection && line.trim()) {
      sections[currentSection] += line + '\n';
    }
  }

  return sections;
}
```

---

## 9. Scripts

### 9.1 start_viewer.sh
```bash
#!/bin/bash
# Start HTTP server and open browser

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PORT=8000

# Check if port is in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null; then
  echo "Port $PORT already in use, opening browser only..."
else
  echo "Starting HTTP server on port $PORT..."
  cd "$SCRIPT_DIR/.."
  python -m http.server $PORT &
  SERVER_PID=$!
  echo "Server PID: $SERVER_PID"
  sleep 1
fi

# Open browser
open "http://localhost:$PORT/viewer/"

echo "Press Ctrl+C to stop server"
wait
```

### 9.2 generate_manifest.py
```python
#!/usr/bin/env python3
"""Generate manifest.json from output/ directory structure."""

import os
import json
from datetime import datetime

OUTPUT_DIR = 'output'
MANIFEST_PATH = os.path.join(OUTPUT_DIR, 'manifest.json')

# List of all 66 books in order
BOOK_ORDER = [
    'Gen', 'Exod', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', 'Ruth',
    '1Sam', '2Sam', '1Kgs', '2Kgs', '1Chr', '2Chr', 'Ezra', 'Neh',
    'Esth', 'Job', 'Ps', 'Prov', 'Eccl', 'Song', 'Isa', 'Jer',
    'Lam', 'Ezek', 'Dan', 'Hos', 'Joel', 'Amos', 'Obad', 'Jonah',
    'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
    'Matt', 'Mark', 'Luke', 'John', 'Acts', 'Rom', '1Cor', '2Cor',
    'Gal', 'Eph', 'Phil', 'Col', '1Thess', '2Thess', '1Tim', '2Tim',
    'Titus', 'Phlm', 'Heb', 'Jas', '1Pet', '2Pet', '1John', '2John',
    '3John', 'Jude', 'Rev'
]

def generate_manifest():
    manifest = {
        'generated': datetime.utcnow().isoformat() + 'Z',
        'books': {}
    }

    for book in BOOK_ORDER:
        book_path = os.path.join(OUTPUT_DIR, book)
        if not os.path.isdir(book_path):
            continue

        manifest['books'][book] = {'chapters': {}}

        for chapter in sorted(os.listdir(book_path), key=lambda x: int(x) if x.isdigit() else 0):
            chapter_path = os.path.join(book_path, chapter)
            if not os.path.isdir(chapter_path):
                continue

            verses = []
            uncertain = []

            for filename in os.listdir(chapter_path):
                if filename.endswith('_uncertain'):
                    verse_num = int(filename.replace('_uncertain', ''))
                    uncertain.append(verse_num)
                    if verse_num not in verses:
                        verses.append(verse_num)
                elif filename.isdigit():
                    verses.append(int(filename))

            manifest['books'][book]['chapters'][chapter] = {
                'verses': sorted(verses),
                'uncertain': sorted(uncertain)
            }

    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"Generated {MANIFEST_PATH}")
    print(f"Books: {len(manifest['books'])}")
    total_verses = sum(
        len(ch['verses'])
        for book in manifest['books'].values()
        for ch in book['chapters'].values()
    )
    print(f"Total verses: {total_verses}")

if __name__ == '__main__':
    generate_manifest()
```

---

## 10. Book Data

### 10.1 book_data.js
Contains mapping for all 66 books:
```javascript
const BOOK_DATA = [
  { eng: 'Gen', chi: '創', chiLong: '創世記', engLong: 'Genesis', chapters: 50 },
  { eng: 'Exod', chi: '出', chiLong: '出埃及記', engLong: 'Exodus', chapters: 40 },
  // ... all 66 books
];

const BOOK_MAP_ENG = {};  // 'Gen' -> book object
const BOOK_MAP_CHI = {};  // '創' -> book object

BOOK_DATA.forEach(book => {
  BOOK_MAP_ENG[book.eng] = book;
  BOOK_MAP_CHI[book.chi] = book;
});
```

---

## 11. Error Handling

### 11.1 Network Errors
- If manifest.json fails to load: show error message, disable navigation
- If API fallback fails: show cached data or "Unable to load" message

### 11.2 Missing Data
- Book not in manifest: dropdown shows book grayed out
- Chapter not in manifest: dropdown shows chapter grayed out
- Verse not parsed: right panel shows "Not yet parsed"

### 11.3 Malformed Parsed Output
- If parsed file doesn't have expected sections: show raw content with warning

---

## 12. Future Enhancements (Out of Scope)

- Strong's dictionary lookup on SN click
- Edit mode for corrections
- Export corrected data
- Side-by-side comparison with KJV
- Search functionality
- Statistics dashboard (parsed %, uncertain %)

---

## 13. Implementation Checklist

### Phase 1: Core Structure
- [ ] Create directory structure
- [ ] Write index.html skeleton
- [ ] Write styles.css base styles
- [ ] Write book_data.js with all 66 books
- [ ] Write generate_manifest.py
- [ ] Write start_viewer.sh

### Phase 2: Data Loading
- [ ] Write data_loader.js (manifest, local files, API)
- [ ] Generate initial manifest.json
- [ ] Test data loading

### Phase 3: Left Panel
- [ ] Write left_panel.js
- [ ] Render chapter verses
- [ ] Verse click selection
- [ ] Selected verse highlighting

### Phase 4: Right Panel
- [ ] Write right_panel.js
- [ ] Parse 3 sections from output
- [ ] Toggle buttons for sections
- [ ] Uncertain verse styling

### Phase 5: Color Coding
- [ ] Write color_mapper.js
- [ ] Extract groups from parsed text
- [ ] Apply colors to right panel
- [ ] Apply matching colors to left panel

### Phase 6: Navigation
- [ ] Write navigation.js
- [ ] Keyboard handlers (arrows)
- [ ] URL hash sync
- [ ] localStorage persistence
- [ ] Chapter boundary crossing

### Phase 7: Polish
- [ ] Header dropdowns
- [ ] Scroll behavior
- [ ] Error messages
- [ ] Loading states
- [ ] Test all 66 books
