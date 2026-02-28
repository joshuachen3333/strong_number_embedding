# Design: Context-Aware Hotkeys

## Architecture Overview

### State Management

Add a new state variable to track the active panel context:

```javascript
// In navigation.js or a new focus_manager.js
let activePanel = 'left'; // 'left' | 'right'
let selectedGroupIndex = -1; // Index of currently selected SN group in right panel
```

### Event Listeners

#### Mouse Hover Detection

```javascript
// Track mouse position to determine active panel
document.querySelector('.left-panel').addEventListener('mouseenter', () => {
  activePanel = 'left';
});

document.querySelector('.right-panel').addEventListener('mouseenter', () => {
  activePanel = 'right';
});
```

#### Click Detection

```javascript
// Left panel: clicks on verses or SN tags
leftPanel.addEventListener('click', (e) => {
  if (e.target.closest('.verse') || e.target.closest('.sn-tag')) {
    activePanel = 'left';
  }
});

// Right panel: clicks on SN groups in parsed section
rightPanel.addEventListener('click', (e) => {
  const snGroup = e.target.closest('.sn-group');
  if (snGroup) {
    activePanel = 'right';
    selectedGroupIndex = getGroupIndex(snGroup);
    highlightSelectedGroup(selectedGroupIndex);
  }
});
```

### Keyboard Handler Modification

Modify the existing `initKeyboard()` function in `navigation.js`:

```javascript
function initKeyboard() {
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
      return;
    }

    if (activePanel === 'left') {
      handleLeftPanelKeys(e);
    } else {
      handleRightPanelKeys(e);
    }
  });
}

function handleLeftPanelKeys(e) {
  // Existing behavior - verse/chapter navigation
  switch (e.key) {
    case 'ArrowUp': navigatePreviousVerse(); break;
    case 'ArrowDown': navigateNextVerse(); break;
    case 'ArrowLeft': navigatePreviousChapter(); break;
    case 'ArrowRight': navigateNextChapter(); break;
    case 'Home': navigateFirstVerse(); break;
    case 'End': navigateLastVerse(); break;
  }
}

function handleRightPanelKeys(e) {
  // New behavior - SN group navigation
  switch (e.key) {
    case 'ArrowUp': navigatePreviousGroup(); break;
    case 'ArrowDown': navigateNextGroup(); break;
    case 'ArrowLeft': navigatePreviousVerse(); break;
    case 'ArrowRight': navigateNextVerse(); break;
    case 'Home': navigateFirstGroup(); break;
    case 'End': navigateLastGroup(); break;
  }
}
```

### SN Group Navigation Functions

```javascript
function getSnGroups() {
  // Get all SN group elements from the parsed section
  return document.querySelectorAll('.parsed-section .sn-group');
}

function navigatePreviousGroup() {
  const groups = getSnGroups();
  if (groups.length === 0) return;

  if (selectedGroupIndex > 0) {
    selectedGroupIndex--;
    selectGroup(selectedGroupIndex);
  } else {
    // At first group, go to previous verse
    navigatePreviousVerse();
    // After verse loads, select last group
    setTimeout(() => selectLastGroup(), 100);
  }
}

function navigateNextGroup() {
  const groups = getSnGroups();
  if (groups.length === 0) return;

  if (selectedGroupIndex < groups.length - 1) {
    selectedGroupIndex++;
    selectGroup(selectedGroupIndex);
  } else {
    // At last group, go to next verse
    navigateNextVerse();
    // After verse loads, select first group
    setTimeout(() => selectFirstGroup(), 100);
  }
}

function navigateFirstGroup() {
  selectGroup(0);
}

function navigateLastGroup() {
  const groups = getSnGroups();
  selectGroup(groups.length - 1);
}

function selectGroup(index) {
  const groups = getSnGroups();
  if (index < 0 || index >= groups.length) return;

  selectedGroupIndex = index;
  highlightSelectedGroup(index);

  // Trigger bidirectional highlighting
  const snCodes = extractSNsFromGroup(groups[index]);
  highlightCorrespondingLeftPanelTags(snCodes);
}
```

### CSS for Selected Group

```css
.sn-group.keyboard-selected {
  outline: 2px solid #1976D2;
  outline-offset: 2px;
  box-shadow: 0 0 4px rgba(25, 118, 210, 0.5);
}
```

## File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `js/navigation.js` | Modify | Add active panel state and context-aware key handlers |
| `js/right_panel.js` | Modify | Add SN group click handlers and selection state |
| `js/color_mapper.js` | Modify | Add keyboard selection highlighting (or create new module) |
| `css/styles.css` | Modify | Add `.keyboard-selected` style for SN groups |

## Edge Cases

1. **Empty parsed section**: When no SN groups exist (unparsed verse), right panel hotkeys should fall back to verse navigation
2. **Verse change clears selection**: When navigating to a new verse, reset `selectedGroupIndex` to -1 (no selection) or 0 (first group)
3. **Toggle section hides groups**: If user toggles off the Parsed section, switch active panel to left
4. **Page load**: Default to left panel active, no SN group selected

## Testing Scenarios

1. Hover over left panel → press ↓ → should go to next verse
2. Hover over right panel → press ↓ → should select next SN group
3. Click SN group in right panel → press ↑ → should select previous SN group
4. In right panel, at first SN group → press ↑ → should go to previous verse, select last group
5. In right panel, at last SN group → press ↓ → should go to next verse, select first group
6. Move mouse from right to left → press ↓ → should go to next verse (not SN group)
