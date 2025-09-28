# Development Documentation: Main Checkbox Synchronization System

This document provides detailed technical documentation for the main checkbox synchronization system implemented in the Dual Bible Reader.

## Overview

The main checkbox system allows either reader (left or right) to act as the "main" reader, with the other automatically becoming the "follower." This creates a dynamic, bidirectional synchronization system where users have explicit control over which reader leads.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Left Reader   │    │  MockMediator   │    │  Right Reader   │
│                 │    │                 │    │                 │
│ [✓] Main        │◄──►│  Event System   │◄──►│ [ ] Main        │
│ Controls        │    │  Callbacks      │    │ Controls        │
│ Content Area    │    │  State Mgmt     │    │ Content Area    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   Scroll Events          Role Management         Scroll Events
   Chapter Events         Position Sync           Chapter Events
   UI Updates             Event Routing           UI Updates
```

## Key Components

### 1. MockMediator Enhancements

#### New Properties
```javascript
_leftReaderUpdateFn: null,     // Callback for left reader updates
_rightReaderUpdateFn: null,    // Callback for right reader updates
_mainReader: 'left',           // Current main reader ('left' or 'right')
```

#### New Methods
```javascript
registerLeftReaderUpdateCallback(callback)   // Register left reader callback
setMainReader(readerType, interaction)       // Set main reader with context
getMainReader()                              // Get current main reader
getFollowerReader()                          // Get current follower reader
```

#### Enhanced syncPosition()
```javascript
syncPosition: function(payload) {
    // Determine which reader to update based on current main reader
    if (this._mainReader === 'left' && this._rightReaderUpdateFn) {
        this._rightReaderUpdateFn(payload.book, payload.chapter, payload.verse);
    } else if (this._mainReader === 'right' && this._leftReaderUpdateFn) {
        this._leftReaderUpdateFn(payload.book, payload.chapter, payload.verse);
    }
}
```

### 2. Reader Components

#### Main Toggle Event Handlers
Both readers implement similar main toggle logic:

```javascript
function handleMainToggle() {
    if (isUpdatingCheckboxes) return; // Prevent infinite loops
    
    if (mainToggle.checked) {
        // Become main reader
        MockMediator.setMainReader('left', 'main checkbox checked');
        // Uncheck other reader's main toggle
        otherMainToggle.checked = false;
        // Immediately publish chapter change event
        publishChapterChangeEvent();
        // Load fresh content for synchronization
        setTimeout(() => loadChapterContent(), 10);
    } else {
        // Become follower, make other reader main
        MockMediator.setMainReader('right', 'left main unchecked');
        otherMainToggle.checked = true;
    }
}
```

#### Scroll Synchronization
Enhanced scroll handlers detect verse positions and sync across readers:

```javascript
function handleScroll() {
    if (!mainToggle.checked) return; // Only sync if main
    
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
        const currentVerse = getTopmostVerseReference();
        if (currentVerse) {
            syncPositionWithMediator(currentVerse.book, currentVerse.chapter, currentVerse.verse);
        }
    }, 100);
}
```

#### Follower Update Callbacks
Each reader implements callback functions for following the other reader:

**Left Reader (following right):**
```javascript
function loadLeftPassage(book, chapter, verse) {
    // Check if book/chapter differs from current display
    const currentDisplayedBook = bookSelect.options[bookSelect.selectedIndex]?.text;
    const currentDisplayedChapter = parseInt(chapterInput.value);
    
    if (currentDisplayedBook !== currentBook || currentDisplayedChapter !== chapter) {
        // Load different chapter and update controls
        updateControlsToMatch(book, chapter);
        loadChapterContent().then(() => scrollToVerse(verse));
    } else {
        // Same chapter, just scroll to verse
        scrollToVerse(verse);
    }
}
```

**Right Reader (following left):**
```javascript
function loadPassage(book, chapter, verse) {
    // Similar logic with right reader's controls and functions
    // Handles book/chapter differences and verse-only scrolling
}
```

## Event System

### Event Types

#### Chapter Change Events
- **`leftReaderChapterChanged`**: Published when left reader loads new content (only if main)
- **`rightReaderChapterChanged`**: Published when right reader loads new content (only if main)

**Event Payload:**
```javascript
{
    book: "Genesis",                    // English book name
    chapter: 1,                        // Chapter number
    version: "UNV (Union Version)",    // Display version name
    internalVersionValue: "創",         // Chinese abbreviation for API
    strong: true,                      // Strong's numbers enabled
    verses: [...]                      // Verse data array
}
```

#### Role Change Events
- **`mainReaderChanged`**: Published when main reader switches

**Event Payload:**
```javascript
{
    newMain: 'left',        // New main reader
    newFollower: 'right',   // New follower reader
    interaction: 'main checkbox checked'  // Reason for change
}
```

### Event Publishing Logic

Both readers now use **conditional publishing** to prevent event conflicts:

```javascript
// Only publish events when this reader is main
if (MockMediator.getMainReader() === 'left') {
    MockMediator.publish('leftReaderChapterChanged', eventData);
}
```

## Synchronization Flows

### 1. Initial Main Selection

```
User Action: Check Right Reader Main Box
├── 1. handleRightMainToggle() triggered
├── 2. MockMediator.setMainReader('right', 'main checkbox checked')
├── 3. Left reader main checkbox unchecked
├── 4. Immediate publish: rightReaderChapterChanged event
├── 5. Left reader receives event → updates controls → loads content
└── 6. Right reader calls loadChapterContent() for fresh sync data
```

### 2. Scroll-Based Synchronization

```
User Action: Scroll in Main Reader (Right)
├── 1. handleRightScroll() triggered
├── 2. getRightTopmostVerseReference() detects current verse
├── 3. syncRightPositionWithMediator() called
├── 4. MockMediator.syncPosition() routes to left reader
├── 5. Left reader's loadLeftPassage() receives book/chapter/verse
├── 6. Left reader checks for book/chapter differences
├── 7a. Same chapter → scrollLeftToVerse() with highlighting
└── 7b. Different chapter → update controls → load content → scroll to verse
```

### 3. Navigation Following

```
User Action: Main Reader Changes Book/Chapter
├── 1. bookSelect.addEventListener() or chapterInput.addEventListener()
├── 2. loadChapterContent() called
├── 3. Conditional check: if (MockMediator.getMainReader() === 'right')
├── 4. Publish rightReaderChapterChanged event
├── 5. Follower reader receives event
├── 6. Follower updates controls and loads matching content
└── 7. syncPosition() called for verse-level alignment
```

## UI Integration

### HTML Structure
```html
<!-- Main checkbox controls added to both readers -->
<label for="left-reader-main-toggle">Main:</label>
<input type="checkbox" id="left-reader-main-toggle" checked>

