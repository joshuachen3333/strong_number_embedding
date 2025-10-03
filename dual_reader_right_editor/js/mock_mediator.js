/**
 * Debug function to display logs on webpage
 */
function debugLog(message) {
    console.log(message);
    const debugContent = document.getElementById('debug-content');
    if (debugContent) {
        const timestamp = new Date().toLocaleTimeString();
        debugContent.innerHTML += `<div>[${timestamp}] ${message}</div>`;
        debugContent.scrollTop = debugContent.scrollHeight;
    }
}

/**
 * Mediator for communication between reader components and bible.fhl.net API.
 * This object will facilitate the observer pattern and handle API calls.
 */
const MockMediator = {
    events: {},
    _currentSynchedVerse: { book: '', chapter: 1, verse: 1 },
    _rightReaderUpdateFn: null,
    _leftReaderUpdateFn: null,
    _bookDataCache: {},
    _mainReader: 'left', // Track which reader is currently main ('left' or 'right')
    _lastInteraction: null, // Track last interaction for debugging

    /**
     * Subscribes a callback function to an event.
     * @param {string} eventName - The name of the event to subscribe to.
     * @param {function} callback - The function to call when the event is published.
     */
    subscribe: function(eventName, callback) {
        if (!this.events[eventName]) {
            this.events[eventName] = [];
        }
        this.events[eventName].push(callback);
        console.log(`MockMediator: Subscribed to ${eventName}`);
    },

    /**
     * Publishes an event, calling all subscribed callbacks with the given data.
     * @param {string} eventName - The name of the event to publish.
     * @param {object} data - The data to pass to the event callbacks.
     */
    publish: function(eventName, data) {
        if (this.events[eventName]) {
            console.log(`MockMediator: Publishing ${eventName} with data:`, data);
            this.events[eventName].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in callback for event ${eventName}:`, error);
                }
            });
        } else {
            console.log(`MockMediator: No subscribers for event ${eventName}`);
        }
    },

    /**
     * Fetches chapter data from bible.fhl.net API
     * @param {string} book - Chinese book abbreviation
     * @param {number} chapter - Chapter number
     * @param {string} version - Version code
     * @param {number} strong - Strong's numbers flag (1 or 0)
     * @returns {Promise<Object>} API response
     */
    fetchChapter: async function(book, chapter, version, strong) {
        const cacheKey = `${book}-${chapter}-${version}-${strong}`;
        debugLog(`Cache key: ${cacheKey}`);
        debugLog(`Cache keys available: ${Object.keys(this._bookDataCache).join(', ')}`);
        
        if (this._bookDataCache[cacheKey]) {
            debugLog(`Returning cached data for ${cacheKey}`);
            return this._bookDataCache[cacheKey];
        }
        
        debugLog(`No cache found, making fresh API call for ${cacheKey}`);

        try {
            // Use the EXACT same format as the working URL you provided
            const apiUrl = `https://bible.fhl.net/json/qb.php?version=${version}&chineses=${encodeURIComponent(book)}&chap=${chapter}&strong=${strong}`;
            debugLog(`✅ Using exact working API format: ${apiUrl}`);
            
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Parse JSON from API
            const data = await response.json();
            debugLog(`📊 JSON Response received for ${version} with ${data.record ? data.record.length : 0} verses`);
            
            // Check if API returned Chinese text when English was requested
            let needsEnglishFallback = false;
            if ((version.toLowerCase() === 'kjv' || version.toLowerCase() === 'esv') && data.record && data.record.length > 0) {
                const sampleText = data.record[0].bible_text || '';
                if (/[\u4e00-\u9fff]/.test(sampleText)) {
                    needsEnglishFallback = true;
                    debugLog(`⚠️ API returned Chinese text for ${version.toUpperCase()} - will provide English fallback`);
                } else {
                    debugLog(`✅ API returned non-Chinese text for ${version.toUpperCase()}`);
                }
            }
            
            // Debug: Log the structure of the first record
            if (data.record && data.record.length > 0) {
                const record = data.record[0];
                debugLog(`First record fields: ${Object.keys(record).join(', ')}`);
                debugLog(`Text sample (bible_text): ${record.bible_text?.substring(0, 100)}...`);
                
                // Check all text fields for Strong's numbers in the actual format returned by FHL
                const textFields = ['bible_text', 'text', 'content', 'verse_text', 'strong_text'];
                let foundStrongsInField = null;
                
                for (const field of textFields) {
                    if (record[field]) {
                        const text = record[field];
                        // Look for the actual FHL format: <WH07225>, <WH0430>, etc.
                        const strongsMatches1 = text.match(/<W[HG]\d+>/g);     // <WH123> - FHL format
                        const strongsMatches2 = text.match(/<[HG]\d+>/g);      // <H123> - alternative format
                        const strongsMatches3 = text.match(/\{<W[HG]\d+>\}/g); // {<WH123>} - wrapped format
                        const strongsMatches4 = text.match(/\{[HG]\d+\}/g);    // {H123} - simple format
                        
                        if (strongsMatches1 || strongsMatches2 || strongsMatches3 || strongsMatches4) {
                            const matches = strongsMatches1 || strongsMatches2 || strongsMatches3 || strongsMatches4;
                            debugLog(`✅ Strong's found in field '${field}': ${matches.slice(0, 3).join(', ')} (${matches.length} total)`);
                            foundStrongsInField = field;
                            break;
                        }
                    }
                }
                
                if (!foundStrongsInField && strong === 1) {
                    debugLog(`❌ JSON API doesn't include Strong's numbers (strong parameter: ${strong})`);
                    debugLog(`💡 Strong's numbers ARE available in web interface: https://bible.fhl.net/new/read.php?chineses=${encodeURIComponent(book)}&chap=${chapter}&VERSION=${version.toUpperCase()}&strongflag=1&TABFLAG=1`);
                    debugLog(`Available fields with content: ${textFields.filter(f => record[f]).map(f => `${f}: "${record[f]?.substring(0, 50)}..."`).join(', ')}`);
                }
            }
            
            // Transform the data to match expected format
            const transformedData = {
                status: "success",
                request: { book, chapter, version, strong },
                data: {
                    book_engs: book, // Keep Chinese for consistency
                    book_chineses: book,
                    chapter_num: chapter,
                    version_code: version,
                    version_name: `FHL ${version.toUpperCase()}`,
                    verses: data.record ? data.record.map(record => {
                        let verseText = record.bible_text || record.text || '';
                        
                        // If English version requested but API returned Chinese, provide meaningful fallback
                        if (needsEnglishFallback) {
                            verseText = this.getEnglishFallbackText(book, chapter, record.sec, version.toUpperCase());
                        }
                        
                        // If Strong's numbers were requested but not found in JSON, log to console instead
                        if (strong === 1 && !verseText.match(/[\{<\(][HG]\d+[\}>)\]]/) && record.sec === 1) {
                            console.log('📝 Note: Strong\'s numbers not available via JSON API for this version');
                        }
                        
                        return {
                            verse_num: record.sec,
                            text: verseText
                        };
                    }) : []
                }
            };
            
            // Cache the result
            this._bookDataCache[cacheKey] = transformedData;
            debugLog(`Cached ${transformedData.data.verses.length} verses for ${cacheKey}`);
            debugLog(`Sample verse text: ${transformedData.data.verses[0]?.text?.substring(0, 50)}...`);
            
            return transformedData;
            
        } catch (error) {
            console.error(`MockMediator: Error fetching chapter ${book} ${chapter}:`, error);
            return {
                status: "error",
                message: `Failed to fetch chapter: ${error.message}`,
                request: { book, chapter, version, strong }
            };
        }
    },

    /**
     * Updates synchronization position and notifies second reader
     * @param {Object} payload - Contains book, chapter, verse, mainReaderVersion
     */
    syncPosition: function(payload) {
        this._currentSynchedVerse = {
            book: payload.book,
            chapter: payload.chapter,
            verse: payload.verse
        };
        
        console.log(`MockMediator: Syncing to ${payload.book} ${payload.chapter}:${payload.verse} from ${this._mainReader} reader`);
        
        // Call the appropriate follower reader's update function based on which reader is main
        if (this._mainReader === 'left' && this._rightReaderUpdateFn) {
            // Left is main, update right (follower)
            this._rightReaderUpdateFn(payload.book, payload.chapter, payload.verse);
        } else if (this._mainReader === 'right' && this._leftReaderUpdateFn) {
            // Right is main, update left (follower)
            this._leftReaderUpdateFn(payload.book, payload.chapter, payload.verse);
        }
        
        return { status: "success", message: "Position synchronized" };
    },

    /**
     * Registers the right reader's update callback
     * @param {Function} callback - Update function from right reader
     */
    registerRightReaderUpdateCallback: function(callback) {
        this._rightReaderUpdateFn = callback;
        console.log('MockMediator: Right reader update callback registered');
    },

    /**
     * Registers the left reader's update callback
     * @param {Function} callback - Update function from left reader
     */
    registerLeftReaderUpdateCallback: function(callback) {
        this._leftReaderUpdateFn = callback;
        console.log('MockMediator: Left reader update callback registered');
    },

    /**
     * Sets which reader is currently the main (last interacted with)
     * @param {string} readerType - 'left' or 'right'
     * @param {string} interaction - Description of the interaction
     */
    setMainReader: function(readerType, interaction) {
        const previousMain = this._mainReader;
        this._mainReader = readerType;
        this._lastInteraction = interaction;
        
        debugLog(`🎯 Main reader changed: ${previousMain} → ${readerType} (${interaction})`);
        console.log(`MockMediator: Main reader is now ${readerType} due to: ${interaction}`);
        
        // Notify both readers about the role change
        this.publish('mainReaderChanged', {
            newMain: readerType,
            newFollower: readerType === 'left' ? 'right' : 'left',
            interaction: interaction
        });
    },

    /**
     * Gets the current main reader
     * @returns {string} 'left' or 'right'
     */
    getMainReader: function() {
        return this._mainReader;
    },

    /**
     * Gets the current follower reader
     * @returns {string} 'left' or 'right'
     */
    getFollowerReader: function() {
        return this._mainReader === 'left' ? 'right' : 'left';
    },

    /**
     * Parses HTML from bible.fhl.net web interface to extract verse data with Strong's numbers
     * @param {string} html - HTML content from web interface
     * @returns {Object} Data object in same format as JSON API
     */
    parseWebInterfaceHTML: function(html) {
        debugLog(`🔍 Parsing HTML content (length: ${html.length})`);
        
        try {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Look for verse content - bible.fhl.net uses different patterns
            const verses = [];
            
            // Try different selectors that might contain verses
            const possibleSelectors = [
                '.BibleText', '.bible_text', '.verse', '.v',
                'td[bgcolor="#FFFFCC"]', 'td[bgcolor="#ffffcc"]',
                'tr td:nth-child(2)', // Sometimes verses are in second column
                '.content td', 'td'
            ];
            
            let versesFound = false;
            for (const selector of possibleSelectors) {
                const elements = doc.querySelectorAll(selector);
                if (elements.length > 0) {
                    debugLog(`📍 Found ${elements.length} elements with selector: ${selector}`);
                    
                    elements.forEach((element, index) => {
                        const text = element.textContent || element.innerText || '';
                        if (text.trim() && text.length > 5) { // Filter out empty or very short content
                            // Try to extract verse number from text or structure
                            const verseMatch = text.match(/^(\d+)[:\s]/);
                            const verseNum = verseMatch ? parseInt(verseMatch[1]) : index + 1;
                            
                            verses.push({
                                sec: verseNum,
                                bible_text: text.trim()
                            });
                            
                            // Log sample of what we found
                            if (index < 3) {
                                debugLog(`📝 Sample verse ${verseNum}: ${text.substring(0, 80)}...`);
                            }
                        }
                    });
                    
                    if (verses.length > 0) {
                        versesFound = true;
                        debugLog(`✅ Successfully parsed ${verses.length} verses using selector: ${selector}`);
                        break;
                    }
                }
            }
            
            if (!versesFound) {
                debugLog(`⚠️ No verses found with any selector. HTML preview: ${html.substring(0, 500)}...`);
                // Fallback: try to extract any text that looks like verses
                const allText = doc.body ? doc.body.textContent : html;
                const lines = allText.split('\n').filter(line => line.trim().length > 10);
                lines.forEach((line, index) => {
                    if (index < 50 && /^\d+/.test(line.trim())) { // Lines starting with numbers
                        verses.push({
                            sec: index + 1,
                            bible_text: line.trim()
                        });
                    }
                });
                debugLog(`🔄 Fallback parsing found ${verses.length} potential verses`);
            }
            
            return {
                record: verses
            };
            
        } catch (error) {
            debugLog(`❌ HTML parsing error: ${error.message}`);
            return { record: [] };
        }
    },

    /**
     * Provides English fallback text when API doesn't return proper English versions
     * @param {string} book - Chinese book abbreviation
     * @param {number} chapter - Chapter number  
     * @param {number} verse - Verse number
     * @param {string} version - Version name (KJV, ESV, etc.)
     * @returns {string} Fallback English text
     */
    getEnglishFallbackText: function(book, chapter, verse, version) {
        // Basic fallback message explaining the limitation
        const bookMap = {
            '創': 'Genesis', '出': 'Exodus', '利': 'Leviticus', '民': 'Numbers', '申': 'Deuteronomy',
            '書': 'Joshua', '士': 'Judges', '得': 'Ruth', '撒上': '1 Samuel', '撒下': '2 Samuel',
            '王上': '1 Kings', '王下': '2 Kings', '代上': '1 Chronicles', '代下': '2 Chronicles',
            '拉': 'Ezra', '尼': 'Nehemiah', '斯': 'Esther', '伯': 'Job', '詩': 'Psalms',
            '箴': 'Proverbs', '傳': 'Ecclesiastes', '歌': 'Song of Solomon', '賽': 'Isaiah',
            '耶': 'Jeremiah', '哀': 'Lamentations', '結': 'Ezekiel', '但': 'Daniel',
            '何': 'Hosea', '珥': 'Joel', '摩': 'Amos', '俄': 'Obadiah', '拿': 'Jonah',
            '彌': 'Micah', '鴻': 'Nahum', '哈': 'Habakkuk', '番': 'Zephaniah', '該': 'Haggai',
            '亞': 'Zechariah', '瑪': 'Malachi', '太': 'Matthew', '可': 'Mark', '路': 'Luke',
            '約': 'John', '徒': 'Acts', '羅': 'Romans', '林前': '1 Corinthians', '林後': '2 Corinthians',
            '加': 'Galatians', '弗': 'Ephesians', '腓': 'Philippians', '西': 'Colossians',
            '帖前': '1 Thessalonians', '帖後': '2 Thessalonians', '提前': '1 Timothy', '提後': '2 Timothy',
            '多': 'Titus', '門': 'Philemon', '來': 'Hebrews', '雅': 'James', '彼前': '1 Peter',
            '彼後': '2 Peter', '約一': '1 John', '約二': '2 John', '約三': '3 John', '猶': 'Jude', '啟': 'Revelation'
        };
        
        const englishBook = bookMap[book] || book;
        return `📖 ${version} ${englishBook} ${chapter}:${verse} - English text not available from bible.fhl.net JSON API. The API only returns Chinese text regardless of version parameter. Please use the web interface URL shown below for actual ${version} content.`;
    },

    /**
     * Clears the cache for debugging version switching issues
     */
    clearCache: function() {
        debugLog('🗑️ Clearing cache');
        this._bookDataCache = {};
    },

    /**
     * Fetches Strong's number definition (placeholder for future implementation)
     * @param {string} strongId - Strong's number (e.g., "G1722")
     * @returns {Promise<Object>} Definition data
     */
    fetchStrongDefinition: async function(strongId) {
        // Placeholder implementation
        return {
            status: "success",
            data: {
                strong_number: strongId,
                original_word: "placeholder",
                definition_zh: "定義待實現",
                definition_en: "Definition not yet implemented"
            }
        };
    },

    /**
     * Gets the current synchronized verse position
     * @returns {Object} Current verse position with book, chapter, verse
     */
    getCurrentSyncPosition: function() {
        return { ...this._currentSynchedVerse };
    }
};

// Example of how components might use the mediator:
// To publish an event:
// MockMediator.publish('mainReaderChapterChanged', { book: 'Genesis', chapter: 1 });

// To subscribe to an event:
// MockMediator.subscribe('mainReaderChapterChanged', function(data) {
//     console.log('Second reader received chapter change:', data);
//     // Logic to update the second reader
// });

// MockMediator.subscribe('strongsNumberClicked', function(data) {
//    console.log('Main reader received strongs number click:', data);
//    // Logic to display Strong's number definition
// });
