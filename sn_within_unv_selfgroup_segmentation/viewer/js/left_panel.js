/**
 * left_panel.js
 * Left panel (UNV Reader) logic
 */

const LeftPanel = (() => {
  let currentBook = null;
  let currentChapter = null;
  let currentVerse = null;
  let chapterVerses = {};
  let snToColorMap = {};

  const leftContent = document.getElementById('left-content');

  /**
   * Render chapter verses in left panel
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @param {Object} verseData - Map of verse number → verse data
   */
  function renderChapter(book, chapter, verseData) {
    currentBook = book;
    currentChapter = chapter;
    chapterVerses = verseData;

    if (Object.keys(verseData).length === 0) {
      leftContent.innerHTML = '<div class="loading-message">無法載入章節資料</div>';
      return;
    }

    let html = '';
    const verseNumbers = Object.keys(verseData).map(Number).sort((a, b) => a - b);

    verseNumbers.forEach(verseNum => {
      const data = verseData[verseNum];
      const uncertainClass = data.isUncertain ? 'uncertain' : '';

      html += `
        <div class="verse ${uncertainClass}" data-verse="${verseNum}">
          <span class="verse-num">${verseNum}</span>
          <span class="verse-text">${escapeHtml(data.text)}</span>
        </div>
      `;
    });

    leftContent.innerHTML = html;

    // Add click handlers
    leftContent.querySelectorAll('.verse').forEach(verseEl => {
      verseEl.addEventListener('click', () => {
        const verse = parseInt(verseEl.dataset.verse);
        selectVerse(verse);
      });
    });
  }

  /**
   * Select a verse
   * @param {number} verse - Verse number
   */
  function selectVerse(verse) {
    currentVerse = verse;

    // Update UI selection
    leftContent.querySelectorAll('.verse').forEach(el => {
      el.classList.remove('selected');
    });

    const verseEl = leftContent.querySelector(`.verse[data-verse="${verse}"]`);
    if (verseEl) {
      verseEl.classList.add('selected');
      // Scroll to selected verse
      verseEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    // Notify app to load right panel
    if (typeof App !== 'undefined' && App.onVerseSelected) {
      App.onVerseSelected(currentBook, currentChapter, verse);
    }
  }

  /**
   * Apply color coding to left panel based on SN-to-color map
   * @param {Object} colorMap - Map from SN code to color
   */
  function applyColors(colorMap) {
    snToColorMap = colorMap;

    leftContent.querySelectorAll('.verse').forEach(verseEl => {
      const verseNum = parseInt(verseEl.dataset.verse);
      const data = chapterVerses[verseNum];
      if (!data) return;

      const textEl = verseEl.querySelector('.verse-text');
      if (!textEl) return;

      // Apply colors to raw text
      const coloredHtml = ColorMapper.applyColorsToRawText(data.text, colorMap);
      textEl.innerHTML = coloredHtml;

      // Add click handlers to SN tags for bidirectional highlighting
      textEl.querySelectorAll('.sn-tag').forEach(snTag => {
        snTag.addEventListener('click', (e) => {
          e.stopPropagation();
          handleSnTagClick(snTag);
        });
      });
    });
  }

  /**
   * Handle SN tag click - trigger bidirectional highlighting
   * @param {Element} snTag - The clicked SN tag element
   */
  function handleSnTagClick(snTag) {
    // Clear all previous highlights
    clearHighlighting();

    // Get SN codes from clicked element
    const snCodes = extractSNsFromElement(snTag);
    if (snCodes.length === 0) return;

    // Apply local highlight (blue) to clicked element
    snTag.classList.add('sn-highlight-local');

    // Trigger remote highlighting in right panel
    if (typeof RightPanel !== 'undefined' && RightPanel.highlightRemote) {
      RightPanel.highlightRemote(snCodes);
    }
  }

  /**
   * Extract SN codes from an element's text content
   * @param {Element} element
   * @returns {string[]} Array of SN codes
   */
  function extractSNsFromElement(element) {
    const text = element.textContent || '';
    const snPattern = /<W[ATH]*H?(\d+)>|\{<W[ATH]*H?(\d+)>\}/g;
    const sns = [];
    let match;

    while ((match = snPattern.exec(text)) !== null) {
      const sn = match[1] || match[2];
      if (sn) sns.push(sn);
    }

    return sns;
  }

  /**
   * Clear all SN highlighting in left panel
   */
  function clearHighlighting() {
    leftContent.querySelectorAll('.sn-highlight-local, .sn-highlight-remote').forEach(el => {
      el.classList.remove('sn-highlight-local', 'sn-highlight-remote');
    });
  }

  /**
   * Apply remote highlighting (orange) to elements matching SN codes
   * Uses consecutive sequence matching to avoid highlighting wrong occurrences
   * @param {string[]} snCodes - Array of SN codes to highlight
   */
  function highlightRemote(snCodes) {
    if (!snCodes || snCodes.length === 0) return;

    // Only highlight in current selected verse
    const selectedVerse = leftContent.querySelector('.verse.selected');
    if (!selectedVerse) return;

    const snTags = Array.from(selectedVerse.querySelectorAll('.sn-tag'));
    if (snTags.length === 0) return;

    // For multiple SNs, find consecutive sequence matching all SNs in order
    if (snCodes.length > 1) {
      for (let i = 0; i <= snTags.length - snCodes.length; i++) {
        let matches = true;
        for (let j = 0; j < snCodes.length; j++) {
          const tagSNs = extractSNsFromElement(snTags[i + j]);
          if (!tagSNs.includes(snCodes[j])) {
            matches = false;
            break;
          }
        }
        if (matches) {
          // Found a matching sequence, highlight it
          for (let j = 0; j < snCodes.length; j++) {
            snTags[i + j].classList.add('sn-highlight-remote');
          }
          return; // Only highlight the first matching sequence
        }
      }
    } else {
      // For single SN, highlight all matches (fallback behavior)
      snTags.forEach(snTag => {
        const tagSNs = extractSNsFromElement(snTag);
        if (tagSNs.includes(snCodes[0])) {
          snTag.classList.add('sn-highlight-remote');
        }
      });
    }
  }

  /**
   * Get current position
   * @returns {Object} { book, chapter, verse }
   */
  function getCurrentPosition() {
    return {
      book: currentBook,
      chapter: currentChapter,
      verse: currentVerse
    };
  }

  /**
   * Get total verses in current chapter
   * @returns {number}
   */
  function getTotalVerses() {
    return Object.keys(chapterVerses).length;
  }

  /**
   * Get verse numbers array (sorted)
   * @returns {number[]}
   */
  function getVerseNumbers() {
    return Object.keys(chapterVerses).map(Number).sort((a, b) => a - b);
  }

  /**
   * Escape HTML special characters
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
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
    snToColorMap = {};
  }

  // Public API
  return {
    renderChapter,
    selectVerse,
    applyColors,
    getCurrentPosition,
    getTotalVerses,
    getVerseNumbers,
    clear,
    highlightRemote,
    clearHighlighting
  };
})();
