# Tasks: Fix Viewer Greedy Morphology Pattern

## Implementation Tasks

- [x] Update morphology pattern in `applyColorsToRawTextLegacy()` (color_mapper.js:232)
- [x] Update morphology pattern in `colorSNsInSpan()` (color_mapper.js:255)
- [x] Update morphology pattern in `applyFallbackColoring()` (color_mapper.js:273)
- [x] Update morphology pattern in `buildRegexPattern()` (color_mapper.js:140)

## Validation Tasks

- [x] Test Gen 1:6 - Click `{<WAH09001>}` → verify `<WAH09001><WH04325>` highlights on right
- [x] Test Gen 1:6 - Click `{<WH04325>}` → verify `<WAH09001><WH04325>` highlights on right
- [x] Test Gen 1:6 - Verify `{<WAH09001>}` and `{<WH04325>}` have same background color
- [x] Test Gen 1:6 - Click `{<WAH01961>}` → verify `{<WAH01961>}{<WTH8799>}` both highlight (regression test)
- [x] Verify no other verses are broken by the pattern change

## Documentation Tasks

- [x] Update prompt.history with fix summary
- [x] Commit changes with descriptive message
