"""FHL Bible API client for fetching verses."""

import requests
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


class FHLClient:
    """Client for FHL Bible API.

    API Documentation:
        Base URL: https://bible.fhl.net/json/qb.php
        Parameters:
            - chineses: Chinese book abbreviation (創, 出, etc.)
            - chap: Chapter number
            - sec: Verse number (optional, returns all verses if omitted)
            - version: Bible version (unv, lcc, kjv, etc.)
            - strong: Include Strong's numbers (0 or 1)
    """

    BASE_URL = "https://bible.fhl.net/json/qb.php"

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
                self.BASE_URL,
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
                self.BASE_URL,
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

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
