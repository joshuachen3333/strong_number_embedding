"""Semantic clusters for representing translation variants.

This module provides SemanticCluster to group multiple translation variants
for a single Strong's number, enabling robust semantic matching.
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TranslationVariant:
    """Represents a translation variant for a Strong's number."""
    term: str  # The translated term
    source: str  # Source version (e.g., "UNV", "KJV", "LCC")
    frequency: int = 1  # Occurrence frequency
    weight: float = 1.0  # Authority weight (UNV higher than others)


class SemanticCluster:
    """Represent semantic variants for a Strong's number.

    A cluster groups all known translation variants for a Strong's number
    across different Bible versions, enabling robust semantic matching.

    Example:
        >>> cluster = SemanticCluster("H0430")
        >>> cluster.set_core_term("神", "UNV")
        >>> cluster.add_variant("上帝", "LCC", frequency=12)
        >>> cluster.add_variant("God", "KJV", frequency=2500)
        >>> cluster.get_all_terms()
        ['神', '上帝', 'God']
    """

    def __init__(self, strong_num: str):
        """Initialize semantic cluster for a Strong's number.

        Args:
            strong_num: Strong's number (e.g., "H0430", "G2316")
        """
        self.strong_num = strong_num
        self.core_term: Optional[str] = None  # Primary term from UNV
        self.core_source: Optional[str] = None
        self.variants: List[TranslationVariant] = []
        self.embeddings: Dict[str, np.ndarray] = {}  # Pre-computed embeddings
        self._unified_embedding: Optional[np.ndarray] = None

        # Authority weights for different sources
        self.source_weights = {
            'UNV': 1.0,  # Highest authority (reference baseline)
            'KJV': 0.8,
            'LCC': 0.7,
            'ESV': 0.7,
            'RCUV': 0.6,
        }

    def set_core_term(self, term: str, source: str = "UNV", frequency: int = 1):
        """Set the core (primary) term for this cluster.

        The core term is typically the most frequent term from UNV.

        Args:
            term: The core term
            source: Source version
            frequency: Occurrence frequency
        """
        self.core_term = term
        self.core_source = source

        # Also add as a variant
        self.add_variant(term, source, frequency, is_core=True)

    def add_variant(self, term: str, source: str,
                   frequency: int = 1, is_core: bool = False):
        """Add a translation variant to the cluster.

        Args:
            term: The translated term
            source: Source version (e.g., "UNV", "KJV")
            frequency: Occurrence frequency
            is_core: Whether this is the core term
        """
        # Check if already exists
        for variant in self.variants:
            if variant.term == term and variant.source == source:
                # Update frequency
                variant.frequency += frequency
                return

        # Calculate weight based on source authority and frequency
        base_weight = self.source_weights.get(source, 0.5)
        weight = base_weight * (1.0 if is_core else 0.8)

        variant = TranslationVariant(
            term=term,
            source=source,
            frequency=frequency,
            weight=weight
        )
        self.variants.append(variant)

        # Invalidate cached unified embedding
        self._unified_embedding = None

    def get_all_terms(self, min_frequency: int = 1) -> List[str]:
        """Get all unique terms in the cluster.

        Args:
            min_frequency: Minimum frequency threshold

        Returns:
            List of unique terms sorted by weight and frequency
        """
        # Filter by frequency
        filtered = [v for v in self.variants if v.frequency >= min_frequency]

        # Sort by weight * frequency (descending)
        filtered.sort(key=lambda v: v.weight * v.frequency, reverse=True)

        # Return unique terms
        seen = set()
        result = []
        for variant in filtered:
            if variant.term not in seen:
                seen.add(variant.term)
                result.append(variant.term)

        return result

    def compute_embeddings(self, semantic_engine):
        """Compute embeddings for all variants using semantic engine.

        Args:
            semantic_engine: Engine with encode() method
        """
        for variant in self.variants:
            if variant.term not in self.embeddings:
                # Encode the term
                embedding = semantic_engine.encode(variant.term)
                self.embeddings[variant.term] = embedding

        # Invalidate cached unified embedding
        self._unified_embedding = None

    def get_unified_embedding(self) -> Optional[np.ndarray]:
        """Get weighted average embedding of all variants.

        Returns:
            Unified embedding vector, or None if embeddings not computed

        Note:
            This caches the result. Call compute_embeddings() first.
        """
        if self._unified_embedding is not None:
            return self._unified_embedding

        if not self.embeddings:
            return None

        # Compute weighted average
        weighted_sum = None
        total_weight = 0.0

        for variant in self.variants:
            if variant.term in self.embeddings:
                embedding = self.embeddings[variant.term]
                weight = variant.weight * variant.frequency

                if weighted_sum is None:
                    weighted_sum = embedding * weight
                else:
                    weighted_sum += embedding * weight

                total_weight += weight

        if weighted_sum is not None and total_weight > 0:
            self._unified_embedding = weighted_sum / total_weight

        return self._unified_embedding

    def get_best_match(self, candidate_embedding: np.ndarray,
                      semantic_engine) -> tuple[str, float]:
        """Find best matching variant for a candidate embedding.

        Args:
            candidate_embedding: Embedding of candidate term
            semantic_engine: Engine with cosine_similarity method

        Returns:
            Tuple of (best_term, similarity_score)
        """
        best_term = None
        best_score = 0.0

        for variant in self.variants:
            if variant.term in self.embeddings:
                variant_emb = self.embeddings[variant.term]

                # Compute similarity
                similarity = semantic_engine.cosine_similarity(
                    candidate_embedding, variant_emb
                )

                # Weight by variant authority
                weighted_score = similarity * variant.weight

                if weighted_score > best_score:
                    best_score = weighted_score
                    best_term = variant.term

        # If no match found, use core term
        if best_term is None and self.core_term:
            best_term = self.core_term
            best_score = 0.0

        return best_term, best_score

    def merge(self, other: 'SemanticCluster'):
        """Merge another cluster into this one.

        Args:
            other: Another SemanticCluster for the same Strong's number
        """
        if other.strong_num != self.strong_num:
            raise ValueError(
                f"Cannot merge clusters with different Strong's numbers: "
                f"{self.strong_num} != {other.strong_num}"
            )

        # Merge variants
        for variant in other.variants:
            self.add_variant(
                variant.term,
                variant.source,
                variant.frequency
            )

        # Merge embeddings
        for term, embedding in other.embeddings.items():
            if term not in self.embeddings:
                self.embeddings[term] = embedding

    def __repr__(self) -> str:
        """String representation of the cluster."""
        terms = self.get_all_terms()
        return (f"SemanticCluster(strong_num='{self.strong_num}', "
                f"core_term='{self.core_term}', "
                f"variants={len(self.variants)}, "
                f"terms={terms[:3]}{'...' if len(terms) > 3 else ''})")
