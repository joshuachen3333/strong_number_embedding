/**
 * navigation.js
 * Keyboard navigation and URL hash management
 * v2.0: Context-aware hotkeys for left/right panel
 */

const Navigation = (() => {
  const LOCALSTORAGE_KEY = 'parsedViewerLastPosition';

  // Context-aware hotkey state
  let activePanel = 'left'; // 'left' | 'right'
  let selectedGroupIndex = -1; // Index of currently selected SN group in right panel (-1 = none)

  /**
   * Initialize keyboard navigation and panel detection
   */
  function initKeyboard() {
    // Set up keyboard listener
    document.addEventListener('keydown', (e) => {
      // Ignore if user is typing in an input/select
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
        return;
      }

      // Route to appropriate handler based on active panel
      if (activePanel === 'left') {
        handleLeftPanelKeys(e);
      } else {
        handleRightPanelKeys(e);
      }
    });

    // Set up panel hover detection
    initPanelDetection();
  }

  /**
   * Initialize panel detection (hover and click)
   */
  function initPanelDetection() {
    const leftPanel = document.querySelector('.left-panel');
    const rightPanel = document.querySelector('.right-panel');

    if (leftPanel) {
      leftPanel.addEventListener('mouseenter', () => {
        activePanel = 'left';
      });

      // Click on left panel also sets it active
      leftPanel.addEventListener('click', (e) => {
        if (e.target.closest('.verse') || e.target.closest('.sn-tag')) {
          activePanel = 'left';
          clearGroupSelection();
        }
      });
    }

    if (rightPanel) {
      rightPanel.addEventListener('mouseenter', () => {
        activePanel = 'right';
      });

      // Click on SN group in parsed section sets right panel active and selects that group
      rightPanel.addEventListener('click', (e) => {
        const snGroup = e.target.closest('.sn-group');
        if (snGroup) {
          activePanel = 'right';
          const groups = getSnGroups();
          const index = Array.from(groups).indexOf(snGroup);
          if (index >= 0) {
            selectGroup(index);
          }
        }
      });
    }
  }

  /**
   * Handle keyboard events when left panel is active (verse/chapter navigation)
   * @param {KeyboardEvent} e
   */
  function handleLeftPanelKeys(e) {
    switch (e.key) {
      case 'ArrowUp':
        e.preventDefault();
        navigatePreviousVerse();
        break;
      case 'ArrowDown':
        e.preventDefault();
        navigateNextVerse();
        break;
      case 'ArrowLeft':
        e.preventDefault();
        navigatePreviousChapter();
        break;
      case 'ArrowRight':
        e.preventDefault();
        navigateNextChapter();
        break;
      case 'Home':
        e.preventDefault();
        navigateFirstVerse();
        break;
      case 'End':
        e.preventDefault();
        navigateLastVerse();
        break;
    }
  }

  /**
   * Handle keyboard events when right panel is active (SN group navigation)
   * @param {KeyboardEvent} e
   */
  function handleRightPanelKeys(e) {
    const groups = getSnGroups();

    // If no groups available, fall back to left panel behavior
    if (groups.length === 0) {
      handleLeftPanelKeys(e);
      return;
    }

    switch (e.key) {
      case 'ArrowUp':
        e.preventDefault();
        navigatePreviousGroup();
        break;
      case 'ArrowDown':
        e.preventDefault();
        navigateNextGroup();
        break;
      case 'ArrowLeft':
        e.preventDefault();
        navigatePreviousVerse();
        break;
      case 'ArrowRight':
        e.preventDefault();
        navigateNextVerse();
        break;
      case 'Home':
        e.preventDefault();
        navigateFirstGroup();
        break;
      case 'End':
        e.preventDefault();
        navigateLastGroup();
        break;
    }
  }

  /**
   * Get all SN group elements from the parsed section (Section 1 only)
   * @returns {NodeListOf<Element>}
   */
  function getSnGroups() {
    // Only get groups from the first parsed-section (Parsed and Formatted Text Section)
    const parsedSection = document.querySelector('.parsed-section .parsed-content');
    if (!parsedSection) return document.querySelectorAll('.nonexistent'); // Empty NodeList
    return parsedSection.querySelectorAll('.sn-group');
  }

  /**
   * Navigate to previous SN group, or previous verse if at first group
   */
  function navigatePreviousGroup() {
    const groups = getSnGroups();
    if (groups.length === 0) return;

    // If no group selected, select the last one
    if (selectedGroupIndex < 0) {
      selectGroup(groups.length - 1);
      return;
    }

    if (selectedGroupIndex > 0) {
      selectGroup(selectedGroupIndex - 1);
    } else {
      // At first group, go to previous verse and select last group
      navigatePreviousVerse();
      // Wait for verse to load, then select last group
      setTimeout(() => {
        const newGroups = getSnGroups();
        if (newGroups.length > 0) {
          selectGroup(newGroups.length - 1);
        }
      }, 150);
    }
  }

  /**
   * Navigate to next SN group, or next verse if at last group
   */
  function navigateNextGroup() {
    const groups = getSnGroups();
    if (groups.length === 0) return;

    // If no group selected, select the first one
    if (selectedGroupIndex < 0) {
      selectGroup(0);
      return;
    }

    if (selectedGroupIndex < groups.length - 1) {
      selectGroup(selectedGroupIndex + 1);
    } else {
      // At last group, go to next verse and select first group
      navigateNextVerse();
      // Wait for verse to load, then select first group
      setTimeout(() => {
        selectGroup(0);
      }, 150);
    }
  }

  /**
   * Navigate to first SN group in current verse
   */
  function navigateFirstGroup() {
    selectGroup(0);
  }

  /**
   * Navigate to last SN group in current verse
   */
  function navigateLastGroup() {
    const groups = getSnGroups();
    if (groups.length > 0) {
      selectGroup(groups.length - 1);
    }
  }

  /**
   * Select an SN group by index and apply highlighting
   * @param {number} index
   */
  function selectGroup(index) {
    const groups = getSnGroups();
    if (index < 0 || index >= groups.length) return;

    // Clear previous selection
    clearGroupSelection();

    // Set new selection
    selectedGroupIndex = index;
    const group = groups[index];
    group.classList.add('keyboard-selected');

    // Scroll the group into view if needed
    group.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Trigger bidirectional highlighting
    triggerBidirectionalHighlight(group);
  }

  /**
   * Clear keyboard selection from all groups
   */
  function clearGroupSelection() {
    document.querySelectorAll('.sn-group.keyboard-selected').forEach(el => {
      el.classList.remove('keyboard-selected');
    });
  }

  /**
   * Trigger bidirectional highlighting for the selected SN group
   * @param {Element} groupElement
   */
  function triggerBidirectionalHighlight(groupElement) {
    // Extract SN codes from the group element
    const snCodes = extractSNsFromGroupElement(groupElement);

    // Use existing highlighting mechanism if available
    if (typeof LeftPanel !== 'undefined' && typeof LeftPanel.highlightSNs === 'function') {
      LeftPanel.highlightSNs(snCodes);
    }

    // Also simulate a click to trigger any existing click-based highlighting
    // This integrates with existing bidirectional highlighting feature
    groupElement.click();
  }

  /**
   * Extract SN codes from a group element
   * @param {Element} groupElement
   * @returns {string[]} Array of SN codes
   */
  function extractSNsFromGroupElement(groupElement) {
    const text = groupElement.textContent || '';
    const snPattern = /<(\d+)>|\((\*?\*?\d+)\)/g;
    const sns = [];
    let match;

    while ((match = snPattern.exec(text)) !== null) {
      const sn = match[1] || match[2];
      if (sn) {
        sns.push(sn.replace(/^\*+/, ''));
      }
    }

    return sns;
  }

  /**
   * Reset group selection (called when verse changes)
   */
  function resetGroupSelection() {
    selectedGroupIndex = -1;
    clearGroupSelection();
  }

  /**
   * Get current active panel
   * @returns {string} 'left' or 'right'
   */
  function getActivePanel() {
    return activePanel;
  }

  /**
   * Set active panel programmatically
   * @param {string} panel - 'left' or 'right'
   */
  function setActivePanel(panel) {
    if (panel === 'left' || panel === 'right') {
      activePanel = panel;
      if (panel === 'left') {
        clearGroupSelection();
      }
    }
  }

  /**
   * Navigate to previous verse (crosses chapter boundary)
   */
  function navigatePreviousVerse() {
    const pos = LeftPanel.getCurrentPosition();
    if (!pos.book || !pos.chapter || !pos.verse) return;

    const verses = LeftPanel.getVerseNumbers();
    const currentIndex = verses.indexOf(pos.verse);

    if (currentIndex > 0) {
      // Previous verse in same chapter
      LeftPanel.selectVerse(verses[currentIndex - 1]);
    } else {
      // Go to previous chapter
      const manifest = DataLoader.getManifest();
      if (!manifest || !manifest.books[pos.book]) return;

      const chapters = Object.keys(manifest.books[pos.book].chapters)
        .map(Number)
        .sort((a, b) => a - b);
      const chapterIndex = chapters.indexOf(pos.chapter);

      if (chapterIndex > 0) {
        // Load previous chapter and go to last verse
        const prevChapter = chapters[chapterIndex - 1];
        if (typeof App !== 'undefined' && App.loadChapter) {
          App.loadChapter(pos.book, prevChapter, 'last');
        }
      } else {
        // Go to previous book
        navigatePreviousBook(pos.book, 'last', 'last');
      }
    }
  }

  /**
   * Navigate to next verse (crosses chapter boundary)
   */
  function navigateNextVerse() {
    const pos = LeftPanel.getCurrentPosition();
    if (!pos.book || !pos.chapter || !pos.verse) return;

    const verses = LeftPanel.getVerseNumbers();
    const currentIndex = verses.indexOf(pos.verse);

    if (currentIndex < verses.length - 1) {
      // Next verse in same chapter
      LeftPanel.selectVerse(verses[currentIndex + 1]);
    } else {
      // Go to next chapter
      const manifest = DataLoader.getManifest();
      if (!manifest || !manifest.books[pos.book]) return;

      const chapters = Object.keys(manifest.books[pos.book].chapters)
        .map(Number)
        .sort((a, b) => a - b);
      const chapterIndex = chapters.indexOf(pos.chapter);

      if (chapterIndex < chapters.length - 1) {
        // Load next chapter and go to first verse
        const nextChapter = chapters[chapterIndex + 1];
        if (typeof App !== 'undefined' && App.loadChapter) {
          App.loadChapter(pos.book, nextChapter, 'first');
        }
      } else {
        // Go to next book
        navigateNextBook(pos.book, 'first', 'first');
      }
    }
  }

  /**
   * Navigate to previous chapter
   */
  function navigatePreviousChapter() {
    const pos = LeftPanel.getCurrentPosition();
    if (!pos.book || !pos.chapter) return;

    const chapters = DataLoader.getChapters(pos.book);
    const currentIndex = chapters.indexOf(pos.chapter);

    if (currentIndex > 0) {
      const prevChapter = chapters[currentIndex - 1];
      if (typeof App !== 'undefined' && App.loadChapter) {
        App.loadChapter(pos.book, prevChapter, 'first');
      }
    } else {
      // Go to previous book, last chapter
      navigatePreviousBook(pos.book, 'last', 'first');
    }
  }

  /**
   * Navigate to next chapter
   */
  function navigateNextChapter() {
    const pos = LeftPanel.getCurrentPosition();
    if (!pos.book || !pos.chapter) return;

    const chapters = DataLoader.getChapters(pos.book);
    const currentIndex = chapters.indexOf(pos.chapter);

    if (currentIndex < chapters.length - 1) {
      const nextChapter = chapters[currentIndex + 1];
      if (typeof App !== 'undefined' && App.loadChapter) {
        App.loadChapter(pos.book, nextChapter, 'first');
      }
    } else {
      // Go to next book, first chapter
      navigateNextBook(pos.book, 'first', 'first');
    }
  }

  /**
   * Navigate to first verse of current chapter
   */
  function navigateFirstVerse() {
    const verses = LeftPanel.getVerseNumbers();
    if (verses.length > 0) {
      LeftPanel.selectVerse(verses[0]);
    }
  }

  /**
   * Navigate to last verse of current chapter
   */
  function navigateLastVerse() {
    const verses = LeftPanel.getVerseNumbers();
    if (verses.length > 0) {
      LeftPanel.selectVerse(verses[verses.length - 1]);
    }
  }

  /**
   * Navigate to previous book
   * @param {string} currentBook - Current book abbreviation
   * @param {string} chapterPos - 'first' or 'last'
   * @param {string} versePos - 'first' or 'last'
   */
  function navigatePreviousBook(currentBook, chapterPos, versePos) {
    const currentIndex = BOOK_DATA.findIndex(b => b.eng === currentBook);
    if (currentIndex <= 0) return; // Already at first book

    // Find previous book with data
    for (let i = currentIndex - 1; i >= 0; i--) {
      const book = BOOK_DATA[i].eng;
      if (DataLoader.hasBookData(book)) {
        const chapters = DataLoader.getChapters(book);
        if (chapters.length > 0) {
          const chapter = chapterPos === 'last' ? chapters[chapters.length - 1] : chapters[0];
          if (typeof App !== 'undefined' && App.loadChapter) {
            App.loadChapter(book, chapter, versePos);
          }
          return;
        }
      }
    }
  }

  /**
   * Navigate to next book
   * @param {string} currentBook - Current book abbreviation
   * @param {string} chapterPos - 'first' or 'last'
   * @param {string} versePos - 'first' or 'last'
   */
  function navigateNextBook(currentBook, chapterPos, versePos) {
    const currentIndex = BOOK_DATA.findIndex(b => b.eng === currentBook);
    if (currentIndex < 0 || currentIndex >= BOOK_DATA.length - 1) return; // Already at last book

    // Find next book with data
    for (let i = currentIndex + 1; i < BOOK_DATA.length; i++) {
      const book = BOOK_DATA[i].eng;
      if (DataLoader.hasBookData(book)) {
        const chapters = DataLoader.getChapters(book);
        if (chapters.length > 0) {
          const chapter = chapterPos === 'last' ? chapters[chapters.length - 1] : chapters[0];
          if (typeof App !== 'undefined' && App.loadChapter) {
            App.loadChapter(book, chapter, versePos);
          }
          return;
        }
      }
    }
  }

  /**
   * Update URL hash
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @param {number} verse - Verse number
   */
  function updateHash(book, chapter, verse) {
    if (!book || !chapter || !verse) return;
    window.location.hash = `#${book}/${chapter}/${verse}`;
  }

  /**
   * Parse URL hash
   * @returns {Object|null} { book, chapter, verse } or null
   */
  function parseHash() {
    const hash = window.location.hash.substring(1); // Remove #
    if (!hash) return null;

    const parts = hash.split('/');
    if (parts.length !== 3) return null;

    return {
      book: parts[0],
      chapter: parseInt(parts[1]),
      verse: parseInt(parts[2])
    };
  }

  /**
   * Save position to localStorage
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @param {number} verse - Verse number
   */
  function savePosition(book, chapter, verse) {
    if (!book || !chapter || !verse) return;

    const position = { book, chapter, verse };
    localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(position));
  }

  /**
   * Load position from localStorage
   * @returns {Object|null} { book, chapter, verse } or null
   */
  function loadPosition() {
    try {
      const stored = localStorage.getItem(LOCALSTORAGE_KEY);
      if (!stored) return null;
      return JSON.parse(stored);
    } catch (error) {
      console.error('Error loading position from localStorage:', error);
      return null;
    }
  }

  /**
   * Get initial position (from hash or localStorage)
   * @returns {Object} { book, chapter, verse }
   */
  function getInitialPosition() {
    // Try hash first
    const hashPos = parseHash();
    if (hashPos) return hashPos;

    // Try localStorage
    const storedPos = loadPosition();
    if (storedPos) return storedPos;

    // Default to Gen 1:1
    return { book: 'Gen', chapter: 1, verse: 1 };
  }

  // Public API
  return {
    initKeyboard,
    updateHash,
    parseHash,
    savePosition,
    loadPosition,
    getInitialPosition,
    navigatePreviousVerse,
    navigateNextVerse,
    navigatePreviousChapter,
    navigateNextChapter,
    // New context-aware hotkey API
    getActivePanel,
    setActivePanel,
    resetGroupSelection,
    selectGroup,
    getSnGroups
  };
})();
