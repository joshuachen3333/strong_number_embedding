## 1. CSS Changes
- [x] 1.1 Add CSS variable `--tooltip-opacity: 0.75` to `.sn-dict-floating-tooltip`
- [x] 1.2 Change `.sn-dict-floating-tooltip` background from `#2c3e50` to `rgba(44, 62, 80, var(--tooltip-opacity))`
- [x] 1.3 Update CSS version in index.html for cache busting

## 2. Testing
- [x] 2.1 Verify tooltip shows with semi-transparent background
- [x] 2.2 Verify highlighted SN is visible through tooltip when overlapping
- [x] 2.3 Verify tooltip text remains readable at default opacity
