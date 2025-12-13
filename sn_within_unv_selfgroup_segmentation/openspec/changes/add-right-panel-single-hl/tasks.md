## 1. HTML Changes
- [x] 1.1 Add `right-single-highlight-mode` checkbox after Spec checkbox in right panel header
- [x] 1.2 Add label with text "Single HL" and appropriate title attribute
- [x] 1.3 Set checkbox default to `checked` for backwards compatibility

## 2. JavaScript Changes
- [x] 2.1 Update `right_panel.js` selector from `#single-highlight-mode` to `#right-single-highlight-mode`
- [x] 2.2 Update initialization log message to clarify it's the right panel checkbox

## 3. Testing
- [x] 3.1 Verify right panel Single HL checkbox appears in correct position (after Spec)
- [x] 3.2 Test: Right panel Single HL ON → clicking SN clears previous right panel highlights
- [x] 3.3 Test: Right panel Single HL OFF → clicking SN accumulates right panel highlights
- [x] 3.4 Test: Left and right panel Single HL work independently
