/**
 * data_loader.js
 * Data loading from manifest, local files, and FHL API
 */

const DataLoader = (() => {
  let manifest = null;
  const FHL_API_BASE = 'https://bible.fhl.net/json/qb.php';

  /**
   * Load manifest.json
   * @returns {Promise<Object>} Manifest data
   */
  async function loadManifest() {
    try {
      const response = await fetch('../output/manifest.json');
      if (!response.ok) {
        throw new Error(`Failed to load manifest: ${response.status}`);
      }
      manifest = await response.json();
      return manifest;
    } catch (error) {
      console.error('Error loading manifest:', error);
      // Return empty manifest if file doesn't exist
      return { generated: new Date().toISOString(), books: {} };
    }
  }

  /**
   * Get manifest data (must call loadManifest first)
   * @returns {Object} Manifest data
   */
  function getManifest() {
    return manifest;
  }

  /**
   * Check if a book has parsed data
   * @param {string} book - Book abbreviation
   * @returns {boolean}
   */
  function hasBookData(book) {
    return manifest && manifest.books && manifest.books[book] !== undefined;
  }

  /**
   * Get available chapters for a book
   * @param {string} book - Book abbreviation
   * @returns {number[]} Array of chapter numbers
   */
  function getChapters(book) {
    if (!hasBookData(book)) return [];
    const chapters = manifest.books[book].chapters;
    return Object.keys(chapters).map(Number).sort((a, b) => a - b);
  }

  /**
   * Get verse data for a chapter
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @returns {Object} { verses: number[], uncertain: number[] }
   */
  function getVerseInfo(book, chapter) {
    if (!hasBookData(book)) return { verses: [], uncertain: [] };
    const chapterData = manifest.books[book].chapters[chapter];
    return chapterData || { verses: [], uncertain: [] };
  }

  /**
   * Try to fetch a local file
   * @param {string} path - Relative path from viewer/
   * @returns {Promise<string|null>} File content or null if not found
   */
  async function tryFetchLocal(path) {
    try {
      const response = await fetch(path);
      if (!response.ok) return null;
      return await response.text();
    } catch (error) {
      return null;
    }
  }

  /**
   * Load parsed output for a verse
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @param {number} verse - Verse number
   * @returns {Promise<Object>} { content: string, isUncertain: boolean, exists: boolean }
   */
  async function loadParsedVerse(book, chapter, verse) {
    // Try regular file first
    const regularPath = `../output/${book}/${chapter}/${verse}`;
    const regularContent = await tryFetchLocal(regularPath);

    if (regularContent) {
      return { content: regularContent, isUncertain: false, exists: true };
    }

    // Try uncertain file
    const uncertainPath = `../output/${book}/${chapter}/${verse}_uncertain`;
    const uncertainContent = await tryFetchLocal(uncertainPath);

    if (uncertainContent) {
      return { content: uncertainContent, isUncertain: true, exists: true };
    }

    return { content: null, isUncertain: false, exists: false };
  }

  /**
   * Fetch UNV+SN text from FHL API
   * @param {string} book - Book abbreviation (English)
   * @param {number} chapter - Chapter number
   * @param {number} verse - Verse number
   * @returns {Promise<Object>} { sec: number, bible_text: string }
   */
  async function fetchFromAPI(book, chapter, verse) {
    try {
      // Get Chinese book abbreviation
      const bookData = BOOK_MAP_ENG[book];
      if (!bookData) {
        throw new Error(`Unknown book: ${book}`);
      }

      const url = `${FHL_API_BASE}?version=unv&chineses=${encodeURIComponent(bookData.chi)}&chap=${chapter}&sec=${verse}&strong=1`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();

      if (data.record && data.record.length > 0) {
        return data.record[0];
      }

      return null;
    } catch (error) {
      console.error('Error fetching from API:', error);
      return null;
    }
  }

  /**
   * Fetch entire chapter from API
   * @param {string} book - Book abbreviation (English)
   * @param {number} chapter - Chapter number
   * @returns {Promise<Array>} Array of verse objects
   */
  async function fetchChapterFromAPI(book, chapter) {
    try {
      const bookData = BOOK_MAP_ENG[book];
      if (!bookData) {
        throw new Error(`Unknown book: ${book}`);
      }

      // FHL API doesn't have a "get all verses" endpoint, so we need to know verse count
      // For now, fetch up to 200 verses (max for any chapter)
      const url = `${FHL_API_BASE}?version=unv&chineses=${encodeURIComponent(bookData.chi)}&chap=${chapter}&strong=1`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();
      return data.record || [];
    } catch (error) {
      console.error('Error fetching chapter from API:', error);
      return [];
    }
  }

  /**
   * Load chapter data (combination of local and API)
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @returns {Promise<Object>} Map of verse number → verse data
   */
  async function loadChapter(book, chapter) {
    const verseData = {};

    // Get verse info from manifest
    const verseInfo = getVerseInfo(book, chapter);

    // If we have manifest data, try loading local files first
    if (verseInfo.verses.length > 0) {
      for (const v of verseInfo.verses) {
        const parsed = await loadParsedVerse(book, chapter, v);
        if (parsed.exists) {
          // Extract raw UNV+SN from Section 2
          const sections = parseSections(parsed.content);
          verseData[v] = {
            text: sections.raw || '',
            parsed: parsed.content,
            isUncertain: parsed.isUncertain
          };
        }
      }
    }

    // Fetch from API to fill in missing verses or get full chapter
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

    return verseData;
  }

  /**
   * Parse the three sections from parsed output
   * @param {string} content - Full parsed file content
   * @returns {Object} { parsed: string, raw: string, notes: string }
   */
  function parseSections(content) {
    const sections = {
      parsed: '',
      raw: '',
      notes: ''
    };

    if (!content) return sections;

    const lines = content.split('\n');
    let currentSection = null;

    for (const line of lines) {
      if (line.includes('Parsed and Formatted Text Section')) {
        currentSection = 'parsed';
        continue;
      } else if (line.includes('Raw UNV+SN Source Text Section')) {
        currentSection = 'raw';
        continue;
      } else if (line.includes('Morphology Notes Section')) {
        currentSection = 'notes';
        continue;
      }

      if (currentSection && line.trim()) {
        sections[currentSection] += line + '\n';
      }
    }

    return sections;
  }

  // Public API
  return {
    loadManifest,
    getManifest,
    hasBookData,
    getChapters,
    getVerseInfo,
    loadParsedVerse,
    fetchFromAPI,
    fetchChapterFromAPI,
    loadChapter,
    parseSections
  };
})();
