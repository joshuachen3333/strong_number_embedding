"""Bible book name mappings for English/Chinese and abbreviations."""

# Book mappings: English name -> Chinese abbreviation (required by FHL API)
BOOK_MAP_EN_TO_ZH = {
    # Old Testament
    "genesis": "創",
    "exodus": "出",
    "leviticus": "利",
    "numbers": "民",
    "deuteronomy": "申",
    "joshua": "書",
    "judges": "士",
    "ruth": "得",
    "1samuel": "撒上",
    "2samuel": "撒下",
    "1kings": "王上",
    "2kings": "王下",
    "1chronicles": "代上",
    "2chronicles": "代下",
    "ezra": "拉",
    "nehemiah": "尼",
    "esther": "斯",
    "job": "伯",
    "psalms": "詩",
    "proverbs": "箴",
    "ecclesiastes": "傳",
    "songofsolomon": "歌",
    "isaiah": "賽",
    "jeremiah": "耶",
    "lamentations": "哀",
    "ezekiel": "結",
    "daniel": "但",
    "hosea": "何",
    "joel": "珥",
    "amos": "摩",
    "obadiah": "俄",
    "jonah": "拿",
    "micah": "彌",
    "nahum": "鴻",
    "habakkuk": "哈",
    "zephaniah": "番",
    "haggai": "該",
    "zechariah": "亞",
    "malachi": "瑪",

    # New Testament
    "matthew": "太",
    "mark": "可",
    "luke": "路",
    "john": "約",
    "acts": "徒",
    "romans": "羅",
    "1corinthians": "林前",
    "2corinthians": "林後",
    "galatians": "加",
    "ephesians": "弗",
    "philippians": "腓",
    "colossians": "西",
    "1thessalonians": "帖前",
    "2thessalonians": "帖後",
    "1timothy": "提前",
    "2timothy": "提後",
    "titus": "多",
    "philemon": "門",
    "hebrews": "來",
    "james": "雅",
    "1peter": "彼前",
    "2peter": "彼後",
    "1john": "約一",
    "2john": "約二",
    "3john": "約三",
    "jude": "猶",
    "revelation": "啟",
}

# Common abbreviations -> full book name
BOOK_ABBREVIATIONS = {
    # Old Testament
    "gen": "genesis",
    "ge": "genesis",
    "exod": "exodus",
    "ex": "exodus",
    "lev": "leviticus",
    "le": "leviticus",
    "num": "numbers",
    "nu": "numbers",
    "deut": "deuteronomy",
    "de": "deuteronomy",
    "dt": "deuteronomy",
    "josh": "joshua",
    "jos": "joshua",
    "judg": "judges",
    "jdg": "judges",
    "ru": "ruth",
    "1sam": "1samuel",
    "1sa": "1samuel",
    "2sam": "2samuel",
    "2sa": "2samuel",
    "1ki": "1kings",
    "2ki": "2kings",
    "1chr": "1chronicles",
    "1ch": "1chronicles",
    "2chr": "2chronicles",
    "2ch": "2chronicles",
    "ezr": "ezra",
    "neh": "nehemiah",
    "ne": "nehemiah",
    "est": "esther",
    "es": "esther",
    "ps": "psalms",
    "psalm": "psalms",
    "prov": "proverbs",
    "pr": "proverbs",
    "eccl": "ecclesiastes",
    "ec": "ecclesiastes",
    "song": "songofsolomon",
    "sos": "songofsolomon",
    "ss": "songofsolomon",
    "isa": "isaiah",
    "is": "isaiah",
    "jer": "jeremiah",
    "je": "jeremiah",
    "lam": "lamentations",
    "la": "lamentations",
    "ezek": "ezekiel",
    "eze": "ezekiel",
    "dan": "daniel",
    "da": "daniel",
    "hos": "hosea",
    "ho": "hosea",
    "joe": "joel",
    "jl": "joel",
    "am": "amos",
    "ob": "obadiah",
    "oba": "obadiah",
    "jon": "jonah",
    "jnh": "jonah",
    "mic": "micah",
    "mi": "micah",
    "nah": "nahum",
    "na": "nahum",
    "hab": "habakkuk",
    "hb": "habakkuk",
    "zeph": "zephaniah",
    "zep": "zephaniah",
    "hag": "haggai",
    "hg": "haggai",
    "zech": "zechariah",
    "zec": "zechariah",
    "mal": "malachi",
    "ml": "malachi",

    # New Testament
    "matt": "matthew",
    "mat": "matthew",
    "mt": "matthew",
    "mar": "mark",
    "mk": "mark",
    "luk": "luke",
    "lk": "luke",
    "jn": "john",
    "joh": "john",
    "act": "acts",
    "ac": "acts",
    "rom": "romans",
    "ro": "romans",
    "1cor": "1corinthians",
    "1co": "1corinthians",
    "2cor": "2corinthians",
    "2co": "2corinthians",
    "gal": "galatians",
    "ga": "galatians",
    "eph": "ephesians",
    "ep": "ephesians",
    "phil": "philippians",
    "php": "philippians",
    "col": "colossians",
    "co": "colossians",
    "1thess": "1thessalonians",
    "1th": "1thessalonians",
    "2thess": "2thessalonians",
    "2th": "2thessalonians",
    "1tim": "1timothy",
    "1ti": "1timothy",
    "2tim": "2timothy",
    "2ti": "2timothy",
    "tit": "titus",
    "ti": "titus",
    "phm": "philemon",
    "pm": "philemon",
    "heb": "hebrews",
    "he": "hebrews",
    "jas": "james",
    "jam": "james",
    "1pet": "1peter",
    "1pe": "1peter",
    "2pet": "2peter",
    "2pe": "2peter",
    "1jn": "1john",
    "2jn": "2john",
    "3jn": "3john",
    "jud": "jude",
    "jd": "jude",
    "rev": "revelation",
    "re": "revelation",
}

def normalize_book_name(book: str) -> str:
    """Normalize book name to lowercase without spaces or numbers in middle.

    Args:
        book: Book name or abbreviation

    Returns:
        Normalized book name

    Examples:
        "Gen" -> "gen"
        "1 Samuel" -> "1samuel"
        "Song of Solomon" -> "songofsolomon"
    """
    # Remove spaces and convert to lowercase
    normalized = book.lower().replace(" ", "").replace("_", "")
    return normalized

def get_chinese_book_abbr(book: str) -> str:
    """Get Chinese book abbreviation from English name or abbreviation.

    Args:
        book: English book name or abbreviation (e.g., "Genesis", "Gen", "gen")

    Returns:
        Chinese abbreviation (e.g., "創")

    Raises:
        ValueError: If book name not recognized
    """
    # Normalize input
    normalized = normalize_book_name(book)

    # Try as abbreviation first
    if normalized in BOOK_ABBREVIATIONS:
        full_name = BOOK_ABBREVIATIONS[normalized]
    else:
        full_name = normalized

    # Get Chinese abbreviation
    if full_name in BOOK_MAP_EN_TO_ZH:
        return BOOK_MAP_EN_TO_ZH[full_name]

    # If still not found, raise error
    raise ValueError(f"Unknown book name: {book}")

def list_supported_books():
    """Get list of all supported book names (English full names)."""
    return sorted(BOOK_MAP_EN_TO_ZH.keys())
