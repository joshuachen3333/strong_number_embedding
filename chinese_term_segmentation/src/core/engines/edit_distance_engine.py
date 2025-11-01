"""
Edit Distance Semantic Engine

Character-based similarity engine using Levenshtein edit distance.
This is the baseline engine that wraps the existing edit distance logic.

Created: 2025-11-01
Phase: 2.1 (Architecture Refactor)
"""

from typing import Optional
from src.core.semantic_engine import SemanticEngine
from src.core.char_variant_normalizer import CharVariantNormalizer


class EditDistanceEngine(SemanticEngine):
    """
    Character-based edit distance similarity engine.

    This is the baseline engine that measures character-level similarity
    using Levenshtein distance. It does NOT understand semantic meaning,
    only character overlap.

    Features:
    - Levenshtein edit distance calculation
    - Character variant normalization (爲 → 為)
    - Normalized similarity scores [0, 1]

    Limitations:
    - Cannot recognize synonyms (神 vs 上帝 → 0.0 similarity)
    - Cannot handle semantic relationships
    - Limited to character-level matching

    Examples:
        >>> engine = EditDistanceEngine()
        >>> engine.similarity("神", "神")  # Exact match
        1.0
        >>> engine.similarity("神", "上帝")  # No character overlap
        0.0
        >>> engine.similarity("獨生的", "獨生")  # Partial match
        0.666...
        >>> engine.similarity("因爲", "因為")  # Variant match
        1.0
    """

    def __init__(self, normalizer: Optional[CharVariantNormalizer] = None):
        """
        Initialize EditDistanceEngine.

        Args:
            normalizer: Optional character variant normalizer.
                       Default: Use default CharVariantNormalizer().

        Example:
            >>> engine = EditDistanceEngine()  # Use default normalizer
            >>> custom_norm = CharVariantNormalizer()
            >>> engine2 = EditDistanceEngine(normalizer=custom_norm)
        """
        self.normalizer = normalizer or CharVariantNormalizer()

    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute edit distance based similarity.

        Algorithm:
        1. Normalize character variants (爲 → 為)
        2. Compute Levenshtein distance
        3. Normalize to [0, 1]: similarity = 1 - (distance / max_length)

        Args:
            text1: First text string
            text2: Second text string

        Returns:
            Similarity score in range [0.0, 1.0]
            - 1.0: Identical (after normalization)
            - 0.0: Completely different characters
            - 0.5: Half of characters match

        Raises:
            ValueError: If both texts are empty

        Examples:
            >>> engine = EditDistanceEngine()
            >>> engine.similarity("神", "神")
            1.0
            >>> engine.similarity("神的", "神")
            0.5  # 1 - (1/2) = 0.5
            >>> engine.similarity("abc", "xyz")
            0.0
        """
        if not text1 and not text2:
            return 1.0  # Both empty → identical

        if not text1 or not text2:
            return 0.0  # One empty → no similarity

        # Normalize character variants first
        text1_norm = self.normalizer.normalize(text1)
        text2_norm = self.normalizer.normalize(text2)

        # Calculate edit distance
        distance = self._levenshtein(text1_norm, text2_norm)

        # Normalize by max length
        max_len = max(len(text1_norm), len(text2_norm))

        if max_len == 0:
            return 1.0  # Both empty after normalization

        # Convert to similarity score (0.0-1.0)
        similarity = 1.0 - (distance / max_len)

        return similarity

    def get_name(self) -> str:
        """
        Return engine identifier.

        Returns:
            "edit-distance"

        Example:
            >>> engine = EditDistanceEngine()
            >>> engine.get_name()
            'edit-distance'
        """
        return "edit-distance"

    def _levenshtein(self, s1: str, s2: str) -> int:
        """
        Calculate Levenshtein edit distance between two strings.

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
            >>> engine = EditDistanceEngine()
            >>> engine._levenshtein("獨生的", "獨生")
            1  # Remove "的"
            >>> engine._levenshtein("abc", "abc")
            0  # Identical
            >>> engine._levenshtein("kitten", "sitting")
            3  # k→s, e→i, insert g

        Algorithm:
            Uses classic DP table where dp[i][j] represents the minimum
            edits needed to transform s1[0:i] into s2[0:j].

            Recurrence relation:
            - If s1[i-1] == s2[j-1]: dp[i][j] = dp[i-1][j-1]
            - Else: dp[i][j] = 1 + min(
                dp[i-1][j],      # Delete from s1
                dp[i][j-1],      # Insert into s1
                dp[i-1][j-1]     # Substitute
              )
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

    def __repr__(self) -> str:
        """
        Return string representation.

        Returns:
            String in format "EditDistanceEngine(name='edit-distance')"

        Example:
            >>> engine = EditDistanceEngine()
            >>> repr(engine)
            "EditDistanceEngine(name='edit-distance')"
        """
        return f"EditDistanceEngine(name='{self.get_name()}')"
