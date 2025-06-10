/**
 * Second Reader Frontend Logic
 * Handles the functionality of the second Bible reader component,
 * which synchronizes with the main reader.
 */
document.addEventListener('DOMContentLoaded', () => {
    const versionSelect = document.getElementById('second-reader-version-select');
    const strongToggle = document.getElementById('second-reader-strong-toggle');
    const contentArea = document.getElementById('second-reader-content-area');

    let currentBook = null;
    let currentChapter = null;
    let currentVerses = null; // Store verses from main reader

    // Event listeners for controls
    versionSelect.addEventListener('change', displaySyncedContent);
    strongToggle.addEventListener('change', displaySyncedContent);

    /**
     * Subscribes to the main reader's chapter change event.
     */
    MockMediator.subscribe('mainReaderChapterChanged', (data) => {
        console.log('SecondReader: Received chapter change from MainReader:', data);
        currentBook = data.book; // This is the display name from main reader
        currentChapter = data.chapter;
        currentVerses = data.verses; // Store the detailed verse data
        // Store the internal version value from main reader if provided, for potential intelligent fetching
        // currentMainReaderInternalVersion = data.internalVersionValue || 'unv';
        // Display content immediately with current settings or fetch new version
        displaySyncedContent();
    });

    /**
     * Displays the content in the second reader, synchronized with the main reader.
     * This might involve re-fetching data if a different version is selected,
     * or re-rendering if only Strong's numbers preference changed.
     */
    async function displaySyncedContent() {
        const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
        const langTranslations = translations[selectedLanguage] || translations.en;

        if (!currentBook || !currentChapter || !currentVerses) {
            contentArea.innerHTML = `<p>${langTranslations.secondReaderWaiting}</p>`;
            return;
        }

        const selectedVersion = versionSelect.value;
        const showStrongs = strongToggle.checked;

        contentArea.innerHTML = `<p>${langTranslations.loading} ${currentBook} ${langTranslations.mainReaderChapterLabel.toLowerCase()} ${currentChapter} (${selectedVersion.toUpperCase()})...</p>`;

        try {
            // If the version is different from what main reader provided (UNV)
            // or if main reader's version is not what we want, we might need to fetch.
            // For this example, let's assume main reader always provides UNV with Strong's.
            // The second reader will then re-render or fetch based on its own controls.

            // If the requested version is the same as main reader's initially loaded (UNV)
            // AND strongs preference matches what main reader COULD provide, we can re-use main reader's data.
            // However, the main reader example always fetches 'unv' with strong=true.
            // The second reader needs to fetch if version is different OR strongs is false (as main gives true).

            // For simplicity in this mock version:
            // If version is "unv" and strongs is true, use main reader's data directly.
            // Otherwise, simulate a fetch for the new version/strongs combination.
            if (selectedVersion === 'unv' && showStrongs && mainReaderProvidedStrongs()) {
                console.log('SecondReader: Rendering UNV with Strongs from main reader data.');
                renderChapter({
                    book: currentBook,
                    chapter: currentChapter,
                    version: selectedVersion.toUpperCase(),
                    strong: showStrongs,
                    verses: currentVerses // Use the verses passed by the main reader
                });
            } else {
                // Simulate fetching for other versions or if Strong's is off for UNV
                console.log(`SecondReader: Simulating fetch for ${selectedVersion}, Strongs: ${showStrongs}`);
                const apiUrl = `/api/bible/${selectedVersion}/${currentBook.toLowerCase().replace(/\s+/g, '')}/${currentChapter}?strong=${showStrongs ? 1 : 0}`;
                console.log(`SecondReader: Fetching from ${apiUrl}`);

                // Mock API call for other versions
                let mockVerseText = `Generic text for ${selectedVersion}.`;
                let versionDisplayText = selectedVersion.toUpperCase();

                const versionOption = Array.from(versionSelect.options).find(opt => opt.value === selectedVersion);
                if (versionOption) {
                    versionDisplayText = versionOption.text;
                }


                if (selectedVersion === 'kjv') {
                    mockVerseText = "In the beginning God created the heaven and the earth (KJV).";
                } else if (selectedVersion === 'esv') {
                    mockVerseText = "In the beginning God created the heavens and the earth (ESV).";
                } else if (selectedVersion === 'rcuv2010') {
                    mockVerseText = "起初神創造天地 (和合本2010)。";
                } else if (selectedVersion === 'lcc') {
                    mockVerseText = "起初，上帝創造了天地 (呂振中)。";
                }

                const mockFetchedData = {
                    book: currentBook, // Already display name
                    chapter: currentChapter,
                    version: versionDisplayText, // Use display text
                    strong: showStrongs,
                    verses: currentVerses.map(v => ({ // Re-map based on original verse structure
                        verse: v.verse,
                        // Simulate slightly different text and Strong's based on version/preference
                        text: `[${versionDisplayText}] Verse ${v.verse}: ${mockVerseText} (Original text reference: ${v.text.substring(0,30)}...)`,
                        strongs: showStrongs ? (v.strongs || []) : [] // Include strongs only if toggled, ensure v.strongs exists
                    }))
                };
                await new Promise(resolve => setTimeout(resolve, 300)); // Simulate network delay
                renderChapter(mockFetchedData);
            }
        } catch (error) {
            console.error('SecondReader: Error loading/displaying chapter content:', error);
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

            let verseText = verse.text;
            if (data.strong && verse.strongs && verse.strongs.length > 0) {
                verse.strongs.forEach(strongObj => {
                    for (const strongNum in strongObj) {
                        const word = strongObj[strongNum];
                        verseText = verseText.replace(word, `${word} <span class="strongs-number" data-strong="${strongNum}">(${strongNum})</span>`);
                    }
                });
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

    // Update initial placeholder text based on selected language
    const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
    const langTranslations = translations[selectedLanguage] || translations.en;
    if (contentArea.firstElementChild && contentArea.firstElementChild.textContent.trim() === "Waiting for main reader...") {
        contentArea.firstElementChild.textContent = langTranslations.secondReaderWaiting;
    }
});
