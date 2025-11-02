"""RefTerm Semantic Engine for RefTerm-based refinement.

This module provides the core semantic matching engine that uses RefTerms
from UNV+SN as the authoritative baseline, eliminating dictionary dependency.

Architecture Note:
    This engine REUSES SimilarityMatcher from Phase 2.1 to avoid code duplication.
    RefTermSemanticEngine focuses on RefTerm-specific logic (clustering, caching)
    while delegating the core matching algorithm to SimilarityMatcher.
"""

import numpy as np
import logging
from typing import List, Tuple, Dict, Optional
from functools import lru_cache

from .semantic_cluster import SemanticCluster
from .refterm_extractor import RefTerm
from .similarity_matcher import SimilarityMatcher


class RefTermSemanticEngine:
    """Core semantic matching using RefTerms as baseline.

    This engine matches RefTerms from UNV+SN directly against target text
    segments using neural embeddings, without relying on external dictionaries.

    Features:
    - Direct RefTerm-to-segment matching
    - Semantic clustering for variant handling
    - LRU caching for embeddings
    - Configurable similarity thresholds

    Example:
        >>> from src.core.engines import SentenceTransformerEngine
        >>> base_engine = SentenceTransformerEngine()
        >>> refterm_engine = RefTermSemanticEngine(base_engine)
        >>> refterm = RefTerm("神", "H0430", "神<WH0430>")
        >>> candidates = ["上", "帝", "上帝"]
        >>> best, score = refterm_engine.find_best_match(refterm, candidates)
        >>> print(f"Best match: {best} (score: {score:.2f})")
        Best match: 上帝 (score: 0.92)
    """

    def __init__(self,
                 base_engine,
                 similarity_threshold: float = 0.6,
                 max_segment_length: int = 4,
                 cache_size: int = 10000):
        """Initialize RefTermSemanticEngine.

        Args:
            base_engine: Base semantic engine (e.g., SentenceTransformerEngine)
            similarity_threshold: Minimum similarity for matches (default: 0.6)
            max_segment_length: Maximum chars per segment combination (default: 4)
            cache_size: Maximum RefTerm embeddings to cache (default: 10000)
        """
        self.base_engine = base_engine
        self.similarity_threshold = similarity_threshold
        self.max_segment_length = max_segment_length
        self.cache_size = cache_size

        # REUSE: SimilarityMatcher from Phase 2.1 (avoid code duplication)
        self.similarity_matcher = SimilarityMatcher(engine=base_engine)

        # RefTerm embedding cache (separate from base engine cache)
        self._refterm_cache: Dict[str, np.ndarray] = {}

        # Cluster cache
        self._cluster_cache: Dict[str, SemanticCluster] = {}

        # Logging
        self.logger = logging.getLogger(__name__)

    def encode_refterm(self, refterm: str) -> np.ndarray:
        """Encode RefTerm with caching.

        Args:
            refterm: RefTerm text (e.g., "神", "知道")

        Returns:
            Embedding vector

        Note:
            Uses separate cache from base engine for RefTerms.
        """
        if refterm in self._refterm_cache:
            return self._refterm_cache[refterm]

        # Encode using base engine
        embedding = self.base_engine.get_embedding(refterm)

        # Cache if space available
        if len(self._refterm_cache) < self.cache_size:
            self._refterm_cache[refterm] = embedding

        return embedding

    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Cosine similarity score in [0, 1]
        """
        # Normalize vectors
        emb1_norm = emb1 / (np.linalg.norm(emb1) + 1e-10)
        emb2_norm = emb2 / (np.linalg.norm(emb2) + 1e-10)

        # Compute dot product (cosine similarity for normalized vectors)
        similarity = np.dot(emb1_norm, emb2_norm)

        # Ensure [0, 1] range (cosine can be [-1, 1])
        return max(0.0, min(1.0, float(similarity)))

    def find_best_match(self,
                       refterm: RefTerm,
                       candidate_segments: List[str]) -> Tuple[Optional[str], float]:
        """Find best matching candidate segment for a RefTerm.

        ARCHITECTURE: Delegates to SimilarityMatcher (Phase 2.1) to avoid code duplication.
        This method focuses on RefTerm-specific preprocessing and postprocessing.

        Args:
            refterm: RefTerm from UNV+SN
            candidate_segments: List of candidate segments from target text

        Returns:
            Tuple of (best_match, similarity_score)
            Returns (None, 0.0) if no match above threshold

        Example:
            >>> refterm = RefTerm("神", "H0430", "神<WH0430>")
            >>> candidates = ["上", "帝", "上帝"]
            >>> best, score = engine.find_best_match(refterm, candidates)
            >>> (best, score)
            ('上帝', 0.92)
        """
        # Convert segment list to continuous text for SimilarityMatcher
        origText = ''.join(candidate_segments)

        # Limit origText length to max_segment_length to avoid over-matching
        # This ensures we don't match phrases that span too many segments
        if len(origText) > self.max_segment_length:
            # Try each sliding window of max length
            best_match = None
            best_score = 0.0

            for i in range(len(origText) - self.max_segment_length + 1):
                window = origText[i:i + self.max_segment_length]
                match = self.similarity_matcher.find_best_substring(
                    refTerm=refterm.term,
                    origText=window,
                    threshold=self.similarity_threshold
                )
                if match:
                    score = self.base_engine.similarity(refterm.term, match)
                    if score > best_score:
                        best_score = score
                        best_match = match

            if best_match:
                return best_match, best_score
            return None, 0.0

        # REUSE: Delegate to SimilarityMatcher (avoid duplicating matching logic)
        best_match = self.similarity_matcher.find_best_substring(
            refTerm=refterm.term,
            origText=origText,
            threshold=self.similarity_threshold
        )

        if best_match:
            # Calculate confidence score
            score = self.base_engine.similarity(refterm.term, best_match)
            return best_match, score

        return None, 0.0

    def build_semantic_cluster(self,
                              strong_num: str,
                              refterms: List[RefTerm]) -> SemanticCluster:
        """Build semantic cluster from multiple RefTerms.

        This groups translation variants for robust matching.

        Args:
            strong_num: Strong's number (e.g., "H0430")
            refterms: List of RefTerms for this Strong's number

        Returns:
            SemanticCluster with all variants

        Example:
            >>> refterms = [
            ...     RefTerm("神", "H0430", "神<WH0430>"),
            ...     RefTerm("上帝", "H0430", "上帝<WH0430>")
            ... ]
            >>> cluster = engine.build_semantic_cluster("H0430", refterms)
            >>> cluster.get_all_terms()
            ['神', '上帝']
        """
        # Check cache
        if strong_num in self._cluster_cache:
            return self._cluster_cache[strong_num]

        # Create new cluster
        cluster = SemanticCluster(strong_num)

        # Add all refterms as variants
        term_counts = {}
        for refterm in refterms:
            if refterm.term not in term_counts:
                term_counts[refterm.term] = 0
            term_counts[refterm.term] += 1

        # Set most frequent as core term
        if term_counts:
            core_term = max(term_counts.items(), key=lambda x: x[1])[0]
            cluster.set_core_term(core_term, "UNV", term_counts[core_term])

            # Add other terms as variants
            for term, count in term_counts.items():
                if term != core_term:
                    cluster.add_variant(term, "UNV", count)

        # Compute embeddings for all terms
        cluster.compute_embeddings(self.base_engine)

        # Cache cluster
        self._cluster_cache[strong_num] = cluster

        return cluster

    def match_with_cluster(self,
                          cluster: SemanticCluster,
                          candidate_segments: List[str]) -> Tuple[Optional[str], float]:
        """Match candidate segments against a semantic cluster.

        ARCHITECTURE: Uses SimilarityMatcher for each cluster variant.

        Args:
            cluster: SemanticCluster for a Strong's number
            candidate_segments: Target text segments

        Returns:
            Tuple of (best_match, score)
        """
        # Convert segments to text
        origText = ''.join(candidate_segments)

        # Limit length for efficiency
        if len(origText) > self.max_segment_length:
            origText = origText[:self.max_segment_length]

        best_match = None
        best_score = 0.0

        # Try matching with each cluster variant
        for variant_term in cluster.get_all_terms():
            # REUSE: Use SimilarityMatcher for each variant
            match = self.similarity_matcher.find_best_substring(
                refTerm=variant_term,
                origText=origText,
                threshold=self.similarity_threshold
            )

            if match:
                score = self.base_engine.similarity(variant_term, match)
                if score > best_score:
                    best_score = score
                    best_match = match

        if best_score < self.similarity_threshold:
            return None, best_score

        return best_match, best_score

    def batch_encode(self, terms: List[str]) -> List[np.ndarray]:
        """Batch encode multiple terms for efficiency.

        Args:
            terms: List of terms to encode

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for term in terms:
            try:
                emb = self.base_engine.get_embedding(term)
                embeddings.append(emb)
            except ValueError:
                # Skip invalid terms
                self.logger.warning(f"Failed to encode term: {term}")
                continue

        return embeddings

    def get_cache_stats(self) -> Dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        base_stats = {}
        if hasattr(self.base_engine, 'get_cache_stats'):
            base_stats = self.base_engine.get_cache_stats()

        return {
            'refterm_cache_size': len(self._refterm_cache),
            'refterm_cache_capacity': self.cache_size,
            'cluster_cache_size': len(self._cluster_cache),
            'base_engine_stats': base_stats
        }

    def clear_cache(self):
        """Clear all caches."""
        self._refterm_cache.clear()
        self._cluster_cache.clear()

        if hasattr(self.base_engine, 'clear_cache'):
            self.base_engine.clear_cache()

        self.logger.info("All caches cleared")

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RefTermSemanticEngine("
            f"base={self.base_engine.get_name()}, "
            f"threshold={self.similarity_threshold}, "
            f"cache={len(self._refterm_cache)}/{self.cache_size})"
        )
