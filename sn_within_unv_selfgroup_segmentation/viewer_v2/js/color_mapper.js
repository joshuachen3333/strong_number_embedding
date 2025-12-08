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
   * Apply color to parsed text lines
   * @param {string} parsedText - Parsed and Formatted Text section
   * @param {Array} groups - Groups from parseGroups()
   * @returns {string} HTML with colored SN groups
   */
  function applyColorsToParsedText(parsedText, groups) {
    const lines = parsedText.trim().split('\n');

    // Create SN to color map for consistency with Raw text
    const snToColorMap = createSNToColorMap(groups);

    return lines.map(line => {
      if (!line.trim() || line.includes('Section:')) {
        return line;
      }

      const sns = extractSNsFromLine(line);
      if (sns.length > 0) {
        // Use the color from the FIRST SN in this group to ensure consistency
        const color = snToColorMap[sns[0]] || '#FFFFFF';

        // Color the SN group part (including braced patterns and morphology codes)
        const matchResult = line.match(/^(\{<[^>]+>\}|<[^>]+>)+(\(\*?\*?\d+\))?/);
        if (matchResult) {
          const snPart = matchResult[0];
          const restPart = line.substring(snPart.length);

          // Escape HTML in snPart to prevent browser from interpreting <WHxxxx> as tags
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
