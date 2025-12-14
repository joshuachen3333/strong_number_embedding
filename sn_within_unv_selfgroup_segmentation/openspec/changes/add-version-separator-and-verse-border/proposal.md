# Change: Add version separator line and colored verse borders

## Why

When both UNV and KJV sections are displayed in the left panel, users need clear visual separation between the two versions. Additionally, the selected verse needs a more prominent border to distinguish it from unselected verses, with colors matching each version's toggle button.

## What Changes

- Add a thick horizontal separator line between UNV and KJV sections when both are visible
  - Blue (#3498db) on the UNV side
  - Teal (#1abc9c) on the KJV side
- Change selected verse styling from left+right border to a full rectangular border (all 4 sides)
  - UNV selected verse: blue border
  - KJV selected verse: teal border
  - Border thickness: slightly thicker than current 3px, but thinner than the separator line

## Impact

- Affected code: `viewer_v2/css/styles.css`
- No JavaScript changes required - pure CSS styling
- Colors use existing CSS variables (`--unv-color`, `--kjv-color`)
