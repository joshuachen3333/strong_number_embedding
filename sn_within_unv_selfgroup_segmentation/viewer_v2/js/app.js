/**
 * app.js
 * Main application controller - orchestrates all components via Mediator
 */

const App = (() => {
  const bookSelect = document.getElementById('book-select');
  const chapterSelect = document.getElementById('chapter-select');

  let manifest = null;
  let currentBook = null;
  let currentChapter = null;

  /**
   * Initialize application
   */
  async function init() {
    console.log('[App] Initializing Parsed Verse Viewer v2...');

    // Initialize all modules
    LeftPanel.init();
    RightPanel.init();
    Navigation.init();
    SNDictionary.init();

    // Subscribe to events
    subscribeToEvents();

    // Set up dropdown handlers
    bookSelect.addEventListener('change', onBookChange);
    chapterSelect.addEventListener('change', onChapterChange);

    // Global click handler to clear highlighting
    document.addEventListener('click', handleGlobalClick);

    // Load manifest
    manifest = await DataLoader.loadManifest();
    if (!manifest || Object.keys(manifest.books).length === 0) {
      UIUtils.showError('無法載入清單檔案，請確認 manifest.json 存在', 'banner');
      return;
    }

    console.log('[App] Manifest loaded:', Object.keys(manifest.books).length, 'books');

    // Populate book dropdown
    populateBookDropdown();

    // Get initial position
    const initialPos = Navigation.getInitialPosition();
    console.log('[App] Initial position:', initialPos);

    // Load initial position
    if (initialPos && initialPos.book) {
      await loadInitialPosition(initialPos);
    }

    console.log('[App] Initialization complete');
  }

  /**
   * Subscribe to mediator events
   */
  function subscribeToEvents() {
    // Subscribe to verse select
    Mediator.subscribe(Mediator.EVENT_TYPES.VERSE_SELECT, handleVerseSelect);

    // Subscribe to chapter load
    Mediator.subscribe(Mediator.EVENT_TYPES.CHAPTER_LOAD, handleChapterLoad);

    // Subscribe to error show
    Mediator.subscribe(Mediator.EVENT_TYPES.ERROR_SHOW, handleErrorShow);

    // Subscribe to loading events for spinner display
    Mediator.subscribe(Mediator.EVENT_TYPES.LOADING_START, handleLoadingStart);
    Mediator.subscribe(Mediator.EVENT_TYPES.LOADING_END, handleLoadingEnd);
  }

  /**
   * Handle verse select event
   * @param {Object} data - {book, chapter, verse}
   */
  async function handleVerseSelect(data) {
    const { book, chapter, verse } = data;
    console.log(`[App] Verse select: ${book} ${chapter}:${verse}`);

    // Load parsed output
    const result = await DataLoader.loadParsedVerse(book, chapter, verse);
    console.log(`[App] Parsed verse result:`, result);

    // Publish verse selected event with full data
    Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECTED, {
      book,
      chapter,
      verse,
      content: result.content,
      isUncertain: result.isUncertain,
      exists: result.exists
    });
    console.log(`[App] Published VERSE_SELECTED event`);
  }

  /**
   * Handle chapter load event
   * @param {Object} data - {book, chapter, versePosition}
   */
  async function handleChapterLoad(data) {
    const { book, chapter, versePosition } = data;
    console.log(`[App] Chapter load: ${book} ${chapter}, verse: ${versePosition}`);

    await loadChapter(book, chapter, versePosition);
  }

  /**
   * Handle error show event
   * @param {Object} data - {message, type}
   */
  function handleErrorShow(data) {
    const { message, type } = data;
    UIUtils.showError(message, type);
  }

  /**
   * Handle loading start event
   * @param {Object} data - {context}
   */
  function handleLoadingStart(data) {
    const { context } = data;

    if (context === 'chapter') {
      UIUtils.showSpinner('#left-content', '載入章節...');
    } else if (context === 'verse') {
      UIUtils.showSpinner('#right-content', '載入經文...');
    }
  }

  /**
   * Handle loading end event
   * @param {Object} data - {context}
   */
  function handleLoadingEnd(data) {
    const { context } = data;

    if (context === 'chapter') {
      UIUtils.hideSpinner('#left-content');
    } else if (context === 'verse') {
      UIUtils.hideSpinner('#right-content');
    }
  }

  /**
   * Populate book dropdown
   */
  function populateBookDropdown() {
    bookSelect.innerHTML = '<option value="">選擇書卷...</option>';

    BOOK_DATA.forEach(book => {
      const option = document.createElement('option');
      option.value = book.eng;

      const hasData = DataLoader.hasBookData(book.eng);
      option.textContent = `${book.chiLong} (${book.engLong})`;

      if (!hasData) {
        option.disabled = true;
        option.textContent += ' [無資料]';
      }

      bookSelect.appendChild(option);
    });
  }

  /**
   * Populate chapter dropdown
   * @param {string} book
   */
  function populateChapterDropdown(book) {
    chapterSelect.innerHTML = '<option value="">選擇章...</option>';

    const chapters = DataLoader.getChapters(book);

    chapters.forEach(chapter => {
      const option = document.createElement('option');
      option.value = chapter;
      option.textContent = `第 ${chapter} 章`;
      chapterSelect.appendChild(option);
    });

    if (chapters.length === 0) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = '（無可用章節）';
      option.disabled = true;
      chapterSelect.appendChild(option);
    }
  }

  /**
   * Handle book dropdown change
   */
  function onBookChange() {
    const book = bookSelect.value;
    if (!book) {
      chapterSelect.innerHTML = '<option value="">選擇章...</option>';
      LeftPanel.clear();
      RightPanel.clear();
      return;
    }

    currentBook = book;
    populateChapterDropdown(book);

    // Auto-select first chapter
    const chapters = DataLoader.getChapters(book);
    if (chapters.length > 0) {
      chapterSelect.value = chapters[0];
      onChapterChange();
    }
  }

  /**
   * Handle chapter dropdown change
   */
  async function onChapterChange() {
    const chapter = parseInt(chapterSelect.value);
    if (!chapter || !currentBook) return;

    currentChapter = chapter;
    await loadChapter(currentBook, chapter, 'first');
  }

  /**
   * Load initial position
   * @param {Object} pos - {book, chapter, verse}
   */
  async function loadInitialPosition(pos) {
    const { book, chapter, verse } = pos;

    // Set dropdowns
    bookSelect.value = book;
    currentBook = book;
    populateChapterDropdown(book);

    chapterSelect.value = chapter;
    currentChapter = chapter;

    // Load chapter and verse
    await loadChapter(book, chapter, verse);
  }

  /**
   * Load a chapter
   * @param {string} book
   * @param {number} chapter
   * @param {number|string} versePosition - verse number or 'first'/'last'
   */
  async function loadChapter(book, chapter, versePosition) {
    console.log(`[App] Loading ${book} ${chapter}:${versePosition}...`);

    // Update dropdowns if needed
    if (book !== currentBook) {
      bookSelect.value = book;
      currentBook = book;
      populateChapterDropdown(book);
    }

    if (chapter !== currentChapter) {
      chapterSelect.value = chapter;
      currentChapter = chapter;
    }

    // Load chapter data
    const verseData = await DataLoader.loadChapter(book, chapter);
    console.log(`[App] Loaded ${Object.keys(verseData).length} verses`);

    // Publish chapter loaded event
    Mediator.publish(Mediator.EVENT_TYPES.CHAPTER_LOADED, {
      book,
      chapter,
      verseData
    });

    // Select verse
    const verses = Object.keys(verseData).map(Number).sort((a, b) => a - b);
    let verseToSelect;

    if (versePosition === 'first') {
      verseToSelect = verses[0];
    } else if (versePosition === 'last') {
      verseToSelect = verses[verses.length - 1];
    } else if (typeof versePosition === 'number') {
      verseToSelect = versePosition;
    } else {
      verseToSelect = verses[0];
    }

    if (verseToSelect) {
      // Publish verse select event
      Mediator.publish(Mediator.EVENT_TYPES.VERSE_SELECT, {
        book,
        chapter,
        verse: verseToSelect
      });
    }
  }

  /**
   * Handle global click to clear highlighting when clicking away from SN elements
   * @param {Event} e
   */
  function handleGlobalClick(e) {
    // Check if click was on an SN element
    const clickedOnSN = e.target.closest('.sn-tag') || e.target.closest('.sn-group');

    if (!clickedOnSN) {
      // Clear all highlighting by removing CSS classes
      document.querySelectorAll('.clicked-local, .clicked-remote').forEach(el => {
        el.classList.remove('clicked-local', 'clicked-remote');
      });
    }
  }

  // Public API
  return {
    init
  };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', App.init);
} else {
  App.init();
}
