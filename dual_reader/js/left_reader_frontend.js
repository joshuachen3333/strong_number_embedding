/**
 * Left Reader Frontend Logic
 * Handles the functionality of the left Bible reader component.
 */
document.addEventListener('DOMContentLoaded', () => {
    const bookSelect = document.getElementById('left-reader-book');
    const chapterInput = document.getElementById('left-reader-chapter');
    const loadButton = document.getElementById('left-reader-load');
    const contentArea = document.getElementById('left-reader-content-area');
    const versionSelect = document.getElementById('left-reader-version-select'); // Changed from versionInput
    const strongToggle = document.getElementById('left-reader-strong-toggle'); // Strong's checkbox
    const mainToggle = document.getElementById('left-reader-main-toggle'); // Main checkbox
    const statusDisplay = document.getElementById('left-reader-status-display'); // For displaying status updates

    let isUpdatingCheckboxes = false; // Flag to prevent infinite loops

    // Book mapping with Chinese abbreviations for bible.fhl.net API
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

    if (bookSelect && books && books.length > 0) {
        console.log('Populating book select dropdown...');
        console.log(`Found bookSelect element: ${bookSelect.id}`);
        console.log(`Total books to populate: ${books.length}`);

        // Clear existing options first - intentionally NOT doing this for now, as per subtask instruction.
        // bookSelect.innerHTML = '';

        books.forEach(book => {
            const option = document.createElement('option');
            option.value = book.chinese; // Use Chinese abbreviation as value for API
            option.textContent = book.english; // Display English name for user
            option.dataset.chinese = book.chinese; // Store Chinese abbreviation
            bookSelect.appendChild(option);
            console.log(`Adding book: ${book.english} (${book.chinese})`);
        });
        console.log(`Finished populating books. Total options: ${bookSelect.options.length}`);
    } else {
        console.error('Could not populate book select: bookSelect element not found or books array is empty.');
        if (!bookSelect) console.error('bookSelect is null or undefined.');
        if (!books || books.length === 0) console.error('books array is null, undefined, or empty.');
    }

    // Event listener for the load button
    loadButton.addEventListener('click', loadChapterContent);

    // Add event listeners for automatic content loading on change
    bookSelect.addEventListener('change', () => {
        // Only set as main if this reader is already main (respect checkbox state)
        if (mainToggle.checked) {
            MockMediator.setMainReader('left', 'book selection');
        }
        const selectedBook = bookSelect.options[bookSelect.selectedIndex].text;
        logStatus(`Book selected: ${selectedBook}`);
        loadChapterContent();
    });
    chapterInput.addEventListener('change', () => {
        // Only set as main if this reader is already main (respect checkbox state)
        if (mainToggle.checked) {
            MockMediator.setMainReader('left', 'chapter selection');
        }
        logStatus(`Chapter selected: ${chapterInput.value}`);
        loadChapterContent();
    });
    versionSelect.addEventListener('change', () => {
        // Only set as main if this reader is already main (respect checkbox state)
        if (mainToggle.checked) {
            MockMediator.setMainReader('left', 'version selection');
        }
        const selectedVersion = versionSelect.options[versionSelect.selectedIndex].text;
        logStatus(`Version selected: ${selectedVersion}`);
        console.log('LeftReader: Version changed, clearing cache');
        MockMediator.clearCache();
        loadChapterContent();
    });
    strongToggle.addEventListener('change', () => {
        // Only set as main if this reader is already main (respect checkbox state)
        if (mainToggle.checked) {
            MockMediator.setMainReader('left', 'Strong\'s toggle');
        }
        logStatus(`Strong's Numbers: ${strongToggle.checked ? 'ON' : 'OFF'}`);
        loadChapterContent();
    });
    mainToggle.addEventListener('change', handleLeftMainToggle);

    // Add scroll event listener for synchronization
    contentArea.addEventListener('scroll', handleScroll);

    // Register with mediator for synchronization updates (when right reader is main)
    MockMediator.registerLeftReaderUpdateCallback(loadLeftPassage);

    /**
     * Load passage callback for mediator synchronization (when right reader is main)
     * @param {string} book - Chinese book abbreviation
     * @param {number} chapter - Chapter number
     * @param {number} verse - Verse number for scrolling
     */
    function loadLeftPassage(book, chapter, verse) {
        console.log(`LeftReader: Loading passage ${book} ${chapter}:${verse} (following right reader)`);
        
        // Find corresponding English book name for display
        const bookEntry = books.find(b => b.chinese === book);
        const currentBook = bookEntry ? bookEntry.english : book;
        
        // Check if we need to load new chapter content or just scroll to verse
        const currentDisplayedBook = bookSelect.options[bookSelect.selectedIndex]?.text;
        const currentDisplayedChapter = parseInt(chapterInput.value);
        
        if (currentDisplayedBook !== currentBook || currentDisplayedChapter !== chapter) {
            // Need to load different chapter
            logStatus(`📨 Following right reader: ${currentBook} ${chapter}`);
            
            // Update our controls to match
            const bookOption = Array.from(bookSelect.options).find(opt => opt.textContent === currentBook);
            if (bookOption) {
                bookSelect.value = bookOption.value;
            }
            chapterInput.value = chapter;
            
            // Load the content with our current settings
            loadChapterContent().then(() => {
                // After loading, scroll to the specific verse
                setTimeout(() => scrollLeftToVerse(verse), 100);
            });
        } else {
            // Same chapter, just scroll to the verse
            scrollLeftToVerse(verse);
        }
    }

    /**
     * Scrolls to a specific verse in the left reader
     * @param {number} verse - Verse number to scroll to
     */
    function scrollLeftToVerse(verse) {
        const verseElement = contentArea.querySelector(`[data-verse="${verse}"]`);
        if (verseElement) {
            verseElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            // Add highlighting to show which verse is being followed
            contentArea.querySelectorAll('.verse-highlighted').forEach(el => el.classList.remove('verse-highlighted'));
            verseElement.classList.add('verse-highlighted');
            logStatus(`📍 Scrolled to verse ${verse}`);
        }
    }

    /**
     * Handles left reader main toggle changes
     */
    function handleLeftMainToggle() {
        if (isUpdatingCheckboxes) return; // Prevent infinite loops
        
        isUpdatingCheckboxes = true;
        const rightMainToggle = document.getElementById('right-reader-main-toggle');
        
        if (mainToggle.checked) {
            MockMediator.setMainReader('left', 'main checkbox checked');
            logStatus('📍 Set as MAIN reader (checkbox)');
            if (rightMainToggle) {
                rightMainToggle.checked = false;
            }
            
            // If left reader has content, immediately publish chapter change event
            const currentDisplayedBook = bookSelect.options[bookSelect.selectedIndex]?.text;
            const currentDisplayedChapter = parseInt(chapterInput.value);
            const currentBookChinese = bookSelect.value;
            
            if (currentDisplayedBook && currentDisplayedChapter && currentBookChinese) {
                console.log('LeftReader: Publishing chapter change event immediately');
                MockMediator.publish('leftReaderChapterChanged', {
                    book: currentDisplayedBook,
                    chapter: currentDisplayedChapter,
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
            MockMediator.setMainReader('right', 'left main unchecked'); 
            logStatus('📍 Set as FOLLOWER reader (checkbox)');
            if (rightMainToggle) {
                rightMainToggle.checked = true;
            }
        }
        
        setTimeout(() => { isUpdatingCheckboxes = false; }, 100);
    }

    /**
     * Logs status updates to the main reader status display
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
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">[${strongsId}]</span>`;
        });
        
        // Format 2: {H1234} or {G5678}
        result = result.replace(/\{([HG])(\d+)\}/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">[${strongsId}]</span>`;
        });
        
        // Format 3: <WH1234> or <WG5678>
        result = result.replace(/<W([HG])(\d+)>/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">[${strongsId}]</span>`;
        });
        
        // Format 4: (H1234) or (G5678)
        result = result.replace(/\(([HG])(\d+)\)/g, (match, lang, number) => {
            const strongsId = `${lang}${number}`;
            return `<span class="strongs-number" data-strong="${strongsId}" title="Strong's ${strongsId}">[${strongsId}]</span>`;
        });
        
        return result;
    }

    /**
     * Loads the chapter content based on selected book, chapter, version, and Strong's numbers preference.
     */
    async function loadChapterContent() {
        console.log('LeftReader: loadChapterContent called');
        const book = bookSelect.value;
        const chapter = chapterInput.value;
        const version = versionSelect.value; // Read from the select dropdown
        const strong = strongToggle.checked ? "1" : "0"; // Use checkbox state
        
        console.log('LeftReader: Values:', { book, chapter, version, strong });

        // Log the API URL being used
        const selectedChineseBook = bookSelect.value; // Now contains the Chinese abbreviation
        const fhlUrl = `https://bible.fhl.net/json/qb.php?version=${version}&chineses=${encodeURIComponent(selectedChineseBook)}&chap=${chapter}&strong=${strong}`;
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
            console.log(`LeftReader: Fetching from mediator for ${book} ${chapter} (${version})`);

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

            console.log(`LeftReader: Loaded ${data.verses.length} verses from FHL API`);
            logStatus(`✅ Loaded ${data.verses.length} verses successfully`);


            renderChapter(data);
            
            // Publish an event that the left reader's content has changed (only if this is the main reader)
            if (MockMediator.getMainReader() === 'left') {
                console.log('LeftReader: Publishing leftReaderChapterChanged event');
                MockMediator.publish('leftReaderChapterChanged', {
                    book: data.book,
                    chapter: parseInt(chapter),
                    version: data.version,
                    internalVersionValue: book, // Pass the Chinese book abbreviation for API calls
                    strong: data.strong,
                    verses: data.verses
                });
            }

            // Also sync position with mediator for right reader
            MockMediator.syncPosition({
                book: book, // Chinese abbreviation
                chapter: parseInt(chapter),
                verse: 1, // Default to first verse
                leftReaderVersion: version
            });

            // Initial sync after loading
            setTimeout(() => {
                const firstVerse = getTopmostVerseReference();
                if (firstVerse) {
                    syncPositionWithMediator(firstVerse.book, firstVerse.chapter, firstVerse.verse);
                }
            }, 100);

        } catch (error) {
            console.error('LeftReader: Error loading chapter content:', error);
            logStatus(`❌ Error: ${error.message}`);
            contentArea.innerHTML = `<p>Error loading content: ${error.message}. Please ensure the backend is running and the API is correct.</p>`;
        }
    }

    /**
     * Renders the chapter content in the content area.
     * @param {object} data - The chapter data from the API.
     */
    function renderChapter(data) {
        // data.version already contains the display text from mockData
        let htmlContent = `<h3>${data.book} ${data.chapter} (${data.version})</h3>`;
        data.verses.forEach(verse => {
            htmlContent += `<p class="verse" data-verse="${verse.verse}" data-book="${bookSelect.value}" data-chapter="${data.chapter}">`;
            htmlContent += `<span class="verse-number">${verse.verse}</span> `;

            // Parse Strong's numbers from the text (embedded as {<WH1234>} or {<WG5678>})
            let verseText = verse.text;
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

        // Add event listeners for Strong's numbers if they are displayed
        if (data.strong) {
            attachStrongsEventListeners();
        }
    }

    /**
     * Handles scroll events to detect current verse and sync with right reader
     */
    let scrollTimeout;
    function handleScroll() {
        // Only sync position if this reader is main (respect checkbox state)
        if (!mainToggle.checked) return;
        
        // Debounce scroll events
        clearTimeout(scrollTimeout);
        scrollTimeout = setTimeout(() => {
            const currentVerse = getTopmostVerseReference();
            if (currentVerse) {
                syncPositionWithMediator(currentVerse.book, currentVerse.chapter, currentVerse.verse);
            }
        }, 100);
    }

    /**
     * Gets the topmost visible verse in the main reader
     * @returns {object|null} Object with book, chapter, verse properties
     */
    function getTopmostVerseReference() {
        const verses = contentArea.querySelectorAll('.verse[data-verse]');
        const containerRect = contentArea.getBoundingClientRect();
        const containerTop = containerRect.top;

        for (const verse of verses) {
            const verseRect = verse.getBoundingClientRect();
            if (verseRect.top >= containerTop && verseRect.top <= containerTop + 100) {
                return {
                    book: verse.getAttribute('data-book'),
                    chapter: parseInt(verse.getAttribute('data-chapter')),
                    verse: parseInt(verse.getAttribute('data-verse'))
                };
            }
        }
        
        // If no verse is in the top area, return the first visible verse
        if (verses.length > 0) {
            const firstVerse = verses[0];
            return {
                book: firstVerse.getAttribute('data-book'),
                chapter: parseInt(firstVerse.getAttribute('data-chapter')),
                verse: parseInt(firstVerse.getAttribute('data-verse'))
            };
        }
        
        return null;
    }

    /**
     * Syncs the current position with the mediator for second reader
     * @param {string} book - Chinese book abbreviation
     * @param {number} chapter - Chapter number
     * @param {number} verse - Verse number
     */
    function syncPositionWithMediator(book, chapter, verse) {
        MockMediator.syncPosition({
            book: book,
            chapter: chapter,
            verse: verse,
            mainReaderVersion: versionSelect.value
        });
    }

    /**
     * Attaches event listeners to Strong's number elements.
     */
    function attachStrongsEventListeners() {
        const strongsElements = contentArea.querySelectorAll('.strongs-number');
        strongsElements.forEach(el => {
            el.addEventListener('click', () => {
                const strongNum = el.dataset.strong;
                logStatus(`🔗 Strong's clicked: ${strongNum}`);
                console.log(`LeftReader: Strong's number ${strongNum} clicked.`);
                // Publish an event when a Strong's number is clicked
                MockMediator.publish('strongsNumberClicked', {
                    strongNumber: strongNum,
                    version: versionSelect.value // use current selection from dropdown
                });
                // Further action: display definition (could be another component subscribing to this)
                alert(`Strong's number clicked: ${strongNum}. Definition lookup not yet implemented.`);
            });
        });
    }

    // Initial load - load Genesis 1 by default
    setTimeout(() => {
        console.log('LeftReader: Attempting initial load...');
        if (bookSelect && bookSelect.options.length > 0) {
            console.log('LeftReader: Setting initial values...');
            bookSelect.selectedIndex = 0; // Select first book (Genesis)
            chapterInput.value = 1;
            console.log('LeftReader: Calling loadChapterContent...');
            loadChapterContent();
        } else {
            console.error('LeftReader: bookSelect not found or no options');
        }
    }, 500);

    // Update initial placeholder text based on selected language
    const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
    const langTranslations = translations[selectedLanguage] || translations.en;
    if (contentArea.firstElementChild && contentArea.firstElementChild.textContent.trim() === "Loading content...") {
         contentArea.firstElementChild.textContent = langTranslations.leftReaderLoadingContent;
    }


    /**
     * Subscribe to main reader role changes
     */
    MockMediator.subscribe('mainReaderChanged', (data) => {
        if (data.newMain === 'left') {
            logStatus(`🎯 Now MAIN reader (${data.interaction})`);
            // Update checkbox to reflect main status only if not from checkbox interaction
            if (!data.interaction.includes('checkbox') && !mainToggle.checked) {
                isUpdatingCheckboxes = true;
                mainToggle.checked = true;
                setTimeout(() => { isUpdatingCheckboxes = false; }, 100);
            }
        } else {
            logStatus(`👥 Now FOLLOWER reader (${data.interaction})`);
            // Update checkbox to reflect follower status only if not from checkbox interaction
            if (!data.interaction.includes('checkbox') && mainToggle.checked) {
                isUpdatingCheckboxes = true;
                mainToggle.checked = false;
                setTimeout(() => { isUpdatingCheckboxes = false; }, 100);
            }
        }
    });

    /**
     * Subscribe to chapter change events from the right reader (when it's main)
     */
    MockMediator.subscribe('rightReaderChapterChanged', async (data) => {
        console.log('LeftReader: Received chapter change from RightReader:', data);
        if (MockMediator.getMainReader() === 'right') {
            logStatus(`📨 Following right reader: ${data.book} ${data.chapter}`);
            // Update our controls to match
            const bookOption = Array.from(bookSelect.options).find(opt => opt.textContent === data.book);
            if (bookOption) {
                bookSelect.value = bookOption.value;
            }
            chapterInput.value = data.chapter;
            // Don't change version or Strong's - those remain independent
            // Load the content with our current settings
            loadChapterContent();
        }
    });
});
