// Simplified vertical resizing for content areas only
class VerticalResizer {
    constructor() {
        this.isResizing = false;
        this.startY = 0;
        this.startHeight = 0;
        this.currentHandle = null;
        this.targetElement = null;

        this.initializeResizers();
    }

    initializeResizers() {
        this.attachEventListeners();

        document.addEventListener('mousemove', this.doResize.bind(this));
        document.addEventListener('mouseup', this.stopResize.bind(this));

        // Re-attach event listeners when new handles are added
        const observer = new MutationObserver(() => {
            this.attachEventListeners();
        });

        // Observe both content areas for changes
        const leftContent = document.getElementById('left-reader-content-area');
        const rightContent = document.getElementById('right-reader-content-area');

        if (leftContent) observer.observe(leftContent, { childList: true });
        if (rightContent) observer.observe(rightContent, { childList: true });
    }

    attachEventListeners() {
        // Remove existing listeners to prevent duplicates
        const handles = document.querySelectorAll('.resize-handle-s[data-target]');

        handles.forEach(handle => {
            // Remove any existing listener first
            handle.removeEventListener('mousedown', this.startResize);
            // Add the listener
            handle.addEventListener('mousedown', this.startResize.bind(this));
        });
    }

    startResize(e) {
        e.preventDefault();

        this.isResizing = true;
        this.currentHandle = e.target;
        this.startY = e.clientY;

        const target = this.currentHandle.getAttribute('data-target');
        this.targetElement = this.getTargetElement(target);

        if (this.targetElement) {
            this.startHeight = parseInt(getComputedStyle(this.targetElement).height, 10);
            document.body.style.cursor = 's-resize';
            document.body.style.userSelect = 'none';
        }
    }

    doResize(e) {
        if (!this.isResizing || !this.targetElement) return;

        e.preventDefault();

        const deltaY = e.clientY - this.startY;
        const target = this.currentHandle.getAttribute('data-target');

        // Different minimum heights for different elements
        let minHeight = 100;
        if (target.includes('status')) {
            minHeight = 40; // Status areas can be smaller
        }

        const newHeight = Math.max(minHeight, this.startHeight + deltaY);

        // Set height on current element
        this.targetElement.style.height = newHeight + 'px';

        // Synchronize with the corresponding element in the other reader
        this.synchronizeHeight(newHeight);
    }

