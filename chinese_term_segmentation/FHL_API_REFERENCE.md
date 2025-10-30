# FHL Bible API Reference

Based on investigation of https://bible.fhl.net/json/ and related documentation.

## Official Documentation Sources

1. **Main API Documentation**: https://bible.fhl.net/json/
2. **Book Abbreviation List**: https://bible.fhl.net/new/listall.html
3. **Bible Reading Interface**: https://bible.fhl.net/new/read.php

## Bible Version Codes (版本)

### Confirmed Versions

Based on URL parameter analysis from FHL's reading interface and API responses:

| Code | Full Name | Language |
|------|-----------|----------|
| `unv` | 和合本 (Chinese Union Version) | Chinese |
| `ncv` | 新譯本 (New Chinese Version) | Chinese |
| `rcuv` | 和合本修訂版 (Revised Chinese Union Version) | Chinese |
| `rcuv2010` | 和合本2010 | Chinese |
| `lcc` | 呂振中譯本 (Lü Zhènzhōng Translation) | Chinese |
| `esv` | English Standard Version | English |
| `kjv` | King James Version | English |
| `nasb` | New American Standard Bible | English |
| `nstrunv` | 新標點和合本 (default for qb.php) | Chinese |
| `tcv` | 台語聖經 (default for rt.php) | Taiwanese |
| `c1933` | 客語聖經 (default for sesub.php) | Hakka |

### Additional Versions (from au.php audio Bible)

