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
  console.log('[ColorMapper] VERSION 20260218-A LOADED - Token-based Chinese text coloring');

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
   * Example: "<WH07121>(8799) — 動詞..." → ['07121', '8799']
   * Example: "<WH07121>(**8799) — 動詞..." → ['07121', '8799']
   * @param {string} line - Line from parsed output
   * @returns {string[]} Array of SN codes (numeric only, without prefixes)
   */
  function extractSNsFromLine(line) {
    // Match SN group at start of line including:
    // - Angle bracket patterns: <WHdddd>, {<WHdddd>}
    // - Parenthetical morphology codes: (8799), (**8799), (*8799)
    const match = line.match(/^((\{<[^>]+>\}|<[^>]+>)(\(\*?\*?\d+\))?)+/);
    if (!match) return [];

    // Updated pattern to handle both formats:
    // - Prefixed: <WHdddd>, <WAHdddd>, <WTHdddd> (raw UNV+SN)
    // - Non-prefixed: <dddd> (parsed output)
    // - Morphology codes: (8xxx), (*8xxx), (**8xxx)
    const snPattern = /<(?:W[ATH]*H?)?(\d+)>|\((\*?\*?\d+)\)/g;
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
   * Strategy: Multi-SN groups take priority over single-SN groups.
   * When an SN appears in both a multi-SN group (e.g., ['09001', '04325'])
   * and a single-SN group (e.g., ['04325']), the multi-SN group's color wins.
   * This ensures semantic grouping is reflected in colors.
   */
  function createSNToColorMap(groups) {
    const snToColor = {};
    console.log(`[ColorMapper] createSNToColorMap: ${groups.length} groups`);

    // First pass: assign colors to SNs in multi-SN groups (priority)
    groups.forEach((group, index) => {
      if (group.sns.length > 1) {
        const color = getColorForGroup(index);
        console.log(`[ColorMapper] Multi-SN group ${index}: ${group.sns.join(',')} → ${color}`);
        group.sns.forEach(sn => {
          snToColor[sn] = color;  // Overwrite any previous assignment
        });
      }
    });

    // Second pass: assign colors to SNs in single-SN groups (if not already assigned)
    groups.forEach((group, index) => {
      if (group.sns.length === 1) {
        const color = getColorForGroup(index);
        const sn = group.sns[0];
        if (!snToColor[sn]) {
          console.log(`[ColorMapper] Single-SN group ${index}: ${sn} → ${color} (new)`);
          snToColor[sn] = color;
        } else {
          console.log(`[ColorMapper] Single-SN group ${index}: ${sn} already assigned ${snToColor[sn]} (skipped)`);
        }
      }
    });

    console.log(`[ColorMapper] Final colorMap:`, snToColor);
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
      // Also handle morphology codes (8xxx only) that may follow
      return `\\{?<W[ATH]*H?${escapedSN}>\\}?(?:\\{?<WTH8\\d{3}>\\}?|\\(\\*?\\*?8\\d{3}\\))?`;
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
   * Tokenize raw UNV+SN text into alternating text and SN tag tokens
   * @param {string} text - Raw text like "起初<WAH09002><WH07225>，　神<WH0430>"
   * @returns {Array<{type: string, value: string, snCode: string|null, groupIndex: number}>}
   */
  function tokenizeRawText(text) {
    const tagPattern = /(\{?<W[ATH]*H?\d+>\}?)/g;
    const tokens = [];
    let lastIndex = 0;
    let match;

    while ((match = tagPattern.exec(text)) !== null) {
      // Text before this tag
      if (match.index > lastIndex) {
        tokens.push({
          type: 'text',
          value: text.substring(lastIndex, match.index),
          snCode: null,
          groupIndex: -1
        });
      }

      // The tag itself — extract numeric code
      const fullTag = match[0];
      const codeMatch = fullTag.match(/(\d+)/);
      const snCode = codeMatch ? codeMatch[1] : null;

      tokens.push({
        type: 'sn',
        value: fullTag,
        snCode: snCode,
        groupIndex: -1
      });

      lastIndex = tagPattern.lastIndex;
    }

    // Trailing text after last tag
    if (lastIndex < text.length) {
      tokens.push({
        type: 'text',
        value: text.substring(lastIndex),
        snCode: null,
        groupIndex: -1
      });
    }

    return tokens;
  }

  /**
   * Assign group indices to tokens using sequential position-based matching
   * @param {Array} tokens - Token array from tokenizeRawText()
   * @param {Array} groups - Groups from parseGroups()
   */
  function assignGroupsToTokens(tokens, groups) {
    // Build flat ordered list of expected SN codes from groups
    const expectedSNs = [];
    groups.forEach((group, gIdx) => {
      group.sns.forEach(sn => {
        expectedSNs.push({ snCode: sn, groupIndex: gIdx });
      });
    });

    // Pass 1: Assign SN tokens to groups by sequential matching
    let expectedIdx = 0;
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].type !== 'sn' || !tokens[i].snCode) continue;

      // Find matching expected SN (may need to skip ahead if raw text has extra tags)
      while (expectedIdx < expectedSNs.length) {
        if (expectedSNs[expectedIdx].snCode === tokens[i].snCode) {
          tokens[i].groupIndex = expectedSNs[expectedIdx].groupIndex;
          expectedIdx++;
          break;
        }
        expectedIdx++;
      }
    }

    // Pass 2: Assign text tokens to the group of nearest following SN token
    for (let i = 0; i < tokens.length; i++) {
      if (tokens[i].type !== 'text') continue;

      for (let j = i + 1; j < tokens.length; j++) {
        if (tokens[j].type === 'sn' && tokens[j].groupIndex >= 0) {
          tokens[i].groupIndex = tokens[j].groupIndex;
          break;
        }
      }
      // If no following SN found, groupIndex stays -1 (uncolored)
    }
  }

  /**
   * Render tokens as colored HTML
   * @param {Array} tokens - Token array with groupIndex assigned
   * @returns {string} HTML string
   */
  function renderColoredTokens(tokens) {
    let html = '';

    tokens.forEach(token => {
      const color = token.groupIndex >= 0 ? getColorForGroup(token.groupIndex) : null;

      if (token.type === 'sn') {
        // SN tag: escape HTML angle brackets, wrap in .sn-tag span
        const escaped = token.value.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        if (color) {
          html += `<span class="sn-tag" style="background-color: ${color};">${escaped}</span>`;
        } else {
          html += escaped;
        }
      } else {
        // Text: wrap in .sn-text span if colored, otherwise plain
        if (color && token.value.trim()) {
          const escaped = token.value.replace(/</g, '&lt;').replace(/>/g, '&gt;');
          html += `<span class="sn-text" style="background-color: ${color};">${escaped}</span>`;
        } else {
          const escaped = token.value.replace(/</g, '&lt;').replace(/>/g, '&gt;');
          html += escaped;
        }
      }
    });

    return html;
  }

  /**
   * Apply color to text containing SN tags (token-based version)
   * @param {string} text - Raw UNV+SN text with <WHdddd> or {<WHdddd>} tags
   * @param {Object} snToColorMap - Map from SN code to color (used as fallback)
   * @param {Array} groups - Groups from parseGroups() (optional for backward compatibility)
   * @returns {string} HTML with colored spans
   *
   * When groups is provided, uses token-based pipeline to color both SN tags AND
   * the Chinese/English text segments associated with each group.
   * Falls back to legacy SN-only coloring when no groups provided.
   */
  function applyColorsToRawText(text, snToColorMap, groups) {
    // Backward compatibility: if no groups provided, use legacy SN-based coloring
    if (!groups || groups.length === 0) {
      console.warn('[ColorMapper] No groups provided - using legacy SN-based coloring');
      return applyColorsToRawTextLegacy(text, snToColorMap);
    }

    // Token-based coloring: tokenize → assign groups → render
    const tokens = tokenizeRawText(text);
    assignGroupsToTokens(tokens, groups);
    return renderColoredTokens(tokens);
  }

  /**
   * Legacy SN-based coloring (backward compatibility)
   */
  function applyColorsToRawTextLegacy(text, snToColorMap) {
    // Match patterns: <WHdddd>, <WTHdddd>, <WAHdddd>, {<WHdddd>}
    // Plus optional morphology codes (8xxx only): {<WTH8xxx>}, <WTH8xxx>, (8xxx), (**8xxx)
    const snPattern = /(\{?<W[ATH]*H?(\d+)>\}?)(\{?<WTH8\d{3}>\}?|\(\*?\*?8\d{3}\))?/g;

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
    const snPattern = /(\{?<W[ATH]*H?(\d+)>\}?)(\{?<WTH8\d{3}>\}?|\(\*?\*?8\d{3}\))?/g;

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
    const uncoloredPattern = /(?<!<span[^>]*>)(\{?<W[ATH]*H?(\d+)>\}?)(\{?<WTH8\d{3}>\}?|\(\*?\*?8\d{3}\))?(?![^<]*<\/span>)/g;

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
        // Updated regex to capture trailing morphology codes for each SN pattern
        const matchResult = line.match(/^((\{<[^>]+>\}|<[^>]+>)(\(\*?\*?\d+\))?)+/);
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
   * Get all SNs in the same semantic group as the clicked element
   * @param {string} clickedSN - The SN code that was clicked (e.g., '0216')
   * @param {Object} colorMap - Map from SN code to color (used as fallback)
   * @param {Array} groups - Groups from parseGroups()
   * @param {HTMLElement} clickedElement - The actual DOM element that was clicked (optional)
   * @returns {string[]} Array of all SN codes in the same group
   */
  function getSNGroupFromColorMap(clickedSN, colorMap, groups, clickedElement) {
    // NEW: If we have the clicked element, use its ACTUAL background color
    // This handles repeated SNs correctly (e.g., two {<0853>} in different groups)
    if (clickedElement && clickedElement.style && clickedElement.style.backgroundColor) {
      const actualColor = clickedElement.style.backgroundColor;

      // Find the group with this exact color
      for (const group of groups) {
        const groupColor = getColorForGroup(group.groupIndex);
        // Convert to rgb() format for comparison
        const rgbColor = groupColor.startsWith('#') ? hexToRgb(groupColor) : groupColor;

        if (rgbColor === actualColor || groupColor === actualColor) {
          return group.sns;
        }
      }
    }

    // FALLBACK: Use the old color map approach
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
   * Convert hex color to rgb() format for comparison
   * @param {string} hex - Hex color like '#FCE4EC'
   * @returns {string} RGB color like 'rgb(252, 228, 236)'
   */
  function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    if (!result) return hex;

    const r = parseInt(result[1], 16);
    const g = parseInt(result[2], 16);
    const b = parseInt(result[3], 16);

    return `rgb(${r}, ${g}, ${b})`;
  }

  /**
   * Find DOM elements matching the given SN codes in a specific section
   * @param {string[]} snCodes - Array of SN codes to find (e.g., ['0853', '0216'])
   * @param {HTMLElement} container - Container element to search within
   * @param {string} elementClass - Class to search for ('.sn-tag' or '.sn-group')
   * @param {Array} groups - Optional: groups array for position-based matching
   * @param {string} targetColor - Optional: color to match for repeated SNs
   * @returns {HTMLElement[]} Array of matching DOM elements
   */
  function findCorrespondingElements(snCodes, container, elementClass, groups, targetColor) {
    const elements = [];
    const targets = container.querySelectorAll(elementClass);

    // NEW: For position-based matching, find which group these SNs belong to
    let groupColor = targetColor;
    if (!groupColor && groups && groups.length > 0) {
      // Find the group that contains these exact SNs
      for (let i = 0; i < groups.length; i++) {
        const group = groups[i];
        // Check if this group's SNs match the target SNs
        if (group.sns.length === snCodes.length &&
            group.sns.every(sn => snCodes.includes(sn))) {
          groupColor = getColorForGroup(i);
          break;
        }
      }
    }

    targets.forEach(el => {
      const text = el.textContent;

      // Check if this element contains any of the target SN codes
      let hasMatchingSN = false;
      for (const snCode of snCodes) {
        if (text.includes(snCode)) {
          hasMatchingSN = true;
          break;
        }
      }

      if (!hasMatchingSN) return;

      // NEW: If we have a target color, also check if the element's color matches
      if (groupColor && el.style && el.style.backgroundColor) {
        const elColor = el.style.backgroundColor;
        const targetRgb = groupColor.startsWith('#') ? hexToRgb(groupColor) : groupColor;

        // Only include if colors match
        if (elColor === targetRgb || elColor === groupColor) {
          elements.push(el);
        }
      } else {
        // No color filtering - use old behavior
        elements.push(el);
      }
    });

    return elements;
  }

  /**
   * Apply group colors to plain text (no SN tags) by matching Chinese words from UNV.
   * Used for LCC/other versions without Strong's Numbers.
   * @param {string} plainText - Plain text (e.g., LCC verse text)
   * @param {string} rawText - Raw UNV+SN text (to extract Chinese segments and group assignments)
   * @param {Array} groups - Groups from parseGroups()
   * @returns {string} HTML with colored spans for matching words
   */
  function applyColorsToPlainText(plainText, rawText, groups) {
    if (!groups || groups.length === 0 || !rawText || !plainText) {
      return plainText ? plainText.replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';
    }

    // Step 1: Tokenize UNV raw text to get Chinese segments with group assignments
    const tokens = tokenizeRawText(rawText);
    assignGroupsToTokens(tokens, groups);

    // Step 2: Extract Chinese text segments with their group indices
    // Build a queue per unique text for handling repeated words (e.g., two "光" in different groups)
    const cjkPattern = /[\u4e00-\u9fff\u3400-\u4dbf]+/g;
    const textQueue = {};  // text -> [groupIndex, groupIndex, ...]

    for (const token of tokens) {
      if (token.type !== 'text' || token.groupIndex < 0) continue;

      let m;
      cjkPattern.lastIndex = 0;
      while ((m = cjkPattern.exec(token.value)) !== null) {
        const word = m[0];
        if (!textQueue[word]) textQueue[word] = [];
        textQueue[word].push(token.groupIndex);
      }
    }

    // Step 3: Get unique texts sorted by length (longest first for greedy matching)
    const uniqueTexts = Object.keys(textQueue).sort((a, b) => b.length - a.length);

    if (uniqueTexts.length === 0) {
      return plainText.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    // Step 4: Walk through plain text left-to-right, try longest match first
    let html = '';
    let i = 0;
    while (i < plainText.length) {
      let matched = false;

      for (const text of uniqueTexts) {
        if (textQueue[text].length > 0 && plainText.startsWith(text, i)) {
          const groupIndex = textQueue[text].shift();
          const color = getColorForGroup(groupIndex);
          const escaped = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
          html += `<span class="sn-text" style="background-color: ${color};">${escaped}</span>`;
          i += text.length;
          matched = true;
          break;
        }
      }

      if (!matched) {
        const ch = plainText[i];
        html += ch === '<' ? '&lt;' : ch === '>' ? '&gt;' : ch;
        i++;
      }
    }

    return html;
  }

  // Public API
  return {
    parseGroups,
    getColorForGroup,
    createSNToColorMap,
    applyColorsToRawText,
    applyColorsToParsedText,
    applyColorsToPlainText,
    extractSNsFromLine,
    getSNGroupFromColorMap,
    findCorrespondingElements
  };
})();
