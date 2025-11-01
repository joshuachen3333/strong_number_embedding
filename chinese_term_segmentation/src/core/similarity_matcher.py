"""Similarity-based substring matcher for term refinement.

This module provides substring matching with character-level similarity,
enabling refinement of coarse FHL boundaries by finding the best matching
substring within a larger phrase.

REFACTORED (Phase 2.1): Now uses pluggable SemanticEngine for similarity calculations.
"""

from typing import Optional, Tuple, List
from src.core.semantic_engine import SemanticEngine
from src.core.engines.edit_distance_engine import EditDistanceEngine


class SimilarityMatcher:
    """Find best matching substring using pluggable semantic similarity engines.

    Uses a configurable SemanticEngine for similarity calculations. Defaults to
    EditDistanceEngine (Levenshtein distance with character variant normalization)
    for backward compatibility.

    Example:
        >>> matcher = SimilarityMatcher()  # Uses EditDistanceEngine by default
        >>> matcher.find_best_substring("獨生的", "將他的獨生")
        "獨生"
        >>> matcher.find_best_substring("因為", "因爲天國")
        "因爲"  # Handles character variant 爲/為

        >>> # Or use custom engine
        >>> from src.core.engines import EditDistanceEngine
        >>> engine = EditDistanceEngine()
        >>> matcher = SimilarityMatcher(engine=engine)
    """

    def __init__(self, engine: Optional[SemanticEngine] = None):
        """Initialize the similarity matcher.

        Args:
            engine: Semantic similarity engine to use for scoring.
                   Default: EditDistanceEngine() for backward compatibility.

        Example:
            >>> # Default behavior (backward compatible)
            >>> matcher = SimilarityMatcher()

            >>> # Custom engine
            >>> custom_engine = EditDistanceEngine()
            >>> matcher = SimilarityMatcher(engine=custom_engine)

        Raises:
            TypeError: If engine is not a SemanticEngine instance.
        """
        # Default to EditDistanceEngine for backward compatibility
        if engine is None:
            self.engine = EditDistanceEngine()
        else:
            # Validate engine type
            if not isinstance(engine, SemanticEngine):
                raise TypeError(
                    f"engine must be instance of SemanticEngine, "
                    f"got {type(engine).__name__}"
                )
            self.engine = engine

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

                # Calculate similarity using pluggable engine
                score = self.engine.similarity(refTerm, substring)

                # Only keep if above threshold
                if score > threshold:
                    candidates.append((substring, score, len(substring)))

        if not candidates:
            return None

        # Sort by: 1) similarity score (desc), 2) length (desc, prefer longer)
        candidates.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Return best match
        return candidates[0][0]


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
