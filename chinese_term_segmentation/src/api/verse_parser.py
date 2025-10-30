"""Verse reference parser for Bible citations.

Supports formats like:
- "Gen 1:3"
- "John 3:16"
- "Romans 8:28-30" (verse ranges)
- "Psalm 23:1-6"
"""

import re
from dataclasses import dataclass
from typing import List, Tuple
from .book_mappings import get_chinese_book_abbr, normalize_book_name


@dataclass
class VerseReference:
    """Represents a parsed Bible verse reference."""

    book: str              # English book name (normalized)
    book_zh: str          # Chinese book abbreviation
    chapter: int
    verse_start: int
    verse_end: int        # Same as verse_start if single verse

    @property
    def is_range(self) -> bool:
        """Check if this is a verse range."""
        return self.verse_end > self.verse_start

    @property
    def verses(self) -> List[int]:
        """Get list of verse numbers in this reference."""
        return list(range(self.verse_start, self.verse_end + 1))

    def __str__(self) -> str:
        """String representation."""
        if self.is_range:
            return f"{self.book.title()} {self.chapter}:{self.verse_start}-{self.verse_end}"
        else:
            return f"{self.book.title()} {self.chapter}:{self.verse_start}"


class VerseParser:
    """Parser for Bible verse references."""

    # Regex patterns
    # Matches: "Gen 1:3", "Genesis 1:3", "1 Samuel 2:10"
    VERSE_PATTERN = re.compile(
        r"^([123]?\s*[a-zA-Z]+(?:\s+of\s+[a-zA-Z]+)?)\s+(\d+):(\d+)(?:-(\d+))?$",
        re.IGNORECASE
    )

    @classmethod
    def parse(cls, reference: str) -> VerseReference:
        """Parse a verse reference string.

        Args:
            reference: Verse reference (e.g., "Gen 1:3", "John 3:16-17")

        Returns:
            VerseReference object

        Raises:
            ValueError: If reference format is invalid

        Examples:
            >>> parser = VerseParser()
            >>> ref = parser.parse("Gen 1:3")
            >>> ref.book
            'genesis'
            >>> ref.chapter
            1
            >>> ref.verse_start
            3
        """
        reference = reference.strip()

        match = cls.VERSE_PATTERN.match(reference)
        if not match:
            raise ValueError(
                f"Invalid verse reference format: {reference}\n"
                f"Expected format: 'Book Chapter:Verse' (e.g., 'Gen 1:3', 'John 3:16-17')"
            )

        book_str, chapter_str, verse_start_str, verse_end_str = match.groups()

        # Parse book name
        try:
            book_zh = get_chinese_book_abbr(book_str)
        except ValueError as e:
            raise ValueError(f"Unknown book name: {book_str}") from e

        # Parse numbers
        chapter = int(chapter_str)
        verse_start = int(verse_start_str)
        verse_end = int(verse_end_str) if verse_end_str else verse_start

        # Validate
        if chapter < 1:
            raise ValueError(f"Invalid chapter number: {chapter}")
        if verse_start < 1:
            raise ValueError(f"Invalid verse number: {verse_start}")
        if verse_end < verse_start:
            raise ValueError(
                f"Invalid verse range: {verse_start}-{verse_end} "
                f"(end must be >= start)"
            )

        # Normalize book name
        book_normalized = normalize_book_name(book_str)
        from .book_mappings import BOOK_ABBREVIATIONS, BOOK_MAP_EN_TO_ZH

        if book_normalized in BOOK_ABBREVIATIONS:
            book_full = BOOK_ABBREVIATIONS[book_normalized]
        else:
            book_full = book_normalized

        return VerseReference(
            book=book_full,
            book_zh=book_zh,
            chapter=chapter,
            verse_start=verse_start,
            verse_end=verse_end
        )

    @classmethod
    def parse_multiple(cls, references: List[str]) -> List[VerseReference]:
        """Parse multiple verse references.

        Args:
            references: List of verse reference strings

        Returns:
            List of VerseReference objects
        """
        return [cls.parse(ref) for ref in references]
