/**
 * navigation.js
 * Keyboard navigation, URL hash, and localStorage with event-driven architecture
 * v2.0: Context-aware hotkeys for left/right panel
 */

const Navigation = (() => {
  const LOCALSTORAGE_KEY = 'parsedViewerLastPosition';

  // Context-aware hotkey state
  let activePanel = 'left'; // 'left' | 'right'
  let selectedGroupIndex = -1; // Index of currently selected SN group in right panel (-1 = none)

  /**
   * Initialize navigation (keyboard, hash, localStorage)
   */
  function init() {
    // Initialize keyboard
    initKeyboard();

    // Initialize panel detection (hover and click)
    initPanelDetection();

    // Subscribe to verse selected event for hash/storage updates
    Mediator.subscribe(Mediator.EVENT_TYPES.VERSE_SELECTED, handleVerseSelected);
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
        console.log('[Navigation] Active panel: left (hover)');
      });

      // Click on left panel also sets it active
      leftPanel.addEventListener('click', (e) => {
        if (e.target.closest('.verse') || e.target.closest('.sn-tag')) {
          activePanel = 'left';
          clearGroupSelection();
          console.log('[Navigation] Active panel: left (click)');
        }
      });
    }

    if (rightPanel) {
      rightPanel.addEventListener('mouseenter', () => {
        activePanel = 'right';
        console.log('[Navigation] Active panel: right (hover)');
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
          console.log('[Navigation] Active panel: right (click on group)');
        }
      });
    }

    console.log('[Navigation] Panel detection initialized');
  }

  /**
   * Initialize keyboard navigation
   */
  function initKeyboard() {
    document.addEventListener('keydown', (e) => {
      // Ignore if typing in input/select
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

    // Trigger bidirectional highlighting via click simulation
    // This integrates with existing SN_CLICK event system
    group.click();

    console.log(`[Navigation] Selected group ${index}`);
  }

  /**
   * Clear keyboard selection from all groups
   */
  function clearGroupSelection() {
    document.querySelectorAll('.sn-group.keyboard-selected').forEach(el => {
      el.classList.remove('keyboard-selected');
    });
    selectedGroupIndex = -1;
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
   * Navigate to previous verse
   */
  function navigatePreviousVerse() {
    const pos = LeftPanel.getCurrentPosition();
    if (!pos.book || !pos.chapter || !pos.verse) return;

    const verses = LeftPanel.getVerseNumbers();
    const currentIndex = verses.indexOf(pos.verse);

    if (currentIndex > 0) {
      // Previous verse in same chapter
      Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
        book: pos.book,
        chapter: pos.chapter,
        verse: verses[currentIndex - 1]
      });
    } else {
      // Go to previous chapter
      const manifest = DataLoader.getManifest();
      if (!manifest || !manifest.books[pos.book]) return;

      const chapters = Object.keys(manifest.books[pos.book].chapters)
        .map(Number)
        .sort((a, b) => a - b);
      const chapterIndex = chapters.indexOf(pos.chapter);

      if (chapterIndex > 0) {
        // Load previous chapter, last verse
        Mediator.publish(Mediator.EVENT_TYPES.CHAPTER_LOAD, {
          book: pos.book,
          chapter: chapters[chapterIndex - 1],
          versePosition: 'last'
        });
      } else {
        // Go to previous book
        navigatePreviousBook(pos.book, 'last', 'last');
      }
    }
  }

  /**
   * Navigate to next verse
   */
  function navigateNextVerse() {
    const pos = LeftPanel.getCurrentPosition();
    if (!pos.book || !pos.chapter || !pos.verse) return;

    const verses = LeftPanel.getVerseNumbers();
    const currentIndex = verses.indexOf(pos.verse);

    if (currentIndex < verses.length - 1) {
      // Next verse in same chapter
      Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
        book: pos.book,
        chapter: pos.chapter,
        verse: verses[currentIndex + 1]
      });
    } else {
      // Go to next chapter
      const manifest = DataLoader.getManifest();
      if (!manifest || !manifest.books[pos.book]) return;

      const chapters = Object.keys(manifest.books[pos.book].chapters)
        .map(Number)
        .sort((a, b) => a - b);
      const chapterIndex = chapters.indexOf(pos.chapter);

      if (chapterIndex < chapters.length - 1) {
        // Load next chapter, first verse
        Mediator.publish(Mediator.EVENT_TYPES.CHAPTER_LOAD, {
          book: pos.book,
          chapter: chapters[chapterIndex + 1],
          versePosition: 'first'
        });
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
      Mediator.publish(Mediator.EVENT_TYPES.CHAPTER_LOAD, {
        book: pos.book,
        chapter: chapters[currentIndex - 1],
        versePosition: 'first'
      });
    } else {
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
      Mediator.publish(Mediator.EVENT_TYPES.CHAPTER_LOAD, {
        book: pos.book,
        chapter: chapters[currentIndex + 1],
        versePosition: 'first'
      });
    } else {
      navigateNextBook(pos.book, 'first', 'first');
    }
  }

  /**
   * Navigate to first verse
   */
  function navigateFirstVerse() {
    const pos = LeftPanel.getCurrentPosition();
    const verses = LeftPanel.getVerseNumbers();
    if (verses.length > 0) {
      Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
        book: pos.book,
        chapter: pos.chapter,
        verse: verses[0]
      });
    }
  }

  /**
   * Navigate to last verse
   */
  function navigateLastVerse() {
    const pos = LeftPanel.getCurrentPosition();
    const verses = LeftPanel.getVerseNumbers();
    if (verses.length > 0) {
      Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
        book: pos.book,
        chapter: pos.chapter,
        verse: verses[verses.length - 1]
      });
    }
  }

  /**
   * Navigate to previous book
   * @param {string} currentBook
   * @param {string} chapterPos - 'first' or 'last'
   * @param {string} versePos - 'first' or 'last'
   */
  function navigatePreviousBook(currentBook, chapterPos, versePos) {
    const currentIndex = BOOK_DATA.findIndex(b => b.eng === currentBook);
    if (currentIndex <= 0) return;

    for (let i = currentIndex - 1; i >= 0; i--) {
      const book = BOOK_DATA[i].eng;
      if (DataLoader.hasBookData(book)) {
        const chapters = DataLoader.getChapters(book);
        if (chapters.length > 0) {
          const chapter = chapterPos === 'last' ? chapters[chapters.length - 1] : chapters[0];
          Mediator.publish(Mediator.EVENT_TYPES.CHAPTER_LOAD, {
            book,
            chapter,
            versePosition: versePos
          });
          return;
        }
      }
    }
  }

  /**
   * Navigate to next book
   * @param {string} currentBook
   * @param {string} chapterPos
   * @param {string} versePos
   */
  function navigateNextBook(currentBook, chapterPos, versePos) {
    const currentIndex = BOOK_DATA.findIndex(b => b.eng === currentBook);
    if (currentIndex < 0 || currentIndex >= BOOK_DATA.length - 1) return;

    for (let i = currentIndex + 1; i < BOOK_DATA.length; i++) {
      const book = BOOK_DATA[i].eng;
      if (DataLoader.hasBookData(book)) {
        const chapters = DataLoader.getChapters(book);
        if (chapters.length > 0) {
          const chapter = chapterPos === 'last' ? chapters[chapters.length - 1] : chapters[0];
          Mediator.publish(Mediator.EVENT_TYPES.CHAPTER_LOAD, {
            book,
            chapter,
            versePosition: versePos
          });
          return;
        }
      }
    }
  }

  /**
   * Handle verse selected event (update hash and localStorage)
   * @param {Object} data - {book, chapter, verse}
   */
  function handleVerseSelected(data) {
    const { book, chapter, verse } = data;

    // Update URL hash
    updateHash(book, chapter, verse);

    // Save to localStorage
    savePosition(book, chapter, verse);
  }

  /**
   * Update URL hash
   * @param {string} book
   * @param {number} chapter
   * @param {number} verse
   */
  function updateHash(book, chapter, verse) {
    if (!book || !chapter || !verse) return;
    window.location.hash = `#${book}/${chapter}/${verse}`;
  }

  /**
   * Parse URL hash
   * @returns {Object|null} {book, chapter, verse}
   */
  function parseHash() {
    const hash = window.location.hash.substring(1);
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
   * @param {string} book
   * @param {number} chapter
   * @param {number} verse
   */
  function savePosition(book, chapter, verse) {
    if (!book || !chapter || !verse) return;

    const position = { book, chapter, verse };
    localStorage.setItem(LOCALSTORAGE_KEY, JSON.stringify(position));
  }

  /**
   * Load position from localStorage
   * @returns {Object|null}
   */
  function loadPosition() {
    try {
      const stored = localStorage.getItem(LOCALSTORAGE_KEY);
      if (!stored) return null;
      return JSON.parse(stored);
    } catch (error) {
      console.error('Error loading position:', error);
      return null;
    }
  }

  /**
   * Get initial position (hash → localStorage → default)
   * @returns {Object} {book, chapter, verse}
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
    init,
    getInitialPosition,
    updateHash,
    parseHash,
    savePosition,
    loadPosition,
    // Context-aware hotkey API
    getActivePanel,
    setActivePanel,
    resetGroupSelection,
    selectGroup,
    getSnGroups
  };
})();
