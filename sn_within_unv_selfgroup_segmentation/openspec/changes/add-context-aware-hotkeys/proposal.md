# Proposal: Context-Aware Hotkeys for Viewer

## Summary

Add context-aware keyboard navigation to the Parsed Verse Viewer. Hotkeys will behave differently depending on which panel (left or right) is currently active. The active panel is determined by mouse hover position or most recent click on an SN group.

## Problem Statement

Currently, all hotkeys (↑↓←→, Home, End) operate on verse-level navigation in the left panel regardless of user focus. When users are reviewing parsed output in the right panel, they cannot use keyboard navigation to move between SN groups within a verse. This forces users to click on each SN group manually, which is inefficient for review workflows.

## Proposed Solution

### Active Panel Detection

1. **Left panel active** when:
   - Mouse is hovering over the left panel area
   - User clicked on a verse or left-side SN tag

2. **Right panel active** when:
   - Mouse is hovering over the right panel area
   - User clicked on an SN group in the parsed section (Section 1)

### Hotkey Behavior

#### Left Panel Active (Current Behavior)

| Key | Function |
|-----|----------|
| ↑ (Arrow Up) | Navigate to previous verse (wraps to previous chapter/book) |
| ↓ (Arrow Down) | Navigate to next verse (wraps to next chapter/book) |
| ← (Arrow Left) | Navigate to previous chapter (wraps to previous book) |
| → (Arrow Right) | Navigate to next chapter (wraps to next book) |
| Home | Jump to first verse of current chapter |
| End | Jump to last verse of current chapter |

#### Right Panel Active (New Behavior)

**Note:** Navigation applies only to **Section 1: "Parsed and Formatted Text Section"**. The Raw and Notes sections are not navigable via keyboard.

| Key | Function |
|-----|----------|
| ↑ (Arrow Up) | Select previous SN group in Parsed section; if at first group, go to previous verse |
| ↓ (Arrow Down) | Select next SN group in Parsed section; if at last group, go to next verse |
| ← (Arrow Left) | Navigate to previous verse |
| → (Arrow Right) | Navigate to next verse |
| Home | Select first SN group in current verse's Parsed section |
| End | Select last SN group in current verse's Parsed section |

### Visual Feedback

- Currently selected SN group in the right panel should have a distinct highlight style (e.g., border or brighter background)
- When navigating with keyboard in right panel mode, both the right panel SN group AND its corresponding left panel SN tags should highlight together (bidirectional highlighting)

## Dependencies

- Requires clickable SN groups in the parsed section (Section 1) of the right panel
- Builds on existing bidirectional SN highlighting feature (if present)

## Out of Scope

- Keyboard navigation within Raw or Notes sections
- Custom key bindings
- Focus management for screen readers (future accessibility enhancement)
