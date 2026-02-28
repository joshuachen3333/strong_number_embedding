# Proposal: Add KJV Toggle to Left Panel

## Summary
Add UNV/KJV toggle buttons to the left panel, allowing users to view and compare Strong's Number distributions between Chinese Union Version (UNV) and King James Version (KJV) translations while keeping the parsed output on the right panel.

## Motivation
When reviewing parsed UNV+SN output on the right panel and clicking through Strong's Numbers, users want to see how the same SNs are distributed in KJV. This cross-reference helps understand translation differences while maintaining the same underlying Hebrew/Greek root words.

## Scope

### In Scope
1. **Left Panel Header Redesign**
   - Remove "UNV+SN Text" title
   - Add [UNV] and [KJV] toggle buttons (right side of header)
   - Color-coded controls: UNV = blue (#3498db), KJV = teal (#1abc9c)
   - Each version has independent SN Dict and Single HL checkboxes
   - Checkboxes appear/disappear based on which toggle is active

2. **Data Loading**
   - Add KJV+SN fetching capability to DataLoader
   - Use FHL API with `version=kjv` parameter

3. **Content Display**
   - When UNV is active: show UNV+SN text
   - When KJV is active: show KJV+SN text
   - Both can be shown simultaneously (stacked vertically)

4. **SN Highlighting**
   - Cross-panel highlighting works for all active versions
   - Each version's Single HL setting is independent

5. **Timeout Configuration**
   - Change highlight/tooltip timeout from 10 seconds to 30 seconds

### Out of Scope
- Right panel changes (remains UNV parsed output only)
- Adding other Bible versions
- Verse number synchronization between UNV/KJV

## UI Design

### Header Layout (single row)
```
[Gen 1:4]  □SN Dict □Single HL  □SN Dict □Single HL  [UNV] [KJV]
           ═══════藍色═══════   ═══════藍綠色═══════   藍    藍綠
           (only if UNV on)     (only if KJV on)
```

### Visibility Rules
| UNV | KJV | Middle Area Shows |
|-----|-----|-------------------|
| OFF | OFF | (empty) |
| ON  | OFF | □SN Dict □Single HL (blue) |
| OFF | ON  | □SN Dict □Single HL (teal) |
| ON  | ON  | □SN Dict □Single HL (blue) │ □SN Dict □Single HL (teal) |

### Content Area
- When both versions are on, show UNV section above KJV section
- Each section has its own scrollable content area

### Colors
| Version | Toggle Button | Checkbox Labels |
|---------|---------------|-----------------|
| UNV     | #3498db (blue) | Same blue |
| KJV     | #1abc9c (teal) | Same teal |

## Technical Approach

### HTML Changes
- Update left panel header structure
- Add toggle buttons [UNV] [KJV]
- Add two sets of checkboxes with version-specific IDs

### CSS Changes
- Color-coded toggle buttons and labels
- Conditional visibility for checkbox groups
- Stacked content sections styling

### JavaScript Changes
- **data_loader.js**: Add `fetchKJVChapter()` method
- **left_panel.js**:
  - Manage UNV/KJV toggle state
  - Render content for active versions
  - Handle independent SN Dict and Single HL settings per version
- **sn_dictionary.js**: Change `HIGHLIGHT_TIMEOUT_MS` from 10000 to 30000

## Dependencies
- FHL API supports KJV with Strong's numbers (verified)
- Same SN format (<WH...>) works for both versions

## Risks
- KJV and UNV may have different verse numbering in some books
- Some SNs in parsed output may not exist in KJV (use default coloring)