    stopResize() {
        if (this.isResizing) {
            this.isResizing = false;
            this.currentHandle = null;
            this.targetElement = null;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    }

    getTargetElement(target) {
        switch(target) {
            case 'left-content':
                return document.getElementById('left-reader-content-area');
            case 'right-content':
                return document.getElementById('right-reader-content-area');
            case 'left-status':
                return document.getElementById('left-reader-status-display');
            case 'right-status':
                return document.getElementById('right-reader-status-display');
            default:
                return null;
        }
    }

    synchronizeHeight(newHeight) {
        if (!this.currentHandle) return;

        const target = this.currentHandle.getAttribute('data-target');
        let correspondingElement = null;

        // Determine which element to synchronize with
        switch(target) {
            case 'left-content':
                correspondingElement = document.getElementById('right-reader-content-area');
                break;
            case 'right-content':
                correspondingElement = document.getElementById('left-reader-content-area');
                break;
            case 'left-status':
                correspondingElement = document.getElementById('right-reader-status-display');
                break;
            case 'right-status':
                correspondingElement = document.getElementById('left-reader-status-display');
                break;
        }

        // Apply the same height to the corresponding element
        if (correspondingElement) {
            correspondingElement.style.height = newHeight + 'px';
        }
    }
}

// Status area toggle functionality
function initializeStatusToggle() {
    const statusToggle = document.getElementById('status-toggle');
    const statusAreas = document.querySelectorAll('.status-area');

    if (statusToggle) {
        statusToggle.addEventListener('change', function() {
            statusAreas.forEach(area => {
                area.style.display = this.checked ? 'block' : 'none';
            });
        });
    }
}

// Follow Verse Scroll special highlighting based on main/follower status
function initializeFollowVerseScrollHighlighting() {
    const leftFollowScroll = document.getElementById('left-reader-follow-scroll');
    const rightFollowScroll = document.getElementById('right-reader-follow-scroll');
    const leftLabel = document.querySelector('label[for="left-reader-follow-scroll"]');
    const rightLabel = document.querySelector('label[for="right-reader-follow-scroll"]');

    function updateHighlighting() {
        // Get current main reader from MockMediator
        const mainReader = MockMediator ? MockMediator.getMainReader() : 'left';

        // Update left reader highlighting
        if (leftLabel) {
            if (mainReader === 'left') {
                // Left is MAIN - deep blue highlighting
                leftLabel.style.backgroundColor = '#1e40af';
                leftLabel.style.color = 'white';
                leftLabel.style.borderColor = '#1d4ed8';
                leftLabel.style.boxShadow = '0 2px 4px rgba(30, 64, 175, 0.3)';
            } else {
                // Left is FOLLOWER - orange-red highlighting
                leftLabel.style.backgroundColor = '#ea580c';
                leftLabel.style.color = 'white';
                leftLabel.style.borderColor = '#dc2626';
                leftLabel.style.boxShadow = '0 2px 4px rgba(234, 88, 12, 0.3)';
            }
        }

        // Update right reader highlighting
        if (rightLabel) {
            if (mainReader === 'right') {
                // Right is MAIN - deep blue highlighting
                rightLabel.style.backgroundColor = '#1e40af';
                rightLabel.style.color = 'white';
                rightLabel.style.borderColor = '#1d4ed8';
                rightLabel.style.boxShadow = '0 2px 4px rgba(30, 64, 175, 0.3)';
            } else {
                // Right is FOLLOWER - orange-red highlighting
                rightLabel.style.backgroundColor = '#ea580c';
                rightLabel.style.color = 'white';
                rightLabel.style.borderColor = '#dc2626';
                rightLabel.style.boxShadow = '0 2px 4px rgba(234, 88, 12, 0.3)';
            }
        }
    }

    // Initial highlighting
    setTimeout(updateHighlighting, 100); // Wait for MockMediator to be ready

    // Listen for main reader changes
    if (typeof MockMediator !== 'undefined') {
        // Override the setMainReader method to trigger highlighting updates
        const originalSetMainReader = MockMediator.setMainReader;
        MockMediator.setMainReader = function(readerType, interaction) {
            originalSetMainReader.call(this, readerType, interaction);
            updateHighlighting();
        };
    }

    // Also listen for checkbox changes to update highlighting
    if (leftFollowScroll) {
        leftFollowScroll.addEventListener('change', () => setTimeout(updateHighlighting, 50));
    }
    if (rightFollowScroll) {
        rightFollowScroll.addEventListener('change', () => setTimeout(updateHighlighting, 50));
    }

    // Global function to update highlighting (can be called from other scripts)
    window.updateFollowVerseScrollHighlighting = updateHighlighting;
}

// Initialize all functionalities when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new VerticalResizer();
    initializeStatusToggle();
    initializeFollowVerseScrollHighlighting();
});

