# Proposal: Style Toggle Buttons with Green Text

## Summary

Change the Parsed/Raw/Notes toggle buttons in the right panel header to use green text color when unchecked (inactive), making them more easily viewable against the light gray panel header background.

## Problem

Currently, the inactive toggle buttons use blue text (`#3498db`) on a transparent background. While visible, the user has requested green text for better distinction and easier identification of which sections can be toggled on.

## Proposed Solution

Update the CSS for inactive toggle buttons to use green text and border color instead of blue.

### CSS Changes

**Before:**
```css
.panel-header-right .toggle-btn {
  border: 1px solid #3498db;
  background-color: transparent;
  color: #3498db;
}
```

**After:**
```css
.panel-header-right .toggle-btn {
  border: 1px solid #27ae60;
  background-color: transparent;
  color: #27ae60;
}

.panel-header-right .toggle-btn:hover {
  background-color: rgba(39, 174, 96, 0.1);
}
```

The active state will remain blue (`#3498db`) to maintain visual distinction between on/off states:
- **Inactive**: Green text/border - indicates "available to turn on"
- **Active**: Blue background with white text - indicates "currently on"

## Scope

- **Files affected**: `viewer_v2/css/styles.css`
- **Complexity**: Minimal - CSS color value changes only
- **Risk**: Low - purely visual enhancement with no behavioral changes

## Color Choice

Using `#27ae60` (green from the same color palette as the existing blue `#3498db`) ensures consistency with the overall design language while providing clear visual distinction.
