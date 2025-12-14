/**
 * left_panel.js
 * Left panel (UNV Reader) with event-driven architecture
 */

const LeftPanel = (() => {
  let currentBook = null;
  let currentChapter = null;
  let currentVerse = null;
  let chapterVerses = {};
  let clickHandlerAttached = false;
  let currentColorMap = {};
  let currentGroups = [];
  let singleHighlightMode = true; // Single highlight mode: true = clear previous, false = multi-highlight

  const leftContent = document.getElementById('left-content');
  const singleHighlightCheckbox = document.getElementById('single-highlight-mode');
  const leftVerseRef = document.getElementById('left-verse-ref');

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

    // Initialize Single Highlight mode checkbox
    if (singleHighlightCheckbox) {
      singleHighlightMode = singleHighlightCheckbox.checked;
      console.log(`[LeftPanel] Single HL checkbox initialized: ${singleHighlightMode ? 'ON (checked)' : 'OFF (unchecked)'}`);
      singleHighlightCheckbox.addEventListener('change', (e) => {
        singleHighlightMode = e.target.checked;
        console.log(`[LeftPanel] Single highlight mode: ${singleHighlightMode ? 'ON' : 'OFF'}`);
      });
    } else {
      console.warn('[LeftPanel] Single HL checkbox not found!');
    }

    // Add click handler once (event delegation)
    if (!clickHandlerAttached) {
      leftContent.addEventListener('click', handleVerseClick);
      clickHandlerAttached = true;
      console.log('[LeftPanel] Click handler attached');
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

    renderChapter();
  }

  /**
   * Render chapter verses
   */
  function renderChapter() {
    if (Object.keys(chapterVerses).length === 0) {
      leftContent.innerHTML = '<div class="loading-message">無法載入章節資料</div>';
      return;
    }

    let html = '';
    const verseNumbers = Object.keys(chapterVerses).map(Number).sort((a, b) => a - b);

    verseNumbers.forEach(verseNum => {
      const data = chapterVerses[verseNum];
      const uncertainClass = data.isUncertain ? 'uncertain' : '';

      html += `
        <div class="verse ${uncertainClass}" data-verse="${verseNum}">
          <span class="verse-num">${verseNum}</span>
          <span class="verse-text">${escapeHtml(data.text)}</span>
        </div>
      `;
    });

    leftContent.innerHTML = html;
    console.log(`[LeftPanel] Rendered ${verseNumbers.length} verses`);
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

    console.log(`[LeftPanel] Verse ${verse} clicked${snTag ? ' (SN tag)' : ''}`);

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
    // (clicking SN on same verse should preserve highlighting)
    const switchingVerses = verse !== currentVerse;
    currentVerse = verse;

    if (switchingVerses) {
      clearHighlighting();
    }

    // Update selection highlight
    leftContent.querySelectorAll('.verse').forEach(el => {
      el.classList.remove('selected');
    });

    const verseEl = leftContent.querySelector(`.verse[data-verse="${verse}"]`);
    if (verseEl) {
      verseEl.classList.add('selected');
      // Scroll to selected verse
      verseEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

    leftContent.querySelectorAll('.verse').forEach(verseEl => {
      const verseNum = parseInt(verseEl.dataset.verse);
      const verseData = chapterVerses[verseNum];
      if (!verseData) return;

      const textEl = verseEl.querySelector('.verse-text');
      if (!textEl) return;

      // Apply colors to raw text
      // Use position-based coloring only for the currently selected verse
      // For other verses, fall back to SN-based coloring
      const useGroups = (verseNum === currentVerse) ? groups : undefined;
      const coloredHtml = ColorMapper.applyColorsToRawText(verseData.text, colorMap, useGroups);
      textEl.innerHTML = coloredHtml;

      // Add SN click handlers
      textEl.querySelectorAll('.sn-tag').forEach(tag => {
        tag.addEventListener('click', (e) => {
          // Don't stop propagation - let event bubble up to verse element
          // so handleVerseClick() can auto-select the verse
          const snCode = extractSNCode(tag.textContent);
          if (snCode) {
            // Get all SNs in the same group - pass the clicked element for position-based matching
            const groupSNs = ColorMapper.getSNGroupFromColorMap(snCode, currentColorMap, currentGroups, tag);

            Mediator.publish(Mediator.EVENT_TYPES.SN_CLICK, {
              source: 'left',
              element: tag,
              snCode: snCode,
              groupSNs: groupSNs,
              verse: verseNum  // Add verse number for single-HL filtering
            });
          }
        });
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
   * @param {Object} event - {source, snCode, groupSNs, element, verse}
   */
  function handleSNClickForHighlighting(event) {
    const { source, groupSNs, verse } = event;

    console.log(`[LeftPanel] SN click - singleHighlightMode=${singleHighlightMode}, source=${source}, verse=${verse}`);

    // Only clear previous highlighting if single highlight mode is ON
    if (singleHighlightMode) {
      console.log('[LeftPanel] Clearing previous highlights (Single HL is ON)');
      clearHighlighting();
    } else {
      console.log('[LeftPanel] Keeping previous highlights (Single HL is OFF)');
    }

    if (source === 'left') {
      // Clicked in left panel - highlight local (blue)
      highlightLocal(groupSNs, verse);
    } else {
      // Clicked in right panel - highlight remote (orange)
      highlightRemote(groupSNs, verse);
    }
  }

  /**
   * Clear all highlighting classes
   */
  function clearHighlighting() {
    leftContent.querySelectorAll('.clicked-local, .clicked-remote').forEach(el => {
      el.classList.remove('clicked-local', 'clicked-remote');
    });
  }

  /**
   * Highlight local SNs (blue) - for clicks originating in left panel
   * @param {string[]} groupSNs - Array of SN codes to highlight
   * @param {number} verse - Verse number to limit highlighting (when Single HL mode is ON)
   */
  function highlightLocal(groupSNs, verse) {
    let container = leftContent;

    // If single HL mode is ON and verse is specified, limit to that verse
    if (singleHighlightMode && verse) {
      container = leftContent.querySelector(`.verse[data-verse="${verse}"]`);
      if (!container) {
        console.warn(`[LeftPanel] Verse ${verse} not found for highlighting`);
        return;
      }
      console.log(`[LeftPanel] Single HL ON - limiting highlight to verse ${verse}`);
    } else {
      console.log('[LeftPanel] Multi HL mode - highlighting across all verses');
    }

    const elements = ColorMapper.findCorrespondingElements(groupSNs, container, '.sn-tag', currentGroups);
    console.log(`[LeftPanel] Found ${elements.length} elements to highlight (local/blue)`);
    elements.forEach(el => el.classList.add('clicked-local'));
  }

  /**
   * Highlight remote SNs (orange) - for clicks originating in right panel
   * @param {string[]} groupSNs - Array of SN codes to highlight
   * @param {number} verse - Verse number to limit highlighting (when Single HL mode is ON)
   */
  function highlightRemote(groupSNs, verse) {
    let container = leftContent;

    // If single HL mode is ON and verse is specified, limit to that verse
    if (singleHighlightMode && verse) {
      container = leftContent.querySelector(`.verse[data-verse="${verse}"]`);
      if (!container) {
        console.warn(`[LeftPanel] Verse ${verse} not found for highlighting`);
        return;
      }
      console.log(`[LeftPanel] Single HL ON - limiting highlight to verse ${verse}`);
    } else {
      console.log('[LeftPanel] Multi HL mode - highlighting across all verses');
    }

    const elements = ColorMapper.findCorrespondingElements(groupSNs, container, '.sn-tag', currentGroups);
    console.log(`[LeftPanel] Found ${elements.length} elements to highlight (remote/orange)`);
    elements.forEach(el => el.classList.add('clicked-remote'));
  }

  /**
   * Clear left panel
   */
  function clear() {
    leftContent.innerHTML = '<div class="loading-message">請選擇書卷和章節...</div>';
    currentBook = null;
    currentChapter = null;
    currentVerse = null;
    chapterVerses = {};
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
    clear
  };
})();