const translations = {
    en: {
        leftReaderMainLabel: "Main:",
        rightReaderMainLabel: "Main:",
        leftReaderBookLabel: "BK:",
        rightReaderBookLabel: "BK:",
        leftReaderChapterLabel: "Cptr:",
        rightReaderChapterLabel: "Cptr:",
        leftReaderLoadButton: "Load Chapter",
        rightReaderLoadButton: "Load Chapter",
        rightReaderVersionLabel: "Ver:",
        rightReaderStrongsLabel: "SN:",
        leftReaderLoadingContent: "Loading content...",
        rightReaderWaiting: "Waiting for left reader...",
        pleaseSelectBookAndChapter: "Please select a book and chapter.",
        loading: "Loading...",
        strongsOn: "Strong's On",
        strongsOff: "Strong's Off",
        followVerseScroll: "FL Ver Scrl:",
        followTextSelection: "FL TxT Sel:",
        // Tooltips
        tooltips: {
            languageLabel: "Select interface language",
            languageSelect: "Choose interface language",
            versionLabel: "Select Bible version",
            leftVersionSelect: "Choose Bible version for left reader",
            rightVersionSelect: "Choose Bible version for right reader",
            bookLabel: "Select Bible book",
            leftBookSelect: "Choose Bible book for left reader",
            rightBookSelect: "Choose Bible book for right reader",
            chapterLabel: "Select chapter number",
            leftChapterInput: "Enter chapter number",
            rightChapterInput: "Enter chapter number",
            strongsToggle: "Toggle Strong's Numbers display",
            strongsLabel: "Show/hide Strong's Numbers",
            leftFollowSelection: "Follow right reader's text selection changes",
            leftFollowSelectionLabel: "Follow text selection from right reader",
            leftFollowScroll: "Follow right reader's verse scrolling",
            leftFollowScrollLabel: "Follow verse selection from right reader",
            rightFollowSelection: "Follow left reader's text selection changes",
            rightFollowSelectionLabel: "Follow text selection from left reader",
            rightFollowScroll: "Follow left reader's verse scrolling",
            rightFollowScrollLabel: "Follow verse selection from left reader",
            editMode: "Enable editing mode for inserting Strong's Numbers",
            editModeLabel: "Toggle edit mode for Strong's Number insertion",
            singleHighlight: "Single highlight mode: show only nearest Strong's position",
            singleHighlightLabel: "Single highlight mode: highlight only nearest Strong's position instead of all occurrences",
            strongsInputLabel: "Strong's Number input field",
            strongsInput: "Enter Strong's Number (e.g., H1234 or G5678) and press Enter to insert",
            debugToggle: "Show/hide debug console output",
            debugLabel: "Toggle debug console output for development",
            statusToggle: "Show/hide status information areas",
            statusLabel: "Toggle status display areas"
        }
    },
    zh: {
      languageName: "正體中文", // Assuming this should remain as the name in the language dropdown
      leftReaderMainLabel: "主要：",
      rightReaderMainLabel: "主要：",
      leftReaderBookLabel: "書卷：",
      rightReaderBookLabel: "書卷：",
      leftReaderChapterLabel: "章：",
      rightReaderChapterLabel: "章：",
      leftReaderLoadButton: "載入章節",
      rightReaderLoadButton: "載入章節",
      rightReaderVersionLabel: "版本：",
      rightReaderStrongsLabel: "SN：",
      leftReaderLoadingContent: "載入内容...",
      rightReaderWaiting: "等待左側 reader...",
      pleaseSelectBookAndChapter: "請選擇書卷和章節。",
      loading: "載入中...",
      strongsOn: "打開 Strong number",
      strongsOff: "關閉 Strong number",
      followVerseScroll: "跟隨經節滾動：",
      followTextSelection: "跟隨文本選擇：",
      // 工具提示
      tooltips: {
          languageLabel: "選擇界面語言",
          languageSelect: "選擇界面語言",
          versionLabel: "選擇聖經版本",
          leftVersionSelect: "選擇左側閱讀器的聖經版本",
          rightVersionSelect: "選擇右側閱讀器的聖經版本",
          bookLabel: "選擇聖經書卷",
          leftBookSelect: "選擇左側閱讀器的聖經書卷",
          rightBookSelect: "選擇右側閱讀器的聖經書卷",
          chapterLabel: "選擇章節號碼",
          leftChapterInput: "輸入章節號碼",
          rightChapterInput: "輸入章節號碼",
          strongsToggle: "切換Strong's Numbers顯示",
          strongsLabel: "顯示/隱藏Strong's Numbers",
          leftFollowSelection: "跟隨右側閱讀器的文本選擇變化",
          leftFollowSelectionLabel: "跟隨右側閱讀器的文本選擇",
          leftFollowScroll: "跟隨右側閱讀器的經節滾動",
          leftFollowScrollLabel: "跟隨右側閱讀器的經節選擇",
          rightFollowSelection: "跟隨左側閱讀器的文本選擇變化",
          rightFollowSelectionLabel: "跟隨左側閱讀器的文本選擇",
          rightFollowScroll: "跟隨左側閱讀器的經節滾動",
          rightFollowScrollLabel: "跟隨左側閱讀器的經節選擇",
          editMode: "啟用編輯模式以插入Strong's Numbers",
          editModeLabel: "切換編輯模式以插入Strong's Numbers",
          singleHighlight: "單一高亮模式：僅顯示最近的Strong's位置",
          singleHighlightLabel: "單一高亮模式：僅高亮最近的Strong's位置而非所有出現位置",
          strongsInputLabel: "Strong's Numbers輸入欄位",
          strongsInput: "輸入Strong's Numbers（例如H1234或G5678）並按Enter插入",
          debugToggle: "顯示/隱藏調試控制台輸出",
          debugLabel: "切換開發調試控制台輸出",
          statusToggle: "顯示/隱藏狀態信息區域",
          statusLabel: "切換狀態顯示區域"
      }
    }
};

