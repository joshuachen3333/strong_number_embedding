# Design: Bidirectional SN Highlighting

## Architecture Overview

The highlighting system extends the existing event-driven architecture using the Mediator pattern. Three panels (left, right-Parsed, right-Raw) communicate through `SN_CLICK` events to coordinate highlighting.

```
┌─────────────────────────────────────────────────────────────┐
│                        Mediator                              │
│                      (SN_CLICK events)                       │
└────────────┬──────────────┬──────────────┬──────────────────┘
             │              │              │
             ▼              ▼              ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │   Left   │   │  Right   │   │  Right   │
      │  Panel   │   │  Parsed  │   │   Raw    │
      │          │   │          │   │          │
      │  Blue /  │   │  Blue /  │   │  Blue /  │
      │  Orange  │   │  Orange  │   │  Orange  │
      └──────────┘   └──────────┘   └──────────┘
```

## Event Flow

### Example: User clicks left panel SN

1. User clicks `<WH0216>` in left panel
2. Left panel publishes `SN_CLICK`:
   ```javascript
   {
     source: 'left',
     snCode: '0216',
     groupSNs: ['0853', '0216'],  // from colorMap
     element: <DOM reference>
   }
   ```
3. All three panels receive event:
   - **Left panel**: Applies `.clicked-local` (blue) to self
   - **Right Parsed**: Applies `.clicked-remote` (orange) to `{<WH0853>}<WH0216>` group
   - **Right Raw**: Applies `.clicked-remote` (orange) to all `<WH0216>` tags

### Example: User clicks right Parsed section

1. User clicks `{<WH0853>}<WH0216>` in right Parsed section
2. Right panel publishes `SN_CLICK`:
   ```javascript
   {
     source: 'right-parsed',
     snCode: '0216',           // primary SN
     groupSNs: ['0853', '0216'], // all SNs in group
     element: <DOM reference>
   }
   ```
3. All panels receive event:
   - **Right Parsed**: Applies `.clicked-local` (blue) to clicked group
   - **Right Raw**: Applies `.clicked-local` (blue) to all tags in `['0853', '0216']`
   - **Left panel**: Applies `.clicked-remote` (orange) to all tags in `['0853', '0216']`

## Data Structures

### Color Map (existing)
```javascript
{
  '0853': '#E8F5E9',  // Group 2 color
  '0216': '#E8F5E9',  // Same group (first occurrence wins)
  '03588': '#FCE4EC'  // Group 3 color
}
```

### Groups Array (existing)
```javascript
[
  { groupIndex: 0, sns: ['0430'], text: '...' },
  { groupIndex: 1, sns: ['07200'], text: '...' },
  { groupIndex: 2, sns: ['0853', '0216'], text: '{<WH0853>}<WH0216>...' },
  { groupIndex: 3, sns: ['03588'], text: '...' }
]
```

### Finding Group Members

Given a clicked SN code (e.g., `'0216'`), find all related SNs:

```javascript
function getSNGroupFromColorMap(clickedSN, colorMap, groups) {
  // Get the color assigned to clicked SN
  const targetColor = colorMap[clickedSN];
  if (!targetColor) return [clickedSN];

  // Find the group that has this color
  for (const group of groups) {
    const groupColor = getColorForGroup(group.groupIndex);
    if (groupColor === targetColor) {
      return group.sns;  // ['0853', '0216']
    }
  }

  return [clickedSN];  // Fallback to single SN
}
```

## DOM Element Selection

### Left Panel
- SNs wrapped in `.sn-tag` spans
- Find by checking `textContent` contains SN code
- Multiple elements may match (e.g., two `<WH0216>` instances)

### Right Parsed Section
- Groups wrapped in `.sn-group` spans
- Each group contains multiple SNs (e.g., `<WH0853><WH0216>`)
- Find by checking if any SN in group matches target SNs

