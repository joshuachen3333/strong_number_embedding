/**
 * right_panel.js
 * Right panel (Parsed Output) logic
 */

const RightPanel = (() => {
  let currentSections = { parsed: '', raw: '', notes: '' };
  let currentGroups = [];
  let showParsed = true;
  let showRaw = true;
  let showNotes = true;

  const rightContent = document.getElementById('right-content');
  const uncertainBadge = document.getElementById('uncertain-badge');
  const rightPanel = document.querySelector('.right-panel');

  // Toggle buttons
  const toggleParsedBtn = document.getElementById('toggle-parsed');
  const toggleRawBtn = document.getElementById('toggle-raw');
  const toggleNotesBtn = document.getElementById('toggle-notes');

  /**
   * Initialize toggle buttons
   */
  function initToggleButtons() {
    toggleParsedBtn.addEventListener('click', () => {
      showParsed = !showParsed;
      toggleParsedBtn.classList.toggle('active', showParsed);
      render();
    });

    toggleRawBtn.addEventListener('click', () => {
      showRaw = !showRaw;
      toggleRawBtn.classList.toggle('active', showRaw);
      render();
    });

    toggleNotesBtn.addEventListener('click', () => {
      showNotes = !showNotes;
      toggleNotesBtn.classList.toggle('active', showNotes);
      render();
    });
  }

  /**
   * Display parsed output for a verse
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @param {number} verse - Verse number
   * @param {string} content - Parsed output content
   * @param {boolean} isUncertain - Whether this is an uncertain verse
   */
  function displayParsedVerse(book, chapter, verse, content, isUncertain) {
    // Parse sections
    currentSections = DataLoader.parseSections(content);

    // Parse groups from parsed text
    currentGroups = ColorMapper.parseGroups(currentSections.parsed);

    // Show/hide uncertain badge
    if (isUncertain) {
      uncertainBadge.style.display = 'block';
      rightPanel.classList.add('uncertain');
    } else {
      uncertainBadge.style.display = 'none';
      rightPanel.classList.remove('uncertain');
    }

    // Render
    render();

    // Create SN-to-color map and notify left panel
    const snToColorMap = ColorMapper.createSNToColorMap(currentGroups);
    if (typeof LeftPanel !== 'undefined' && LeftPanel.applyColors) {
      LeftPanel.applyColors(snToColorMap);
    }
  }

  /**
   * Display "not parsed" message
   * @param {string} book - Book abbreviation
   * @param {number} chapter - Chapter number
   * @param {number} verse - Verse number
   */
  function displayNotParsed(book, chapter, verse) {
    uncertainBadge.style.display = 'none';
    rightPanel.classList.remove('uncertain');

    rightContent.innerHTML = `
      <div class="not-parsed">
        <div class="icon">📄</div>
        <div class="message">此節尚未解析</div>
        <div class="verse-ref">${book} ${chapter}:${verse}</div>
      </div>
    `;

    // Clear colors on left panel
    if (typeof LeftPanel !== 'undefined' && LeftPanel.applyColors) {
      LeftPanel.applyColors({});
    }
  }

  /**
   * Render right panel content
   */
  function render() {
    let html = '';

    // Warnings for uncertain verses
    if (rightPanel.classList.contains('uncertain')) {
      html += `
        <div class="warning-message">
          <strong>⚠️ 此節包含不確定的解析</strong>
          請參考下方註釋了解詳情
        </div>
      `;
    }

    // Section 1: Parsed and Formatted Text
    if (showParsed && currentSections.parsed) {
      const coloredParsed = ColorMapper.applyColorsToParsedText(
        currentSections.parsed,
        currentGroups
      );

      html += `
        <div class="parsed-section">
          <div class="section-title">Parsed and Formatted Text Section</div>
          <div class="parsed-content">
            ${coloredParsed.split('\n').map(line =>
              `<div class="parsed-line">${line}</div>`
            ).join('')}
          </div>
        </div>
      `;
    }

    // Section 2: Raw UNV+SN Source Text
    if (showRaw && currentSections.raw) {
      const snToColorMap = ColorMapper.createSNToColorMap(currentGroups);
      const coloredRaw = ColorMapper.applyColorsToRawText(
        currentSections.raw.trim(),
        snToColorMap
      );

      html += `
        <div class="parsed-section">
          <div class="section-title">Raw UNV+SN Source Text Section</div>
          <div class="raw-text">${coloredRaw}</div>
        </div>
      `;
    }

    // Section 3: Morphology Notes
    if (showNotes && currentSections.notes) {
      html += `
        <div class="parsed-section">
          <div class="section-title">Morphology Notes Section</div>
          <div class="morphology-content">
            ${currentSections.notes.split('\n').map(line =>
              `<div class="morphology-note">${escapeHtml(line)}</div>`
            ).join('')}
          </div>
        </div>
      `;
    }

    rightContent.innerHTML = html || '<div class="loading-message">無資料可顯示</div>';

    // Add click handlers for bidirectional highlighting
    addHighlightClickHandlers();
  }

  /**
   * Add click handlers to SN groups and tags for bidirectional highlighting
   */
  function addHighlightClickHandlers() {
    // Add click handlers to SN groups in parsed section
    rightContent.querySelectorAll('.sn-group').forEach(snGroup => {
      snGroup.addEventListener('click', (e) => {
        e.stopPropagation();
        handleSnGroupClick(snGroup);
      });
    });

    // Add click handlers to SN tags in raw section
    rightContent.querySelectorAll('.raw-text .sn-tag').forEach(snTag => {
      snTag.addEventListener('click', (e) => {
        e.stopPropagation();
        handleSnTagClick(snTag);
      });
    });
  }

  /**
   * Handle SN group click in parsed section
   * @param {Element} snGroup - The clicked SN group element
   */
  function handleSnGroupClick(snGroup) {
    // Clear all previous highlights
    clearHighlighting();
    if (typeof LeftPanel !== 'undefined' && LeftPanel.clearHighlighting) {
      LeftPanel.clearHighlighting();
    }

    // Get SN codes from clicked element
    const snCodes = extractSNsFromElement(snGroup);
    if (snCodes.length === 0) return;

    // Apply local highlight (blue) to clicked element
    snGroup.classList.add('sn-highlight-local');

    // Also highlight corresponding elements in raw section
    highlightInRawSection(snCodes);

    // Trigger remote highlighting in left panel
    if (typeof LeftPanel !== 'undefined' && LeftPanel.highlightRemote) {
      LeftPanel.highlightRemote(snCodes);
    }
  }

  /**
   * Handle SN tag click in raw section
   * @param {Element} snTag - The clicked SN tag element
   */
  function handleSnTagClick(snTag) {
    // Clear all previous highlights
    clearHighlighting();
    if (typeof LeftPanel !== 'undefined' && LeftPanel.clearHighlighting) {
      LeftPanel.clearHighlighting();
    }

    // Get SN codes from clicked element
    const snCodes = extractSNsFromElement(snTag);
    if (snCodes.length === 0) return;

    // Apply local highlight (blue) to clicked element
    snTag.classList.add('sn-highlight-local');

    // Also highlight corresponding elements in parsed section
    highlightInParsedSection(snCodes);

    // Trigger remote highlighting in left panel
    if (typeof LeftPanel !== 'undefined' && LeftPanel.highlightRemote) {
      LeftPanel.highlightRemote(snCodes);
    }
  }

  /**
   * Extract SN codes from an element's text content
   * @param {Element} element
   * @returns {string[]} Array of SN codes
   */
  function extractSNsFromElement(element) {
    const text = element.textContent || '';
    // Match <WHdddd>, <WAHdddd>, <WTHdddd>, {<WHdddd>}, (dddd), (*dddd), (**dddd)
    const snPattern = /<W[ATH]*H?(\d+)>|\{<W[ATH]*H?(\d+)>\}|\((\*?\*?\d+)\)/g;
    const sns = [];
    let match;

    while ((match = snPattern.exec(text)) !== null) {
      const sn = match[1] || match[2] || (match[3] ? match[3].replace(/^\*+/, '') : null);
      if (sn) sns.push(sn);
    }

    return sns;
  }

  /**
   * Clear all SN highlighting in right panel
   */
  function clearHighlighting() {
    rightContent.querySelectorAll('.sn-highlight-local, .sn-highlight-remote').forEach(el => {
      el.classList.remove('sn-highlight-local', 'sn-highlight-remote');
    });
  }

  /**
   * Highlight elements in raw section matching SN codes
   * Uses consecutive sequence matching to avoid highlighting wrong occurrences
   * @param {string[]} snCodes - Array of SN codes to highlight
   */
  function highlightInRawSection(snCodes) {
    if (!snCodes || snCodes.length === 0) return;

    const snTags = Array.from(rightContent.querySelectorAll('.raw-text .sn-tag'));
    if (snTags.length === 0) return;

    // For multiple SNs, find consecutive sequence matching all SNs in order
    if (snCodes.length > 1) {
      for (let i = 0; i <= snTags.length - snCodes.length; i++) {
        let matches = true;
        for (let j = 0; j < snCodes.length; j++) {
          const tagSNs = extractSNsFromElement(snTags[i + j]);
          if (!tagSNs.includes(snCodes[j])) {
            matches = false;
            break;
          }
        }
        if (matches) {
          // Found a matching sequence, highlight it
          for (let j = 0; j < snCodes.length; j++) {
            snTags[i + j].classList.add('sn-highlight-local');
          }
          return; // Only highlight the first matching sequence
        }
      }
    } else {
      // For single SN, highlight all matches (fallback behavior)
      snTags.forEach(snTag => {
        const tagSNs = extractSNsFromElement(snTag);
        if (tagSNs.includes(snCodes[0])) {
          snTag.classList.add('sn-highlight-local');
        }
      });
    }
  }

  /**
   * Highlight elements in parsed section matching SN codes
   * @param {string[]} snCodes - Array of SN codes to highlight
   */
  function highlightInParsedSection(snCodes) {
    if (!snCodes || snCodes.length === 0) return;

    rightContent.querySelectorAll('.sn-group').forEach(snGroup => {
      const groupSNs = extractSNsFromElement(snGroup);
      if (groupSNs.some(sn => snCodes.includes(sn))) {
        snGroup.classList.add('sn-highlight-local');
      }
    });
  }

  /**
   * Apply remote highlighting (orange) to elements matching SN codes
   * Uses consecutive sequence matching for raw section to avoid highlighting wrong occurrences
   * @param {string[]} snCodes - Array of SN codes to highlight
   */
  function highlightRemote(snCodes) {
    if (!snCodes || snCodes.length === 0) return;

    // Highlight in parsed section - match groups by exact SN signature
    rightContent.querySelectorAll('.sn-group').forEach(snGroup => {
      const groupSNs = extractSNsFromElement(snGroup);
      // Check if the group's SNs match all the snCodes in order
      if (snCodes.length === groupSNs.length &&
          snCodes.every((sn, idx) => groupSNs[idx] === sn)) {
        snGroup.classList.add('sn-highlight-remote');
      }
    });

    // Highlight in raw section with consecutive sequence matching
    const snTags = Array.from(rightContent.querySelectorAll('.raw-text .sn-tag'));
    if (snTags.length === 0) return;

    if (snCodes.length > 1) {
      for (let i = 0; i <= snTags.length - snCodes.length; i++) {
        let matches = true;
        for (let j = 0; j < snCodes.length; j++) {
          const tagSNs = extractSNsFromElement(snTags[i + j]);
          if (!tagSNs.includes(snCodes[j])) {
            matches = false;
            break;
          }
        }
        if (matches) {
          for (let j = 0; j < snCodes.length; j++) {
            snTags[i + j].classList.add('sn-highlight-remote');
          }
          return; // Only highlight the first matching sequence
        }
      }
    } else {
      // For single SN, highlight all matches
      snTags.forEach(snTag => {
        const tagSNs = extractSNsFromElement(snTag);
        if (tagSNs.includes(snCodes[0])) {
          snTag.classList.add('sn-highlight-remote');
        }
      });
    }
  }

  /**
   * Escape HTML special characters
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Clear right panel
   */
  function clear() {
    currentSections = { parsed: '', raw: '', notes: '' };
    currentGroups = [];
    rightContent.innerHTML = '<div class="loading-message">請點擊左側節次以查看解析結果...</div>';
    uncertainBadge.style.display = 'none';
    rightPanel.classList.remove('uncertain');
  }

  // Public API
  return {
    initToggleButtons,
    displayParsedVerse,
    displayNotParsed,
    clear,
    highlightRemote,
    clearHighlighting
  };
})();
