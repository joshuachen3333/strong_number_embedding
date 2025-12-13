# Proposal: Add Single HL Checkbox to Right Panel

## Summary
Add a dedicated "Single HL" (Single Highlight) checkbox to the right panel, giving each panel independent control over highlight behavior. Update the right panel header layout to: SN Dict → Spec → Single HL.

## Motivation
Currently, the left panel has a Single HL checkbox that controls highlight behavior for **both** panels (they share the same checkbox element). This prevents users from having different highlight modes per panel. Adding a dedicated checkbox to the right panel enables independent control.

## Current Behavior
- Left panel has: `SN Dict` checkbox + `Single HL` checkbox
- Right panel has: `SN Dict` checkbox + `Spec` checkbox + toggle buttons (Parsed/Raw/Notes)
- Both panels read from the same `single-highlight-mode` checkbox in the left panel
- No way to have different Single HL settings per panel

## Proposed Behavior
- Left panel: `SN Dict` + `Single HL` (unchanged)
- Right panel: `SN Dict` + `Spec` + `Single HL` (new checkbox added)
- Each panel reads from its own checkbox
- Default: both checked (ON) for backwards compatibility

## Technical Approach

1. **HTML Changes** (`index.html`):
   - Add new checkbox `right-single-highlight-mode` after Spec checkbox
   - Layout order: SN Dict → Spec → Single HL → toggle buttons

2. **JavaScript Changes** (`right_panel.js`):
   - Change selector from `#single-highlight-mode` to `#right-single-highlight-mode`
   - No logic changes needed (same behavior, just different element)

3. **Optional: Persist setting** (if localStorage pattern already exists):
   - Save/restore `right-single-highlight-mode` state

## Impact
- **Files changed**: `viewer_v2/index.html`, `viewer_v2/js/right_panel.js`
- **Risk**: Low - isolated UI change with clear scope
- **Testing**: Verify highlight clearing works independently per panel
