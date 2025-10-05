# Development Criteria & Guidelines (English)

## Preface
This document records development guidelines learned from painful experiences. **Every code modification, feature expansion, debugging, or architectural adjustment must pass through this checklist first.**

---

## Core Development Principles

### 1. Architecture Consistency Check
**Question:** Does this modification conform to the system's design patterns?

**Checkpoints:**
- [ ] Does it conform to the Mediator pattern's event publish/subscribe mechanism?
- [ ] Does it follow existing module responsibility boundaries?
- [ ] Does it maintain consistency with existing API interfaces?
- [ ] Does it conform to existing code style and naming conventions?

**System-Specific Patterns:**
- MockMediator as central event coordinator
- Reader components communicate through events, not direct calls
- Strong's functionality spans components through standardized events

### 2. Dependency Integrity
**Question:** Will this break existing initialization order or event flow?

**Checkpoints:**
- [ ] Initialization order: DOM → Event listeners → State sync → Content loading
- [ ] Event flow: User interaction → Event publish → Mediator coordination → Target response
- [ ] Dependency chain: DOM elements → JavaScript variables → Functional logic
- [ ] Are timing-sensitive operations properly using setTimeout/Promise

**Key Dependencies:**
- HTML DOM elements must exist before JavaScript variable initialization
- Left/right reader follow state mutual exclusion relationship
- Edit mode activation must ensure main reader role assignment

### 3. State Management Rationality
**Question:** Does this introduce new state inconsistencies?

**Checkpoints:**
- [ ] Are JavaScript variables synchronized with DOM state?
- [ ] Are there conflicts between multiple state variables?
- [ ] Are state changes going through correct channels?
- [ ] Is there a Single Source of Truth?

**System State Mapping:**
- `isEditMode` ↔ `editModeToggle.checked`
- Main/Follower role ↔ Follow checkbox state
- Strong's display ↔ `strongToggle.checked`
- Content state ↔ localStorage/API data

### 4. Functional Boundary Clarity
**Question:** Does this violate module responsibility boundaries?

**Checkpoints:**
- [ ] Do left/right readers maintain independence?
- [ ] Does MockMediator only handle coordination, not business logic?
- [ ] Is Strong's functionality properly distributed across components?
- [ ] Is localStorage management centralized in appropriate locations?

**Responsibility Boundaries:**
- **Left Reader**: Display reference content, provide Strong's mapping source
- **Right Reader**: Edit functionality, Strong's suggestions, localStorage management
- **MockMediator**: Event coordination, data caching, role management
- **App**: Global settings, language switching, UI coordination

### 5. Backward Compatibility
**Question:** Will this break existing APIs or interfaces?

**Checkpoints:**
- [ ] Are existing function signatures preserved?
- [ ] Is localStorage data format compatible?
- [ ] Are event names and parameters consistent?
- [ ] Are CSS class names and DOM structure stable?

---

## System-Specific Architecture Elements

### Mediator Pattern Implementation
```javascript
// Correct: Communicate through Mediator
MockMediator.publish('eventName', data);

// Wrong: Direct component calls
leftReader.someFunction();
```

### Three-Tier Loading Priority
```javascript
// Priority: JSON → localStorage → API
1. Check local JSON files
2. Check localStorage storage
3. Finally API calls
```

### Main/Follower Dynamic System
```javascript
// Follow checkbox logic: checked = follower, unchecked = main
// Last operated reader becomes main, others become follower
```

### Strong's Functionality Integration Points
- **Left reader**: `attachStrongsEventListeners()` - Read-only clicks
- **Right reader**: `attachStrongsEventListenersSecondReader()` - Edit integration
- **Cross reader**: `WordMappingEngine` - Automatic mapping

### Edit Mode State Management
```javascript
// State sync order
1. HTML checkbox as Single Source of Truth
2. JavaScript variables sync during initialization
3. State changes through event handlers
```

---

## Pre-Modification Check Flow

### Step 1: Problem Analysis
- [ ] Clearly define the specific problem to solve
- [ ] Analyze root cause, not just surface symptoms
- [ ] Confirm impact scope and priority

### Step 2: Architecture Review
- [ ] Check the 5 core principles above
- [ ] Identify potentially affected system components
- [ ] Evaluate if there are solutions more aligned with existing architecture

### Step 3: Design Solution
- [ ] Design minimal-impact implementation plan
- [ ] Confirm modification atomicity (independently testable and rollbackable)
- [ ] Prepare test verification plan

### Step 4: Implementation Check
- [ ] Modify only one logical concept at a time
- [ ] Test verification immediately after each modification
- [ ] Confirm no breakage of existing functionality

### Step 5: Integrity Verification
- [ ] Test if modification solves original problem
- [ ] Verify no new problems introduced
- [ ] Confirm overall system functionality normal

---

## Anti-Pattern Case Records

### Case 1: localStorage Direct Loading Error
**Wrong Approach:** Skip API loading, directly build page from localStorage
**Problem:** Destroyed complete initialization flow, lost Strong's functionality
**Correct Approach:** First API load complete functionality, then use restoreEditedContent to overlay

