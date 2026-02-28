/**
 * data_loader.js
 * Data loading with caching for manifest, parsed files, and API
 */

const DataLoader = (() => {
  const FHL_API_BASE = 'https://bible.fhl.net/json/qb.php';

  // In-memory cache
  const cache = {
    manifest: null,
    parsedVerses: {},        // "Book/Chapter/Verse" -> content
    apiChapters: {},          // "Book/Chapter" -> verse array
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
    const chaps = manifest.books[book].chapters;
    return Object.keys(chaps).map(Number).sort((a, b) => a - b);
  }

  /**
   * Get verse info for a chapter
   * @param {string} book
   * @param {number} chap
   * @returns {Object} {verses: [], uncertain: []}
   */
  function getVerseInfo(book, chap) {
    if (!hasBookData(book)) return { verses: [], uncertain: [] };
    const chapterData = manifest.books[book].chapters[chap];
    return chapterData || { verses: [], uncertain: [] };
  }

  /**
   * Load parsed verse with caching
   * @param {string} book
   * @param {number} chap
   * @param {number} verse
   * @returns {Promise<Object>} {content, isUncertain, exists}
   */
  async function loadParsedVerse(book, chap, sec) {
    const cacheKey = `${book}/${chap}/${sec}`;

    // Check cache
    if (cache.parsedVerses[cacheKey]) {
      console.log(`[DataLoader] Parsed verse ${cacheKey} from cache`);
      return cache.parsedVerses[cacheKey];
    }

    Mediator.publish(Mediator.EVENT_TYPES.LOADING_START, { context: 'verse', book, chap, sec });

    try {
      // Try regular file
      const regularPath = `../output/${book}/${chap}/${sec}`;
      const regularContent = await tryFetchLocal(regularPath);

      if (regularContent) {
        const result = { content: regularContent, isUncertain: false, exists: true };
        cache.parsedVerses[cacheKey] = result;
        Mediator.publish(Mediator.EVENT_TYPES.LOADING_END, { context: 'verse' });
        return result;
      }

      // Try uncertain file
      const uncertainPath = `../output/${book}/${chap}/${sec}_uncertain`;
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
   * @param {number} chap
   * @returns {Promise<Array>}
   */
  async function fetchChapterFromAPI(book, chap) {
    const cacheKey = `${book}/${chap}`;

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

      const url = `${FHL_API_BASE}?version=unv&chineses=${encodeURIComponent(bookData.chi)}&chap=${chap}&strong=1`;
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
   * Fetch KJV chapter from FHL API with caching
   * @param {string} book - English book abbreviation (e.g., "Gen")
   * @param {number} chap
   * @returns {Promise<Array>}
   */
  async function fetchKJVChapterFromAPI(book, chap) {
    const cacheKey = `kjv/${book}/${chap}`;

    // Check cache
    if (cache.apiChapters[cacheKey]) {
      console.log(`[DataLoader] KJV API chapter ${cacheKey} from cache`);
      return cache.apiChapters[cacheKey];
    }

    try {
      const bookData = BOOK_MAP_ENG[book];
      if (!bookData) {
        throw new Error(`Unknown book: ${book}`);
      }

      const url = `${FHL_API_BASE}?version=kjv&chineses=${encodeURIComponent(bookData.chi)}&chap=${chap}&strong=1`;
      console.log(`[DataLoader] Fetching KJV: ${url}`);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`KJV API request failed: ${response.status}`);
      }

      const data = await response.json();
      const result = data.record || [];

      // Cache result
      cache.apiChapters[cacheKey] = result;

      console.log(`[DataLoader] KJV loaded: ${result.length} verses`);
      return result;

    } catch (error) {
      console.error(`Error fetching KJV chapter from API:`, error);
      Mediator.publish(Mediator.EVENT_TYPES.ERROR_SHOW, {
        message: '無法載入 KJV 經文資料',
        type: 'toast'
      });
      return [];
    }
  }

  /**
   * Fetch LCC chapter from FHL API with caching
   * @param {string} book - English book abbreviation (e.g., "Gen")
   * @param {number} chap
   * @returns {Promise<Array>}
   */
  async function fetchLCCChapterFromAPI(book, chap) {
    const cacheKey = `lcc/${book}/${chap}`;

    // Check cache
    if (cache.apiChapters[cacheKey]) {
      console.log(`[DataLoader] LCC API chapter ${cacheKey} from cache`);
      return cache.apiChapters[cacheKey];
    }

    try {
      const bookData = BOOK_MAP_ENG[book];
      if (!bookData) {
        throw new Error(`Unknown book: ${book}`);
      }

      const url = `${FHL_API_BASE}?version=lcc&chineses=${encodeURIComponent(bookData.chi)}&chap=${chap}`;
      console.log(`[DataLoader] Fetching LCC: ${url}`);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`LCC API request failed: ${response.status}`);
      }

      const data = await response.json();
      const result = data.record || [];

      // Cache result
      cache.apiChapters[cacheKey] = result;

      console.log(`[DataLoader] LCC loaded: ${result.length} verses`);
      return result;

    } catch (error) {
      console.error(`Error fetching LCC chapter from API:`, error);
      Mediator.publish(Mediator.EVENT_TYPES.ERROR_SHOW, {
        message: '無法載入呂振中譯本經文資料',
        type: 'toast'
      });
      return [];
    }
  }

  /**
   * Load chapter data (combo of local + API)
   * @param {string} book
   * @param {number} chap
   * @returns {Promise<Object>} Map of verse -> {text, parsed, isUncertain}
   */
  async function loadChapter(book, chap) {
    const verseData = {};

    Mediator.publish(Mediator.EVENT_TYPES.LOADING_START, { context: 'chapter', book, chap });

    // Get verse info from manifest
    const verseInfo = getVerseInfo(book, chap);

    // Load local parsed files
    if (verseInfo.verses.length > 0) {
      for (const v of verseInfo.verses) {
        const parsed = await loadParsedVerse(book, chap, v);
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
      const apiData = await fetchChapterFromAPI(book, chap);
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
      spec: '',
      specRefs: {},  // Parsed spec references: { "3.3.2": { title: "...", content: "..." } }
      parsedTitle: 'Parsed and Formatted Text Section',
      rawTitle: 'Raw UNV+SN Source Text Section',
      notesTitle: 'Morphology Notes Section',
      specTitle: 'Spec References Section'
    };

    if (!content) return sections;

    const lines = content.split('\n');
    let currentSection = null;
    let currentSpecRef = null;  // For parsing spec references

    for (const line of lines) {
      if (line.includes('Parsed and Formatted Text Section')) {
        currentSection = 'parsed';
        currentSpecRef = null;
        // Extract full title (including version info if present)
        sections.parsedTitle = line.replace(/:\s*$/, '');  // Remove trailing colon
        continue;
      } else if (line.includes('Raw UNV+SN Source Text Section')) {
        currentSection = 'raw';
        currentSpecRef = null;
        sections.rawTitle = line.replace(/:\s*$/, '');
        continue;
      } else if (line.includes('Morphology Notes Section')) {
        currentSection = 'notes';
        currentSpecRef = null;
        sections.notesTitle = line.replace(/:\s*$/, '');
        continue;
      } else if (line.includes('Spec References Section')) {
        currentSection = 'spec';
        currentSpecRef = null;
        sections.specTitle = line.replace(/:\s*$/, '');
        continue;
      } else if (line.startsWith('--- UNCERTAINTY')) {
        // Stop parsing at uncertainty notes
        currentSection = null;
        currentSpecRef = null;
        continue;
      }

      // Parse spec references section into structured data
      if (currentSection === 'spec') {
        // Check for new spec reference header: [3.3.2]: Title
        const refMatch = line.match(/^\[(\d+(?:\.\d+)*)\]:\s*(.+)$/);
        if (refMatch) {
          currentSpecRef = refMatch[1];
          sections.specRefs[currentSpecRef] = {
            title: refMatch[2],
            content: ''
          };
          continue;
        }
        // Append content to current spec reference
        if (currentSpecRef && line.trim()) {
          sections.specRefs[currentSpecRef].content += line + '\n';
        }
        // Also store raw text
        if (line.trim()) {
          sections.spec += line + '\n';
        }
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
    fetchKJVChapterFromAPI,
    fetchLCCChapterFromAPI,
    loadChapter,
    parseSections,
    clearCache
  };
})();
