/**
 * mediator.js
 * Event bus for decoupled component communication (Mediator pattern)
 *
 * Components publish events without knowing who subscribes.
 * Components subscribe to events without knowing who publishes.
 */

const Mediator = (() => {
  // Event catalog for documentation
  const EVENT_TYPES = {
    // Verse events
    VERSE_SELECT: 'verse:select',           // User requests verse selection
    VERSE_SELECTED: 'verse:selected',       // Verse data loaded and ready

    // Chapter events
    CHAPTER_LOAD: 'chapter:load',           // Request to load chapter
    CHAPTER_LOADED: 'chapter:loaded',       // Chapter data ready

    // UI events
    COLORS_APPLY: 'colors:apply',           // Apply color map to panels
    LOADING_START: 'loading:start',         // Show loading indicator
    LOADING_END: 'loading:end',             // Hide loading indicator
    ERROR_SHOW: 'error:show',               // Display error message

    // Dictionary events
    SN_CLICK: 'sn:click',                   // Strong's number clicked
    TOOLTIP_SHOW: 'tooltip:show',           // Show dictionary tooltip
    TOOLTIP_HIDE: 'tooltip:hide'            // Hide dictionary tooltip
  };

  // Subscribers map: { eventType: [callback1, callback2, ...] }
  const subscribers = {};

  /**
   * Subscribe to an event
   * @param {string} eventType - Event type from EVENT_TYPES
   * @param {Function} callback - Function to call when event published
   * @returns {Function} Unsubscribe function
   */
  function subscribe(eventType, callback) {
    if (!subscribers[eventType]) {
      subscribers[eventType] = [];
    }

    subscribers[eventType].push(callback);

    // Return unsubscribe function
    return () => unsubscribe(eventType, callback);
  }

  /**
   * Unsubscribe from an event
   * @param {string} eventType - Event type
   * @param {Function} callback - Callback to remove
   */
  function unsubscribe(eventType, callback) {
    if (!subscribers[eventType]) return;

    const index = subscribers[eventType].indexOf(callback);
    if (index > -1) {
      subscribers[eventType].splice(index, 1);
    }
  }

  /**
   * Publish an event to all subscribers
   * @param {string} eventType - Event type
   * @param {*} data - Data to pass to subscribers
   */
  function publish(eventType, data) {
    if (!subscribers[eventType]) return;

    // Call all subscribers with the data
    subscribers[eventType].forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`Error in subscriber for ${eventType}:`, error);
      }
    });
  }

  /**
   * Get event type constants for use in components
   * @returns {Object} EVENT_TYPES
   */
  function getEventTypes() {
    return EVENT_TYPES;
  }

  /**
   * Debug: List all subscribers
   * @returns {Object} Subscribers map
   */
  function getSubscribers() {
    const counts = {};
    for (const eventType in subscribers) {
      counts[eventType] = subscribers[eventType].length;
    }
    return counts;
  }

  // Public API
  return {
    subscribe,
    unsubscribe,
    publish,
    EVENT_TYPES,
    getEventTypes,
    getSubscribers
  };
})();
