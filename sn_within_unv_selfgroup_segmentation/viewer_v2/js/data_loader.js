/**
 * data_loader.js
 * Data loading with caching for manifest, parsed files, and API
 */

const DataLoader = (() => {
  const FHL_API_BASE = 'https://bible.fhl.net/json/qb.php';

  // In-memory cache
  const cache = {
    manifest: null,
    parsedVerses: {},      // "Book/Chapter/Verse" -> content
    apiChapters: {},       // "Book/Chapter" -> verse array
    sections: {}           // "Book/Chapter/Verse" -> {parsed, raw, notes}
  };

  let manifest = null;

  /**
   * Load manifest.json with caching
   * @returns {Promise<Object>} Manifest data
   */
  async function loadManifest() {
    // Check cache
    if (cache.manifest) {
      console.log('[DataLoader] Manifest loaded from cache');
      manifest = cache.manifest;
      return manifest;
    }

    try {
      Mediator.publish(Mediator.EVENT_TYPES.LOADING_START, { context: 'manifest' });

      const response = await fetch('../output/manifest.json');
      if (!response.ok) {
        throw new Error(`Failed to load manifest: ${response.status}`);
      }

      manifest = await response.json();
      cache.manifest = manifest;

      Mediator.publish(Mediator.EVENT_TYPES.LOADING_END, { context: 'manifest' });

      console.log(`[DataLoader] Manifest loaded: ${Object.keys(manifest.books).length} books`);
      return manifest;

    } catch (error) {
      Mediator.publish(Mediator.EVENT_TYPES.LOADING_END, { context: 'manifest' });
      Mediator.publish(Mediator.EVENT_TYPES.ERROR_SHOW, {
        message: '無法載入清單檔案，請確認 manifest.json 存在',
        type: 'banner'
      });
      console.error('Error loading manifest:', error);
      return { generated: new Date().toISOString(), books: {} };
    }
  }

  /**
   * Get manifest data
   * @returns {Object}
   */
  function getManifest() {
    return manifest;
  }

  /**
   * Check if book has data
   * @param {string} book - Book abbreviation
   * @returns {boolean}
   */
  function hasBookData(book) {
    return manifest && manifest.books && manifest.books[book] !== undefined;
  }

  /**
   * Get chapters for a book
   * @param {string} book - Book abbreviation
   * @returns {number[]}
   */
  function getChapters(book) {
    if (!hasBookData(book)) return [];
    const chapters = manifest.books[book].chapters;
    return Object.keys(chapters).map(Number).sort((a, b) => a - b);
  }

  /**
   * Get verse info for a chapter
   * @param {string} book
   * @param {number} chapter
   * @returns {Object} {verses: [], uncertain: []}
   */
  function getVerseInfo(book, chapter) {
    if (!hasBookData(book)) return { verses: [], uncertain: [] };
    const chapterData = manifest.books[book].chapters[chapter];
    return chapterData || { verses: [], uncertain: [] };
  }

  /**
   * Load parsed verse with caching
   * @param {string} book
   * @param {number} chapter
   * @param {number} verse
   * @returns {Promise<Object>} {content, isUncertain, exists}
   */
  async function loadParsedVerse(book, chapter, verse) {
    const cacheKey = `${book}/${chapter}/${verse}`;

    // Check cache
    if (cache.parsedVerses[cacheKey]) {
      console.log(`[DataLoader] Parsed verse ${cacheKey} from cache`);
      return cache.parsedVerses[cacheKey];
    }

    Mediator.publish(Mediator.EVENT_TYPES.LOADING_START, { context: 'verse', book, chapter, verse });

    try {
      // Try regular file
      const regularPath = `../output/${book}/${chapter}/${verse}`;
      const regularContent = await tryFetchLocal(regularPath);

      if (regularContent) {
        const result = { content: regularContent, isUncertain: false, exists: true };
        cache.parsedVerses[cacheKey] = result;
        Mediator.publish(Mediator.EVENT_TYPES.LOADING_END, { context: 'verse' });
        return result;
      }

      // Try uncertain file
      const uncertainPath = `../output/${book}/${chapter}/${verse}_uncertain`;
      const uncertainContent = await tryFetchLocal(uncertainPath);

      if (uncertainContent) {
        const result = { content: uncertainContent, isUncertain: true, exists: true };
        cache.parsedVerses[cacheKey] = result;
        Mediator.publish(Mediator.EVENT_TYPES.LOADING_END, { context: 'verse' });
        return result;
      }

      // No parsed file
      Mediator.publish(Mediator.EVENT_TYPES.LOADING_END, { context: 'verse' });
      return { content: null, isUncertain: false, exists: false };

    } catch (error) {
      Mediator.publish(Mediator.EVENT_TYPES.LOADING_END, { context: 'verse' });
      console.error(`Error loading parsed verse ${cacheKey}:`, error);
      return { content: null, isUncertain: false, exists: false };
    }
  }

  /**
   * Try to fetch local file
   * @param {string} path
   * @returns {Promise<string|null>}
   */
  async function tryFetchLocal(path) {
    try {
      const response = await fetch(path, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      if (!response.ok) return null;
      return await response.text();
    } catch (error) {
      return null;
    }
  }

  /**
   * Fetch chapter from FHL API with caching
   * @param {string} book
   * @param {number} chapter
   * @returns {Promise<Array>}
   */
  async function fetchChapterFromAPI(book, chapter) {
    const cacheKey = `${book}/${chapter}`;

    // Check cache
    if (cache.apiChapters[cacheKey]) {
      console.log(`[DataLoader] API chapter ${cacheKey} from cache`);
      return cache.apiChapters[cacheKey];
    }

    try {
      const bookData = BOOK_MAP_ENG[book];
      if (!bookData) {
        throw new Error(`Unknown book: ${book}`);
      }

      const url = `${FHL_API_BASE}?version=unv&chineses=${encodeURIComponent(bookData.chi)}&chap=${chapter}&strong=1`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();
      const result = data.record || [];

      // Cache result
      cache.apiChapters[cacheKey] = result;

      return result;

    } catch (error) {
      console.error(`Error fetching chapter from API:`, error);
      Mediator.publish(Mediator.EVENT_TYPES.ERROR_SHOW, {
        message: '無法載入經文資料',
        type: 'toast'
      });
      return [];
    }
  }

  /**
   * Load chapter data (combo of local + API)
   * @param {string} book
   * @param {number} chapter
   * @returns {Promise<Object>} Map of verse -> {text, parsed, isUncertain}
   */
  async function loadChapter(book, chapter) {
    const verseData = {};

    Mediator.publish(Mediator.EVENT_TYPES.LOADING_START, { context: 'chapter', book, chapter });

    // Get verse info from manifest
    const verseInfo = getVerseInfo(book, chapter);

    // Load local parsed files
    if (verseInfo.verses.length > 0) {
      for (const v of verseInfo.verses) {
        const parsed = await loadParsedVerse(book, chapter, v);
        if (parsed.exists) {
          const sections = parseSections(parsed.content);
          verseData[v] = {
            text: sections.raw || '',
            parsed: parsed.content,
            isUncertain: parsed.isUncertain
          };
        }
      }
    }

    // Fetch from API to fill gaps
    try {
      const apiData = await fetchChapterFromAPI(book, chapter);
      apiData.forEach(verseObj => {
        const verseNum = verseObj.sec;
        if (!verseData[verseNum]) {
          verseData[verseNum] = {
            text: verseObj.bible_text || '',
            parsed: null,
            isUncertain: false
          };
        }
      });
    } catch (error) {
      console.error('Error loading chapter:', error);
    }

    Mediator.publish(Mediator.EVENT_TYPES.LOADING_END, { context: 'chapter' });

    return verseData;
  }

  /**
   * Parse 3 sections from parsed output with caching
   * @param {string} content
   * @returns {Object} {parsed, raw, notes, parsedTitle, rawTitle, notesTitle}
   */
  function parseSections(content) {
    const sections = {
      parsed: '',
      raw: '',
      notes: '',
      parsedTitle: 'Parsed and Formatted Text Section',
      rawTitle: 'Raw UNV+SN Source Text Section',
      notesTitle: 'Morphology Notes Section'
    };

    if (!content) return sections;

    const lines = content.split('\n');
    let currentSection = null;

    for (const line of lines) {
      if (line.includes('Parsed and Formatted Text Section')) {
        currentSection = 'parsed';
        // Extract full title (including version info if present)
        sections.parsedTitle = line.replace(/:\s*$/, '');  // Remove trailing colon
        continue;
      } else if (line.includes('Raw UNV+SN Source Text Section')) {
        currentSection = 'raw';
        sections.rawTitle = line.replace(/:\s*$/, '');
        continue;
      } else if (line.includes('Morphology Notes Section')) {
        currentSection = 'notes';
        sections.notesTitle = line.replace(/:\s*$/, '');
        continue;
      }

      if (currentSection && line.trim()) {
        sections[currentSection] += line + '\n';
      }
    }

    return sections;
  }

  /**
   * Clear cache (for testing/debugging)
   */
  function clearCache() {
    cache.parsedVerses = {};
    cache.apiChapters = {};
    cache.sections = {};
    console.log('[DataLoader] Cache cleared');
  }

  // Public API
  return {
    loadManifest,
    getManifest,
    hasBookData,
    getChapters,
    getVerseInfo,
    loadParsedVerse,
    fetchChapterFromAPI,
    loadChapter,
    parseSections,
    clearCache
  };
})();
