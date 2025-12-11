/**
 * app.js
 * Main application controller
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
    console.log('Initializing Parsed Verse Viewer...');

    // Initialize right panel toggle buttons
    RightPanel.initToggleButtons();

    // Load manifest
    manifest = await DataLoader.loadManifest();
    console.log('Manifest loaded:', manifest);

    // Populate book dropdown
    populateBookDropdown();

    // Initialize keyboard navigation
    Navigation.initKeyboard();

    // Set up dropdown change handlers
    bookSelect.addEventListener('change', onBookChange);
    chapterSelect.addEventListener('change', onChapterChange);

    // Get initial position
    const initialPos = Navigation.getInitialPosition();
    console.log('Initial position:', initialPos);

    // Load initial position
    if (initialPos && initialPos.book) {
      // Set book dropdown
      bookSelect.value = initialPos.book;
      currentBook = initialPos.book;

      // Populate chapters
      populateChapterDropdown(initialPos.book);

      // Set chapter dropdown
      if (initialPos.chapter) {
        chapterSelect.value = initialPos.chapter;
        currentChapter = initialPos.chapter;

        // Load chapter and select verse
        await loadChapter(initialPos.book, initialPos.chapter, initialPos.verse);
      }
    }

    console.log('Application initialized.');
  }

  /**
   * Populate book dropdown
   */
  function populateBookDropdown() {
    // Clear existing options except first
    bookSelect.innerHTML = '<option value="">選擇書卷...</option>';

    BOOK_DATA.forEach(book => {
      const option = document.createElement('option');
      option.value = book.eng;

      // Check if book has data
      const hasData = DataLoader.hasBookData(book.eng);

      // Display book name (Chinese + English)
      option.textContent = `${book.chiLong} (${book.engLong})`;

      // Gray out books without data
      if (!hasData) {
        option.disabled = true;
        option.textContent += ' [無資料]';
      }

      bookSelect.appendChild(option);
    });
  }

  /**
   * Populate chapter dropdown
   * @param {string} book - Book abbreviation
   */
  function populateChapterDropdown(book) {
    // Clear existing options
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

    // Auto-select first chapter if available
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
   * Load a chapter
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @param {number|string} versePosition - Verse number or 'first'/'last'
   */
  async function loadChapter(book, chapter, versePosition) {
    console.log(`Loading ${book} ${chapter}:${versePosition}...`);

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
    console.log(`Loaded ${Object.keys(verseData).length} verses`);

    // Render left panel
    LeftPanel.renderChapter(book, chapter, verseData);

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
      LeftPanel.selectVerse(verseToSelect);
    }
  }

  /**
   * Called when a verse is selected (from LeftPanel)
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @param {number} verse - Verse number
   */
  async function onVerseSelected(book, chapter, verse) {
    console.log(`Verse selected: ${book} ${chapter}:${verse}`);

    // Load parsed output
    const result = await DataLoader.loadParsedVerse(book, chapter, verse);

    if (result.exists) {
      // Display parsed output
      RightPanel.displayParsedVerse(book, chapter, verse, result.content, result.isUncertain);
    } else {
      // Display "not parsed"
      RightPanel.displayNotParsed(book, chapter, verse);
    }

    // Update URL hash
    Navigation.updateHash(book, chapter, verse);

    // Save position
    Navigation.savePosition(book, chapter, verse);
  }

  // Public API
  return {
    init,
    loadChapter,
    onVerseSelected
  };
})();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', App.init);
} else {
  App.init();
}
