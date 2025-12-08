/**
 * navigation.js
 * Keyboard navigation, URL hash, and localStorage with event-driven architecture
 */

const Navigation = (() => {
  const LOCALSTORAGE_KEY = 'parsedViewerLastPosition';

  /**
   * Initialize navigation (keyboard, hash, localStorage)
   */
  function init() {
    // Initialize keyboard
    initKeyboard();

    // Subscribe to verse selected event for hash/storage updates
    Mediator.subscribe(Mediator.EVENT_TYPES.VERSE_SELECTED, handleVerseSelected);
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
    });
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
    loadPosition
  };
})();