### Right Raw Section
- SNs wrapped in `.sn-tag` spans
- May include morphology codes (e.g., `<WH0216><WTH8799>`)
- Find by checking `textContent` contains SN code

## Highlighting Algorithm

### When source = 'left'
```javascript
handleSNClick(event) {
  if (event.source === 'left') {
    // Apply blue to self (local)
    leftPanel.highlightLocal(event.groupSNs);

    // Apply orange to right panels (remote)
    rightPanel.highlightParsedRemote(event.groupSNs);
    rightPanel.highlightRawRemote(event.groupSNs);
  }
}
```

### When source = 'right-parsed' or 'right-raw'
```javascript
handleSNClick(event) {
  if (event.source.startsWith('right-')) {
    // Apply blue to both right sections (local)
    rightPanel.highlightParsedLocal(event.groupSNs);
    rightPanel.highlightRawLocal(event.groupSNs);

    // Apply orange to left panel (remote)
    leftPanel.highlightRemote(event.groupSNs);
  }
}
```

## CSS Implementation

### Highlight Classes
```css
.sn-tag.clicked-local,
.sn-group.clicked-local {
  background-color: #1e88e5 !important;  /* Deep blue */
  color: white !important;
  font-weight: bold;
}

.sn-tag.clicked-remote,
.sn-group.clicked-remote {
  background-color: #ff9800 !important;  /* Orange */
  color: white !important;
  font-weight: bold;
}
```

### Priority Handling
Use `!important` to override existing color backgrounds from semantic grouping. This ensures highlighting is always visible.

## Edge Cases

### Same SN Appears Multiple Times
**Scenario**: In Gen 1:4, `<0216>` (light) appears twice.

**Behavior**: All instances highlighted together with same color.

**Implementation**: Loop through all matching elements and apply class to each.

### Click Outside SN Elements
**Scenario**: User clicks on Chinese text or whitespace.

**Behavior**: Clear all highlighting.

**Implementation**: Global click handler checks if `event.target` has `.sn-tag` or `.sn-group` class. If not, call `clearHighlighting()`.

### Verse Navigation
**Scenario**: User highlights SN in Gen 1:4, then navigates to Gen 1:5.

**Behavior**: Highlighting should clear automatically.

**Implementation**: Subscribe to `VERSE_SELECTED` event and call `clearHighlighting()` before rendering new verse.

### Dictionary Tooltip Conflict
**Scenario**: Clicking SN should show both highlighting and dictionary tooltip.

**Behavior**: Both features work simultaneously.

**Implementation**: Use `event.stopPropagation()` carefully. Dictionary handler subscribes to same `SN_CLICK` event, so both will trigger.

## Performance Considerations

### Element Lookup Optimization
Cache DOM queries where possible:
```javascript
// Bad: Query every time
const tags = document.querySelectorAll('.sn-tag');

// Good: Query once per verse
let cachedTags = null;
function getTags() {
  if (!cachedTags) {
    cachedTags = document.querySelectorAll('.sn-tag');
  }
  return cachedTags;
}

// Clear cache on verse change
function onVerseChange() {
  cachedTags = null;
  clearHighlighting();
}
```

### Minimize Reflows
Apply classes in batch using DocumentFragment when possible, though for small numbers of elements (< 20 per verse) this is not critical.

## Testing Strategy

### Unit Tests (Manual Verification)
1. Click each type of SN and verify colors
2. Test with verses containing repeated SNs
3. Test verse navigation clears highlighting
4. Test click-away clears highlighting

### Integration Tests
1. Verify highlighting doesn't break existing features (dictionary, color grouping)
2. Test across different Bible books (Gen, Exod, etc.)
3. Test with uncertain verses (marked with `_uncertain`)

## Future Enhancements (Out of Scope)

- Persistent highlighting across page reloads (would need localStorage)
- Multi-select highlighting (Ctrl+click for multiple SNs)
- Customizable colors (user preferences)
- Cross-verse highlighting (compare SNs across different verses)
