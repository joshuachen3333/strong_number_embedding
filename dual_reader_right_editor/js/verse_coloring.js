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

  // Chinese abbreviation → parser book code (matches start_server.py CHI_TO_ENG)
  const CHI_TO_ENG = {
    '創': 'Gen', '出': 'Exod', '利': 'Lev', '民': 'Num', '申': 'Deut',
    '書': 'Josh', '士': 'Judg', '得': 'Ruth',
    '撒上': '1Sam', '撒下': '2Sam', '王上': '1Kgs', '王下': '2Kgs',
    '代上': '1Chr', '代下': '2Chr', '拉': 'Ezra', '尼': 'Neh',
    '斯': 'Esth', '伯': 'Job', '詩': 'Ps', '箴': 'Prov',
    '傳': 'Eccl', '歌': 'Song', '賽': 'Isa', '耶': 'Jer',
    '哀': 'Lam', '結': 'Ezek', '但': 'Dan', '何': 'Hos',
    '珥': 'Joel', '摩': 'Amos', '俄': 'Obad', '拿': 'Jonah',
    '彌': 'Mic', '鴻': 'Nah', '哈': 'Hab', '番': 'Zeph',
    '該': 'Hag', '亞': 'Zech', '瑪': 'Mal',
    '太': 'Matt', '可': 'Mark', '路': 'Luke', '約': 'John',
    '徒': 'Acts', '羅': 'Rom',
    '林前': '1Cor', '林後': '2Cor', '加': 'Gal', '弗': 'Eph',
    '腓': 'Phil', '西': 'Col',
    '帖前': '1Thess', '帖後': '2Thess',
    '提前': '1Tim', '提後': '2Tim', '多': 'Titus',
    '門': 'Phlm', '來': 'Heb', '雅': 'Jas',
    '彼前': '1Pet', '彼後': '2Pet',
    '約一': '1John', '約二': '2John', '約三': '3John',
    '猶': 'Jude', '啟': 'Rev'
  };

  // In-memory cache: "創/1/1" -> {sections, groups, colorMap}
  const cache = {};

  /**
   * Get parser book code from Chinese abbreviation
   * @param {string} chineses - Chinese book abbreviation (e.g., '創')
   * @returns {string|null} Parser book code (e.g., 'Gen') or null
   */
  function getParserCode(chineses) {
    return CHI_TO_ENG[chineses] || null;
  }

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
   * @returns {Promise<{sections, groups, colorMap, isUncertain}|{error: string}>}
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
        return { error: response.status === 404 ? 'not-found' : 'no-data' };
      }

      const data = await response.json();
      if (!data.content) return { error: 'no-data' };

      const sections = parseSections(data.content);
      if (!sections.parsed || !sections.raw) {
        console.warn(`[VerseColoring] Missing parsed/raw sections for ${chineses} ${chapter}:${verse}`);
        return { error: 'no-data' };
      }

      const groups = ColorMapper.parseGroups(sections.parsed);
      if (!groups || groups.length === 0) {
        console.warn(`[VerseColoring] No groups found for ${chineses} ${chapter}:${verse}`);
        return { error: 'no-data' };
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
      return { error: 'no-server' };
    }
  }

  /**
   * Apply group-based coloring to a verse element
   * @param {HTMLElement} verseEl - The .verse[data-verse] element
   * @returns {Promise<{success: boolean, error: string|null}>}
   */
  async function colorVerse(verseEl) {
    if (!verseEl) return { success: false, error: 'no-data' };

    // Already colored?
    if (verseEl.dataset.groupColored === 'true') return { success: true, error: null };

    const chineses = verseEl.dataset.book;
    const chapter = parseInt(verseEl.dataset.chapter);
    const verse = parseInt(verseEl.dataset.verse);

    if (!chineses || !chapter || !verse) return { success: false, error: 'no-data' };

    const data = await fetchParsedData(chineses, chapter, verse);
    if (data.error) return { success: false, error: data.error };

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

    return { success: true, error: null };
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
    colorVerse,
    getParserCode
  };
})();
