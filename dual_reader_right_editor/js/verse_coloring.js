/**
 * verse_coloring.js
 * Fetches parsed verse data from the API server and applies group-based coloring
 * using the shared ColorMapper engine.
 *
 * Depends on: ColorMapper (shared/js/color_mapper.js)
 * Used by: left_reader_frontend.js (verse click handler)
 */

const VerseColoring = (() => {
  // Guard: ColorMapper must be loaded first
  if (typeof ColorMapper === 'undefined') {
    console.warn('[VerseColoring] ColorMapper not available — module disabled');
    return null;
  }

  const API_BASE = '/api/parse';

  // In-memory cache: "Gen/1/1" -> {sections, groups, colorMap}
  const cache = {};

  /**
   * Parse parsed output content into sections (simplified from viewer_v2's data_loader.js)
   * @param {string} content - Full parsed verse output
   * @returns {{parsed: string, raw: string, notes: string}}
   */
  function parseSections(content) {
    const sections = { parsed: '', raw: '', notes: '' };
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
      } else if (line.includes('Spec References Section') || line.startsWith('--- UNCERTAINTY')) {
        currentSection = null;
        continue;
      }

      if (currentSection && line.trim()) {
        sections[currentSection] += line + '\n';
      }
    }

    return sections;
  }

  /**
   * Fetch parsed verse data from the API server
   * @param {string} chineses - Chinese book abbreviation (e.g., '創')
   * @param {number} chapter - Chapter number
   * @param {number} verse - Verse number
   * @returns {Promise<{sections, groups, colorMap, isUncertain}|null>}
   */
  async function fetchParsedData(chineses, chapter, verse) {
    // Check cache first
    const cacheKey = `${chineses}/${chapter}/${verse}`;
    if (cache[cacheKey]) return cache[cacheKey];

    try {
      const url = `${API_BASE}?chineses=${encodeURIComponent(chineses)}&chapter=${chapter}&verse=${verse}`;
      const response = await fetch(url);

      if (!response.ok) {
        console.warn(`[VerseColoring] API returned ${response.status} for ${chineses} ${chapter}:${verse}`);
        return null;
      }

      const data = await response.json();
      if (!data.content) return null;

      const sections = parseSections(data.content);
      if (!sections.parsed || !sections.raw) {
        console.warn(`[VerseColoring] Missing parsed/raw sections for ${chineses} ${chapter}:${verse}`);
        return null;
      }

      const groups = ColorMapper.parseGroups(sections.parsed);
      if (!groups || groups.length === 0) {
        console.warn(`[VerseColoring] No groups found for ${chineses} ${chapter}:${verse}`);
        return null;
      }

      const colorMap = ColorMapper.createSNToColorMap(groups);

      const result = {
        sections,
        groups,
        colorMap,
        isUncertain: data.is_uncertain || false
      };

      cache[cacheKey] = result;
      return result;
    } catch (error) {
      console.warn(`[VerseColoring] Fetch error for ${chineses} ${chapter}:${verse}:`, error.message);
      return null;
    }
  }

  /**
   * Apply group-based coloring to a verse element
   * @param {HTMLElement} verseEl - The .verse[data-verse] element
   * @returns {Promise<boolean>} true if coloring was applied
   */
  async function colorVerse(verseEl) {
    if (!verseEl) return false;

    // Already colored?
    if (verseEl.dataset.groupColored === 'true') return true;

    const chineses = verseEl.dataset.book;
    const chapter = parseInt(verseEl.dataset.chapter);
    const verse = parseInt(verseEl.dataset.verse);

    if (!chineses || !chapter || !verse) return false;

    const data = await fetchParsedData(chineses, chapter, verse);
    if (!data) return false;

    // Get the raw text from the parsed output's raw section (trimmed)
    const rawText = data.sections.raw.trim();

    // Apply group-based coloring
    const coloredHtml = ColorMapper.applyColorsToRawText(rawText, data.colorMap, data.groups);

    // Preserve the verse number span
    const verseNumSpan = verseEl.querySelector('.verse-number');
    const verseNumHtml = verseNumSpan ? verseNumSpan.outerHTML + ' ' : '';

    verseEl.innerHTML = verseNumHtml + coloredHtml;
    verseEl.dataset.groupColored = 'true';

    // Re-attach data-strong attributes and strongs-number class to .sn-tag elements
    reattachStrongsAttrs(verseEl);

    return true;
  }

  /**
   * Add data-strong attribute and strongs-number class to .sn-tag elements
   * so that existing A1 highlighting and strongsNumberClicked events still work.
   * @param {HTMLElement} verseEl - The verse element with colored content
   */
  function reattachStrongsAttrs(verseEl) {
    verseEl.querySelectorAll('.sn-tag').forEach(el => {
      const text = el.textContent;
      // Extract SN code from text like "<WH0430>" or "<WAH09002>"
      const match = text.match(/W[ATH]*([HG]?)(\d+)/);
      if (match) {
        const lang = match[1] || 'H'; // Default to Hebrew if no H/G prefix
        const number = match[2];
        el.dataset.strong = `${lang}${number}`;
        el.classList.add('strongs-number');
      }
    });
  }

  // Public API
  return {
    parseSections,
    fetchParsedData,
    colorVerse
  };
})();
