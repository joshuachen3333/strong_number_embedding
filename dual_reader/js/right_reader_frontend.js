/**
 * Right Reader Frontend Logic
 * Handles the functionality of the right Bible reader component,
 * which can be either main or follower depending on last interaction.
 */
document.addEventListener('DOMContentLoaded', () => {
    const bookSelect = document.getElementById('right-reader-book');
    const chapterInput = document.getElementById('right-reader-chapter');
    const loadButton = document.getElementById('right-reader-load');
    const versionSelect = document.getElementById('right-reader-version-select');
    const strongToggle = document.getElementById('right-reader-strong-toggle');
    const contentArea = document.getElementById('right-reader-content-area');
    const statusDisplay = document.getElementById('right-reader-status-display');

    let currentBook = null;
    let currentChapter = null;
    let currentBookChinese = null; // Store Chinese book abbreviation for API calls
    let currentVerses = null; // Store verses from main reader

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
    loadButton.addEventListener('click', loadChapterContent);
    
    bookSelect.addEventListener('change', () => {
        MockMediator.setMainReader('right', 'book selection');
        const selectedBook = bookSelect.options[bookSelect.selectedIndex].text;
        logStatus(`Book selected: ${selectedBook}`);
        loadChapterContent();
    });
    chapterInput.addEventListener('change', () => {
        MockMediator.setMainReader('right', 'chapter selection');
        logStatus(`Chapter selected: ${chapterInput.value}`);
        loadChapterContent();
    });
    versionSelect.addEventListener('change', () => {
        MockMediator.setMainReader('right', 'version selection');
        const selectedVersion = versionSelect.options[versionSelect.selectedIndex].text;
        logStatus(`Version selected: ${selectedVersion}`);
        console.log('RightReader: Version changed to', versionSelect.value);
        console.log('RightReader: Clearing cache for version change');
        MockMediator.clearCache();
        loadChapterContent();
    });
    strongToggle.addEventListener('change', () => {
        MockMediator.setMainReader('right', 'Strong\'s toggle');
        logStatus(`Strong's Numbers: ${strongToggle.checked ? 'ON' : 'OFF'}`);
        console.log('RightReader: Strong toggle changed to', strongToggle.checked);
        loadChapterContent();
    });

    // Register with mediator for synchronization updates
    MockMediator.registerRightReaderUpdateCallback(loadPassage);

    /**
     * Subscribes to chapter change events from the left reader (when it's main).
     */
    MockMediator.subscribe('leftReaderChapterChanged', async (data) => {
        console.log('RightReader: Received chapter change from LeftReader:', data);
        if (MockMediator.getMainReader() === 'left') {
            logStatus(`📨 Following left reader: ${data.book} ${data.chapter}`);
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
        console.log(`SecondReader: Loading passage ${book} ${chapter}:${verse}`);
        currentBookChinese = book;
        currentChapter = chapter;
        // Find corresponding English book name for display
        const bookMapping = [
            { english: "Genesis", chinese: "創" }, { english: "Exodus", chinese: "出" }, { english: "Leviticus", chinese: "利" },
            { english: "Numbers", chinese: "民" }, { english: "Deuteronomy", chinese: "申" }, { english: "Joshua", chinese: "書" },
            { english: "Judges", chinese: "士" }, { english: "Ruth", chinese: "得" }, { english: "1 Samuel", chinese: "撒上" },
            { english: "2 Samuel", chinese: "撒下" }, { english: "1 Kings", chinese: "王上" }, { english: "2 Kings", chinese: "王下" },
            { english: "1 Chronicles", chinese: "代上" }, { english: "2 Chronicles", chinese: "代下" }, { english: "Ezra", chinese: "拉" },
            { english: "Nehemiah", chinese: "尼" }, { english: "Esther", chinese: "斯" }, { english: "Job", chinese: "伯" },
            { english: "Psalms", chinese: "詩" }, { english: "Proverbs", chinese: "箴" }, { english: "Ecclesiastes", chinese: "傳" },
            { english: "Song of Songs", chinese: "歌" }, { english: "Isaiah", chinese: "賽" }, { english: "Jeremiah", chinese: "耶" },
            { english: "Lamentations", chinese: "哀" }, { english: "Ezekiel", chinese: "結" }, { english: "Daniel", chinese: "但" },
            { english: "Hosea", chinese: "何" }, { english: "Joel", chinese: "珥" }, { english: "Amos", chinese: "摩" },
            { english: "Obadiah", chinese: "俄" }, { english: "Jonah", chinese: "拿" }, { english: "Micah", chinese: "彌" },
            { english: "Nahum", chinese: "鴻" }, { english: "Habakkuk", chinese: "哈" }, { english: "Zephaniah", chinese: "番" },
            { english: "Haggai", chinese: "該" }, { english: "Zechariah", chinese: "亞" }, { english: "Malachi", chinese: "瑪" },
            { english: "Matthew", chinese: "太" }, { english: "Mark", chinese: "可" }, { english: "Luke", chinese: "路" },
            { english: "John", chinese: "約" }, { english: "Acts", chinese: "徒" }, { english: "Romans", chinese: "羅" },
            { english: "1 Corinthians", chinese: "林前" }, { english: "2 Corinthians", chinese: "林後" }, { english: "Galatians", chinese: "加" },
            { english: "Ephesians", chinese: "弗" }, { english: "Philippians", chinese: "腓" }, { english: "Colossians", chinese: "西" },
            { english: "1 Thessalonians", chinese: "帖前" }, { english: "2 Thessalonians", chinese: "帖後" }, { english: "1 Timothy", chinese: "提前" },
            { english: "2 Timothy", chinese: "提後" }, { english: "Titus", chinese: "多" }, { english: "Philemon", chinese: "門" },
            { english: "Hebrews", chinese: "來" }, { english: "James", chinese: "雅" }, { english: "1 Peter", chinese: "彼前" },
            { english: "2 Peter", chinese: "彼後" }, { english: "1 John", chinese: "約一" }, { english: "2 John", chinese: "約二" },
            { english: "3 John", chinese: "約三" }, { english: "Jude", chinese: "猶" }, { english: "Revelation", chinese: "啟" }
        ];
        
        const bookEntry = bookMapping.find(b => b.chinese === book);
        currentBook = bookEntry ? bookEntry.english : book;
        
        displaySyncedContent().then(() => {
            scrollToVerse(verse);
        });
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
        const book = bookSelect.value;
        const chapter = chapterInput.value;
        const version = versionSelect.value;
        const strong = strongToggle.checked ? "1" : "0";

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

        if (data.strong) {
            attachStrongsEventListenersSecondReader();
        }
    }

    /**
     * Attaches event listeners to Strong's number elements in the second reader.
     */
    function attachStrongsEventListenersSecondReader() {
        const strongsElements = contentArea.querySelectorAll('.strongs-number');
        strongsElements.forEach(el => {
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
            verseElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            // Add highlighting
            contentArea.querySelectorAll('.verse-highlighted').forEach(el => el.classList.remove('verse-highlighted'));
            verseElement.classList.add('verse-highlighted');
        }
    }

    // Add scroll event listener for synchronization
    contentArea.addEventListener('scroll', () => {
        MockMediator.setMainReader('right', 'scroll');
    });

    // Initial setup - set default values but don't auto-load (left reader is main initially)
    setTimeout(() => {
        if (bookSelect.options.length > 0) {
            bookSelect.selectedIndex = 0; // Select first book (Genesis)
            chapterInput.value = 1;
            // Don't auto-load, wait for left reader to lead or manual interaction
        }
    }, 500);

    // Update initial placeholder text based on selected language
    const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
    const langTranslations = translations[selectedLanguage] || translations.en;
    if (contentArea.firstElementChild && contentArea.firstElementChild.textContent.trim() === "Waiting for left reader...") {
        contentArea.firstElementChild.textContent = langTranslations.rightReaderWaiting;
    }
});
