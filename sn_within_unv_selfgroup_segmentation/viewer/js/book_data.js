/**
 * book_data.js
 * Book mappings for all 66 books with English/Chinese abbreviations and chapter counts
 */

const BOOK_DATA = [
  // Old Testament
  { eng: 'Gen', chi: '創', chiLong: '創世記', engLong: 'Genesis', chapters: 50 },
  { eng: 'Exod', chi: '出', chiLong: '出埃及記', engLong: 'Exodus', chapters: 40 },
  { eng: 'Lev', chi: '利', chiLong: '利未記', engLong: 'Leviticus', chapters: 27 },
  { eng: 'Num', chi: '民', chiLong: '民數記', engLong: 'Numbers', chapters: 36 },
  { eng: 'Deut', chi: '申', chiLong: '申命記', engLong: 'Deuteronomy', chapters: 34 },
  { eng: 'Josh', chi: '書', chiLong: '約書亞記', engLong: 'Joshua', chapters: 24 },
  { eng: 'Judg', chi: '士', chiLong: '士師記', engLong: 'Judges', chapters: 21 },
  { eng: 'Ruth', chi: '得', chiLong: '路得記', engLong: 'Ruth', chapters: 4 },
  { eng: '1Sam', chi: '撒上', chiLong: '撒母耳記上', engLong: '1 Samuel', chapters: 31 },
  { eng: '2Sam', chi: '撒下', chiLong: '撒母耳記下', engLong: '2 Samuel', chapters: 24 },
  { eng: '1Kgs', chi: '王上', chiLong: '列王紀上', engLong: '1 Kings', chapters: 22 },
  { eng: '2Kgs', chi: '王下', chiLong: '列王紀下', engLong: '2 Kings', chapters: 25 },
  { eng: '1Chr', chi: '代上', chiLong: '歷代志上', engLong: '1 Chronicles', chapters: 29 },
  { eng: '2Chr', chi: '代下', chiLong: '歷代志下', engLong: '2 Chronicles', chapters: 36 },
  { eng: 'Ezra', chi: '拉', chiLong: '以斯拉記', engLong: 'Ezra', chapters: 10 },
  { eng: 'Neh', chi: '尼', chiLong: '尼希米記', engLong: 'Nehemiah', chapters: 13 },
  { eng: 'Esth', chi: '斯', chiLong: '以斯帖記', engLong: 'Esther', chapters: 10 },
  { eng: 'Job', chi: '伯', chiLong: '約伯記', engLong: 'Job', chapters: 42 },
  { eng: 'Ps', chi: '詩', chiLong: '詩篇', engLong: 'Psalms', chapters: 150 },
  { eng: 'Prov', chi: '箴', chiLong: '箴言', engLong: 'Proverbs', chapters: 31 },
  { eng: 'Eccl', chi: '傳', chiLong: '傳道書', engLong: 'Ecclesiastes', chapters: 12 },
  { eng: 'Song', chi: '歌', chiLong: '雅歌', engLong: 'Song of Solomon', chapters: 8 },
  { eng: 'Isa', chi: '賽', chiLong: '以賽亞書', engLong: 'Isaiah', chapters: 66 },
  { eng: 'Jer', chi: '耶', chiLong: '耶利米書', engLong: 'Jeremiah', chapters: 52 },
  { eng: 'Lam', chi: '哀', chiLong: '耶利米哀歌', engLong: 'Lamentations', chapters: 5 },
  { eng: 'Ezek', chi: '結', chiLong: '以西結書', engLong: 'Ezekiel', chapters: 48 },
  { eng: 'Dan', chi: '但', chiLong: '但以理書', engLong: 'Daniel', chapters: 12 },
  { eng: 'Hos', chi: '何', chiLong: '何西阿書', engLong: 'Hosea', chapters: 14 },
  { eng: 'Joel', chi: '珥', chiLong: '約珥書', engLong: 'Joel', chapters: 3 },
  { eng: 'Amos', chi: '摩', chiLong: '阿摩司書', engLong: 'Amos', chapters: 9 },
  { eng: 'Obad', chi: '俄', chiLong: '俄巴底亞書', engLong: 'Obadiah', chapters: 1 },
  { eng: 'Jonah', chi: '拿', chiLong: '約拿書', engLong: 'Jonah', chapters: 4 },
  { eng: 'Mic', chi: '彌', chiLong: '彌迦書', engLong: 'Micah', chapters: 7 },
  { eng: 'Nah', chi: '鴻', chiLong: '那鴻書', engLong: 'Nahum', chapters: 3 },
  { eng: 'Hab', chi: '哈', chiLong: '哈巴谷書', engLong: 'Habakkuk', chapters: 3 },
  { eng: 'Zeph', chi: '番', chiLong: '西番雅書', engLong: 'Zephaniah', chapters: 3 },
  { eng: 'Hag', chi: '該', chiLong: '哈該書', engLong: 'Haggai', chapters: 2 },
  { eng: 'Zech', chi: '亞', chiLong: '撒迦利亞書', engLong: 'Zechariah', chapters: 14 },
  { eng: 'Mal', chi: '瑪', chiLong: '瑪拉基書', engLong: 'Malachi', chapters: 4 },

  // New Testament
  { eng: 'Matt', chi: '太', chiLong: '馬太福音', engLong: 'Matthew', chapters: 28 },
  { eng: 'Mark', chi: '可', chiLong: '馬可福音', engLong: 'Mark', chapters: 16 },
  { eng: 'Luke', chi: '路', chiLong: '路加福音', engLong: 'Luke', chapters: 24 },
  { eng: 'John', chi: '約', chiLong: '約翰福音', engLong: 'John', chapters: 21 },
  { eng: 'Acts', chi: '徒', chiLong: '使徒行傳', engLong: 'Acts', chapters: 28 },
  { eng: 'Rom', chi: '羅', chiLong: '羅馬書', engLong: 'Romans', chapters: 16 },
  { eng: '1Cor', chi: '林前', chiLong: '哥林多前書', engLong: '1 Corinthians', chapters: 16 },
  { eng: '2Cor', chi: '林後', chiLong: '哥林多後書', engLong: '2 Corinthians', chapters: 13 },
  { eng: 'Gal', chi: '加', chiLong: '加拉太書', engLong: 'Galatians', chapters: 6 },
  { eng: 'Eph', chi: '弗', chiLong: '以弗所書', engLong: 'Ephesians', chapters: 6 },
  { eng: 'Phil', chi: '腓', chiLong: '腓立比書', engLong: 'Philippians', chapters: 4 },
  { eng: 'Col', chi: '西', chiLong: '歌羅西書', engLong: 'Colossians', chapters: 4 },
  { eng: '1Thess', chi: '帖前', chiLong: '帖撒羅尼迦前書', engLong: '1 Thessalonians', chapters: 5 },
  { eng: '2Thess', chi: '帖後', chiLong: '帖撒羅尼迦後書', engLong: '2 Thessalonians', chapters: 3 },
  { eng: '1Tim', chi: '提前', chiLong: '提摩太前書', engLong: '1 Timothy', chapters: 6 },
  { eng: '2Tim', chi: '提後', chiLong: '提摩太後書', engLong: '2 Timothy', chapters: 4 },
  { eng: 'Titus', chi: '多', chiLong: '提多書', engLong: 'Titus', chapters: 3 },
  { eng: 'Phlm', chi: '門', chiLong: '腓利門書', engLong: 'Philemon', chapters: 1 },
  { eng: 'Heb', chi: '來', chiLong: '希伯來書', engLong: 'Hebrews', chapters: 13 },
  { eng: 'Jas', chi: '雅', chiLong: '雅各書', engLong: 'James', chapters: 5 },
  { eng: '1Pet', chi: '彼前', chiLong: '彼得前書', engLong: '1 Peter', chapters: 5 },
  { eng: '2Pet', chi: '彼後', chiLong: '彼得後書', engLong: '2 Peter', chapters: 3 },
  { eng: '1John', chi: '約一', chiLong: '約翰一書', engLong: '1 John', chapters: 5 },
  { eng: '2John', chi: '約二', chiLong: '約翰二書', engLong: '2 John', chapters: 1 },
  { eng: '3John', chi: '約三', chiLong: '約翰三書', engLong: '3 John', chapters: 1 },
  { eng: 'Jude', chi: '猶', chiLong: '猶大書', engLong: 'Jude', chapters: 1 },
  { eng: 'Rev', chi: '啟', chiLong: '啟示錄', engLong: 'Revelation', chapters: 22 }
];

// Create lookup maps
const BOOK_MAP_ENG = {};
const BOOK_MAP_CHI = {};

BOOK_DATA.forEach(book => {
  BOOK_MAP_ENG[book.eng] = book;
  BOOK_MAP_CHI[book.chi] = book;
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { BOOK_DATA, BOOK_MAP_ENG, BOOK_MAP_CHI };
}
