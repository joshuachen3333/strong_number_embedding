/**
 * Hebrew Alphabet Data
 * 22 letters with pronunciation, forms, and examples
 */

const hebrewLetters = [
    {
        id: 1,
        letter: "א",
        name: "Aleph",
        nameHebrew: "אָלֶף",
        sound: "silent / glottal stop",
        hasVowelUse: true,
        vowelInfo: {
            letter: "א",
            sound: "ā (long a)",
            description: "母音字母 (mater lectionis)"
        },
        examples: [
            { word: "אֱלֹהִים", target: "א", strong: "H430", en: "God", zh: "神", translit: "Elohim" },
            { word: "אָדָם", target: "א", strong: "H120", en: "man, Adam", zh: "人，亞當", translit: "adam" },
            { word: "אֶרֶץ", target: "א", strong: "H776", en: "earth, land", zh: "地，土地", translit: "eretz" },
            { word: "אוֹר", target: "א", strong: "H216", en: "light", zh: "光", translit: "or" },
            { word: "אָב", target: "א", strong: "H1", en: "father", zh: "父親", translit: "av" }
        ],
        // Examples where א acts as vowel carrier (mater lectionis)
        vowelExamples: [
            { word: "רֹאשׁ", target: "א", strong: "H7218", en: "head", zh: "頭", translit: "rosh", note: "א carries ō sound" },
            { word: "מָצָא", target: "א", strong: "H4672", en: "to find", zh: "找到", translit: "matsa", note: "final א marks ā" },
            { word: "קָרָא", target: "א", strong: "H7121", en: "to call", zh: "呼叫", translit: "qara", note: "final א marks ā" },
            { word: "בָּרָא", target: "א", strong: "H1254", en: "created", zh: "創造", translit: "bara", note: "final א marks ā" },
            { word: "נָשָׂא", target: "א", strong: "H5375", en: "to lift", zh: "舉起", translit: "nasa", note: "final א marks ā" }
        ]
    },
    {
        id: 2,
        letter: "ב",
        name: "Bet",
        nameHebrew: "בֵּית",
        sound: "b (with dagesh) / v (without)",
        examples: [
            { word: "בְּרֵאשִׁית", target: "ב", strong: "H7225", en: "in the beginning", zh: "起初", translit: "bereshit" },
            { word: "בָּרָא", target: "ב", strong: "H1254", en: "created", zh: "創造", translit: "bara" },
            { word: "בֵּן", target: "ב", strong: "H1121", en: "son", zh: "兒子", translit: "ben" },
            { word: "בַּיִת", target: "ב", strong: "H1004", en: "house", zh: "房子", translit: "bayit" },
            { word: "בְּרִית", target: "ב", strong: "H1285", en: "covenant", zh: "約", translit: "berit" }
        ]
    },
    {
        id: 3,
        letter: "ג",
        name: "Gimel",
        nameHebrew: "גִּימֶל",
        sound: "g (as in 'go')",
        examples: [
            { word: "גָּדוֹל", target: "ג", strong: "H1419", en: "great, big", zh: "大的", translit: "gadol" },
            { word: "גּוֹי", target: "ג", strong: "H1471", en: "nation", zh: "國家", translit: "goy" },
            { word: "גַּן", target: "ג", strong: "H1588", en: "garden", zh: "園子", translit: "gan" },
            { word: "גִּבּוֹר", target: "ג", strong: "H1368", en: "mighty, hero", zh: "勇士", translit: "gibbor" },
            { word: "גָּמָל", target: "ג", strong: "H1581", en: "camel", zh: "駱駝", translit: "gamal" }
        ]
    },
    {
        id: 4,
        letter: "ד",
        name: "Dalet",
        nameHebrew: "דָּלֶת",
        sound: "d",
        examples: [
            { word: "דָּבָר", target: "ד", strong: "H1697", en: "word, thing", zh: "話語，事情", translit: "davar" },
            { word: "דֶּרֶךְ", target: "ד", strong: "H1870", en: "way, road", zh: "道路", translit: "derekh" },
            { word: "דָּם", target: "ד", strong: "H1818", en: "blood", zh: "血", translit: "dam" },
            { word: "דָּוִד", target: "ד", strong: "H1732", en: "David", zh: "大衛", translit: "David" },
            { word: "דַּעַת", target: "ד", strong: "H1847", en: "knowledge", zh: "知識", translit: "da'at" }
        ]
    },
    {
        id: 5,
        letter: "ה",
        name: "He",
        nameHebrew: "הֵא",
        sound: "h",
        hasVowelUse: true,
        vowelInfo: {
            letter: "ה",
            sound: "ā, ē (at word end)",
            description: "字尾母音 (final mater lectionis)"
        },
        examples: [
            { word: "הָאָרֶץ", target: "ה", strong: "H776", en: "the earth", zh: "這地", translit: "ha'aretz" },
            { word: "הִנֵּה", target: "ה", strong: "H2009", en: "behold", zh: "看哪", translit: "hinneh" },
            { word: "הָיָה", target: "ה", strong: "H1961", en: "to be, was", zh: "是，存在", translit: "hayah" },
            { word: "הַר", target: "ה", strong: "H2022", en: "mountain", zh: "山", translit: "har" },
            { word: "הָלַךְ", target: "ה", strong: "H1980", en: "to walk, go", zh: "行走", translit: "halakh" }
        ],
        // Examples where final ה marks vowel sound
        vowelExamples: [
            { word: "תּוֹרָה", target: "ה", strong: "H8451", en: "law, Torah", zh: "律法", translit: "torah", note: "final ה marks ā" },
            { word: "שָׂרָה", target: "ה", strong: "H8283", en: "Sarah", zh: "撒拉", translit: "Sarah", note: "final ה marks ā" },
            { word: "יְהוּדָה", target: "ה", strong: "H3063", en: "Judah", zh: "猶大", translit: "Yehudah", note: "final ה marks ā" },
            { word: "מֹשֶׁה", target: "ה", strong: "H4872", en: "Moses", zh: "摩西", translit: "Mosheh", note: "final ה marks ē" },
            { word: "עֹשֶׂה", target: "ה", strong: "H6213", en: "maker, doer", zh: "做的人", translit: "oseh", note: "final ה marks ē" }
        ]
    },
    {
        id: 6,
        letter: "ו",
        name: "Vav",
        nameHebrew: "וָו",
        sound: "v / w",
        hasVowelUse: true,
        vowelInfo: {
            letter: "וֹ / וּ",
            sound: "ō (cholam) / ū (shureq)",
            description: "常用母音字母"
        },
        examples: [
            { word: "וְ", target: "ו", strong: "H9002", en: "and", zh: "和", translit: "ve-" },
            { word: "וַיֹּאמֶר", target: "ו", strong: "H559", en: "and he said", zh: "他說", translit: "vayyomer" },
            { word: "וַיְהִי", target: "ו", strong: "H1961", en: "and it was", zh: "於是有了", translit: "vayehi" },
            { word: "קוֹל", target: "ו", strong: "H6963", en: "voice", zh: "聲音", translit: "qol" },
            { word: "שָׁלוֹם", target: "ו", strong: "H7965", en: "peace", zh: "平安", translit: "shalom" }
        ],
        // Examples where ו represents vowel sounds (cholam/shureq)
        vowelExamples: [
            { word: "אוֹר", target: "וֹ", strong: "H216", en: "light", zh: "光", translit: "or", note: "וֹ = cholam (ō)" },
            { word: "טוֹב", target: "וֹ", strong: "H2896", en: "good", zh: "好的", translit: "tov", note: "וֹ = cholam (ō)" },
            { word: "קוֹל", target: "וֹ", strong: "H6963", en: "voice", zh: "聲音", translit: "qol", note: "וֹ = cholam (ō)" },
            { word: "רוּחַ", target: "וּ", strong: "H7307", en: "spirit, wind", zh: "靈，風", translit: "ruach", note: "וּ = shureq (ū)" },
            { word: "בָּרוּךְ", target: "וּ", strong: "H1288", en: "blessed", zh: "蒙福的", translit: "barukh", note: "וּ = shureq (ū)" }
        ]
    },
    {
        id: 7,
        letter: "ז",
        name: "Zayin",
        nameHebrew: "זַיִן",
        sound: "z",
        examples: [
            { word: "זָכַר", target: "ז", strong: "H2142", en: "to remember", zh: "記念", translit: "zakhar" },
            { word: "זֶרַע", target: "ז", strong: "H2233", en: "seed", zh: "種子，後裔", translit: "zera" },
            { word: "זָהָב", target: "ז", strong: "H2091", en: "gold", zh: "金子", translit: "zahav" },
            { word: "זְמַן", target: "ז", strong: "H2165", en: "time", zh: "時間", translit: "zeman" },
            { word: "זָקֵן", target: "ז", strong: "H2205", en: "old, elder", zh: "老人，長老", translit: "zaqen" }
        ]
    },
    {
        id: 8,
        letter: "ח",
        name: "Chet",
        nameHebrew: "חֵית",
        sound: "ch (guttural, like German 'Bach')",
        examples: [
            { word: "חַיִּים", target: "ח", strong: "H2416", en: "life", zh: "生命", translit: "chayyim" },
            { word: "חֶסֶד", target: "ח", strong: "H2617", en: "loving-kindness", zh: "慈愛", translit: "chesed" },
            { word: "חָכְמָה", target: "ח", strong: "H2451", en: "wisdom", zh: "智慧", translit: "chokhmah" },
            { word: "חֹשֶׁךְ", target: "ח", strong: "H2822", en: "darkness", zh: "黑暗", translit: "choshekh" },
            { word: "חָוָּה", target: "ח", strong: "H2332", en: "Eve", zh: "夏娃", translit: "Chavvah" }
        ]
    },
    {
        id: 9,
        letter: "ט",
        name: "Tet",
        nameHebrew: "טֵית",
        sound: "t (emphatic)",
        examples: [
            { word: "טוֹב", target: "ט", strong: "H2896", en: "good", zh: "好的", translit: "tov" },
            { word: "טָהוֹר", target: "ט", strong: "H2889", en: "clean, pure", zh: "潔淨的", translit: "tahor" },
            { word: "טָמֵא", target: "ט", strong: "H2931", en: "unclean", zh: "不潔淨的", translit: "tame" },
            { word: "טַל", target: "ט", strong: "H2919", en: "dew", zh: "露水", translit: "tal" },
            { word: "טֶרֶם", target: "ט", strong: "H2962", en: "before, not yet", zh: "還沒有", translit: "terem" }
        ]
    },
    {
        id: 10,
        letter: "י",
        name: "Yod",
        nameHebrew: "יוֹד",
        sound: "y",
        hasVowelUse: true,
        vowelInfo: {
            letter: "י",
            sound: "ī (long i)",
            description: "母音字母 (mater lectionis)"
        },
        examples: [
            { word: "יְהוָה", target: "י", strong: "H3068", en: "LORD (YHWH)", zh: "耶和華", translit: "YHWH" },
            { word: "יוֹם", target: "י", strong: "H3117", en: "day", zh: "日子", translit: "yom" },
            { word: "יָד", target: "י", strong: "H3027", en: "hand", zh: "手", translit: "yad" },
            { word: "יִשְׂרָאֵל", target: "י", strong: "H3478", en: "Israel", zh: "以色列", translit: "Yisrael" },
            { word: "יָרֵא", target: "י", strong: "H3372", en: "to fear", zh: "敬畏", translit: "yare" }
        ],
        // Examples where י represents long i vowel (chirik gadol)
        vowelExamples: [
            { word: "אֱלֹהִים", target: "י", strong: "H430", en: "God", zh: "神", translit: "Elohim", note: "י = chirik gadol (ī)" },
            { word: "מָשִׁיחַ", target: "י", strong: "H4899", en: "Messiah, anointed", zh: "彌賽亞", translit: "mashiach", note: "י = chirik gadol (ī)" },
            { word: "צַדִּיק", target: "י", strong: "H6662", en: "righteous", zh: "義人", translit: "tsaddiq", note: "י = chirik gadol (ī)" },
            { word: "נָבִיא", target: "י", strong: "H5030", en: "prophet", zh: "先知", translit: "navi", note: "י = chirik gadol (ī)" },
            { word: "שָׁמַיִם", target: "י", strong: "H8064", en: "heaven", zh: "天", translit: "shamayim", note: "י in dual ending" }
        ]
    },
    {
        id: 11,
        letter: "כ",
        name: "Kaf",
        nameHebrew: "כַּף",
        sound: "k (with dagesh) / kh (without)",
        hasFinalForm: true,
        finalForm: {
            letter: "ך",
            name: "Final Kaf",
            description: "字尾形"
        },
        examples: [
            { word: "כֹּל", target: "כ", strong: "H3605", en: "all, every", zh: "所有的", translit: "kol" },
            { word: "כֹּהֵן", target: "כ", strong: "H3548", en: "priest", zh: "祭司", translit: "kohen" },
            { word: "כָּבוֹד", target: "כ", strong: "H3519", en: "glory", zh: "榮耀", translit: "kavod" },
            { word: "מֶלֶךְ", target: "ך", strong: "H4428", en: "king", zh: "王", translit: "melekh" },
            { word: "דֶּרֶךְ", target: "ך", strong: "H1870", en: "way", zh: "道路", translit: "derekh" }
        ],
        // Examples showing final ך at word end
        finalExamples: [
            { word: "מֶלֶךְ", target: "ך", strong: "H4428", en: "king", zh: "王", translit: "melekh" },
            { word: "דֶּרֶךְ", target: "ך", strong: "H1870", en: "way, road", zh: "道路", translit: "derekh" },
            { word: "מַלְאָךְ", target: "ך", strong: "H4397", en: "angel, messenger", zh: "天使", translit: "malakh" },
            { word: "בָּרוּךְ", target: "ך", strong: "H1288", en: "blessed", zh: "蒙福的", translit: "barukh" },
            { word: "חֹשֶׁךְ", target: "ך", strong: "H2822", en: "darkness", zh: "黑暗", translit: "choshekh" }
        ]
    },
    {
        id: 12,
        letter: "ל",
        name: "Lamed",
        nameHebrew: "לָמֶד",
        sound: "l",
        examples: [
            { word: "לֵב", target: "ל", strong: "H3820", en: "heart", zh: "心", translit: "lev" },
            { word: "לַיְלָה", target: "ל", strong: "H3915", en: "night", zh: "夜晚", translit: "laylah" },
            { word: "לֶחֶם", target: "ל", strong: "H3899", en: "bread", zh: "餅", translit: "lechem" },
            { word: "לָשׁוֹן", target: "ל", strong: "H3956", en: "tongue", zh: "舌頭", translit: "lashon" },
            { word: "לְ", target: "ל", strong: "H9001", en: "to, for", zh: "向，為", translit: "le-" }
        ]
    },
    {
        id: 13,
        letter: "מ",
        name: "Mem",
        nameHebrew: "מֵם",
        sound: "m",
        hasFinalForm: true,
        finalForm: {
            letter: "ם",
            name: "Final Mem",
            description: "字尾形（封閉方形）"
        },
        examples: [
            { word: "מַיִם", target: "מ", strong: "H4325", en: "water", zh: "水", translit: "mayim" },
            { word: "מֶלֶךְ", target: "מ", strong: "H4428", en: "king", zh: "王", translit: "melekh" },
            { word: "מֹשֶׁה", target: "מ", strong: "H4872", en: "Moses", zh: "摩西", translit: "Mosheh" },
            { word: "שָׁמַיִם", target: "ם", strong: "H8064", en: "heaven", zh: "天", translit: "shamayim" },
            { word: "שָׁלוֹם", target: "ם", strong: "H7965", en: "peace", zh: "平安", translit: "shalom" }
        ],
        // Examples showing final ם (closed form) at word end
        finalExamples: [
            { word: "שָׁלוֹם", target: "ם", strong: "H7965", en: "peace", zh: "平安", translit: "shalom" },
            { word: "עוֹלָם", target: "ם", strong: "H5769", en: "eternity, forever", zh: "永遠", translit: "olam" },
            { word: "אָדָם", target: "ם", strong: "H120", en: "man, Adam", zh: "人", translit: "adam" },
            { word: "אַבְרָהָם", target: "ם", strong: "H85", en: "Abraham", zh: "亞伯拉罕", translit: "Avraham" },
            { word: "יְרוּשָׁלַיִם", target: "ם", strong: "H3389", en: "Jerusalem", zh: "耶路撒冷", translit: "Yerushalayim" }
        ]
    },
    {
        id: 14,
        letter: "נ",
        name: "Nun",
        nameHebrew: "נוּן",
        sound: "n",
        hasFinalForm: true,
        finalForm: {
            letter: "ן",
            name: "Final Nun",
            description: "字尾形（長尾）"
        },
        examples: [
            { word: "נֶפֶשׁ", target: "נ", strong: "H5315", en: "soul", zh: "靈魂", translit: "nefesh" },
            { word: "נָבִיא", target: "נ", strong: "H5030", en: "prophet", zh: "先知", translit: "navi" },
            { word: "נָתַן", target: "נ", strong: "H5414", en: "to give", zh: "給", translit: "natan" },
            { word: "בֵּן", target: "ן", strong: "H1121", en: "son", zh: "兒子", translit: "ben" },
            { word: "גַּן", target: "ן", strong: "H1588", en: "garden", zh: "園子", translit: "gan" }
        ],
        // Examples showing final ן (long tail) at word end
        finalExamples: [
            { word: "בֵּן", target: "ן", strong: "H1121", en: "son", zh: "兒子", translit: "ben" },
            { word: "גַּן", target: "ן", strong: "H1588", en: "garden", zh: "園子", translit: "gan" },
            { word: "אָמֵן", target: "ן", strong: "H543", en: "amen, truly", zh: "阿們", translit: "amen" },
            { word: "כֹּהֵן", target: "ן", strong: "H3548", en: "priest", zh: "祭司", translit: "kohen" },
            { word: "אָדוֹן", target: "ן", strong: "H113", en: "lord, master", zh: "主人", translit: "adon" }
        ]
    },
    {
        id: 15,
        letter: "ס",
        name: "Samekh",
        nameHebrew: "סָמֶךְ",
        sound: "s",
        examples: [
            { word: "סֵפֶר", target: "ס", strong: "H5612", en: "book, scroll", zh: "書卷", translit: "sefer" },
            { word: "סוּס", target: "ס", strong: "H5483", en: "horse", zh: "馬", translit: "sus" },
            { word: "סֶלָה", target: "ס", strong: "H5542", en: "selah", zh: "細拉", translit: "selah" },
            { word: "סָבִיב", target: "ס", strong: "H5439", en: "around", zh: "周圍", translit: "saviv" },
            { word: "סָגַר", target: "ס", strong: "H5462", en: "to close", zh: "關閉", translit: "sagar" }
        ]
    },
    {
        id: 16,
        letter: "ע",
        name: "Ayin",
        nameHebrew: "עַיִן",
        sound: "silent / guttural (voiced pharyngeal)",
        examples: [
            { word: "עַל", target: "ע", strong: "H5921", en: "on, upon", zh: "在…上", translit: "al" },
            { word: "עַיִן", target: "ע", strong: "H5869", en: "eye", zh: "眼睛", translit: "ayin" },
            { word: "עוֹלָם", target: "ע", strong: "H5769", en: "eternity", zh: "永遠", translit: "olam" },
            { word: "עֶבֶד", target: "ע", strong: "H5650", en: "servant", zh: "僕人", translit: "eved" },
            { word: "עִיר", target: "ע", strong: "H5892", en: "city", zh: "城市", translit: "ir" }
        ]
    },
    {
        id: 17,
        letter: "פ",
        name: "Pe",
        nameHebrew: "פֵּא",
        sound: "p (with dagesh) / f (without)",
        hasFinalForm: true,
        finalForm: {
            letter: "ף",
            name: "Final Pe",
            description: "字尾形（下延）"
        },
        examples: [
            { word: "פָּנִים", target: "פ", strong: "H6440", en: "face", zh: "臉", translit: "panim" },
            { word: "פֶּה", target: "פ", strong: "H6310", en: "mouth", zh: "口", translit: "peh" },
            { word: "פָּרָה", target: "פ", strong: "H6509", en: "to be fruitful", zh: "繁衍", translit: "parah" },
            { word: "כֶּסֶף", target: "ף", strong: "H3701", en: "silver", zh: "銀子", translit: "kesef" },
            { word: "אַף", target: "ף", strong: "H639", en: "nose, anger", zh: "鼻子，怒氣", translit: "af" }
        ],
        // Examples showing final ף (descending form) at word end
        finalExamples: [
            { word: "כֶּסֶף", target: "ף", strong: "H3701", en: "silver, money", zh: "銀子", translit: "kesef" },
            { word: "אַף", target: "ף", strong: "H639", en: "nose, anger", zh: "鼻子，怒氣", translit: "af" },
            { word: "כָּנָף", target: "ף", strong: "H3671", en: "wing", zh: "翅膀", translit: "kanaf" },
            { word: "אֶלֶף", target: "ף", strong: "H505", en: "thousand", zh: "一千", translit: "elef" },
            { word: "יוֹסֵף", target: "ף", strong: "H3130", en: "Joseph", zh: "約瑟", translit: "Yosef" }
        ]
    },
    {
        id: 18,
        letter: "צ",
        name: "Tsade",
        nameHebrew: "צָדֵי",
        sound: "ts (as in 'cats')",
        hasFinalForm: true,
        finalForm: {
            letter: "ץ",
            name: "Final Tsade",
            description: "字尾形（下延）"
        },
        examples: [
            { word: "צֶדֶק", target: "צ", strong: "H6664", en: "righteousness", zh: "公義", translit: "tsedek" },
            { word: "צִיּוֹן", target: "צ", strong: "H6726", en: "Zion", zh: "錫安", translit: "Tsiyon" },
            { word: "צֶלֶם", target: "צ", strong: "H6754", en: "image", zh: "形象", translit: "tselem" },
            { word: "אֶרֶץ", target: "ץ", strong: "H776", en: "earth", zh: "地", translit: "eretz" },
            { word: "עֵץ", target: "ץ", strong: "H6086", en: "tree, wood", zh: "樹", translit: "ets" }
        ],
        // Examples showing final ץ (descending form) at word end
        finalExamples: [
            { word: "אֶרֶץ", target: "ץ", strong: "H776", en: "earth, land", zh: "地", translit: "eretz" },
            { word: "עֵץ", target: "ץ", strong: "H6086", en: "tree, wood", zh: "樹", translit: "ets" },
            { word: "קֵץ", target: "ץ", strong: "H7093", en: "end", zh: "結局", translit: "qets" },
            { word: "חֵץ", target: "ץ", strong: "H2671", en: "arrow", zh: "箭", translit: "chets" },
            { word: "רָץ", target: "ץ", strong: "H7323", en: "ran", zh: "跑", translit: "rats" }
        ]
    },
    {
        id: 19,
        letter: "ק",
        name: "Qof",
        nameHebrew: "קוֹף",
        sound: "q (k from back of throat)",
        examples: [
            { word: "קוֹל", target: "ק", strong: "H6963", en: "voice", zh: "聲音", translit: "qol" },
            { word: "קֹדֶשׁ", target: "ק", strong: "H6944", en: "holy", zh: "聖潔", translit: "qodesh" },
            { word: "קָרָא", target: "ק", strong: "H7121", en: "to call", zh: "呼叫", translit: "qara" },
            { word: "קָטֹן", target: "ק", strong: "H6996", en: "small", zh: "小的", translit: "qaton" },
            { word: "קָדוֹשׁ", target: "ק", strong: "H6918", en: "holy one", zh: "聖者", translit: "qadosh" }
        ]
    },
    {
        id: 20,
        letter: "ר",
        name: "Resh",
        nameHebrew: "רֵישׁ",
        sound: "r (rolled or guttural)",
        examples: [
            { word: "רוּחַ", target: "ר", strong: "H7307", en: "spirit, wind", zh: "靈，風", translit: "ruach" },
            { word: "רֹאשׁ", target: "ר", strong: "H7218", en: "head", zh: "頭", translit: "rosh" },
            { word: "רַב", target: "ר", strong: "H7227", en: "many, great", zh: "多的", translit: "rav" },
            { word: "רָעָה", target: "ר", strong: "H7451", en: "evil", zh: "邪惡", translit: "ra'ah" },
            { word: "רָקִיעַ", target: "ר", strong: "H7549", en: "firmament", zh: "穹蒼", translit: "raqia" }
        ]
    },
    {
        id: 21,
        letter: "שׁ",
        name: "Shin",
        nameHebrew: "שִׁין",
        sound: "sh",
        hasAlternate: true,
        alternateInfo: {
            letter: "שׂ",
            name: "Sin",
            sound: "s",
            description: "點在左邊時發 s 音"
        },
        examples: [
            { word: "שָׁמַיִם", target: "שׁ", strong: "H8064", en: "heaven", zh: "天", translit: "shamayim" },
            { word: "שָׁלוֹם", target: "שׁ", strong: "H7965", en: "peace", zh: "平安", translit: "shalom" },
            { word: "שֵׁם", target: "שׁ", strong: "H8034", en: "name", zh: "名字", translit: "shem" },
            { word: "שָׁמַע", target: "שׁ", strong: "H8085", en: "to hear", zh: "聽", translit: "shama" },
            { word: "שֶׁמֶשׁ", target: "שׁ", strong: "H8121", en: "sun", zh: "太陽", translit: "shemesh" }
        ]
    },
    {
        id: 22,
        letter: "ת",
        name: "Tav",
        nameHebrew: "תָּו",
        sound: "t",
        examples: [
            { word: "תּוֹרָה", target: "ת", strong: "H8451", en: "law, Torah", zh: "律法", translit: "torah" },
            { word: "תְּהוֹם", target: "ת", strong: "H8415", en: "deep", zh: "深淵", translit: "tehom" },
            { word: "תֹהוּ", target: "ת", strong: "H8414", en: "formless", zh: "空虛", translit: "tohu" },
            { word: "תְּפִלָּה", target: "ת", strong: "H8605", en: "prayer", zh: "禱告", translit: "tefillah" },
            { word: "בְּרֵאשִׁית", target: "ת", strong: "H7225", en: "beginning", zh: "起初", translit: "bereshit" }
        ]
    }
];

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = hebrewLetters;
}
