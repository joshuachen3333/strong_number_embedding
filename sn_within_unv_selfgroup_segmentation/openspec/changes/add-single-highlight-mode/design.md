# Design: Single Highlight Mode

## Architecture Overview

This feature adds a user-controllable toggle for the SN highlighting behavior implemented in `add-bidirectional-sn-highlighting`. The design leverages the existing event-driven architecture and simply gates the `clearHighlighting()` call based on checkbox state.

## Component Changes

### 1. HTML Structure (index.html)

Add checkbox to left panel header:

```html
<section class="left-panel">
  <div class="panel-header">
    <h2>UNV+SN Text</h2>
    <div class="panel-controls">
      <input type="checkbox" id="single-highlight-mode" checked>
      <label for="single-highlight-mode">Single HL</label>
    </div>
  </div>
  <div id="left-content" class="panel-content">
    ...
  </div>
</section>
```

**Placement rationale**: Left panel header keeps the control close to where highlighting occurs in the left reader.

### 2. Left Panel Logic (left_panel.js)

**State Management:**
- Add `let singleHighlightMode = true;` to track checkbox state
- Initialize in `init()` by reading checkbox and attaching change listener

**Highlighting Logic:**
Modify `handleSNClickForHighlighting()`:

```javascript
function handleSNClickForHighlighting(event) {
  const { source, groupSNs } = event;

  // Only clear if single highlight mode is ON
  if (singleHighlightMode) {
    clearHighlighting();
  }

  if (source === 'left') {
    highlightLocal(groupSNs);
  } else {
    highlightRemote(groupSNs);
  }
}
```

**Global Clear Events:**
Click-away and verse navigation should ALWAYS clear all highlights regardless of mode:
- `handleVerseSelected()`: Always calls `clearHighlighting()`
- Global click handler in app.js: Always clears highlights

### 3. Right Panel Logic (right_panel.js)

Apply same pattern to `handleSNClickForHighlighting()`:
- Add `let singleHighlightMode = true;` state variable
- Read from same checkbox (cross-panel coordination)
- Conditionally skip `clearHighlighting()` when mode is OFF

**Note**: Both panels should read the same checkbox since it's a global highlighting behavior.

### 4. CSS Styling (styles.css)

Add styling for the new control:

```css
.panel-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}

.panel-controls input[type="checkbox"] {
  cursor: pointer;
}

.panel-controls label {
  font-size: 14px;
  cursor: pointer;
  user-select: none;
}
```

## Data Flow

```
User clicks checkbox
  ↓
Change event fired
  ↓
left_panel.js updates singleHighlightMode
right_panel.js updates singleHighlightMode
  ↓
Next SN click event
  ↓
handleSNClickForHighlighting() checks singleHighlightMode
  ↓
  IF singleHighlightMode = true:
    Clear previous highlighting
    Apply new highlighting
  ELSE:
    Keep previous highlighting
    Add new highlighting
```

## Edge Cases

1. **Switching modes with active highlights:**
   - Changing checkbox state does NOT clear existing highlights
   - Next click respects new mode setting

2. **Click-away behavior:**
   - Always clears ALL highlights regardless of mode
   - Provides easy "reset" mechanism

3. **Verse navigation:**
   - Always clears ALL highlights regardless of mode
   - Prevents highlight state from persisting across verses

4. **Multiple highlights in multi-mode:**
   - No limit on number of highlighted groups
   - All use same blue/orange color scheme
   - User can click-away to clear all

## Testing Strategy

### Unit Test Scenarios
1. Checkbox defaults to checked
2. Clicking checkbox toggles state
3. Single mode ON: new click clears previous
4. Single mode OFF: multiple groups highlighted
5. Click-away clears all in both modes
6. Verse navigation clears all in both modes

### Manual Test Scenarios
1. Toggle checkbox and verify visual state
2. Highlight Gen 1:4 `<0216>`, then highlight `<0430>` in single mode (first clears)
3. Turn off single mode, highlight both `<0216>` and `<0430>` (both visible)
4. Click away - all clear
5. Multi-highlight, then navigate to verse 5 - all clear

## Performance Considerations

- Negligible: Only adds one boolean check per click
- No impact on rendering or data loading

## Backwards Compatibility

- Default state (checked) maintains current behavior
- No breaking changes to existing code
- No changes to event system or data structures

## Future Enhancements (Out of Scope)

- Keyboard shortcut to toggle mode (e.g., Ctrl+H)
- Visual indicator showing how many groups are highlighted
- Max limit on simultaneous highlights (e.g., 5 groups)
- Persistent mode preference in localStorage
