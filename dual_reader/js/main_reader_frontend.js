/**
 * Main Reader Frontend Logic
 * Handles the functionality of the main Bible reader component.
 */
document.addEventListener('DOMContentLoaded', () => {
    const bookSelect = document.getElementById('main-reader-book');
    const chapterInput = document.getElementById('main-reader-chapter');
    const loadButton = document.getElementById('main-reader-load');
    const contentArea = document.getElementById('main-reader-content-area');
    const versionInput = document.getElementById('main-reader-version'); // Hidden input
    const strongInput = document.getElementById('main-reader-strong');   // Hidden input

    // Populate book select options (example, replace with actual book data)
    const books = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"]; // Add all books
    books.forEach(book => {
        const option = document.createElement('option');
        option.value = book.toLowerCase().replace(/\s+/g, ''); // e.g., "genesis"
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
        const version = versionInput.value; // e.g., "unv"
        const strong = strongInput.value; // "1" for true, "0" for false

        if (!book || !chapter) {
            contentArea.innerHTML = '<p>Please select a book and chapter.</p>';
            return;
        }

        contentArea.innerHTML = `<p>Loading ${bookSelect.options[bookSelect.selectedIndex].text} chapter ${chapter}...</p>`;

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
            const mockData = {
                book: bookSelect.options[bookSelect.selectedIndex].text,
                chapter: chapter,
                version: version.toUpperCase(),
                strong: strong === "1",
                verses: [
                    {
                        verse: 1,
                        text: "In the beginning God created the heavens and the earth.",
                        strongs: [{ "G1234": "beginning" }, { "G5678": "God" }] // Example
                    },
                    {
                        verse: 2,
                        text: "And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.",
                        strongs: []
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
                version: data.version,
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
        let htmlContent = `<h3>${data.book} ${data.chapter} (${data.version.toUpperCase()})</h3>`;
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
                    version: versionInput.value // or from data if more reliable
                });
                // Further action: display definition (could be another component subscribing to this)
                alert(`Strong's number clicked: ${strongNum}. Definition lookup not yet implemented.`);
            });
        });
    }

    // Initial load (optional, or trigger via button)
    // loadChapterContent();
    // For now, let's not auto-load to allow users to select first.

    // Subscribe to events from other components (if needed)
    // e.g., MockMediator.subscribe('secondReaderSettingsChanged', (data) => {
    //     console.log('MainReader received settings change from second reader:', data);
    //     // Potentially update main reader if its settings are linked
    // });
});