### Case 2: State Sync Error
**Wrong Approach:** HTML checkbox checked=true, JavaScript isEditMode=false
**Problem:** State inconsistency causes condition check errors
**Correct Approach:** Sync state during initialization: isEditMode = editModeToggle.checked

### Case 3: Missing Function Error
**Wrong Approach:** Call non-existent addVerseEditingListeners()
**Problem:** Broke localStorage restoration flow
**Correct Approach:** Use existing event listener mechanisms

---

## Critical Architecture Inventory

### Critical Functions That Must Be Preserved

#### MockMediator Core Coordination Functions
```javascript
// Event system - Foundation of all cross-component communication
subscribe(eventName, callback)    // Event subscription mechanism
publish(eventName, data)          // Event publishing mechanism with error handling
events object structure           // Core of pub/sub pattern

// Data management - Three-tier loading system
fetchChapter(book, chapter, version, strong)  // API integration and caching
_bookDataCache                               // Prevent duplicate API calls
clearCache()                                // Cache invalidation on version switch

// Sync coordination - Main/Follower system
syncPosition(payload)                       // Chapter-level synchronization
setMainReader(readerType, interaction)      // Role management
getMainReader() / getFollowerReader()       // Role state queries
registerLeftReaderUpdateCallback(callback)  // Left reader callback registration
registerRightReaderUpdateCallback(callback) // Right reader callback registration

// Key state variables
_mainReader        // 'left' or 'right', defaults to 'right'
_currentSynchedVerse  // Global chapter position state
```

#### Reader Initialization Functions (Order Cannot Be Changed)
```javascript
// Left Reader
loadLeftPassage(book, chapter, verse)  // Mediator sync callback
initializeLeftReaderDefaults()         // UNV, Strong's ON, follow right reader
loadChapterContent()                   // Main content loading

// Right Reader
loadPassage(book, chapter, verse)      // Mediator sync callback
loadChapterContent()                   // Three-tier loading system
displaySyncedContent()                 // Follower content synchronization
initializeRightReaderDefaults()        // LCC, Edit Mode ON
```

#### Three-Tier Loading System (Critical Priority Order)
```javascript
// Priority order - Absolutely cannot be changed
1. Local JSON files (${book}_${chapter}_${version}_edited.json)
2. localStorage cache
3. API calls (bible.fhl.net)

// Key loading functions
loadFromJsonFile(jsonData)    // JSON file processing
restoreEditedContent()        // localStorage restoration (only after renderChapter)
MockMediator.fetchChapter()   // API integration and caching
```

#### Strong's Number System Functions
```javascript
// Parse functions (two readers must stay synchronized)
parseStrongsNumbers(text)           // 4 formats converted to clickable spans
// Formats: {<WH1234>}, {H1234}, <WH1234>, (H1234)

// Event functions
attachStrongsEventListeners()       // Left reader - read-only clicks
attachStrongsEventListenersSecondReader()  // Right reader - edit integration
// Publish 'strongsNumberClicked' events to MockMediator
```

#### Edit Mode Functions (Right Reader Exclusive)
```javascript
// State management
isEditMode                 // Sync with editModeToggle.checked
currentEditingVerse        // Current editing verse
handleEditModeToggle()     // Edit mode toggle handler

// Auto-save system
saveEditedContent()        // localStorage persistence
autoSaveTimer             // Timed auto-save
hasUnsavedChanges         // Change tracking flag

// Undo/Redo system
undoStack / redoStack     // Edit history stacks
isUndoRedoAction          // Infinite loop prevention flag
```

#### Critical Engine Components
```javascript
// WordMappingEngine - Cross-Reader Word Mapping Engine
WordMappingEngine.createWordMapping(leftVerse, rightVerse, verseId)  // Create word pairs
WordMappingEngine.getStrongsForWord(word)                           // Get word's Strong's suggestions
WordMappingEngine.colorPalette                                      // Pairing color palette
WordMappingEngine.clearHighlights(verse)                           // Clear highlighting

// SuggestionEngine - Strong's Suggestion Engine (Black Box Interface)
SuggestionEngine.getSuggestion(context)                            // Abstract suggestion logic
// Note: This is a black box interface, internal logic cannot be modified

// Multi-Character Word Detection Engine - Multi-character word detection engine
detectMultiCharWords(chineseText)                                   // Chinese multi-character word analysis
extractWordsWithStrongs(leftVerse)                                  // Extract Strong's word mapping

// Auto-Save Engine - Auto-save engine
startAutoSave()                                                     // Start auto-save timer
stopAutoSave()                                                      // Stop auto-save
markContentAsModified()                                             // Mark content as modified

// Undo/Redo Stack Engine - Edit history management engine
saveToUndoStack(element)                                            // Save edit state
performUndo() / performRedo()                                       // Execute undo/redo
clearUndoRedoStacks()                                               // Clear history stacks

// VerticalResizer - UI Adjustment Engine (Global Component)
VerticalResizer.class                                               // UI scaling behavior management
// Location: app.js - Handles global resize functionality
```

