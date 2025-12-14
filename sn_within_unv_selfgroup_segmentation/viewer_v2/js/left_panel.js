/**
 * left_panel.js
 * Left panel (UNV/KJV Reader) with event-driven architecture
 */

const LeftPanel = (() => {
  let currentBook = null;
  let currentChapter = null;
  let currentVerse = null;
  let chapterVerses = {};      // UNV verse data
  let kjvChapterVerses = {};   // KJV verse data
  let clickHandlerAttached = false;
  let currentColorMap = {};
  let currentGroups = [];

  // Version toggle states
  let unvActive = true;
  let kjvActive = false;

  // Per-version settings
  let unvSNDict = false;
  let unvSingleHL = true;
  let kjvSNDict = false;
  let kjvSingleHL = true;

  // DOM elements
  const leftContent = document.getElementById('left-content');
  const unvContent = document.getElementById('unv-content');
  const kjvContent = document.getElementById('kjv-content');
  const leftVerseRef = document.getElementById('left-verse-ref');

  // Toggle buttons
  const toggleUNV = document.getElementById('toggle-unv');
  const toggleKJV = document.getElementById('toggle-kjv');

  // Control groups
  const unvControls = document.querySelector('.unv-controls');
  const kjvControls = document.querySelector('.kjv-controls');

  // Checkboxes
  const unvSNDictCheckbox = document.getElementById('unv-sn-dict-toggle');
  const unvSingleHLCheckbox = document.getElementById('unv-single-hl-mode');
  const kjvSNDictCheckbox = document.getElementById('kjv-sn-dict-toggle');
  const kjvSingleHLCheckbox = document.getElementById('kjv-single-hl-mode');

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
        if (kjvActive && currentBook && currentChapter) {
          loadKJVData();
        }
        console.log(`[LeftPanel] KJV toggle: ${kjvActive ? 'ON' : 'OFF'}`);
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

    // Update control visibility
    if (unvControls) {
      unvControls.style.display = unvActive ? 'inline-flex' : 'none';
    }
    if (kjvControls) {
      kjvControls.style.display = kjvActive ? 'inline-flex' : 'none';
    }
  }

  /**
   * Load KJV data for current chapter
   */
  async function loadKJVData() {
    if (!currentBook || !currentChapter) return;

    console.log(`[LeftPanel] Loading KJV data for ${currentBook} ${currentChapter}`);

    try {
      const kjvData = await DataLoader.fetchKJVChapterFromAPI(currentBook, currentChapter);
      kjvChapterVerses = {};

      kjvData.forEach(verseObj => {
        const verseNum = verseObj.sec;
        kjvChapterVerses[verseNum] = {
          text: verseObj.bible_text || '',
          isUncertain: false
        };
      });

      renderKJVContent();
      console.log(`[LeftPanel] KJV data loaded: ${Object.keys(kjvChapterVerses).length} verses`);
    } catch (error) {
      console.error('[LeftPanel] Error loading KJV data:', error);
    }
  }

  /**
   * Handle chapter loaded event
   * @param {Object} data - {book, chapter, verseData}
   */
  function handleChapterLoaded(data) {
    const { book, chapter, verseData } = data;
    currentBook = book;
    currentChapter = chapter;
    chapterVerses = verseData;

    renderUNVContent();

    // Load KJV data if KJV is active
    if (kjvActive) {
      loadKJVData();
    }
  }

  /**
   * Render UNV chapter verses
   */
  function renderUNVContent() {
    if (!unvContent) return;

    if (Object.keys(chapterVerses).length === 0) {
      unvContent.innerHTML = '<div class="loading-message">無法載入章節資料</div>';
      return;
    }

    let html = '';
    const verseNumbers = Object.keys(chapterVerses).map(Number).sort((a, b) => a - b);

    verseNumbers.forEach(verseNum => {
      const data = chapterVerses[verseNum];
      const uncertainClass = data.isUncertain ? 'uncertain' : '';

      html += `
        <div class="verse ${uncertainClass}" data-verse="${verseNum}" data-version="unv">
          <span class="verse-num">${verseNum}</span>
          <span class="verse-text">${escapeHtml(data.text)}</span>
        </div>
      `;
    });

    unvContent.innerHTML = html;
    console.log(`[LeftPanel] Rendered ${verseNumbers.length} UNV verses`);
  }

  /**
   * Render KJV chapter verses
   */
  function renderKJVContent() {
    if (!kjvContent) return;

    if (Object.keys(kjvChapterVerses).length === 0) {
      kjvContent.innerHTML = '<div class="loading-message">Loading KJV...</div>';
      return;
    }

    let html = '';
    const verseNumbers = Object.keys(kjvChapterVerses).map(Number).sort((a, b) => a - b);

    verseNumbers.forEach(verseNum => {
      const data = kjvChapterVerses[verseNum];

      html += `
        <div class="verse" data-verse="${verseNum}" data-version="kjv">
          <span class="verse-num">${verseNum}</span>
          <span class="verse-text">${escapeHtml(data.text)}</span>
        </div>
      `;
    });

    kjvContent.innerHTML = html;
    console.log(`[LeftPanel] Rendered ${verseNumbers.length} KJV verses`);

    // Apply colors if we have a color map
    if (Object.keys(currentColorMap).length > 0) {
      applyColorsToKJV();
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

    const verse = parseInt(verseEl.dataset.verse);

    // If clicking SN on same verse, don't re-select (preserves highlighting)
    if (snTag && verse === currentVerse) {
      console.log(`[LeftPanel] SN click on same verse ${verse}, skipping re-select`);
      return;
    }

    console.log(`[LeftPanel] Verse ${verse} clicked (${version})${snTag ? ' (SN tag)' : ''}`);

    // Publish verse select event
    Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
      book: currentBook,
      chapter: currentChapter,
      verse: verse
    });
  }

  /**
   * Handle verse selected event (update UI only)
   * @param {Object} data - {book, chapter, verse}
   */
  function handleVerseSelected(data) {
    const { verse } = data;

    // Only clear SN highlighting when switching to a DIFFERENT verse
    const switchingVerses = verse !== currentVerse;
    currentVerse = verse;

    if (switchingVerses) {
      clearHighlighting();
    }

    // Update selection highlight for both UNV and KJV
    leftContent.querySelectorAll('.verse').forEach(el => {
      el.classList.remove('selected');
    });

    // Select verse in both versions
    const unvVerseEl = unvContent?.querySelector(`.verse[data-verse="${verse}"]`);
    const kjvVerseEl = kjvContent?.querySelector(`.verse[data-verse="${verse}"]`);

    if (unvVerseEl) {
      unvVerseEl.classList.add('selected');
      if (unvActive) {
        unvVerseEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    if (kjvVerseEl) {
      kjvVerseEl.classList.add('selected');
    }

    // Update verse reference display
    if (leftVerseRef) {
      leftVerseRef.textContent = `${currentBook} ${currentChapter}:${verse}`;
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
    if (kjvActive && Object.keys(kjvChapterVerses).length > 0) {
      applyColorsToKJV();
    }
  }

  /**
   * Apply colors to UNV content
   */
  function applyColorsToUNV() {
    if (!unvContent) return;

    unvContent.querySelectorAll('.verse').forEach(verseEl => {
      const verseNum = parseInt(verseEl.dataset.verse);
      const verseData = chapterVerses[verseNum];
      if (!verseData) return;

      const textEl = verseEl.querySelector('.verse-text');
      if (!textEl) return;

      // Apply colors to raw text
      const useGroups = (verseNum === currentVerse) ? currentGroups : undefined;
      const coloredHtml = ColorMapper.applyColorsToRawText(verseData.text, currentColorMap, useGroups);
      textEl.innerHTML = coloredHtml;

      // Add SN click handlers
      addSNClickHandlers(textEl, verseNum, 'unv');
    });
  }

  /**
   * Apply colors to KJV content
   */
  function applyColorsToKJV() {
    if (!kjvContent) return;

    kjvContent.querySelectorAll('.verse').forEach(verseEl => {
      const verseNum = parseInt(verseEl.dataset.verse);
      const verseData = kjvChapterVerses[verseNum];
      if (!verseData) return;

      const textEl = verseEl.querySelector('.verse-text');
      if (!textEl) return;

      // Apply colors to raw text (use groups for selected verse, same as UNV)
      const useGroups = (verseNum === currentVerse) ? currentGroups : undefined;
      const coloredHtml = ColorMapper.applyColorsToRawText(verseData.text, currentColorMap, useGroups);
      textEl.innerHTML = coloredHtml;

      // Add SN click handlers
      addSNClickHandlers(textEl, verseNum, 'kjv');
    });
  }

  /**
   * Add SN click handlers to a text element
   * @param {Element} textEl - The text element containing SN tags
   * @param {number} verseNum - Verse number
   * @param {string} version - 'unv' or 'kjv'
   */
  function addSNClickHandlers(textEl, verseNum, version) {
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
            verse: verseNum,
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
      chapter: currentChapter,
      verse: currentVerse
    };
  }

  /**
   * Get verse numbers array
   * @returns {number[]}
   */
  function getVerseNumbers() {
    return Object.keys(chapterVerses).map(Number).sort((a, b) => a - b);
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

    // Clear previous highlighting based on per-version settings
    if (unvActive && useUnvSingleHL) {
      clearHighlightingInContainer(unvContent);
    }
    if (kjvActive && useKjvSingleHL) {
      clearHighlightingInContainer(kjvContent);
    }

    // Apply highlighting to both active versions
    // Both UNV and KJV now use group-based coloring for the selected verse,
    // so color-based filtering works for both
    if (source === 'left') {
      // Clicked in left panel - highlight local (blue)
      if (unvActive) highlightInContainer(unvContent, groupSNs, verse, 'clicked-local', useUnvSingleHL);
      if (kjvActive) highlightInContainer(kjvContent, groupSNs, verse, 'clicked-local', useKjvSingleHL);
    } else {
      // Clicked in right panel - highlight remote (orange)
      if (unvActive) highlightInContainer(unvContent, groupSNs, verse, 'clicked-remote', useUnvSingleHL);
      if (kjvActive) highlightInContainer(kjvContent, groupSNs, verse, 'clicked-remote', useKjvSingleHL);
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
    currentBook = null;
    currentChapter = null;
    currentVerse = null;
    chapterVerses = {};
    kjvChapterVerses = {};
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
