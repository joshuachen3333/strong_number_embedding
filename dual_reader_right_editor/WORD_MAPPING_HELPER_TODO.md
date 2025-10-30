# Global Word Mapping Helper - Implementation Plan

## 🔍 CRITICAL DISCOVERY: Existing Word Mapping System

**Date: 2025-01-20**

### Evidence of Existing Word Mapping

During testing with LCC version (呂振中譯本) in the right reader, we observed:

1. **Visual Evidence:**
   - Right reader shows colored highlights on words: "起初" (blue), "上帝" (orange), "天地" (yellow)
   - These are NOT Strong's number highlights (LCC has no Strong's numbers)
   - These are `.word-mapping-highlight` elements with special attributes

2. **DOM Structure Evidence:**
   ```html
   <!-- From right reader with LCC version -->
   <span class="word-mapping-highlight right-highlight"
         data-mapped-word="起初"
         title="Mapped word: 起初"
         style="background-color: rgb(227, 242, 253);">
     起初
   </span>

   <!-- From left reader with UNV version -->
   <span class="word-mapping-highlight left-highlight"
         data-mapped-word="起初"
         title="Mapped word: 起初">
     起初
   </span>
   ```

3. **Functional Evidence:**
   - Status log shows: "Word mapping complete: 188 word pairs highlighted across 31 verses"
   - The system already knows: "神" (UNV) ↔ "上帝" (LCC)
   - This mapping happens dynamically when loading chapters

### Current Word Mapping Capabilities

**What Already Exists:**
- ✅ Dynamic word-to-word mapping between different Bible versions
- ✅ Visual highlighting of mapped words (`.word-mapping-highlight` class)
- ✅ Data attributes storing mapping information (`data-mapped-word`)
- ✅ Works for versions WITHOUT Strong's numbers (like LCC)
- ✅ Covers entire chapters (hundreds of word pairs)

**Current Direction:**
- Works for: **RIGHT → LEFT** (clicking right term highlights left term in orange)
- Location: Likely in `right_reader_frontend.js` (triggerWordMapping function)

