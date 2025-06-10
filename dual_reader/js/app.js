const translations = {
    en: {
        mainReaderTitle: "Main Reader",
        secondReaderTitle: "Second Reader",
        mainReaderBookLabel: "Book:",
        mainReaderChapterLabel: "Chapter:",
        mainReaderLoadButton: "Load Chapter",
        secondReaderVersionLabel: "Version:",
        secondReaderStrongsLabel: "Strong's Numbers:",
        mainReaderLoadingContent: "Loading content...",
        secondReaderWaiting: "Waiting for main reader...",
        pleaseSelectBookAndChapter: "Please select a book and chapter.",
        loading: "Loading...",
        strongsOn: "Strong's On",
        strongsOff: "Strong's Off"
    },
    zh: {
      languageName: "正體中文", // Assuming this should remain as the name in the language dropdown
      mainReaderTitle: "main reader",
      secondReaderTitle: "2nd reader",
      mainReaderBookLabel: "書卷：",
      mainReaderChapterLabel: "章：",
      mainReaderLoadButton: "載入章節",
      secondReaderVersionLabel: "版本：",
      secondReaderStrongsLabel: "Strong number：",
      mainReaderLoadingContent: "載入内容...",
      secondReaderWaiting: "等待main reader...",
      pleaseSelectBookAndChapter: "請選擇書卷和章節。",
      loading: "載入中...",
      strongsOn: "打開 Strong number",
      strongsOff: "關閉 Strong number"
    }
};

function updateUIText(language) {
    const langTranslations = translations[language];
    if (!langTranslations) {
        console.error(`Translations not found for language: ${language}`);
        return;
    }

    // Update static text elements in index.html
    const mainReaderTitleEl = document.getElementById('mainReaderTitle');
    if (mainReaderTitleEl) mainReaderTitleEl.textContent = langTranslations.mainReaderTitle;

    const secondReaderTitleEl = document.getElementById('secondReaderTitle');
    if (secondReaderTitleEl) secondReaderTitleEl.textContent = langTranslations.secondReaderTitle;

    // Update text elements in main_reader_frontend.js
    const mainReaderBookLabel = document.querySelector('#main-reader-component .reader-controls label[for="main-reader-book"]');
    if (mainReaderBookLabel) mainReaderBookLabel.textContent = langTranslations.mainReaderBookLabel;

    const mainReaderChapterLabel = document.querySelector('#main-reader-component .reader-controls label[for="main-reader-chapter"]');
    if (mainReaderChapterLabel) mainReaderChapterLabel.textContent = langTranslations.mainReaderChapterLabel;

    const mainReaderLoadButton = document.getElementById('main-reader-load');
    if (mainReaderLoadButton) mainReaderLoadButton.textContent = langTranslations.mainReaderLoadButton;

    // Update text elements in second_reader_frontend.js
    const secondReaderVersionLabel = document.querySelector('#second-reader-component .reader-controls label[for="second-reader-version-select"]');
    if (secondReaderVersionLabel) secondReaderVersionLabel.textContent = langTranslations.secondReaderVersionLabel;

    const secondReaderStrongsLabel = document.querySelector('#second-reader-component .reader-controls label[for="second-reader-strong-toggle"]');
    if (secondReaderStrongsLabel) secondReaderStrongsLabel.textContent = langTranslations.secondReaderStrongsLabel;

    // Update dynamic content placeholders if they exist (initial load)
    const mainReaderContentArea = document.getElementById('main-reader-content-area');
    if (mainReaderContentArea && mainReaderContentArea.firstElementChild && mainReaderContentArea.firstElementChild.textContent.trim() === "Loading content...") {
        mainReaderContentArea.firstElementChild.textContent = langTranslations.mainReaderLoadingContent;
    }

    const secondReaderContentArea = document.getElementById('second-reader-content-area');
    if (secondReaderContentArea && secondReaderContentArea.firstElementChild && secondReaderContentArea.firstElementChild.textContent.trim() === "Waiting for main reader...") {
        secondReaderContentArea.firstElementChild.textContent = langTranslations.secondReaderWaiting;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const languageSelector = document.getElementById('language');
    if (!languageSelector) {
        console.error("Language selector not found!");
        return;
    }

    // Load saved language or default to English
    const savedLanguage = localStorage.getItem('selectedLanguage') || 'en';
    languageSelector.value = savedLanguage;
    updateUIText(savedLanguage); // Initial UI update

    languageSelector.addEventListener('change', (event) => {
        const selectedLanguage = event.target.value;
        localStorage.setItem('selectedLanguage', selectedLanguage);
        updateUIText(selectedLanguage);
    });
});

/**
 * Main Application Script
 * Initializes the Dual Bible Reader application.
 *
 * For this project, the primary initialization and event handling are within
 * main_reader_frontend.js and second_reader_frontend.js. This app.js
 * can be used for any overarching application setup or coordination if needed.
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("Dual Bible Reader application initializing...");

    // Example: Check if MockMediator is loaded
    if (typeof MockMediator !== 'undefined') {
        console.log("MockMediator is loaded and ready.");
    } else {
        console.error("MockMediator is not loaded. Communication between components may fail.");
    }

    // Example: You could publish an 'appLoaded' event if other components need to know
    // MockMediator.publish('appLoaded', { timestamp: new Date() });

    // At this point, main_reader_frontend.js and second_reader_frontend.js
    // should have already set up their respective components and event listeners
    // because their scripts are included before app.js and they also listen for
    // DOMContentLoaded.

    console.log("Dual Bible Reader application initialized.");
    console.log("Main reader and Second reader should be active.");
    console.log("Try loading a chapter in the Main Reader.");
});
