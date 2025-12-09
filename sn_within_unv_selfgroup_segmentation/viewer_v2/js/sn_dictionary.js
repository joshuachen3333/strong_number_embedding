/**
 * sn_dictionary.js
 * Strong's Dictionary lookup with tooltip display
 */

const SNDictionary = (() => {
  // localStorage key
  const STORAGE_KEY_ENABLED = 'viewer_v2_sn_tooltip_enabled';

  // Dictionary cache
  const dictCache = {};

  let currentTooltip = null;
  let tooltipEnabled = false; // Default OFF

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
   * Initialize dictionary (subscribe to click events)
   */
  function init() {
    // Load saved setting
    tooltipEnabled = loadSetting(STORAGE_KEY_ENABLED, false);
    console.log(`[SNDictionary] Tooltip enabled: ${tooltipEnabled}`);

    // Initialize checkbox
    const checkbox = document.getElementById('sn-dict-toggle');
    if (checkbox) {
      checkbox.checked = tooltipEnabled;
      checkbox.addEventListener('change', (e) => {
        tooltipEnabled = e.target.checked;
        saveSetting(STORAGE_KEY_ENABLED, tooltipEnabled);
        console.log(`[SNDictionary] Tooltip ${tooltipEnabled ? 'enabled' : 'disabled'}`);
        if (!tooltipEnabled) {
          hideTooltip();
        }
      });
    }

    // Subscribe to SN click events
    Mediator.subscribe(Mediator.EVENT_TYPES.SN_CLICK, handleSNClick);

    // Global click handler to close tooltip
    document.addEventListener('click', (e) => {
      if (currentTooltip && !currentTooltip.contains(e.target) && !e.target.classList.contains('sn-tag')) {
        hideTooltip();
      }
    });
  }

  /**
   * Handle SN click event from mediator
   * @param {Object} data - {element, snCode}
   */
  async function handleSNClick(data) {
    // Check if tooltip is enabled
    if (!tooltipEnabled) {
      console.log('[SNDictionary] Tooltip disabled, skipping');
      return;
    }

    const { element, snCode } = data;

    // If clicking same element, hide tooltip
    if (currentTooltip && currentTooltip.dataset.snCode === snCode) {
      hideTooltip();
      return;
    }

    // Hide existing tooltip
    hideTooltip();

    // Show loading tooltip
    showLoadingTooltip(element, snCode);

    // Fetch definition
    const definition = await fetchDefinition(snCode);

    // Update tooltip with definition
    if (definition) {
      showDefinitionTooltip(element, snCode, definition);
    } else {
      showErrorTooltip(element, snCode);
    }
  }

  /**
   * Fetch Strong's definition with caching
   * @param {string} snCode - Strong's number (e.g., "07225" or "5316")
   * @returns {Promise<Object|null>}
   */
  async function fetchDefinition(snCode) {
    // Check cache
    if (dictCache[snCode]) {
      console.log(`[SNDictionary] Definition for ${snCode} from cache`);
      return dictCache[snCode];
    }

    try {
      // Determine if Hebrew (1-8999) or Greek (9000+)
      const num = parseInt(snCode);
      const testament = num < 9000 ? 'ot' : 'nt';

      // Try local JSON first
      const localDef = await tryFetchLocal(snCode, testament);
      if (localDef) {
        dictCache[snCode] = localDef;
        return localDef;
      }

      // TODO: Fallback to FHL API if needed
      // For now, return mock data
      const mockDef = {
        sn: snCode,
        word: testament === 'ot' ? 'רֵאשִׁית' : 'ἀγάπη',
        transliteration: testament === 'ot' ? 'rēʾšîṯ' : 'agapē',
        definition: testament === 'ot' ?
          '名詞：開始、起初、首要' :
          '名詞：愛、神聖的愛',
        testament
      };

      dictCache[snCode] = mockDef;
      return mockDef;

    } catch (error) {
      console.error(`Error fetching definition for ${snCode}:`, error);
      return null;
    }
  }

  /**
   * Try to fetch from local JSON
   * @param {string} snCode
   * @param {string} testament - 'ot' or 'nt'
   * @returns {Promise<Object|null>}
   */
  async function tryFetchLocal(snCode, testament) {
    try {
      // Path to local dictionary JSON
      const path = `../strong_dict_json/${testament}/${snCode}.json`;
      const response = await fetch(path);
      if (!response.ok) return null;
      return await response.json();
    } catch (error) {
      return null;
    }
  }

  /**
   * Show loading tooltip
   * @param {HTMLElement} element
   * @param {string} snCode
   */
  function showLoadingTooltip(element, snCode) {
    const tooltip = createTooltip(snCode);
    tooltip.innerHTML = `
      <div class="tooltip-loading">
        <div class="mini-spinner"></div>
        <div>載入中...</div>
      </div>
    `;
    positionTooltip(tooltip, element);
    document.body.appendChild(tooltip);
    currentTooltip = tooltip;
  }

  /**
   * Show definition tooltip
   * @param {HTMLElement} element
   * @param {string} snCode
   * @param {Object} definition
   */
  function showDefinitionTooltip(element, snCode, definition) {
    if (!currentTooltip) {
      currentTooltip = createTooltip(snCode);
      document.body.appendChild(currentTooltip);
    }

    const prefix = definition.testament === 'ot' ? 'H' : 'G';

    currentTooltip.innerHTML = `
      <div class="tooltip-header">
        <span class="tooltip-sn">${prefix}${snCode}</span>
        <button class="tooltip-close" onclick="SNDictionary.hideTooltip()">×</button>
      </div>
      <div class="tooltip-body">
        <div class="tooltip-word">${definition.word}</div>
        <div class="tooltip-translit">${definition.transliteration}</div>
        <div class="tooltip-def">${definition.definition}</div>
      </div>
    `;

    positionTooltip(currentTooltip, element);
  }

  /**
   * Show error tooltip
   * @param {HTMLElement} element
   * @param {string} snCode
   */
  function showErrorTooltip(element, snCode) {
    if (!currentTooltip) {
      currentTooltip = createTooltip(snCode);
      document.body.appendChild(currentTooltip);
    }

    currentTooltip.innerHTML = `
      <div class="tooltip-error">
        <div>無法載入字典資料</div>
        <div class="tooltip-sn-code">${snCode}</div>
      </div>
    `;

    positionTooltip(currentTooltip, element);
  }

  /**
   * Create tooltip element
   * @param {string} snCode
   * @returns {HTMLElement}
   */
  function createTooltip(snCode) {
    const tooltip = document.createElement('div');
    tooltip.className = 'sn-tooltip';
    tooltip.dataset.snCode = snCode;
    return tooltip;
  }

  /**
   * Position tooltip near element
   * @param {HTMLElement} tooltip
   * @param {HTMLElement} element
   */
  function positionTooltip(tooltip, element) {
    const rect = element.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;

    // Position below element
    let top = rect.bottom + scrollTop + 5;
    let left = rect.left + scrollLeft;

    // Adjust if off-screen
    tooltip.style.position = 'absolute';
    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
    tooltip.style.zIndex = '1000';

    // Wait for render to check bounds
    setTimeout(() => {
      const tooltipRect = tooltip.getBoundingClientRect();
      if (tooltipRect.right > window.innerWidth) {
        tooltip.style.left = `${window.innerWidth - tooltipRect.width - 10}px`;
      }
      if (tooltipRect.bottom > window.innerHeight + scrollTop) {
        // Position above element instead
        tooltip.style.top = `${rect.top + scrollTop - tooltipRect.height - 5}px`;
      }
    }, 10);
  }

  /**
   * Hide current tooltip
   */
  function hideTooltip() {
    if (currentTooltip) {
      currentTooltip.remove();
      currentTooltip = null;
    }
  }

  // Public API
  return {
    init,
    fetchDefinition,
    hideTooltip
  };
})();
