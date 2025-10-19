/**
 * Right Reader Frontend Logic
 * Handles the functionality of the right Bible reader component,
 * which can be either main or follower depending on last interaction.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Helper function to find the associated term/word near a Strong's number
    function findAssociatedTerm(strongEl) {
        // Strategy 1: Check if there's text immediately after the Strong's number
        let nextSibling = strongEl.nextSibling;
        if (nextSibling && nextSibling.nodeType === Node.TEXT_NODE) {
            const text = nextSibling.textContent.trim();
            // Extract the first word (Chinese characters or English word)
            const match = text.match(/^[\u4e00-\u9fa5]+|^[a-zA-Z]+/);
            if (match && match[0].length > 0) {
                // Create a span for this word
                const wordSpan = document.createElement('span');
                wordSpan.textContent = match[0];
                const remainingText = text.substring(match[0].length);
                nextSibling.textContent = remainingText;
                strongEl.parentNode.insertBefore(wordSpan, nextSibling);
                return wordSpan;
            }
        }

        // Strategy 2: Look for adjacent span or text within parent WAH element
        const parent = strongEl.parentElement;
        if (parent && (parent.tagName === 'WAH09002' || parent.classList.contains('verse'))) {
            // Look for text near the Strong's number
            const parentText = parent.textContent;
            const snText = strongEl.textContent;
            const snIndex = parentText.indexOf(snText);
            if (snIndex !== -1) {
                const afterSN = parentText.substring(snIndex + snText.length);
                const match = afterSN.match(/^[\u4e00-\u9fa5]+|^[a-zA-Z]+/);
                if (match && match[0].length > 0) {
                    // Find the text node and wrap it
                    for (const child of parent.childNodes) {
                        if (child.nodeType === Node.TEXT_NODE && child.textContent.includes(match[0])) {
                            const wordSpan = document.createElement('span');
                            wordSpan.textContent = match[0];
                            const remainingText = child.textContent.replace(match[0], '');
                            child.textContent = remainingText;
                            parent.insertBefore(wordSpan, child);
                            return wordSpan;
                        }
                    }
                }
            }
        }

        return null; // No associated term found
    }

    const bookSelect = document.getElementById('right-reader-book');
    const chapterInput = document.getElementById('right-reader-chapter');
    // Load button removed - auto-loading on selection changes
    const versionSelect = document.getElementById('right-reader-version-select');
    const strongToggle = document.getElementById('right-reader-strong-toggle');
    const followScrollToggle = document.getElementById('right-reader-follow-scroll');
    const followSelectionToggle = document.getElementById('right-reader-follow-selection');
    const contentArea = document.getElementById('right-reader-content-area');
    const statusDisplay = document.getElementById('right-reader-status-display');

    // Edit Mode controls
    const editModeToggle = document.getElementById('right-reader-edit-mode');
    const strongControlsContainer = document.getElementById('right-reader-strong-controls');
    const strongNumberInput = document.getElementById('strong-number-input');
    const insertStrongBtn = document.getElementById('insert-strong-btn');
    const leftAlignmentSpacer = document.getElementById('left-reader-alignment-spacer');

    // References to left reader checkboxes for cross-reader control
    const leftFollowScrollToggle = document.getElementById('left-reader-follow-scroll');
    const leftFollowSelectionToggle = document.getElementById('left-reader-follow-selection');

    let isUpdatingCheckboxes = false; // Flag to prevent infinite loops
    let currentBook = null;
    let currentChapter = null;
    let currentBookChinese = null; // Store Chinese book abbreviation for API calls
    let currentVerses = null; // Store verses from main reader

    // Edit Mode state (minimal) - will be synced with HTML checkbox during initialization
    let isEditMode = false; // Will be set from editModeToggle.checked during init
    let currentEditingVerse = null; // Track which verse is being edited

    // Highlighting timeout management
    let highlightTimer = null;

    // Undo/Redo system
    let undoStack = []; // Array of {verseId, content, cursorPos}
    let redoStack = [];
    let isUndoRedoAction = false; // Prevent undo/redo from creating new history

    // Auto-save system
    let autoSaveTimer = null;
    let hasUnsavedChanges = false;
    const AUTO_SAVE_INTERVAL = 10 * 1000; // 10 seconds for testing (was 3 minutes)
    const MANUAL_SAVE_ENABLED = true; // Enable immediate save for debugging

    // Book mapping with Chinese abbreviations for bible.fhl.net API (same as left reader)
    const books = [
        { english: "Genesis", chinese: "創" },
        { english: "Exodus", chinese: "出" },
        { english: "Leviticus", chinese: "利" },
        { english: "Numbers", chinese: "民" },
        { english: "Deuteronomy", chinese: "申" },
        { english: "Joshua", chinese: "書" },
        { english: "Judges", chinese: "士" },
        { english: "Ruth", chinese: "得" },
        { english: "1 Samuel", chinese: "撒上" },
        { english: "2 Samuel", chinese: "撒下" },
        { english: "1 Kings", chinese: "王上" },
        { english: "2 Kings", chinese: "王下" },
        { english: "1 Chronicles", chinese: "代上" },
        { english: "2 Chronicles", chinese: "代下" },
        { english: "Ezra", chinese: "拉" },
        { english: "Nehemiah", chinese: "尼" },
        { english: "Esther", chinese: "斯" },
        { english: "Job", chinese: "伯" },
        { english: "Psalms", chinese: "詩" },
        { english: "Proverbs", chinese: "箴" },
        { english: "Ecclesiastes", chinese: "傳" },
        { english: "Song of Songs", chinese: "歌" },
        { english: "Isaiah", chinese: "賽" },
        { english: "Jeremiah", chinese: "耶" },
        { english: "Lamentations", chinese: "哀" },
        { english: "Ezekiel", chinese: "結" },
        { english: "Daniel", chinese: "但" },
        { english: "Hosea", chinese: "何" },
        { english: "Joel", chinese: "珥" },
        { english: "Amos", chinese: "摩" },
        { english: "Obadiah", chinese: "俄" },
        { english: "Jonah", chinese: "拿" },
        { english: "Micah", chinese: "彌" },
        { english: "Nahum", chinese: "鴻" },
        { english: "Habakkuk", chinese: "哈" },
        { english: "Zephaniah", chinese: "番" },
        { english: "Haggai", chinese: "該" },
        { english: "Zechariah", chinese: "亞" },
        { english: "Malachi", chinese: "瑪" },
        { english: "Matthew", chinese: "太" },
        { english: "Mark", chinese: "可" },
        { english: "Luke", chinese: "路" },
        { english: "John", chinese: "約" },
        { english: "Acts", chinese: "徒" },
        { english: "Romans", chinese: "羅" },
        { english: "1 Corinthians", chinese: "林前" },
        { english: "2 Corinthians", chinese: "林後" },
        { english: "Galatians", chinese: "加" },
        { english: "Ephesians", chinese: "弗" },
        { english: "Philippians", chinese: "腓" },
        { english: "Colossians", chinese: "西" },
        { english: "1 Thessalonians", chinese: "帖前" },
        { english: "2 Thessalonians", chinese: "帖後" },
        { english: "1 Timothy", chinese: "提前" },
        { english: "2 Timothy", chinese: "提後" },
        { english: "Titus", chinese: "多" },
        { english: "Philemon", chinese: "門" },
        { english: "Hebrews", chinese: "來" },
        { english: "James", chinese: "雅" },
        { english: "1 Peter", chinese: "彼前" },
        { english: "2 Peter", chinese: "彼後" },
        { english: "1 John", chinese: "約一" },
        { english: "2 John", chinese: "約二" },
        { english: "3 John", chinese: "約三" },
        { english: "Jude", chinese: "猶" },
        { english: "Revelation", chinese: "啟" }
    ];

    // Populate book dropdown
    if (bookSelect && books && books.length > 0) {
        console.log('RightReader: Populating book select dropdown...');
        books.forEach(book => {
            const option = document.createElement('option');
            option.value = book.chinese; // Use Chinese abbreviation as value for API
            option.textContent = book.english; // Display English name for user
            option.dataset.chinese = book.chinese; // Store Chinese abbreviation
            bookSelect.appendChild(option);
        });
        console.log(`RightReader: Finished populating books. Total options: ${bookSelect.options.length}`);
    }

    /**
     * Logs status updates to the second reader status display
     * @param {string} message - Status message to log
     */
    function logStatus(message) {
        if (statusDisplay) {
            const timestamp = new Date().toLocaleTimeString();
            const statusDiv = document.createElement('div');
            statusDiv.textContent = `[${timestamp}] ${message}`;
            statusDisplay.appendChild(statusDiv);
            statusDisplay.scrollTop = statusDisplay.scrollHeight;
        }
    }

    // Event listeners for controls
    // Auto-load when book or chapter changes
    bookSelect.addEventListener('change', loadChapterContent);
    chapterInput.addEventListener('change', loadChapterContent);
    versionSelect.addEventListener('change', loadChapterContent);
    
    bookSelect.addEventListener('change', () => {
        // Save current position to localStorage whenever book changes
        localStorage.setItem('rightReader_lastBook', bookSelect.value);
        localStorage.setItem('rightReader_lastChapter', chapterInput.value);
        console.log(`RightReader: Saved book/chapter to localStorage: ${bookSelect.value}/${chapterInput.value}`);

        // Only set as main if this reader is not following (both follow checkboxes unchecked)
        if (!followScrollToggle.checked && !followSelectionToggle.checked) {
            MockMediator.setMainReader('right', 'book selection');
        }
        const selectedBook = bookSelect.options[bookSelect.selectedIndex].text;
        logStatus(`Book selected: ${selectedBook}`);
        loadChapterContent();
    });
    chapterInput.addEventListener('change', () => {
        // Save current position to localStorage whenever chapter changes
        localStorage.setItem('rightReader_lastBook', bookSelect.value);
        localStorage.setItem('rightReader_lastChapter', chapterInput.value);
        console.log(`RightReader: Saved book/chapter to localStorage: ${bookSelect.value}/${chapterInput.value}`);

        // Only set as main if this reader is already main (respect checkbox state)
        if (!followScrollToggle.checked && !followSelectionToggle.checked) {
            MockMediator.setMainReader('right', 'chapter selection');
        }
        logStatus(`Chapter selected: ${chapterInput.value}`);
        loadChapterContent();
    });
    versionSelect.addEventListener('change', () => {
        // Only set as main if this reader is already main (respect checkbox state)
        if (!followScrollToggle.checked && !followSelectionToggle.checked) {
            MockMediator.setMainReader('right', 'version selection');
        }
        const selectedVersion = versionSelect.options[versionSelect.selectedIndex].text;
        logStatus(`Version selected: ${selectedVersion}`);
        console.log('RightReader: Version changed to', versionSelect.value);
        console.log('RightReader: Clearing cache for version change');
        MockMediator.clearCache();
        loadChapterContent();
    });
    strongToggle.addEventListener('change', () => {
        // Only set as main if this reader is already main (respect checkbox state)
        if (!followScrollToggle.checked && !followSelectionToggle.checked) {
            MockMediator.setMainReader('right', 'Strong\'s toggle');
        }
        logStatus(`Strong's Numbers: ${strongToggle.checked ? 'ON' : 'OFF'}`);
        console.log('RightReader: Strong toggle changed to', strongToggle.checked);

        // Immediately hide/show Strong's numbers without reloading
        const strongsElements = contentArea.querySelectorAll('.strongs-number');
        strongsElements.forEach(el => {
            el.style.display = strongToggle.checked ? '' : 'none';
        });

        loadChapterContent();
    });
    followScrollToggle.addEventListener('change', () => {
        if (isUpdatingCheckboxes) return; // Prevent infinite loops

        const status = followScrollToggle.checked ? 'ENABLED' : 'DISABLED';
        logStatus(`📍 Follow verse scroll: ${status}`);
        console.log('RightReader: Follow scroll toggle changed to', followScrollToggle.checked);

        // When right reader becomes follower, make left reader main by unchecking its follow boxes
        if (followScrollToggle.checked) {
            isUpdatingCheckboxes = true;
            // Auto-uncheck left reader follow checkboxes to make it main
            leftFollowScrollToggle.checked = false;
            leftFollowSelectionToggle.checked = false;
            // Also ensure this reader's text selection is checked (parent control)
            if (!followSelectionToggle.checked) {
                followSelectionToggle.checked = true;
                logStatus('📍 Follow text selection: ENABLED (required for verse scroll)');
            }
            logStatus('📍 Right reader is now FOLLOWER, left reader is now MAIN');

            // Update MockMediator to know left reader is now main
            MockMediator.setMainReader('left', 'right follow scroll checked');

            setTimeout(() => { isUpdatingCheckboxes = false; }, 100);
        }

        // If follow scroll is enabled, immediately sync to current left reader position
        if (followScrollToggle.checked) {
            // Get left reader's current state directly from its controls
            const leftBookSelect = document.getElementById('left-reader-book');
            const leftChapterInput = document.getElementById('left-reader-chapter');

            if (leftBookSelect && leftChapterInput && leftBookSelect.value && leftChapterInput.value) {
                const leftBook = leftBookSelect.value; // Chinese abbreviation
                const leftChapter = parseInt(leftChapterInput.value);

                // Try to get current verse from left reader's scroll position
                const leftContentArea = document.getElementById('left-reader-content-area');
                let leftVerse = 1; // Default to verse 1

                if (leftContentArea) {
                    // Try to find the topmost verse in left reader
                    const verses = leftContentArea.querySelectorAll('.verse[data-verse]');
                    if (verses.length > 0) {
                        const containerRect = leftContentArea.getBoundingClientRect();
                        const containerTop = containerRect.top;

                        for (const verse of verses) {
                            const verseRect = verse.getBoundingClientRect();
                            if (verseRect.top >= containerTop) {
                                leftVerse = parseInt(verse.getAttribute('data-verse')) || 1;
                                break;
                            }
                        }
                    }
                }

                console.log('RightReader: Immediately syncing to current left reader position');
                logStatus(`📨 Syncing to left reader: ${leftBook} ${leftChapter}:${leftVerse}`);
                loadPassage(leftBook, leftChapter, leftVerse);
            }
        }
    });

    followSelectionToggle.addEventListener('change', () => {
        if (isUpdatingCheckboxes) return; // Prevent infinite loops

        const status = followSelectionToggle.checked ? 'ENABLED' : 'DISABLED';
        logStatus(`📍 Follow text selection: ${status}`);
        console.log('RightReader: Follow selection toggle changed to', followSelectionToggle.checked);

        if (followSelectionToggle.checked) {
            isUpdatingCheckboxes = true;
            // Auto-uncheck left reader follow checkboxes to make it main
            leftFollowScrollToggle.checked = false;
            leftFollowSelectionToggle.checked = false;
            // Enable Follow Verse Scroll by default when text selection is enabled
            if (!followScrollToggle.checked) {
                followScrollToggle.checked = true;
                logStatus('📍 Follow verse scroll: ENABLED (default with text selection)');
            }
            logStatus('📍 Right reader is now FOLLOWER, left reader is now MAIN');

            // Update MockMediator to know left reader is now main
            MockMediator.setMainReader('left', 'right follow selection checked');

            setTimeout(() => { isUpdatingCheckboxes = false; }, 100);

            // Immediately sync to current left reader position
            {
                // Get left reader's current state directly from its controls
                const leftBookSelect = document.getElementById('left-reader-book');
                const leftChapterInput = document.getElementById('left-reader-chapter');

                if (leftBookSelect && leftChapterInput && leftBookSelect.value && leftChapterInput.value) {
                    const leftBook = leftBookSelect.value; // Chinese abbreviation
                    const leftChapter = parseInt(leftChapterInput.value);

                    // Try to get current verse from left reader's scroll position
                    const leftContentArea = document.getElementById('left-reader-content-area');
                    let leftVerse = 1; // Default to verse 1

                    if (leftContentArea) {
                        // Try to find the topmost verse in left reader
                        const verses = leftContentArea.querySelectorAll('.verse[data-verse]');
                        if (verses.length > 0) {
                            const containerRect = leftContentArea.getBoundingClientRect();
                            const containerTop = containerRect.top;

                            for (const verse of verses) {
                                const verseRect = verse.getBoundingClientRect();
                                if (verseRect.top >= containerTop) {
                                    leftVerse = parseInt(verse.getAttribute('data-verse')) || 1;
                                    break;
                                }
                            }
                        }
                    }

                    console.log('RightReader: Immediately syncing to current left reader position');
                    logStatus(`📨 Syncing to left reader: ${leftBook} ${leftChapter}:${leftVerse}`);
                    loadPassage(leftBook, leftChapter, leftVerse);
                }
            }
        } else {
            // When Follow Text Selection is unchecked, Follow Verse Scroll must be unchecked
            if (followScrollToggle.checked) {
                isUpdatingCheckboxes = true;
                followScrollToggle.checked = false;
                logStatus('📍 Follow verse scroll: DISABLED (text selection disabled)');
                setTimeout(() => { isUpdatingCheckboxes = false; }, 100);
            }
        }
    });
    // Main toggle removed - using follow checkboxes for role determination

    // Register with mediator for synchronization updates
    MockMediator.registerRightReaderUpdateCallback(loadPassage);

    /**
     * Handles right reader main toggle changes
     */
    function handleRightMainToggle() {
        if (isUpdatingCheckboxes) return; // Prevent infinite loops
        
        isUpdatingCheckboxes = true;
        const leftMainToggle = document.getElementById('left-reader-main-toggle');
        
        if (mainToggle.checked) {
            MockMediator.setMainReader('right', 'main checkbox checked');
            logStatus('📍 Set as MAIN reader (checkbox)');
            if (leftMainToggle) {
                leftMainToggle.checked = false;
            }
            
            // If right reader has content, immediately publish chapter change event
            if (currentBook && currentChapter) {
                console.log('RightReader: Publishing chapter change event immediately');
                MockMediator.publish('rightReaderChapterChanged', {
                    book: currentBook,
                    chapter: currentChapter,
                    version: versionSelect.options[versionSelect.selectedIndex]?.text || versionSelect.value,
                    internalVersionValue: currentBookChinese,
                    strong: strongToggle.checked,
                    verses: [] // Will be populated when content loads
                });
            }
            
            // Also load content to ensure it's fresh and sync position
            setTimeout(() => {
                loadChapterContent();
            }, 10);
        } else {
            MockMediator.setMainReader('left', 'right main unchecked');
            logStatus('📍 Set as FOLLOWER reader (checkbox)');
            if (leftMainToggle) {
                leftMainToggle.checked = true;
            }
        }
        
        setTimeout(() => { isUpdatingCheckboxes = false; }, 100);
    }

    /**
     * Subscribes to chapter change events from the left reader (when it's main).
     */
    MockMediator.subscribe('leftReaderChapterChanged', async (data) => {
        console.log('RightReader: Received chapter change from LeftReader:', data);
        if (MockMediator.getMainReader() === 'left') {
            // Check if follow text selection is enabled
            if (!followSelectionToggle.checked) {
                console.log('RightReader: Follow text selection disabled, ignoring chapter change event');
                logStatus('📍 Follow text selection disabled - ignoring left reader chapter change');
                return;
            }

            logStatus(`📨 Following left reader: ${data.book} ${data.chapter}`);

            // Update our controls to match the left reader
            const bookOption = Array.from(bookSelect.options).find(opt => opt.textContent === data.book);
            if (bookOption) {
                bookSelect.value = bookOption.value;
            }
            chapterInput.value = data.chapter;

            // Update tracking variables
            currentBook = data.book; // This is the display name from left reader
            currentChapter = data.chapter;
            currentBookChinese = data.internalVersionValue; // This should contain Chinese abbreviation
            currentVerses = data.verses; // Store the detailed verse data

            // Display content immediately with current settings or fetch new version
            await displaySyncedContent();
        }
    });

    /**
     * Subscribes to main reader role changes
     */
    MockMediator.subscribe('mainReaderChanged', (data) => {
        if (data.newMain === 'right') {
            logStatus(`🎯 Now MAIN reader (${data.interaction})`);
        } else {
            logStatus(`👥 Now FOLLOWER reader (${data.interaction})`);
        }
    });

    /**
     * Load passage callback for mediator synchronization
     * @param {string} book - Chinese book abbreviation
     * @param {number} chapter - Chapter number
     * @param {number} verse - Verse number for scrolling
     */
    function loadPassage(book, chapter, verse) {
        console.log(`RightReader: Loading passage ${book} ${chapter}:${verse} (following left reader)`);

        // Find corresponding English book name for display
        const bookEntry = books.find(b => b.chinese === book);
        const targetBook = bookEntry ? bookEntry.english : book;

        // Check if we need to load new chapter content or just scroll to verse
        const currentDisplayedBook = bookSelect.options[bookSelect.selectedIndex]?.text;
        const currentDisplayedChapter = parseInt(chapterInput.value);

        if (currentDisplayedBook !== targetBook || currentDisplayedChapter !== chapter) {
            // Need to load different chapter - check if follow text selection is enabled
            if (!followSelectionToggle.checked) {
                console.log('RightReader: Follow text selection disabled, ignoring book/chapter change');
                logStatus('📍 Follow text selection disabled - not following book/chapter changes');
                return;
            }
        } else {
            // Same chapter, just verse scrolling - check if follow verse scroll is enabled
            if (!followScrollToggle.checked) {
                console.log('RightReader: Follow verse scroll disabled, ignoring verse scroll');
                logStatus('📍 Follow verse scroll disabled - not following verse changes');
                return;
            }
        }

        if (currentDisplayedBook !== targetBook || currentDisplayedChapter !== chapter) {
            // Need to load different chapter
            logStatus(`📨 Following left reader: ${targetBook} ${chapter}`);
            
            // Update our controls to match
            const bookOption = Array.from(bookSelect.options).find(opt => opt.textContent === targetBook);
            if (bookOption) {
                bookSelect.value = bookOption.value;
            }
            chapterInput.value = chapter;
            
            // Update tracking variables
            currentBookChinese = book;
            currentChapter = chapter;
            currentBook = targetBook;
            
            // Load the content with our current settings
            displaySyncedContent().then(() => {
                // After loading, scroll to the specific verse
                setTimeout(() => scrollToVerse(verse), 100);
            });
        } else {
            // Same chapter, just scroll to the verse
            scrollToVerse(verse);
        }
    }

    /**
     * Removes version prefixes from verse text since version is already shown in header
     * @param {string} text - Original verse text
     * @param {string} versionName - Version display name to remove
     * @returns {string} Cleaned verse text
     */
    function cleanVerseText(text, versionName) {
        if (!text) return text;
        
        // Remove version prefixes like [UNV], [KJV], [ESV], etc.
        let cleanedText = text.replace(/^\[.*?\]\s*/, '');
        
        // Also remove version name if it appears at the beginning
        if (versionName) {
            const versionPattern = new RegExp(`^\\[?${versionName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\]?\\s*`, 'i');
            cleanedText = cleanedText.replace(versionPattern, '');
        }
        
        return cleanedText.trim();
    }

    /**
     * Parses Strong's numbers from embedded tags and makes them clickable
     * @param {string} text - Text with embedded Strong's tags in various formats
     * @returns {string} HTML with clickable Strong's numbers
     */
    function parseStrongsNumbers(text) {
        let result = text;
        
        // Format 1: {<WH1234>} or {<WG5678>}
        result = result.replace(/\{<W([HG])(\d+)>\}/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
        });

        // Format 2: {H1234} or {G5678}
        result = result.replace(/\{([HG])(\d+)\}/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
        });

        // Format 3: <WH1234> or <WG5678>
        result = result.replace(/<W([HG])(\d+)>/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
        });

        // Format 4: (H1234) or (G5678)
        result = result.replace(/\(([HG])(\d+)\)/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
        });
        
        return result;
    }

    /**
     * Loads the chapter content based on selected book, chapter, version, and Strong's numbers preference.
     */
    async function loadChapterContent() {
        const book = bookSelect.value;
        const chapter = chapterInput.value;
        const version = versionSelect.value;
        const strong = strongToggle.checked ? "1" : "0";

        // Update current state variables for scroll synchronization
        currentBookChinese = book; // Chinese abbreviation
        currentChapter = parseInt(chapter);
        const bookEntry = books.find(b => b.chinese === book);
        currentBook = bookEntry ? bookEntry.english : book; // English display name

        // Priority order: 1. Local JSON file, 2. localStorage, 3. API fetch

        // 1. Check for local JSON file first
        const versionName = version.toUpperCase();
        const localJsonFile = `${currentBookChinese}_${currentChapter}_${versionName}_edited.json`;

        try {
            console.log(`[LOAD] Checking for local JSON file: ${localJsonFile}`);
            const response = await fetch(localJsonFile);
            if (response.ok) {
                const jsonData = await response.json();
                console.log(`[LOAD] Found local JSON file: ${localJsonFile}`);
                logStatus(`📁 Loading from file: ${localJsonFile}`);

                await loadFromJsonFile(jsonData);
                return; // Skip localStorage and API fetch
            }
        } catch (error) {
            console.log(`[LOAD] No local JSON file found (${localJsonFile}), checking localStorage...`);
        }


        // Log the API URL being used
        const fhlUrl = `https://bible.fhl.net/json/qb.php?version=${version}&chineses=${encodeURIComponent(book)}&chap=${chapter}&strong=${strong}`;
        logStatus(`API URL: ${fhlUrl}`);

        const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
        const langTranslations = translations[selectedLanguage] || translations.en;

        if (!book || !chapter) {
            contentArea.innerHTML = `<p>${langTranslations.pleaseSelectBookAndChapter}</p>`;
            return;
        }

        contentArea.innerHTML = `<p>${langTranslations.loading} ${bookSelect.options[bookSelect.selectedIndex].text} ${langTranslations.leftReaderChapterLabel.toLowerCase()} ${chapter}...</p>`;

        try {
            logStatus(`Loading ${bookSelect.options[bookSelect.selectedIndex].text} ${chapter} (${version})...`);
            console.log(`RightReader: Fetching from mediator for ${book} ${chapter} (${version})`);

            // Use the mediator to fetch chapter data from bible.fhl.net
            const apiResponse = await MockMediator.fetchChapter(book, parseInt(chapter), version, parseInt(strong));
            
            if (apiResponse.status === 'error') {
                throw new Error(apiResponse.message);
            }

            // Transform the response to match the expected format for rendering
            const selectedVersionOption = versionSelect.options[versionSelect.selectedIndex];
            const versionDisplayText = selectedVersionOption ? selectedVersionOption.text : version.toUpperCase();
            
            const data = {
                book: bookSelect.options[bookSelect.selectedIndex].text,
                chapter: parseInt(chapter),
                version: versionDisplayText,
                strong: strong === "1",
                verses: apiResponse.data.verses.map(verse => ({
                    verse: verse.verse_num,
                    text: cleanVerseText(verse.text, versionDisplayText),
                    strongs: [] // Strong's numbers will be embedded in the text from FHL
                }))
            };

            console.log(`RightReader: Loaded ${data.verses.length} verses from FHL API`);
            logStatus(`✅ Loaded ${data.verses.length} verses successfully`);

            renderChapter(data);
            
            // Publish an event that the right reader's content has changed (only if this is the main reader)
            if (MockMediator.getMainReader() === 'right') {
                MockMediator.publish('rightReaderChapterChanged', {
                    book: data.book,
                    chapter: parseInt(chapter),
                    version: data.version,
                    internalVersionValue: book, // Pass the Chinese book abbreviation for API calls
                    strong: data.strong,
                    verses: data.verses
                });

                // Also sync position with mediator for left reader
                MockMediator.syncPosition({
                    book: book, // Chinese abbreviation
                    chapter: parseInt(chapter),
                    verse: 1, // Default to first verse
                    rightReaderVersion: version
                });
            }

        } catch (error) {
            console.error('RightReader: Error loading chapter content:', error);
            logStatus(`❌ Error: ${error.message}`);
            contentArea.innerHTML = `<p>Error loading content: ${error.message}. Please ensure the backend is running and the API is correct.</p>`;
        }
    }

    /**
     * Displays the content in the right reader, synchronized with the left reader.
     * This might involve re-fetching data if a different version is selected,
     * or re-rendering if only Strong's numbers preference changed.
     */
    async function displaySyncedContent() {
        const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
        const langTranslations = translations[selectedLanguage] || translations.en;

        if (!currentBook || !currentChapter || !currentBookChinese) {
            contentArea.innerHTML = `<p>${langTranslations.secondReaderWaiting}</p>`;
            return;
        }

        const selectedVersion = versionSelect.value;
        const showStrongs = strongToggle.checked;

        contentArea.innerHTML = `<p>${langTranslations.loading} ${currentBook} ${langTranslations.leftReaderChapterLabel.toLowerCase()} ${currentChapter} (${selectedVersion.toUpperCase()})...</p>`;

        try {
            // Log the API URL being used
            const fhlUrl = `https://bible.fhl.net/json/qb.php?version=${selectedVersion}&chineses=${encodeURIComponent(currentBookChinese)}&chap=${currentChapter}&strong=${showStrongs ? 1 : 0}`;
            logStatus(`API URL: ${fhlUrl}`);
            logStatus(`Loading ${currentBook} ${currentChapter} (${selectedVersion})...`);

            console.log(`SecondReader: Fetching ${selectedVersion} for ${currentBookChinese}, Strongs: ${showStrongs}`);
            
            // Use mediator to fetch chapter data from bible.fhl.net
            const apiResponse = await MockMediator.fetchChapter(
                currentBookChinese, 
                currentChapter, 
                selectedVersion, 
                showStrongs ? 1 : 0
            );
            
            if (apiResponse.status === 'error') {
                throw new Error(apiResponse.message);
            }

            // Get version display text
            const versionOption = Array.from(versionSelect.options).find(opt => opt.value === selectedVersion);
            const versionDisplayText = versionOption ? versionOption.text : selectedVersion.toUpperCase();

            const data = {
                book: currentBook,
                chapter: currentChapter,
                version: versionDisplayText,
                strong: showStrongs,
                verses: apiResponse.data.verses.map(verse => ({
                    verse: verse.verse_num,
                    text: cleanVerseText(verse.text, versionDisplayText),
                    strongs: [] // Strong's numbers are embedded in text from FHL
                }))
            };

            console.log(`SecondReader: Loaded ${data.verses.length} verses from FHL API`);
            logStatus(`✅ Loaded ${data.verses.length} verses successfully`);
            renderChapter(data);
        } catch (error) {
            console.error('SecondReader: Error loading/displaying chapter content:', error);
            logStatus(`❌ Error: ${error.message}`);
            contentArea.innerHTML = `<p>Error loading content for second reader: ${error.message}</p>`;
        }
    }

    /**
     * Helper to check if the main reader's data included Strong's numbers.
     * This is a simplified check based on the current main_reader_frontend.js behavior.
     */
    function mainReaderProvidedStrongs() {
        // Check if the first verse from main reader has some strongs data.
        // This relies on main_reader_frontend.js providing strongs data if it was loaded.
        // The structure of `currentVerses` comes from the main reader's `mockData.verses`
        // which now conditionally includes strongs based on its own strong toggle.
        // So, if main reader's strong toggle was on for its 'unv' (or other) load, it should be here.
        return currentVerses && currentVerses.length > 0 && currentVerses[0] && currentVerses[0].strongs && currentVerses[0].strongs.length > 0;
    }


    /**
     * Renders the chapter content in the second reader's content area.
     * @param {object} data - The chapter data.
     */
    function renderChapter(data) {
        const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
        const langTranslations = translations[selectedLanguage] || translations.en;

        // data.version already contains the display text from mockFetchedData or main reader
        let htmlContent = `<h3>${data.book} ${data.chapter} (${data.version})`;
        htmlContent += data.strong ? ` - ${langTranslations.strongsOn}` : ` - ${langTranslations.strongsOff}`;
        htmlContent += `</h3>`;

        data.verses.forEach(verse => {
            htmlContent += `<p class="verse" data-verse="${verse.verse}">`;
            htmlContent += `<span class="verse-number">${verse.verse}</span> `;

            // Clean and parse verse text
            let verseText = cleanVerseText(verse.text, data.version);
            
            // Parse Strong's numbers from the text (embedded as {<WH1234>} or {<WG5678>})
            if (data.strong) {
                verseText = parseStrongsNumbers(verseText);
            } else {
                // Remove Strong's number tags if toggle is off (all formats including FHL format)
                verseText = verseText.replace(/<W[HG]\d+>/g, '');       // <WH123> - FHL format
                verseText = verseText.replace(/<[HG]\d+>/g, '');        // <H123> - Alternative format
                verseText = verseText.replace(/\{<W[HG]\d+>\}/g, '');   // {<WH123>} - Wrapped format
                verseText = verseText.replace(/\{[HG]\d+\}/g, '');      // {H123} - Simple format
            }
            htmlContent += verseText;
            htmlContent += `</p>`;
        });
        contentArea.innerHTML = htmlContent;

        // Re-add resize handle (SE only - S handle is now outside content area)
        if (!contentArea.querySelector('.resize-handle-se')) {
            const seHandle = document.createElement('div');
            seHandle.className = 'resize-handle-se';
            contentArea.appendChild(seHandle);
        }

        if (data.strong) {
            attachStrongsEventListenersSecondReader();
        }

        // Restore edited content after rendering if in edit mode
        if (isEditMode) {
            setTimeout(() => {
                restoreEditedContent();

                // CRITICAL: After restoring content, hide Strong's numbers if toggle is unchecked
                // This fixes the issue where localStorage content has Strong's numbers embedded
                if (!strongToggle.checked) {
                    const strongsElements = contentArea.querySelectorAll('.strongs-number');
                    strongsElements.forEach(el => {
                        el.style.display = 'none';
                    });
                    console.log(`[RENDER] Hid ${strongsElements.length} Strong's numbers after content restoration`);
                }

                // Apply word mapping after restoration completes
                setTimeout(() => {
                    triggerWordMapping(data.chapter);
                }, 50);
            }, 100);
        } else {
            // Apply proactive word mapping highlighting for non-edit mode
            setTimeout(() => {
                triggerWordMapping(data.chapter);
            }, 200);
        }
    }

    /**
     * Triggers automatic word mapping between left and right readers
     * @param {number} chapter - Current chapter number
     */
    function triggerWordMapping(chapter) {
        try {
            // Get left reader content area
            const leftContentArea = document.getElementById('left-reader-content-area');
            if (!leftContentArea) {
                logStatus('🔗 Word mapping: No left reader found');
                return;
            }

            // Validate book/chapter synchronization for effective word mapping
            const leftBookSelect = document.getElementById('left-reader-book');
            const leftChapterInput = document.getElementById('left-reader-chapter');

            if (leftBookSelect && leftChapterInput) {
                const leftBook = leftBookSelect.value;
                const leftChapter = parseInt(leftChapterInput.value);

                // Only create word mappings if both readers are on the same book/chapter
                if (leftBook !== currentBookChinese || leftChapter !== currentChapter) {
                    logStatus(`🔗 Word mapping skipped: Book/chapter mismatch (L:${leftBook}/${leftChapter} vs R:${currentBookChinese}/${currentChapter})`);
                    return;
                }

                logStatus(`🔗 Starting word mapping for synchronized readers: ${currentBookChinese} ${currentChapter}`);
            }

            // Get all verses in both readers
            const leftVerses = leftContentArea.querySelectorAll('.verse[data-verse]');
            const rightVerses = contentArea.querySelectorAll('.verse[data-verse]');

            let mappingsCreated = 0;

            // Process each verse pair
            leftVerses.forEach(leftVerse => {
                const verseId = leftVerse.getAttribute('data-verse');
                const rightVerse = contentArea.querySelector(`[data-verse="${verseId}"]`);

                if (rightVerse) {
                    // Check if left verse has Strong's numbers
                    const strongsElements = leftVerse.querySelectorAll('.strongs-number');

                    if (strongsElements.length > 0) {
                        logStatus(`🔗 Creating word mapping for verse ${verseId}...`);

                        // Create word mapping for this verse pair
                        const mappings = WordMappingEngine.createWordMapping(leftVerse, rightVerse, verseId);

                        if (mappings.length > 0) {
                            mappingsCreated += mappings.length;
                            console.log(`Word mapping created for verse ${verseId}: ${mappings.length} pairs`);
                        }
                    }
                }
            });

            if (mappingsCreated > 0) {
                logStatus(`✅ Word mapping complete: ${mappingsCreated} word pairs highlighted across ${leftVerses.length} verses`);

                // Add click listeners to mapped words for instant Strong's suggestions
                addWordMappingClickListeners();
            } else {
                logStatus('🔗 Word mapping: No mappings created (no Strong\'s numbers in reference text)');
            }

        } catch (error) {
            logStatus(`❌ Word mapping failed: ${error.message}`);
            console.error('Word mapping error:', error);
        }
    }

    /**
     * Adds click listeners to mapped words for instant Strong's suggestions
     */
    function addWordMappingClickListeners() {
        try {
            // Add listeners to highlighted words in right reader
            const rightHighlights = contentArea.querySelectorAll('.word-mapping-highlight.right-highlight');
            rightHighlights.forEach(highlight => {
                highlight.addEventListener('click', handleMappedWordClick);
                highlight.style.cursor = 'pointer';
                highlight.title = 'Click to get Strong\'s suggestion for this word';
            });

            logStatus(`🔗 Added click listeners to ${rightHighlights.length} mapped words`);

        } catch (error) {
            logStatus(`❌ Error adding word mapping click listeners: ${error.message}`);
        }
    }

    /**
     * Handles clicks on mapped words to provide instant Strong's suggestions
     */
    function handleMappedWordClick(event) {
        // A1: Self-highlighting behavior (works regardless of edit mode)
        const clickedElement = event.target;

        // Clear previous self-highlights in right reader
        const previousSelfHighlights = contentArea.querySelectorAll('.self-highlight');
        previousSelfHighlights.forEach(element => {
            element.classList.remove('self-highlight');
        });

        // Add self-highlight to clicked word
        clickedElement.classList.add('self-highlight');
        console.log(`[A1] Applied self-highlight to clicked word: "${clickedElement.textContent}"`);

        // Strong's suggestion behavior (only in edit mode)
        if (!isEditMode) {
            logStatus('💡 Enable Edit Mode to get Strong\'s suggestions for mapped words');
            return;
        }

        const clickedWord = event.target.getAttribute('data-mapped-word');
        const strongsNumber = WordMappingEngine.getStrongsForWord(clickedWord);

        if (strongsNumber) {
            // Auto-fill Strong's input
            strongNumberInput.value = strongsNumber;

            // Get verse context for the clicked word
            const verseElement = event.target.closest('.verse');
            const verseNum = verseElement ? verseElement.getAttribute('data-verse') : 'unknown';

            // Copy to clipboard for convenience
            navigator.clipboard.writeText(strongsNumber).then(() => {
                logStatus(`💡 Clicked "${clickedWord}" in verse ${verseNum} → suggested ${strongsNumber} (copied to clipboard, ready to insert)`);
            }).catch(() => {
                logStatus(`💡 Clicked "${clickedWord}" in verse ${verseNum} → suggested ${strongsNumber} (ready to insert)`);
            });

            // Highlight the input briefly to show it was filled
            strongNumberInput.style.backgroundColor = '#e3f2fd';
            setTimeout(() => {
                strongNumberInput.style.backgroundColor = '';
            }, 1000);

            // Highlight matching Strong's number in left reader for visual confirmation
            highlightStrongsInLeftReader(strongsNumber, verseNum);

            // Focus on the input for immediate insertion
            strongNumberInput.focus();

        } else {
            const verseElement = event.target.closest('.verse');
            const verseNum = verseElement ? verseElement.getAttribute('data-verse') : 'unknown';
            logStatus(`❌ No Strong's number mapping found for "${clickedWord}" in verse ${verseNum}`);
        }
    }

    /**
     * Highlights matching Strong's numbers in left reader for visual confirmation
     */
    function highlightStrongsInLeftReader(strongsNumber, verseNum, shouldClear = true) {
        try {
            console.log(`[DEBUG] Attempting to highlight Strong's number: ${strongsNumber} in verse ${verseNum} (clear: ${shouldClear})`);

            // Clear any existing Strong's highlights first (if requested)
            if (shouldClear) {
                clearStrongsHighlighting();
            }

            // Get left reader content area
            const leftContentArea = document.getElementById('left-reader-content-area');
            if (!leftContentArea) {
                console.log('[DEBUG] Left reader content area not found');
                logStatus('❌ Left reader not found for highlighting');
                return;
            }

            console.log('[DEBUG] Left reader content area found');

            // Debug: Check what Strong's numbers exist in left reader
            const allStrongsElements = leftContentArea.querySelectorAll('.strongs-number');
            console.log(`[DEBUG] Found ${allStrongsElements.length} total Strong's elements in left reader`);

            if (allStrongsElements.length === 0) {
                // Check if left reader has Strong's toggle enabled
                const leftStrongToggle = document.getElementById('left-reader-strong-toggle');
                if (leftStrongToggle && !leftStrongToggle.checked) {
                    console.log('[DEBUG] Left reader Strong\'s toggle is OFF - enabling it');
                    leftStrongToggle.checked = true;
                    // Trigger a reload of left reader content
                    leftStrongToggle.dispatchEvent(new Event('change'));
                    logStatus('🔧 Enabled Strong\'s numbers in left reader for highlighting');

                    // Wait a moment for content to reload, then try again
                    setTimeout(() => highlightStrongsInLeftReader(strongsNumber, verseNum, false), 1000);
                    return;
                } else {
                    console.log('[DEBUG] Left reader has no Strong\'s numbers available');
                    logStatus('⚠️ No Strong\'s numbers found in left reader (may need to reload with Strong\'s enabled)');
                    return;
                }
            }

            if (allStrongsElements.length > 0) {
                console.log('[DEBUG] First few Strong\'s numbers in left reader:');
                for (let i = 0; i < Math.min(5, allStrongsElements.length); i++) {
                    const el = allStrongsElements[i];
                    console.log(`  - ${el.getAttribute('data-strong')}: "${el.textContent}"`);
                }
            }

            // Find matching Strong's numbers in left reader
            const strongsElements = leftContentArea.querySelectorAll(`.strongs-number[data-strong="${strongsNumber}"]`);
            console.log(`[DEBUG] Found ${strongsElements.length} matching elements for ${strongsNumber}`);
            let highlightCount = 0;

            // Check left reader's highlight mode preference
            const leftHighlightModeToggle = document.getElementById('left-reader-highlight-mode');
            const isSingleMode = leftHighlightModeToggle && leftHighlightModeToggle.checked;
            const mode = isSingleMode ? 'SINGLE' : 'MULTIPLE';
            console.log(`[DEBUG] Using highlight mode: ${mode}`);

            let elementsToHighlight = strongsElements;

            // If single mode is enabled, find the best match (same verse or closest)
            if (isSingleMode && strongsElements.length > 1) {
                const targetVerse = parseInt(verseNum);
                let bestMatch = null;
                let bestDistance = Infinity;

                for (const strongEl of strongsElements) {
                    // Find the verse this Strong's number belongs to
                    const verseContainer = strongEl.closest('[data-verse]');
                    if (verseContainer) {
                        const elementVerse = parseInt(verseContainer.getAttribute('data-verse'));
                        const distance = Math.abs(elementVerse - targetVerse);

                        if (distance < bestDistance) {
                            bestDistance = distance;
                            bestMatch = strongEl;
                        }
                    }
                }

                if (bestMatch) {
                    elementsToHighlight = [bestMatch];
                    console.log(`[DEBUG] Single mode: Selected nearest match in verse ${bestMatch.closest('[data-verse]')?.getAttribute('data-verse')}`);
                }
            }

            elementsToHighlight.forEach(strongEl => {
                // Add highlight class for easier clearing
                strongEl.classList.add('strongs-highlighted');

                // Add highlight styling using MATCHED_SN_HL_COLOR
                const matchedColor = typeof HighlightingFoundation !== 'undefined'
                    ? HighlightingFoundation.MATCHED_SN_HL_COLOR
                    : '#ff6b35';
                strongEl.style.backgroundColor = matchedColor;
                strongEl.style.color = 'white';
                strongEl.style.padding = '2px 4px';
                strongEl.style.borderRadius = '3px';
                strongEl.style.fontWeight = 'bold';
                strongEl.style.border = `2px solid ${matchedColor}`;

                // Add pulsing animation
                strongEl.style.animation = 'strongsPulse 2s ease-in-out infinite';
                highlightCount++;

                // === NEW: MATCHED_TERM highlighting ===
                // Find the associated word/term near this Strong's number
                const associatedTerm = findAssociatedTerm(strongEl);
                if (associatedTerm && typeof HighlightingFoundation !== 'undefined') {
                    associatedTerm.classList.add('matched-term-highlighted');
                    associatedTerm.style.backgroundColor = HighlightingFoundation.MATCHED_TERM_HL_COLOR;
                    associatedTerm.style.color = 'black';
                    associatedTerm.style.padding = '2px 4px';
                    associatedTerm.style.borderRadius = '3px';
                    associatedTerm.style.fontWeight = 'bold';
                }

                // === NEW: MATCHED_VERSE highlighting ===
                // Check if HL Ver checkbox is checked
                const hlVerCheckbox = document.getElementById('left-reader-hl-ver');
                if (hlVerCheckbox && hlVerCheckbox.checked) {
                    const verseContainer = strongEl.closest('[data-verse]');
                    if (verseContainer && typeof HighlightingFoundation !== 'undefined') {
                        verseContainer.classList.add('matched-verse-highlighted');
                        verseContainer.style.backgroundColor = HighlightingFoundation.MATCHED_VERSE_HL_COLOR;
                    }
                }
            });

            // Add CSS animation if it doesn't exist
            if (!document.getElementById('strongs-animation-style')) {
                const style = document.createElement('style');
                style.id = 'strongs-animation-style';
                style.textContent = `
                    @keyframes strongsPulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.7; }
                    }
                `;
                document.head.appendChild(style);
            }

            if (highlightCount > 0) {
                const modeText = isSingleMode ? '(single mode)' : '(multiple mode)';
                logStatus(`🔍 Highlighted ${highlightCount} matching ${strongsNumber} instances in left reader ${modeText}`);
                // Note: Highlighting timeout now managed by caller
            } else {
                logStatus(`🔍 No matching ${strongsNumber} found in left reader to highlight`);
            }
        } catch (error) {
            console.error('[DEBUG] Error in highlightStrongsInLeftReader:', error);
            logStatus(`❌ Highlighting failed: ${error.message}`);
        }
    }

    function highlightStrongsInLeftReaderNoClearing(strongsNumber, verseNum) {
        try {
            console.log(`[DEBUG] Highlighting Strong's number (no clearing): ${strongsNumber} in verse ${verseNum}`);

            // Get left reader content area
            const leftContentArea = document.getElementById('left-reader-content-area');
            if (!leftContentArea) {
                console.log('[DEBUG] Left reader content area not found');
                logStatus('❌ Left reader not found for highlighting');
                return;
            }

            console.log('[DEBUG] Left reader content area found');

            // Debug: Check what Strong's numbers exist in left reader
            const allStrongsElements = leftContentArea.querySelectorAll('.strongs-number');
            console.log(`[DEBUG] Found ${allStrongsElements.length} total Strong's elements in left reader`);

            if (allStrongsElements.length === 0) {
                // Check if left reader has Strong's toggle enabled
                const leftStrongToggle = document.getElementById('left-reader-strong-toggle');
                if (leftStrongToggle && !leftStrongToggle.checked) {
                    console.log('[DEBUG] Left reader Strong\'s toggle is OFF - enabling it');
                    leftStrongToggle.checked = true;
                    // Trigger a reload of left reader content
                    leftStrongToggle.dispatchEvent(new Event('change'));
                    logStatus('🔧 Enabled Strong\'s numbers in left reader for highlighting');

                    // Wait a moment for content to reload, then try again
                    setTimeout(() => highlightStrongsInLeftReader(strongsNumber, verseNum), 1000);
                    return;
                } else {
                    console.log('[DEBUG] Left reader has no Strong\'s numbers available');
                    logStatus('⚠️ No Strong\'s numbers found in left reader (may need to reload with Strong\'s enabled)');
                    return;
                }
            }

            if (allStrongsElements.length > 0) {
                console.log('[DEBUG] First few Strong\'s numbers in left reader:');
                for (let i = 0; i < Math.min(5, allStrongsElements.length); i++) {
                    const el = allStrongsElements[i];
                    console.log(`  - ${el.getAttribute('data-strong')}: "${el.textContent}"`);
                }
            }

            // Find matching Strong's numbers in left reader
            const strongsElements = leftContentArea.querySelectorAll(`.strongs-number[data-strong="${strongsNumber}"]`);
            console.log(`[DEBUG] Found ${strongsElements.length} matching elements for ${strongsNumber}`);
            let highlightCount = 0;

            strongsElements.forEach(strongEl => {
                // Add highlight styling using MATCHED_SN_HL_COLOR
                const matchedColor = typeof HighlightingFoundation !== 'undefined'
                    ? HighlightingFoundation.MATCHED_SN_HL_COLOR
                    : '#ff6b35';
                strongEl.style.backgroundColor = matchedColor;
                strongEl.style.color = 'white';
                strongEl.style.fontWeight = 'bold';
                strongEl.style.border = `2px solid ${matchedColor}`;
                strongEl.style.borderRadius = '4px';
                strongEl.style.padding = '2px 4px';
                strongEl.style.boxShadow = '0 2px 8px rgba(255, 107, 53, 0.4)';
                strongEl.style.transform = 'scale(1.1)';
                strongEl.style.transition = 'all 0.3s ease';
                strongEl.classList.add('strongs-highlighted');

                highlightCount++;

                // Add pulsing animation
                strongEl.style.animation = 'strongsPulse 2s ease-in-out infinite';
            });

            // Add CSS animation if it doesn't exist
            if (!document.getElementById('strongs-animation-style')) {
                const style = document.createElement('style');
                style.id = 'strongs-animation-style';
                style.textContent = `
                    @keyframes strongsPulse {
                        0%, 100% { opacity: 1; }
                        50% { opacity: 0.7; }
                    }
                `;
                document.head.appendChild(style);
            }

            if (highlightCount > 0) {
                logStatus(`🔍 Highlighted ${highlightCount} matching ${strongsNumber} instances in left reader`);

                // Note: Highlighting timeout now managed by caller
            } else {
                logStatus(`🔍 No matching ${strongsNumber} found in left reader to highlight`);
            }

        } catch (error) {
            console.error('Error highlighting Strong\'s numbers in left reader:', error);
        }
    }

    /**
     * Clears Strong's number highlighting in left reader
     */
    function clearStrongsHighlighting() {
        try {
            console.log('[DEBUG] clearStrongsHighlighting called');
            const leftContentArea = document.getElementById('left-reader-content-area');
            if (!leftContentArea) {
                console.log('[DEBUG] Left content area not found');
                return;
            }

            // Clear Strong's number highlights
            const highlightedElements = leftContentArea.querySelectorAll('.strongs-highlighted');
            console.log(`[DEBUG] Found ${highlightedElements.length} highlighted elements to clear`);

            highlightedElements.forEach((el, index) => {
                console.log(`[DEBUG] Clearing highlight ${index + 1}: ${el.getAttribute('data-strong')} - "${el.textContent}"`);

                // Remove highlight styling
                el.style.backgroundColor = '';
                el.style.color = '';
                el.style.fontWeight = '';
                el.style.border = '';
                el.style.borderRadius = '';
                el.style.padding = '';
                el.style.boxShadow = '';
                el.style.transform = '';
                el.style.transition = '';
                el.style.animation = '';
                el.classList.remove('strongs-highlighted');
            });

            // Clear MATCHED_TERM highlights
            const matchedTerms = leftContentArea.querySelectorAll('.matched-term-highlighted');
            matchedTerms.forEach(el => {
                el.style.backgroundColor = '';
                el.style.color = '';
                el.style.fontWeight = '';
                el.style.padding = '';
                el.style.borderRadius = '';
                el.classList.remove('matched-term-highlighted');
            });

            // Clear MATCHED_VERSE highlights
            const matchedVerses = leftContentArea.querySelectorAll('.matched-verse-highlighted');
            matchedVerses.forEach(el => {
                el.style.backgroundColor = '';
                el.classList.remove('matched-verse-highlighted');
            });

            console.log(`[DEBUG] Cleared ${highlightedElements.length} SN, ${matchedTerms.length} terms, ${matchedVerses.length} verses`);

        } catch (error) {
            console.error('Error clearing Strong\'s highlighting:', error);
        }
    }

    /**
     * Handles Strong's number input field changes for live highlighting
     */
    function handleStrongsInputChange() {
        const inputValue = strongNumberInput.value.trim().toUpperCase();

        if (inputValue && /^[HG]\d+$/i.test(inputValue)) {
            // Valid Strong's number format - highlight in left reader
            if (currentEditingVerse) {
                const verseNum = currentEditingVerse.getAttribute('data-verse');
                highlightStrongsInLeftReader(inputValue, verseNum);
            }
        } else {
            // Invalid or empty - clear highlighting
            clearStrongsHighlighting();
        }
    }

    /**
     * Attaches event listeners to Strong's number elements in the second reader.
     * Prevents duplicate listeners by checking for existing listeners.
     */
    function attachStrongsEventListenersSecondReader() {
        const strongsElements = contentArea.querySelectorAll('.strongs-number');
        console.log(`[ATTACH-LISTENERS] Found ${strongsElements.length} Strong's number elements`);

        strongsElements.forEach(el => {
            // Check if listener already attached (prevent duplicates)
            if (!el.hasAttribute('data-listener-attached')) {
                el.addEventListener('click', () => {
                    const strongNum = el.dataset.strong;
                    logStatus(`🔗 Strong's clicked: ${strongNum}`);
                    console.log(`SecondReader: Strong's number ${strongNum} clicked.`);
                    // Publish an event (could be the same or a different event name)
                    MockMediator.publish('strongsNumberClicked', {
                        strongNumber: strongNum,
                        version: versionSelect.value // Version from this reader
                    });
                    alert(`Strong's number clicked (Second Reader): ${strongNum}. Definition lookup not yet implemented.`);
                });

                // Mark as having listener attached
                el.setAttribute('data-listener-attached', 'true');
                console.log(`[ATTACH-LISTENERS] Added click listener to ${strongNum}`);
            } else {
                console.log(`[ATTACH-LISTENERS] Skipping ${el.dataset.strong} - listener already attached`);
            }
        });
    }

    // Subscribe to Strong's number clicks (e.g., if a central definition display is implemented)
    // MockMediator.subscribe('strongsNumberClicked', (data) => {
    //    console.log('Second reader also acknowledges Strongs click:', data);
    //    // This might be useful if the second reader also needs to react,
    //    // but typically one component would display the definition.
    // });

    /**
     * Scrolls to a specific verse in the second reader
     * @param {number} verse - Verse number to scroll to
     */
    function scrollToVerse(verse) {
        const verseElement = contentArea.querySelector(`[data-verse="${verse}"]`);
        if (verseElement) {
            // Use more precise scrolling to align exactly with left reader
            verseElement.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Fine-tune positioning after smooth scroll completes
            setTimeout(() => {
                const containerRect = contentArea.getBoundingClientRect();
                const verseRect = verseElement.getBoundingClientRect();
                const offset = verseRect.top - containerRect.top;

                // If verse is not exactly at top, adjust by small amount
                if (Math.abs(offset) > 2) {
                    contentArea.scrollTop += offset;
                }
            }, 300); // Wait for smooth scroll to complete

            // Add highlighting
            contentArea.querySelectorAll('.verse-highlighted').forEach(el => el.classList.remove('verse-highlighted'));
            verseElement.classList.add('verse-highlighted');
        }
    }

    // Add scroll event listener for synchronization
    contentArea.addEventListener('scroll', handleRightScroll);

    // Add Edit Mode event listener
    editModeToggle.addEventListener('change', handleEditModeToggle);

    // Add click listener for verse editing
    contentArea.addEventListener('click', handleVerseClick);

    // Add event listener for Strong's insertion (Enter key since button was removed)
    if (insertStrongBtn) {
        insertStrongBtn.addEventListener('click', handleInsertStrong);
    }

    // Add Enter key handler for Strong's insertion
    strongNumberInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleInsertStrong();
        }
    });

    // Add event listener for Strong's number input changes (live highlighting)
    strongNumberInput.addEventListener('input', handleStrongsInputChange);
    strongNumberInput.addEventListener('focus', handleStrongsInputChange);
    strongNumberInput.addEventListener('blur', clearStrongsHighlighting);

    // Add keyboard shortcuts for undo/redo and manual save
    document.addEventListener('keydown', function(e) {
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const cmdKey = isMac ? e.metaKey : e.ctrlKey;

        // Manual save hotkey - works in edit mode
        if (cmdKey && e.key === 's' && isEditMode) {
            e.preventDefault();
            console.log('[MANUAL-SAVE] Manual save triggered via hotkey');
            saveEditedContent();
            logStatus('💾 Manual save completed (Ctrl+S)');
            return;
        }

        // Export to JSON file hotkey (Cmd+E)
        if (cmdKey && e.key === 'e' && isEditMode) {
            e.preventDefault();
            console.log('[EXPORT] Export to JSON triggered via hotkey');
            exportToJsonFile();
            return;
        }

        // Only handle undo/redo shortcuts when in edit mode and a verse is being edited
        if (!isEditMode || !currentEditingVerse) return;

        if (cmdKey && e.key === 'z' && !e.shiftKey) {
            e.preventDefault();
            handleUndo();
        } else if (cmdKey && e.key === 'r') {
            e.preventDefault();
            handleRedo();
        }
    });

    /**
     * Auto-save system functions
     */
    function saveEditedContent() {
        console.log(`[AUTO-SAVE] saveEditedContent called. isEditMode: ${isEditMode}, currentBookChinese: ${currentBookChinese}, currentChapter: ${currentChapter}`);

        if (!isEditMode) {
            console.log('[AUTO-SAVE] Not in edit mode, skipping save');
            return;
        }

        if (!currentBookChinese || !currentChapter) {
            console.log('[AUTO-SAVE] Missing book/chapter info, skipping save');
            return;
        }

        const editedContent = {};
        const currentBookChapter = `${currentBookChinese}_${currentChapter}`;
        console.log(`[AUTO-SAVE] Checking for edited content in ${currentBookChapter}`);

        // Find all verses that have been edited (have contentEditable attribute or modified content)
        const allVerses = contentArea.querySelectorAll('[data-verse]');
        console.log(`[AUTO-SAVE] Found ${allVerses.length} verses to check`);

        allVerses.forEach(verse => {
            const verseNum = verse.getAttribute('data-verse');
            const originalContent = verse.getAttribute('data-original') || '';
            const currentContent = verse.innerHTML;

            console.log(`[AUTO-SAVE] Verse ${verseNum}:`);
            console.log(`  Original: "${originalContent.substring(0, 50)}..."`);
            console.log(`  Current:  "${currentContent.substring(0, 50)}..."`);
            console.log(`  ContentEditable: ${verse.contentEditable}`);

            // Save if content has been modified or if it's different from original
            if (currentContent !== originalContent || verse.contentEditable === 'true') {
                editedContent[verseNum] = {
                    content: currentContent,
                    original: originalContent,
                    lastModified: Date.now()
                };
                console.log(`  -> SAVING verse ${verseNum} (modified)`);
            } else {
                console.log(`  -> SKIPPING verse ${verseNum} (unchanged)`);
            }
        });

        // Save to localStorage with book/chapter key
        if (Object.keys(editedContent).length > 0) {
            const saveKey = `rightReader_edited_${currentBookChapter}`;
            localStorage.setItem(saveKey, JSON.stringify(editedContent));

            const timestamp = new Date().toLocaleTimeString();
            logStatus(`💾 Auto-saved ${Object.keys(editedContent).length} edited verses at ${timestamp}`);
            console.log(`[AUTO-SAVE] ✅ SAVED edited content for ${currentBookChapter}:`, editedContent);
            console.log(`[AUTO-SAVE] LocalStorage key: ${saveKey}`);

            // After auto-save, re-detect completed pairs and remove colors for saved Strong's numbers
            Object.keys(editedContent).forEach(verseNum => {
                const verseId = verseNum;
                const rightVerse = contentArea.querySelector(`[data-verse="${verseId}"]`);
                const leftVerse = document.querySelector(`#left-reader-content-area [data-verse="${verseId}"]`);

                if (rightVerse && leftVerse) {
                    // Re-detect completed pairs for this verse
                    WordMappingEngine.detectCompletedPairs(rightVerse, verseId);
                    // Re-apply highlighting (will skip completed pairs)
                    if (WordMappingEngine.currentMappings.length > 0) {
                        WordMappingEngine.highlightWordPairs(leftVerse, rightVerse, WordMappingEngine.currentMappings, verseId);
                    }

                    // Note: Strong's numbers now maintain green color via CSS
                }
            });
        } else {
            console.log('[AUTO-SAVE] No edited content to save');
        }

        hasUnsavedChanges = false;
    }


    /**
     * Load content from FHL-compatible JSON file
     */
    async function loadFromJsonFile(jsonData) {
        console.log(`[LOAD_JSON] Loading from JSON file:`, jsonData);

        if (!jsonData.record || !Array.isArray(jsonData.record)) {
            throw new Error('Invalid JSON format: missing record array');
        }

        const bookEntry = books.find(b => b.chinese === jsonData.book_chinese || b.chinese === currentBookChinese);
        const bookName = bookEntry ? bookEntry.english : (jsonData.book || currentBook);

        let htmlContent = `<h3>${bookName} ${currentChapter}</h3>`;

        // Sort verses by verse number
        const sortedRecords = jsonData.record.sort((a, b) => a.sec - b.sec);

        sortedRecords.forEach(record => {
            const verseNum = record.sec;
            const verseContent = record.bible_text;

            htmlContent += `
                <div class="verse-container" data-verse="${verseNum}">
                    <span class="verse-number" data-verse="${verseNum}">${verseNum}</span>
                    <span class="verse-text" data-verse="${verseNum}" contenteditable="true">${verseContent}</span>
                </div>
            `;
        });

        contentArea.innerHTML = htmlContent;

        // Attach Strong's number event listeners for click functionality
        if (strongToggle.checked) {
            attachStrongsEventListenersSecondReader();
        }

        // Restore edited content after rendering if in edit mode
        if (isEditMode) {
            setTimeout(() => {
                restoreEditedContent();
                // Apply word mapping after restoration completes
                setTimeout(() => {
                    triggerWordMapping(currentChapter);
                }, 50);
            }, 100);
        } else {
            // Apply proactive word mapping highlighting for non-edit mode
            setTimeout(() => {
                triggerWordMapping(currentChapter);
            }, 200);
        }

        logStatus(`✅ Loaded ${sortedRecords.length} verses from JSON file (${jsonData.version})`);
        console.log(`[LOAD_JSON] Successfully loaded ${sortedRecords.length} verses from JSON file`);
    }

    /**
     * Export edited content to FHL-compatible JSON file
     */
    function exportToJsonFile() {
        if (!isEditMode || !currentBookChinese || !currentChapter) {
            logStatus('❌ Cannot export: No active editing session');
            return;
        }

        const currentBookChapter = `${currentBookChinese}_${currentChapter}`;
        const saveKey = `rightReader_edited_${currentBookChapter}`;
        const savedData = localStorage.getItem(saveKey);

        if (!savedData) {
            logStatus('❌ No edited content to export');
            return;
        }

        try {
            const editedContent = JSON.parse(savedData);
            const bookEntry = books.find(b => b.chinese === currentBookChinese);
            const versionName = versionSelect.value.toUpperCase();

            // Convert to FHL API format
            const fhlFormat = {
                book: bookEntry ? bookEntry.english : currentBookChinese,
                book_chinese: currentBookChinese,
                chapter: currentChapter,
                version: versionName,
                strong_enabled: strongToggle.checked,
                record: []
            };

            // Convert edited verses to FHL record format
            Object.keys(editedContent).sort((a, b) => parseInt(a) - parseInt(b)).forEach(verseNum => {
                fhlFormat.record.push({
                    bible_text: editedContent[verseNum],
                    sec: parseInt(verseNum)
                });
            });

            // Create filename
            const filename = `${currentBookChinese}_${currentChapter}_${versionName}_edited.json`;

            // Download file
            const blob = new Blob([JSON.stringify(fhlFormat, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            logStatus(`📁 Exported: ${filename} (${Object.keys(editedContent).length} verses)`);
            console.log(`[EXPORT] Successfully exported ${filename}`);

        } catch (error) {
            console.error('[EXPORT] Error exporting to JSON:', error);
            logStatus('❌ Export failed: ' + error.message);
        }
    }

    function restoreEditedContent() {
        console.log(`[RESTORE] restoreEditedContent called. isEditMode: ${isEditMode}, currentBookChinese: ${currentBookChinese}, currentChapter: ${currentChapter}`);

        if (!isEditMode || !currentBookChinese || !currentChapter) {
            console.log('[RESTORE] Conditions not met, skipping restore');
            return;
        }

        const currentBookChapter = `${currentBookChinese}_${currentChapter}`;
        const saveKey = `rightReader_edited_${currentBookChapter}`;
        console.log(`[RESTORE] Looking for localStorage key: ${saveKey}`);

        const savedData = localStorage.getItem(saveKey);
        console.log(`[RESTORE] Retrieved data: ${savedData ? 'FOUND' : 'NOT FOUND'}`);

        if (!savedData) {
            console.log('[RESTORE] No saved data found');
            return;
        }

        try {
            const editedContent = JSON.parse(savedData);
            console.log(`[RESTORE] Parsed edited content:`, editedContent);

            let restoredCount = 0;
            const allVerses = contentArea.querySelectorAll('[data-verse]');
            console.log(`[RESTORE] Found ${allVerses.length} verses in DOM`);

            Object.keys(editedContent).forEach(verseNum => {
                console.log(`[RESTORE] Attempting to restore verse ${verseNum}`);
                const verse = contentArea.querySelector(`[data-verse="${verseNum}"]`);

                if (verse && editedContent[verseNum]) {
                    console.log(`[RESTORE] Found verse ${verseNum} in DOM`);

                    // Store original content as data attribute if not already stored
                    if (!verse.getAttribute('data-original')) {
                        console.log(`[RESTORE] Storing original content for verse ${verseNum}`);
                        verse.setAttribute('data-original', verse.innerHTML);
                    }

                    console.log(`[RESTORE] Restoring content for verse ${verseNum}:`);
                    console.log(`  From: "${verse.innerHTML.substring(0, 50)}..."`);
                    console.log(`  To:   "${editedContent[verseNum].content.substring(0, 50)}..."`);

                    // CRITICAL FIX: Extract only the verse content, preserve structure
                    const savedContent = editedContent[verseNum].content;

                    console.log(`[RESTORE] Saved content structure analysis:`);
                    console.log(`  Full saved content: "${savedContent.substring(0, 100)}..."`);

                    // Check if saved content has complete verse structure
                    if (savedContent.includes('verse-number') && savedContent.includes('verse-text')) {
                        // Saved content has complete verse-container structure
                        console.log(`[RESTORE] Saved content has complete verse-container structure`);
                        verse.innerHTML = savedContent;
                    } else if (savedContent.includes('verse-number') && !savedContent.includes('verse-text')) {
                        // Saved content has API structure with verse-number
                        console.log(`[RESTORE] Saved content has API structure with verse-number`);
                        verse.innerHTML = savedContent;
                    } else {
                        // Saved content is text-only, need to preserve current structure
                        console.log(`[RESTORE] Saved content is text-only, preserving current structure`);

                        const isCurrentVerseContainer = verse.classList.contains('verse-container');
                        if (isCurrentVerseContainer) {
                            // Preserve verse-container structure
                            const verseTextSpan = verse.querySelector('.verse-text');
                            if (verseTextSpan) {
                                verseTextSpan.innerHTML = savedContent;
                                console.log(`[RESTORE] Updated verse-text span only`);
                            } else {
                                // CRITICAL FIX: Always preserve verse number even in fallback
                                const verseNumberSpan = verse.querySelector('.verse-number');
                                const verseNum = verse.getAttribute('data-verse');
                                const verseNumberHtml = verseNumberSpan ? verseNumberSpan.outerHTML : `<span class="verse-number" data-verse="${verseNum}">${verseNum}</span>`;
                                verse.innerHTML = `${verseNumberHtml}<span class="verse-text" data-verse="${verseNum}" contenteditable="true">${savedContent}</span>`;
                                console.log(`[RESTORE] Reconstructed verse-container structure with preserved verse number`);
                            }
                        } else {
                            // Preserve API structure
                            const verseNumberSpan = verse.querySelector('.verse-number');
                            if (verseNumberSpan) {
                                verse.innerHTML = `${verseNumberSpan.outerHTML} ${savedContent}`;
                                console.log(`[RESTORE] Preserved verse-number span in API structure`);
                            } else {
                                // CRITICAL FIX: Always preserve verse number even in fallback
                                const verseNum = verse.getAttribute('data-verse');
                                verse.innerHTML = `<span class="verse-number">${verseNum}</span> ${savedContent}`;
                                console.log(`[RESTORE] Reconstructed API structure with preserved verse number`);
                            }
                        }
                    }
                    restoredCount++;

                    console.log(`[RESTORE] ✅ Successfully restored verse ${verseNum}`);
                } else {
                    console.log(`[RESTORE] ❌ Could not find verse ${verseNum} in DOM or no saved content`);
                }
            });

            if (restoredCount > 0) {
                logStatus(`📂 Restored ${restoredCount} edited verses from previous session`);
                console.log(`[RESTORE] ✅ SUCCESSFULLY restored ${restoredCount} verses for ${currentBookChapter}`);

                // CRITICAL: Re-attach event listeners to restored Strong's numbers
                if (strongToggle.checked) {
                    console.log(`[RESTORE] Re-attaching Strong's event listeners after restoration`);
                    attachStrongsEventListenersSecondReader();
                }

                // Background validation disabled to prevent corrupting user work
                // setTimeout(() => {
                //     performBackgroundValidation(editedContent);
                // }, 200);
            } else {
                console.log(`[RESTORE] ⚠️ No verses were restored`);
            }
        } catch (error) {
            console.error('[RESTORE] Error restoring edited content:', error);
            logStatus('⚠️ Error restoring previous edits');
        }
    }

    /**
     * Performs background validation tasks after content restoration
     * 1. Verifies verse content consistency with fresh FHL data
     * 2. Converts plain text Strong's numbers to proper HTML spans
     */
    async function performBackgroundValidation(editedContent) {
        console.log(`[VALIDATION] Starting background validation for ${Object.keys(editedContent).length} edited verses`);

        try {
            // Task 1: Fetch fresh content from FHL API for comparison
            await validateVerseConsistency(editedContent);

            // Task 2: Convert plain text Strong's numbers to HTML spans
            convertPlainTextStrongsToHtml();

            console.log(`[VALIDATION] ✅ Background validation completed`);
        } catch (error) {
            console.error('[VALIDATION] Error during background validation:', error);
        }
    }

    /**
     * Task 1: Validates that verse content (excluding SN) matches fresh FHL data
     */
    async function validateVerseConsistency(editedContent) {
        console.log(`[VALIDATION-CONSISTENCY] Checking verse consistency with FHL...`);

        try {
            // Fetch fresh data from FHL API
            const fhlUrl = `https://bible.fhl.net/json/qb.php?version=${versionSelect.value}&chineses=${encodeURIComponent(currentBookChinese)}&chap=${currentChapter}&strong=0`;
            console.log(`[VALIDATION-CONSISTENCY] Fetching fresh data: ${fhlUrl}`);

            const response = await fetch(fhlUrl);
            if (!response.ok) {
                throw new Error(`Failed to fetch fresh data: ${response.status}`);
            }

            const freshData = await response.json();
            if (!freshData.record || !Array.isArray(freshData.record)) {
                throw new Error('Invalid fresh data format from FHL');
            }

            let inconsistencyCount = 0;
            let checkedCount = 0;

            // Check each edited verse against fresh data
            Object.keys(editedContent).forEach(verseNum => {
                const freshVerse = freshData.record.find(r => r.sec == verseNum);
                if (!freshVerse) {
                    console.log(`[VALIDATION-CONSISTENCY] ⚠️ Verse ${verseNum} not found in fresh data`);
                    return;
                }

                const verse = contentArea.querySelector(`[data-verse="${verseNum}"]`);
                if (!verse) {
                    console.log(`[VALIDATION-CONSISTENCY] ⚠️ Verse ${verseNum} not found in DOM`);
                    return;
                }

                // Extract text content without Strong's numbers for comparison
                const editedText = extractTextWithoutStrongsNumbers(verse.textContent);
                const freshText = cleanVerseText(freshVerse.bible_text, versionSelect.value);

                checkedCount++;

                if (editedText.trim() !== freshText.trim()) {
                    inconsistencyCount++;
                    console.log(`[VALIDATION-CONSISTENCY] ❌ Inconsistency in verse ${verseNum}:`);
                    console.log(`  Edited: "${editedText.substring(0, 100)}..."`);
                    console.log(`  Fresh:  "${freshText.substring(0, 100)}..."`);

                    // AUTO-REPAIR: Extract existing Strong's numbers and restore correct text
                    const existingStrongsNumbers = extractStrongsNumbersFromVerse(verse);
                    console.log(`[VALIDATION-CONSISTENCY] 🔧 Auto-repairing verse ${verseNum} with ${existingStrongsNumbers.length} existing SN`);

                    // Restore fresh text and re-insert Strong's numbers
                    const repairedContent = restoreVerseWithStrongsNumbers(freshText, existingStrongsNumbers);
                    verse.innerHTML = repairedContent;

                    // Update localStorage with repaired content
                    editedContent[verseNum].content = repairedContent;
                    const currentBookChapter = `${currentBookChinese}_${currentChapter}`;
                    const saveKey = `rightReader_edited_${currentBookChapter}`;
                    localStorage.setItem(saveKey, JSON.stringify(editedContent));

                    console.log(`[VALIDATION-CONSISTENCY] ✅ Auto-repaired verse ${verseNum} and updated localStorage`);
                } else {
                    console.log(`[VALIDATION-CONSISTENCY] ✅ Verse ${verseNum} is consistent`);
                    verse.removeAttribute('data-inconsistent');
                    verse.removeAttribute('data-fresh-text');
                }
            });

            console.log(`[VALIDATION-CONSISTENCY] Checked ${checkedCount} verses, found ${inconsistencyCount} inconsistencies`);

            if (inconsistencyCount > 0) {
                logStatus(`🔧 Auto-repaired: ${inconsistencyCount} verses restored to FHL original text (SN preserved)`);
                console.log(`[VALIDATION-CONSISTENCY] ✅ Auto-repaired ${inconsistencyCount} inconsistent verses`);
            } else {
                console.log(`[VALIDATION-CONSISTENCY] ✅ All verses are consistent with FHL`);
            }
        } catch (error) {
            console.error('[VALIDATION-CONSISTENCY] Error validating verse consistency:', error);
        }
    }

    /**
     * Task 2: Converts plain text Strong's numbers to proper HTML spans
     */
    function convertPlainTextStrongsToHtml() {
        console.log(`[VALIDATION-STRONGS] Converting plain text Strong's numbers to HTML...`);

        const allVerses = contentArea.querySelectorAll('[data-verse]');
        let conversionCount = 0;

        allVerses.forEach(verse => {
            let verseHtml = verse.innerHTML;
            let originalHtml = verseHtml;

            // Find plain text Strong's number patterns that aren't already HTML spans
            const strongsPatterns = [
                /(?<!data-strong="[^"]*"[^>]*>)(?<!<span[^>]*>)<([HG]\d+)>(?!<\/span>)/g,  // <H1234> not already in span
                /(?<!data-strong="[^"]*"[^>]*>)(?<!<span[^>]*>)\[([HG]\d+)\](?!<\/span>)/g, // [H1234] not already in span
                /(?<!data-strong="[^"]*"[^>]*>)(?<!<span[^>]*>)\{([HG]\d+)\}(?!<\/span>)/g  // {H1234} not already in span
            ];

            strongsPatterns.forEach(pattern => {
                verseHtml = verseHtml.replace(pattern, (match, strongsId) => {
                    conversionCount++;
                    console.log(`[VALIDATION-STRONGS] Converting ${match} to HTML span in verse ${verse.getAttribute('data-verse')}`);
                    return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
                });
            });

            // Update verse if changes were made
            if (verseHtml !== originalHtml) {
                verse.innerHTML = verseHtml;
                console.log(`[VALIDATION-STRONGS] Updated verse ${verse.getAttribute('data-verse')} with converted Strong's numbers`);
            }
        });

        if (conversionCount > 0) {
            console.log(`[VALIDATION-STRONGS] ✅ Converted ${conversionCount} plain text Strong's numbers to HTML`);

            // Re-attach event listeners to newly converted Strong's numbers
            if (strongToggle.checked) {
                setTimeout(() => {
                    attachStrongsEventListenersSecondReader();
                }, 10);
            }

            logStatus(`🔧 Background fix: Converted ${conversionCount} Strong's numbers to proper format`);
        } else {
            console.log(`[VALIDATION-STRONGS] ✅ No plain text Strong's numbers found`);
        }
    }

    /**
     * Helper function to extract text content without Strong's numbers
     */
    function extractTextWithoutStrongsNumbers(text) {
        return text
            .replace(/<[HG]\d+>/g, '')      // Remove <H1234>
            .replace(/\[[HG]\d+\]/g, '')    // Remove [H1234]
            .replace(/\{[HG]\d+\}/g, '')    // Remove {H1234}
            .replace(/\s+/g, ' ')           // Normalize whitespace
            .trim();
    }

    /**
     * Extract existing Strong's numbers from a verse element
     */
    function extractStrongsNumbersFromVerse(verse) {
        const strongsNumbers = [];

        // Method 1: Extract from HTML spans with data-strong attribute
        const spanElements = verse.querySelectorAll('.strongs-number[data-strong]');
        spanElements.forEach(span => {
            const strongsId = span.getAttribute('data-strong');
            const precedingText = getPrecedingTextBeforeElement(verse, span);
            strongsNumbers.push({
                id: strongsId,
                position: precedingText.length,
                precedingText: precedingText,
                format: 'span'
            });
        });

        // Method 2: Extract from plain text patterns
        const verseHtml = verse.innerHTML;
        const patterns = [
            /<([HG]\d+)>/g,   // <H1234>
            /\[([HG]\d+)\]/g, // [H1234]
            /\{([HG]\d+)\}/g  // {H1234}
        ];

        patterns.forEach(pattern => {
            let match;
            while ((match = pattern.exec(verseHtml)) !== null) {
                const strongsId = match[1];
                const beforeMatch = verseHtml.substring(0, match.index);
                const precedingText = extractTextWithoutStrongsNumbers(beforeMatch);

                strongsNumbers.push({
                    id: strongsId,
                    position: precedingText.length,
                    precedingText: precedingText,
                    format: 'text',
                    originalMatch: match[0]
                });
            }
        });

        // Sort by position for proper insertion order
        strongsNumbers.sort((a, b) => a.position - b.position);

        console.log(`[EXTRACT-SN] Found ${strongsNumbers.length} Strong's numbers:`, strongsNumbers);
        return strongsNumbers;
    }

    /**
     * Get text content that precedes a specific element within a verse
     */
    function getPrecedingTextBeforeElement(verse, targetElement) {
        const walker = document.createTreeWalker(
            verse,
            NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
            null,
            false
        );

        let precedingText = '';
        let node;

        while (node = walker.nextNode()) {
            if (node === targetElement) {
                break;
            }
            if (node.nodeType === Node.TEXT_NODE) {
                precedingText += node.textContent;
            }
        }

        return extractTextWithoutStrongsNumbers(precedingText);
    }

    /**
     * Restore verse with fresh text and re-insert Strong's numbers at appropriate positions
     */
    function restoreVerseWithStrongsNumbers(freshText, strongsNumbers) {
        if (strongsNumbers.length === 0) {
            return freshText;
        }

        console.log(`[RESTORE-SN] Restoring verse with fresh text: "${freshText}"`);
        console.log(`[RESTORE-SN] Re-inserting ${strongsNumbers.length} Strong's numbers`);

        let result = freshText;
        let insertedChars = 0; // Track how many characters we've inserted

        // Insert Strong's numbers based on their original positions
        strongsNumbers.forEach((sn, index) => {
            // Try to find the best insertion point in the fresh text
            let insertionPoint = findBestInsertionPoint(freshText, sn, index);

            // Adjust for previously inserted characters
            insertionPoint += insertedChars;

            // Create the Strong's number span
            const strongsSpan = `<span class="strongs-number" data-strong="${sn.id}" title="Strong's ${sn.id}">&lt;${sn.id}&gt;</span>`;

            // Insert the span
            result = result.substring(0, insertionPoint) + strongsSpan + result.substring(insertionPoint);
            insertedChars += strongsSpan.length;

            console.log(`[RESTORE-SN] Inserted ${sn.id} at position ${insertionPoint}`);
        });

        console.log(`[RESTORE-SN] Final result: "${result}"`);
        return result;
    }

    /**
     * Find the best insertion point for a Strong's number in fresh text
     */
    function findBestInsertionPoint(freshText, strongsNumber, index) {
        // Strategy 1: Try to match the preceding text exactly
        const precedingText = strongsNumber.precedingText.trim();
        if (precedingText) {
            const exactMatch = freshText.indexOf(precedingText);
            if (exactMatch !== -1) {
                const insertionPoint = exactMatch + precedingText.length;
                console.log(`[FIND-INSERTION] Exact match for "${precedingText}" at position ${insertionPoint}`);
                return insertionPoint;
            }
        }

        // Strategy 2: Use character position as fallback
        const charPosition = Math.min(strongsNumber.position, freshText.length);
        console.log(`[FIND-INSERTION] Using character position ${charPosition} for ${strongsNumber.id}`);
        return charPosition;
    }

    function startAutoSave() {
        if (autoSaveTimer) {
            clearInterval(autoSaveTimer);
        }

        autoSaveTimer = setInterval(() => {
            if (hasUnsavedChanges && isEditMode) {
                saveEditedContent();
            }
        }, AUTO_SAVE_INTERVAL);

        logStatus(`🕐 Auto-save enabled: every ${AUTO_SAVE_INTERVAL / 60000} minutes`);
        console.log('[AUTO-SAVE] Timer started');
    }

    function stopAutoSave() {
        if (autoSaveTimer) {
            clearInterval(autoSaveTimer);
            autoSaveTimer = null;
            logStatus('🛑 Auto-save disabled');
            console.log('[AUTO-SAVE] Timer stopped');
        }
    }

    function markContentAsModified() {
        hasUnsavedChanges = true;
        console.log('[AUTO-SAVE] Content marked as modified');

        // Immediate save for debugging (in addition to timer)
        if (MANUAL_SAVE_ENABLED) {
            setTimeout(() => {
                console.log('[AUTO-SAVE] Triggering immediate save for debugging');
                saveEditedContent();
            }, 5000);
        }
    }

    /**
     * Handles Edit Mode toggle - minimal implementation
     */
    function handleEditModeToggle() {
        if (isUpdatingCheckboxes) return; // Prevent infinite loops

        isEditMode = editModeToggle.checked;
        logStatus(`📝 Edit Mode: ${isEditMode ? 'ENABLED' : 'DISABLED'}`);

        if (isEditMode) {
            // When edit mode is enabled, make right reader main and left reader follower
            isUpdatingCheckboxes = true;

            // Right reader (this reader) must uncheck follow boxes to become main
            followScrollToggle.checked = false;
            followSelectionToggle.checked = false;

            // Left reader must CHECK follow boxes to become follower
            leftFollowScrollToggle.checked = true;
            leftFollowSelectionToggle.checked = true;

            // Show Strong's insertion controls and left alignment spacer
            if (strongControlsContainer) strongControlsContainer.style.display = 'block';
            if (leftAlignmentSpacer) leftAlignmentSpacer.style.display = 'block';

            // Set right reader as main
            MockMediator.setMainReader('right', 'edit mode enabled');
            logStatus('📍 Right reader is now MAIN (edit mode), left reader is now FOLLOWER');
            logStatus('🔧 Strong\'s insertion controls: ENABLED');

            // Start auto-save timer
            startAutoSave();

            setTimeout(() => { isUpdatingCheckboxes = false; }, 100);

            // Immediately sync left reader to current right reader position
            if (currentBook && currentChapter) {
                // Try to get current verse from right reader's scroll position
                let currentVerse = 1; // Default to verse 1

                // Try to find the topmost verse in right reader
                const verses = contentArea.querySelectorAll('.verse[data-verse]');
                if (verses.length > 0) {
                    const containerRect = contentArea.getBoundingClientRect();
                    const containerTop = containerRect.top;

                    for (const verse of verses) {
                        const verseRect = verse.getBoundingClientRect();
                        if (verseRect.top >= containerTop) {
                            currentVerse = parseInt(verse.getAttribute('data-verse')) || 1;
                            break;
                        }
                    }
                }

                console.log('RightReader: Immediately syncing left reader to current position');
                logStatus(`📨 Syncing left reader to: ${currentBookChinese} ${currentChapter}:${currentVerse}`);

                // Use MockMediator to sync the position
                MockMediator.syncPosition({
                    book: currentBookChinese,
                    chapter: currentChapter,
                    verse: currentVerse
                });
            }

        } else {
            // Stop auto-save when edit mode is disabled
            stopAutoSave();

            // If edit mode is disabled, make any currently editing verse non-editable
            if (currentEditingVerse) {
                currentEditingVerse.contentEditable = false;
                currentEditingVerse.style.backgroundColor = '';
                currentEditingVerse.style.border = '';
                currentEditingVerse = null;
            }

            const editableVerses = contentArea.querySelectorAll('.verse[contenteditable="true"]');
            editableVerses.forEach(verse => {
                verse.contentEditable = false;
                verse.style.backgroundColor = '';
                verse.style.border = '';
            });

            // Hide Strong's insertion controls and left alignment spacer
            if (strongControlsContainer) strongControlsContainer.style.display = 'none';
            if (leftAlignmentSpacer) leftAlignmentSpacer.style.display = 'none';

            logStatus('🔧 Strong\'s insertion controls: DISABLED');
        }
    }

    /**
     * Handles paste events in verses - converts Strong's number patterns to HTML spans
     */
    function handleVersePaste(event) {
        event.preventDefault(); // Prevent default paste behavior

        // Get pasted text from clipboard
        const clipboardData = event.clipboardData || window.clipboardData;
        const pastedText = clipboardData.getData('text');

        console.log(`[PASTE] Original text: "${pastedText}"`);

        // Convert Strong's number patterns to HTML spans
        let processedText = convertStrongsToHtml(pastedText);

        console.log(`[PASTE] Processed text: "${processedText}"`);

        // Use execCommand to insert HTML properly into contenteditable
        if (document.queryCommandSupported('insertHTML')) {
            document.execCommand('insertHTML', false, processedText);
        } else {
            // Fallback for browsers that don't support insertHTML
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                range.deleteContents();

                // Create a temporary container to parse HTML
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = processedText;

                // Insert each child node
                while (tempDiv.firstChild) {
                    range.insertNode(tempDiv.firstChild);
                }

                // Collapse range to end
                range.collapse(false);
                selection.removeAllRanges();
                selection.addRange(range);
            }
        }

        // Re-attach event listeners to newly created Strong's number spans
        if (strongToggle.checked) {
            setTimeout(() => {
                attachStrongsEventListenersSecondReader();
            }, 10);
        }

        // Trigger input event for auto-save
        event.target.dispatchEvent(new Event('input', { bubbles: true }));

        logStatus(`📋 Pasted and converted Strong's numbers`);
    }

    /**
     * Converts Strong's number patterns in text to HTML spans
     */
    function convertStrongsToHtml(text) {
        let result = text;

        console.log(`[CONVERT] Input text: "${text}"`);

        // Convert various Strong's number patterns to HTML spans
        // Pattern 1: <H1234> or <G5678>
        result = result.replace(/<([HG])(\d+)>/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            console.log(`[CONVERT] Converting ${match} to span with data-strong="${strongsId}"`);
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
        });

        // Pattern 2: [H1234] or [G5678]
        result = result.replace(/\[([HG])(\d+)\]/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            console.log(`[CONVERT] Converting ${match} to span with data-strong="${strongsId}"`);
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
        });

        // Pattern 3: {H1234} or {G5678}
        result = result.replace(/\{([HG])(\d+)\}/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            console.log(`[CONVERT] Converting ${match} to span with data-strong="${strongsId}"`);
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
        });

        // Pattern 4: H1234 or G5678 (standalone)
        result = result.replace(/\b([HG])(\d+)\b/g, (match, lang, number) => {
            // Only convert if not already converted (avoid double conversion)
            if (result.includes(`data-strong="${lang}${number}"`)) {
                return match; // Already converted, leave as is
            }
            const strongsId = `${lang}${number}`;
            console.log(`[CONVERT] Converting standalone ${match} to span with data-strong="${strongsId}"`);
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">&lt;${strongsId}&gt;</span>`;
        });

        console.log(`[CONVERT] Final result: "${result}"`);
        return result;
    }

    /**
     * A1: Handles self-highlighting for any clicked element in right reader
     * Works on Strong's numbers, Chinese text, and pre-highlighted words
     */
    function handleA1SelfHighlighting(event) {
        const clickedElement = event.target;
        console.log(`[A1] Click detected on: ${clickedElement.tagName}.${clickedElement.className || 'no-class'}`);

        // Clear previous self-highlights in right reader
        const previousSelfHighlights = contentArea.querySelectorAll('.self-highlight');
        previousSelfHighlights.forEach(element => {
            element.classList.remove('self-highlight');
        });

        let targetElement = null;

        // Case 1: Click on Strong's number span
        if (clickedElement.classList.contains('strongs-number')) {
            targetElement = clickedElement;
            console.log(`[A1] Strong's number clicked: ${clickedElement.textContent}`);
        }
        // Case 2: Click on already highlighted word
        else if (clickedElement.classList.contains('word-mapping-highlight') &&
                 clickedElement.classList.contains('right-highlight')) {
            targetElement = clickedElement;
            console.log(`[A1] Pre-highlighted word clicked: ${clickedElement.textContent}`);

            // For pre-highlighted words, use the clicked element's text directly for Strong's lookup
            const clickedText = clickedElement.textContent.trim();
            if (clickedText) {
                // Find Strong's number for this specific word (use element text, not cursor position)
                const verseElement = clickedElement.closest('.verse');
                if (verseElement) {
                    const leftVerseNum = verseElement.getAttribute('data-verse');
                    const leftVerse = document.querySelector(`#left-reader-content-area .verse[data-verse="${leftVerseNum}"]`);

                    if (leftVerse) {
                        // Use direct word match instead of cursor position
                        const strongsForWord = WordMappingEngine.findStrongsByDirectMatch(leftVerse, clickedText);
                        if (strongsForWord && strongsForWord.length > 0) {
                            console.log(`[A1] Direct match for "${clickedText}": ${strongsForWord.join(', ')}`);
                            // Highlight the corresponding Strong's number in left reader
                            highlightStrongsInLeftReader(strongsForWord[0], leftVerseNum, true);
                        }
                    }
                }
            }
        }
        // Case 3: Click on Chinese text (for A2 word expansion + A1 highlighting)
        else {
            targetElement = handleChineseTextClick(event);
        }

        // Apply self-highlight to target element
        if (targetElement) {
            targetElement.classList.add('self-highlight');
            console.log(`[A1] Applied self-highlight to: "${targetElement.textContent}"`);
        }
    }

    /**
     * Simple word expansion function for A1 highlighting (without WordMappingEngine dependency)
     */
    function simpleExpandToCompleteWord(text, charPosition) {
        console.log(`[A2 Debug] simpleExpandToCompleteWord called with charPosition=${charPosition}, text="${text}"`);

        // Simple Chinese word boundary detection
        const commonWords = [
            '起初', '上帝', '創造', '天地', '混沌', '深淵', '黑暗', '光明',
            '第一', '第二', '第三', '第四', '第五', '第六', '第七',
            '早晨', '晚上', '白天', '夜晚', '空氣', '旱地', '海洋',
            '看見', '很好', '分開', '稱為', '有了', '收聚', '露出',
            '發光', '管理', '分別', '各種', '活物', '牲畜', '昆蟲',
            '野獸', '形像', '樣式', '管轄', '治理', '生養', '眾多',
            '遍滿', '征服', '食物'
        ];

        // Start with character at position
        let start = charPosition;
        let end = charPosition + 1;

        // Expand left and right to find word boundaries
        while (start > 0 && /[\u4e00-\u9fff]/.test(text[start - 1])) {
            start--;
        }
        while (end < text.length && /[\u4e00-\u9fff]/.test(text[end])) {
            end++;
        }

        // Extract the potential word
        let word = text.substring(start, end);
        console.log(`[A2 Debug] Boundary detection found: "${word}" (start=${start}, end=${end})`);

        // Try to find known multi-character words that contain our position
        for (const commonWord of commonWords) {
            const wordStart = text.indexOf(commonWord, Math.max(0, charPosition - commonWord.length));
            if (wordStart !== -1 &&
                wordStart <= charPosition &&
                charPosition < wordStart + commonWord.length) {
                console.log(`[A2 Debug] Found common word match: "${commonWord}" at position ${wordStart}`);
                return {
                    word: commonWord,
                    start: wordStart,
                    end: wordStart + commonWord.length
                };
            }
        }

        // Fall back to single character or detected boundary
        console.log(`[A2 Debug] No common word match, returning boundary detection result`);
        return {
            word: word || text[charPosition],
            start: start,
            end: end
        };
    }

    /**
     * A2: Handles clicks on Chinese text for word expansion and highlighting
     */
    function handleChineseTextClick(event) {
        const clickedElement = event.target;

        // Only handle text nodes or spans with Chinese characters
        if (clickedElement.nodeType === Node.TEXT_NODE ||
            (clickedElement.textContent && /[\u4e00-\u9fff]/.test(clickedElement.textContent))) {

            // Get cursor position for A2 word expansion
            const range = document.caretRangeFromPoint(event.clientX, event.clientY);
            if (range) {
                const textNode = range.startContainer;
                const cursorPosition = range.startOffset;

                if (textNode.nodeType === Node.TEXT_NODE) {
                    // Get full verse context for better word detection
                    const verseElement = textNode.parentElement.closest('.verse');
                    const fullVerseText = verseElement ? verseElement.textContent : textNode.textContent;

                    // Calculate cursor position in full verse context
                    let fullTextOffset = cursorPosition;
                    if (verseElement && textNode.parentElement !== verseElement) {
                        // Need to calculate offset in full verse
                        fullTextOffset = getTextOffsetInVerse(verseElement, textNode, cursorPosition);
                    }

                    console.log(`[A2 Debug] Using full verse text: "${fullVerseText.substring(0, 50)}...", offset: ${fullTextOffset}`);

                    // Simple word expansion for A1 highlighting (without dependency on WordMappingEngine)
                    const expandedWord = simpleExpandToCompleteWord(fullVerseText, fullTextOffset);

                    if (expandedWord && expandedWord.word) {
                        // Create or find a span for the expanded word in the original text node
                        const targetSpan = createHighlightSpanForText(textNode, expandedWord, cursorPosition);
                        console.log(`[A2] Chinese text click expanded: "${expandedWord.word}"`);
                        return targetSpan;
                    }
                }
            }
        }

        return null;
    }

    /**
     * Helper function to calculate text offset within verse element
     */
    function getTextOffsetInVerse(verseElement, targetTextNode, offsetInNode) {
        let totalOffset = 0;
        const walker = document.createTreeWalker(
            verseElement,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let currentNode;
        while (currentNode = walker.nextNode()) {
            if (currentNode === targetTextNode) {
                return totalOffset + offsetInNode;
            }
            totalOffset += currentNode.textContent.length;
        }

        return offsetInNode; // Fallback
    }

    /**
     * Creates a highlight span for text content to enable self-highlighting
     */
    function createHighlightSpanForText(textNode, expandedWord, cursorPosition) {
        try {
            const parent = textNode.parentNode;
            const text = textNode.textContent;

            // Find the word within the current text node
            // expandedWord.start and expandedWord.end are positions in the full verse text
            // We need to find where the word appears in this specific text node
            const wordText = expandedWord.word;

            // Search for the word around the cursor position in this text node
            let wordStartInNode = text.indexOf(wordText, Math.max(0, cursorPosition - wordText.length));

            // If not found near cursor, try exact cursor position
            if (wordStartInNode === -1 || wordStartInNode > cursorPosition || wordStartInNode + wordText.length < cursorPosition) {
                wordStartInNode = text.indexOf(wordText);
            }

            if (wordStartInNode === -1) {
                console.log(`[A2] Warning: Could not find word "${wordText}" in text node "${text}"`);
                return null;
            }

            const wordEndInNode = wordStartInNode + wordText.length;

            // Split text and create highlight span for the expanded word
            const beforeText = text.substring(0, wordStartInNode);
            const afterText = text.substring(wordEndInNode);

            // Create new span for the word
            const highlightSpan = document.createElement('span');
            highlightSpan.className = 'word-mapping-highlight right-highlight';
            highlightSpan.textContent = wordText;
            highlightSpan.title = `A2 expanded: ${wordText}`;

            // Replace text node with new structure
            if (beforeText) parent.insertBefore(document.createTextNode(beforeText), textNode);
            parent.insertBefore(highlightSpan, textNode);
            if (afterText) parent.insertBefore(document.createTextNode(afterText), textNode);
            parent.removeChild(textNode);

            return highlightSpan;
        } catch (error) {
            console.log(`[A2] Error creating highlight span: ${error.message}`);
            return null;
        }
    }

    /**
     * Handles clicks on verses when in edit mode - minimal implementation
     */
    function handleVerseClick(event) {
        // A1: Self-highlighting behavior (works for all clicks, regardless of edit mode)
        handleA1SelfHighlighting(event);

        // Edit mode behavior (only when edit mode is enabled)
        if (!isEditMode) return;

        // Find the verse element that was clicked (support both .verse and .verse-container)
        const verseElement = event.target.closest('.verse') || event.target.closest('.verse-container');
        if (!verseElement) return;

        // Clear previous editing verse
        if (currentEditingVerse && currentEditingVerse !== verseElement) {
            currentEditingVerse.contentEditable = false;
            currentEditingVerse.style.backgroundColor = '';
            currentEditingVerse.style.border = '';
        }

        // Set current editing verse
        currentEditingVerse = verseElement;

        // Save initial state for undo
        saveToUndoStack(verseElement);

        // Store original content for auto-save if not already stored
        if (!verseElement.getAttribute('data-original')) {
            verseElement.setAttribute('data-original', verseElement.innerHTML);
        }

        // Make this verse editable
        verseElement.contentEditable = true;
        verseElement.style.backgroundColor = '#fff9c4';
        verseElement.style.border = '2px solid #007cba';
        verseElement.focus();

        logStatus(`📝 Editing verse ${verseElement.getAttribute('data-verse')}`);

        // Add input event listener for cursor position changes and auto-suggestion
        verseElement.addEventListener('input', handleVerseInput);
        verseElement.addEventListener('click', handleCursorPositionChange);

        // Add paste event listener to convert pasted Strong's numbers to HTML spans
        verseElement.addEventListener('paste', handleVersePaste);

        // Add blur event to save when clicking outside (but not when clicking Insert button)
        verseElement.addEventListener('blur', function saveOnBlur(e) {
            // Don't save if user clicked on Strong's controls
            if (e.relatedTarget && (
                e.relatedTarget === insertStrongBtn ||
                e.relatedTarget === strongNumberInput ||
                strongControlsContainer.contains(e.relatedTarget)
            )) {
                return; // Keep editing active
            }

            verseElement.contentEditable = false;
            verseElement.style.backgroundColor = '';
            verseElement.style.border = '';
            currentEditingVerse = null;
            verseElement.removeEventListener('blur', saveOnBlur);
            logStatus(`💾 Saved verse ${verseElement.getAttribute('data-verse')}`);
        });
    }

    /**
     * Gets insertion context for precise status messages
     */
    function getInsertionContext(verse, range) {
        const verseText = verse.textContent;
        const cursorPosition = getTextOffset(verse, range.startContainer, range.startOffset);

        // Extract words before and after cursor
        const beforeText = verseText.substring(0, cursorPosition);
        const afterText = verseText.substring(cursorPosition);

        const beforeWords = getLastWords(beforeText, 2);
        const afterWords = getFirstWords(afterText, 2);

        return {
            position: 'middle',
            beforeText: beforeWords,
            afterText: afterWords,
            cursorPosition: cursorPosition,
            totalLength: verseText.length,
            wordCount: getWordCount(verseText)
        };
    }

    /**
     * Gets last N words from text
     */
    function getLastWords(text, count) {
        if (!text) return '';

        // Handle both English and Chinese text
        const cleanText = text.replace(/[<>()[\]{}]/g, ' ').trim();

        // For mixed English/Chinese, split on various delimiters
        const words = cleanText.split(/[\s，。！？\u3000]+/).filter(w => w.length > 0);

        return words.slice(-count).join(' ') || cleanText.slice(-10);
    }

    /**
     * Gets first N words from text
     */
    function getFirstWords(text, count) {
        if (!text) return '';

        // Handle both English and Chinese text
        const cleanText = text.replace(/[<>()[\]{}]/g, ' ').trim();

        // For mixed English/Chinese, split on various delimiters
        const words = cleanText.split(/[\s，。！？\u3000]+/).filter(w => w.length > 0);

        return words.slice(0, count).join(' ') || cleanText.slice(0, 10);
    }

    /**
     * Gets word count from text
     */
    function getWordCount(text) {
        if (!text) return 0;

        const cleanText = text.replace(/[<>()[\]{}]/g, ' ').trim();

        // Count English words and Chinese characters
        const englishWords = (cleanText.match(/[a-zA-Z]+/g) || []).length;
        const chineseChars = (cleanText.match(/[\u4e00-\u9fff]/g) || []).length;

        return englishWords + chineseChars;
    }

    /**
     * Formats precise insertion status message
     */
    function formatPreciseInsertionStatus(strongNumber, verseNum, context) {
        let status = `✅ Inserted <${strongNumber}> in verse ${verseNum}`;

        if (context.position === 'end') {
            if (context.beforeText) {
                status += ` at end after "${context.beforeText}"`;
            } else {
                status += ` at end of verse`;
            }
        } else {
            // Middle insertion
            if (context.beforeText && context.afterText) {
                status += ` after "${context.beforeText}" before "${context.afterText}"`;
            } else if (context.beforeText) {
                status += ` after "${context.beforeText}"`;
            } else if (context.afterText) {
                status += ` before "${context.afterText}"`;
            } else {
                status += ` at position ${context.cursorPosition}`;
            }
        }

        // Add word position info
        if (context.wordCount > 0) {
            status += ` (${context.wordCount} words total)`;
        }

        return status;
    }

    /**
     * Handles inserting Strong's numbers at cursor position
     */
    function handleInsertStrong() {
        let strongNumber = strongNumberInput.value.trim();

        // Validate input format
        if (!strongNumber) {
            logStatus('❌ Please enter a Strong\'s number (e.g., H1234 or G5678)');
            strongNumberInput.focus();
            return;
        }

        // Remove angle brackets if user included them
        strongNumber = strongNumber.replace(/[<>]/g, '');

        // Validate format: H/G followed by numbers (allow leading zeros)
        const strongPattern = /^[HG]\d+$/i;
        if (!strongPattern.test(strongNumber)) {
            logStatus('❌ Invalid format. Use H1234 or G5678 format (without < >)');
            strongNumberInput.focus();
            return;
        }

        console.log('Inserting Strong\'s number:', strongNumber);

        // Check if there's a currently editing verse
        if (!currentEditingVerse) {
            logStatus('❌ Please click on a verse to edit it first');
            return;
        }

        const editingVerse = currentEditingVerse;

        // Save state before insertion for undo
        saveToUndoStack(editingVerse);

        // Insert Strong's number at cursor position
        const normalizedNumber = strongNumber.toUpperCase();
        const strongsSpan = `<span class="strongs-number" data-strong="${normalizedNumber}" title="Strong's ${normalizedNumber}">&lt;${normalizedNumber}&gt;</span>`;

        // Get current selection/cursor position
        const selection = window.getSelection();
        console.log('Selection range count:', selection.rangeCount);

        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            console.log('Range ancestor:', range.commonAncestorContainer);
            console.log('Editing verse:', editingVerse);

            // Make sure we're inserting within the editing verse
            if (editingVerse.contains(range.commonAncestorContainer) || editingVerse === range.commonAncestorContainer) {
                console.log('Cursor is within editing verse, proceeding with insertion');

                // Capture context before insertion for precise status message
                const insertionContext = getInsertionContext(editingVerse, range);

                // Create a temporary div to parse the HTML
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = strongsSpan;
                const strongsElement = tempDiv.firstChild;
                console.log('Created Strong\'s element:', strongsElement);

                // Insert the Strong's number
                range.deleteContents();
                range.insertNode(strongsElement);
                console.log('Inserted Strong\'s element');

                // Move cursor after the inserted element
                range.setStartAfter(strongsElement);
                range.collapse(true);
                selection.removeAllRanges();
                selection.addRange(range);

                // Clear input and provide precise feedback
                strongNumberInput.value = '';
                const verseNum = editingVerse.getAttribute('data-verse');
                const preciseStatus = formatPreciseInsertionStatus(normalizedNumber, verseNum, insertionContext);

                // Mark content as modified for auto-save
                markContentAsModified();
                logStatus(preciseStatus);
                console.log('Successfully inserted Strong\'s number');

                // Immediately remove colors for this completed pair
                WordMappingEngine.removeColorsForNewlyInsertedStrongs(verseNum, normalizedNumber);

                // Clear Strong's highlighting after successful insertion
                clearStrongsHighlighting();

                // Focus back on the editing verse
                editingVerse.focus();
            } else {
                console.log('Cursor is NOT within editing verse');
                logStatus('❌ Please place cursor inside the verse you\'re editing');
            }
        } else {
            console.log('No selection range found');
            // If no selection, try to insert at the end of the editing verse
            if (editingVerse) {
                // Capture context for end insertion
                const endContext = {
                    position: 'end',
                    beforeText: getLastWords(editingVerse.textContent, 3),
                    afterText: '',
                    wordCount: getWordCount(editingVerse.textContent)
                };

                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = strongsSpan;
                const strongsElement = tempDiv.firstChild;

                editingVerse.appendChild(strongsElement);

                strongNumberInput.value = '';
                const verseNum = editingVerse.getAttribute('data-verse');
                const preciseStatus = formatPreciseInsertionStatus(normalizedNumber, verseNum, endContext);

                // Mark content as modified for auto-save
                markContentAsModified();
                logStatus(preciseStatus);
                console.log('Inserted at end of verse (no cursor position)');

                // Immediately remove colors for this completed pair
                WordMappingEngine.removeColorsForNewlyInsertedStrongs(verseNum, normalizedNumber);

                // Clear Strong's highlighting after successful insertion
                clearStrongsHighlighting();

                editingVerse.focus();
            } else {
                logStatus('❌ Please place cursor where you want to insert the Strong\'s number');
            }
        }
    }

    /**
     * Saves current verse state to undo stack
     */
    function saveToUndoStack(verse) {
        if (isUndoRedoAction) return; // Don't save during undo/redo operations

        const verseId = verse.getAttribute('data-verse');
        const content = verse.innerHTML;

        // Save current cursor position
        let cursorPos = 0;
        const selection = window.getSelection();
        if (selection.rangeCount > 0 && verse.contains(selection.anchorNode)) {
            const range = selection.getRangeAt(0);
            cursorPos = getTextOffset(verse, range.startContainer, range.startOffset);
        }

        const state = {
            verseId: verseId,
            content: content,
            cursorPos: cursorPos,
            timestamp: Date.now()
        };

        undoStack.push(state);

        // Limit undo stack size
        if (undoStack.length > 50) {
            undoStack.shift();
        }

        // Clear redo stack when new action is performed
        redoStack = [];

        console.log(`Saved undo state for verse ${verseId}`);
    }

    /**
     * Gets text offset for cursor position restoration
     */
    function getTextOffset(root, node, offset) {
        let textOffset = 0;
        const walker = document.createTreeWalker(
            root,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let currentNode;
        while (currentNode = walker.nextNode()) {
            if (currentNode === node) {
                return textOffset + offset;
            }
            textOffset += currentNode.textContent.length;
        }
        return textOffset;
    }

    /**
     * Gets the position of an element within the text content of its parent
     */
    function getElementTextPosition(parentElement, targetElement) {
        let position = 0;
        const walker = document.createTreeWalker(
            parentElement,
            NodeFilter.SHOW_ALL,
            null,
            false
        );

        let currentNode;
        while (currentNode = walker.nextNode()) {
            if (currentNode === targetElement) {
                return position;
            }

            // Only count text content, not element tags
            if (currentNode.nodeType === Node.TEXT_NODE) {
                position += currentNode.textContent.length;
            }
        }

        return position;
    }

    /**
     * Restores cursor position from text offset
     */
    function restoreCursorPosition(verse, textOffset) {
        const walker = document.createTreeWalker(
            verse,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );

        let currentOffset = 0;
        let currentNode;

        while (currentNode = walker.nextNode()) {
            const nodeLength = currentNode.textContent.length;
            if (currentOffset + nodeLength >= textOffset) {
                const range = document.createRange();
                const selection = window.getSelection();
                const offsetInNode = textOffset - currentOffset;

                range.setStart(currentNode, Math.min(offsetInNode, nodeLength));
                range.collapse(true);

                selection.removeAllRanges();
                selection.addRange(range);
                return;
            }
            currentOffset += nodeLength;
        }
    }

    /**
     * Handles undo operation
     */
    function handleUndo() {
        if (!currentEditingVerse || undoStack.length === 0) {
            logStatus('❌ Nothing to undo');
            return;
        }

        const verseId = currentEditingVerse.getAttribute('data-verse');

        // Find the most recent state for current verse
        let undoIndex = -1;
        for (let i = undoStack.length - 1; i >= 0; i--) {
            if (undoStack[i].verseId === verseId) {
                undoIndex = i;
                break;
            }
        }

        if (undoIndex === -1) {
            logStatus('❌ No undo history for this verse');
            return;
        }

        // Save current state to redo stack
        const currentState = {
            verseId: verseId,
            content: currentEditingVerse.innerHTML,
            cursorPos: 0,
            timestamp: Date.now()
        };
        redoStack.push(currentState);

        // Restore previous state
        const undoState = undoStack[undoIndex];
        isUndoRedoAction = true;

        currentEditingVerse.innerHTML = undoState.content;
        restoreCursorPosition(currentEditingVerse, undoState.cursorPos);

        isUndoRedoAction = false;

        // Remove the undo state we just used
        undoStack.splice(undoIndex, 1);

        logStatus(`↶ Undid change in verse ${verseId}`);
        console.log('Undo performed');
    }

    /**
     * Handles redo operation
     */
    function handleRedo() {
        if (!currentEditingVerse || redoStack.length === 0) {
            logStatus('❌ Nothing to redo');
            return;
        }

        const verseId = currentEditingVerse.getAttribute('data-verse');

        // Find the most recent redo state for current verse
        let redoIndex = -1;
        for (let i = redoStack.length - 1; i >= 0; i--) {
            if (redoStack[i].verseId === verseId) {
                redoIndex = i;
                break;
            }
        }

        if (redoIndex === -1) {
            logStatus('❌ No redo history for this verse');
            return;
        }

        // Save current state to undo stack
        saveToUndoStack(currentEditingVerse);

        // Restore redo state
        const redoState = redoStack[redoIndex];
        isUndoRedoAction = true;

        currentEditingVerse.innerHTML = redoState.content;
        restoreCursorPosition(currentEditingVerse, redoState.cursorPos);

        isUndoRedoAction = false;

        // Remove the redo state we just used
        redoStack.splice(redoIndex, 1);

        logStatus(`↷ Redid change in verse ${verseId}`);
        console.log('Redo performed');
    }

    /**
     * Handles input events in verse (for undo tracking)
     */
    function handleVerseInput(e) {
        if (!isUndoRedoAction && currentEditingVerse) {
            // Mark content as modified for auto-save
            markContentAsModified();

            // Debounce saving to undo stack during typing
            clearTimeout(window.verseInputTimeout);
            window.verseInputTimeout = setTimeout(() => {
                saveToUndoStack(currentEditingVerse);
            }, 1000);
        }
    }

    /**
     * Handles cursor position changes for auto-suggestion
     */
    function handleCursorPositionChange(e) {
        if (!currentEditingVerse || !isEditMode) return;

        // Small delay to ensure cursor position is settled
        setTimeout(() => {
            suggestStrongsFromLeftReader();
        }, 100);
    }

    /**
     * Intelligent Word Mapping Engine
     * Maps words between left (reference with Strong's) and right (target) verses
     */
    const WordMappingEngine = {
        currentMappings: [],
        completedPairs: new Set(), // Track completed word pairs: "verseId:leftWord:strongsNumber"
        colorPairs: [
            { left: '#e3f2fd', right: '#bbdefb' },  // Blue pair
            { left: '#f3e5f5', right: '#ce93d8' },  // Purple pair
            { left: '#e8f5e8', right: '#a5d6a7' },  // Green pair
            { left: '#fff3e0', right: '#ffcc02' },  // Orange pair
            { left: '#fce4ec', right: '#f8bbd9' },  // Pink pair
            { left: '#e0f2f1', right: '#80cbc4' },  // Teal pair
        ],

        /**
         * Main function: Create word mappings and apply highlighting
         */
        createWordMapping(leftVerse, rightVerse, verseId) {
            try {
                // 1. Parse reference verse (left) for word-Strong's pairs
                const referenceWords = this.parseReferenceVerse(leftVerse);
                logStatus(`🔗 Found ${referenceWords.length} reference words with Strong's`);

                // 2. Map words from left to right verse
                const mappings = this.mapWordsToTarget(referenceWords, rightVerse);
                logStatus(`🔗 Mapped ${mappings.length} word pairs`);

                // 3. Store mappings for click handling
                this.currentMappings = mappings;

                // 4. Detect completed pairs before highlighting
                this.detectCompletedPairs(rightVerse, verseId);

                // 5. Apply color highlighting (skips completed pairs)
                this.highlightWordPairs(leftVerse, rightVerse, mappings, verseId);

                return mappings;
            } catch (error) {
                logStatus(`❌ Word mapping failed: ${error.message}`);
                return [];
            }
        },

        /**
         * Parse left verse to extract word-Strong's pairs
         */
        parseReferenceVerse(leftVerse) {
            const words = [];
            const strongsElements = leftVerse.querySelectorAll('.strongs-number');

            strongsElements.forEach(strongEl => {
                const strongsNumber = strongEl.getAttribute('data-strong');
                const extractedWords = this.extractWordsNearStrongs(leftVerse, strongEl);

                extractedWords.forEach(word => {
                    if (word.trim()) {
                        words.push({
                            word: word.trim(),
                            strongs: strongsNumber,
                            confidence: 1.0
                        });
                    }
                });
            });

            return words;
        },

        /**
         * Enhanced word extraction with proper Chinese term segmentation (斷詞)
         * Recognizes whole terms like 上帝、創造 instead of individual characters
         */
        extractWordsNearStrongs(verse, strongsElement) {
            const words = [];

            // Chinese multi-character terms that should be treated as single units
            const chineseTerms = [
                '上帝', '創造', '耶和華', '天地', '起初', '空虛', '混沌', '深淵', '水面',
                '神的', '運行', '要有', '就有', '看著', '甚好', '分開', '稱為',
                '第一', '第二', '第三', '第四', '第五', '第六', '第七',
                '早晨', '晚上', '穹蒼', '旱地', '青草', '菜蔬', '果樹', '結果子',
                '各從', '其類', '光體', '大光', '小光', '管理', '晝夜', '分別',
                '明暗', '定節令', '日子', '年歲', '作記號', '海中', '空中',
                '地上', '爬物', '走獸', '牲畜', '昆蟲', '飛鳥', '各樣', '活物'
            ];

            const verseText = verse.textContent;
            const strongsText = strongsElement.textContent;
            const strongsPosition = verseText.indexOf(strongsText);

            if (strongsPosition !== -1) {
                // Look for text before the Strong's number
                const beforeText = verseText.substring(0, strongsPosition);

                // First, try to find known Chinese terms that end at this position
                for (const term of chineseTerms) {
                    if (beforeText.endsWith(term)) {
                        words.push(term);
                        console.log(`[TERM-SEGMENT] Found complete term: "${term}" → ${strongsText}`);
                        return words; // Return immediately for complete terms
                    }
                }

                // If no complete term found, extract the immediate preceding Chinese characters
                // but try to get meaningful chunks (2-3 characters when possible)
                const chineseCharsMatch = beforeText.match(/[\u4e00-\u9fff]+$/); // Chinese chars at end
                if (chineseCharsMatch) {
                    const chineseChars = chineseCharsMatch[0];

                    // For multi-character sequences, prefer whole sequence or last 2 chars
                    if (chineseChars.length >= 2) {
                        // Check if last 2 characters form a known term
                        const lastTwoChars = chineseChars.slice(-2);
                        if (chineseTerms.includes(lastTwoChars)) {
                            words.push(lastTwoChars);
                            console.log(`[TERM-SEGMENT] Found 2-char term: "${lastTwoChars}" → ${strongsText}`);
                        } else {
                            // Use the complete sequence if it's reasonable length (≤ 4 chars)
                            if (chineseChars.length <= 4) {
                                words.push(chineseChars);
                                console.log(`[TERM-SEGMENT] Using full sequence: "${chineseChars}" → ${strongsText}`);
                            } else {
                                // For very long sequences, take last 2 characters
                                words.push(lastTwoChars);
                                console.log(`[TERM-SEGMENT] Using last 2 chars: "${lastTwoChars}" → ${strongsText}`);
                            }
                        }
                    } else {
                        // Single character
                        words.push(chineseChars);
                        console.log(`[TERM-SEGMENT] Single char: "${chineseChars}" → ${strongsText}`);
                    }
                }
            }

            // Remove duplicates and filter out Strong's number patterns
            const uniqueWords = [...new Set(words)].filter(word =>
                word &&
                word.length > 0 &&
                !word.match(/^[HG]\d+$/) && // Not a Strong's number
                !word.match(/^[<>()[\]{}]+$/) // Not just punctuation
            );

            return uniqueWords;
        },

        /**
         * Map reference words to target verse words
         */
        mapWordsToTarget(referenceWords, rightVerse) {
            const mappings = [];
            const rightText = rightVerse.textContent;
            const rightWords = this.extractAllWords(rightText);

            referenceWords.forEach((refWord, index) => {
                // Try multiple matching strategies
                const matches = this.findWordMatches(refWord.word, rightWords, rightText);

                matches.forEach(match => {
                    mappings.push({
                        leftWord: refWord.word,
                        rightWord: match.word,
                        rightIndex: match.index,
                        strongs: refWord.strongs,
                        confidence: match.confidence,
                        colorPair: this.colorPairs[index % this.colorPairs.length]
                    });
                });

                if (matches.length === 0) {
                    console.log(`No match found for: ${refWord.word} (${refWord.strongs})`);
                }
            });

            return mappings;
        },

        /**
         * Extract all words from text for matching
         */
        extractAllWords(text) {
            // Handle both English and Chinese text
            const words = [];

            // English words (space-separated)
            const englishWords = text.match(/[a-zA-Z]+/g) || [];

            // Chinese words/characters (no spaces)
            const chineseChars = text.match(/[\u4e00-\u9fff]+/g) || [];

            return [...englishWords, ...chineseChars];
        },

        /**
         * Find word matches using multiple strategies
         */
        findWordMatches(leftWord, rightWords, rightText) {
            const matches = [];

            // Strategy 1: Exact match
            const exactIndex = rightText.indexOf(leftWord);
            if (exactIndex !== -1) {
                matches.push({
                    word: leftWord,
                    index: exactIndex,
                    confidence: 1.0
                });
                return matches; // Exact match found, use it
            }

            // Strategy 2: Cross-language mapping via Strong's number context
            // This is where we'd add specific translation pairs
            const crossLangMatch = this.getCrossLanguageMatch(leftWord);
            if (crossLangMatch) {
                const crossIndex = rightText.indexOf(crossLangMatch);
                if (crossIndex !== -1) {
                    matches.push({
                        word: crossLangMatch,
                        index: crossIndex,
                        confidence: 0.9
                    });
                }
            }

            // Strategy 3: Partial matching for compound words
            rightWords.forEach(rightWord => {
                if (rightWord.includes(leftWord) || leftWord.includes(rightWord)) {
                    const partialIndex = rightText.indexOf(rightWord);
                    if (partialIndex !== -1) {
                        matches.push({
                            word: rightWord,
                            index: partialIndex,
                            confidence: 0.7
                        });
                    }
                }
            });

            // Strategy 4: Phonetic/semantic similarity (simplified)
            // This could be expanded with more sophisticated algorithms
            rightWords.forEach(rightWord => {
                if (this.areSimilarWords(leftWord, rightWord)) {
                    const similarIndex = rightText.indexOf(rightWord);
                    if (similarIndex !== -1) {
                        matches.push({
                            word: rightWord,
                            index: similarIndex,
                            confidence: 0.6
                        });
                    }
                }
            });

            // Remove duplicates and sort by confidence
            const uniqueMatches = matches.filter((match, index, self) =>
                index === self.findIndex(m => m.word === match.word)
            ).sort((a, b) => b.confidence - a.confidence);

            return uniqueMatches.slice(0, 1); // Return best match only
        },

        /**
         * Cross-language word mapping dictionary
         * This can be expanded with more translation pairs
         */
        getCrossLanguageMatch(word) {
            const crossLangDict = {
                // Genesis 1:1 specific mappings
                '起初': 'beginning',
                'beginning': '起初',
                '上帝': 'God',
                'God': '上帝',
                '創造': 'created',
                'created': '創造',
                '天': 'heaven',
                'heaven': '天',
                '地': 'earth',
                'earth': '地',

                // Common theological terms
                '主': 'Lord',
                'Lord': '主',
                '耶和華': 'LORD',
                'LORD': '耶和華',
                '靈': 'Spirit',
                'Spirit': '靈',
                '道': 'Word',
                'Word': '道',
                '光': 'light',
                'light': '光',
                '愛': 'love',
                'love': '愛',
                '信': 'faith',
                'faith': '信',
                '望': 'hope',
                'hope': '望',
                '生命': 'life',
                'life': '生命',
                '永生': 'eternal',
                'eternal': '永生',
                '救': 'save',
                'save': '救',
                '罪': 'sin',
                'sin': '罪',
                '義': 'righteousness',
                'righteousness': '義'
            };

            return crossLangDict[word] || null;
        },

        /**
         * Simple similarity check for words
         */
        areSimilarWords(word1, word2) {
            // Simple length and character overlap check
            if (Math.abs(word1.length - word2.length) > 3) return false;

            const minLength = Math.min(word1.length, word2.length);
            if (minLength < 3) return false;

            let commonChars = 0;
            for (let i = 0; i < minLength; i++) {
                if (word1[i] && word2[i] && word1[i].toLowerCase() === word2[i].toLowerCase()) {
                    commonChars++;
                }
            }

            return (commonChars / minLength) > 0.6;
        },

        /**
         * Apply color highlighting to word pairs
         */
        highlightWordPairs(leftVerse, rightVerse, mappings, verseId) {
            // Clear existing highlights first
            this.clearHighlights(leftVerse);
            this.clearHighlights(rightVerse);

            mappings.forEach(mapping => {
                // Skip highlighting if this pair is already completed
                if (this.isPairCompleted(verseId, mapping.leftWord, mapping.strongs)) {
                    return;
                }

                // Highlight in left verse (find the word before Strong's number)
                this.highlightWordInVerse(leftVerse, mapping.leftWord, mapping.colorPair.left, 'left');

                // Highlight in right verse
                this.highlightWordInVerse(rightVerse, mapping.rightWord, mapping.colorPair.right, 'right');
            });
        },

        /**
         * Highlight a specific word in a verse with enhanced text parsing
         */
        highlightWordInVerse(verse, word, color, side) {
            // Try multiple highlighting strategies
            let highlighted = false;

            // Strategy 1: Direct text node highlighting (improved)
            highlighted = this.highlightInTextNodes(verse, word, color, side);

            // Strategy 2: If direct highlighting failed, try HTML-aware highlighting
            if (!highlighted) {
                highlighted = this.highlightWithHtmlAwareness(verse, word, color, side);
            }

            // Strategy 3: If still not highlighted, try partial word matching
            if (!highlighted) {
                highlighted = this.highlightPartialMatch(verse, word, color, side);
            }

            if (!highlighted) {
                console.log(`Could not highlight word "${word}" in verse`);
            }
        },

        /**
         * Enhanced text node highlighting
         */
        highlightInTextNodes(verse, word, color, side) {
            const walker = document.createTreeWalker(
                verse,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            let textNode;
            while (textNode = walker.nextNode()) {
                const text = textNode.textContent;
                const wordIndex = text.indexOf(word);

                if (wordIndex !== -1) {
                    // Check if this text node is not inside a Strong's number span
                    const parent = textNode.parentNode;
                    if (parent && parent.classList && parent.classList.contains('strongs-number')) {
                        continue; // Skip highlighting inside Strong's numbers
                    }

                    // Split text node and wrap word in highlight span
                    const beforeText = text.substring(0, wordIndex);
                    const wordText = text.substring(wordIndex, wordIndex + word.length);
                    const afterText = text.substring(wordIndex + word.length);

                    // Create highlight span
                    const highlightSpan = document.createElement('span');
                    highlightSpan.className = `word-mapping-highlight ${side}-highlight`;
                    highlightSpan.style.backgroundColor = color;
                    highlightSpan.style.padding = '1px 2px';
                    highlightSpan.style.borderRadius = '2px';
                    highlightSpan.style.cursor = 'pointer';
                    highlightSpan.style.fontWeight = 'bold';
                    highlightSpan.textContent = wordText;
                    highlightSpan.setAttribute('data-mapped-word', word);
                    highlightSpan.title = `Mapped word: ${word}`;

                    // Replace text node with highlighted version
                    if (beforeText) parent.insertBefore(document.createTextNode(beforeText), textNode);
                    parent.insertBefore(highlightSpan, textNode);
                    if (afterText) parent.insertBefore(document.createTextNode(afterText), textNode);

                    parent.removeChild(textNode);
                    return true;
                }
            }
            return false;
        },

        /**
         * HTML-aware highlighting for complex structures
         */
        highlightWithHtmlAwareness(verse, word, color, side) {
            const verseHtml = verse.innerHTML;
            const verseText = verse.textContent;

            // Find the word in the text content
            const wordIndex = verseText.indexOf(word);
            if (wordIndex === -1) return false;

            // Create a temporary div to work with HTML
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = verseHtml;

            // Find all text nodes and their positions
            let textPosition = 0;
            const walker = document.createTreeWalker(
                tempDiv,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            let textNode;
            while (textNode = walker.nextNode()) {
                const nodeText = textNode.textContent;
                const nodeEnd = textPosition + nodeText.length;

                // Check if our word falls within this text node
                if (textPosition <= wordIndex && wordIndex < nodeEnd) {
                    const relativeIndex = wordIndex - textPosition;
                    const beforeText = nodeText.substring(0, relativeIndex);
                    const wordText = nodeText.substring(relativeIndex, relativeIndex + word.length);
                    const afterText = nodeText.substring(relativeIndex + word.length);

                    // Create highlighted version
                    const parent = textNode.parentNode;
                    const highlightSpan = document.createElement('span');
                    highlightSpan.className = `word-mapping-highlight ${side}-highlight`;
                    highlightSpan.style.backgroundColor = color;
                    highlightSpan.style.padding = '1px 2px';
                    highlightSpan.style.borderRadius = '2px';
                    highlightSpan.style.cursor = 'pointer';
                    highlightSpan.style.fontWeight = 'bold';
                    highlightSpan.textContent = wordText;
                    highlightSpan.setAttribute('data-mapped-word', word);
                    highlightSpan.title = `Mapped word: ${word}`;

                    // Replace the text node
                    if (beforeText) parent.insertBefore(document.createTextNode(beforeText), textNode);
                    parent.insertBefore(highlightSpan, textNode);
                    if (afterText) parent.insertBefore(document.createTextNode(afterText), textNode);
                    parent.removeChild(textNode);

                    // Update the verse with modified HTML
                    verse.innerHTML = tempDiv.innerHTML;
                    return true;
                }

                textPosition = nodeEnd;
            }

            return false;
        },

        /**
         * Partial word matching for compound words or character-level matching
         * Enhanced to preserve Chinese term integrity (不破壞中文詞組完整性)
         */
        highlightPartialMatch(verse, word, color, side) {
            console.log(`[PARTIAL-MATCH] Attempting partial match for: "${word}"`);

            // For Chinese characters, DO NOT break apart terms that should stay together
            if (/[\u4e00-\u9fff]/.test(word)) {
                // List of terms that should NEVER be broken apart
                const integralTerms = [
                    '上帝', '創造', '耶和華', '天地', '起初', '空虛', '混沌', '深淵', '水面',
                    '神的', '運行', '要有', '就有', '看著', '甚好', '分開', '稱為'
                ];

                // If this is an integral term, only try exact matching
                if (integralTerms.includes(word)) {
                    console.log(`[PARTIAL-MATCH] "${word}" is an integral term, skipping character-by-character matching`);
                    return false; // Don't break apart integral terms
                }

                // For other Chinese words, try character-by-character only as last resort
                if (word.length === 1) {
                    // Already a single character, try direct match
                    if (this.highlightInTextNodes(verse, word, color, side)) {
                        console.log(`[PARTIAL-MATCH] Highlighted single character: ${word}`);
                        return true;
                    }
                } else {
                    // Multi-character word that's not in integral terms
                    // Try to find the whole word first, then individual chars
                    console.log(`[PARTIAL-MATCH] "${word}" not found as whole term, this may indicate a segmentation issue`);
                    return false; // Don't fall back to character matching for now
                }
            }

            // For English words, try stem matching
            if (/[a-zA-Z]/.test(word)) {
                const stem = word.length > 4 ? word.substring(0, word.length - 2) : word;
                if (stem !== word && this.highlightInTextNodes(verse, stem, color, side)) {
                    console.log(`[PARTIAL-MATCH] Highlighted stem: ${stem} for word: ${word}`);
                    return true;
                }
            }

            return false;
        },

        /**
         * Clear existing highlights and prevent rainbow edges
         */
        clearHighlights(verse) {
            // Find all highlight spans
            const highlights = verse.querySelectorAll('.word-mapping-highlight');
            highlights.forEach(highlight => {
                const parent = highlight.parentNode;
                parent.insertBefore(document.createTextNode(highlight.textContent), highlight);
                parent.removeChild(highlight);
            });

            // Normalize text nodes to prevent fragmentation that causes rainbow edges
            const walker = document.createTreeWalker(
                verse,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            const textNodes = [];
            let node;
            while (node = walker.nextNode()) {
                textNodes.push(node);
            }

            // Merge adjacent text nodes
            textNodes.forEach(textNode => {
                if (textNode.parentNode) {
                    let nextSibling = textNode.nextSibling;
                    while (nextSibling && nextSibling.nodeType === Node.TEXT_NODE) {
                        textNode.textContent += nextSibling.textContent;
                        nextSibling.parentNode.removeChild(nextSibling);
                        nextSibling = textNode.nextSibling;
                    }
                }
            });
        },

        /**
         * Get Strong's number for a clicked word
         */
        getStrongsForWord(clickedWord) {
            const mapping = this.currentMappings.find(m =>
                m.leftWord === clickedWord || m.rightWord === clickedWord
            );
            return mapping ? mapping.strongs : null;
        },

        /**
         * Detect completed word pairs by scanning for Strong's numbers in right verse
         * Enhanced to detect both data-strong and text patterns
         */
        detectCompletedPairs(rightVerse, verseId) {
            // Method 1: Find elements with data-strong attribute
            const strongsElements = rightVerse.querySelectorAll('.strongs-number[data-strong]');
            strongsElements.forEach(strongEl => {
                const strongsNumber = strongEl.getAttribute('data-strong');
                this.markStrongsAsCompleted(verseId, strongsNumber);
            });

            // Method 2: Find Strong's patterns in text content (for localStorage restored content)
            const verseText = rightVerse.textContent || rightVerse.innerHTML;
            const strongsPatterns = [
                /<H(\d+)>/g,  // <H1234>
                /<G(\d+)>/g,  // <G1234>
                /\[H(\d+)\]/g, // [H1234]
                /\[G(\d+)\]/g, // [G1234]
                /{H(\d+)}/g,  // {H1234}
                /{G(\d+)}/g   // {G1234}
            ];

            strongsPatterns.forEach(pattern => {
                let match;
                while ((match = pattern.exec(verseText)) !== null) {
                    const strongsNumber = match[1] ? `${match[0].includes('H') ? 'H' : 'G'}${match[1]}` : match[0];
                    console.log(`[DETECT-COMPLETED] Found Strong's pattern: ${strongsNumber} in verse ${verseId}`);
                    this.markStrongsAsCompleted(verseId, strongsNumber);
                }
            });

            console.log(`[DETECT-COMPLETED] Completed pairs for verse ${verseId}:`,
                Array.from(this.completedPairs).filter(key => key.startsWith(`${verseId}:`)));
        },

        /**
         * Mark all mappings with this Strong's number as completed
         */
        markStrongsAsCompleted(verseId, strongsNumber) {
            // Normalize Strong's number format
            const normalizedStrongs = strongsNumber.replace(/[<>\[\]{}]/g, '');

            this.currentMappings.forEach(mapping => {
                const mappingStrongs = mapping.strongs.replace(/[<>\[\]{}]/g, '');
                if (mappingStrongs === normalizedStrongs) {
                    const pairKey = `${verseId}:${mapping.leftWord}:${mapping.strongs}`;
                    this.completedPairs.add(pairKey);
                    console.log(`[MARK-COMPLETED] Added completed pair: ${pairKey}`);
                }
            });
        },

        /**
         * Check if a word pair is completed (has Strong's number inserted)
         */
        isPairCompleted(verseId, leftWord, strongsNumber) {
            const pairKey = `${verseId}:${leftWord}:${strongsNumber}`;
            return this.completedPairs.has(pairKey);
        },

        /**
         * Remove colors for newly inserted Strong's numbers (immediate feedback)
         * Ensures Strong's numbers retain their default green color (#28a745)
         */
        removeColorsForNewlyInsertedStrongs(verseId, strongsNumber) {
            // Mark all mappings with this Strong's number as completed
            this.currentMappings.forEach(mapping => {
                if (mapping.strongs === strongsNumber) {
                    const pairKey = `${verseId}:${mapping.leftWord}:${strongsNumber}`;
                    this.completedPairs.add(pairKey);
                    console.log(`[REMOVE-COLORS] Marked as completed: ${pairKey}`);
                }
            });

            // Re-apply word mapping to remove colors from Chinese words
            const leftVerse = document.querySelector('#left-reader-content-area [data-verse="' + verseId + '"]');
            const rightVerse = document.querySelector('#right-reader-content-area [data-verse="' + verseId + '"]');

            if (leftVerse && rightVerse) {
                this.highlightWordPairs(leftVerse, rightVerse, this.currentMappings, verseId);
                // Note: Strong's numbers maintain green color via CSS
            }
        },

    };

    /**
     * Abstract Suggestion Engine - Black Box Interface
     * Future: Can be replaced with AI/ML, better algorithms, external APIs, etc.
     */
    const SuggestionEngine = {
        /**
         * Main suggestion interface - gets Strong's suggestion for cursor position
         * @param {Object} context - All context needed for suggestion
         * @returns {string|null} - Suggested Strong's number or null
         */
        getSuggestion(context) {
            try {
                // Validate context
                if (!this.validateContext(context)) return null;

                // Use current position-based algorithm (pluggable)
                return this.algorithms.positionBased(context);
            } catch (error) {
                logStatus(`❌ Suggestion Engine Error: ${error.message}`);
                return null;
            }
        },

        /**
         * Validates suggestion context
         */
        validateContext(context) {
            return context && context.rightVerse && context.leftVerse &&
                   typeof context.cursorPosition === 'number';
        },

        /**
         * Pluggable algorithms - can be swapped/improved
         */
        algorithms: {
            /**
             * Current position-based matching (temporary implementation)
             */
            positionBased(context) {
                const { leftVerse, cursorPosition, verseId, rightVerse } = context;

                logStatus(`🔍 Suggestion: Verse ${verseId}, cursor at pos ${cursorPosition}`);

                const strongsElements = leftVerse.querySelectorAll('.strongs-number');
                if (strongsElements.length === 0) {
                    logStatus('🔍 Suggestion: No Strong\'s numbers in reference text');
                    return null;
                }

                // Use word-based matching instead of character position
                const suggestion = this.findStrongsByWordContext(leftVerse, rightVerse, cursorPosition);

                if (suggestion) {
                    const strongDisplay = Array.isArray(suggestion.strong) ? suggestion.strong.join(', ') : suggestion.strong;
                    logStatus(`💡 Suggestion: Found ${strongDisplay} for word "${suggestion.word}" (confidence: ${suggestion.confidence})`);
                    return suggestion.strong;
                }

                logStatus(`🔍 Suggestion: No matching word found at cursor position`);
                return null;
            },

            /**
             * Find Strong's number by analyzing word context around cursor
             */
            findStrongsByWordContext(leftVerse, rightVerse, cursorPosition) {
                // Get the word at cursor position in right verse
                const rightText = rightVerse.textContent;
                const wordAtCursor = this.getWordAtPosition(rightText, cursorPosition);

                if (!wordAtCursor) {
                    console.log('[DEBUG] No word found at cursor position');
                    return null;
                }

                console.log(`[DEBUG] Word at cursor: "${wordAtCursor.word}" at position ${wordAtCursor.start}-${wordAtCursor.end}`);

                // Look for this word or its translation in the left verse
                const leftWords = this.extractWordsWithStrongs(leftVerse);

                // Strategy 1: Direct match (same language) - collect ALL matches
                const directMatches = [];
                for (const leftWord of leftWords) {
                    if (leftWord.word === wordAtCursor.word) {
                        console.log(`[DEBUG] Direct match found: ${leftWord.word} → ${leftWord.strong}`);
                        // Handle both single Strong's numbers and arrays
                        if (Array.isArray(leftWord.strong)) {
                            directMatches.push(...leftWord.strong);
                        } else {
                            directMatches.push(leftWord.strong);
                        }
                    }
                }

                // Strategy 1.5: Check for multi-character words that contain the clicked character
                for (const leftWord of leftWords) {
                    if (leftWord.word.includes(wordAtCursor.word) && leftWord.word.length > 1) {
                        console.log(`[DEBUG] Multi-char match found: "${leftWord.word}" contains "${wordAtCursor.word}" → ${Array.isArray(leftWord.strong) ? leftWord.strong.join(', ') : leftWord.strong}`);
                        // Handle both single Strong's numbers and arrays
                        if (Array.isArray(leftWord.strong)) {
                            directMatches.push(...leftWord.strong);
                        } else {
                            directMatches.push(leftWord.strong);
                        }
                    }
                }

                if (directMatches.length > 0) {
                    // Remove duplicates
                    const uniqueMatches = [...new Set(directMatches)];
                    console.log(`[DEBUG] Found ${uniqueMatches.length} Strong's numbers for "${wordAtCursor.word}": ${uniqueMatches.join(', ')}`);
                    return {
                        word: wordAtCursor.word,
                        strong: uniqueMatches.length === 1 ? uniqueMatches[0] : uniqueMatches,
                        confidence: 1.0
                    };
                }

                // Strategy 2: Cross-language translation
                const translation = this.getTranslation(wordAtCursor.word);
                if (translation) {
                    for (const leftWord of leftWords) {
                        if (leftWord.word === translation) {
                            console.log(`[DEBUG] Translation match: ${wordAtCursor.word} → ${translation} → ${leftWord.strong}`);
                            return {
                                word: wordAtCursor.word,
                                strong: leftWord.strong,
                                confidence: 0.9
                            };
                        }
                    }
                }

                // Strategy 3: Positional matching (as fallback)
                const wordPosition = this.getWordPositionInVerse(rightVerse, wordAtCursor);
                const closestLeftWord = this.getWordAtSimilarPosition(leftWords, wordPosition);

                if (closestLeftWord) {
                    console.log(`[DEBUG] Positional match: ${wordAtCursor.word} → ${closestLeftWord.word} → ${closestLeftWord.strong}`);
                    return {
                        word: wordAtCursor.word,
                        strong: closestLeftWord.strong,
                        confidence: 0.7
                    };
                }

                return null;
            },

            /**
             * A2: Expands a single Chinese character to its complete word boundary
             * @param {string} text - Full text content
             * @param {number} charPosition - Position of the Chinese character
             * @returns {Object} - {word, start, end} of the complete word
             */
            expandToCompleteWord(text, charPosition) {
                // Define common Chinese word patterns for biblical text
                const commonWords = [
                    '起初', '上帝', '創造', '天地', '混沌', '深淵', '黑暗', '光明',
                    '第一', '第二', '第三', '第四', '第五', '第六', '第七',
                    '早晨', '晚上', '白天', '夜晚', '空氣', '旱地', '海洋',
                    '各樣', '各種', '種類', '活物', '野獸', '牲畜', '飛鳥',
                    '男人', '女人', '夫妻', '生育', '管理', '治理', '看守',
                    '園子', '伊甸', '河流', '分為', '四道', '善惡', '生命',
                    '知識', '智慧', '聰明', '分別', '赤身', '羞恥', '遮掩'
                ];

                const char = text.charAt(charPosition);
                console.log(`[DEBUG] A2: Expanding character "${char}" at position ${charPosition}`);

                // Find the longest word that contains this character at this position
                let bestMatch = {
                    word: char,
                    start: charPosition,
                    end: charPosition + 1
                };

                for (const word of commonWords) {
                    const charIndex = word.indexOf(char);
                    if (charIndex !== -1) {
                        // Calculate where this word would start in the text
                        const wordStart = charPosition - charIndex;
                        const wordEnd = wordStart + word.length;

                        // Check if the complete word exists at this position
                        if (wordStart >= 0 && wordEnd <= text.length) {
                            const textSegment = text.substring(wordStart, wordEnd);
                            if (textSegment === word) {
                                console.log(`[DEBUG] A2: Found complete word "${word}" containing "${char}"`);
                                bestMatch = {
                                    word: word,
                                    start: wordStart,
                                    end: wordEnd
                                };
                                break; // Use first (longest) match
                            }
                        }
                    }
                }

                console.log(`[DEBUG] A2: Final expansion: "${bestMatch.word}" (${bestMatch.start}-${bestMatch.end})`);
                return bestMatch;
            },

            /**
             * Get word at cursor position - check LEFT of cursor first (where user clicked)
             */
            getWordAtPosition(text, position) {
                console.log(`[DEBUG] Getting word at position ${position} in text: "${text}"`);

                // Strategy 1: Check character to the LEFT of cursor (where user clicked)
                if (position > 0) {
                    const leftChar = text.charAt(position - 1);
                    console.log(`[DEBUG] Character to LEFT of cursor (position ${position - 1}): "${leftChar}"`);

                    if (/[\u4e00-\u9fff]/.test(leftChar)) {
                        console.log(`[DEBUG] Found clicked Chinese character: "${leftChar}"`);

                        // A2: Expand to complete word using word boundary detection
                        const expandedWord = this.expandToCompleteWord(text, position - 1);
                        console.log(`[DEBUG] A2: Expanded "${leftChar}" to complete word: "${expandedWord.word}"`);

                        return expandedWord;
                    }
                }

                // Strategy 2: Check character AT cursor position
                if (position < text.length) {
                    const charAtCursor = text.charAt(position);
                    console.log(`[DEBUG] Character AT cursor: "${charAtCursor}"`);

                    if (/[\u4e00-\u9fff]/.test(charAtCursor)) {
                        console.log(`[DEBUG] Found Chinese character at cursor: "${charAtCursor}"`);

                        // A2: Expand to complete word using word boundary detection
                        const expandedWord = this.expandToCompleteWord(text, position);
                        console.log(`[DEBUG] A2: Expanded "${charAtCursor}" to complete word: "${expandedWord.word}"`);

                        return expandedWord;
                    }
                }

                // Strategy 3: Look LEFT then RIGHT for nearest Chinese character
                for (let offset = 1; offset <= 3; offset++) {
                    // Check LEFT
                    if (position - offset >= 0) {
                        const leftChar = text.charAt(position - offset);
                        if (/[\u4e00-\u9fff]/.test(leftChar)) {
                            console.log(`[DEBUG] Found Chinese character ${offset} positions LEFT: "${leftChar}"`);
                            return {
                                word: leftChar,
                                start: position - offset,
                                end: position - offset + 1
                            };
                        }
                    }

                    // Check RIGHT
                    if (position + offset < text.length) {
                        const rightChar = text.charAt(position + offset);
                        if (/[\u4e00-\u9fff]/.test(rightChar)) {
                            console.log(`[DEBUG] Found Chinese character ${offset} positions RIGHT: "${rightChar}"`);
                            return {
                                word: rightChar,
                                start: position + offset,
                                end: position + offset + 1
                            };
                        }
                    }
                }

                // Strategy 4: English word boundaries (fallback)
                const englishWords = text.match(/[a-zA-Z]+/g) || [];
                let searchPos = 0;

                for (const word of englishWords) {
                    const wordStart = text.indexOf(word, searchPos);
                    const wordEnd = wordStart + word.length;

                    if (position >= wordStart && position <= wordEnd) {
                        console.log(`[DEBUG] Found English word: "${word}"`);
                        return {
                            word: word,
                            start: wordStart,
                            end: wordEnd
                        };
                    }
                    searchPos = wordEnd;
                }

                console.log(`[DEBUG] No word found at position ${position}`);
                return null;
            },

            /**
             * Extract words with their Strong's numbers from left verse
             */
            extractWordsWithStrongs(leftVerse) {
                const words = [];
                const strongsElements = leftVerse.querySelectorAll('.strongs-number');

                console.log(`[DEBUG] Found ${strongsElements.length} Strong's elements in left verse`);

                strongsElements.forEach((strongEl, index) => {
                    const strong = strongEl.getAttribute('data-strong');
                    console.log(`[DEBUG] Processing Strong's #${index + 1}: ${strong}`);

                    // Get the full text content of the verse to find context
                    const verseText = leftVerse.textContent;
                    console.log(`[DEBUG] Full verse text: "${verseText}"`);

                    // Find the position of this Strong's number in the overall text
                    const strongPosition = this.getElementTextPosition(leftVerse, strongEl);
                    console.log(`[DEBUG] ${strong} appears at text position: ${strongPosition}`);

                    // Look for Chinese characters near this position
                    if (strongPosition >= 0) {
                        // Check characters immediately before the Strong's position (most accurate)
                        const beforeText = verseText.substring(Math.max(0, strongPosition - 3), strongPosition);
                        const beforeChars = beforeText.match(/[\u4e00-\u9fff]/g) || [];
                        console.log(`[DEBUG] Characters before ${strong}: ${beforeChars.join('')}`);

                        // For multi-SN patterns like "創造<H01254><H0853>",
                        // H0853 may not have chars immediately before it but should associate with "創"
                        if (beforeChars.length > 0) {
                            const lastChar = beforeChars[beforeChars.length - 1];
                            words.push({ word: lastChar, strong, position: 'before', distance: 'immediate' });
                            console.log(`[DEBUG] Added Chinese char (before): "${lastChar}" → ${strong}`);
                        } else {
                            // Check if this is a consecutive Strong's number (like H0853 after H01254)
                            // Look further back for Chinese characters
                            const extendedBeforeText = verseText.substring(Math.max(0, strongPosition - 15), strongPosition);
                            const extendedChars = extendedBeforeText.match(/[\u4e00-\u9fff]/g) || [];
                            console.log(`[DEBUG] Extended characters before ${strong}: ${extendedChars.join('')}`);

                            if (extendedChars.length > 0) {
                                // Take the last 2 characters to handle multi-char words like "創造"
                                const lastTwoChars = extendedChars.slice(-2);
                                if (lastTwoChars.length >= 2) {
                                    // Associate with the first character of the pair (e.g., "創" in "創造")
                                    const firstChar = lastTwoChars[0];
                                    words.push({ word: firstChar, strong, position: 'extended', distance: 'near' });
                                    console.log(`[DEBUG] Added Chinese char (extended): "${firstChar}" → ${strong}`);
                                } else if (lastTwoChars.length === 1) {
                                    const singleChar = lastTwoChars[0];
                                    words.push({ word: singleChar, strong, position: 'extended', distance: 'near' });
                                    console.log(`[DEBUG] Added Chinese char (extended single): "${singleChar}" → ${strong}`);
                                }
                            }
                        }

                        // Check characters immediately after the Strong's position (less reliable)
                        const afterText = verseText.substring(strongPosition + 10, strongPosition + 13);
                        const afterChars = afterText.match(/[\u4e00-\u9fff]/g) || [];
                        console.log(`[DEBUG] Characters after ${strong}: ${afterChars.join('')}`);

                        // Take only the FIRST character after (and only if no character was found before)
                        if (afterChars.length > 0 && beforeChars.length === 0) {
                            const firstChar = afterChars[0];
                            words.push({ word: firstChar, strong, position: 'after', distance: 'immediate' });
                            console.log(`[DEBUG] Added Chinese char (after): "${firstChar}" → ${strong}`);
                        }
                    }
                });

                // Group by word but allow multiple Strong's numbers per word
                const wordStrongsMap = new Map();

                words.forEach(item => {
                    const wordKey = item.word;

                    if (!wordStrongsMap.has(wordKey)) {
                        wordStrongsMap.set(wordKey, []);
                    }

                    const existing = wordStrongsMap.get(wordKey);

                    // Check if this Strong's number is already added for this word
                    const alreadyExists = existing.some(existingItem => existingItem.strong === item.strong);

                    if (!alreadyExists) {
                        existing.push(item);
                        console.log(`[DEBUG] Added association "${wordKey}": ${item.strong} (${item.position})`);
                    } else {
                        console.log(`[DEBUG] Skipping duplicate "${wordKey}": ${item.strong} (${item.position})`);
                    }
                });

                // Convert to flat array, but preserve multiple Strong's per word information
                const uniqueWords = [];
                wordStrongsMap.forEach((strongsArray, word) => {
                    // Sort by position preference (before > after) then add all
                    const sorted = strongsArray.sort((a, b) => {
                        if (a.position === 'before' && b.position === 'after') return -1;
                        if (a.position === 'after' && b.position === 'before') return 1;
                        return 0;
                    });
                    uniqueWords.push(...sorted);
                });

                // NEW: Handle multi-character words by detecting consecutive characters with Strong's numbers
                const multiCharWords = this.detectMultiCharWords(words, leftVerse);
                multiCharWords.forEach(multiWord => {
                    uniqueWords.push(multiWord);
                    console.log(`[DEBUG] Added multi-char word: "${multiWord.word}" with ${Array.isArray(multiWord.strong) ? multiWord.strong.length : 1} Strong's numbers`);
                });

                console.log(`[DEBUG] Extracted ${uniqueWords.length} unique word-Strong's pairs:`, uniqueWords);
                return uniqueWords;
            },

            /**
             * Find Strong's numbers for a word using direct text matching
             * Used for pre-highlighted words where we have the exact text
             */
            findStrongsByDirectMatch(leftVerse, targetWord) {
                const words = this.extractWordsWithStrongs(leftVerse);
                const matches = [];

                // Look for exact matches
                for (const wordItem of words) {
                    if (wordItem.word === targetWord) {
                        if (Array.isArray(wordItem.strong)) {
                            matches.push(...wordItem.strong);
                        } else {
                            matches.push(wordItem.strong);
                        }
                    }
                }

                // Remove duplicates
                const uniqueMatches = [...new Set(matches)];
                console.log(`[DEBUG] Direct match for "${targetWord}": ${uniqueMatches.join(', ')}`);
                return uniqueMatches;
            },

            /**
             * Detect multi-character words that have multiple Strong's numbers
             */
            detectMultiCharWords(words, leftVerse) {
                const multiCharWords = [];
                const verseText = leftVerse.textContent;

                // Group words by their characters to find potential multi-char combinations
                const charStrongMap = new Map();
                words.forEach(wordItem => {
                    const char = wordItem.word;
                    if (!charStrongMap.has(char)) {
                        charStrongMap.set(char, []);
                    }
                    charStrongMap.get(char).push(wordItem.strong);
                });

                console.log(`[DEBUG] Character-Strong's mapping:`, Array.from(charStrongMap.entries()));

                // Look for consecutive character pairs in the verse text
                for (let i = 0; i < verseText.length - 1; i++) {
                    const char1 = verseText[i];
                    const char2 = verseText[i + 1];

                    // Check if both characters are Chinese and have Strong's numbers
                    if (char1.match(/[\u4e00-\u9fff]/) && char2.match(/[\u4e00-\u9fff]/)) {
                        const strongs1 = charStrongMap.get(char1) || [];
                        const strongs2 = charStrongMap.get(char2) || [];

                        if (strongs1.length > 0 && strongs2.length > 0) {
                            const combinedWord = char1 + char2;
                            const allStrongs = [...strongs1, ...strongs2];

                            // Remove duplicates
                            const uniqueStrongs = [...new Set(allStrongs)];

                            multiCharWords.push({
                                word: combinedWord,
                                strong: uniqueStrongs,
                                position: 'combined',
                                distance: 'immediate'
                            });

                            console.log(`[DEBUG] Detected multi-char word: "${combinedWord}" with Strong's: ${uniqueStrongs.join(', ')}`);
                        }
                    }
                }

                return multiCharWords;
            },

            /**
             * Get the text position of an element within its parent
             */
            getElementTextPosition(parent, element) {
                const walker = document.createTreeWalker(
                    parent,
                    NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
                    null,
                    false
                );

                let position = 0;
                let node;

                while (node = walker.nextNode()) {
                    if (node === element) {
                        return position;
                    }
                    if (node.nodeType === Node.TEXT_NODE) {
                        position += node.textContent.length;
                    }
                }
                return -1;
            },

            /**
             * Simple translation lookup
             */
            getTranslation(word) {
                const translations = {
                    // Genesis 1 key words
                    '光': 'light',
                    'light': '光',
                    '說': 'said',
                    'said': '說',
                    '地': 'earth',
                    'earth': '地',
                    '神': 'God',
                    'God': '神',
                    '起初': 'beginning',
                    'beginning': '起初',
                    '創造': 'created',
                    'created': '創造',
                    '天': 'heaven',
                    'heaven': '天',
                    '水': 'water',
                    'water': '水',
                    '好': 'good',
                    'good': '好',
                    '分開': 'divided',
                    'divided': '分開',
                    '要': 'let',
                    'let': '要',
                    '有': 'there',
                    'there': '有'
                };

                console.log(`[DEBUG] Looking up translation for: "${word}" → ${translations[word] || 'not found'}`);
                return translations[word] || null;
            },

            /**
             * Get relative position of word in verse (0-1 scale)
             */
            getWordPositionInVerse(verse, wordInfo) {
                const text = verse.textContent;
                return wordInfo.start / text.length;
            },

            /**
             * Find word at similar relative position
             */
            getWordAtSimilarPosition(leftWords, targetPosition) {
                // Simple implementation: return word with closest position
                // This could be enhanced with better algorithms
                return leftWords.length > 0 ? leftWords[Math.floor(targetPosition * leftWords.length)] : null;
            }

            // Future algorithms can be added here:
            // aiEnhanced(context) { ... }
            // semanticMatching(context) { ... }
            // externalApiLookup(context) { ... }
        },

        /**
         * Helper: Get element position in text
         */
        getElementPosition(parent, element) {
            let position = 0;
            const walker = document.createTreeWalker(parent, NodeFilter.SHOW_ALL);

            let node;
            while (node = walker.nextNode()) {
                if (node === element) return position;
                if (node.nodeType === Node.TEXT_NODE) {
                    position += node.textContent.length;
                }
            }
            return position;
        }
    };

    /**
     * Suggests Strong's number using the abstract suggestion engine
     */
    function suggestStrongsFromLeftReader() {
        try {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return;

            const range = selection.getRangeAt(0);
            const verseId = currentEditingVerse.getAttribute('data-verse');
            const cursorPosition = getTextOffset(currentEditingVerse, range.startContainer, range.startOffset);

            // Find left verse
            const leftContentArea = document.getElementById('left-reader-content-area');
            const leftVerse = leftContentArea?.querySelector(`[data-verse="${verseId}"]`);

            if (!leftVerse) {
                logStatus(`🔍 No reference verse ${verseId} found`);
                return;
            }

            // Create context for suggestion engine
            const context = {
                rightVerse: currentEditingVerse,
                leftVerse: leftVerse,
                cursorPosition: cursorPosition,
                verseId: verseId,
                rightText: currentEditingVerse.textContent,
                leftText: leftVerse.textContent
            };

            // Get suggestion from black box engine
            const suggestion = SuggestionEngine.getSuggestion(context);

            if (suggestion) {
                // Handle both single and multiple Strong's numbers
                const inputValue = Array.isArray(suggestion) ? suggestion.join(' ') : suggestion;
                const clipboardValue = Array.isArray(suggestion) ?
                    suggestion.map(sn => `<${sn}>`).join('') :
                    `<${suggestion}>`;

                strongNumberInput.value = inputValue;
                navigator.clipboard.writeText(clipboardValue).then(() => {
                    const displayValue = Array.isArray(suggestion) ? suggestion.join(', ') : suggestion;
                    logStatus(`💡 Suggested: ${displayValue} (copied to clipboard)`);
                }).catch(() => {
                    logStatus(`💡 Suggested: ${suggestion}`);
                });

                // Highlight matching Strong's number(s) in left reader for visual confirmation
                if (Array.isArray(suggestion)) {
                    // Highlight multiple Strong's numbers - clear first, then add all without clearing between
                    suggestion.forEach((sn, index) => {
                        highlightStrongsInLeftReader(sn, verseId, index === 0); // Clear only on first one
                    });
                } else {
                    // Highlight single Strong's number
                    highlightStrongsInLeftReader(suggestion, verseId, true);
                }

                // Set/reset the highlighting timeout (single timer for all highlights)
                if (highlightTimer) {
                    clearTimeout(highlightTimer);
                }
                highlightTimer = setTimeout(() => {
                    clearStrongsHighlighting();
                    highlightTimer = null;
                    console.log('[DEBUG] Auto-cleared highlighting after 10 seconds');
                }, 10000); // 10 seconds
            } else {
                strongNumberInput.value = '';
                // Clear highlighting when no suggestion
                clearStrongsHighlighting();
            }

        } catch (error) {
            logStatus(`❌ Suggestion failed: ${error.message}`);
        }
    }


    /**
     * Handles scroll events to detect current verse and sync with left reader
     */
    let scrollTimeout;
    function handleRightScroll() {
        // Only sync position if this reader is main (both follow checkboxes unchecked)
        if (followScrollToggle.checked || followSelectionToggle.checked) return;
        
        // Debounce scroll events
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            const currentVerse = getRightTopmostVerseReference();
            if (currentVerse) {
                syncRightPositionWithMediator(currentVerse.book, currentVerse.chapter, currentVerse.verse);
            }
        }, 100);
    }

    /**
     * Gets the topmost visible verse in the right reader
     * @returns {object|null} Object with book, chapter, verse properties
     */
    function getRightTopmostVerseReference() {
        const verses = contentArea.querySelectorAll('.verse[data-verse]');
        const containerRect = contentArea.getBoundingClientRect();
        const containerTop = containerRect.top;

        for (const verse of verses) {
            const verseRect = verse.getBoundingClientRect();
            if (verseRect.top >= containerTop && verseRect.top <= containerTop + 100) {
                return {
                    book: currentBookChinese, // Use Chinese abbreviation for API consistency
                    chapter: currentChapter,
                    verse: parseInt(verse.getAttribute('data-verse'))
                };
            }
        }
        
        // If no verse is in the top area, return the first visible verse
        if (verses.length > 0) {
            const firstVerse = verses[0];
            return {
                book: currentBookChinese,
                chapter: currentChapter,
                verse: parseInt(firstVerse.getAttribute('data-verse'))
            };
        }
        
        return null;
    }

    /**
     * Syncs the current position with the mediator for left reader
     * @param {string} book - Chinese book abbreviation
     * @param {number} chapter - Chapter number
     * @param {number} verse - Verse number
     */
    function syncRightPositionWithMediator(book, chapter, verse) {
        MockMediator.syncPosition({
            book: book,
            chapter: chapter,
            verse: verse,
            rightReaderVersion: versionSelect.value
        });
    }

    // Initialize right reader defaults
    function initializeRightReaderDefaults() {
        console.log('RightReader: Initializing defaults...');

        // 0. Sync JavaScript state with HTML checkbox states
        isEditMode = editModeToggle.checked;
        console.log(`RightReader: Synced isEditMode = ${isEditMode} from HTML checkbox`);

        // 1. Set version to LCC (呂振中譯本)
        versionSelect.value = 'lcc';
        logStatus('📍 Version: LCC (default)');

        // 1.5. Restore last book/chapter from localStorage or default to Genesis 1
        const savedBook = localStorage.getItem('rightReader_lastBook') || '創'; // Genesis
        const savedChapter = localStorage.getItem('rightReader_lastChapter') || '1';

        // Set the saved book and chapter
        if (bookSelect && bookSelect.querySelector(`option[value="${savedBook}"]`)) {
            bookSelect.value = savedBook;
            console.log(`RightReader: Restored book to ${savedBook}`);
        } else {
            bookSelect.value = '創'; // Default to Genesis if saved book not found
            console.log('RightReader: Using default book (Genesis)');
        }

        if (chapterInput) {
            chapterInput.value = savedChapter;
            console.log(`RightReader: Restored chapter to ${savedChapter}`);
        }

        // 2. Load saved content first before enabling edit mode
        console.log('RightReader: Loading saved content before edit mode...');
        loadChapterContent().then(() => {
            console.log('RightReader: Saved content loaded, now enabling edit mode...');

            // 3. Enable edit mode by default (this will override follow settings)
            isUpdatingCheckboxes = true;

            // Since edit mode checkbox is already checked in HTML, trigger the edit mode logic
            if (editModeToggle.checked) {
                // Trigger edit mode initialization manually with extra delay to ensure left reader is ready
                setTimeout(() => {
                    console.log('RightReader: Triggering edit mode with left reader elements check...');

                    // Verify left reader elements are available
                    const leftScroll = document.getElementById('left-reader-follow-scroll');
                    const leftSelection = document.getElementById('left-reader-follow-selection');
                    console.log('Left reader follow elements:', { leftScroll, leftSelection });

                    handleEditModeToggle();
                }, 300);
                logStatus('📝 Edit Mode: ENABLED (default)');
            } else {
                // This case should rarely happen since edit mode is default, but if disabled:
                // Right reader should still be main, just without editing capabilities
                logStatus('📍 Edit mode disabled - right reader still main but read-only');
                MockMediator.setMainReader('right', 'right reader default (non-edit mode)');
            }

            setTimeout(() => { isUpdatingCheckboxes = false; }, 200);

            console.log('RightReader: Defaults initialized with edit mode preference...');
        }).catch(error => {
            console.error('RightReader: Error loading saved content:', error);
            logStatus('❌ Failed to load saved content, proceeding with edit mode...');

            // Continue with edit mode even if content loading fails
            isUpdatingCheckboxes = true;
            if (editModeToggle.checked) {
                setTimeout(() => handleEditModeToggle(), 300);
                logStatus('📝 Edit Mode: ENABLED (default)');
            }
            setTimeout(() => { isUpdatingCheckboxes = false; }, 200);
        });
    }

    // Update initial placeholder text based on selected language
    const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
    const langTranslations = translations[selectedLanguage] || translations.en;
    if (contentArea.firstElementChild && contentArea.firstElementChild.textContent.trim() === "Waiting for left reader...") {
        contentArea.firstElementChild.textContent = langTranslations.rightReaderWaiting;
    }

    // Initialize defaults after a short delay to ensure all elements are ready
    setTimeout(initializeRightReaderDefaults, 100);

    // Global test function for debugging (accessible from browser console)
    window.testStrongsHighlighting = function(strongsNumber) {
        console.log(`[TEST] Testing highlighting for: ${strongsNumber}`);
        highlightStrongsInLeftReader(strongsNumber || 'H0430', '1');
    };

    window.clearStrongsHighlighting = clearStrongsHighlighting;
});