### Critical Components That Cannot Be Broken

#### Key DOM Elements (ID Selectors)
```javascript
// Reader containers
'left-reader-content-area', 'right-reader-content-area'
'left-reader-book', 'right-reader-book'
'left-reader-chapter', 'right-reader-chapter'
'left-reader-version-select', 'right-reader-version-select'
'left-reader-strong-toggle', 'right-reader-strong-toggle'

// Follow system checkboxes (Core of Main/Follower logic)
'left-reader-follow-scroll', 'left-reader-follow-selection'
'right-reader-follow-scroll', 'right-reader-follow-selection'

// Edit Mode (Right reader exclusive)
'right-reader-edit-mode'
'right-reader-strong-controls'
'strong-number-input', 'insert-strong-btn'
```

#### Functional Data Attributes
```javascript
data-verse="${verseNum}"        // Verse identification for scroll sync
data-book="${bookChinese}"      // Book identification for API calls
data-chapter="${chapterNum}"    // Chapter identification
data-strong="${strongsId}"      // Strong's number identification
data-original="${content}"      // Edit change tracking
```

#### Functional CSS Classes
```javascript
.verse              // Verse container class
.verse-number       // Verse number span
.strongs-number     // Clickable Strong's number span
.verse-highlighted  // Sync scroll highlighting
```

### Critical Relationships That Cannot Be Violated

#### Main/Follower System (Most Fragile Architecture)
```javascript
// Follow Checkbox Logic - Absolutely cannot be changed
Parent-Child relationship: Follow Text Selection (parent) → Follow Verse Scroll (child)
Last Checkbox Wins: Any follow checkbox checked → that reader becomes follower
Cross-Reader updates: Check follow → auto-uncheck other reader's follow
Immediate sync: follower immediately syncs to main reader current position

// Role determination rules
Both follow checkboxes unchecked = MAIN reader
Either follow checkbox checked = FOLLOWER reader
Cannot have both readers as followers simultaneously
```

#### Event System Architecture
```javascript
// Core event names (Cannot be changed)
'leftReaderChapterChanged'   // Left reader chapter navigation
'rightReaderChapterChanged'  // Right reader chapter navigation
'mainReaderChanged'          // Main/Follower role changes
'strongsNumberClicked'       // Strong's number interactions

// Event data structures (Must maintain format)
Chapter Change: {book, chapter, version, internalVersionValue, strong, verses}
Main Reader Change: {newMain, newFollower, interaction}
Sync Position: {book, chapter, verse, mainReaderVersion}
```

#### Strong's Integration Points
```javascript
// Cross-component dependency relationships
Parse functions must stay synchronized in both readers
Event publishing only from main reader
WordMappingEngine handles cross-reader word pairing and color coordination
SuggestionEngine provides black box logic for Strong's suggestions
Multi-Character Word Detection Engine handles Chinese multi-character word analysis
Click handlers attached during renderChapter()
Word mapping depends on edit mode state

// Engine collaboration relationships
WordMappingEngine ↔ SuggestionEngine ↔ Strong's parse functions
Auto-Save Engine ↔ Edit Mode ↔ localStorage system
Undo/Redo Engine ↔ Edit Mode ↔ Cursor Position management

// Engine modification constraints
WordMappingEngine: Can extend pairing logic, cannot modify color coordination interface
SuggestionEngine: Black box interface, absolutely cannot modify internal implementation
Multi-Char Detection: Can optimize algorithms, cannot modify return format
Auto-Save Engine: Can adjust frequency, cannot modify storage format
Undo/Redo Engine: Can extend operation types, cannot modify stack structure
VerticalResizer: Global component, modifications need impact assessment on all UI
```

### Immutable Initialization Sequence
```javascript
1. DOM Ready → All readers' DOMContentLoaded listeners
2. Book dropdown population → Both readers' identical book arrays
3. MockMediator callback registration → readers register update callbacks
4. Default initialization → Left reader sets defaults, right reader waits
5. Event listener attachment → All control listeners
6. Initial content loading → Left reader loads Genesis 1

// Sequential dependencies (Cannot be reversed)
MockMediator must load before readers (index.html script order)
Book arrays must populate before any book selection
Callback registration must occur before any synchronization
Follow checkbox logic must be fully initialized before user interaction
```

### State Synchronization Patterns
```javascript
// Single Source of Truth pattern
HTML checkbox state → JavaScript variable state
editModeToggle.checked → isEditMode
followCheckbox.checked → Main/Follower role

// State change flow
User interaction → DOM event → State update → MockMediator coordination → Cross-component sync
```

---

## Documentation Update Requirements

This document should be continuously updated as system complexity grows:
- Add new architectural issues to anti-pattern cases when discovered
- Update architecture elements when major system features are added
- Optimize check processes after development guidelines are verified through practice

**Update Principle:** Learn from actual errors, continuously improve development standards.