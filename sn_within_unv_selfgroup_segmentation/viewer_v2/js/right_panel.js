/**
 * right_panel.js
 * Right panel (Parsed Output) with event-driven architecture
 */

const RightPanel = (() => {
  // localStorage keys
  const STORAGE_KEY_SHOW_PARSED = 'viewer_v2_show_parsed';
  const STORAGE_KEY_SHOW_RAW = 'viewer_v2_show_raw';
  const STORAGE_KEY_SHOW_NOTES = 'viewer_v2_show_notes';
  const STORAGE_KEY_SHOW_SPEC = 'viewer_v2_show_spec';

  let currentSections = { parsed: '', raw: '', notes: '', specRefs: null };
  let currentGroups = [];
  let currentColorMap = {};
  let currentVerse = null;  // Track current verse for single-HL filtering
  let showParsed = true;   // Default ON
  let showRaw = false;     // Default OFF
  let showNotes = false;   // Default OFF
  let showSpec = false;    // Default OFF - spec tooltips
  let singleHighlightMode = true; // Single highlight mode: true = clear previous, false = multi-highlight
  let specTooltipElement = null; // Tooltip element for spec references

  const rightContent = document.getElementById('right-content');
  const uncertainBadge = document.getElementById('uncertain-badge');
  const verseRefDisplay = document.getElementById('verse-ref-display');
  const rightPanel = document.querySelector('.right-panel');
  const singleHighlightCheckbox = document.getElementById('single-highlight-mode');

  // Toggle buttons
  const toggleParsedBtn = document.getElementById('toggle-parsed');
  const toggleRawBtn = document.getElementById('toggle-raw');
  const toggleNotesBtn = document.getElementById('toggle-notes');
  // Spec is now a checkbox, not a button
  const toggleSpecCheckbox = document.getElementById('toggle-spec');

  /**
   * Load setting from localStorage with error handling
   * @param {string} key
   * @param {*} defaultValue
   * @returns {*}
   */
  function loadSetting(key, defaultValue) {
    try {
      const stored = localStorage.getItem(key);
      if (stored === null) return defaultValue;
      return JSON.parse(stored);
    } catch (e) {
      console.warn(`[RightPanel] Failed to load setting ${key}:`, e);
      return defaultValue;
    }
  }

  /**
   * Save setting to localStorage with error handling
   * @param {string} key
   * @param {*} value
   */
  function saveSetting(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.warn(`[RightPanel] Failed to save setting ${key}:`, e);
    }
  }

  /**
   * Initialize right panel
   */
  function init() {
    console.log('[RightPanel] Initializing...');

    // Load saved toggle states from localStorage
    showParsed = loadSetting(STORAGE_KEY_SHOW_PARSED, true);
    showRaw = loadSetting(STORAGE_KEY_SHOW_RAW, false);
    showNotes = loadSetting(STORAGE_KEY_SHOW_NOTES, false);
    showSpec = loadSetting(STORAGE_KEY_SHOW_SPEC, false);
    console.log(`[RightPanel] Loaded settings: Parsed=${showParsed}, Raw=${showRaw}, Notes=${showNotes}, Spec=${showSpec}`);

    // Initialize toggle buttons
    initToggleButtons();

    // Initialize Single Highlight mode checkbox (cross-panel coordination with left panel)
    if (singleHighlightCheckbox) {
      singleHighlightMode = singleHighlightCheckbox.checked;
      console.log(`[RightPanel] Single HL checkbox initialized: ${singleHighlightMode ? 'ON (checked)' : 'OFF (unchecked)'}`);
      singleHighlightCheckbox.addEventListener('change', (e) => {
        singleHighlightMode = e.target.checked;
        console.log(`[RightPanel] Single highlight mode: ${singleHighlightMode ? 'ON' : 'OFF'}`);
      });
    } else {
      console.warn('[RightPanel] Single HL checkbox not found!');
    }

    // Subscribe to verse selected event
    Mediator.subscribe(Mediator.EVENT_TYPES.VERSE_SELECTED, handleVerseSelected);
    console.log('[RightPanel] Subscribed to VERSE_SELECTED');

    // Subscribe to SN click event for highlighting
    Mediator.subscribe(Mediator.EVENT_TYPES.SN_CLICK, handleSNClickForHighlighting);
  }

  /**
   * Initialize toggle buttons
   */
  function initToggleButtons() {
    // Apply initial states from loaded settings
    toggleParsedBtn.classList.toggle('active', showParsed);
    toggleRawBtn.classList.toggle('active', showRaw);
    toggleNotesBtn.classList.toggle('active', showNotes);
    // Spec is now a checkbox
    if (toggleSpecCheckbox) {
      toggleSpecCheckbox.checked = showSpec;
    }

    toggleParsedBtn.addEventListener('click', () => {
      showParsed = !showParsed;
      toggleParsedBtn.classList.toggle('active', showParsed);
      saveSetting(STORAGE_KEY_SHOW_PARSED, showParsed);
      render();
    });

    toggleRawBtn.addEventListener('click', () => {
      showRaw = !showRaw;
      toggleRawBtn.classList.toggle('active', showRaw);
      saveSetting(STORAGE_KEY_SHOW_RAW, showRaw);
      render();
    });

    toggleNotesBtn.addEventListener('click', () => {
      showNotes = !showNotes;
      toggleNotesBtn.classList.toggle('active', showNotes);
      saveSetting(STORAGE_KEY_SHOW_NOTES, showNotes);
      render();
    });

    // Spec checkbox handler
    if (toggleSpecCheckbox) {
      toggleSpecCheckbox.addEventListener('change', (e) => {
        showSpec = e.target.checked;
        saveSetting(STORAGE_KEY_SHOW_SPEC, showSpec);
        render();
      });
    }
  }

  /**
   * Handle verse selected event
   * @param {Object} data - {book, chapter, verse, content, isUncertain, exists}
   */
  function handleVerseSelected(data) {
    const { book, chapter, verse, content, isUncertain, exists } = data;
    console.log(`[RightPanel] Received VERSE_SELECTED:`, data);

    // Only clear SN highlighting when switching to a DIFFERENT verse
    // (clicking SN on same verse should preserve highlighting)
    if (verse !== currentVerse) {
      clearHighlighting();
    }

    if (!exists) {
      console.log(`[RightPanel] Verse not parsed, showing "not parsed" message`);
      displayNotParsed(book, chapter, verse);
      return;
    }

    console.log(`[RightPanel] Displaying parsed verse`);
    displayParsedVerse(book, chapter, verse, content, isUncertain);
  }

  /**
   * Display parsed verse
   * @param {string} book
   * @param {number} chapter
   * @param {number} verse
   * @param {string} content
   * @param {boolean} isUncertain
   */
  function displayParsedVerse(book, chapter, verse, content, isUncertain) {
    // Store current verse for single-HL filtering
    currentVerse = verse;

    // Update verse reference display
    verseRefDisplay.textContent = `${book} ${chapter}:${verse}`;
    verseRefDisplay.style.display = 'block';

    // Parse sections
    currentSections = DataLoader.parseSections(content);

    // Show/hide uncertain badge
    if (isUncertain) {
      uncertainBadge.style.display = 'block';
      rightPanel.classList.add('uncertain');
    } else {
      uncertainBadge.style.display = 'none';
      rightPanel.classList.remove('uncertain');
    }

    // First render without colors (to create DOM elements for group parsing)
    render();

    // Parse groups FROM DOM after rendering (more reliable than parsing from raw text)
    const parsedContent = rightContent.querySelector('.parsed-section .parsed-content');
    if (parsedContent) {
      const preElements = Array.from(parsedContent.querySelectorAll('pre.parsed-line'));
      const reconstructedText = preElements.map(pre => pre.textContent).join('\n');
      currentGroups = ColorMapper.parseGroups(reconstructedText);
      console.log(`[RightPanel] Parsed ${currentGroups.length} groups from DOM`);
    } else {
      // Fallback: try parsing from raw text
      currentGroups = ColorMapper.parseGroups(currentSections.parsed);
      console.log(`[RightPanel] Parsed ${currentGroups.length} groups from raw text (fallback)`);
    }

    // Create color map
    currentColorMap = ColorMapper.createSNToColorMap(currentGroups);

    // Re-render with colors applied
    console.log(`[RightPanel] Re-rendering with ${currentGroups.length} groups and colorMap with ${Object.keys(currentColorMap).length} SNs`);
    render();

    // Publish event for left panel
    Mediator.publish(Mediator.EVENT_TYPES.COLORS_APPLY, { colorMap: currentColorMap, groups: currentGroups });
  }

  /**
   * Display "not parsed" message
   * @param {string} book
   * @param {number} chapter
   * @param {number} verse
   */
  function displayNotParsed(book, chapter, verse) {
    // Update verse reference display
    verseRefDisplay.textContent = `${book} ${chapter}:${verse}`;
    verseRefDisplay.style.display = 'block';

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
    Mediator.publish(Mediator.EVENT_TYPES.COLORS_APPLY, { colorMap: {} });
  }

  /**
   * Convert [3.x.x] spec references to tooltip spans
   * @param {string} text - Text containing spec references
   * @param {Object} specRefs - Spec references data { "3.3.2": { title, content } }
   * @returns {string} Text with tooltip spans
   */
  function addSpecTooltips(text, specRefs) {
    // Pattern to match spec references like [3.3.2], [3.4.4]
    return text.replace(/\[(\d+(?:\.\d+)+)\]/g, (match, refNum) => {
      const ref = specRefs[refNum];
      if (ref) {
        // Create span with only ref number - tooltip content comes from specRefs on hover
        return `<span class="spec-ref-tooltip" data-spec-ref="${refNum}">[${refNum}]</span>`;
      }
      return match;  // No tooltip for unknown references
    });
  }

  /**
   * Create or get the spec tooltip element
   */
  function getSpecTooltip() {
    if (!specTooltipElement) {
      specTooltipElement = document.createElement('div');
      specTooltipElement.className = 'spec-tooltip-container';
      specTooltipElement.style.display = 'none';
      document.body.appendChild(specTooltipElement);
    }
    return specTooltipElement;
  }

  /**
   * Show spec tooltip near the element
   * @param {HTMLElement} element - The spec-ref-tooltip element
   */
  function showSpecTooltip(element) {
    const refNum = element.dataset.specRef;
    const ref = currentSections.specRefs?.[refNum];
    if (!ref) return;

    const tooltip = getSpecTooltip();
    tooltip.innerHTML = `<div class="tooltip-title">[${refNum}] ${escapeHtml(ref.title)}</div><div class="tooltip-content">${escapeHtml(ref.content.trim())}</div>`;

    // Position tooltip above the element
    const rect = element.getBoundingClientRect();
    tooltip.style.display = 'block';

    // Calculate position
    const tooltipRect = tooltip.getBoundingClientRect();
    let top = rect.top - tooltipRect.height - 10;
    let left = rect.left;

    // Adjust if tooltip goes off screen
    if (top < 10) {
      top = rect.bottom + 10;  // Show below instead
    }
    if (left + tooltipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tooltipRect.width - 10;
    }
    if (left < 10) left = 10;

    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
  }

  /**
   * Hide spec tooltip
   */
  function hideSpecTooltip() {
    const tooltip = getSpecTooltip();
    tooltip.style.display = 'none';
  }

  /**
   * Attach hover listeners to spec tooltip spans
   */
  function attachSpecTooltipListeners() {
    if (!showSpec || !currentSections.specRefs) return;

    const spans = rightContent.querySelectorAll('.spec-ref-tooltip');
    spans.forEach(span => {
      span.addEventListener('mouseenter', () => showSpecTooltip(span));
      span.addEventListener('mouseleave', hideSpecTooltip);
    });
  }

  /**
   * Render right panel content
   */
  function render() {
    let html = '';

    // Warning for uncertain verses
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
      let coloredParsed = ColorMapper.applyColorsToParsedText(
        currentSections.parsed,
        currentGroups
      );

      // If spec tooltips enabled, convert [3.x.x] references to tooltip spans
      if (showSpec && currentSections.specRefs) {
        coloredParsed = addSpecTooltips(coloredParsed, currentSections.specRefs);
      }

      // Wrap each line in pre tag for monospace display
      const wrappedLines = coloredParsed.split('\n')
        .map(line => line.trim() ? '<pre class="parsed-line">' + line + '</pre>' : '')
        .join('');

      html += '<div class="parsed-section">' +
        '<div class="section-title">' + (currentSections.parsedTitle || 'Parsed and Formatted Text Section') + '</div>' +
        '<div class="parsed-content">' +
        wrappedLines +
        '</div>' +
        '</div>';
    }

    // Section 2: Raw UNV+SN Source Text
    if (showRaw && currentSections.raw) {
      const colorMap = ColorMapper.createSNToColorMap(currentGroups);
      const coloredRaw = ColorMapper.applyColorsToRawText(
        currentSections.raw.trim(),
        colorMap,
        currentGroups  // Pass groups for position-based coloring
      );

      html += `
        <div class="parsed-section">
          <div class="section-title">${currentSections.rawTitle || 'Raw UNV+SN Source Text Section'}</div>
          <div class="raw-text">${coloredRaw}</div>
        </div>
      `;

      // Add SN click handlers for Raw section after render
      setTimeout(() => addSNClickHandlersRaw(), 10);
    }

    // Add SN click handlers for Parsed section after first render
    if (showParsed && currentSections.parsed) {
      setTimeout(() => addSNClickHandlersParsed(), 10);
    }

    // Section 3: Morphology Notes
    if (showNotes && currentSections.notes) {
      html += `
        <div class="parsed-section">
          <div class="section-title">${currentSections.notesTitle || 'Morphology Notes Section'}</div>
          <div class="morphology-content">
            ${currentSections.notes.split('\n').map(line =>
              line.trim() ? `<div class="morphology-note">${escapeHtml(line)}</div>` : ''
            ).join('')}
          </div>
        </div>
      `;
    }

    rightContent.innerHTML = html || '<div class="loading-message">無資料可顯示</div>';

    // Attach spec tooltip listeners after render
    if (showSpec && currentSections.specRefs) {
      setTimeout(attachSpecTooltipListeners, 10);
    }
  }

  /**
   * Add SN click handlers to Parsed section groups
   */
  function addSNClickHandlersParsed() {
    rightContent.querySelectorAll('.sn-group').forEach(group => {
      group.addEventListener('click', (e) => {
        e.stopPropagation();
        // Extract all SN codes from the group
        const sns = ColorMapper.extractSNsFromLine(group.textContent);
        if (sns.length > 0) {
          Mediator.publish(Mediator.EVENT_TYPES.SN_CLICK, {
            source: 'right-parsed',
            element: group,
            snCode: sns[0],  // Primary SN
            groupSNs: sns,
            verse: currentVerse  // Add verse number for single-HL filtering
          });
        }
      });
    });
  }

  /**
   * Add SN click handlers to Raw section tags
   */
  function addSNClickHandlersRaw() {
    rightContent.querySelectorAll('.sn-tag').forEach(tag => {
      tag.addEventListener('click', (e) => {
        e.stopPropagation();
        const snCode = extractSNCode(tag.textContent);
        if (snCode) {
          // Get all SNs in the same group - pass the clicked element for position-based matching
          const groupSNs = ColorMapper.getSNGroupFromColorMap(snCode, currentColorMap, currentGroups, tag);

          Mediator.publish(Mediator.EVENT_TYPES.SN_CLICK, {
            source: 'right-raw',
            element: tag,
            snCode: snCode,
            groupSNs: groupSNs,
            verse: currentVerse  // Add verse number for single-HL filtering
          });
        }
      });
    });
  }

  /**
   * Extract SN code from tag text
   * @param {string} text
   * @returns {string|null}
   */
  function extractSNCode(text) {
    const match = text.match(/\d+/);
    return match ? match[0] : null;
  }

  /**
   * Escape HTML
   * @param {string} text
   * @returns {string}
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Escape text for use in HTML data attributes
   * More aggressive escaping including quotes and newlines
   * @param {string} text - Text to escape
   * @returns {string} Escaped text safe for data attributes
   */
  function escapeForAttribute(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/\n/g, '&#10;')
      .replace(/\r/g, '&#13;');
  }

  /**
   * Handle SN click for highlighting
   * @param {Object} event - {source, snCode, groupSNs, element, verse}
   */
  function handleSNClickForHighlighting(event) {
    const { source, groupSNs, verse } = event;

    console.log(`[RightPanel] SN click - singleHighlightMode=${singleHighlightMode}, source=${source}, verse=${verse}`);

    // Only clear previous highlighting if single highlight mode is ON
    if (singleHighlightMode) {
      console.log('[RightPanel] Clearing previous highlights (Single HL is ON)');
      clearHighlighting();
    } else {
      console.log('[RightPanel] Keeping previous highlights (Single HL is OFF)');
    }

    if (source && source.startsWith('right-')) {
      // Clicked in right panel - highlight local (blue)
      highlightParsedLocal(groupSNs);
      highlightRawLocal(groupSNs);
    } else {
      // Clicked in left panel - highlight remote (orange)
      highlightParsedRemote(groupSNs);
      highlightRawRemote(groupSNs);
    }
  }

  /**
   * Clear all highlighting classes
   */
  function clearHighlighting() {
    rightContent.querySelectorAll('.clicked-local, .clicked-remote').forEach(el => {
      el.classList.remove('clicked-local', 'clicked-remote');
    });
  }

  /**
   * Highlight Parsed section locally (blue)
   */
  function highlightParsedLocal(groupSNs) {
    const elements = ColorMapper.findCorrespondingElements(groupSNs, rightContent, '.sn-group', currentGroups);
    elements.forEach(el => el.classList.add('clicked-local'));
  }

  /**
   * Highlight Parsed section remotely (orange)
   */
  function highlightParsedRemote(groupSNs) {
    const elements = ColorMapper.findCorrespondingElements(groupSNs, rightContent, '.sn-group', currentGroups);
    elements.forEach(el => el.classList.add('clicked-remote'));
  }

  /**
   * Highlight Raw section locally (blue)
   */
  function highlightRawLocal(groupSNs) {
    const elements = ColorMapper.findCorrespondingElements(groupSNs, rightContent, '.sn-tag', currentGroups);
    elements.forEach(el => el.classList.add('clicked-local'));
  }

  /**
   * Highlight Raw section remotely (orange)
   */
  function highlightRawRemote(groupSNs) {
    const elements = ColorMapper.findCorrespondingElements(groupSNs, rightContent, '.sn-tag', currentGroups);
    elements.forEach(el => el.classList.add('clicked-remote'));
  }

  /**
   * Clear right panel
   */
  function clear() {
    currentSections = { parsed: '', raw: '', notes: '' };
    currentGroups = [];
    currentColorMap = {};
    rightContent.innerHTML = '<div class="loading-message">請點擊左側節次以查看解析結果...</div>';
    verseRefDisplay.style.display = 'none';
    uncertainBadge.style.display = 'none';
    rightPanel.classList.remove('uncertain');
  }

  // Public API
  return {
    init,
    clear
  };
})();
