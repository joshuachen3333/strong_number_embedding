## 1. Add Version Separator

- [x] 1.1 Add thick horizontal separator line between UNV and KJV sections
  - Use `border-bottom` on `.unv-section` (blue, ~4-5px)
  - Use `border-top` on `.kjv-section` (teal, ~4-5px)
  - Creates a two-tone separator effect

## 2. Update Selected Verse Border

- [x] 2.1 Modify `.verse.selected` in UNV section
  - Change from left+right border to full rectangular border (all 4 sides)
  - Use blue color (`var(--unv-color)`)
  - Border width: 4px (thicker than current 3px, thinner than separator)

- [x] 2.2 Add version-specific selected verse styling
  - `.unv-section .verse.selected`: blue border
  - `.kjv-section .verse.selected`: teal border

## 3. Update Version Cache Buster

- [x] 3.1 Update CSS version parameter in `index.html`

## 4. Verify

- [x] 4.1 Test with only UNV visible - verify blue border on selected verse
- [x] 4.2 Test with only KJV visible - verify teal border on selected verse
- [x] 4.3 Test with both visible - verify:
  - Two-tone separator line between sections
  - Blue border on UNV selected verse
  - Teal border on KJV selected verse
  - Both versions highlight the same verse number
