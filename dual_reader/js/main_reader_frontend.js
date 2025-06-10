/**
 * Main Reader Frontend Logic
 * Handles the functionality of the main Bible reader component.
 */
document.addEventListener('DOMContentLoaded', () => {
    const bookSelect = document.getElementById('main-reader-book');
    const chapterInput = document.getElementById('main-reader-chapter');
    const loadButton = document.getElementById('main-reader-load');
    const contentArea = document.getElementById('main-reader-content-area');
    const versionSelect = document.getElementById('main-reader-version-select'); // Changed from versionInput
    const strongInput = document.getElementById('main-reader-strong');   // Hidden input

    // Populate book select options (example, replace with actual book data)
    const books = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
        "Ecclesiastes", "Song of Songs", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
        "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
        "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
        "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
    ];
    books.forEach(book => {
        const option = document.createElement('option');
        option.value = book.toLowerCase().replace(/\s+/g, ''); // e.g., "genesis", "songofsongs"
        option.textContent = book;
        bookSelect.appendChild(option);
    });

    // Event listener for the load button
    loadButton.addEventListener('click', loadChapterContent);

    /**
     * Loads the chapter content based on selected book, chapter, version, and Strong's numbers preference.
     */
    async function loadChapterContent() {
        const book = bookSelect.value;
        const chapter = chapterInput.value;
        const version = versionSelect.value; // Read from the select dropdown
        const strong = strongInput.value; // "1" for true, "0" for false

        const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
        const langTranslations = translations[selectedLanguage] || translations.en;

        if (!book || !chapter) {
            contentArea.innerHTML = `<p>${langTranslations.pleaseSelectBookAndChapter}</p>`;
            return;
        }

        contentArea.innerHTML = `<p>${langTranslations.loading} ${bookSelect.options[bookSelect.selectedIndex].text} ${langTranslations.mainReaderChapterLabel.toLowerCase()} ${chapter}...</p>`;

        try {
            // Construct the API URL (example using a local Flask backend)
            // The actual API endpoint will depend on your backend setup.
            // For now, we'll use a placeholder and simulate a fetch.
            const apiUrl = `/api/bible/${version}/${book}/${chapter}?strong=${strong}`;
            console.log(`MainReader: Fetching from ${apiUrl}`);

            // Simulate API call
            // const response = await fetch(apiUrl);
            // if (!response.ok) {
            //     throw new Error(`HTTP error! status: ${response.status}`);
            // }
            // const data = await response.json();

            // Mock data for now, as the backend isn't implemented yet
            // Get the display text of the selected version
            const selectedVersionOption = versionSelect.options[versionSelect.selectedIndex];
            const versionDisplayText = selectedVersionOption ? selectedVersionOption.text : version.toUpperCase();

            const mockData = {
                book: bookSelect.options[bookSelect.selectedIndex].text,
                chapter: chapter,
                version: versionDisplayText, // Use display text for rendering
                strong: strong === "1",
                verses: [
                    {
                        verse: 1,
                        text: `[${versionDisplayText}] In the beginning God created the heavens and the earth. (Verse 1 text for ${book} ${chapter})`,
                        strongs: strong === "1" ? [{ "G1234": "beginning" }, { "G5678": "God" }] : []
                    },
                    {
                        verse: 2,
                        text: `[${versionDisplayText}] And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters. (Verse 2 text for ${book} ${chapter})`,
                        strongs: strong === "1" ? [{ "G0001": "earth" }] : []
                    },
                    {
                        verse: 3,
                        text: `[${versionDisplayText}] And God said, Let there be light: and there was light. (Verse 3 text for ${book} ${chapter})`,
                        strongs: strong === "1" ? [{ "G0002": "God" }, { "G0003": "light" }] : []
                    },
                    {
                        verse: 4,
                        text: `[${versionDisplayText}] And God saw the light, that it was good: and God divided the light from the darkness. (Verse 4 text for ${book} ${chapter})`,
                        strongs: []
                    },
                    {
                        verse: 5,
                        text: `[${versionDisplayText}] And God called the light Day, and the darkness he called Night. And the evening and the morning were the first day. (Verse 5 text for ${book} ${chapter})`,
                        strongs: strong === "1" ? [{ "G0004": "Day" }, {"G0005": "Night"}] : []
                    }
                ]
            };
            await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
            const data = mockData;


            renderChapter(data);
            // Publish an event that the main reader's content has changed
            MockMediator.publish('mainReaderChapterChanged', {
                book: data.book,
                chapter: parseInt(chapter),
                version: data.version, // This should be the actual version value (e.g., 'unv', 'kjv') for consistency if second reader fetches
                internalVersionValue: version, // Pass the actual value for API calls if needed by second reader
                strong: data.strong,
                verses: data.verses // Pass the actual verses
            });

        } catch (error) {
            console.error('MainReader: Error loading chapter content:', error);
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
            htmlContent += `<p class="verse" data-verse="${verse.verse}">`;
            htmlContent += `<span class="verse-number">${verse.verse}</span> `;

            // Simple text rendering for now. Strong's numbers would need more complex handling.
            let verseText = verse.text;
            if (data.strong && verse.strongs && verse.strongs.length > 0) {
                // This is a simplified way to show strong's numbers.
                // A more robust solution would involve mapping them to specific words.
                verse.strongs.forEach(strongObj => {
                    for (const strongNum in strongObj) {
                        const word = strongObj[strongNum];
                        // Naive replacement, might not always be accurate for multiple occurrences
                        verseText = verseText.replace(word, `${word} <span class="strongs-number" data-strong="${strongNum}">(${strongNum})</span>`);
                    }
                });
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
     * Attaches event listeners to Strong's number elements.
     */
    function attachStrongsEventListeners() {
        const strongsElements = contentArea.querySelectorAll('.strongs-number');
        strongsElements.forEach(el => {
            el.addEventListener('click', () => {
                const strongNum = el.dataset.strong;
                console.log(`MainReader: Strong's number ${strongNum} clicked.`);
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

    // Initial load (optional, or trigger via button)
    // loadChapterContent();
    // For now, let's not auto-load to allow users to select first.
    // Update initial placeholder text based on selected language
    const selectedLanguage = localStorage.getItem('selectedLanguage') || 'en';
    const langTranslations = translations[selectedLanguage] || translations.en;
    if (contentArea.firstElementChild && contentArea.firstElementChild.textContent.trim() === "Loading content...") {
         contentArea.firstElementChild.textContent = langTranslations.mainReaderLoadingContent;
    }


    // Subscribe to events from other components (if needed)
    // e.g., MockMediator.subscribe('secondReaderSettingsChanged', (data) => {
    //     console.log('MainReader received settings change from second reader:', data);
    //     // Potentially update main reader if its settings are linked
    // });
});
