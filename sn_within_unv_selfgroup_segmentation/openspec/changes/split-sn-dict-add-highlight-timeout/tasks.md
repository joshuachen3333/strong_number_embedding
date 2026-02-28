## 1. HTML Layout Changes
- [x] 1.1 Remove global SN Dict checkbox from header-right in index.html
- [x] 1.2 Add SN Dict checkbox to left panel header (before Single HL)
- [x] 1.3 Add SN Dict checkbox to right panel header (first position)
- [x] 1.4 Convert Spec toggle button to checkbox style (after SN Dict)
- [x] 1.5 Update CSS version query parameter for cache busting

## 2. CSS Styling
- [x] 2.1 Add styles for panel-specific SN Dict checkboxes
- [x] 2.2 Update SN Dict tooltip styles to match Spec tooltip (hover-style floating)
- [x] 2.3 Remove old popup-style tooltip CSS if no longer needed (kept for backwards compatibility)

## 3. SN Dictionary Module Updates
- [x] 3.1 Refactor sn_dictionary.js to support dual panel controls
- [x] 3.2 Add left panel SN Dict state management
- [x] 3.3 Add right panel SN Dict state management
- [x] 3.4 Implement hover-style floating tooltip (like Spec tooltip)
- [x] 3.5 Add auto-show tooltip on highlight when panel's SN Dict is checked

## 4. Highlight Timeout System
- [x] 4.1 Add global highlight timeout manager (10-second timer)
- [x] 4.2 Implement timeout reset on new highlight actions
- [x] 4.3 Implement synchronized cleanup: blue → orange → tooltips
- [x] 4.4 Integrate timeout with navigation.js keyboard highlights
- [x] 4.5 Integrate timeout with left_panel.js click highlights
- [x] 4.6 Integrate timeout with right_panel.js click highlights

## 5. localStorage Persistence
- [x] 5.1 Add localStorage key for left panel SN Dict setting
- [x] 5.2 Add localStorage key for right panel SN Dict setting
- [x] 5.3 Update app.js initialization to restore panel-specific settings (handled in sn_dictionary.js)
- [x] 5.4 Remove old global SN Dict localStorage handling (old key ignored, new keys used)

## 6. Testing
- [x] 6.1 Test left panel SN Dict toggle independently
- [x] 6.2 Test right panel SN Dict toggle independently
- [x] 6.3 Test Spec checkbox functionality after conversion
- [x] 6.4 Test auto-show tooltip on blue highlight (local click)
- [x] 6.5 Test auto-show tooltip on orange highlight (remote)
- [x] 6.6 Test 10-second timeout clears highlights and tooltips
- [x] 6.7 Test new highlight resets timeout
- [x] 6.8 Test synchronized cleanup order (blue → orange → tooltips)
- [x] 6.9 Test localStorage persistence across page reloads