<label for="right-reader-main-toggle">Main:</label>
<input type="checkbox" id="right-reader-main-toggle">
```

### Translation Support
```javascript
// Added to translations object in app.js
leftReaderMainLabel: "Main:",
rightReaderMainLabel: "Main:",
leftReaderMainLabel: "主要：",  // Chinese
rightReaderMainLabel: "主要：", // Chinese
```

### Status Updates
Both readers provide real-time status feedback:
- "📍 Set as MAIN reader (checkbox)"
- "📍 Set as FOLLOWER reader (checkbox)"
- "📨 Following right reader: Genesis 1"
- "📍 Scrolled to verse 5"

## Performance Optimizations

### Smart Content Loading
```javascript
// Only load new content when book/chapter actually differs
if (currentDisplayedBook !== targetBook || currentDisplayedChapter !== chapter) {
    // Load different chapter
    loadChapterContent().then(() => scrollToVerse(verse));
} else {
    // Same chapter, just scroll to verse (no API call needed)
    scrollToVerse(verse);
}
```

### Debounced Scroll Events
```javascript
// Prevent excessive API calls during scroll
clearTimeout(scrollTimeout);
scrollTimeout = setTimeout(() => {
    // Process scroll position
}, 100);
```

### Loop Prevention
```javascript
let isUpdatingCheckboxes = false;

function handleMainToggle() {
    if (isUpdatingCheckboxes) return; // Prevent infinite loops
    isUpdatingCheckboxes = true;
    // ... toggle logic
    setTimeout(() => { isUpdatingCheckboxes = false; }, 100);
}
```

## Testing Scenarios

### Manual Testing Checklist

1. **Basic Functionality**
   - [ ] Left main checked → Right follows immediately
   - [ ] Right main checked → Left follows immediately
   - [ ] Only one main checkbox can be checked at a time

2. **Scroll Synchronization**
   - [ ] Left main + scroll → Right follows verse position
   - [ ] Right main + scroll → Left follows verse position
   - [ ] Verse highlighting appears in follower reader

3. **Navigation Following**
   - [ ] Main reader book change → Follower updates book/chapter
   - [ ] Main reader chapter change → Follower updates chapter
   - [ ] Follower controls visually update to show following

4. **Edge Cases**
   - [ ] Unchecking main → Other reader becomes main automatically
   - [ ] Fast checkbox toggling → No infinite loops
   - [ ] Different book/chapter → Smart content loading works
   - [ ] Same chapter scroll → Only verse scrolling (no reload)

5. **UI Consistency**
   - [ ] Status displays show correct main/follower state
   - [ ] Controls update to reflect current state
   - [ ] Visual highlighting works in both directions

## Debugging

### Console Logging
Key debug messages to look for:
```
LeftReader: Publishing chapter change event immediately
RightReader: Received chapter change from LeftReader: {book: "Genesis", chapter: 1}
MockMediator: Main reader is now right due to: main checkbox checked
MockMediator: Syncing to 創 1:5 from right reader
```

### Common Issues

1. **Checkboxes not syncing**: Check `isUpdatingCheckboxes` flag logic
2. **Events not publishing**: Verify `MockMediator.getMainReader()` conditions
3. **Content not loading**: Check book mapping and API integration
4. **Scroll not following**: Verify callback registration and verse detection

## Future Enhancements

### Potential Improvements
1. **Cross-tab Synchronization**: WebSocket integration for multi-tab sync
2. **Gesture Controls**: Touch/swipe controls for mobile main reader switching
3. **Advanced Highlighting**: Multiple verse highlighting and annotations
4. **Performance Metrics**: Sync timing and performance monitoring
5. **User Preferences**: Remember preferred main reader across sessions

### Architecture Considerations
- **State Management**: Consider Redux-like state management for complex scenarios
- **Component Separation**: Further modularization of sync logic
- **Event Optimization**: Batch event processing for performance
- **Error Recovery**: Robust error handling and state recovery mechanisms