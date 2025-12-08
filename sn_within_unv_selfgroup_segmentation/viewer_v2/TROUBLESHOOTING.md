# Troubleshooting Viewer v2

## Issue: Right panel not showing parsed result

### Quick Checks

1. **Open Browser Console** (F12 → Console tab)
   - Look for RED error messages
   - Common errors:
     - "Failed to fetch" → manifest.json or parsed files not accessible
     - "Uncaught TypeError" → JavaScript error in modules
     - "Mediator is not defined" → Script loading order issue

2. **Run Console Test**
   - Copy contents of `console-test.js`
   - Paste into browser console
   - Press Enter
   - Check output for failures

3. **Check Manual Verse Selection**
   In console, run:
   ```javascript
   Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
     book: 'Gen',
     chapter: 1,
     verse: 1
   });
   ```
   Does right panel update?

### Common Issues

#### Issue 1: Manifest Not Loading
**Symptom**: Book dropdown is empty or shows error banner

**Fix**: Check path
```bash
ls output/manifest.json  # Should exist
```

#### Issue 2: Events Not Firing
**Symptom**: Click verse, nothing happens

**Debug**:
```javascript
// In console
Mediator.subscribe(Mediator.EVENT_TYPES.VERSE_SELECT, (data) => {
  console.log('VERSE SELECT:', data);
});

// Then click a verse - should see log
```

#### Issue 3: Script Loading Order
**Symptom**: "X is not defined" errors

**Check**: index.html script order must be:
1. mediator.js (FIRST!)
2. ui_utils.js
3. book_data.js
4. data_loader.js
5. ...rest...
6. app.js (LAST!)

#### Issue 4: Data Path Wrong
**Symptom**: "Failed to fetch ../output/..."

**Fix**: Relative paths from viewer_v2/:
- Manifest: `../output/manifest.json`
- Parsed: `../output/Gen/1/1`

### Manual Event Flow Test

```javascript
// 1. Check subscribers
Mediator.getSubscribers()
// Should show verse:select, verse:selected, chapter:load, etc.

// 2. Trigger chapter load
Mediator.publish(Mediator.EVENT_TYPES.CHAPTER_LOAD, {
  book: 'Gen',
  chapter: 1,
  versePosition: 'first'
});

// 3. Wait 2 seconds, then check
setTimeout(() => {
  console.log(LeftPanel.getCurrentPosition());
}, 2000);
```

### If All Else Fails

1. Check Network tab (F12 → Network)
   - Reload page
   - Look for failed requests (red)
   - Click on failed request to see error

2. Add debug logging to app.js:
   ```javascript
   // At top of handleVerseSelect
   console.log('[DEBUG] handleVerseSelect called:', data);
   ```

3. Compare with working viewer v1:
   ```
   http://localhost:8000/viewer/
   ```
   Does v1 work? If yes, v2 has a code issue.
   If no, server/data issue.
