"""Similarity-based substring matcher for term refinement.

This module provides substring matching with character-level similarity,
enabling refinement of coarse FHL boundaries by finding the best matching
substring within a larger phrase.
"""

from typing import Optional, Dict, Tuple, List


class SimilarityMatcher:
    """Find best matching substring using character-level similarity.

    Uses edit distance (Levenshtein distance) with character variant
    normalization to find the most similar substring within a coarse boundary.

    Example:
        >>> matcher = SimilarityMatcher()
        >>> matcher.find_best_substring("獨生的", "將他的獨生")
        "獨生"
        >>> matcher.find_best_substring("因為", "因爲天國")
        "因爲"  # Handles character variant 爲/為
    """

    def __init__(self):
        """Initialize the similarity matcher."""
        self.variant_map = self._load_character_variants()

    def find_best_substring(
        self,
        refTerm: str,
        origText: str,
        threshold: float = 0.6
    ) -> Optional[str]:
        """Find best matching substring in origText.

        Generates all possible substrings of origText (length ≥ 2),
        calculates similarity with refTerm using edit distance,
        and returns the substring with highest similarity above threshold.

        Args:
            refTerm: Reference term from Strong's Dictionary (e.g., "獨生的")
            origText: Coarse boundary from UNV+SN (e.g., "將他的獨生")
            threshold: Minimum similarity score (0.0-1.0, default: 0.6)

        Returns:
            Best matching substring, or None if no match above threshold

        Algorithm:
            1. Generate all substrings of origText (length ≥ 2)
            2. Calculate similarity for each substring vs refTerm
            3. Normalize character variants before comparison
            4. Return substring with highest similarity > threshold
            5. Prefer longer matches if similarity scores are equal

        Example:
            >>> matcher.find_best_substring("獨生的", "將他的獨生")
            "獨生"  # similarity ~0.67 after removing "的"

            >>> matcher.find_best_substring("因為", "因爲天國")
            "因爲"  # variant match after normalization

            >>> matcher.find_best_substring("獨生的", "天國是")
            None  # no substring above threshold
        """
        if not refTerm or not origText:
            return None

        # Collect candidates: (substring, similarity_score, length)
        candidates: List[Tuple[str, float, int]] = []

        # Determine minimum substring length
        # If refTerm is single char, allow single-char substrings
        # Otherwise, require substrings of length ≥ 2 for efficiency
        min_length = 1 if len(refTerm) == 1 else 2

        # Generate all substrings (length ≥ min_length)
        for i in range(len(origText)):
            for j in range(i + min_length, len(origText) + 1):
                substring = origText[i:j]

                # Calculate similarity
                score = self._similarity(refTerm, substring)

                # Only keep if above threshold
                if score > threshold:
                    candidates.append((substring, score, len(substring)))

        if not candidates:
            return None

        # Sort by: 1) similarity score (desc), 2) length (desc, prefer longer)
        candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Return best match
        return candidates[0][0]

    def _similarity(self, s1: str, s2: str) -> float:
        """Calculate character-level similarity score.

        Uses edit distance (Levenshtein) normalized by max length,
        with character variant normalization applied first.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Similarity score from 0.0 (completely different) to 1.0 (identical)

        Formula:
            similarity = 1.0 - (edit_distance / max_length)

        Example:
            >>> matcher._similarity("獨生的", "獨生")
            0.666...  # 1 - (1/3) = 0.67

            >>> matcher._similarity("因為", "因爲")
            1.0  # Perfect match after variant normalization

            >>> matcher._similarity("abc", "abc")
            1.0  # Identical strings
        """
        # Normalize character variants first
        s1_norm = self._normalize_variants(s1)
        s2_norm = self._normalize_variants(s2)

        # Calculate edit distance
        distance = self._edit_distance(s1_norm, s2_norm)

        # Normalize by max length
        max_len = max(len(s1_norm), len(s2_norm))

        if max_len == 0:
            return 0.0

        # Convert to similarity score (0.0-1.0)
        similarity = 1.0 - (distance / max_len)

        return similarity

    def _edit_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein edit distance between two strings.

        Uses dynamic programming to find minimum number of single-character
        edits (insertions, deletions, substitutions) needed to transform
        s1 into s2.

        Args:
            s1: Source string
            s2: Target string

        Returns:
            Edit distance (minimum number of edits)

        Complexity:
            Time: O(m × n) where m, n are string lengths
            Space: O(m × n) for DP table

        Example:
            >>> matcher._edit_distance("獨生的", "獨生")
            1  # Remove "的"

            >>> matcher._edit_distance("abc", "abc")
            0  # Identical

            >>> matcher._edit_distance("kitten", "sitting")
            3  # k→s, e→i, insert g
        """
        m, n = len(s1), len(s2)

        # Create DP table
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Initialize base cases
        for i in range(m + 1):
            dp[i][0] = i  # Delete all chars from s1
        for j in range(n + 1):
            dp[0][j] = j  # Insert all chars from s2

        # Fill DP table
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    # Characters match, no edit needed
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    # Take minimum of: insert, delete, substitute
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # Delete from s1
                        dp[i][j - 1],      # Insert into s1
                        dp[i - 1][j - 1]   # Substitute
                    )

        return dp[m][n]

    def _normalize_variants(self, text: str) -> str:
        """Normalize character variants to standard form.

        Replaces variant Chinese characters with their standard equivalents
        to enable matching across different Bible versions that use different
        Unicode codepoints for the same semantic character.

        Args:
            text: Text with potential character variants

        Returns:
            Text with variants normalized to standard form

        Common Biblical Variants:
            爲 (U+7232) → 為 (U+70BA)  # "because"
            衞 (U+885E) → 衛 (U+885B)  # "David"
            綫 (U+7DAB) → 線 (U+7DDA)  # "line"

        Example:
            >>> matcher._normalize_variants("因爲天國")
            "因為天國"  # 爲 → 為

            >>> matcher._normalize_variants("大衞王")
            "大衛王"  # 衞 → 衛

            >>> matcher._normalize_variants("no variants")
            "no variants"  # No change
        """
        if not text:
            return ""

        normalized = text
        for variant, standard in self.variant_map.items():
            normalized = normalized.replace(variant, standard)
        return normalized

    def _load_character_variants(self) -> Dict[str, str]:
        """Load character variant mappings.

        Returns dictionary mapping variant characters to their standard forms.
        This list is expandable as new variants are discovered in biblical texts.

        Returns:
            Dictionary of {variant: standard} mappings

        Common Biblical Variants:
            - 爲/為: Different Unicode representations of "because/為"
            - 衞/衛: Different forms of "guard/衛" (as in "David/大衛")
            - 綫/線: Different forms of "line/線"

        Note:
            This is a curated list of common variants found in Chinese Bible
            translations. Additional variants can be discovered by analyzing
            unmatched terms and examining Unicode differences.

        Future Enhancement:
            Could be loaded from external configuration file for easier updates.
        """
        return {
            # Common biblical character variants
            '爲': '為',  # U+7232 → U+70BA (because, 因爲 → 因為)
            '衞': '衛',  # U+885E → U+885B (guard, 大衞 → 大衛)
            '綫': '線',  # U+7DAB → U+7DDA (line, 界綫 → 界線)

            # Add more variants as discovered
            # Format: 'variant': 'standard'
        }


# Convenience function for quick testing
def find_best_match(ref: str, text: str, threshold: float = 0.6) -> Optional[str]:
    """Convenience function for quick substring matching.

    Args:
        ref: Reference term
        text: Text to search in
        threshold: Similarity threshold

    Returns:
        Best matching substring or None

    Example:
        >>> find_best_match("獨生的", "將他的獨生")
        "獨生"
    """
    matcher = SimilarityMatcher()
    return matcher.find_best_substring(ref, text, threshold)
