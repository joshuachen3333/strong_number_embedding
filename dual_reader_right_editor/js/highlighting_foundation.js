/**
 * Highlighting Foundation - Minimal Implementation for A1 Only
 * Clean abstraction layer that plugs into existing architecture
 *
 * A1: Self-highlighting - Click term in reader → highlight same term in dark blue
 *
 * Following dev_criteria.md:
 * - Additive enhancement (no refactoring)
 * - Integrates with existing MockMediator
 * - Preserves all existing functionality
 * - Minimal, focused, testable
 */

const HighlightingFoundation = {
    // === CONFIGURATION ===
    CLICKED_VERSE_HL_COLOR: '#bfdbfe', // Pale Blue - Whole verse background when term clicked (adjust here)
    CLICKED_TERM_HL_COLOR: '#1e40af',  // Dark Blue - Specific clicked term/word (like FL Ver Sel button)

    // === STATE ===
    currentHighlight: null,        // Currently highlighted term
    currentVerseHighlight: null,   // Currently highlighted verse container
    isActive: false,

    // === INITIALIZATION ===
    init: function() {
        console.log('HighlightingFoundation: Initializing A1 self-highlighting...');

        // Verify MockMediator dependency
        if (typeof MockMediator === 'undefined') {
            console.error('HighlightingFoundation: MockMediator not found!');
            return false;
        }

        // Inject CSS for A1
        this.injectA1CSS();

        // Subscribe to cleanup events
        this.setupCleanupEvents();

        // Add A1 click handlers after content loads
        this.setupA1ClickHandlers();

        this.isActive = true;
        console.log('HighlightingFoundation: A1 ready');
        return true;
    },

    // === A1 CORE FUNCTIONALITY ===
    /**
     * A1: Highlight a term with dark blue (like FL Ver Sel button)
     * @param {Element} element - Element to highlight
     * @param {string} readerType - 'left' or 'right' (for logging)
     */
    highlightTerm: function(element, readerType) {
        if (!this.isActive || !element) return;

        console.log(`HighlightingFoundation A1: Highlighting "${element.textContent.trim()}" in ${readerType} reader`);

        // Clear any existing highlights
        this.clearHighlights();

        // Find the verse container (parent .verse or .verse-container)
        const verseContainer = element.closest('.verse, .verse-container');

        // Apply pale blue highlight to whole verse
        if (verseContainer) {
            verseContainer.classList.add('highlight-verse-bg');
            verseContainer.style.setProperty('background-color', this.CLICKED_VERSE_HL_COLOR, 'important');
            this.currentVerseHighlight = verseContainer;
            console.log('HighlightingFoundation A1: Pale blue verse background applied');
        }

        // Apply dark blue highlight to specific term
        element.classList.add('highlight-a1');
        element.style.setProperty('background-color', this.CLICKED_TERM_HL_COLOR, 'important');
        this.currentHighlight = element;

        console.log('HighlightingFoundation A1: Dark blue term highlight applied');
    },

    /**
     * Clear all A1 highlights (both term and verse)
     */
    clearHighlights: function() {
        // Clear term highlights
        document.querySelectorAll('.highlight-a1').forEach(el => {
            el.classList.remove('highlight-a1');
            el.style.removeProperty('background-color');
        });

        // Clear verse background highlights
        document.querySelectorAll('.highlight-verse-bg').forEach(el => {
            el.classList.remove('highlight-verse-bg');
            el.style.removeProperty('background-color');
        });

        this.currentHighlight = null;
        this.currentVerseHighlight = null;
    },

    // === INTEGRATION SETUP ===
    /**
     * Subscribe to existing events for cleanup
     */
    setupCleanupEvents: function() {
        // Clear highlights when content changes
        MockMediator.subscribe('leftReaderChapterChanged', () => {
            this.clearHighlights();
        });

        MockMediator.subscribe('rightReaderChapterChanged', () => {
            this.clearHighlights();
        });

        MockMediator.subscribe('mainReaderChanged', () => {
            this.clearHighlights();
        });
    },

    /**
     * Setup A1 click handlers for both readers
     */
    setupA1ClickHandlers: function() {
        // Wait for content to be loaded
        setTimeout(() => {
            this.addA1HandlerToReader('left');
            this.addA1HandlerToReader('right');
        }, 500);
    },

    /**
     * Add A1 click handler to a specific reader
     * @param {string} readerType - 'left' or 'right'
     */
    addA1HandlerToReader: function(readerType) {
        const contentArea = document.getElementById(`${readerType}-reader-content-area`);
        if (!contentArea) {
            console.log(`HighlightingFoundation A1: ${readerType} reader not found`);
            return;
        }

        // Add click handler with event delegation
        contentArea.addEventListener('click', (event) => {
            console.log(`HighlightingFoundation A1: Click detected in ${readerType} reader on:`, event.target);
            console.log(`  - tagName: ${event.target.tagName}`);
            console.log(`  - className: ${event.target.className}`);
            console.log(`  - textContent: "${event.target.textContent.trim().substring(0, 20)}..."`);

            // Don't interfere with existing functionality
            if (event.target.classList.contains('strongs-number') ||
                event.target.closest('.reader-controls')) {
                console.log(`  - SKIPPED: Strong's number or control`);
                return;
            }

            // Don't interfere with active editing (right reader only)
            if (readerType === 'right' &&
                event.target.getAttribute('contenteditable') === 'true') {
                console.log(`  - SKIPPED: Active editing`);
                return;
            }

            // Find the clicked text element
            let targetElement = event.target;
            console.log(`  - Initial target:`, targetElement);

            // Handle clicks on WAH elements or verse containers - find actual word element
            if (targetElement.tagName === 'WAH09002' ||
                targetElement.classList.contains('verse') ||
                targetElement.classList.contains('verse-container')) {
                console.log(`  - Clicked on verse container, finding word element...`);
                // Use document.caretRangeFromPoint to find actual text element
                const range = document.caretRangeFromPoint(event.clientX, event.clientY);
                if (range && range.startContainer.nodeType === Node.TEXT_NODE) {
                    const textNode = range.startContainer;
                    const parentElement = textNode.parentElement;

                    // Look for the closest meaningful word element (span, em, etc.)
                    let wordElement = parentElement;

                    // If parent is WAH or verse container, try to create a word span
                    if (wordElement.tagName === 'WAH09002' ||
                        wordElement.classList.contains('verse') ||
                        wordElement.classList.contains('verse-container')) {

                        // Extract the word around the click position
                        const textContent = textNode.textContent;
                        const offset = range.startOffset;

                        // Find word boundaries
                        const beforeText = textContent.substring(0, offset);
                        const afterText = textContent.substring(offset);

                        // Simple word boundary detection (space, punctuation)
                        const wordStart = Math.max(0,
                            Math.max(beforeText.lastIndexOf(' '),
                                    beforeText.lastIndexOf('；'),
                                    beforeText.lastIndexOf('，'),
                                    beforeText.lastIndexOf('。')) + 1);

                        const wordEndInAfter = Math.min(afterText.length,
                            Math.min(
                                afterText.indexOf(' ') === -1 ? afterText.length : afterText.indexOf(' '),
                                afterText.indexOf('；') === -1 ? afterText.length : afterText.indexOf('；'),
                                afterText.indexOf('，') === -1 ? afterText.length : afterText.indexOf('，'),
                                afterText.indexOf('。') === -1 ? afterText.length : afterText.indexOf('。')
                            ));

                        const wordEnd = offset + wordEndInAfter;
                        const clickedWord = textContent.substring(wordStart, wordEnd).trim();

                        if (clickedWord && clickedWord.length > 0) {
                            // Create a temporary span for the word
                            const wordSpan = document.createElement('span');
                            wordSpan.textContent = clickedWord;
                            wordSpan.classList.add('temp-word-highlight');

                            // Split the text node and insert the span
                            const beforeNode = document.createTextNode(textContent.substring(0, wordStart));
                            const afterNode = document.createTextNode(textContent.substring(wordEnd));

                            textNode.parentNode.insertBefore(beforeNode, textNode);
                            textNode.parentNode.insertBefore(wordSpan, textNode);
                            textNode.parentNode.insertBefore(afterNode, textNode);
                            textNode.parentNode.removeChild(textNode);

                            targetElement = wordSpan;
                            console.log(`  - Created word span for: "${clickedWord}"`);
                        }
                    } else {
                        targetElement = wordElement;
                        console.log(`  - Found word element:`, targetElement);
                    }
                }
            }

            // Skip if not a meaningful text element
            if (!targetElement || !targetElement.textContent.trim() ||
                targetElement === contentArea ||
                targetElement.classList.contains('verse-number')) {
                console.log(`  - SKIPPED: Not meaningful text element`);
                return;
            }

            console.log(`  - PROCEEDING: Will highlight "${targetElement.textContent.trim()}"`);
            // A1: Apply self-highlighting
            this.highlightTerm(targetElement, readerType);
        });

        console.log(`HighlightingFoundation A1: ${readerType} reader handler added`);
    },

    // === CSS INJECTION ===
    /**
     * Inject minimal CSS for A1 highlighting
     */
    injectA1CSS: function() {
        const styleId = 'highlighting-foundation-a1';
        if (document.getElementById(styleId)) return;

        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            /* A1: Clicked Term Highlight - Dark Blue */
            .highlight-a1 {
                background-color: ${this.CLICKED_TERM_HL_COLOR} !important;
                color: white !important;
                padding: 2px 4px !important;
                border-radius: 3px !important;
                font-weight: bold !important;
                display: inline-block !important;
                transition: background-color 0.2s ease;
                cursor: pointer;
            }

            .highlight-a1:hover {
                background-color: #2563eb !important;
            }

            /* A1: Verse Background Highlight - Pale Blue */
            .highlight-verse-bg {
                background-color: ${this.CLICKED_VERSE_HL_COLOR} !important;
                transition: background-color 0.2s ease;
            }
        `;

        document.head.appendChild(style);
        console.log('HighlightingFoundation A1: CSS injected');
    },

    // === PUBLIC API ===
    /**
     * Check if A1 system is ready
     */
    isReady: function() {
        return this.isActive;
    },

    /**
     * Get current state
     */
    getState: function() {
        return {
            isActive: this.isActive,
            currentHighlight: this.currentHighlight
        };
    },

    // === TESTING FUNCTIONS ===
    /**
     * Test A1 by finding and highlighting text
     * @param {string} readerType - 'left' or 'right'
     * @param {string} text - Text to find and highlight
     */
    testA1: function(readerType = 'right', text = '起初') {
        console.log(`Testing A1: Looking for "${text}" in ${readerType} reader`);

        const contentArea = document.getElementById(`${readerType}-reader-content-area`);
        if (!contentArea) {
            console.error(`${readerType} reader not found`);
            return false;
        }

        // Find text in content area
        const walker = document.createTreeWalker(
            contentArea,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.includes(text)) {
                const element = node.parentElement;
                console.log(`Found "${text}" in element:`, element);
                this.highlightTerm(element, readerType);
                return true;
            }
        }

        console.error(`Text "${text}" not found in ${readerType} reader`);
        return false;
    },

    /**
     * Reset highlighting (clear all)
     */
    reset: function() {
        this.clearHighlights();
        console.log('HighlightingFoundation A1: Reset completed');
    }
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('HighlightingFoundation: DOMContentLoaded triggered');
    setTimeout(() => {
        console.log('HighlightingFoundation: About to call init()');
        HighlightingFoundation.init();
    }, 100);
});

// Also try immediate initialization
console.log('HighlightingFoundation: Script loaded immediately');

// Make available globally for testing and integration
window.HighlightingFoundation = HighlightingFoundation;