**What We Need:**
- Reverse the logic: **LEFT → RIGHT** (clicking left term finds mapped word in right reader)
- Use mapped word for cursor positioning (not Strong's number matching)

### Revised Implementation Strategy

**Instead of building from scratch, we should:**

1. **Investigate existing word mapping code**
   - Find where `.word-mapping-highlight` elements are created
   - Understand the mapping algorithm (how does it know "神" ↔ "上帝"?)
   - Locate the mapping data structure or API

2. **Reuse existing mapping for cursor positioning**
   ```javascript
   // Pseudo-code for new approach
   makeVerseEditableAndPositionCursor: function(clickedWord, verseNumber) {
     // Option A: Look for word-mapping-highlight element in right reader
     const rightVerse = rightReader.querySelector(`[data-verse="${verseNumber}"]`);
     const mappedElement = rightVerse.querySelector(
       `.word-mapping-highlight[data-mapped-word="${clickedWord}"]`
     );

     if (mappedElement) {
       // Position cursor at right edge of this element
       this.positionCursorAfter(mappedElement);
     }
   }
   ```

3. **Leverage bidirectional mapping**
   - If RIGHT → LEFT highlighting works
   - Then LEFT → RIGHT should use the SAME mapping data
   - Just reverse the lookup direction

### Key Questions to Answer

1. **Where is word mapping implemented?**
   - File: `right_reader_frontend.js`? `app.js`? Separate module?
   - Function name: `triggerWordMapping()`? Something else?

2. **How does it create mappings?**
   - Pre-computed JSON files?
   - Dynamic algorithm based on Strong's numbers?
   - API call to external service?
   - Uses WordMappingEngine module?

3. **What's the mapping data structure?**
   - Array of word pairs?
   - Hash map with keys?
   - Stored in DOM as data attributes?

4. **Can we query the mapping?**
   - Given: "神" in left reader (UNV)
   - Query: "What's the corresponding word in right reader (LCC)?"
   - Answer: "上帝"

### Advantages of Using Existing System

1. **No need to build from scratch** ✅
2. **Already proven to work** with LCC, ESV, etc. ✅
3. **Handles complex cases** (188 word pairs in one chapter!) ✅
4. **Dynamically updates** when changing versions ✅
5. **Less code to maintain** ✅

### Next Steps

**IMMEDIATE TODO:**
1. [ ] Search codebase for `word-mapping-highlight` class creation
2. [ ] Find the word mapping implementation (likely `triggerWordMapping` function)
3. [ ] Understand the mapping algorithm/data source
4. [ ] Extract reusable mapping query function
5. [ ] Update `makeVerseEditableAndPositionCursor()` to use existing mapping
6. [ ] Test LEFT → RIGHT cursor positioning with LCC

**Original plan below is kept for reference but may not be needed if existing system is sufficient.**

---

## Problem Statement

**Current Implementation Issue:**
The cursor positioning feature (clicking left term → position cursor in right reader) currently relies on finding matching Strong's numbers in the right reader. This is backwards logic because:
- It only works when the right reader ALREADY has Strong's numbers
- The whole purpose of the tool is to INSERT Strong's numbers into translations that DON'T have them yet
- Defeats the purpose of the editing feature

**Example of the Problem:**
- Left reader: UNV with Strong's (神<H0430>)
- Right reader: LCC without Strong's (上帝)
- Click "神" in left → Copies H0430 to clipboard ✅
- But cannot position cursor after "上帝" in right reader ❌
- Because there's no H0430 in LCC to match against

## Correct Logic Flow

1. User clicks word in LEFT reader (e.g., "神" in UNV)
2. System finds adjacent Strong's number (H0430)
3. System copies H0430 to clipboard ✅
4. System fills H0430 into SN cpd field ✅
5. **NEW: System looks up word mapping:** "神" (UNV, verse 1, position X) ↔ "上帝" (LCC, verse 1, position Y)
6. System finds "上帝" in right reader using the mapping
7. System enables edit mode in right reader
8. System makes verse editable
9. System positions cursor at right edge of "上帝"
10. User presses Cmd+V to paste `<H0430>` after "上帝"

## Proposed Solution: Global Word Mapping Helper Tool

### Overview
Create a **chapter-level word mapping system** that pre-computes and stores word correspondences between different Bible versions for each book/chapter.

### Mapping Structure

```javascript
// Example structure
const wordMappings = {
  "Genesis": {
    1: {  // Chapter 1
      1: [  // Verse 1
        {
          position: 0,
          unv: { word: "起初", strong: "H07225", offset: 0 },
          kjv: { word: "beginning", strong: "H07225", offset: 0 },
          lcc: { word: "起初", offset: 0 }
        },
        {
          position: 1,
          unv: { word: "神", strong: "H0430", offset: 2 },
          kjv: { word: "God", strong: "H0430", offset: 1 },
          lcc: { word: "上帝", offset: 2 }
        },
        {
          position: 2,
          unv: { word: "創造", strong: "H01254", offset: 3 },
          kjv: { word: "created", strong: "H01254", offset: 2 },
          lcc: { word: "創造", offset: 4 }
        }
        // ... more words
      ],
      2: [ /* verse 2 words */ ]
      // ... more verses
    },
    2: { /* chapter 2 */ }
  },
  "Exodus": { /* ... */ }
};
```

### Required Components

1. **Word Mapper Generator Script**
   - Input: Bible versions (UNV, KJV, LCC, etc.) for a book/chapter
   - Process: Align words across versions using:
     - Strong's numbers (primary anchor)
     - Word position
     - Semantic similarity
   - Output: JSON mapping file per chapter

2. **Mapping Lookup API**
   ```javascript
   // Example API
   function findCorrespondingWord(sourceVersion, targetVersion, book, chapter, verse, wordPosition) {
     // Returns: { word: "上帝", offset: 2 }
   }

   function findWordByStrong(targetVersion, book, chapter, verse, strongNumber) {
     // Returns: { word: "上帝", position: 1, offset: 2 }
   }
   ```

3. **Integration with highlighting_foundation.js**
   ```javascript
   makeVerseEditableAndPositionCursor: function(sourceWord, strongNumber, verseNumber) {
     // Get target version from right reader
     const targetVersion = document.getElementById('right-reader-version-select').value;

     // Look up corresponding word using mapping
     const targetWord = WordMappingHelper.findWordByStrong(
       targetVersion, currentBook, currentChapter, verseNumber, strongNumber
     );

     // Find the word in right reader DOM
     const targetElement = this.findWordInVerse(targetWord.word, verseNumber, 'right');

     // Position cursor at right edge of target word
     this.positionCursorAfter(targetElement);
   }
   ```

### Implementation Steps

#### Phase 1: Mapping Generator (Priority)
- [ ] Create script to generate word mappings for a single chapter
- [ ] Test with Genesis 1 across UNV, KJV, LCC
- [ ] Validate mapping accuracy
- [ ] Store as JSON file: `word_mappings/Genesis_1.json`

#### Phase 2: Mapping Loader
- [ ] Create WordMappingHelper module to load and query mappings
- [ ] Implement lookup functions
- [ ] Add caching for performance
- [ ] Test with different version combinations

#### Phase 3: Integration
- [ ] Update `triggerMatchedHighlighting()` to use word mapping
- [ ] Modify `makeVerseEditableAndPositionCursor()` to:
   - Look up target word using mapping (not Strong's number matching)
   - Find word in DOM by text content
   - Position cursor correctly
- [ ] Test complete workflow

#### Phase 4: Scale Up
- [ ] Generate mappings for all chapters
- [ ] Optimize loading (lazy load per chapter)
- [ ] Add fallback logic for missing mappings
- [ ] Handle edge cases (multiple occurrences of same word)

### Benefits

1. **Works for ALL version combinations**
   - Left: UNV (with Strong's) → Right: LCC (no Strong's) ✅
   - Left: KJV (with Strong's) → Right: ESV (no Strong's) ✅
   - Any combination!

2. **Accurate word correspondence**
   - "神" → "上帝" (not just searching for "神")
   - "God" → "上帝"
   - Handles different word choices across translations

3. **Enables the core workflow**
   - Click word in reference version → Insert Strong's in target version
   - This is the PRIMARY use case for the editor!

### Expected User Workflow (After Implementation)

```
1. User selects: Left = UNV (with Strong's), Right = LCC (no Strong's)
2. User clicks "神" in left reader (UNV)
3. System:
   - Copies H0430 to clipboard
   - Fills H0430 into SN cpd field
   - Looks up mapping: "神" (UNV) → "上帝" (LCC)
   - Finds "上帝" in right reader DOM
   - Enables edit mode
   - Makes verse editable
   - Positions cursor after "上帝"
4. User presses Cmd+V
5. Result: "上帝<H0430>" in LCC text ✅
```

## Files to Create/Modify

### New Files
- `word_mappings/Genesis_1.json` - Word mapping data
- `js/word_mapping_helper.js` - Mapping loader and lookup API
- `scripts/generate_word_mappings.py` or `.js` - Mapping generator

### Modified Files
- `js/highlighting_foundation.js` - Update cursor positioning logic to use word mapping
- `index.html` - Load word_mapping_helper.js script

## Notes

- This is the CORRECT architecture for the Strong's insertion tool
- Word mapping should be generated ONCE per chapter, then reused
- Mapping quality is critical - may need manual verification for accuracy
- Consider using existing word alignment algorithms or APIs if available

## Next Session TODO

1. **Create word mapping generator** for Genesis 1
2. **Test mapping accuracy** manually
3. **Implement WordMappingHelper** API
4. **Update cursor positioning** to use mapping
5. **Test complete workflow** with UNV → LCC

---
*Created: 2025-01-20*
*Status: Planning - Ready for implementation*
