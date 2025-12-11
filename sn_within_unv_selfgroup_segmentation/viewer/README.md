# Parsed Verse Viewer

A dual-panel web viewer for reviewing UNV+SN parsed output verse by verse.

## Quick Start

1. **Generate manifest** (first time or after adding new parsed verses):
   ```bash
   cd /Users/joshua/work/strong_number_embedding/sn_within_unv_selfgroup_segmentation
   python generate_manifest.py
   ```

2. **Start the viewer**:
   ```bash
   cd viewer
   ./start_viewer.sh
   ```

3. The viewer will open in your browser at `http://localhost:8000/viewer/`

## Features

### Left Panel (UNV Reader)
- Displays all verses of selected chapter with Strong's Numbers
- Click any verse to select and view parsed output
- Color-coded SN groups matching right panel
- Uncertain verses marked with orange left border

### Right Panel (Parsed Output)
- Shows three sections (toggleable):
  - **Parsed and Formatted Text** — Grouped SNs with descriptions
  - **Raw UNV+SN Source Text** — Original text with tags
  - **Morphology Notes** — Verbal forms and notes
- Color-coded groups matching left panel
- Warning badge for uncertain verses

### Navigation

**Mouse:**
- Click verse text to select
- Click book/chapter dropdowns to navigate

**Keyboard:**
- `↑` Up — Previous verse (crosses chapter boundaries)
- `↓` Down — Next verse (crosses chapter boundaries)
- `←` Left — Previous chapter
- `→` Right — Next chapter
- `Home` — First verse of chapter
- `End` — Last verse of chapter

**URL & Storage:**
- URL reflects position: `#Gen/1/5` (bookmarkable)
- Position saved to localStorage (restored on reload)

## Files

```
viewer/
├── index.html              # Main HTML
├── css/
│   └── styles.css          # Styling
├── js/
│   ├── app.js              # Main controller
│   ├── book_data.js        # 66 books mapping
│   ├── color_mapper.js     # Color coding logic
│   ├── data_loader.js      # Data fetching (local + API)
│   ├── left_panel.js       # Left panel logic
│   ├── right_panel.js      # Right panel logic
│   └── navigation.js       # Keyboard & URL navigation
├── start_viewer.sh         # Launch script
├── SPEC.md                 # Full specification
└── README.md               # This file
```

## Data Sources

- **Primary:** Local files `../output/{Book}/{Chapter}/{verse}`
- **Fallback:** FHL API `bible.fhl.net` for UNV+SN text
- **Manifest:** `../output/manifest.json` (lists available verses)

## Updating Manifest

After batch parsing new verses:
```bash
python generate_manifest.py
```

The viewer will warn if manifest is older than 1 day.

## Troubleshooting

**"manifest.json not found"**
- Run `python generate_manifest.py` first

**"Port 8000 already in use"**
- Another server is running, or
- Use different port: `python -m http.server 8001`

**Colors not showing**
- Check that parsed files have "Parsed and Formatted Text Section"
- Verify SN format: `<dddd>` or `(**dddd)` or `{<dddd>}`

**Verse shows "Not yet parsed"**
- File doesn't exist in `output/{Book}/{Chapter}/{verse}`
- Or API fallback failed (check network)

## Browser Requirements

- Modern browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- localStorage supported
- Fetch API supported

## Development

See `SPEC.md` for detailed architecture and implementation notes.
