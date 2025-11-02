"""RefTerm extractor for extracting reference terms from UNV+SN text.

This module provides the core RefTerm extraction functionality that treats
UNV+SN terms as the authoritative semantic baseline, eliminating the need
for external dictionaries.
"""

import re
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from collections import Counter
from enum import Enum

from .strongs_parser import StrongsNumberParser, TermBoundary


class RefTermSource(Enum):
    """Enum for RefTerm data sources.

    These represent different ways to obtain the reference term for matching.

    Attributes:
        UNV_CHINESE: Extract from UNV+SN text (original method)
        HEBREW_WORD: Use Hebrew word form from FHL Parsing API
        HEBREW_LEMMA: Use Hebrew lemma/root from FHL Parsing API
        FHL_CHINESE: Use FHL Chinese explanation from Parsing API
    """
    UNV_CHINESE = "unv-chinese"      # 從 UNV+SN 提取（原有方法）
    HEBREW_WORD = "hebrew-word"      # qp.php word 欄位
    HEBREW_LEMMA = "hebrew-lemma"    # qp.php orig 欄位
    FHL_CHINESE = "fhl-chinese"      # qp.php exp 欄位


@dataclass
class RefTerm:
    """Represents a reference term from UNV+SN text or FHL Parsing API.

    RefTerms are the authoritative semantic baseline for refinement.
    """
    term: str  # Reference term (Chinese from UNV/FHL, or Hebrew from parsing)
    strong_num: str  # Normalized Strong's number (e.g., "H0430", "G2316")
    original_text: str  # Original text with tags (e.g., "神<WH0430>") or full context
    source: RefTermSource = RefTermSource.UNV_CHINESE  # Source of the RefTerm

    def __post_init__(self):
        """Ensure Strong's number is normalized."""
        if self.strong_num and not self.strong_num.startswith(('H', 'G')):
            # Already normalized
            pass
        elif not self.strong_num:
            raise ValueError(f"RefTerm must have a Strong's number")


