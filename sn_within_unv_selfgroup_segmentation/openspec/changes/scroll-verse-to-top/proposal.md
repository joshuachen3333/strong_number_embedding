# Proposal: Scroll Selected Verse to Top

## Problem
When a verse is selected in the left panel, it scrolls into view using `block: 'nearest'`, which keeps the verse in view with minimal scrolling. This can leave the selected verse at the bottom or middle of the panel, making it less prominent.

## Solution
Change the scroll behavior so that the selected verse always scrolls to the top of the left panel, making it consistently positioned and easier to read alongside the right panel's parsed output.

## Scope
- Change `scrollIntoView` option from `block: 'nearest'` to `block: 'start'` in left_panel.js

## Files Affected
- `viewer_v2/js/left_panel.js` - verse selection scroll behavior

## Non-Goals
- No changes to right panel scroll behavior
- No changes to navigation.js scroll behavior (SN group highlighting)
