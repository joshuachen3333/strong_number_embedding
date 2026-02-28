/**
 * Hebrew Alphabet Cards - Main Application
 */

(function() {
    'use strict';

    // =====================
    // State
    // =====================
    const state = {
        currentPage: 'overview', // 'overview', 'card', 'print'
        currentLetterIndex: 0,
        currentForm: 'base', // 'base', 'final', 'vowel'
        isAnimating: false,
        autoStroke: true, // Auto-play stroke animation on card open
        autoAudio: false, // Auto-play audio on card open
        romanization: true // Include romanization in pronunciation
    };

    // Load preferences from localStorage
    const savedAutoStroke = localStorage.getItem('hebrewCards_autoStroke');
    if (savedAutoStroke !== null) {
        state.autoStroke = savedAutoStroke === 'true';
    }

    const savedAutoAudio = localStorage.getItem('hebrewCards_autoAudio');
    if (savedAutoAudio !== null) {
        state.autoAudio = savedAutoAudio === 'true';
    }

    const savedRomanization = localStorage.getItem('hebrewCards_romanization');
    if (savedRomanization !== null) {
        state.romanization = savedRomanization === 'true';
    }

    // =====================
    // DOM Elements
    // =====================
    const elements = {
        // Pages
        overviewPage: document.getElementById('overview-page'),
        cardPage: document.getElementById('card-page'),
        printPage: document.getElementById('print-page'),

        // Overview
        letterGrid: document.getElementById('letter-grid'),

        // Card elements
        currentLetter: document.getElementById('current-letter'),
        letterName: document.getElementById('letter-name'),
        letterSound: document.getElementById('letter-sound'),
        letterPosition: document.getElementById('letter-position'),
        exampleList: document.getElementById('example-list'),
        formIndicators: document.getElementById('form-indicators'),

        // Buttons
        btnBack: document.getElementById('btn-back'),
        btnPrev: document.getElementById('btn-prev'),
        btnNext: document.getElementById('btn-next'),
        btnPrint: document.getElementById('btn-print'),
        btnBase: document.getElementById('btn-base'),
        btnFinal: document.getElementById('btn-final'),
        btnVowel: document.getElementById('btn-vowel'),
        btnStroke: document.getElementById('btn-stroke'),
        btnAudio: document.getElementById('btn-audio'),
        autoStrokeToggle: document.getElementById('auto-stroke-toggle'),
        autoAudioToggle: document.getElementById('auto-audio-toggle'),
        romanizationToggle: document.getElementById('romanization-toggle'),

        // Stroke area
        strokeArea: document.getElementById('stroke-area'),
        strokeSvg: document.getElementById('stroke-svg'),

        // Print
        printLetter: document.getElementById('print-letter'),
        printName: document.getElementById('print-name'),

        // Keyboard hints
        keyboardHints: document.getElementById('keyboard-hints'),

        // Examples header
        examplesHeader: document.getElementById('examples-header')
    };

    // =====================
    // Initialize
    // =====================
    function init() {
        renderOverviewGrid();
        bindEvents();
        showPage('overview');

        // Set initial toggle states from saved preferences
        if (elements.autoStrokeToggle) {
            elements.autoStrokeToggle.checked = state.autoStroke;
        }
        if (elements.autoAudioToggle) {
            elements.autoAudioToggle.checked = state.autoAudio;
        }
        if (elements.romanizationToggle) {
            elements.romanizationToggle.checked = state.romanization;
        }
    }

    // =====================
    // Page Navigation
    // =====================
    function showPage(pageName) {
        state.currentPage = pageName;

        // Hide all pages
        elements.overviewPage.classList.remove('active');
        elements.cardPage.classList.remove('active');
        elements.printPage.classList.remove('active');

        // Show target page
        switch (pageName) {
            case 'overview':
                elements.overviewPage.classList.add('active');
                elements.keyboardHints.style.display = 'none';
                break;
            case 'card':
                elements.cardPage.classList.add('active');
                elements.keyboardHints.style.display = 'flex';
                renderCard();
                break;
            case 'print':
                elements.printPage.classList.add('active');
                elements.keyboardHints.style.display = 'none';
                renderPrintView();
                break;
        }
    }

    // =====================
    // Overview Grid
    // =====================
    function renderOverviewGrid() {
        elements.letterGrid.innerHTML = '';

        hebrewLetters.forEach((letterData, index) => {
            const item = document.createElement('div');
            item.className = 'grid-item';
            item.dataset.index = index;

            // Badges
            let badges = '<div class="badges">';
            if (letterData.hasFinalForm) {
                badges += '<span class="badge badge-f" title="有字尾形">F</span>';
            }
            if (letterData.hasVowelUse) {
                badges += '<span class="badge badge-v" title="可作母音">V</span>';
            }
            badges += '</div>';

            item.innerHTML = `
                ${badges}
                <div class="letter">${letterData.letter}</div>
                <div class="name">${letterData.name}</div>
            `;

            item.addEventListener('click', () => {
                state.currentLetterIndex = index;
                state.currentForm = 'base';
                showPage('card');
            });

            elements.letterGrid.appendChild(item);
        });
    }

    // =====================
    // Card Rendering
    // =====================
    function renderCard() {
        const letterData = hebrewLetters[state.currentLetterIndex];

        // Reset form to base
        state.currentForm = 'base';

        // Update letter display
        updateLetterDisplay();

        // Update position indicator
        elements.letterPosition.textContent = `${state.currentLetterIndex + 1} / 22`;

        // Update form buttons visibility
        updateFormButtons(letterData);

        // Render examples
        renderExamples(letterData);

        // Reset stroke area
        elements.strokeArea.classList.remove('active');
        state.isAnimating = false;

        // Auto-play stroke animation if enabled
        if (state.autoStroke) {
            // Small delay to let the card render first
            setTimeout(() => {
                playStrokeAnimation();
            }, 300);
        }

        // Auto-play audio if enabled
        if (state.autoAudio) {
            // Delay to let stroke animation start first (if enabled)
            const audioDelay = state.autoStroke ? 500 : 300;
            setTimeout(() => {
                playAudio();
            }, audioDelay);
        }
    }

    function updateLetterDisplay() {
        const letterData = hebrewLetters[state.currentLetterIndex];
        let displayLetter = letterData.letter;
        let displayName = letterData.name;
        let displaySound = letterData.sound;
        let letterClass = 'big-letter';

        // Handle different forms
        if (state.currentForm === 'final' && letterData.hasFinalForm) {
            displayLetter = letterData.finalForm.letter;
            displayName = letterData.finalForm.name;
            displaySound = letterData.finalForm.description;
            letterClass += ' final-form';
        } else if (state.currentForm === 'vowel' && letterData.hasVowelUse) {
            displayLetter = letterData.vowelInfo.letter;
            displayName = `${letterData.name} (母音)`;
            displaySound = letterData.vowelInfo.sound;
            letterClass += ' vowel-form';
        }

        elements.currentLetter.textContent = displayLetter;
        elements.currentLetter.className = letterClass;
        elements.letterName.textContent = displayName;
        elements.letterSound.textContent = displaySound;

        // Update form button states
        updateFormButtonStates();
    }

    function updateFormButtons(letterData) {
        // Show/hide final form button
        if (letterData.hasFinalForm) {
            elements.btnFinal.classList.remove('hidden');
        } else {
            elements.btnFinal.classList.add('hidden');
        }

        // Show/hide vowel form button
        if (letterData.hasVowelUse) {
            elements.btnVowel.classList.remove('hidden');
        } else {
            elements.btnVowel.classList.add('hidden');
        }

        updateFormButtonStates();
    }

    function updateFormButtonStates() {
        // Base button is active when in base form
        elements.btnBase.classList.toggle('active', state.currentForm === 'base');

        // Final and Vowel buttons use toggle-on class when active
        elements.btnFinal.classList.remove('active', 'toggle-on');
        elements.btnVowel.classList.remove('active', 'toggle-on');

        if (state.currentForm === 'final') {
            elements.btnFinal.classList.add('toggle-on');
        }
        if (state.currentForm === 'vowel') {
            elements.btnVowel.classList.add('toggle-on');
        }

        // Add vowel-btn class for specific styling
        elements.btnVowel.classList.add('vowel-btn');

        // Update examples header based on form
        updateExamplesHeader();
    }

    function updateExamplesHeader() {
        if (!elements.examplesHeader) return;

        // Remove all form classes
        elements.examplesHeader.classList.remove('final-header', 'vowel-header');

        // Update text and class based on current form
        switch (state.currentForm) {
            case 'final':
                elements.examplesHeader.textContent = '字尾形例字 Final Form Examples';
                elements.examplesHeader.classList.add('final-header');
                break;
            case 'vowel':
                elements.examplesHeader.textContent = '母音用法例字 Vowel Use Examples';
                elements.examplesHeader.classList.add('vowel-header');
                break;
            default:
                elements.examplesHeader.textContent = '例字 Examples';
        }
    }

    // =====================
    // Examples Rendering
    // =====================
    function renderExamples(letterData) {
        elements.exampleList.innerHTML = '';

        // Select appropriate examples based on current form
        let examples = letterData.examples; // Default: base form examples

        if (state.currentForm === 'final' && letterData.hasFinalForm && letterData.finalExamples) {
            examples = letterData.finalExamples;
        } else if (state.currentForm === 'vowel' && letterData.hasVowelUse && letterData.vowelExamples) {
            examples = letterData.vowelExamples;
        }

        examples.forEach(example => {
            const item = document.createElement('div');
            item.className = 'example-item';

            // Highlight target letter in the word
            const highlightedWord = highlightTargetLetter(example.word, example.target);

            // Build note display if present (for vowel examples)
            const noteHtml = example.note
                ? `<div class="example-note">${example.note}</div>`
                : '';

            item.innerHTML = `
                <div class="example-word">${highlightedWord}</div>
                <div class="example-meta">
                    <span class="strong-num">${example.strong}</span>
                    <span class="transliteration">${example.translit}</span>
                </div>
                <div class="example-translations">
                    <span class="zh">${example.zh}</span>
                    <span class="separator">|</span>
                    <span class="en">${example.en}</span>
                </div>
                ${noteHtml}
            `;

            elements.exampleList.appendChild(item);
        });
    }

    function highlightTargetLetter(word, target) {
        // Escape special regex characters
        const escapedTarget = target.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

        // Create regex that matches the target letter (with possible nikkud)
        const regex = new RegExp(`(${escapedTarget})`, 'g');

        return word.replace(regex, '<span class="target-letter">$1</span>');
    }

    // =====================
    // Print View
    // =====================
    function renderPrintView() {
        const letterData = hebrewLetters[state.currentLetterIndex];
        let displayLetter = letterData.letter;
        let displayName = letterData.name;

        if (state.currentForm === 'final' && letterData.hasFinalForm) {
            displayLetter = letterData.finalForm.letter;
            displayName = letterData.finalForm.name;
        } else if (state.currentForm === 'vowel' && letterData.hasVowelUse) {
            displayLetter = letterData.vowelInfo.letter;
            displayName = `${letterData.name} (Vowel)`;
        }

        elements.printLetter.textContent = displayLetter;
        elements.printName.textContent = displayName;
    }

    // =====================
    // Stroke Animation
    // =====================
    function playStrokeAnimation() {
        if (state.isAnimating) return;

        const letterData = hebrewLetters[state.currentLetterIndex];
        let targetLetter = letterData.letter;

        if (state.currentForm === 'final' && letterData.hasFinalForm) {
            targetLetter = letterData.finalForm.letter;
        }

        const strokeData = getStrokePaths(targetLetter);
        if (!strokeData) {
            console.log('No stroke data for:', targetLetter);
            return;
        }

        state.isAnimating = true;
        elements.strokeArea.classList.add('active');
        elements.strokeSvg.innerHTML = '';

        // Draw guide paths (light gray) with stroke numbers
        strokeData.strokes.forEach((stroke, idx) => {
            const guidePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            guidePath.setAttribute('d', stroke.path);
            guidePath.setAttribute('class', 'stroke-path-guide');
            elements.strokeSvg.appendChild(guidePath);

            // Add stroke number at the start of each path
            const startPoint = getPathStartPoint(stroke.path);
            if (startPoint) {
                const numText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                numText.setAttribute('x', startPoint.x + 8);
                numText.setAttribute('y', startPoint.y - 5);
                numText.setAttribute('class', 'stroke-number');
                numText.textContent = (idx + 1).toString();
                elements.strokeSvg.appendChild(numText);
            }
        });

        // Animate strokes sequentially
        animateStrokes(strokeData.strokes, 0);
    }

    /**
     * Extract start point from SVG path data
     */
    function getPathStartPoint(pathData) {
        const match = pathData.match(/M\s*([0-9.]+)\s+([0-9.]+)/);
        if (match) {
            return { x: parseFloat(match[1]), y: parseFloat(match[2]) };
        }
        return null;
    }

    function animateStrokes(strokes, index) {
        if (index >= strokes.length) {
            state.isAnimating = false;
            return;
        }

        const stroke = strokes[index];
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', stroke.path);
        path.setAttribute('class', 'stroke-path');

        // Calculate path length for animation
        elements.strokeSvg.appendChild(path);
        const length = path.getTotalLength();

        // Set up dash animation
        path.style.strokeDasharray = length;
        path.style.strokeDashoffset = length;

        // Create pen tip indicator
        const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        dot.setAttribute('r', '6');
        dot.setAttribute('class', 'stroke-dot');
        elements.strokeSvg.appendChild(dot);

        // Animate
        const duration = 800; // ms
        const startTime = performance.now();

        function animate(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Update path
            path.style.strokeDashoffset = length * (1 - progress);

            // Update dot position
            const point = path.getPointAtLength(length * progress);
            dot.setAttribute('cx', point.x);
            dot.setAttribute('cy', point.y);

            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                // Remove dot after animation
                setTimeout(() => {
                    dot.remove();
                    // Next stroke
                    setTimeout(() => {
                        animateStrokes(strokes, index + 1);
                    }, 200);
                }, 100);
            }
        }

        requestAnimationFrame(animate);
    }

    // =====================
    // Audio Playback (Natural Voice)
    // =====================

    // Cache for available voices
    let cachedVoices = [];
    let hebrewVoice = null;
    let naturalEnglishVoice = null;

    /**
     * Initialize voices when available
     * Prioritizes natural/premium voices over machine voices
     */
    function initVoices() {
        cachedVoices = speechSynthesis.getVoices();

        // Find best Hebrew voice (natural/premium preferred)
        const hebrewVoices = cachedVoices.filter(v =>
            v.lang.startsWith('he') || v.lang.startsWith('iw')
        );
        // Prefer natural/premium voices (usually contain 'Natural', 'Premium', 'Enhanced', or don't have 'Compact')
        hebrewVoice = hebrewVoices.find(v =>
            v.name.includes('Natural') || v.name.includes('Premium') ||
            v.name.includes('Enhanced') || v.name.includes('Wavenet') ||
            v.name.includes('Neural')
        ) || hebrewVoices.find(v => !v.name.includes('Compact')) || hebrewVoices[0];

        // Find best English voice for letter names (natural preferred)
        const englishVoices = cachedVoices.filter(v =>
            v.lang.startsWith('en')
        );
        naturalEnglishVoice = englishVoices.find(v =>
            (v.name.includes('Natural') || v.name.includes('Premium') ||
             v.name.includes('Enhanced') || v.name.includes('Samantha') ||
             v.name.includes('Karen') || v.name.includes('Daniel') ||
             v.name.includes('Wavenet') || v.name.includes('Neural')) &&
            !v.name.includes('Compact')
        ) || englishVoices.find(v => !v.name.includes('Compact')) || englishVoices[0];

        if (hebrewVoice) {
            console.log('Hebrew voice:', hebrewVoice.name);
        }
        if (naturalEnglishVoice) {
            console.log('English voice:', naturalEnglishVoice.name);
        }
    }

    // Initialize voices on load and when voices change
    if ('speechSynthesis' in window) {
        // Voices may not be immediately available
        if (speechSynthesis.getVoices().length > 0) {
            initVoices();
        }
        speechSynthesis.onvoiceschanged = initVoices;
    }

    function playAudio() {
        const letterData = hebrewLetters[state.currentLetterIndex];

        if (!('speechSynthesis' in window)) {
            console.log('Speech synthesis not supported');
            alert(`發音: ${letterData.name}`);
            return;
        }

        // Cancel any ongoing speech
        speechSynthesis.cancel();

        // Speak Hebrew letter first (if Hebrew voice available)
        const hebrewLetter = state.currentForm === 'final' && letterData.hasFinalForm
            ? letterData.finalForm.letter
            : letterData.letter;

        if (hebrewVoice) {
            const hebrewUtterance = new SpeechSynthesisUtterance(hebrewLetter);
            hebrewUtterance.voice = hebrewVoice;
            hebrewUtterance.lang = 'he-IL';
            hebrewUtterance.rate = 0.7;
            hebrewUtterance.pitch = 1.0;

            // After Hebrew pronunciation, speak the English name if romanization is enabled
            hebrewUtterance.onend = function() {
                if (state.romanization) {
                    speakEnglishName(letterData);
                }
            };

            speechSynthesis.speak(hebrewUtterance);
        } else if (state.romanization) {
            // Fallback: just speak English name (only if romanization enabled)
            speakEnglishName(letterData);
        }
    }

    function speakEnglishName(letterData) {
        let textToSpeak = letterData.name;

        if (state.currentForm === 'vowel' && letterData.hasVowelUse) {
            textToSpeak = letterData.name + ', as vowel';
        } else if (state.currentForm === 'final' && letterData.hasFinalForm) {
            textToSpeak = letterData.finalForm.name;
        }

        const englishUtterance = new SpeechSynthesisUtterance(textToSpeak);
        if (naturalEnglishVoice) {
            englishUtterance.voice = naturalEnglishVoice;
        }
        englishUtterance.lang = 'en-US';
        englishUtterance.rate = 0.85;
        englishUtterance.pitch = 1.0;
        speechSynthesis.speak(englishUtterance);
    }

    // =====================
    // Navigation
    // =====================
    function goToPrevLetter() {
        if (state.currentLetterIndex > 0) {
            state.currentLetterIndex--;
            state.currentForm = 'base';
            renderCard();
        }
    }

    function goToNextLetter() {
        if (state.currentLetterIndex < hebrewLetters.length - 1) {
            state.currentLetterIndex++;
            state.currentForm = 'base';
            renderCard();
        }
    }

    function goToOverview() {
        showPage('overview');
    }

    function togglePrintMode() {
        if (state.currentPage === 'print') {
            showPage('card');
        } else if (state.currentPage === 'card') {
            showPage('print');
        }
    }

    // =====================
    // Form Switching (Toggle Behavior)
    // =====================
    function switchToBase() {
        const letterData = hebrewLetters[state.currentLetterIndex];
        state.currentForm = 'base';
        updateLetterDisplay();
        renderExamples(letterData); // Re-render examples for base form
    }

    /**
     * Toggle Final form: if currently in final form, go back to base; otherwise switch to final
     */
    function toggleFinal() {
        const letterData = hebrewLetters[state.currentLetterIndex];
        if (!letterData.hasFinalForm) return;

        if (state.currentForm === 'final') {
            // Toggle OFF - back to base
            state.currentForm = 'base';
        } else {
            // Toggle ON - switch to final
            state.currentForm = 'final';
        }
        updateLetterDisplay();
        renderExamples(letterData);
    }

    /**
     * Toggle Vowel form: if currently in vowel form, go back to base; otherwise switch to vowel
     */
    function toggleVowel() {
        const letterData = hebrewLetters[state.currentLetterIndex];
        if (!letterData.hasVowelUse) return;

        if (state.currentForm === 'vowel') {
            // Toggle OFF - back to base
            state.currentForm = 'base';
        } else {
            // Toggle ON - switch to vowel
            state.currentForm = 'vowel';
        }
        updateLetterDisplay();
        renderExamples(letterData);
    }

    // Legacy functions for direct switching (used by base button)
    function switchToFinal() {
        toggleFinal();
    }

    function switchToVowel() {
        toggleVowel();
    }

    // =====================
    // Event Binding
    // =====================
    function bindEvents() {
        // Navigation buttons
        elements.btnBack.addEventListener('click', goToOverview);
        elements.btnPrev.addEventListener('click', goToPrevLetter);
        elements.btnNext.addEventListener('click', goToNextLetter);
        elements.btnPrint.addEventListener('click', togglePrintMode);

        // Form buttons
        elements.btnBase.addEventListener('click', switchToBase);
        elements.btnFinal.addEventListener('click', switchToFinal);
        elements.btnVowel.addEventListener('click', switchToVowel);

        // Control buttons
        elements.btnStroke.addEventListener('click', playStrokeAnimation);
        elements.btnAudio.addEventListener('click', playAudio);

        // Auto-stroke toggle
        if (elements.autoStrokeToggle) {
            elements.autoStrokeToggle.addEventListener('change', function() {
                state.autoStroke = this.checked;
                // Save preference to localStorage
                localStorage.setItem('hebrewCards_autoStroke', state.autoStroke);
            });
        }

        // Auto-audio toggle
        if (elements.autoAudioToggle) {
            elements.autoAudioToggle.addEventListener('change', function() {
                state.autoAudio = this.checked;
                // Save preference to localStorage
                localStorage.setItem('hebrewCards_autoAudio', state.autoAudio);
            });
        }

        // Romanization toggle
        if (elements.romanizationToggle) {
            elements.romanizationToggle.addEventListener('change', function() {
                state.romanization = this.checked;
                // Save preference to localStorage
                localStorage.setItem('hebrewCards_romanization', state.romanization);
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', handleKeydown);
    }

    function handleKeydown(e) {
        // Ignore if in input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        const key = e.key.toLowerCase();

        // Global shortcuts
        if (key === 'escape') {
            if (state.currentPage === 'print') {
                showPage('card');
            } else if (state.currentPage === 'card') {
                showPage('overview');
            }
            return;
        }

        // Page-specific shortcuts
        switch (state.currentPage) {
            case 'overview':
                // Number keys 1-9 and 0 for quick access
                if (key >= '1' && key <= '9') {
                    const index = parseInt(key) - 1;
                    if (index < hebrewLetters.length) {
                        state.currentLetterIndex = index;
                        showPage('card');
                    }
                }
                break;

            case 'card':
                switch (key) {
                    case 'arrowleft':
                        e.preventDefault();
                        goToPrevLetter();
                        break;
                    case 'arrowright':
                        e.preventDefault();
                        goToNextLetter();
                        break;
                    case 'arrowup':
                        e.preventDefault();
                        goToOverview();
                        break;
                    case 'p':
                        togglePrintMode();
                        break;
                    case ' ':
                        e.preventDefault();
                        switchToBase();
                        break;
                    case 'f':
                        switchToFinal();
                        break;
                    case 'v':
                        switchToVowel();
                        break;
                    case 's':
                        playStrokeAnimation();
                        break;
                    case 'a':
                        playAudio();
                        break;
                }
                break;

            case 'print':
                if (key === 'p' || key === 'escape') {
                    showPage('card');
                }
                break;
        }
    }

    // =====================
    // Start App
    // =====================
    document.addEventListener('DOMContentLoaded', init);

})();
