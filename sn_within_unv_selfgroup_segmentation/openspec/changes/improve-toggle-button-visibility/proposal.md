# Proposal: Improve Toggle Button Visibility

## Summary

Enhance the visual contrast of the Parsed/Raw/Notes toggle buttons in the right panel header when they are in the inactive (unchecked) state. Currently, the transparent background blends with the light gray panel header background (`#ecf0f1`), making inactive buttons hard to distinguish.

## Problem

After moving the toggle buttons from the global dark header to the right panel's light gray header:
- **Active state**: Blue background (`#3498db`) with white text - clearly visible
- **Inactive state**: Transparent background with blue border/text - blends with `#ecf0f1` background

Users find it difficult to identify which sections are toggled off because the inactive buttons lack sufficient visual contrast.

## Proposed Solution

Add a white background to inactive toggle buttons to create clear visual distinction from the panel header background.

### CSS Changes

**Before:**
```css
.toggle-btn {
  background-color: transparent;
  /* ... other styles ... */
}
```

**After:**
```css
.toggle-btn {
  background-color: white;
  /* ... other styles ... */
}
```

## Scope

- **Files affected**: `viewer_v2/css/styles.css`
- **Complexity**: Minimal - single CSS property change
- **Risk**: Low - purely visual enhancement with no behavioral changes

## Alternatives Considered

1. **Light blue tint background** (`rgba(52, 152, 219, 0.1)`) - More subtle but less contrast
2. **Darker border** - Would require more changes and might clash with active state
3. **Different text color** - Could reduce accessibility

Recommendation: White background provides maximum contrast while maintaining the existing color scheme.
