// Paste this into the browser console to test the event flow

console.log('=== Testing Viewer v2 ===');

// Test 1: Check if modules loaded
console.log('\n1. Modules loaded?');
console.log('Mediator:', typeof Mediator !== 'undefined' ? '✓' : '✗');
console.log('DataLoader:', typeof DataLoader !== 'undefined' ? '✓' : '✗');
console.log('App:', typeof App !== 'undefined' ? '✓' : '✗');
console.log('LeftPanel:', typeof LeftPanel !== 'undefined' ? '✓' : '✗');
console.log('RightPanel:', typeof RightPanel !== 'undefined' ? '✓' : '✗');

// Test 2: Check event subscribers
console.log('\n2. Event subscribers:');
if (typeof Mediator !== 'undefined') {
  console.log(Mediator.getSubscribers());
}

// Test 3: Manually trigger verse select
console.log('\n3. Manually triggering verse:select event...');
if (typeof Mediator !== 'undefined') {
  Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
    book: 'Gen',
    chapter: 1,
    verse: 1
  });
  console.log('Event published. Check if right panel updates.');
}

// Test 4: Check manifest
console.log('\n4. Testing manifest load...');
if (typeof DataLoader !== 'undefined') {
  DataLoader.loadManifest().then(manifest => {
    console.log('Manifest books:', Object.keys(manifest.books).slice(0, 5));
  });
}

// Test 5: Check current position
setTimeout(() => {
  console.log('\n5. Current position:');
  if (typeof LeftPanel !== 'undefined') {
    console.log(LeftPanel.getCurrentPosition());
  }
}, 2000);

console.log('\n=== Tests complete. Check output above ===');
