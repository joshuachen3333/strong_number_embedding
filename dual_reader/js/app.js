const translations = {
    en: {
        leftReaderTitle: "Left Reader",
        rightReaderTitle: "Right Reader",
        leftReaderBookLabel: "Book:",
        leftReaderChapterLabel: "Chapter:",
        leftReaderLoadButton: "Load Chapter",
        rightReaderVersionLabel: "Version:",
        rightReaderStrongsLabel: "Strong's Numbers:",
        leftReaderLoadingContent: "Loading content...",
        rightReaderWaiting: "Waiting for left reader...",
        pleaseSelectBookAndChapter: "Please select a book and chapter.",
        loading: "Loading...",
        strongsOn: "Strong's On",
        strongsOff: "Strong's Off"
    },
    zh: {
      languageName: "正體中文", // Assuming this should remain as the name in the language dropdown
      leftReaderTitle: "左側 reader",
      rightReaderTitle: "右側 reader",
      leftReaderBookLabel: "書卷：",
      leftReaderChapterLabel: "章：",
      leftReaderLoadButton: "載入章節",
      rightReaderVersionLabel: "版本：",
      rightReaderStrongsLabel: "Strong number：",
      leftReaderLoadingContent: "載入内容...",
      rightReaderWaiting: "等待左側 reader...",
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
    const leftReaderTitleEl = document.getElementById('leftReaderTitle');
    if (leftReaderTitleEl) leftReaderTitleEl.textContent = langTranslations.leftReaderTitle;

    const rightReaderTitleEl = document.getElementById('rightReaderTitle');
    if (rightReaderTitleEl) rightReaderTitleEl.textContent = langTranslations.rightReaderTitle;

    // Update text elements in left_reader_frontend.js
    const leftReaderBookLabel = document.querySelector('#left-reader-component .reader-controls label[for="left-reader-book"]');
    if (leftReaderBookLabel) leftReaderBookLabel.textContent = langTranslations.leftReaderBookLabel;

    const leftReaderChapterLabel = document.querySelector('#left-reader-component .reader-controls label[for="left-reader-chapter"]');
    if (leftReaderChapterLabel) leftReaderChapterLabel.textContent = langTranslations.leftReaderChapterLabel;

    const leftReaderLoadButton = document.getElementById('left-reader-load');
    if (leftReaderLoadButton) leftReaderLoadButton.textContent = langTranslations.leftReaderLoadButton;

    // Update text elements in right_reader_frontend.js
    const rightReaderVersionLabel = document.querySelector('#right-reader-component .reader-controls label[for="right-reader-version-select"]');
    if (rightReaderVersionLabel) rightReaderVersionLabel.textContent = langTranslations.rightReaderVersionLabel;

    const rightReaderStrongsLabel = document.querySelector('#right-reader-component .reader-controls label[for="right-reader-strong-toggle"]');
    if (rightReaderStrongsLabel) rightReaderStrongsLabel.textContent = langTranslations.rightReaderStrongsLabel;

    // Update dynamic content placeholders if they exist (initial load)
    const leftReaderContentArea = document.getElementById('left-reader-content-area');
    if (leftReaderContentArea && leftReaderContentArea.firstElementChild && leftReaderContentArea.firstElementChild.textContent.trim() === "Loading content...") {
        leftReaderContentArea.firstElementChild.textContent = langTranslations.leftReaderLoadingContent;
    }

    const rightReaderContentArea = document.getElementById('right-reader-content-area');
    if (rightReaderContentArea && rightReaderContentArea.firstElementChild && rightReaderContentArea.firstElementChild.textContent.trim() === "Waiting for left reader...") {
        rightReaderContentArea.firstElementChild.textContent = langTranslations.rightReaderWaiting;
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
 * Resize functionality for making areas draggable
 */
function initializeResizeHandles() {
    let isResizing = false;
    let currentElement = null;
    let resizeType = null;
    let startX = 0;
    let startY = 0;
    let startWidth = 0;
    let startHeight = 0;

    console.log("Initializing resize handles...");
    
    // Handle southeast resize (width and height)
    const seHandles = document.querySelectorAll('.resize-handle-se');
    console.log("Found SE handles:", seHandles.length);
    seHandles.forEach(handle => {
        handle.addEventListener('mousedown', (e) => {
            console.log("SE handle mousedown");
            isResizing = true;
            resizeType = 'se';
            currentElement = handle.parentElement;
            startX = e.clientX;
            startY = e.clientY;
            startWidth = parseInt(document.defaultView.getComputedStyle(currentElement).width, 10);
            startHeight = parseInt(document.defaultView.getComputedStyle(currentElement).height, 10);
            console.log("Starting resize:", { startWidth, startHeight });
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Handle south resize (height only)
    const sHandles = document.querySelectorAll('.resize-handle-s');
    console.log("Found S handles:", sHandles.length);
    sHandles.forEach(handle => {
        handle.addEventListener('mousedown', (e) => {
            console.log("S handle mousedown");
            isResizing = true;
            resizeType = 's';
            currentElement = handle.parentElement;
            startY = e.clientY;
            startHeight = parseInt(document.defaultView.getComputedStyle(currentElement).height, 10);
            console.log("Starting height resize:", { startHeight });
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Mouse move handler
    document.addEventListener('mousemove', (e) => {
        if (!isResizing || !currentElement) return;

        if (resizeType === 'se') {
            // Southeast resize: adjust both width and height
            const newWidth = startWidth + (e.clientX - startX);
            const newHeight = startHeight + (e.clientY - startY);
            
            if (newWidth >= 200 && newWidth <= window.innerWidth * 0.9) {
                currentElement.style.width = newWidth + 'px';
            }
            if (newHeight >= 100 && newHeight <= window.innerHeight * 0.9) {
                currentElement.style.height = newHeight + 'px';
            }
        } else if (resizeType === 's') {
            // South resize: adjust height only
            const newHeight = startHeight + (e.clientY - startY);
            
            if (newHeight >= 40 && newHeight <= window.innerHeight * 0.5) {
                currentElement.style.height = newHeight + 'px';
            }
        }
        e.preventDefault();
    });

    // Mouse up handler
    document.addEventListener('mouseup', (e) => {
        if (isResizing) {
            console.log("Resize ended");
        }
        isResizing = false;
        currentElement = null;
        resizeType = null;
    });

    console.log("Resize handles initialized");
}

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

    // Set up debug toggle functionality
    const debugToggle = document.getElementById('debug-toggle');
    const debugOutput = document.getElementById('debug-output');
    
    if (debugToggle && debugOutput) {
        debugToggle.addEventListener('change', () => {
            debugOutput.style.display = debugToggle.checked ? 'block' : 'none';
        });
        console.log("Debug toggle initialized");
    }

    // Initialize resize functionality
    initializeResizeHandles();

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
