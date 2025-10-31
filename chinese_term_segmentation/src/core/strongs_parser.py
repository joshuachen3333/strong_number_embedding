"""Strong's Number parser for extracting term boundaries from UNV+SN text.

⚠️  CRITICAL UNDERSTANDING - READ THIS FIRST! ⚠️
=================================================

Strong's Number tags mark the word BEFORE them, NOT after!

错误理解 (WRONG): SN tag 后面的字符 = 新词的开始
正确理解 (CORRECT): SN tag 标记它前面的词！

Example:
    "因為<G3754>"
    ❌ WRONG: G3754 applies to whatever comes AFTER
    ✅ CORRECT: G3754 applies to "因為" (the word BEFORE the tag)

Real example from Matthew 5:3:
    "的人有福了<G3107>！因為<G3754>天<G3772>國<G932>"
    Parsing:
    - "的人有福了" + <G3107> → term "的人有福了" has SN [G3107]
    - "因為" + <G3754> → term "因為" has SN [G3754]
    - "天" + <G3772> → term "天" has SN [G3772]
    - "國" + <G932> → term "國" has SN [G932]

This was the MAJOR BUG in initial implementation - I was collecting SNs for the NEXT term
instead of the CURRENT term. This caused completely wrong term-to-SN associations.

Implementation implication: When encountering a tag, finalize the CURRENT accumulated term
with that tag's SN, then start accumulating the NEXT term.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class TermBoundary:
    """Represents a term with its Strong's Numbers."""
    term: str  # Chinese term text
    strongs_numbers: List[str]  # List of Strong's Numbers (e.g., ["G2316", "G25"])
    start_pos: int  # Start position in original text
    end_pos: int  # End position in original text


class StrongsNumberParser:
    """Parser for extracting term boundaries from UNV text with Strong's Numbers.

    ⚠️  KEY PRINCIPLE: Strong's Number tags FOLLOW the term they describe!

    Supports four Strong's Number formats from FHL API:
    1. <WH1234> / <WG5678> - FHL Hebrew/Greek format
    2. {<WH1234>} / {<WG5678>} - Wrapped format
    3. {H1234} / {G5678} - Simple format
    4. (H1234) / (G5678) - Parentheses format

    Also handles morphology tags like <WTH8804>, <WTG5656>, etc.
    """

    # Regex pattern for Strong's Numbers (all formats)
    # Matches: <WH1234>, <WG5678>, {<WH1234>}, {H1234}, (G5678), etc.
    # Also matches morphology tags: <WTH8804>, <WTG5656>
    SN_PATTERN = re.compile(
        r'<WT[HG]\d+>|'  # Morphology tags (e.g., <WTH8804>)
        r'<WAH\d+>|'  # Aramaic morphology tags
        r'[<{(](?:W)?([HG]\d+)[>})]'  # Strong's Numbers
    )

    def __init__(self):
        """Initialize the parser."""
        pass

    def parse(self, text_with_sn: str) -> List[TermBoundary]:
        """Parse UNV text with Strong's Numbers to extract term boundaries.

        Key principle: Strong's Number tags FOLLOW the term they describe.
        Example: "因為<G3754>" means "因為" corresponds to G3754.

        Args:
            text_with_sn: UNV text with Strong's Numbers
                Example: "神<G2316>愛<G25>世人<G2889>"

        Returns:
            List of TermBoundary objects with terms and their Strong's Numbers

        Example:
            >>> parser = StrongsNumberParser()
            >>> boundaries = parser.parse("神<G2316>愛<G25>世人<G2889>")
            >>> [(b.term, b.strongs_numbers) for b in boundaries]
            [('神', ['G2316']), ('愛', ['G25']), ('世人', ['G2889'])]
        """
        boundaries = []
        current_term = ""
        current_start = 0
        i = 0

        while i < len(text_with_sn):
            # Check for Strong's Number or morphology tag
            match = self.SN_PATTERN.match(text_with_sn, i)

            if match:
                # Found a tag - this marks the END of current term
                # The tag(s) apply to the term we just accumulated

                # Extract Strong's Number if present (group 1)
                collected_sns = []
                if match.group(1):
                    collected_sns.append(match.group(1))

                # Move past this tag
                i = match.end()

                # Check if there are more consecutive tags (multiple SNs for one term)
                while i < len(text_with_sn):
                    next_match = self.SN_PATTERN.match(text_with_sn, i)
                    if next_match:
                        if next_match.group(1):
                            collected_sns.append(next_match.group(1))
                        i = next_match.end()
                    else:
                        break

                # Finalize the current term with collected SNs
                if current_term:
                    boundaries.append(TermBoundary(
                        term=current_term,
                        strongs_numbers=collected_sns,
                        start_pos=current_start,
                        end_pos=i
                    ))
                    current_term = ""
                    current_start = i

            else:
                char = text_with_sn[i]

                # Handle punctuation and whitespace
                if char in ' \t\n　，。、：；！？「」『』':
                    # Finalize current term if exists (without SN)
                    if current_term:
                        boundaries.append(TermBoundary(
                            term=current_term,
                            strongs_numbers=[],
                            start_pos=current_start,
                            end_pos=i
                        ))
                        current_term = ""

                    i += 1
                    current_start = i

                else:
                    # Regular character - add to current term
                    current_term += char
                    i += 1

        # Add last term if exists (without SN - tags should have been processed)
        if current_term:
            boundaries.append(TermBoundary(
                term=current_term,
                strongs_numbers=[],
                start_pos=current_start,
                end_pos=len(text_with_sn)
            ))

        return boundaries

    def extract_terms(self, text_with_sn: str) -> List[str]:
        """Extract just the terms (without Strong's Numbers).

        Args:
            text_with_sn: UNV text with Strong's Numbers

        Returns:
            List of Chinese terms

        Example:
            >>> parser = StrongsNumberParser()
            >>> parser.extract_terms("神<G2316>愛<G25>世人<G2889>")
            ['神', '愛', '世人']
        """
        boundaries = self.parse(text_with_sn)
        return [b.term for b in boundaries]

    def get_clean_text(self, text_with_sn: str) -> str:
        """Remove all Strong's Number tags to get clean text.

        Args:
            text_with_sn: UNV text with Strong's Numbers

        Returns:
            Clean Chinese text without any tags

        Example:
            >>> parser = StrongsNumberParser()
            >>> parser.get_clean_text("神<G2316>愛<G25>世人<G2889>")
            '神愛世人'
        """
        # Remove all SN tags
        clean = self.SN_PATTERN.sub('', text_with_sn)
        return clean

    def get_sn_mapping(self, text_with_sn: str) -> dict[str, List[str]]:
        """Create a mapping of terms to their Strong's Numbers.

        Args:
            text_with_sn: UNV text with Strong's Numbers

        Returns:
            Dictionary mapping terms to their Strong's Numbers

        Example:
            >>> parser = StrongsNumberParser()
            >>> parser.get_sn_mapping("神<G2316>愛<G25>世人<G2889>")
            {'神': ['G2316'], '愛': ['G25'], '世人': ['G2889']}
        """
        boundaries = self.parse(text_with_sn)
        mapping = {}

        for boundary in boundaries:
            if boundary.term and boundary.strongs_numbers:
                mapping[boundary.term] = boundary.strongs_numbers

        return mapping
