"""
Semantic Engine Interface

This module defines the abstract base class for semantic similarity engines.
All engines must implement this interface to be compatible with the
SimilarityMatcher system.

Created: 2025-11-01
Phase: 2.1 (Architecture Refactor)
"""

from abc import ABC, abstractmethod


class SemanticEngine(ABC):
    """
    Abstract base class for semantic similarity engines.

    All engines must implement this interface to be compatible
    with the SimilarityMatcher system. Engines compute semantic
    similarity between text strings, returning scores in [0, 1].

    Examples:
        >>> class MyEngine(SemanticEngine):
        ...     def similarity(self, text1: str, text2: str) -> float:
        ...         # Custom similarity logic
        ...         return 0.5
        ...     def get_name(self) -> str:
        ...         return "my-engine"
        ...
        >>> engine = MyEngine()
        >>> score = engine.similarity("神", "上帝")
        >>> print(f"{engine.get_name()}: {score}")
        my-engine: 0.5
    """

    @abstractmethod
    def similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two text strings.

        This method must be implemented by all concrete engine classes.
        The similarity score represents how semantically similar the
        two text strings are, with higher scores indicating greater
        similarity.

        Args:
            text1: First text string to compare
            text2: Second text string to compare

        Returns:
            Similarity score in range [0.0, 1.0]
            - 0.0: Completely dissimilar (no semantic relationship)
            - 1.0: Identical or perfectly similar (same meaning)
            - 0.5: Moderate similarity (some relationship)

        Raises:
            ValueError: If inputs are invalid (e.g., None, empty strings)
            NotImplementedError: If method is not implemented by subclass

        Note:
            Implementations should handle Chinese text appropriately,
            including Traditional and Simplified characters, and should
            be robust to different character encodings.

        Examples:
            >>> engine = EditDistanceEngine()
            >>> engine.similarity("神", "神")  # Exact match
            1.0
            >>> engine.similarity("神", "上帝")  # Different characters
            0.0
            >>> engine.similarity("神的", "神")  # Partial match
            0.5
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the engine identifier for logging and metrics.

        This method must return a unique identifier for the engine
        that can be used in CLI flags, logging, and metrics collection.

        Returns:
            Unique engine name (kebab-case recommended)
            Examples: "edit-distance", "sentence-transformer", "bert"

        Note:
            The name should be:
            - Unique across all engines
            - Lowercase with hyphens (kebab-case)
            - Descriptive of the algorithm used
            - Suitable for use in CLI arguments

        Examples:
            >>> engine = EditDistanceEngine()
            >>> engine.get_name()
            'edit-distance'
        """
        pass

    def __repr__(self) -> str:
        """
        Return string representation of the engine.

        Returns:
            String in format "ClassName(name='engine-name')"

        Examples:
            >>> engine = EditDistanceEngine()
            >>> repr(engine)
            "EditDistanceEngine(name='edit-distance')"
        """
        return f"{self.__class__.__name__}(name='{self.get_name()}')"

    def __str__(self) -> str:
        """
        Return user-friendly string representation.

        Returns:
            Engine name

        Examples:
            >>> engine = EditDistanceEngine()
            >>> str(engine)
            'edit-distance'
        """
        return self.get_name()
