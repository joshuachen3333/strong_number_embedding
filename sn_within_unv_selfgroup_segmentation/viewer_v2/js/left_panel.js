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

  const leftContent = document.getElementById('left-content');

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

    const verse = parseInt(verseEl.dataset.verse);
    console.log(`[LeftPanel] Verse ${verse} clicked`);

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
    currentVerse = verse;

    // Update selection highlight
    leftContent.querySelectorAll('.verse').forEach(el => {
      el.classList.remove('selected');
    });

    const verseEl = leftContent.querySelector(`.verse[data-verse="${verse}"]`);
    if (verseEl) {
      verseEl.classList.add('selected');
      // Scroll to selected verse
      verseEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  /**
   * Handle colors apply event
   * @param {Object} data - {colorMap}
   */
  function handleColorsApply(data) {
    const { colorMap } = data;

    leftContent.querySelectorAll('.verse').forEach(verseEl => {
      const verseNum = parseInt(verseEl.dataset.verse);
      const verseData = chapterVerses[verseNum];
      if (!verseData) return;

      const textEl = verseEl.querySelector('.verse-text');
      if (!textEl) return;

      // Apply colors to raw text
      const coloredHtml = ColorMapper.applyColorsToRawText(verseData.text, colorMap);
      textEl.innerHTML = coloredHtml;

      // Add SN click handlers
      textEl.querySelectorAll('.sn-tag').forEach(tag => {
        tag.addEventListener('click', (e) => {
          e.stopPropagation();
          const snCode = extractSNCode(tag.textContent);
          if (snCode) {
            Mediator.publish(Mediator.EVENT_TYPES.SN_CLICK, {
              element: tag,
              snCode: snCode
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
   * Clear left panel
   */
  function clear() {
    leftContent.innerHTML = '<div class="loading-message">請選擇書卷和章節...</div>';
    currentBook = null;
    currentChapter = null;
    currentVerse = null;
    chapterVerses = {};
  }

  // Public API
  return {
    init,
    getCurrentPosition,
    getVerseNumbers,
    clear
  };
})();
