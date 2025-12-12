# Proposal: Show Multiple SN Dictionary Tooltips

## Summary
When clicking on an SN group containing 2-3 Strong's Numbers (e.g., `<WAH09002><WH08432>`), display dictionary tooltips for ALL SNs in the group, not just the first one.

## Motivation
Currently, when a user clicks on an SN group like `<09002><07225>` (prefix + core), only the first SN's dictionary entry is displayed. This limits the user's ability to understand compound constructs and multi-SN expressions without multiple interactions.

## Current Behavior
- Click on `<09002><07225>` → Shows only H09002 dictionary
- `groupSNs` array is available but only `primarySN` (first element) is used
- Single tooltip per panel

## Proposed Behavior

### 2 SNs in group:
- Display 2 tooltips: one ABOVE, one BELOW the highlighted element
- Ensures highlighted text remains visible between tooltips

### 3 SNs in group:
- Display 3 tooltips with reasonable distribution:
  - Option A: 1 above, 2 below (horizontal)
  - Option B: 2 above (horizontal), 1 below
- Choose based on available screen space

### Layout Strategy:
```
┌─────────────────┐
│   Tooltip #1    │  ← Above
└─────────────────┘
    ▼ highlighted ▼
┌─────────────────┐
│   Tooltip #2    │  ← Below (or side-by-side for 3)
└─────────────────┘
```

## Technical Approach

1. **Modify `createFloatingTooltips()`**: Create tooltip pool (3 per panel)
2. **Modify `handleSNHighlight()`**: Process all `groupSNs`, not just first
3. **New `showMultipleTooltips()`**: Fetch definitions for all SNs in parallel
4. **New `positionMultipleTooltips()`**: Smart layout algorithm:
   - 2 tooltips: above + below
   - 3 tooltips: distribute vertically and horizontally

## Impact
- **Files changed**: `viewer_v2/js/sn_dictionary.js`, `viewer_v2/css/styles.css`
- **Performance**: Parallel dictionary fetches (all cached after first load)
- **User experience**: Complete information for compound SN groups
