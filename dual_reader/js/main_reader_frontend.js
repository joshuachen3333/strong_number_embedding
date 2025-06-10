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
    const apiUrlDisplay = document.getElementById('main-reader-api-url-display'); // For displaying FHL.net URL

    // Populate book select options
    const books = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
        "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalms", "Proverbs",
        "Ecclesiastes", "Song of Songs", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel",
        "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
        "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon",
        "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
    ];

    if (bookSelect && books && books.length > 0) {
        console.log('Populating book select dropdown...');
        console.log(`Found bookSelect element: ${bookSelect.id}`);
        console.log(`Total books to populate: ${books.length}`);

        // Clear existing options first - intentionally NOT doing this for now, as per subtask instruction.
        // bookSelect.innerHTML = '';

        books.forEach(book => {
            const option = document.createElement('option');
            option.value = book.toLowerCase().replace(/\s+/g, ''); // e.g., "genesis", "songofsongs"
            option.textContent = book;
            bookSelect.appendChild(option);
            console.log(`Adding book: ${book}`); // Kept from previous step
        });
        console.log(`Finished populating books. Total options: ${bookSelect.options.length}`);
    } else {
        console.error('Could not populate book select: bookSelect element not found or books array is empty.');
        if (!bookSelect) console.error('bookSelect is null or undefined.');
        if (!books || books.length === 0) console.error('books array is null, undefined, or empty.');
    }

    // Event listener for the load button
    loadButton.addEventListener('click', loadChapterContent);

    // Add event listeners for automatic content loading on change - REMOVED
    // bookSelect.addEventListener('change', loadChapterContent);
    // chapterInput.addEventListener('change', loadChapterContent);
    // versionSelect.addEventListener('change', loadChapterContent);

    /**
     * Loads the chapter content based on selected book, chapter, version, and Strong's numbers preference.
     */
    async function loadChapterContent() {
        const book = bookSelect.value;
        const chapter = chapterInput.value;
        const version = versionSelect.value; // Read from the select dropdown
        const strong = strongInput.value; // "1" for true, "0" for false (Main reader strongs is implicitly on for UNV)

        // Construct and display FHL.net URL
        const fhlNetBookName = bookSelect.options[bookSelect.selectedIndex].text; // Using English book name as placeholder for 'chineses'
        // Simplified FHL URL construction for display - actual API parameters might vary
        const fhlUrl = `https://bible.fhl.net/new/read.php?chineses=${encodeURIComponent(fhlNetBookName)}&chap=${chapter}&VERSION=${version}&strongflag=1&TABFLAG=1`;
        if (apiUrlDisplay) {
            apiUrlDisplay.textContent = fhlUrl;
        }

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

            console.log(`MainReader: Loading version '${version}' (${versionDisplayText})`); // Added logging

            const mockData = {
                book: bookSelect.options[bookSelect.selectedIndex].text,
                chapter: chapter,
                version: versionDisplayText, // Use display text for rendering
                strong: strong === "1",
                verses: [
                    // Genesis 1 (Sample Verses)
                    { verse: 1, text: `[${versionDisplayText}] In the beginning God created the heavens and the earth.` , strongs: strong === "1" ? [{"H7225":"beginning"},{"H1254":"God created"},{"H853":"את"},{"H8064":"heavens"},{"H853":"את"},{"H776":"earth"}] : []},
                    { verse: 2, text: `[${versionDisplayText}] Now the earth was formless and empty, darkness was over the surface of the deep, and the Spirit of God was hovering over the waters.` , strongs: strong === "1" ? [{"H776":"earth"},{"H1961":"was"},{"H8414":"formless"},{"H922":"empty"},{"H2822":"darkness"},{"H5921":"over"},{"H6440":"surface"},{"H8415":"deep"},{"H7307":"Spirit"},{"H430":"God"},{"H7363":"hovering"},{"H5921":"over"},{"H6440":"surface"},{"H4325":"waters"}] : []},
                        { verse: 3, text: `[${versionDisplayText}] And God said, \"Let there be light,\" and there was light.` , strongs: strong === "1" ? [{"H430":"God"},{"H559":"said"},{"H1961":"Let there be"},{"H216":"light"},{"H1961":"there was"},{"H216":"light"}] : []},
                        { verse: 4, text: `[${versionDisplayText}] God saw that the light was good, and he separated the light from the darkness.` , strongs: strong === "1" ? [{"H430":"God"},{"H7200":"saw"},{"H216":"light"},{"H2896":"good"},{"H430":"God"},{"H914":"separated"},{"H996":"between"},{"H216":"light"},{"H996":"between"},{"H2822":"darkness"}] : []},
                        { verse: 5, text: `[${versionDisplayText}] God called the light \"day,\" and the darkness he called \"night.\" And there was evening, and there was morning—the first day.` , strongs: strong === "1" ? [{"H430":"God"},{"H7121":"called"},{"H216":"light"},{"H3117":"day"},{"H2822":"darkness"},{"H7121":"called"},{"H3915":"night"},{"H1961":"And there was"},{"H6153":"evening"},{"H1961":"and there was"},{"H1242":"morning"},{"H259":"first"},{"H3117":"day"}] : []},
                        { verse: 6, text: `[${versionDisplayText}] And God said, \"Let there be a vault between the waters to separate water from water.\"` , strongs: []},
                        { verse: 7, text: `[${versionDisplayText}] So God made the vault and separated the water under the vault from the water above it. And it was so.` , strongs: []},
                        { verse: 8, text: `[${versionDisplayText}] God called the vault \"sky.\" And there was evening, and there was morning—the second day.` , strongs: []},
                        { verse: 9, text: `[${versionDisplayText}] And God said, \"Let the water under the sky be gathered to one place, and let dry ground appear.\" And it was so.` , strongs: []},
                        { verse: 10, text: `[${versionDisplayText}] God called the dry ground \"land,\" and the gathered waters he called \"seas.\" And God saw that it was good.` , strongs: []},
                        { verse: 11, text: `[${versionDisplayText}] Then God said, \"Let the land produce vegetation: seed-bearing plants and trees on the land that bear fruit with seed in it, according to their various kinds.\" And it was so.` , strongs: []},
                        { verse: 12, text: `[${versionDisplayText}] The land produced vegetation: plants bearing seed according to their kinds and trees bearing fruit with seed in it according to their kinds. And God saw that it was good.` , strongs: []},
                        { verse: 13, text: `[${versionDisplayText}] And there was evening, and there was morning—the third day.` , strongs: []},
                        { verse: 14, text: `[${versionDisplayText}] And God said, \"Let there be lights in the vault of the sky to separate the day from the night, and let them serve as signs to mark sacred times, and days and years,` , strongs: []},
                        { verse: 15, text: `[${versionDisplayText}] and let them be lights in the vault of the sky to give light on the earth.\" And it was so.` , strongs: []},
                        { verse: 16, text: `[${versionDisplayText}] God made two great lights—the greater light to govern the day and the lesser light to govern the night. He also made the stars.` , strongs: []},
                        { verse: 17, text: `[${versionDisplayText}] God set them in the vault of the sky to give light on the earth,` , strongs: []},
                        { verse: 18, text: `[${versionDisplayText}] to govern the day and the night, and to separate light from darkness. And God saw that it was good.` , strongs: []},
                        { verse: 19, text: `[${versionDisplayText}] And there was evening, and there was morning—the fourth day.` , strongs: []},
                        { verse: 20, text: `[${versionDisplayText}] And God said, \"Let the water teem with living creatures, and let birds fly above the earth across the vault of the sky.\"` , strongs: []},
                        { verse: 21, text: `[${versionDisplayText}] So God created the great creatures of the sea and every living thing with which the water teems and that moves about in it, according to their kinds, and every winged bird according to its kind. And God saw that it was good.` , strongs: []},
                        { verse: 22, text: `[${versionDisplayText}] God blessed them and said, \"Be fruitful and increase in number and fill the water in the seas, and let the birds increase on the earth.\"` , strongs: []},
                        { verse: 23, text: `[${versionDisplayText}] And there was evening, and there was morning—the fifth day.` , strongs: []},
                        { verse: 24, text: `[${versionDisplayText}] And God said, \"Let the land produce living creatures according to their kinds: the livestock, the creatures that move along the ground, and the wild animals, each according to its kind.\" And it was so.` , strongs: []},
                        { verse: 25, text: `[${versionDisplayText}] God made the wild animals according to their kinds, the livestock according to their kinds, and all the creatures that move along the ground according to their kinds. And God saw that it was good.` , strongs: []}
                    ]
            };

            if (version === 'lcc') {
                console.log('MainReader: Mock data for LCC (first 2 verses):', JSON.stringify(mockData.verses.slice(0, 2))); // Added logging
            }

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
