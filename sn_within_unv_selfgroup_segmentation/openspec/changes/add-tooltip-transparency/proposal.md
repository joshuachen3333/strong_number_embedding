# Proposal: Add Tooltip Transparency

## Problem
When the SN dictionary tooltip appears near a highlighted Strong's Number, it can cover/block the highlighted text, making it difficult to see both the tooltip content and the highlighted SN simultaneously.

## Solution
Make the tooltip background semi-transparent so users can see through it to the highlighted element underneath. Use CSS `rgba()` for background-color with an adjustable alpha value (default ~0.85 for good readability while still allowing see-through).

## Scope
- CSS-only change to `.sn-dict-floating-tooltip` class
- Convert solid `background-color: #2c3e50` to `rgba(44, 62, 80, 0.85)`
- Add CSS variable `--tooltip-opacity` for easy adjustment

## Files Affected
- `viewer_v2/css/styles.css` - tooltip background styling

## Non-Goals
- No JavaScript changes
- No tooltip repositioning logic
- No new UI controls for opacity adjustment (just CSS variable for developer tuning)
