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
    // Blue Family - CLICKED (in clicked reader)
    CLICKED_VERSE_HL_COLOR: '#bfdbfe', // Pale Blue - Whole verse background when term clicked
    CLICKED_TERM_HL_COLOR: '#1e40af',  // Dark Blue - Specific clicked term/word

    // Orange Family - MATCHED (in other reader)
    MATCHED_SN_HL_COLOR: '#ff6b35',    // Darkest Orange - Matched Strong's number
    MATCHED_TERM_HL_COLOR: '#ff9966',  // Lighter Orange - Matched term/word
    MATCHED_VERSE_HL_COLOR: '#ffe0cc', // Much Lighter Orange - Matched verse background

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

        // Clear any existing highlights (both A1 and MATCHED)
        this.clearHighlights();
        this.clearMatchedHighlights();

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

        // === A2: Cross-reader MATCHED highlighting ===
        // Trigger MATCHED highlighting in the other reader
        this.triggerMatchedHighlighting(element, readerType);
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

    /**
     * Clear MATCHED highlights (orange family) in all readers
     */
    clearMatchedHighlights: function() {
        // Clear MATCHED Strong's number highlights
        document.querySelectorAll('.matched-sn-highlighted').forEach(el => {
            el.style.backgroundColor = '';
            el.style.color = '';
            el.style.padding = '';
            el.style.borderRadius = '';
            el.style.fontWeight = '';
            el.style.border = '';
            el.style.boxShadow = '';
            el.style.animation = '';
            el.classList.remove('matched-sn-highlighted');
        });

        // Clear MATCHED term highlights
        document.querySelectorAll('.matched-term-highlighted').forEach(el => {
            el.style.backgroundColor = '';
            el.style.color = '';
            el.style.fontWeight = '';
            el.style.padding = '';
            el.style.borderRadius = '';
            el.classList.remove('matched-term-highlighted');
        });

        // Clear MATCHED verse highlights
        document.querySelectorAll('.matched-verse-highlighted').forEach(el => {
            el.style.backgroundColor = '';
            el.classList.remove('matched-verse-highlighted');
        });

        console.log('HighlightingFoundation: Cleared all MATCHED highlights');
    },

    /**
     * A2: Trigger MATCHED highlighting in the other reader
     * @param {Element} clickedElement - The clicked word element
     * @param {string} clickedReaderType - 'left' or 'right'
     */
    triggerMatchedHighlighting: function(clickedElement, clickedReaderType) {
        console.log(`HighlightingFoundation A2: Triggering MATCHED highlighting from ${clickedReaderType} reader`);

        // Determine the other reader
        const otherReaderType = clickedReaderType === 'left' ? 'right' : 'left';
        const otherContentArea = document.getElementById(`${otherReaderType}-reader-content-area`);

        if (!otherContentArea) {
            console.log(`HighlightingFoundation A2: ${otherReaderType} reader not found`);
            return;
        }

        // Get the verse number from the clicked element
        const clickedVerse = clickedElement.closest('[data-verse]');
        if (!clickedVerse) {
            console.log('HighlightingFoundation A2: No verse container found for clicked element');
            return;
        }

        const verseNumber = clickedVerse.getAttribute('data-verse');
        console.log(`HighlightingFoundation A2: Clicked in verse ${verseNumber}`);

        // Find Strong's numbers near the clicked word in the CLICKED reader
        const clickedWord = clickedElement.textContent.trim();
        const strongsNumbers = this.findNearbyStrongsNumbers(clickedElement, clickedReaderType);

        console.log(`HighlightingFoundation A2: Found ${strongsNumbers.length} Strong's numbers near "${clickedWord}":`, strongsNumbers);

        // If no Strong's numbers found near the clicked word, just highlight verse background (if enabled)
        if (strongsNumbers.length === 0) {
            console.log('HighlightingFoundation A2: No Strong\'s numbers found near clicked word');

            // Only highlight verse background if Ver HL checkbox is enabled
            const verseHlCheckbox = document.getElementById(`${otherReaderType}-reader-hl-ver`);
            if (verseHlCheckbox && verseHlCheckbox.checked) {
                const otherVerse = otherContentArea.querySelector(`[data-verse="${verseNumber}"]`);
                if (otherVerse) {
                    otherVerse.classList.add('matched-verse-highlighted');
                    otherVerse.style.backgroundColor = this.MATCHED_VERSE_HL_COLOR;
                    console.log(`HighlightingFoundation A2: Applied MATCHED_VERSE_HL_COLOR to verse ${verseNumber} (no specific Strong's)`);
                }
            }
            return;
        }

        // Copy Strong's number to clipboard and fill SN cpd field (when clicking from LEFT reader)
        if (clickedReaderType === 'left' && strongsNumbers.length > 0) {
            const strongNumber = strongsNumbers[0]; // Use the first (primary) Strong's number

            // Copy to clipboard
            navigator.clipboard.writeText(strongNumber).then(() => {
                console.log(`HighlightingFoundation A2: Copied ${strongNumber} to clipboard`);
            }).catch(err => {
                console.error('HighlightingFoundation A2: Failed to copy to clipboard:', err);
            });

            // Fill the SN cpd field in right reader
            const strongNumberInput = document.getElementById('strong-number-input');
            if (strongNumberInput) {
                strongNumberInput.value = strongNumber;
                console.log(`HighlightingFoundation A2: Filled SN cpd field with ${strongNumber}`);

                // Highlight the input briefly to show it was filled
                strongNumberInput.style.backgroundColor = '#e3f2fd';
                setTimeout(() => {
                    strongNumberInput.style.backgroundColor = '';
                }, 1000);
            }
        }

        // Highlight matching Strong's numbers in the OTHER reader
        this.highlightMatchedStrongs(strongsNumbers, otherReaderType, verseNumber);
    },

    /**
     * Find Strong's numbers near a clicked element
     * @param {Element} element - The clicked element
     * @param {string} readerType - 'left' or 'right'
     * @returns {Array} Array of Strong's number strings (e.g., ['H0430', 'H0776'])
     */
    findNearbyStrongsNumbers: function(element, readerType) {
        const strongsNumbers = [];

        // Primary strategy: Check for Strong's number as next sibling
        // In Chinese/English Bible text, Strong's numbers typically come AFTER the word
        let nextSibling = element.nextElementSibling;
        if (nextSibling) {
            // Direct Strong's number element
            if (nextSibling.classList.contains('strongs-number')) {
                const sn = nextSibling.getAttribute('data-strong');
                if (sn) strongsNumbers.push(sn);
                console.log(`HighlightingFoundation: Found Strong's ${sn} as next sibling`);
                return strongsNumbers;
            }

            // Container element (like WAH09002) - look for first Strong's number inside
            const firstStrongInside = nextSibling.querySelector('.strongs-number');
            if (firstStrongInside) {
                const sn = firstStrongInside.getAttribute('data-strong');
                if (sn) {
                    strongsNumbers.push(sn);
                    console.log(`HighlightingFoundation: Found Strong's ${sn} inside next sibling container (${nextSibling.tagName})`);
                    return strongsNumbers;
                }
            }
        }

        // Fallback: Check for Strong's number as previous sibling
        // (less common but possible in some text layouts)
        let prevSibling = element.previousElementSibling;
        if (prevSibling && prevSibling.classList.contains('strongs-number')) {
            const sn = prevSibling.getAttribute('data-strong');
            if (sn) strongsNumbers.push(sn);
            console.log(`HighlightingFoundation: Found Strong's ${sn} as previous sibling`);
            return strongsNumbers;
        }

        // Last resort: Check parent's next sibling (only for specific inline elements)
        const parent = element.parentElement;
        if (parent && parent.tagName !== 'P' && !parent.classList.contains('verse') && !parent.classList.contains('verse-container')) {
            let parentNextSibling = parent.nextElementSibling;
            if (parentNextSibling && parentNextSibling.classList.contains('strongs-number')) {
                const sn = parentNextSibling.getAttribute('data-strong');
                if (sn) {
                    strongsNumbers.push(sn);
                    console.log(`HighlightingFoundation: Found Strong's ${sn} as parent's next sibling`);
                }
            }
        }

        return strongsNumbers;
    },

    /**
     * Highlight matching Strong's numbers in the target reader with MATCHED colors
     * @param {Array} strongsNumbers - Array of Strong's number strings
     * @param {string} targetReaderType - 'left' or 'right'
     * @param {string} verseNumber - Verse number to highlight
     */
    highlightMatchedStrongs: function(strongsNumbers, targetReaderType, verseNumber) {
        const targetContentArea = document.getElementById(`${targetReaderType}-reader-content-area`);
        if (!targetContentArea) return;

        console.log(`HighlightingFoundation A2: Highlighting in ${targetReaderType} reader, verse ${verseNumber}, Strong's:`, strongsNumbers);

        let highlightCount = 0;

        // Find matching Strong's numbers in the target reader
        strongsNumbers.forEach(strongNum => {
            const selector = `.strongs-number[data-strong="${strongNum}"]`;
            const matchingElements = targetContentArea.querySelectorAll(selector);

            matchingElements.forEach(strongEl => {
                // Only highlight if in the same verse
                const strongVerse = strongEl.closest('[data-verse]');
                if (strongVerse && strongVerse.getAttribute('data-verse') === verseNumber) {
                    // Apply MATCHED_SN_HL_COLOR (darkest orange)
                    strongEl.classList.add('matched-sn-highlighted');
                    strongEl.style.backgroundColor = this.MATCHED_SN_HL_COLOR;
                    strongEl.style.color = 'white';
                    strongEl.style.padding = '2px 4px';
                    strongEl.style.borderRadius = '3px';
                    strongEl.style.fontWeight = 'bold';
                    strongEl.style.border = `2px solid ${this.MATCHED_SN_HL_COLOR}`;

                    highlightCount++;
                    console.log(`HighlightingFoundation A2: Highlighted Strong's ${strongNum} with MATCHED_SN_HL_COLOR`);

                    // Find and highlight associated term (MATCHED_TERM_HL_COLOR)
                    const associatedTerm = this.findAssociatedTermForStrongsNumber(strongEl);
                    if (associatedTerm) {
                        associatedTerm.classList.add('matched-term-highlighted');
                        associatedTerm.style.backgroundColor = this.MATCHED_TERM_HL_COLOR;
                        associatedTerm.style.color = 'black';
                        associatedTerm.style.padding = '2px 4px';
                        associatedTerm.style.borderRadius = '3px';
                        associatedTerm.style.fontWeight = 'bold';
                        console.log(`HighlightingFoundation A2: Highlighted associated term with MATCHED_TERM_HL_COLOR`);
                    }

                    // Check if verse background highlighting is enabled
                    const verseHlCheckbox = document.getElementById(`${targetReaderType}-reader-hl-ver`);
                    if (verseHlCheckbox && verseHlCheckbox.checked && strongVerse) {
                        strongVerse.classList.add('matched-verse-highlighted');
                        strongVerse.style.backgroundColor = this.MATCHED_VERSE_HL_COLOR;
                        console.log(`HighlightingFoundation A2: Applied MATCHED_VERSE_HL_COLOR to verse ${verseNumber}`);
                    }
                }
            });
        });

        console.log(`HighlightingFoundation A2: Highlighted ${highlightCount} Strong's numbers in ${targetReaderType} reader`);
    },

    /**
     * Find the associated term/word near a Strong's number element
     * @param {Element} strongEl - The Strong's number element
     * @returns {Element|null} The associated term element or null
     */
    findAssociatedTermForStrongsNumber: function(strongEl) {
        // Primary Strategy: Check PREVIOUS sibling for text
        // In Chinese/English Bible text: 神<H0430>, the word comes BEFORE the Strong's number
        let prevSibling = strongEl.previousSibling;
        if (prevSibling && prevSibling.nodeType === Node.TEXT_NODE) {
            const text = prevSibling.textContent.trim();
            // Match Chinese characters or English word at the END of the text
            const match = text.match(/[\u4e00-\u9fa5]+$|[a-zA-Z]+$/);
            if (match && match[0].length > 0) {
                const word = match[0];
                const wordStart = text.lastIndexOf(word);
                const beforeWord = text.substring(0, wordStart);

                const wordSpan = document.createElement('span');
                wordSpan.textContent = word;

                // Replace the text node with: beforeWord + wordSpan
                const beforeNode = document.createTextNode(beforeWord);
                strongEl.parentNode.insertBefore(beforeNode, strongEl);
                strongEl.parentNode.insertBefore(wordSpan, strongEl);
                strongEl.parentNode.removeChild(prevSibling);

                return wordSpan;
            }
        }

        // Strategy 2: Check previous element sibling
        let prevElement = strongEl.previousElementSibling;
        if (prevElement && prevElement.textContent.trim() &&
            !prevElement.classList.contains('strongs-number') &&
            !prevElement.classList.contains('verse-number')) {
            return prevElement;
        }

        // Fallback: Check next sibling (less common)
        let nextSibling = strongEl.nextSibling;
        if (nextSibling && nextSibling.nodeType === Node.TEXT_NODE) {
            const text = nextSibling.textContent.trim();
            const match = text.match(/^[\u4e00-\u9fa5]+|^[a-zA-Z]+/);
            if (match && match[0].length > 0) {
                const wordSpan = document.createElement('span');
                wordSpan.textContent = match[0];
                const remainingText = text.substring(match[0].length);
                nextSibling.textContent = remainingText;
                strongEl.parentNode.insertBefore(wordSpan, nextSibling);
                return wordSpan;
            }
        }

        return null;
    },

    // === INTEGRATION SETUP ===
    /**
     * Subscribe to existing events for cleanup
     */
    setupCleanupEvents: function() {
        // Clear highlights when content changes
        MockMediator.subscribe('leftReaderChapterChanged', () => {
            this.clearHighlights();
            this.clearMatchedHighlights();
        });

        MockMediator.subscribe('rightReaderChapterChanged', () => {
            this.clearHighlights();
            this.clearMatchedHighlights();
        });

        MockMediator.subscribe('mainReaderChanged', () => {
            this.clearHighlights();
            this.clearMatchedHighlights();
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
        this.clearMatchedHighlights();
        console.log('HighlightingFoundation: Reset completed (A1 + A2)');
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