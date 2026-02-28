/**
 * left_panel.js
 * Left panel (UNV/KJV Reader) with event-driven architecture
 */

const LeftPanel = (() => {
  let currentBook = null;
  let currentChap = null;
  let currentSec = null;
  let chapSecs = {};           // UNV sec data
  let kjvChapSecs = {};        // KJV sec data
  let lccChapSecs = {};        // LCC sec data
  let clickHandlerAttached = false;
  let currentColorMap = {};
  let currentGroups = [];

  // Version toggle states
  let unvActive = true;
  let kjvActive = false;
  let lccActive = false;

  // Per-version settings
  let unvSNDict = false;
  let unvSingleHL = true;
  let kjvSNDict = false;
  let kjvSingleHL = true;
  let lccSingleHL = true;

  // DOM elements
  const leftContent = document.getElementById('left-content');
  const unvContent = document.getElementById('unv-content');
  const kjvContent = document.getElementById('kjv-content');
  const lccContent = document.getElementById('lcc-content');
  const leftVerseRef = document.getElementById('left-verse-ref');

  // Toggle buttons
  const toggleUNV = document.getElementById('toggle-unv');
  const toggleKJV = document.getElementById('toggle-kjv');
  const toggleLCC = document.getElementById('toggle-lcc');

  // Control groups
  const unvControls = document.querySelector('.unv-controls');
  const kjvControls = document.querySelector('.kjv-controls');
  const lccControls = document.querySelector('.lcc-controls');

  // Checkboxes
  const unvSNDictCheckbox = document.getElementById('unv-sn-dict-toggle');
  const unvSingleHLCheckbox = document.getElementById('unv-single-hl-mode');
  const kjvSNDictCheckbox = document.getElementById('kjv-sn-dict-toggle');
  const kjvSingleHLCheckbox = document.getElementById('kjv-single-hl-mode');
  const lccSingleHLCheckbox = document.getElementById('lcc-single-hl-mode');

  /**
   * Initialize left panel (subscribe to events)
   */
  function init() {
    console.log('[LeftPanel] Initializing...');

    // Subscribe to chapter loaded event
    Mediator.subscribe(Mediator.EVENT_TYPES.CHAPTER_LOADED, handleChapterLoaded);

    // Subscribe to colors apply event
    Mediator.subscribe(Mediator.EVENT_TYPES.COLORS_APPLY, handleColorsApply);

    // Subscribe to verse selected event (for highlighting only)
    Mediator.subscribe(Mediator.EVENT_TYPES.VERSE_SELECTED, handleVerseSelected);

    // Subscribe to SN click event for highlighting
    Mediator.subscribe(Mediator.EVENT_TYPES.SN_CLICK, handleSNClickForHighlighting);

    // Initialize toggle buttons
    initToggleButtons();

    // Initialize checkboxes
    initCheckboxes();

    // Add click handler once (event delegation)
    if (!clickHandlerAttached) {
      leftContent.addEventListener('click', handleVerseClick);
      clickHandlerAttached = true;
      console.log('[LeftPanel] Click handler attached');
    }

    // Apply initial visibility
    updateVersionVisibility();
  }

  /**
   * Initialize toggle button event listeners
   */
  function initToggleButtons() {
    if (toggleUNV) {
      toggleUNV.addEventListener('click', () => {
        unvActive = !unvActive;
        toggleUNV.classList.toggle('active', unvActive);
        updateVersionVisibility();
        console.log(`[LeftPanel] UNV toggle: ${unvActive ? 'ON' : 'OFF'}`);
      });
    }

    if (toggleKJV) {
      toggleKJV.addEventListener('click', () => {
        kjvActive = !kjvActive;
        toggleKJV.classList.toggle('active', kjvActive);
        updateVersionVisibility();
        // Load KJV data if activating and we have a current chapter
        if (kjvActive && currentBook && currentChap) {
          loadKJVData();
        }
        console.log(`[LeftPanel] KJV toggle: ${kjvActive ? 'ON' : 'OFF'}`);
      });
    }

    if (toggleLCC) {
      toggleLCC.addEventListener('click', () => {
        lccActive = !lccActive;
        toggleLCC.classList.toggle('active', lccActive);
        updateVersionVisibility();
        // Load LCC data if activating and we have a current chapter
        if (lccActive && currentBook && currentChap) {
          loadLCCData();
        }
        console.log(`[LeftPanel] LCC toggle: ${lccActive ? 'ON' : 'OFF'}`);
      });
    }
  }

  /**
   * Initialize checkbox event listeners
   */
  function initCheckboxes() {
    if (unvSNDictCheckbox) {
      unvSNDict = unvSNDictCheckbox.checked;
      unvSNDictCheckbox.addEventListener('change', (e) => {
        unvSNDict = e.target.checked;
        console.log(`[LeftPanel] UNV SN Dict: ${unvSNDict ? 'ON' : 'OFF'}`);
      });
    }

    if (unvSingleHLCheckbox) {
      unvSingleHL = unvSingleHLCheckbox.checked;
      unvSingleHLCheckbox.addEventListener('change', (e) => {
        unvSingleHL = e.target.checked;
        console.log(`[LeftPanel] UNV Single HL: ${unvSingleHL ? 'ON' : 'OFF'}`);
      });
    }

    if (kjvSNDictCheckbox) {
      kjvSNDict = kjvSNDictCheckbox.checked;
      kjvSNDictCheckbox.addEventListener('change', (e) => {
        kjvSNDict = e.target.checked;
        console.log(`[LeftPanel] KJV SN Dict: ${kjvSNDict ? 'ON' : 'OFF'}`);
      });
    }

    if (kjvSingleHLCheckbox) {
      kjvSingleHL = kjvSingleHLCheckbox.checked;
      kjvSingleHLCheckbox.addEventListener('change', (e) => {
        kjvSingleHL = e.target.checked;
        console.log(`[LeftPanel] KJV Single HL: ${kjvSingleHL ? 'ON' : 'OFF'}`);
      });
    }

    if (lccSingleHLCheckbox) {
      lccSingleHL = lccSingleHLCheckbox.checked;
      lccSingleHLCheckbox.addEventListener('change', (e) => {
        lccSingleHL = e.target.checked;
        console.log(`[LeftPanel] LCC Single HL: ${lccSingleHL ? 'ON' : 'OFF'}`);
      });
    }
  }

  /**
   * Update version content and control visibility
   */
  function updateVersionVisibility() {
    // Update content visibility
    if (unvContent) {
      unvContent.style.display = unvActive ? 'block' : 'none';
    }
    if (kjvContent) {
      kjvContent.style.display = kjvActive ? 'block' : 'none';
    }
    if (lccContent) {
      lccContent.style.display = lccActive ? 'block' : 'none';
    }

    // Update control visibility
    if (unvControls) {
      unvControls.style.display = unvActive ? 'inline-flex' : 'none';
    }
    if (kjvControls) {
      kjvControls.style.display = kjvActive ? 'inline-flex' : 'none';
    }
    if (lccControls) {
      lccControls.style.display = lccActive ? 'inline-flex' : 'none';
    }
  }

  /**
   * Load KJV data for current chapter
   */
  async function loadKJVData() {
    if (!currentBook || !currentChap) return;

    console.log(`[LeftPanel] Loading KJV data for ${currentBook} ${currentChap}`);

    try {
      const kjvData = await DataLoader.fetchKJVChapterFromAPI(currentBook, currentChap);
      kjvChapSecs = {};

      kjvData.forEach(secObj => {
        const secNum = secObj.sec;
        kjvChapSecs[secNum] = {
          text: secObj.bible_text || '',
          isUncertain: false
        };
      });

      renderKJVContent();
      console.log(`[LeftPanel] KJV data loaded: ${Object.keys(kjvChapSecs).length} secs`);
    } catch (error) {
      console.error('[LeftPanel] Error loading KJV data:', error);
    }
  }

  /**
   * Load LCC data for current chapter
   */
  async function loadLCCData() {
    if (!currentBook || !currentChap) return;

    console.log(`[LeftPanel] Loading LCC data for ${currentBook} ${currentChap}`);

    try {
      const lccData = await DataLoader.fetchLCCChapterFromAPI(currentBook, currentChap);
      lccChapSecs = {};

      lccData.forEach(secObj => {
        const secNum = secObj.sec;
        lccChapSecs[secNum] = {
          text: secObj.bible_text || ''
        };
      });

      renderLCCContent();
      console.log(`[LeftPanel] LCC data loaded: ${Object.keys(lccChapSecs).length} secs`);
    } catch (error) {
      console.error('[LeftPanel] Error loading LCC data:', error);
    }
  }

  /**
   * Handle chapter loaded event
   * @param {Object} data - {book, chapter, verseData}
   */
  function handleChapterLoaded(data) {
    const { book, chapter, verseData } = data;
    currentBook = book;
    currentChap = chapter;
    chapSecs = verseData;

    renderUNVContent();

    // Load KJV data if KJV is active
    if (kjvActive) {
      loadKJVData();
    }

    // Load LCC data if LCC is active
    if (lccActive) {
      loadLCCData();
    }
  }

  /**
   * Render UNV chapter secs
   */
  function renderUNVContent() {
    if (!unvContent) return;

    if (Object.keys(chapSecs).length === 0) {
      unvContent.innerHTML = '<div class="loading-message">無法載入章節資料</div>';
      return;
    }

    let html = '';
    const secNumbers = Object.keys(chapSecs).map(Number).sort((a, b) => a - b);

    secNumbers.forEach(secNum => {
      const data = chapSecs[secNum];
      const uncertainClass = data.isUncertain ? 'uncertain' : '';

      html += `
        <div class="verse ${uncertainClass}" data-verse="${secNum}" data-version="unv">
          <span class="verse-num">${secNum}</span>
          <span class="verse-text">${escapeHtml(data.text)}</span>
        </div>
      `;
    });

    unvContent.innerHTML = html;
    console.log(`[LeftPanel] Rendered ${secNumbers.length} UNV secs`);
  }

  /**
   * Render KJV chapter secs
   */
  function renderKJVContent() {
    if (!kjvContent) return;

    if (Object.keys(kjvChapSecs).length === 0) {
      kjvContent.innerHTML = '<div class="loading-message">Loading KJV...</div>';
      return;
    }

    let html = '';
    const secNumbers = Object.keys(kjvChapSecs).map(Number).sort((a, b) => a - b);

    secNumbers.forEach(secNum => {
      const data = kjvChapSecs[secNum];

      html += `
        <div class="verse" data-verse="${secNum}" data-version="kjv">
          <span class="verse-num">${secNum}</span>
          <span class="verse-text">${escapeHtml(data.text)}</span>
        </div>
      `;
    });

    kjvContent.innerHTML = html;
    console.log(`[LeftPanel] Rendered ${secNumbers.length} KJV secs`);

    // Apply colors if we have a color map
    if (Object.keys(currentColorMap).length > 0) {
      applyColorsToKJV();
    }
  }

  /**
   * Render LCC chapter secs
   */
  function renderLCCContent() {
    if (!lccContent) return;

    if (Object.keys(lccChapSecs).length === 0) {
      lccContent.innerHTML = '<div class="loading-message">Loading LCC (呂振中譯本)...</div>';
      return;
    }

    let html = '';
    const secNumbers = Object.keys(lccChapSecs).map(Number).sort((a, b) => a - b);

    secNumbers.forEach(secNum => {
      const data = lccChapSecs[secNum];

      html += `
        <div class="verse" data-verse="${secNum}" data-version="lcc">
          <span class="verse-num">${secNum}</span>
          <span class="verse-text">${escapeHtml(data.text)}</span>
        </div>
      `;
    });

    lccContent.innerHTML = html;
    console.log(`[LeftPanel] Rendered ${secNumbers.length} LCC secs`);

    // Apply colors if we have a color map
    if (Object.keys(currentColorMap).length > 0) {
      applyColorsToLCC();
    }
  }

  /**
   * Handle verse click
   * @param {Event} e
   */
  function handleVerseClick(e) {
    const verseEl = e.target.closest('.verse');
    if (!verseEl) return;

    // Check if clicking on an SN tag
    const snTag = e.target.closest('.sn-tag');
    const version = verseEl.dataset.version || 'unv';

    // Don't trigger verse selection if user is selecting text (unless clicking SN tag)
    const selection = window.getSelection();
    if (!snTag && selection && selection.toString().length > 0) {
      console.log('[LeftPanel] Text selection detected, skipping verse click');
      return;
    }

    const sec = parseInt(verseEl.dataset.verse);

    // If clicking SN on same sec, don't re-select (preserves highlighting)
    if (snTag && sec === currentSec) {
      console.log(`[LeftPanel] SN click on same sec ${sec}, skipping re-select`);
      return;
    }

    console.log(`[LeftPanel] Sec ${sec} clicked (${version})${snTag ? ' (SN tag)' : ''}`);

    // Publish verse select event
    Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
      book: currentBook,
      chapter: currentChap,
      verse: sec
    });
  }

  /**
   * Handle verse selected event (update UI only)
   * @param {Object} data - {book, chapter, verse}
   */
  function handleVerseSelected(data) {
    const { verse } = data;

    // Only clear SN highlighting when switching to a DIFFERENT verse
    const switchingVerses = verse !== currentSec;
    currentSec = verse;

    if (switchingVerses) {
      clearHighlighting();
    }

    // Update selection highlight for both UNV and KJV
    leftContent.querySelectorAll('.verse').forEach(el => {
      el.classList.remove('selected');
    });

    // Select verse in all versions
    const unvVerseEl = unvContent?.querySelector(`.verse[data-verse="${verse}"]`);
    const kjvVerseEl = kjvContent?.querySelector(`.verse[data-verse="${verse}"]`);
    const lccVerseEl = lccContent?.querySelector(`.verse[data-verse="${verse}"]`);

    if (unvVerseEl) {
      unvVerseEl.classList.add('selected');
      if (unvActive) {
        unvVerseEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    if (kjvVerseEl) {
      kjvVerseEl.classList.add('selected');
      if (kjvActive) {
        kjvVerseEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    if (lccVerseEl) {
      lccVerseEl.classList.add('selected');
      if (lccActive) {
        lccVerseEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    // Update verse reference display
    if (leftVerseRef) {
      leftVerseRef.textContent = `${currentBook} ${currentChap}:${verse}`;
      leftVerseRef.style.display = 'block';
    }
  }

  /**
   * Handle colors apply event
   * @param {Object} data - {colorMap, groups}
   */
  function handleColorsApply(data) {
    const { colorMap, groups } = data;

    // Store for highlighting
    currentColorMap = colorMap || {};
    currentGroups = groups || [];

    // Apply colors to UNV content
    applyColorsToUNV();

    // Apply colors to KJV content if active
    if (kjvActive && Object.keys(kjvChapSecs).length > 0) {
      applyColorsToKJV();
    }

    // Apply colors to LCC content if active
    if (lccActive && Object.keys(lccChapSecs).length > 0) {
      applyColorsToLCC();
    }
  }

  /**
   * Apply colors to UNV content
   */
  function applyColorsToUNV() {
    if (!unvContent) return;

    unvContent.querySelectorAll('.verse').forEach(verseEl => {
      const secNum = parseInt(verseEl.dataset.verse);
      const secData = chapSecs[secNum];
      if (!secData) return;

      const textEl = verseEl.querySelector('.verse-text');
      if (!textEl) return;

      // Apply colors to raw text
      const useGroups = (secNum === currentSec) ? currentGroups : undefined;
      const coloredHtml = ColorMapper.applyColorsToRawText(secData.text, currentColorMap, useGroups);
      textEl.innerHTML = coloredHtml;

      // Add SN click handlers
      addSNClickHandlers(textEl, secNum, 'unv');
    });
  }

  /**
   * Apply colors to KJV content
   */
  function applyColorsToKJV() {
    if (!kjvContent) return;

    kjvContent.querySelectorAll('.verse').forEach(verseEl => {
      const secNum = parseInt(verseEl.dataset.verse);
      const secData = kjvChapSecs[secNum];
      if (!secData) return;

      const textEl = verseEl.querySelector('.verse-text');
      if (!textEl) return;

      // Apply colors to raw text (use groups for selected verse, same as UNV)
      const useGroups = (secNum === currentSec) ? currentGroups : undefined;
      const coloredHtml = ColorMapper.applyColorsToRawText(secData.text, currentColorMap, useGroups);
      textEl.innerHTML = coloredHtml;

      // Add SN click handlers
      addSNClickHandlers(textEl, secNum, 'kjv');
    });
  }

  /**
   * Apply colors to LCC content by matching Chinese words from UNV
   */
  function applyColorsToLCC() {
    if (!lccContent) return;

    lccContent.querySelectorAll('.verse').forEach(verseEl => {
      const secNum = parseInt(verseEl.dataset.verse);
      const lccData = lccChapSecs[secNum];
      if (!lccData) return;

      const textEl = verseEl.querySelector('.verse-text');
      if (!textEl) return;

      // Only color the selected verse (need UNV raw text + groups)
      if (secNum === currentSec && currentGroups.length > 0) {
        const unvData = chapSecs[secNum];
        const unvRawText = unvData ? unvData.text : null;
        const coloredHtml = ColorMapper.applyColorsToPlainText(lccData.text, unvRawText, currentGroups);
        textEl.innerHTML = coloredHtml;
      } else {
        textEl.innerHTML = escapeHtml(lccData.text);
      }
    });
  }

  /**
   * Add SN click handlers to a text element
   * @param {Element} textEl - The text element containing SN tags
   * @param {number} secNum - Sec number
   * @param {string} version - 'unv' or 'kjv'
   */
  function addSNClickHandlers(textEl, secNum, version) {
    textEl.querySelectorAll('.sn-tag').forEach(tag => {
      tag.addEventListener('click', (e) => {
        const snCode = extractSNCode(tag.textContent);
        if (snCode) {
          const groupSNs = ColorMapper.getSNGroupFromColorMap(snCode, currentColorMap, currentGroups, tag);

          Mediator.publish(Mediator.EVENT_TYPES.SN_CLICK, {
            source: 'left',
            element: tag,
            snCode: snCode,
            groupSNs: groupSNs,
            verse: secNum,
            version: version,
            snDictEnabled: version === 'unv' ? unvSNDict : kjvSNDict
          });
        }
      });
    });
  }

  /**
   * Extract SN code from tag text
   * @param {string} text - e.g., "<WH07225>" or "{<WH07225>}"
   * @returns {string|null}
   */
  function extractSNCode(text) {
    const match = text.match(/\d+/);
    return match ? match[0] : null;
  }

  /**
   * Get current position
   * @returns {Object} {book, chapter, verse}
   */
  function getCurrentPosition() {
    return {
      book: currentBook,
      chapter: currentChap,
      verse: currentSec
    };
  }

  /**
   * Get verse numbers array
   * @returns {number[]}
   */
  function getVerseNumbers() {
    return Object.keys(chapSecs).map(Number).sort((a, b) => a - b);
  }

  /**
   * Escape HTML
   * @param {string} text
   * @returns {string}
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Handle SN click for highlighting
   * @param {Object} event - {source, snCode, groupSNs, element, verse, version}
   */
  function handleSNClickForHighlighting(event) {
    const { source, groupSNs, verse, version } = event;

    console.log(`[LeftPanel] SN click - source=${source}, verse=${verse}, version=${version}`);

    // Determine which Single HL mode to use based on source
    const useUnvSingleHL = source === 'left' && version === 'unv' ? unvSingleHL : unvSingleHL;
    const useKjvSingleHL = source === 'left' && version === 'kjv' ? kjvSingleHL : kjvSingleHL;
    const useLccSingleHL = lccSingleHL;

    // Clear previous highlighting based on per-version settings
    if (unvActive && useUnvSingleHL) {
      clearHighlightingInContainer(unvContent);
    }
    if (kjvActive && useKjvSingleHL) {
      clearHighlightingInContainer(kjvContent);
    }
    if (lccActive && useLccSingleHL) {
      clearHighlightingInContainer(lccContent);
    }

    // Apply highlighting to all active versions
    // UNV and KJV use group-based coloring, LCC uses word-match coloring
    if (source === 'left') {
      // Clicked in left panel - highlight local (blue)
      if (unvActive) highlightInContainer(unvContent, groupSNs, verse, 'clicked-local', useUnvSingleHL);
      if (kjvActive) highlightInContainer(kjvContent, groupSNs, verse, 'clicked-local', useKjvSingleHL);
      if (lccActive) highlightInLCCContainer(lccContent, groupSNs, verse, 'clicked-local', useLccSingleHL);
    } else {
      // Clicked in right panel - highlight remote (orange)
      if (unvActive) highlightInContainer(unvContent, groupSNs, verse, 'clicked-remote', useUnvSingleHL);
      if (kjvActive) highlightInContainer(kjvContent, groupSNs, verse, 'clicked-remote', useKjvSingleHL);
      if (lccActive) highlightInLCCContainer(lccContent, groupSNs, verse, 'clicked-remote', useLccSingleHL);
    }
  }

  /**
   * Clear highlighting in a specific container
   * @param {Element} container
   */
  function clearHighlightingInContainer(container) {
    if (!container) return;
    container.querySelectorAll('.clicked-local, .clicked-remote').forEach(el => {
      el.classList.remove('clicked-local', 'clicked-remote');
    });
  }

  /**
   * Clear all highlighting
   */
  function clearHighlighting() {
    clearHighlightingInContainer(unvContent);
    clearHighlightingInContainer(kjvContent);
    clearHighlightingInContainer(lccContent);
  }

  /**
   * Highlight SNs in a container
   * @param {Element} container
   * @param {string[]} groupSNs - Array of SN codes to highlight
   * @param {number} verse - Verse number to limit highlighting (when Single HL mode is ON)
   * @param {string} className - CSS class to add ('clicked-local' or 'clicked-remote')
   * @param {boolean} singleHLMode - Whether to limit to current verse
   */
  function highlightInContainer(container, groupSNs, verse, className, singleHLMode) {
    if (!container) return;

    let searchContainer = container;

    // If single HL mode is ON and verse is specified, limit to that verse
    if (singleHLMode && verse) {
      searchContainer = container.querySelector(`.verse[data-verse="${verse}"]`);
      if (!searchContainer) {
        console.warn(`[LeftPanel] Verse ${verse} not found for highlighting`);
        return;
      }
    }

    // Use color-based filtering with currentGroups
    // Both UNV and KJV now have group-based coloring for the selected verse
    const elements = ColorMapper.findCorrespondingElements(groupSNs, searchContainer, '.sn-tag', currentGroups);
    console.log(`[LeftPanel] Found ${elements.length} elements to highlight (${className})`);
    elements.forEach(el => el.classList.add(className));
  }

  /**
   * Highlight matching words in LCC container by group color
   * LCC has .sn-text spans (no .sn-tag), so we match by background color
   * @param {Element} container
   * @param {string[]} groupSNs - SN codes in the clicked group
   * @param {number} verse - Verse number
   * @param {string} className - CSS class ('clicked-local' or 'clicked-remote')
   * @param {boolean} singleHLMode - Limit to current verse
   */
  function highlightInLCCContainer(container, groupSNs, verse, className, singleHLMode) {
    if (!container) return;

    let searchContainer = container;
    if (singleHLMode && verse) {
      searchContainer = container.querySelector(`.verse[data-verse="${verse}"]`);
      if (!searchContainer) return;
    }

    // Find the group color for these SNs
    let targetColor = null;
    for (let i = 0; i < currentGroups.length; i++) {
      const group = currentGroups[i];
      if (group.sns.some(sn => groupSNs.includes(sn))) {
        targetColor = ColorMapper.getColorForGroup(i);
        break;
      }
    }
    if (!targetColor) return;

    // Find .sn-text elements with matching background color
    const targetRgb = hexToRgb(targetColor);
    searchContainer.querySelectorAll('.sn-text').forEach(el => {
      const elColor = el.style.backgroundColor;
      if (elColor === targetRgb || elColor === targetColor) {
        el.classList.add(className);
      }
    });
  }

  /**
   * Convert hex to rgb for color comparison
   */
  function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return hex;
    return `rgb(${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)})`;
  }

  /**
   * Get SN Dict enabled state for a version
   * @param {string} version - 'unv' or 'kjv'
   * @returns {boolean}
   */
  function isSNDictEnabled(version) {
    return version === 'kjv' ? kjvSNDict : unvSNDict;
  }

  /**
   * Clear left panel
   */
  function clear() {
    if (unvContent) {
      unvContent.innerHTML = '<div class="loading-message">請選擇書卷和章節...</div>';
    }
    if (kjvContent) {
      kjvContent.innerHTML = '<div class="loading-message">Loading KJV...</div>';
    }
    if (lccContent) {
      lccContent.innerHTML = '<div class="loading-message">Loading LCC (呂振中譯本)...</div>';
    }
    currentBook = null;
    currentChap = null;
    currentSec = null;
    chapSecs = {};
    kjvChapSecs = {};
    lccChapSecs = {};
    currentColorMap = {};
    currentGroups = [];
    if (leftVerseRef) {
      leftVerseRef.style.display = 'none';
    }
  }

  // Public API
  return {
    init,
    getCurrentPosition,
    getVerseNumbers,
    isSNDictEnabled,
    clear
  };
})();
