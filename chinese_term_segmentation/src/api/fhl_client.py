"""FHL Bible API client for fetching verses and Strong's dictionary."""

import requests
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class VerseData:
    """Represents a single verse from FHL API."""

    version: str          # Bible version (unv, lcc, etc.)
    book: str            # English book name
    book_zh: str         # Chinese book abbreviation
    chapter: int
    verse: int
    text: str            # Verse text


@dataclass
class StrongEntry:
    """Represents a Strong's Number dictionary entry from FHL API."""

    sn: str                    # Strong's number (e.g., "3439")
    original: str              # Original Greek/Hebrew word (e.g., "μονογενής")
    chinese_meaning: str       # Chinese meaning/translation
    english_meaning: str       # English meaning/translation
    related: List[str]         # Related words (NT only)


class FHLClient:
    """Client for FHL Bible API.

    API Documentation:
        Verse API: https://bible.fhl.net/json/qb.php
            Parameters:
                - chineses: Chinese book abbreviation (創, 出, etc.)
                - chap: Chapter number
                - sec: Verse number (optional, returns all verses if omitted)
                - version: Bible version (unv, lcc, kjv, etc.)
                - strong: Include Strong's numbers (0 or 1)

        Strong's Dictionary API: https://bible.fhl.net/json/sd.php
            Parameters:
                - N: Testament (0=NT, 1=OT)
                - k: Strong's number (numeric, without G/H prefix)
                - gb: Language (0=traditional Chinese, 1=simplified)
    """

    VERSE_API_URL = "https://bible.fhl.net/json/qb.php"
    STRONG_DICT_API_URL = "https://bible.fhl.net/json/sd.php"

    # Supported versions
    SUPPORTED_VERSIONS = [
        "unv",      # 和合本 (Chinese Union Version)
        "lcc",      # 呂振中譯本
        "kjv",      # King James Version
        "rcuv2010", # 和合本2010
        "esv",      # English Standard Version
        "nasb",     # New American Standard Bible
    ]

    def __init__(self, timeout: int = 10):
        """Initialize FHL API client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self._strong_dict_cache: Dict[str, Optional[StrongEntry]] = {}

    def fetch_verse(
        self,
        book_zh: str,
        chapter: int,
        verse: int,
        version: str = "unv",
        include_strongs: bool = False
    ) -> Optional[VerseData]:
        """Fetch a single verse from FHL API.

        Args:
            book_zh: Chinese book abbreviation (e.g., "創", "太")
            chapter: Chapter number
            verse: Verse number
            version: Bible version code
            include_strongs: Include Strong's numbers in text

        Returns:
            VerseData object or None if not found

        Raises:
            requests.RequestException: If API request fails
            ValueError: If version not supported
        """
        if version not in self.SUPPORTED_VERSIONS:
            raise ValueError(
                f"Unsupported version: {version}. "
                f"Supported: {', '.join(self.SUPPORTED_VERSIONS)}"
            )

        params = {
            "chineses": book_zh,
            "chap": str(chapter),
            "sec": str(verse),
            "version": version,
            "strong": "1" if include_strongs else "0"
        }

        logger.debug(f"Fetching verse: {book_zh} {chapter}:{verse} ({version})")

        try:
            response = self.session.get(
                self.VERSE_API_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Parse response
            if "record" in data and len(data["record"]) > 0:
                record = data["record"][0]

                return VerseData(
                    version=version,
                    book="",  # Will be filled by caller
                    book_zh=book_zh,
                    chapter=chapter,
                    verse=verse,
                    text=record.get("bible_text", "")
                )

            logger.warning(f"No data returned for {book_zh} {chapter}:{verse}")
            return None

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def fetch_verses(
        self,
        book_zh: str,
        chapter: int,
        verses: List[int],
        version: str = "unv",
        include_strongs: bool = False
    ) -> List[VerseData]:
        """Fetch multiple verses from FHL API.

        Args:
            book_zh: Chinese book abbreviation
            chapter: Chapter number
            verses: List of verse numbers
            version: Bible version code
            include_strongs: Include Strong's numbers

        Returns:
            List of VerseData objects
        """
        results = []

        for verse_num in verses:
            verse_data = self.fetch_verse(
                book_zh=book_zh,
                chapter=chapter,
                verse=verse_num,
                version=version,
                include_strongs=include_strongs
            )

            if verse_data:
                results.append(verse_data)

        return results

    def fetch_chapter(
        self,
        book_zh: str,
        chapter: int,
        version: str = "unv",
        include_strongs: bool = False
    ) -> List[VerseData]:
        """Fetch entire chapter from FHL API.

        Args:
            book_zh: Chinese book abbreviation
            chapter: Chapter number
            version: Bible version code
            include_strongs: Include Strong's numbers

        Returns:
            List of VerseData objects (all verses in chapter)
        """
        params = {
            "chineses": book_zh,
            "chap": str(chapter),
            "version": version,
            "strong": "1" if include_strongs else "0"
        }

        logger.debug(f"Fetching chapter: {book_zh} {chapter} ({version})")

        try:
            response = self.session.get(
                self.VERSE_API_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            results = []
            if "record" in data:
                for i, record in enumerate(data["record"], start=1):
                    results.append(VerseData(
                        version=version,
                        book="",
                        book_zh=book_zh,
                        chapter=chapter,
                        verse=i,  # Verse number is sequential
                        text=record.get("bible_text", "")
                    ))

            return results

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def fetch_for_correction(
        self,
        book_zh: str,
        chapter: int,
        verse: int,
        target_version: str = "lcc"
    ) -> tuple[Optional[VerseData], Optional[VerseData]]:
        """Fetch both target version and UNV+SN for boundary correction.

        This is a convenience method for the SN-based correction workflow.

        Args:
            book_zh: Chinese book abbreviation
            chapter: Chapter number
            verse: Verse number
            target_version: Target version to correct (lcc, rcuv2010, etc.)

        Returns:
            Tuple of (target_verse, unv_sn_verse)
            - target_verse: Verse in target version (without SN)
            - unv_sn_verse: UNV verse with Strong's Numbers (reference)

        Raises:
            ValueError: If target_version is "unv" (redundant)
            requests.RequestException: If API request fails
        """
        if target_version == "unv":
            raise ValueError(
                "Cannot use UNV as target for SN correction. "
                "UNV already has Strong's Numbers. "
                "Use other versions: lcc, rcuv2010, rcuv"
            )

        # Fetch target version (without Strong's Numbers)
        target_verse = self.fetch_verse(
            book_zh=book_zh,
            chapter=chapter,
            verse=verse,
            version=target_version,
            include_strongs=False
        )

        # Fetch UNV with Strong's Numbers (reference standard)
        unv_sn_verse = self.fetch_verse(
            book_zh=book_zh,
            chapter=chapter,
            verse=verse,
            version="unv",
            include_strongs=True
        )

        return target_verse, unv_sn_verse

    def fetch_strong_dict(
        self,
        sn: str,
        simplified: bool = False
    ) -> Optional[StrongEntry]:
        """Fetch Strong's Number dictionary entry from FHL API.

        Args:
            sn: Strong's number with prefix (e.g., "G3439", "H430")
            simplified: Use simplified Chinese if True (default: traditional)

        Returns:
            StrongEntry object or None if not found

        Raises:
            ValueError: If SN format is invalid
            requests.RequestException: If API request fails

        Example:
            >>> client = FHLClient()
            >>> entry = client.fetch_strong_dict("G3439")
            >>> entry.original
            'μονογενής'
            >>> entry.chinese_meaning
            '獨生的'
        """
        # Validate and parse SN
        if not sn or len(sn) < 2:
            raise ValueError(f"Invalid Strong's number format: {sn}")

        prefix = sn[0].upper()
        if prefix not in ('G', 'H'):
            raise ValueError(
                f"Invalid Strong's number prefix: {prefix}. "
                "Expected 'G' (Greek) or 'H' (Hebrew)"
            )

        try:
            number = sn[1:]  # Remove prefix
            int(number)  # Validate it's numeric
        except ValueError:
            raise ValueError(
                f"Invalid Strong's number: {sn}. "
                "Expected format: G#### or H####"
            )

        # Check cache first
        cache_key = f"{sn}_{int(simplified)}"
        if cache_key in self._strong_dict_cache:
            logger.debug(f"Strong's cache hit: {sn}")
            return self._strong_dict_cache[cache_key]

        # Determine testament: G=New Testament (0), H=Old Testament (1)
        testament = 0 if prefix == 'G' else 1

        params = {
            "N": str(testament),
            "k": number,
            "gb": "1" if simplified else "0"
        }

        logger.debug(f"Fetching Strong's: {sn} (testament={testament}, gb={params['gb']})")

        try:
            response = self.session.get(
                self.STRONG_DICT_API_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Parse response
            if data.get("record_count", 0) > 0 and "record" in data:
                record = data["record"][0]

                # Extract Chinese meaning from dic_text (【...】 pattern)
                chinese_meaning = self._extract_chinese_meaning(
                    record.get("dic_text", "")
                )

                entry = StrongEntry(
                    sn=record.get("sn", number),
                    original=record.get("orig", ""),
                    chinese_meaning=chinese_meaning,
                    english_meaning=record.get("edic_text", "")[:100],  # Limit length
                    related=[]  # TODO: Parse 'same' field if needed
                )

                # Cache the result
                self._strong_dict_cache[cache_key] = entry
                logger.debug(f"Strong's fetched and cached: {sn}")
                return entry

            # Not found - cache None to avoid repeated API calls
            logger.warning(f"Strong's entry not found: {sn}")
            self._strong_dict_cache[cache_key] = None
            return None

        except requests.RequestException as e:
            logger.error(f"API request failed for {sn}: {e}")
            # Don't cache errors - allow retry
            return None

    def _extract_chinese_meaning(self, dic_text: str) -> str:
        """Extract Chinese meaning from dictionary text.

        The dic_text format from FHL API typically looks like:
        "3439 monogenes {mon-og-en-ace'}\r\n\r\n源字 SNG03441...\r\n\r\n欽定本 -...\r\n\r\n1) 獨一無二的, 唯一的\r\n..."

        Args:
            dic_text: Raw dictionary text from API

        Returns:
            Extracted Chinese meaning (first definition)
        """
        if not dic_text:
            return ""

        # Strategy 1: Extract from 【...】 brackets (some entries use this)
        match = re.search(r'【([^】]+)】', dic_text)
        if match:
            return match.group(1)

        # Strategy 2: Extract from numbered definition "1) ..."
        # This is the most common format in FHL
        match = re.search(r'1\)\s*([^\r\n]+)', dic_text)
        if match:
            meaning = match.group(1).strip()
            # Remove trailing sub-definitions (1a), 1b), etc.)
            meaning = re.split(r'\s+1[a-z]\)', meaning)[0].strip()
            # Remove commas and extra whitespace
            meaning = meaning.rstrip('，,')
            return meaning

        # Strategy 3: Look for Chinese after "欽定本" marker
        # Skip "源字" and find actual definitions
        parts = dic_text.split('欽定本')
        if len(parts) > 1:
            # Find first meaningful Chinese phrase after marker
            chinese_match = re.search(r'[\u4e00-\u9fff]{2,}', parts[1])
            if chinese_match:
                return chinese_match.group(0)

        # Strategy 4: Find first multi-character Chinese phrase
        # (skipping single chars like "源", "字")
        chinese_match = re.search(r'[\u4e00-\u9fff]{2,}', dic_text)
        if chinese_match:
            word = chinese_match.group(0)
            # Skip common meta words
            if word not in ['源字', '欽定本', '形容詞', '動詞', '名詞']:
                return word

        # Last resort: return first 20 chars
        return dic_text[:20].strip()

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
