/**
 * color_mapper.js
 * Color mapping for SN groups
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
   * Example: "<WH0776> — 名詞..." → ['0776']
   * Example: "<WH01961>(8804) — 動詞..." → ['01961', '8804']
   * Example: "{<WAH05921>}<WH06440> — ..." → ['05921', '06440']
   * @param {string} line - Line from parsed output
   * @returns {string[]} Array of SN codes
   */
  function extractSNsFromLine(line) {
    // Match the SN group part at the beginning of the line
    // Format: <WHdddd>, <WAHdddd>, <WTHdddd>, {<WHdddd>}, (dddd), (*dddd), (**dddd)
    const match = line.match(/^([<{(][^—]+)/);
    if (!match) return [];

    const snPart = match[0];
    const sns = [];

    // Match <WHdddd>, <WAHdddd>, <WTHdddd> patterns
    const whPattern = /<W[ATH]*H?(\d+)>/g;
    let m;
    while ((m = whPattern.exec(snPart)) !== null) {
      sns.push(m[1]);
    }

    // Match (dddd), (*dddd), (**dddd) morphology patterns
    const morphPattern = /\((\*?\*?\d+)\)/g;
    while ((m = morphPattern.exec(snPart)) !== null) {
      const cleanSN = m[1].replace(/^\*+/, '');
      sns.push(cleanSN);
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
   */
  function createSNToColorMap(groups) {
    const snToColor = {};

    groups.forEach((group, index) => {
      const color = getColorForGroup(index);
      group.sns.forEach(sn => {
        snToColor[sn] = color;
      });
    });

    return snToColor;
  }

  /**
   * Apply color to text containing SN tags
   * @param {string} text - Raw UNV+SN text with <WHdddd> or {<WHdddd>} tags
   * @param {Object} snToColorMap - Map from SN code to color
   * @returns {string} HTML with colored spans
   */
  function applyColorsToRawText(text, snToColorMap) {
    // Match patterns: <WHdddd>, <WTHdddd>, <WAHdddd>, {<WHdddd>}
    const snPattern = /(\{?<W[ATH]*H?(\d+)>\}?)/g;

    return text.replace(snPattern, (match, fullTag, snCode) => {
      const color = snToColorMap[snCode];
      // Escape HTML entities to prevent browser interpretation
      const escapedTag = fullTag.replace(/</g, '&lt;').replace(/>/g, '&gt;');
      if (color) {
        return `<span class="sn-tag" style="background-color: ${color};">${escapedTag}</span>`;
      }
      return escapedTag;
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
    let groupIndex = 0;

    return lines.map(line => {
      if (!line.trim() || line.includes('Section:')) {
        return line;
      }

      const sns = extractSNsFromLine(line);
      if (sns.length > 0 && groupIndex < groups.length) {
        const color = getColorForGroup(groupIndex);
        groupIndex++;

        // Match the SN group part at the beginning of the line
        // Format: <WHdddd>, <WAHdddd>, <WTHdddd>, {<WHdddd>}, (dddd)
        const snPartMatch = line.match(/^([<{][^—]+)/);
        if (snPartMatch) {
          const snPart = snPartMatch[0].trim();
          const restPart = line.substring(snPartMatch[0].length);

          // Escape HTML entities in snPart to prevent browser interpretation
          const escapedSnPart = snPart.replace(/</g, '&lt;').replace(/>/g, '&gt;');

          return `<span class="sn-group" style="background-color: ${color};">${escapedSnPart}</span>${restPart}`;
        }
      }

      return line;
    }).join('\n');
  }

  // Public API
  return {
    parseGroups,
    getColorForGroup,
    createSNToColorMap,
    applyColorsToRawText,
    applyColorsToParsedText,
    extractSNsFromLine
  };
})();