class RefTermExtractor:
    """Extract reference terms from UNV+SN text or FHL Parsing API.

    This class builds on StrongsNumberParser to create RefTerm objects
    that serve as the authoritative semantic baseline for refinement.

    Supports three RefTerm sources:
    1. UNV_CHINESE: Extract from UNV+SN text (original method)
    2. HEBREW_WORD: Use Hebrew word form from FHL Parsing API
    3. HEBREW_LEMMA: Use Hebrew lemma/root from FHL Parsing API
    4. FHL_CHINESE: Use FHL Chinese explanation from Parsing API

    Example (UNV+SN):
        >>> extractor = RefTermExtractor()
        >>> refterms = extractor.extract_terms("因為<WH03588>神<WH0430>")
        >>> [(rt.term, rt.strong_num) for rt in refterms]
        [('因為', 'H03588'), ('神', 'H0430')]

    Example (Parsing API):
        >>> from src.api.fhl_client import FHLClient, ParsingEntry
        >>> client = FHLClient()
        >>> parsing_entries = client.fetch_parsing("gen", 3, 5)
        >>> refterms = extractor.extract_from_parsing(
        ...     parsing_entries,
        ...     source=RefTermSource.FHL_CHINESE
        ... )
        >>> [(rt.term, rt.strong_num) for rt in refterms]
        [('因為', 'H03588'), ('知道', 'H03045'), ('上帝', 'H0430')]
    """

    def __init__(self):
        """Initialize the RefTerm extractor."""
        self.parser = StrongsNumberParser()

    # Grammar/morphology markers to clean from FHL Chinese explanations
    GRAMMAR_MARKERS = [
        "Qal", "Nif'al", "Pi'el", "Pu'al", "Hif'il", "Hof'al", "Hitpa'el",  # Hebrew stems
        "Nifal", "Piel", "Pual", "Hifil", "Hofal", "Hitpael",  # Alternative spellings
        '主動分詞', '被動分詞', '不定詞', '命令式', '未完成式', '完成式',  # Tenses
        '單陽', '單陰', '複陽', '複陰',  # Number/gender
        '第一人稱', '第二人稱', '第三人稱',  # Person
        '名詞', '動詞', '形容詞', '副詞', '連接詞', '介詞', '代名詞',  # Parts of speech
        '陽性', '陰性', '複數', '單數',  # Gender/number
    ]

    def extract_terms(self, unv_sn_text: str) -> List[RefTerm]:
        """Extract RefTerms from UNV+SN text.

        Args:
            unv_sn_text: UNV text with Strong's Numbers
                Example: "神<WH0430>說<WH0559>"

        Returns:
            List of RefTerm objects with normalized Strong's numbers

        Example:
            >>> extractor = RefTermExtractor()
            >>> refterms = extractor.extract_terms("神<WH0430>說<WH0559>")
            >>> [(rt.term, rt.strong_num) for rt in refterms]
            [('神', 'H0430'), ('說', 'H0559')]
        """
        boundaries = self.parser.parse(unv_sn_text)
        refterms = []

        for boundary in boundaries:
            if boundary.strongs_numbers:
                # A term can have multiple Strong's numbers
                # Create a RefTerm for each Strong's number
                for sn in boundary.strongs_numbers:
                    normalized_sn = self._normalize_strong_num(sn)

                    refterm = RefTerm(
                        term=boundary.term,
                        strong_num=normalized_sn,
                        original_text=unv_sn_text[boundary.start_pos:boundary.end_pos],
                        source=RefTermSource.UNV_CHINESE
                    )
                    refterms.append(refterm)

        return refterms

    def _normalize_strong_num(self, sn: str) -> str:
        """Normalize Strong's number to standard format.

        Converts various formats to standard H#### or G#### format.

        Args:
            sn: Strong's number in any format (e.g., "WH0430", "H430", "G2316")

        Returns:
            Normalized Strong's number (e.g., "H0430", "G2316")

        Example:
            >>> extractor = RefTermExtractor()
            >>> extractor._normalize_strong_num("WH0430")
            'H0430'
            >>> extractor._normalize_strong_num("G25")
            'G0025'
        """
        # Remove 'W' prefix if present
        if sn.startswith('W'):
            sn = sn[1:]

        # Extract letter and number
        match = re.match(r'([HGA])(\d+)', sn)
        if not match:
            return sn  # Return as-is if format is unexpected

        letter, number = match.groups()

        # Pad number to 4 or 5 digits
        if len(number) < 4:
            number = number.zfill(4)
        elif len(number) == 4:
            # Check if it's already 4 digits (Hebrew can be 4 or 5)
            number = number.zfill(4)
        else:
            # 5 digits - keep as is
            pass

        return f"{letter}{number}"

    def build_corpus_map(self, verses: List[str]) -> Dict[str, Counter]:
        """Build frequency map of Strong's numbers to Chinese terms from corpus.

        This scans UNV+SN verses to learn which Chinese terms are most commonly
        used for each Strong's number. This is more reliable than dictionaries!

        Args:
            verses: List of UNV+SN verse texts

        Returns:
            Dictionary mapping Strong's number to Counter of terms
            Example: {"H0430": Counter({"神": 2600, "上帝": 12})}

        Example:
            >>> extractor = RefTermExtractor()
            >>> verses = ["神<WH0430>說", "神<WH0430>看"]
            >>> corpus_map = extractor.build_corpus_map(verses)
            >>> corpus_map["H0430"]
            Counter({'神': 2})
        """
        corpus_map = {}

        for verse in verses:
            refterms = self.extract_terms(verse)

            for refterm in refterms:
                if refterm.strong_num not in corpus_map:
                    corpus_map[refterm.strong_num] = Counter()

                corpus_map[refterm.strong_num][refterm.term] += 1

        return corpus_map

    def get_primary_term(self, corpus_map: Dict[str, Counter],
                        strong_num: str) -> str:
        """Get the most frequent (primary) term for a Strong's number.

        Args:
            corpus_map: Corpus frequency map from build_corpus_map()
            strong_num: Strong's number (e.g., "H0430")

        Returns:
            Most frequent term for this Strong's number

        Example:
            >>> corpus_map = {"H0430": Counter({"神": 2600, "上帝": 12})}
            >>> extractor = RefTermExtractor()
            >>> extractor.get_primary_term(corpus_map, "H0430")
            '神'
        """
        if strong_num not in corpus_map:
            return None

        # Return most common term
        return corpus_map[strong_num].most_common(1)[0][0]

    def get_term_variants(self, corpus_map: Dict[str, Counter],
                         strong_num: str, min_count: int = 3) -> List[str]:
        """Get all variant translations for a Strong's number.

        Args:
            corpus_map: Corpus frequency map
            strong_num: Strong's number
            min_count: Minimum occurrence count to include variant

        Returns:
            List of variant terms sorted by frequency

        Example:
            >>> corpus_map = {"H0430": Counter({"神": 2600, "上帝": 12, "神明": 2})}
            >>> extractor = RefTermExtractor()
            >>> extractor.get_term_variants(corpus_map, "H0430", min_count=3)
            ['神', '上帝']
        """
        if strong_num not in corpus_map:
            return []

        # Filter by minimum count and sort by frequency
        variants = [term for term, count in corpus_map[strong_num].items()
                   if count >= min_count]

        # Sort by frequency (descending)
        variants.sort(key=lambda t: corpus_map[strong_num][t], reverse=True)

        return variants

    def extract_from_parsing(
        self,
        parsing_entries: List,  # List[ParsingEntry] from fhl_client
        source: RefTermSource = RefTermSource.FHL_CHINESE
    ) -> List[RefTerm]:
        """Extract RefTerms from FHL Parsing API entries.

        Args:
            parsing_entries: List of ParsingEntry objects from FHLClient.fetch_parsing()
            source: Which field to use as RefTerm (default: FHL_CHINESE)

        Returns:
            List of RefTerm objects

        Example:
            >>> from src.api.fhl_client import FHLClient
            >>> client = FHLClient()
            >>> parsing_entries = client.fetch_parsing("gen", 3, 5)
            >>>
            >>> # Use FHL Chinese explanation
            >>> refterms = extractor.extract_from_parsing(
            ...     parsing_entries,
            ...     source=RefTermSource.FHL_CHINESE
            ... )
            >>> [(rt.term, rt.strong_num) for rt in refterms[:3]]
            [('因為', 'H03588'), ('知道', 'H03045'), ('上帝', 'H0430')]
            >>>
            >>> # Use Hebrew lemma
            >>> refterms = extractor.extract_from_parsing(
            ...     parsing_entries,
            ...     source=RefTermSource.HEBREW_LEMMA
            ... )
            >>> [(rt.term, rt.strong_num) for rt in refterms[:3]]
            [('כִּי', 'H03588'), ('יָדַע', 'H03045'), ('אֱלֹהִים', 'H0430')]
        """
        refterms = []

        for entry in parsing_entries:
            # Skip entries without Strong's Number (like wid=0 summary row)
            if not entry.sn or entry.wid == '0':
                continue

            # Get the term based on source
            if source == RefTermSource.HEBREW_WORD:
                term = entry.word
            elif source == RefTermSource.HEBREW_LEMMA:
                term = entry.orig
            elif source == RefTermSource.FHL_CHINESE:
                # Clean grammar markers from Chinese explanation
                term = self._clean_fhl_chinese(entry.exp)
            else:
                raise ValueError(f"Unsupported RefTermSource for Parsing API: {source}")

            # Skip if term is empty after extraction
            if not term or not term.strip():
                continue

            # Normalize Strong's Number
            sn_list = entry.get_sn_list()
            if not sn_list:
                # Try to parse SN directly if get_sn_list() failed
                sn_list = [entry.sn]

            # Create RefTerm for each SN (handles compound SNs)
            for sn in sn_list:
                normalized_sn = self._normalize_strong_num(sn)

                refterm = RefTerm(
                    term=term.strip(),
                    strong_num=normalized_sn,
                    original_text=f"{entry.word} (wid={entry.wid})",
                    source=source
                )
                refterms.append(refterm)

        return refterms

    def _clean_fhl_chinese(self, exp: str) -> str:
        """Clean FHL Chinese explanation by removing grammar markers.

        Args:
            exp: FHL Chinese explanation (e.g., "Qal 知道、認識、辨別")

        Returns:
            Cleaned Chinese term (e.g., "知道")

        Example:
            >>> extractor = RefTermExtractor()
            >>> extractor._clean_fhl_chinese("Qal 知道、認識、辨別")
            '知道'
            >>> extractor._clean_fhl_chinese("上帝、神、神明")
            '上帝'
            >>> extractor._clean_fhl_chinese("因為、當、如果、即使、不必翻譯")
            '因為'
            >>> extractor._clean_fhl_chinese("不必翻譯")
            ''  # Returns empty for non-translatable terms
        """
        if not exp:
            return ""

        # Remove grammar markers at the beginning
        cleaned = exp
        for marker in self.GRAMMAR_MARKERS:
            # Match marker at start with optional space
            pattern = rf'^{re.escape(marker)}\s+'
            cleaned = re.sub(pattern, '', cleaned)

        # Split by various delimiters (、 , ; ；)
        delimiters = ['、', ',', ';', '；']
        parts = [cleaned]
        for delimiter in delimiters:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(delimiter))
            parts = new_parts

        # Clean each part
        parts = [p.strip() for p in parts if p.strip()]

        if not parts:
            return ""

        # Filter out non-translatable terms
        non_translatable = ['不必翻譯', '即使', '等等', '或']
        valid_parts = [p for p in parts if p not in non_translatable]

        if not valid_parts:
            # All parts are non-translatable
            return ""

        # Return first valid meaning
        return valid_parts[0]
