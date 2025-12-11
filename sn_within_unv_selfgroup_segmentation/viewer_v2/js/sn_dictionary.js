/**
 * sn_dictionary.js
 * Strong's Dictionary lookup with hover-style floating tooltip display
 * v2.0: Dual panel support with auto-show on highlight
 */

const SNDictionary = (() => {
  // localStorage keys for panel-specific settings
  const STORAGE_KEY_LEFT_ENABLED = 'viewer_v2_left_sn_dict_enabled';
  const STORAGE_KEY_RIGHT_ENABLED = 'viewer_v2_right_sn_dict_enabled';

  // Dictionary cache (individual lookups)
  const dictCache = {};

  // Full dictionary data (loaded once)
  let otDictData = null;
  let ntDictData = null;
  let otDictLoading = null;
  let ntDictLoading = null;

  // State for each panel
  let leftEnabled = false;
  let rightEnabled = false;

  // Floating tooltip elements - one for each panel (independent)
  let leftTooltip = null;
  let rightTooltip = null;

  // Highlight timeout management (10 seconds)
  const HIGHLIGHT_TIMEOUT_MS = 10000;
  let highlightTimeoutId = null;

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
      console.warn(`[SNDictionary] Failed to load setting ${key}:`, e);
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
      console.warn(`[SNDictionary] Failed to save setting ${key}:`, e);
    }
  }

  /**
   * Initialize dictionary (subscribe to events and set up checkboxes)
   */
  function init() {
    // Load saved settings
    leftEnabled = loadSetting(STORAGE_KEY_LEFT_ENABLED, false);
    rightEnabled = loadSetting(STORAGE_KEY_RIGHT_ENABLED, false);
    console.log(`[SNDictionary] Left enabled: ${leftEnabled}, Right enabled: ${rightEnabled}`);

    // Initialize left panel checkbox
    const leftCheckbox = document.getElementById('left-sn-dict-toggle');
    if (leftCheckbox) {
      leftCheckbox.checked = leftEnabled;
      leftCheckbox.addEventListener('change', (e) => {
        leftEnabled = e.target.checked;
        saveSetting(STORAGE_KEY_LEFT_ENABLED, leftEnabled);
        console.log(`[SNDictionary] Left panel SN Dict: ${leftEnabled ? 'enabled' : 'disabled'}`);
        if (!leftEnabled) {
          hideFloatingTooltip();
        }
      });
    }

    // Initialize right panel checkbox
    const rightCheckbox = document.getElementById('right-sn-dict-toggle');
    if (rightCheckbox) {
      rightCheckbox.checked = rightEnabled;
      rightCheckbox.addEventListener('change', (e) => {
        rightEnabled = e.target.checked;
        saveSetting(STORAGE_KEY_RIGHT_ENABLED, rightEnabled);
        console.log(`[SNDictionary] Right panel SN Dict: ${rightEnabled ? 'enabled' : 'disabled'}`);
        if (!rightEnabled) {
          hideFloatingTooltip();
        }
      });
    }

    // Create floating tooltip elements for both panels
    createFloatingTooltips();

    // Subscribe to SN click events for auto-show tooltip
    Mediator.subscribe(Mediator.EVENT_TYPES.SN_CLICK, handleSNHighlight);

    console.log('[SNDictionary] Initialized with dual panel support');
  }

  /**
   * Create floating tooltip elements for both panels
   */
  function createFloatingTooltips() {
    if (!leftTooltip) {
      leftTooltip = document.createElement('div');
      leftTooltip.className = 'sn-dict-floating-tooltip sn-tooltip-left';
      leftTooltip.style.display = 'none';
      document.body.appendChild(leftTooltip);
    }
    if (!rightTooltip) {
      rightTooltip = document.createElement('div');
      rightTooltip.className = 'sn-dict-floating-tooltip sn-tooltip-right';
      rightTooltip.style.display = 'none';
      document.body.appendChild(rightTooltip);
    }
  }

  /**
   * Handle SN highlight event - auto-show tooltip if panel's SN Dict is enabled
   * BOTH panels can show tooltips independently when both checkboxes are enabled
   * @param {Object} data - {source, element, snCode, groupSNs, verse}
   */
  async function handleSNHighlight(data) {
    const { source, element, snCode, groupSNs } = data;

    // Determine which panel the click originated from
    const isLeftPanelSource = source === 'left';
    const isRightPanelSource = source && source.startsWith('right-');

    // Reset highlight timeout
    resetHighlightTimeout();

    // Get the primary SN code
    const primarySN = snCode || (groupSNs && groupSNs[0]);
    if (!primarySN) return;

    console.log(`[SNDictionary] Handling highlight: source=${source}, leftEnabled=${leftEnabled}, rightEnabled=${rightEnabled}`);

    // Show tooltips on BOTH panels independently (not mutually exclusive)

    // LEFT panel tooltip:
    // - If click from left AND left enabled → show on source element (blue)
    // - If click from right AND left enabled → show on receiving element (orange)
    if (leftEnabled) {
      if (isLeftPanelSource) {
        console.log('[SNDictionary] Showing LEFT tooltip (local/blue highlight)');
        await showTooltipForPanel('left', element, primarySN);
      } else if (isRightPanelSource) {
        // Wait for orange highlights to be applied, then find element in left panel
        setTimeout(async () => {
          console.log('[SNDictionary] Looking for highlighted element in LEFT panel (remote/orange)...');
          const leftElement = findHighlightedElementInPanel('left', groupSNs);
          if (leftElement) {
            await showTooltipForPanel('left', leftElement, primarySN);
          } else {
            console.log('[SNDictionary] No element found in LEFT panel for tooltip');
            hideTooltipForPanel('left');
          }
        }, 50);
      }
    } else {
      hideTooltipForPanel('left');
    }

    // RIGHT panel tooltip:
    // - If click from right AND right enabled → show on source element (blue)
    // - If click from left AND right enabled → show on receiving element (orange)
    if (rightEnabled) {
      if (isRightPanelSource) {
        console.log('[SNDictionary] Showing RIGHT tooltip (local/blue highlight)');
        await showTooltipForPanel('right', element, primarySN);
      } else if (isLeftPanelSource) {
        // Wait for orange highlights to be applied, then find element in right panel
        setTimeout(async () => {
          console.log('[SNDictionary] Looking for highlighted element in RIGHT panel (remote/orange)...');
          const rightElement = findHighlightedElementInPanel('right', groupSNs);
          if (rightElement) {
            await showTooltipForPanel('right', rightElement, primarySN);
          } else {
            console.log('[SNDictionary] No element found in RIGHT panel for tooltip');
            hideTooltipForPanel('right');
          }
        }, 50);
      }
    } else {
      hideTooltipForPanel('right');
    }

    // If neither panel is enabled, log it
    if (!leftEnabled && !rightEnabled) {
      console.log('[SNDictionary] SN Dict disabled for both panels, no tooltips shown');
    }
  }

  /**
   * Show tooltip for a specific panel
   * @param {string} panel - 'left' or 'right'
   * @param {HTMLElement} element
   * @param {string} primarySN
   */
  async function showTooltipForPanel(panel, element, primarySN) {
    const tooltip = panel === 'left' ? leftTooltip : rightTooltip;
    if (!tooltip) {
      createFloatingTooltips();
    }

    console.log(`[SNDictionary] showTooltipForPanel: panel=${panel}, SN=${primarySN}`);

    // Show loading state
    showLoadingTooltipForPanel(panel, element);

    // Fetch definition
    const definition = await fetchDefinition(primarySN);

    // Show definition or error
    if (definition) {
      showDefinitionTooltipForPanel(panel, element, primarySN, definition);
    } else {
      showErrorTooltipForPanel(panel, element, primarySN);
    }
  }

  /**
   * Hide tooltip for a specific panel
   * @param {string} panel - 'left' or 'right'
   */
  function hideTooltipForPanel(panel) {
    const tooltip = panel === 'left' ? leftTooltip : rightTooltip;
    if (tooltip) {
      tooltip.style.display = 'none';
    }
  }

  /**
   * Show loading tooltip for a specific panel
   * @param {string} panel - 'left' or 'right'
   * @param {HTMLElement} element
   */
  function showLoadingTooltipForPanel(panel, element) {
    const tooltip = panel === 'left' ? leftTooltip : rightTooltip;
    if (!tooltip) return;

    tooltip.innerHTML = `
      <div class="tooltip-loading">
        <div class="mini-spinner"></div>
        <div>載入中...</div>
      </div>
    `;

    positionTooltipForPanel(panel, element);
    tooltip.style.display = 'block';
  }

  /**
   * Show definition tooltip for a specific panel
   * @param {string} panel - 'left' or 'right'
   * @param {HTMLElement} element
   * @param {string} snCode
   * @param {Object} definition
   */
  function showDefinitionTooltipForPanel(panel, element, snCode, definition) {
    const tooltip = panel === 'left' ? leftTooltip : rightTooltip;
    if (!tooltip) return;

    const prefix = definition.testament === 'ot' ? 'H' : 'G';

    // Build meta section (part of speech and TWOT)
    let metaHtml = '';
    if (definition.partOfSpeech || definition.twot) {
      const posHtml = definition.partOfSpeech ? `<span class="tooltip-pos">${definition.partOfSpeech}</span>` : '';
      const twotHtml = definition.twot ? `<span class="tooltip-twot">TWOT ${definition.twot}</span>` : '';
      metaHtml = `<div class="tooltip-meta">${posHtml}${twotHtml}</div>`;
    }

    // Build definitions list
    let defsHtml = '';
    if (definition.definitions && definition.definitions.length > 0) {
      const defItems = definition.definitions.map(d => {
        const className = d.level === 0 ? 'tooltip-def-item' : 'tooltip-subdef';
        return `<div class="${className}">${d.text}</div>`;
      }).join('');
      defsHtml = `<div class="tooltip-def-list">${defItems}</div>`;
    } else if (definition.definition) {
      // Fallback to legacy single definition
      defsHtml = `<div class="tooltip-def">${definition.definition}</div>`;
    }

    tooltip.innerHTML = `
      <span class="tooltip-sn">${prefix}${snCode}</span>
      <div class="tooltip-word">${definition.word}</div>
      <div class="tooltip-translit">${definition.transliteration}</div>
      <div class="tooltip-divider"></div>
      ${metaHtml}
      ${defsHtml}
    `;

    positionTooltipForPanel(panel, element);
    tooltip.style.display = 'block';
  }

  /**
   * Show error tooltip for a specific panel
   * @param {string} panel - 'left' or 'right'
   * @param {HTMLElement} element
   * @param {string} snCode
   */
  function showErrorTooltipForPanel(panel, element, snCode) {
    const tooltip = panel === 'left' ? leftTooltip : rightTooltip;
    if (!tooltip) return;

    tooltip.innerHTML = `
      <div class="tooltip-error">
        <div>無法載入字典資料</div>
        <div style="font-family: monospace; margin-top: 4px;">${snCode}</div>
      </div>
    `;

    positionTooltipForPanel(panel, element);
    tooltip.style.display = 'block';
  }

  /**
   * Position tooltip for a specific panel
   * @param {string} panel - 'left' or 'right'
   * @param {HTMLElement} element
   */
  function positionTooltipForPanel(panel, element) {
    const tooltip = panel === 'left' ? leftTooltip : rightTooltip;
    if (!tooltip || !element) {
      console.log(`[SNDictionary] positionTooltipForPanel: missing tooltip or element for ${panel}`);
      return;
    }

    const rect = element.getBoundingClientRect();
    console.log(`[SNDictionary] ${panel} element rect: top=${rect.top.toFixed(0)}, left=${rect.left.toFixed(0)}, bottom=${rect.bottom.toFixed(0)}`);

    // Position above the element by default
    let top = rect.top - 10;
    let left = rect.left;

    // Show tooltip temporarily to get dimensions
    tooltip.style.visibility = 'hidden';
    tooltip.style.display = 'block';
    const tooltipRect = tooltip.getBoundingClientRect();
    tooltip.style.visibility = 'visible';

    // Adjust top to be above tooltip
    top = rect.top - tooltipRect.height - 10;

    // If would go off top of screen, show below instead
    if (top < 10) {
      top = rect.bottom + 10;
    }

    // Adjust left if would go off right edge
    if (left + tooltipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tooltipRect.width - 10;
    }

    // Ensure doesn't go off left edge
    if (left < 10) {
      left = 10;
    }

    console.log(`[SNDictionary] Positioning ${panel} tooltip at: top=${top.toFixed(0)}, left=${left.toFixed(0)}`);
    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
  }

  // DEPRECATED: Keep old functions for backwards compatibility
  /**
   * Show tooltip for a specific element (deprecated - use showTooltipForPanel)
   * @param {HTMLElement} element
   * @param {string} primarySN
   */
  async function showTooltipForElement(element, primarySN) {
    // Default to left tooltip for backwards compatibility
    await showTooltipForPanel('left', element, primarySN);
  }

  /**
   * Find highlighted element in a panel (for remote/orange highlighting)
   * @param {string} panel - 'left' or 'right'
   * @param {string[]} groupSNs - Array of SN codes to look for
   * @returns {HTMLElement|null}
   */
  function findHighlightedElementInPanel(panel, groupSNs) {
    const container = panel === 'left'
      ? document.getElementById('left-content')
      : document.getElementById('right-content');

    if (!container) {
      console.log(`[SNDictionary] Container not found for panel: ${panel}`);
      return null;
    }

    // Look for elements with clicked-remote class (orange highlight)
    const remoteHighlighted = container.querySelector('.clicked-remote');
    if (remoteHighlighted) {
      const rect = remoteHighlighted.getBoundingClientRect();
      console.log(`[SNDictionary] Found .clicked-remote element in ${panel} panel at (${rect.left.toFixed(0)}, ${rect.top.toFixed(0)})`);
      return remoteHighlighted;
    }

    console.log(`[SNDictionary] No .clicked-remote found in ${panel} panel, trying fallback...`);

    // Fallback: find any SN tag with matching SN code
    if (groupSNs && groupSNs.length > 0) {
      const snTags = container.querySelectorAll('.sn-tag, .sn-group');
      for (const tag of snTags) {
        const text = tag.textContent;
        for (const sn of groupSNs) {
          if (text.includes(sn)) {
            const rect = tag.getBoundingClientRect();
            console.log(`[SNDictionary] Fallback: found SN tag with ${sn} at (${rect.left.toFixed(0)}, ${rect.top.toFixed(0)})`);
            return tag;
          }
        }
      }
    }

    console.log(`[SNDictionary] No element found for tooltip in ${panel} panel`);
    return null;
  }

  /**
   * Reset the highlight timeout (called on each new highlight action)
   */
  function resetHighlightTimeout() {
    // Clear existing timeout
    if (highlightTimeoutId) {
      clearTimeout(highlightTimeoutId);
      highlightTimeoutId = null;
    }

    // Set new timeout
    highlightTimeoutId = setTimeout(() => {
      console.log('[SNDictionary] Highlight timeout - clearing highlights and tooltip');
      clearAllHighlightsAndTooltip();
    }, HIGHLIGHT_TIMEOUT_MS);
  }

  /**
   * Clear all highlights and hide tooltips (synchronized cleanup)
   */
  function clearAllHighlightsAndTooltip() {
    // 1. Clear blue (local) highlights
    document.querySelectorAll('.clicked-local').forEach(el => {
      el.classList.remove('clicked-local');
    });

    // 2. Clear orange (remote) highlights
    document.querySelectorAll('.clicked-remote').forEach(el => {
      el.classList.remove('clicked-remote');
    });

    // 3. Clear keyboard selection
    document.querySelectorAll('.keyboard-selected').forEach(el => {
      el.classList.remove('keyboard-selected');
    });

    // 4. Hide both tooltips
    hideTooltipForPanel('left');
    hideTooltipForPanel('right');

    // Clear timeout ID
    highlightTimeoutId = null;
  }

  /**
   * Fetch Strong's definition with caching
   * @param {string} snCode - Strong's number (e.g., "07225" or "5316")
   * @returns {Promise<Object|null>}
   */
  async function fetchDefinition(snCode) {
    // Normalize snCode to padded format (e.g., "1234" -> "01234")
    const paddedCode = snCode.padStart(5, '0');

    // Check cache first
    if (dictCache[paddedCode]) {
      console.log(`[SNDictionary] Definition for ${paddedCode} from cache`);
      return dictCache[paddedCode];
    }

    try {
      // Determine if Hebrew or Greek
      // Hebrew: 1-8674 (core), 8000-8999 (morphology), 09000-09999 (prefixes)
      // Greek: starts fresh 1-5624 but in our dict stored differently
      // Key insight: 09xxx codes are Hebrew prefixes (5-digit starting with 09)
      const num = parseInt(snCode);
      const is09xxPrefix = paddedCode.startsWith('09') && paddedCode.length === 5;
      // Greek Strong's numbers in NT are typically stored as-is (1-5624)
      // but our NT file has different numbering - let's check the actual range
      // For now: 09xxx = Hebrew prefix, others < 9000 = Hebrew, else = error (no lookup)
      const testament = is09xxPrefix ? 'ot' : (num < 9000 ? 'ot' : 'nt');

      console.log(`[SNDictionary] Looking up ${paddedCode} in ${testament} dictionary`);

      // Load full dictionary if not already loaded
      const dictData = await loadFullDictionary(testament);

      if (dictData) {
        // Find entry by SN code
        const entry = dictData.find(e => e.sn === paddedCode);
        if (entry) {
          // Transform to our format with enhanced content
          const definition = {
            sn: paddedCode,
            word: entry.orig || '',
            transliteration: extractTransliteration(entry.dic_text),
            partOfSpeech: extractPartOfSpeech(entry.dic_text),
            twot: extractTWOT(entry.dic_text),
            definitions: extractFullDefinitions(entry.dic_text),
            definition: extractDefinition(entry.dic_text), // Legacy field for backwards compatibility
            testament
          };
          dictCache[paddedCode] = definition;
          console.log(`[SNDictionary] Found definition for ${paddedCode}: ${entry.orig}`);
          return definition;
        }
      }

      // Not found - return error indicator
      console.log(`[SNDictionary] No definition found for ${paddedCode}`);
      return null;

    } catch (error) {
      console.error(`[SNDictionary] Error fetching definition for ${snCode}:`, error);
      return null;
    }
  }

  /**
   * Load full dictionary file (cached)
   * @param {string} testament - 'ot' or 'nt'
   * @returns {Promise<Array|null>}
   */
  async function loadFullDictionary(testament) {
    // Return cached data if available
    if (testament === 'ot' && otDictData) return otDictData;
    if (testament === 'nt' && ntDictData) return ntDictData;

    // Return existing loading promise if in progress
    if (testament === 'ot' && otDictLoading) return otDictLoading;
    if (testament === 'nt' && ntDictLoading) return ntDictLoading;

    // Start loading
    const filename = testament === 'ot'
      ? 'strong_number_words_dict_1_9015_ot.json'
      : 'strong_number_words_dict_1_7008_nt.json';
    // Use local symlink (viewer_v2/strong_dict_json -> ../../original_text_preparation/strong_dict_json)
    // Path is relative to index.html, not to this JS file
    const path = `strong_dict_json/${filename}`;

    console.log(`[SNDictionary] Loading ${testament} dictionary from ${path}`);

    const loadPromise = (async () => {
      try {
        const response = await fetch(path);
        if (!response.ok) {
          console.error(`[SNDictionary] Failed to load ${testament} dictionary: ${response.status}`);
          return null;
        }
        const data = await response.json();
        console.log(`[SNDictionary] Loaded ${testament} dictionary with ${data.length} entries`);
        return data;
      } catch (error) {
        console.error(`[SNDictionary] Error loading ${testament} dictionary:`, error);
        return null;
      }
    })();

    // Cache the promise
    if (testament === 'ot') {
      otDictLoading = loadPromise;
      otDictData = await loadPromise;
      otDictLoading = null;
      return otDictData;
    } else {
      ntDictLoading = loadPromise;
      ntDictData = await loadPromise;
      ntDictLoading = null;
      return ntDictData;
    }
  }

  /**
   * Extract transliteration from dic_text
   * @param {string} dicText
   * @returns {string}
   */
  function extractTransliteration(dicText) {
    if (!dicText) return '';
    // Format: "01 'ab {a:v}\n\n..." - extract the part in {}
    const match = dicText.match(/\{([^}]+)\}/);
    return match ? match[1] : '';
  }

  /**
   * Extract part of speech from dic_text
   * @param {string} dicText
   * @returns {string}
   */
  function extractPartOfSpeech(dicText) {
    if (!dicText) return '';
    // Look for patterns like "陽性名詞", "動詞", "形容詞", "陰性名詞", "副詞"
    const patterns = [
      /[；;]\s*(陽性名詞|陰性名詞|陽性複數名詞|陰性複數名詞|名詞)/,
      /[；;]\s*(動詞)/,
      /[；;]\s*(形容詞)/,
      /[；;]\s*(副詞)/,
      /[；;]\s*(介系詞|依附介系詞)/,
      /[；;]\s*(連接詞)/,
      /[；;]\s*(感嘆詞)/,
      /[；;]\s*(代名詞)/,
      /[；;]\s*(數詞)/,
      /[；;]\s*(冠詞)/,
    ];

    for (const pattern of patterns) {
      const match = dicText.match(pattern);
      if (match) return match[1];
    }
    return '';
  }

  /**
   * Extract TWOT reference from dic_text
   * @param {string} dicText
   * @returns {string}
   */
  function extractTWOT(dicText) {
    if (!dicText) return '';
    // Look for "TWOT - XXX" or "TWOT -XXX"
    const match = dicText.match(/TWOT\s*[-–]\s*(\d+[a-z]?(?:,\s*\d+[a-z]?)*)/i);
    return match ? match[1] : '';
  }

  /**
   * Extract full definitions from dic_text (including sub-definitions)
   * @param {string} dicText
   * @returns {Array<{level: number, text: string}>}
   */
  function extractFullDefinitions(dicText) {
    if (!dicText) return [];

    const lines = dicText.split('\n');
    const definitions = [];
    let inDefinitions = false;

    for (const line of lines) {
      const trimmed = line.trim();

      // Start capturing when we see "1)" pattern
      if (trimmed.match(/^1\)/)) {
        inDefinitions = true;
      }

      if (inDefinitions) {
        // Main definition: "1)", "2)", etc.
        if (trimmed.match(/^\d+\)/)) {
          definitions.push({ level: 0, text: trimmed });
        }
        // Sub-definition: "1a)", "1b)", "2a)", etc.
        else if (trimmed.match(/^\d+[a-z]\)/)) {
          definitions.push({ level: 1, text: trimmed });
        }
        // Sub-sub-definition: "1a1)", "1a2)", etc.
        else if (trimmed.match(/^\d+[a-z]\d+[a-z]?\)/)) {
          definitions.push({ level: 2, text: trimmed });
        }
        // Stop if we hit another section marker or empty content
        else if (trimmed.length === 0 && definitions.length > 0) {
          // Allow one blank line
        }
        else if (trimmed.match(/^[A-Z]/) && !trimmed.match(/^\d/)) {
          // Likely a new section (e.g., "AV -"), stop
          break;
        }
      }
    }

    // Limit to reasonable number of definitions
    return definitions.slice(0, 15);
  }

  /**
   * Extract definition summary from dic_text (legacy - single line)
   * @param {string} dicText
   * @returns {string}
   */
  function extractDefinition(dicText) {
    if (!dicText) return '';
    // Get the first meaningful definition line (usually after "欽定本 - ...")
    const lines = dicText.split('\n');

    // Look for numbered definitions like "1) ..."
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.match(/^1\)/)) {
        return trimmed;
      }
    }

    // Fallback: get first non-empty line after header info
    for (let i = 0; i < lines.length; i++) {
      const trimmed = lines[i].trim();
      if (trimmed && !trimmed.match(/^[\d]+\s/) && !trimmed.includes('{') && !trimmed.includes('TWOT')) {
        if (trimmed.length > 10 && !trimmed.startsWith('欽定本')) {
          return trimmed.substring(0, 100);
        }
      }
    }

    return '';
  }

  /**
   * Show loading tooltip near the highlighted element
   * @param {HTMLElement} element
   */
  function showLoadingTooltip(element) {
    if (!floatingTooltip) createFloatingTooltip();

    floatingTooltip.innerHTML = `
      <div class="tooltip-loading">
        <div class="mini-spinner"></div>
        <div>載入中...</div>
      </div>
    `;

    positionFloatingTooltip(element);
    floatingTooltip.style.display = 'block';
  }

  /**
   * Show definition in floating tooltip
   * @param {HTMLElement} element
   * @param {string} snCode
   * @param {Object} definition
   */
  function showDefinitionTooltip(element, snCode, definition) {
    if (!floatingTooltip) createFloatingTooltip();

    const prefix = definition.testament === 'ot' ? 'H' : 'G';

    floatingTooltip.innerHTML = `
      <span class="tooltip-sn">${prefix}${snCode}</span>
      <div class="tooltip-word">${definition.word}</div>
      <div class="tooltip-translit">${definition.transliteration}</div>
      <div class="tooltip-def">${definition.definition}</div>
    `;

    positionFloatingTooltip(element);
    floatingTooltip.style.display = 'block';
  }

  /**
   * Show error in floating tooltip
   * @param {HTMLElement} element
   * @param {string} snCode
   */
  function showErrorTooltip(element, snCode) {
    if (!floatingTooltip) createFloatingTooltip();

    floatingTooltip.innerHTML = `
      <div class="tooltip-error">
        <div>無法載入字典資料</div>
        <div style="font-family: monospace; margin-top: 4px;">${snCode}</div>
      </div>
    `;

    positionFloatingTooltip(element);
    floatingTooltip.style.display = 'block';
  }

  /**
   * Position floating tooltip near the element
   * @param {HTMLElement} element
   */
  function positionFloatingTooltip(element) {
    if (!floatingTooltip || !element) {
      console.log('[SNDictionary] positionFloatingTooltip: missing tooltip or element');
      return;
    }

    const rect = element.getBoundingClientRect();
    console.log(`[SNDictionary] Element rect: top=${rect.top.toFixed(0)}, left=${rect.left.toFixed(0)}, bottom=${rect.bottom.toFixed(0)}`);

    // Position above the element by default
    let top = rect.top - 10;
    let left = rect.left;

    // Show tooltip temporarily to get dimensions
    floatingTooltip.style.visibility = 'hidden';
    floatingTooltip.style.display = 'block';
    const tooltipRect = floatingTooltip.getBoundingClientRect();
    floatingTooltip.style.visibility = 'visible';

    // Adjust top to be above tooltip
    top = rect.top - tooltipRect.height - 10;

    // If would go off top of screen, show below instead
    if (top < 10) {
      top = rect.bottom + 10;
    }

    // Adjust left if would go off right edge
    if (left + tooltipRect.width > window.innerWidth - 10) {
      left = window.innerWidth - tooltipRect.width - 10;
    }

    // Ensure doesn't go off left edge
    if (left < 10) {
      left = 10;
    }

    console.log(`[SNDictionary] Positioning tooltip at: top=${top.toFixed(0)}, left=${left.toFixed(0)}`);
    floatingTooltip.style.top = `${top}px`;
    floatingTooltip.style.left = `${left}px`;
  }

  /**
   * Hide all floating tooltips (for backwards compatibility and checkbox toggle)
   */
  function hideFloatingTooltip() {
    hideTooltipForPanel('left');
    hideTooltipForPanel('right');
  }

  /**
   * Get left panel enabled state
   * @returns {boolean}
   */
  function isLeftEnabled() {
    return leftEnabled;
  }

  /**
   * Get right panel enabled state
   * @returns {boolean}
   */
  function isRightEnabled() {
    return rightEnabled;
  }

  /**
   * Manually clear highlights and tooltip (for external calls)
   */
  function clearHighlights() {
    if (highlightTimeoutId) {
      clearTimeout(highlightTimeoutId);
      highlightTimeoutId = null;
    }
    clearAllHighlightsAndTooltip();
  }

  // Public API
  return {
    init,
    fetchDefinition,
    hideFloatingTooltip,
    isLeftEnabled,
    isRightEnabled,
    clearHighlights,
    resetHighlightTimeout
  };
})();