- 台語 (Taiwanese)
- 客家話 (Hakka)
- 廣東話 (Cantonese)
- 現代中文譯本 (Today's Chinese Version)
- 紅皮聖經 (Red Cover Bible)
- 希伯來文 (Hebrew)
- 福州話 (Fuzhou dialect)
- 希臘文 (Greek)
- NetBible中文版 (NetBible Chinese)
- 全民台語聖經 (Common Taiwanese Bible)
- 鄒語 (Tsou language)
- 現代台語譯本 (Modern Taiwanese Translation)
- 現代客語譯本 (Modern Hakka Translation)
- 達悟語 (Tao language)

## Book Abbreviations (書卷)

### Official Mapping Structure

The official book list at https://bible.fhl.net/new/listall.html provides:
- 編號 (Number): 1-66 for canonical books, 101-115 for Apocrypha, 201-217 for Apostolic Fathers
- 英文簡寫 (English Abbreviation): Gen, Ex, Matt, etc.
- 英文全名 (English Full Name): Genesis, Exodus, Matthew, etc.
- 中文簡寫 (Chinese Abbreviation): 創, 出, 太, etc.
- 英文短簡寫 (English Short Abbreviation): Ge, Ex, Mt, etc.

### 66 Canonical Books

#### Old Testament (1-39)

| # | English | Full Name | Chinese | Chinese Full |
|---|---------|-----------|---------|--------------|
| 1 | Gen | Genesis | 創 | 創世記 |
| 2 | Ex | Exodus | 出 | 出埃及記 |
| 3 | Lev | Leviticus | 利 | 利未記 |
| 4 | Num | Numbers | 民 | 民數記 |
| 5 | Deut | Deuteronomy | 申 | 申命記 |
| 6 | Josh | Joshua | 書 | 約書亞記 |
| 7 | Judg | Judges | 士 | 士師記 |
| 8 | Ruth | Ruth | 得 | 路得記 |
| 9 | 1 Sam | First Samuel | 撒上 | 撒母耳記上 |
| 10 | 2 Sam | Second Samuel | 撒下 | 撒母耳記下 |
| 11 | 1 Kings | First Kings | 王上 | 列王紀上 |
| 12 | 2 Kings | Second Kings | 王下 | 列王紀下 |
| 13 | 1 Chron | First Chronicles | 代上 | 歷代志上 |
| 14 | 2 Chron | Second Chronicles | 代下 | 歷代志下 |
| 15 | Ezra | Ezra | 拉 | 以斯拉記 |
| 16 | Neh | Nehemiah | 尼 | 尼希米記 |
| 17 | Esth | Esther | 斯 | 以斯帖記 |
| 18 | Job | Job | 伯 | 約伯記 |
| 19 | Ps | Psalms | 詩 | 詩篇 |
| 20 | Prov | Proverbs | 箴 | 箴言 |
| 21 | Eccles | Ecclesiastes | 傳 | 傳道書 |
| 22 | Song | Song of Solomon | 歌 | 雅歌 |
| 23 | Is | Isaiah | 賽 | 以賽亞書 |
| 24 | Jer | Jeremiah | 耶 | 耶利米書 |
| 25 | Lam | Lamentations | 哀 | 耶利米哀歌 |
| 26 | Ezek | Ezekiel | 結 | 以西結書 |
| 27 | Dan | Daniel | 但 | 但以理書 |
| 28 | Hos | Hosea | 何 | 何西阿書 |
| 29 | Joel | Joel | 珥 | 約珥書 |
| 30 | Amos | Amos | 摩 | 阿摩司書 |
| 31 | Obad | Obadiah | 俄 | 俄巴底亞書 |
| 32 | Jon | Jonah | 拿 | 約拿書 |
| 33 | Mic | Micah | 彌 | 彌迦書 |
| 34 | Nah | Nahum | 鴻 | 那鴻書 |
| 35 | Hab | Habakkuk | 哈 | 哈巴谷書 |
| 36 | Zeph | Zephaniah | 番 | 西番雅書 |
| 37 | Hag | Haggai | 該 | 哈該書 |
| 38 | Zech | Zechariah | 亞 | 撒迦利亞書 |
| 39 | Mal | Malachi | 瑪 | 瑪拉基書 |

#### New Testament (40-66)

| # | English | Full Name | Chinese | Chinese Full |
|---|---------|-----------|---------|--------------|
| 40 | Matt | Matthew | 太 | 馬太福音 |
| 41 | Mark | Mark | 可 | 馬可福音 |
| 42 | Luke | Luke | 路 | 路加福音 |
| 43 | John | John | 約 | 約翰福音 |
| 44 | Acts | Acts | 徒 | 使徒行傳 |
| 45 | Rom | Romans | 羅 | 羅馬書 |
| 46 | 1 Cor | First Corinthians | 林前 | 哥林多前書 |
| 47 | 2 Cor | Second Corinthians | 林後 | 哥林多後書 |
| 48 | Gal | Galatians | 加 | 加拉太書 |
| 49 | Eph | Ephesians | 弗 | 以弗所書 |
| 50 | Phil | Philippians | 腓 | 腓立比書 |
| 51 | Col | Colossians | 西 | 歌羅西書 |
| 52 | 1 Thess | First Thessalonians | 帖前 | 帖撒羅尼迦前書 |
| 53 | 2 Thess | Second Thessalonians | 帖後 | 帖撒羅尼迦後書 |
| 54 | 1 Tim | First Timothy | 提前 | 提摩太前書 |
| 55 | 2 Tim | Second Timothy | 提後 | 提摩太後書 |
| 56 | Titus | Titus | 多 | 提多書 |
| 57 | Philem | Philemon | 門 | 腓利門書 |
| 58 | Heb | Hebrews | 來 | 希伯來書 |
| 59 | James | James | 雅 | 雅各書 |
| 60 | 1 Pet | First Peter | 彼前 | 彼得前書 |
| 61 | 2 Pet | Second Peter | 彼後 | 彼得後書 |
| 62 | 1 John | First John | 約一 | 約翰一書 |
| 63 | 2 John | Second John | 約二 | 約翰二書 |
| 64 | 3 John | Third John | 約三 | 約翰三書 |
| 65 | Jude | Jude | 猶 | 猶大書 |
| 66 | Rev | Revelation | 啟 | 啟示錄 |

## API Endpoints

### 1. qb.php - Retrieve Bible Verses

**URL**: `https://bible.fhl.net/json/qb.php`

**Parameters**:
- `chineses` (required): Chinese book abbreviation (創, 出, 太, etc.)
- `chap` (required): Chapter number
- `sec` (optional): Verse number (omit to get all verses in chapter)
- `version` (optional): Bible version code (default: nstrunv)
- `strong` (optional): Include Strong's numbers (0 or 1, default: 0)
- `gb` (optional): Simplified Chinese output (0 or 1)

**Response Format**:
```json
{
  "record": [
    {
      "sec": "1",
      "bible_text": "起初　神創造天地。"
    },
    {
      "sec": "2",
      "bible_text": "地是空虛混沌，淵面黑暗；　神的靈運行在水面上。"
    }
  ]
}
```

**Example**:
```
https://bible.fhl.net/json/qb.php?chineses=創&chap=1&sec=1&version=unv&strong=0
```

### 2. se.php - Search Bible Text

**Parameters**:
- `VERSION`: Bible version code
- `orig`: Original language flag
- `q`: Search query
- `RANGE`: Search range
- `limit`: Results limit
- `offset`: Results offset
- `gb`: Simplified Chinese flag

### 3. qp.php - Parse Word Analysis

**Parameters**:
- `engs`: English book abbreviation
- `chap`: Chapter number
- `sec`: Verse number
- `gb`: Simplified Chinese flag

### 4. sc.php - Get Commentaries

**Parameters**:
- `book`: Book identifier
- `engs`: English book abbreviation
- `chap`: Chapter number
- `sec`: Verse number
- `gb`: Simplified Chinese flag
- `validbook`: Valid book flag

### 5. sd.php - Original Language Dictionary

**Parameters**:
- `N`: Entry number
- `k`: Keyword
- `gb`: Simplified Chinese flag

### 6. au.php - Audio Bible

**Parameters**:
- `version`: Audio version
- `bid`: Book ID
- `chap`: Chapter number
- `gb`: Simplified Chinese flag

## Important Notes

1. **Chinese Abbreviations Required**: Even for English Bible versions (KJV, ESV, etc.), the API requires Chinese book abbreviations in the `chineses` parameter.

2. **Strong's Numbers**: Not all versions have Strong's numbers available via the JSON API. The web interface may have more complete data.

3. **Verse Ranges**: To fetch verse ranges (e.g., John 3:16-17), make separate API calls for each verse or fetch the entire chapter and filter.

4. **Book Numbering**:
   - 1-66: Canonical Protestant Bible
   - 101-115: Apocrypha/Deuterocanonical books
   - 201-217: Apostolic Fathers' writings

5. **Character Encoding**: API returns UTF-8 encoded Traditional Chinese characters. Use `gb=1` parameter for Simplified Chinese.

## Verification Against Implementation

Our `src/api/book_mappings.py` implementation **correctly matches** the official FHL book abbreviations:
- ✅ "genesis" → "創" (matches official)
- ✅ "matthew" → "太" (matches official)
- ✅ All 66 canonical books correctly mapped

Our `src/api/fhl_client.py` supported versions **align with** FHL's confirmed versions:
- ✅ unv, lcc, kjv, rcuv2010, esv, nasb all confirmed

## References

- Official API Documentation: https://bible.fhl.net/json/
- Book Abbreviation List: https://bible.fhl.net/new/listall.html
- Bible Reading Interface: https://bible.fhl.net/new/read.php
- Parent Project Documentation: ../CLAUDE.md
