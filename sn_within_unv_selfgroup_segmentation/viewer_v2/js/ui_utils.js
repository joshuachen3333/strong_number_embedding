/**
 * ui_utils.js
 * UI utility functions for loading states, errors, and toasts
 */

const UIUtils = (() => {
  let activeSpinners = new Set();
  let activeToasts = [];

  /**
   * Show loading spinner in container
   * @param {HTMLElement|string} container - Container element or selector
   * @param {string} message - Optional loading message
   */
  function showSpinner(container, message = '載入中...') {
    const el = typeof container === 'string' ? document.querySelector(container) : container;
    if (!el) return;

    // Check if spinner already exists
    const existingSpinner = el.querySelector('.spinner-overlay');
    if (existingSpinner) return;

    const spinnerHTML = `
      <div class="spinner-overlay">
        <div class="spinner-content">
          <div class="spinner"></div>
          <div class="spinner-message">${message}</div>
        </div>
      </div>
    `;

    el.style.position = 'relative';
    el.insertAdjacentHTML('beforeend', spinnerHTML);
    activeSpinners.add(el);
  }

  /**
   * Hide loading spinner from container
   * @param {HTMLElement|string} container - Container element or selector
   */
  function hideSpinner(container) {
    const el = typeof container === 'string' ? document.querySelector(container) : container;
    if (!el) return;

    const spinner = el.querySelector('.spinner-overlay');
    if (spinner) {
      spinner.remove();
      activeSpinners.delete(el);
    }
  }

  /**
   * Show error message
   * @param {string} message - Error message
   * @param {string} type - 'banner' or 'toast' (default: 'toast')
   * @param {number} duration - Toast duration in ms (default: 3000)
   */
  function showError(message, type = 'toast', duration = 3000) {
    if (type === 'banner') {
      showBanner(message, 'error');
    } else {
      showToast(message, 'error', duration);
    }
  }

  /**
   * Show banner at top of page
   * @param {string} message - Message text
   * @param {string} type - 'error', 'warning', 'info', 'success'
   */
  function showBanner(message, type = 'info') {
    // Remove existing banners
    const existing = document.querySelectorAll('.banner');
    existing.forEach(b => b.remove());

    const banner = document.createElement('div');
    banner.className = `banner banner-${type}`;
    banner.innerHTML = `
      <span class="banner-message">${message}</span>
      <button class="banner-close" onclick="this.parentElement.remove()">×</button>
    `;

    document.body.insertBefore(banner, document.body.firstChild);
  }

  /**
   * Show toast notification
   * @param {string} message - Message text
   * @param {string} type - 'error', 'warning', 'info', 'success'
   * @param {number} duration - Duration in ms (0 = persistent)
   */
  function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    container.appendChild(toast);
    activeToasts.push(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
          toast.remove();
          const index = activeToasts.indexOf(toast);
          if (index > -1) activeToasts.splice(index, 1);
        }, 300);
      }, duration);
    }
  }

  /**
   * Show success message
   * @param {string} message - Success message
   * @param {number} duration - Toast duration in ms
   */
  function showSuccess(message, duration = 2000) {
    showToast(message, 'success', duration);
  }

  /**
   * Clear all UI elements (spinners, toasts, banners)
   */
  function clearAll() {
    // Clear spinners
    activeSpinners.forEach(el => hideSpinner(el));
    activeSpinners.clear();

    // Clear toasts
    activeToasts.forEach(toast => toast.remove());
    activeToasts = [];

    // Clear banners
    document.querySelectorAll('.banner').forEach(b => b.remove());
  }

  // Public API
  return {
    showSpinner,
    hideSpinner,
    showError,
    showBanner,
    showToast,
    showSuccess,
    clearAll
  };
})();
