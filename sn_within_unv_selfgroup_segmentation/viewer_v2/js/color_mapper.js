/**
 * color_mapper.js
 * Color mapping for SN groups
 *
 * This module provides position-based color mapping to correctly handle
 * repeated Strong's Numbers in different groups. When the same SN appears
 * in multiple groups (e.g., object marker {<0853>} אֵת), each occurrence
 * receives the color of its respective group, not a single shared color.
 *
 * Key features:
 * - Position-based coloring: matches group patterns sequentially in text
 * - Handles repeated SNs correctly (e.g., two {<0853>} in different groups)
 * - Preserves WH/WAH/WTH prefixes in all processing
 * - Falls back to SN-based coloring for unmatched SNs
 */

const ColorMapper = (() => {
  // Fixed palette of 15 distinct colors
  const GROUP_COLORS = [
    '#E3F2FD', // Light Blue
    '#FFF3E0', // Light Orange
    '#E8F5E9', // Light Green
    '#FCE4EC', // Light Pink
    '#F3E5F5', // Light Purple
    '#E0F7FA', // Light Cyan
    '#FFFDE7', // Light Yellow
    '#EFEBE9', // Light Brown
    '#ECEFF1', // Light Gray-Blue
    '#F1F8E9', // Light Lime
    '#FBE9E7', // Light Deep Orange
    '#E8EAF6', // Light Indigo
    '#E0F2F1', // Light Teal
    '#FFF8E1', // Light Amber
    '#F9FBE7', // Light Yellow-Green
  ];

  /**
   * Extract Strong's Numbers from a parsed text line
   * Example: "<WAH09002><WH07225> — 介系詞..." → ['09002', '07225']
   * Example: "{<WAH0853>}<WH08064> — 冠詞..." → ['0853', '08064']
   * @param {string} line - Line from parsed output
   * @returns {string[]} Array of SN codes (numeric only, without prefixes)
   */
  function extractSNsFromLine(line) {
    const match = line.match(/^(\{<[^>]+>\}|<[^>]+>)+/);
    if (!match) return [];

    // Updated pattern to handle prefixed tags: <WHdddd>, <WAHdddd>, <WTHdddd>
    const snPattern = /<W[ATH]*H?(\d+)>|\((\*?\*?\d+)\)/g;
    const sns = [];
    let m;

    while ((m = snPattern.exec(match[0])) !== null) {
      // Capture either numeric from <WHdddd> or morphology code
      const sn = m[1] || m[2];
      if (sn) {
        // Remove ** or * prefix from morphology codes
        const cleanSN = sn.replace(/^\*+/, '');
        sns.push(cleanSN);
      }
    }

    return sns;
  }

  /**
   * Parse parsed text section to extract groups and their SNs
   * @param {string} parsedText - The "Parsed and Formatted Text Section" content
   * @returns {Array<{groupIndex: number, sns: string[], text: string}>}
   */
  function parseGroups(parsedText) {
    const lines = parsedText.trim().split('\n');
    const groups = [];

    lines.forEach((line, index) => {
      if (!line.trim() || line.includes('Section:')) return;

      const sns = extractSNsFromLine(line);
      if (sns.length > 0) {
        groups.push({
          groupIndex: index,
          sns: sns,
          text: line
        });
      }
    });

    return groups;
  }

  /**
   * Get color for a group index
   * @param {number} groupIndex - Group index (0-based)
   * @returns {string} Color code
   */
  function getColorForGroup(groupIndex) {
    return GROUP_COLORS[groupIndex % GROUP_COLORS.length];
  }

  /**
   * Create a mapping from SN code to color
   * @param {Array} groups - Groups from parseGroups()
   * @returns {Object} Map of SN code → color
   *
   * Note: When the same SN appears in multiple groups (e.g., "light" <0216>
   * appears twice in Gen 1:4), we use "first occurrence wins" strategy to
   * maintain color consistency for the same word throughout the verse.
   */
  function createSNToColorMap(groups) {
    const snToColor = {};

    groups.forEach((group, index) => {
      const color = getColorForGroup(index);
      group.sns.forEach(sn => {
        // Only assign color if not already assigned (first occurrence wins)
        if (!snToColor[sn]) {
          snToColor[sn] = color;
        }
      });
    });

    return snToColor;
  }

  /**
   * Build regex pattern to match a sequence of SNs in raw text
   * @param {string[]} sns - Array of SN codes (e.g., ['0853', '08064'])
   * @returns {RegExp} Regex pattern to match this SN sequence
   *
   * Example: ['0853', '08064'] → /\{?<W[ATH]*H?0853>\}?.*?\{?<W[ATH]*H?08064>\}?/
   */
  function buildRegexPattern(sns) {
    if (!sns || sns.length === 0) return null;

    const snPatterns = sns.map(sn => {
      // Escape special regex chars in SN code
      const escapedSN = sn.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      // Match: optional brace, <WH/WAH/WTH prefix>, SN code, >, optional brace
      // Also handle morphology codes that may follow
      return `\\{?<W[ATH]*H?${escapedSN}>\\}?(?:<W[ATH]*H?\\d+>|\\(\\*?\\*?\\d+\\))?`;
    }).join('([^<>{}()]+)?');  // Only match text WITHOUT angle brackets/braces between SNs

    return new RegExp(snPatterns, 'g');
  }

  /**
   * Build group pattern matchers for position-based coloring
   * @param {Array} groups - Groups from parseGroups()
   * @returns {Array<{groupIndex: number, sns: string[], pattern: RegExp, color: string}>}
   */
  function buildGroupPatterns(groups) {
    return groups.map((group, index) => ({
      groupIndex: index,
      sns: group.sns,
      pattern: buildRegexPattern(group.sns),
      color: getColorForGroup(index)
    }));
  }

  /**
   * Apply color to text containing SN tags (position-based version)
   * @param {string} text - Raw UNV+SN text with <WHdddd> or {<WHdddd>} tags
   * @param {Object} snToColorMap - Map from SN code to color (used as fallback)
   * @param {Array} groups - Groups from parseGroups() (optional for backward compatibility)
   * @returns {string} HTML with colored spans
   *
   * NEW: When groups is provided, uses position-based matching to handle repeated SNs correctly.
   * Falls back to SN-based coloring for unmatched SNs.
   */
  function applyColorsToRawText(text, snToColorMap, groups) {
    // Backward compatibility: if no groups provided, use legacy SN-based coloring
    if (!groups || groups.length === 0) {
      console.warn('[ColorMapper] No groups provided - using legacy SN-based coloring');
      return applyColorsToRawTextLegacy(text, snToColorMap);
    }

    // Position-based coloring: collect all matches first, then apply in reverse order
    const allMatches = [];
    const groupPatterns = buildGroupPatterns(groups);

    // Collect all matches from all groups
    groupPatterns.forEach(({pattern, color, sns}) => {
      if (!pattern) return;

      let match;
      pattern.lastIndex = 0;

      while ((match = pattern.exec(text)) !== null) {
        const matchStart = match.index;
        const matchEnd = matchStart + match[0].length;

        // Check if this range overlaps with already-recorded matches
        const overlaps = allMatches.some(m =>
          (matchStart >= m.start && matchStart < m.end) ||
          (matchEnd > m.start && matchEnd <= m.end) ||
          (matchStart <= m.start && matchEnd >= m.end)
        );

        if (!overlaps) {
          allMatches.push({
            start: matchStart,
            end: matchEnd,
            text: match[0],
            color: color
          });
        }
      }
    });

    // Sort matches by start position (descending) to apply from end to start
    allMatches.sort((a, b) => b.start - a.start);

    // Apply colors from end to start (so indices remain valid)
    let result = text;
    allMatches.forEach(({start, end, text: matchedText, color}) => {
      const coloredText = colorSNsInSpan(matchedText, color);
      result = result.substring(0, start) + coloredText + result.substring(end);
    });

    // Fallback: color any remaining uncolored SNs using SN-based map
    result = applyFallbackColoring(result, snToColorMap);

    return result;
  }

  /**
   * Legacy SN-based coloring (backward compatibility)
   */
  function applyColorsToRawTextLegacy(text, snToColorMap) {
    // Match patterns: <WHdddd>, <WTHdddd>, <WAHdddd>, {<WHdddd>}
    // Plus optional morphology codes (**dddd) or (*dddd) that follow
    const snPattern = /(\{?<W[ATH]*H?(\d+)>\}?)(<W[AT]*H?\d+>|\(\*?\*?\d+\))?/g;

    return text.replace(snPattern, (match, fullTag, snCode, morphCode) => {
      const color = snToColorMap[snCode];
      // HTML-escape the angle brackets to prevent browser interpretation as tags
      const escapedTag = fullTag.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const escapedMorph = morphCode ? morphCode.replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';

      if (color) {
        // Apply same color to both Strong's number and morphology code
        return `<span class="sn-tag" style="background-color: ${color};">${escapedTag}${escapedMorph}</span>`;
      }
      return escapedTag + escapedMorph;
    });
  }

  /**
   * Color all SNs within a text span with the same color
   * @param {string} text - Text containing SN tags
   * @param {string} color - Background color to apply
   * @returns {string} HTML with colored spans
   */
  function colorSNsInSpan(text, color) {
    const snPattern = /(\{?<W[ATH]*H?(\d+)>\}?)(<W[AT]*H?\d+>|\(\*?\*?\d+\))?/g;

    return text.replace(snPattern, (match, fullTag, snCode, morphCode) => {
      const escapedTag = fullTag.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const escapedMorph = morphCode ? morphCode.replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';

      return `<span class="sn-tag" style="background-color: ${color};">${escapedTag}${escapedMorph}</span>`;
    });
  }

  /**
   * Apply fallback coloring to SNs not colored by group matching
   * @param {string} html - Partially colored HTML
   * @param {Object} snToColorMap - SN-to-color fallback map
   * @returns {string} HTML with fallback colors applied
   */
  function applyFallbackColoring(html, snToColorMap) {
    // Match uncolored SN patterns (not already wrapped in <span>)
    const uncoloredPattern = /(?<!<span[^>]*>)(\{?<W[ATH]*H?(\d+)>\}?)(<W[AT]*H?\d+>|\(\*?\*?\d+\))?(?![^<]*<\/span>)/g;

    return html.replace(uncoloredPattern, (match, fullTag, snCode, morphCode) => {
      const color = snToColorMap[snCode];
      if (!color) {
        // No color available - return as-is
        return match.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      }

      const escapedTag = fullTag.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      const escapedMorph = morphCode ? morphCode.replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';

      console.warn(`[ColorMapper] Fallback coloring for unmatched SN: ${snCode}`);
      return `<span class="sn-tag" style="background-color: ${color};">${escapedTag}${escapedMorph}</span>`;
    });
  }

  /**
   * Apply color to parsed text lines
   * @param {string} parsedText - Parsed and Formatted Text section
   * @param {Array} groups - Groups from parseGroups()
   * @returns {string} HTML with colored SN groups
   */
  function applyColorsToParsedText(parsedText, groups) {
    const lines = parsedText.trim().split('\n');

    // Position-based coloring: each line corresponds to a group
    let groupIndex = 0;

    return lines.map(line => {
      if (!line.trim() || line.includes('Section:')) {
        return line;
      }

      const sns = extractSNsFromLine(line);
      if (sns.length > 0) {
        // Use position-based color: each group gets its own color based on index
        const color = getColorForGroup(groupIndex);
        groupIndex++;

        // Color the SN group part (including braced patterns and morphology codes)
        const matchResult = line.match(/^(\{<[^>]+>\}|<[^>]+>)+(\(\*?\*?\d+\))?/);
        if (matchResult) {
          const snPart = matchResult[0];
          const restPart = line.substring(snPart.length);

          // Escape HTML in BOTH snPart and restPart to prevent browser from interpreting <WHxxxx> as tags
          const escapedSnPart = snPart.replace(/</g, '&lt;').replace(/>/g, '&gt;');
          const escapedRestPart = restPart.replace(/</g, '&lt;').replace(/>/g, '&gt;');
          return `<span class="sn-group" style="background-color: ${color};">${escapedSnPart}</span>${escapedRestPart}`;
        }
      }

      return line;
    }).join('\n');
  }

  /**
   * Get all SNs in the same semantic group as the clicked SN
   * @param {string} clickedSN - The SN code that was clicked (e.g., '0216')
   * @param {Object} colorMap - Map from SN code to color
   * @param {Array} groups - Groups from parseGroups()
   * @returns {string[]} Array of all SN codes in the same group
   */
  function getSNGroupFromColorMap(clickedSN, colorMap, groups) {
    // Get the color assigned to clicked SN
    const targetColor = colorMap[clickedSN];
    if (!targetColor) return [clickedSN];

    // Find the group that has this color
    for (const group of groups) {
      const groupColor = getColorForGroup(group.groupIndex);
      if (groupColor === targetColor) {
        return group.sns;  // Return all SNs in this group
      }
    }

    return [clickedSN];  // Fallback to single SN
  }

  /**
   * Find DOM elements matching the given SN codes in a specific section
   * @param {string[]} snCodes - Array of SN codes to find (e.g., ['0853', '0216'])
   * @param {HTMLElement} container - Container element to search within
   * @param {string} elementClass - Class to search for ('.sn-tag' or '.sn-group')
   * @returns {HTMLElement[]} Array of matching DOM elements
   */
  function findCorrespondingElements(snCodes, container, elementClass) {
    const elements = [];
    const targets = container.querySelectorAll(elementClass);

    targets.forEach(el => {
      const text = el.textContent;
      // Check if this element contains any of the target SN codes
      for (const snCode of snCodes) {
        if (text.includes(snCode)) {
          elements.push(el);
          break;  // Don't add same element multiple times
        }
      }
    });

    return elements;
  }

  // Public API
  return {
    parseGroups,
    getColorForGroup,
    createSNToColorMap,
    applyColorsToRawText,
    applyColorsToParsedText,
    extractSNsFromLine,
    getSNGroupFromColorMap,
    findCorrespondingElements
  };
})();