function updateUIText(language) {
    const langTranslations = translations[language];
    if (!langTranslations) {
        console.error(`Translations not found for language: ${language}`);
        return;
    }

    // Update text elements in left_reader_frontend.js
    const leftReaderMainLabel = document.querySelector('#left-reader-component .reader-controls label[for="left-reader-main-toggle"]');
    if (leftReaderMainLabel) leftReaderMainLabel.textContent = langTranslations.leftReaderMainLabel;

    const leftReaderBookLabel = document.querySelector('#left-reader-component .reader-controls label[for="left-reader-book"]');
    if (leftReaderBookLabel) leftReaderBookLabel.textContent = langTranslations.leftReaderBookLabel;

    const leftReaderChapterLabel = document.querySelector('#left-reader-component .reader-controls label[for="left-reader-chapter"]');
    if (leftReaderChapterLabel) leftReaderChapterLabel.textContent = langTranslations.leftReaderChapterLabel;

    // Load buttons removed from layout

    // Update text elements in right_reader_frontend.js
    const rightReaderMainLabel = document.querySelector('#right-reader-component .reader-controls label[for="right-reader-main-toggle"]');
    if (rightReaderMainLabel) rightReaderMainLabel.textContent = langTranslations.rightReaderMainLabel;

    const rightReaderVersionLabel = document.querySelector('label[for="right-reader-version-select"]');
    if (rightReaderVersionLabel) rightReaderVersionLabel.textContent = langTranslations.rightReaderVersionLabel;

    const rightReaderStrongsLabel = document.querySelector('label[for="right-reader-strong-toggle"]');
    if (rightReaderStrongsLabel) rightReaderStrongsLabel.textContent = langTranslations.rightReaderStrongsLabel;

    const leftReaderVersionLabel = document.querySelector('label[for="left-reader-version-select"]');
    if (leftReaderVersionLabel) leftReaderVersionLabel.textContent = langTranslations.rightReaderVersionLabel;

    const leftReaderStrongsLabel = document.querySelector('label[for="left-reader-strong-toggle"]');
    if (leftReaderStrongsLabel) leftReaderStrongsLabel.textContent = langTranslations.rightReaderStrongsLabel;

    // Update right reader labels
    const rightReaderBookLabel = document.querySelector('label[for="right-reader-book"]');
    if (rightReaderBookLabel) rightReaderBookLabel.textContent = langTranslations.rightReaderBookLabel;

    const rightReaderChapterLabel = document.querySelector('label[for="right-reader-chapter"]');
    if (rightReaderChapterLabel) rightReaderChapterLabel.textContent = langTranslations.rightReaderChapterLabel;

    // Load buttons removed from layout

    // Update follow checkbox labels
    const leftFollowScrollLabel = document.querySelector('label[for="left-reader-follow-scroll"]');
    if (leftFollowScrollLabel) leftFollowScrollLabel.textContent = langTranslations.followVerseScroll;

    const leftFollowSelectionLabel = document.querySelector('label[for="left-reader-follow-selection"]');
    if (leftFollowSelectionLabel) leftFollowSelectionLabel.textContent = langTranslations.followTextSelection;

    const rightFollowScrollLabel = document.querySelector('label[for="right-reader-follow-scroll"]');
    if (rightFollowScrollLabel) rightFollowScrollLabel.textContent = langTranslations.followVerseScroll;

    const rightFollowSelectionLabel = document.querySelector('label[for="right-reader-follow-selection"]');
    if (rightFollowSelectionLabel) rightFollowSelectionLabel.textContent = langTranslations.followTextSelection;

    // Update dynamic content placeholders if they exist (initial load)
    const leftReaderContentArea = document.getElementById('left-reader-content-area');
    if (leftReaderContentArea && leftReaderContentArea.firstElementChild && leftReaderContentArea.firstElementChild.textContent.trim() === "Loading content...") {
        leftReaderContentArea.firstElementChild.textContent = langTranslations.leftReaderLoadingContent;
    }

    const rightReaderContentArea = document.getElementById('right-reader-content-area');
    if (rightReaderContentArea && rightReaderContentArea.firstElementChild && rightReaderContentArea.firstElementChild.textContent.trim() === "Waiting for left reader...") {
        rightReaderContentArea.firstElementChild.textContent = langTranslations.rightReaderWaiting;
    }

    // Update tooltips
    if (langTranslations.tooltips) {
        const tooltips = langTranslations.tooltips;

        // Language selector
        const languageLabel = document.querySelector('label[for="language"]');
        if (languageLabel) languageLabel.title = tooltips.languageLabel;
        const languageSelect = document.getElementById('language');
        if (languageSelect) languageSelect.title = tooltips.languageSelect;

        // Version controls
        const leftVersionLabel = document.querySelector('label[for="left-reader-version-select"]');
        if (leftVersionLabel) leftVersionLabel.title = tooltips.versionLabel;
        const leftVersionSelect = document.getElementById('left-reader-version-select');
        if (leftVersionSelect) leftVersionSelect.title = tooltips.leftVersionSelect;

        const rightVersionLabel = document.querySelector('label[for="right-reader-version-select"]');
        if (rightVersionLabel) rightVersionLabel.title = tooltips.versionLabel;
        const rightVersionSelect = document.getElementById('right-reader-version-select');
        if (rightVersionSelect) rightVersionSelect.title = tooltips.rightVersionSelect;

        // Book controls
        const leftBookLabel = document.querySelector('label[for="left-reader-book"]');
        if (leftBookLabel) leftBookLabel.title = tooltips.bookLabel;
        const leftBookSelect = document.getElementById('left-reader-book');
        if (leftBookSelect) leftBookSelect.title = tooltips.leftBookSelect;

        const rightBookLabel = document.querySelector('label[for="right-reader-book"]');
        if (rightBookLabel) rightBookLabel.title = tooltips.bookLabel;
        const rightBookSelect = document.getElementById('right-reader-book');
        if (rightBookSelect) rightBookSelect.title = tooltips.rightBookSelect;

        // Chapter controls
        const leftChapterLabel = document.querySelector('label[for="left-reader-chapter"]');
        if (leftChapterLabel) leftChapterLabel.title = tooltips.chapterLabel;
        const leftChapterInput = document.getElementById('left-reader-chapter');
        if (leftChapterInput) leftChapterInput.title = tooltips.leftChapterInput;

        const rightChapterLabel = document.querySelector('label[for="right-reader-chapter"]');
        if (rightChapterLabel) rightChapterLabel.title = tooltips.chapterLabel;
        const rightChapterInput = document.getElementById('right-reader-chapter');
        if (rightChapterInput) rightChapterInput.title = tooltips.rightChapterInput;

        // Strong's Numbers controls
        const leftStrongsToggle = document.getElementById('left-reader-strong-toggle');
        if (leftStrongsToggle) leftStrongsToggle.title = tooltips.strongsToggle;
        const leftStrongsLabel = document.querySelector('label[for="left-reader-strong-toggle"]');
        if (leftStrongsLabel) leftStrongsLabel.title = tooltips.strongsLabel;

        const rightStrongsToggle = document.getElementById('right-reader-strong-toggle');
        if (rightStrongsToggle) rightStrongsToggle.title = tooltips.strongsToggle;
        const rightStrongsLabel = document.querySelector('label[for="right-reader-strong-toggle"]');
        if (rightStrongsLabel) rightStrongsLabel.title = tooltips.strongsLabel;

        // Follow controls
        const leftFollowSelection = document.getElementById('left-reader-follow-selection');
        if (leftFollowSelection) leftFollowSelection.title = tooltips.leftFollowSelection;
        const leftFollowSelectionLabel = document.querySelector('label[for="left-reader-follow-selection"]');
        if (leftFollowSelectionLabel) leftFollowSelectionLabel.title = tooltips.leftFollowSelectionLabel;

        const leftFollowScroll = document.getElementById('left-reader-follow-scroll');
        if (leftFollowScroll) leftFollowScroll.title = tooltips.leftFollowScroll;
        const leftFollowScrollLabel = document.querySelector('label[for="left-reader-follow-scroll"]');
        if (leftFollowScrollLabel) leftFollowScrollLabel.title = tooltips.leftFollowScrollLabel;

        const rightFollowSelection = document.getElementById('right-reader-follow-selection');
        if (rightFollowSelection) rightFollowSelection.title = tooltips.rightFollowSelection;
        const rightFollowSelectionLabel = document.querySelector('label[for="right-reader-follow-selection"]');
        if (rightFollowSelectionLabel) rightFollowSelectionLabel.title = tooltips.rightFollowSelectionLabel;

        const rightFollowScroll = document.getElementById('right-reader-follow-scroll');
        if (rightFollowScroll) rightFollowScroll.title = tooltips.rightFollowScroll;
        const rightFollowScrollLabel = document.querySelector('label[for="right-reader-follow-scroll"]');
        if (rightFollowScrollLabel) rightFollowScrollLabel.title = tooltips.rightFollowScrollLabel;

        // Edit mode controls
        const editModeToggle = document.getElementById('right-reader-edit-mode');
        if (editModeToggle) editModeToggle.title = tooltips.editMode;
        const editModeLabel = document.querySelector('label[for="right-reader-edit-mode"]');
        if (editModeLabel) editModeLabel.title = tooltips.editModeLabel;

        // Single highlight mode
        const singleHighlightToggle = document.getElementById('left-reader-highlight-mode');
        if (singleHighlightToggle) singleHighlightToggle.title = tooltips.singleHighlight;
        const singleHighlightLabel = document.querySelector('label[for="left-reader-highlight-mode"]');
        if (singleHighlightLabel) singleHighlightLabel.title = tooltips.singleHighlightLabel;

        // Strong's input controls
        const strongsInputLabel = document.querySelector('#right-reader-strong-controls span');
        if (strongsInputLabel) strongsInputLabel.title = tooltips.strongsInputLabel;
        const strongsInput = document.getElementById('strong-number-input');
        if (strongsInput) strongsInput.title = tooltips.strongsInput;

        // Debug and status controls
        const debugToggle = document.getElementById('debug-toggle');
        if (debugToggle) debugToggle.title = tooltips.debugToggle;
        const debugLabel = document.querySelector('label[for="debug-toggle"]');
        if (debugLabel) debugLabel.title = tooltips.debugLabel;

        const statusToggle = document.getElementById('status-toggle');
        if (statusToggle) statusToggle.title = tooltips.statusToggle;
        const statusLabel = document.querySelector('label[for="status-toggle"]');
        if (statusLabel) statusLabel.title = tooltips.statusLabel;
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
