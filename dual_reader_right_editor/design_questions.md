# Right Editor Design Decisions

This document records the design decisions for the dual reader with right editor functionality.

## User Preferences (Decided)

### Q1: Editor Interface Approach
**Selected: Option C - Hybrid (View All, Edit One)**
- Show all verses in chapter view
- Only selected verse becomes editable
- Clear indication of which verse is being edited
- Easy navigation between verses

### Q2: Strong's Number Insertion Method
**Selected: Method C - Auto-Suggest from Left Reader**
- User clicks word in right editor
- System checks if left reader has Strong's for same verse position
- Auto-suggests matching Strong's number from left reader
- User clicks to accept/reject suggestion
- Provides intelligent assistance based on reference text

### Q3: Strong's Number Format
**Selected: FHL Format**
- Hebrew: `<WH1234>`
- Greek: `<WG5678>`
- Maintains consistency with FHL.net standard format
- Clear distinction between Hebrew and Greek numbers

### Q4: Visual Feedback and Progress
**Selected: All suggestions accepted**
- Per-verse indicators: ✅ ✏️ ❌ (completed, edited, untouched)
- Per-chapter progress: "15/31 verses edited (48%)"
- Per-book progress bar or percentage
- Edited verses: Different background color
- Strong's numbers: Highlighted/colored differently
- Unsaved changes: Border color change

### Q5: Synchronization Behavior
**Selected: Smart Editing Mode Sync**
- **When right enters editing mode**: Left automatically follows (unless manually unchecked later)
- **When left has Strong's numbers**: Right highlights suggestions and already inserted Strong's
- **When right has verse being edited**: Left highlights same verse and highlights the word being clicked (for insertion)
- **Bidirectional highlighting**: Both readers show corresponding positions

### Q6: Data Persistence Strategy
**Selected: Hybrid Auto-save + Manual Save**
- Auto-save: Every 30 seconds + on navigation
- Manual save button for user peace of mind
- Both localStorage (working data) + export (backup files)

### Q7: Workflow Integration
**Selected: Chapter-by-Chapter Sequential Work**
1. Load reference text (KJV/UNV) with Strong's in left reader
2. Load target text (呂振中 or other version) in right editor
3. Navigate chapter by chapter, adding Strong's numbers
4. Export completed chapters

**Note**: Work might be done on versions other than LCC (呂振中), so editor should support any version selection.

## Implementation Notes

### Version Flexibility
- Editor should work with any Bible version, not just LCC
- User should be able to select target version for editing
- System should handle versions with or without existing Strong's numbers

### Auto-Suggestion Logic
- Match by verse position and word similarity
- Handle cases where verse structures differ between versions
- Provide fallback when no clear match exists

### Highlighting Coordination
- Left reader highlights: current verse + clicked word
- Right editor highlights: suggested Strong's positions + already inserted Strong's
- Visual distinction between suggestions vs confirmed insertions

### Progress Tracking
- Track completion at verse, chapter, and book levels
- Persist progress across sessions
- Export progress reports with completed work

## Future Considerations

### Potential Changes
- Insertion method might need refinement based on usage
- Synchronization behavior might need adjustment for complex editing scenarios
- Additional export formats might be needed
- Undo/redo functionality requirements
- Keyboard shortcut preferences
- Multi-user collaboration features

### Technical Extensibility
- Support for different Strong's number formats if needed
- Integration with external Strong's dictionaries
- Bulk editing operations
- Version comparison features
- Advanced search and replace for Strong's numbers

---

**Date Created**: 2025-01-15
**Last Updated**: 2025-01-15
**Status**: Initial design decisions recorded