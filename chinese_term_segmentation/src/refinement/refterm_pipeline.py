"""RefTerm Refinement Pipeline for term boundary refinement.

This module implements the complete RefTerm-based refinement pipeline
that eliminates dictionary dependency by using RefTerms as ground truth.
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from src.core.refterm_extractor import RefTermExtractor, RefTerm
from src.core.refterm_semantic_engine import RefTermSemanticEngine
from src.core.semantic_cluster import SemanticCluster


@dataclass
class RefinementResult:
    """Result of RefTerm refinement for a single term."""
    refterm: RefTerm  # Original RefTerm from UNV+SN
    refined_term: str  # Refined term from target text
    confidence: float  # Confidence score [0, 1]
    method: str  # "refterm" or "fallback"
    original_coarse: Optional[str] = None  # Original coarse segmentation


class RefTermRefinementPipeline:
    """Complete pipeline for RefTerm-based refinement.

    This pipeline:
    1. Extracts RefTerms from UNV+SN text
    2. Segments target text
    3. Matches RefTerms semantically with target segments
    4. Returns refined alignments

    Example:
        >>> from src.core.engines import SentenceTransformerEngine
        >>> base_engine = SentenceTransformerEngine()
        >>> pipeline = RefTermRefinementPipeline(base_engine)
        >>>
        >>> # Refine a verse
        >>> unv_text = "神<WH0430>說<WH0559>"
        >>> lcc_text = "上帝說"
        >>> lcc_segments = ["上", "帝", "說"]
        >>>
        >>> results = pipeline.refine_verse(unv_text, lcc_segments)
        >>> for r in results:
        ...     print(f"{r.refterm.term} ({r.refterm.strong_num}) → {r.refined_term} (conf: {r.confidence:.2f})")
        神 (H0430) → 上帝 (conf: 0.92)
        說 (H0559) → 說 (conf: 1.00)
    """

    def __init__(self,
                 base_engine,
                 similarity_threshold: float = 0.6,
                 fallback_dict_engine=None,
                 use_clustering: bool = True,
                 debug: bool = False):
        """Initialize RefTerm refinement pipeline.

        Args:
            base_engine: Base semantic engine (e.g., SentenceTransformerEngine)
            similarity_threshold: Minimum similarity for matches (default: 0.6)
            fallback_dict_engine: Optional dictionary-based engine for fallback
            use_clustering: Use semantic clustering (default: True)
            debug: Enable debug logging (default: False)
        """
        self.extractor = RefTermExtractor()
        self.semantic_engine = RefTermSemanticEngine(
            base_engine,
            similarity_threshold=similarity_threshold
        )
        self.fallback_dict_engine = fallback_dict_engine
        self.use_clustering = use_clustering
        self.debug = debug

        # Logging
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def refine_verse(self,
                    unv_sn_text: str,
                    target_segments: List[str]) -> List[RefinementResult]:
        """Refine a complete verse using RefTerm matching.

        Args:
            unv_sn_text: UNV text with Strong's numbers
            target_segments: Segmented target text (e.g., from pkuseg)

        Returns:
            List of RefinementResult objects

        Example:
            >>> unv_text = "因為<WH03588>神<WH0430>知道<WH03045>"
            >>> lcc_segments = ["因", "為", "上", "帝", "知", "道"]
            >>> results = pipeline.refine_verse(unv_text, lcc_segments)
        """
        # Extract RefTerms
        refterms = self.extractor.extract_terms(unv_sn_text)

        if self.debug:
            self.logger.debug(f"Extracted {len(refterms)} RefTerms")
            for rt in refterms:
                self.logger.debug(f"  {rt.term} ({rt.strong_num})")

        # Refine each RefTerm
        results = []
        used_segments = set()  # Track used segments to avoid overlaps

        for refterm in refterms:
            # Get available segments (not yet used)
            available_segments = [
                seg for i, seg in enumerate(target_segments)
                if i not in used_segments
            ]

            if not available_segments:
                # No segments left
                self.logger.warning(
                    f"No available segments for {refterm.term} ({refterm.strong_num})"
                )
                results.append(RefinementResult(
                    refterm=refterm,
                    refined_term=refterm.term,  # Fallback to RefTerm itself
                    confidence=0.0,
                    method="fallback"
                ))
                continue

            # Match RefTerm against available segments
            refined_term, confidence = self.semantic_engine.find_best_match(
                refterm, available_segments
            )

            if refined_term is None:
                # No match above threshold
                if self.fallback_dict_engine:
                    # Try dictionary fallback
                    refined_term, confidence = self._fallback_match(
                        refterm, available_segments
                    )
                    method = "fallback-dict"
                else:
                    # IMPORTANT: Cannot use RefTerm as-is! Must be substring of target text
                    # Return None to indicate no match found
                    refined_term = None
                    confidence = 0.0
                    method = "no-match"
            else:
                method = "refterm"

            # Mark segments as used
            if refined_term:
                # Find which segments were used
                for i, seg in enumerate(target_segments):
                    if i not in used_segments and seg in refined_term:
                        used_segments.add(i)

            results.append(RefinementResult(
                refterm=refterm,
                refined_term=refined_term,
                confidence=confidence,
                method=method
            ))

            if self.debug:
                self.logger.debug(
                    f"Refined: {refterm.term} → {refined_term} "
                    f"(conf: {confidence:.2f}, method: {method})"
                )

        return results

    def _fallback_match(self,
                       refterm: RefTerm,
                       segments: List[str]) -> Tuple[str, float]:
        """Fallback to dictionary-based matching.

        Args:
            refterm: RefTerm to match
            segments: Available segments

        Returns:
            Tuple of (term, confidence)
        """
        if not self.fallback_dict_engine:
            return refterm.term, 0.0

        # Use dictionary engine (implementation depends on existing system)
        # This is a placeholder for integration with existing dictionary system
        self.logger.debug(f"Using fallback for {refterm.term}")

        return refterm.term, 0.0

    def refine_batch(self,
                    verse_pairs: List[Tuple[str, List[str]]]) -> List[List[RefinementResult]]:
        """Batch refine multiple verses for efficiency.

        Args:
            verse_pairs: List of (unv_sn_text, target_segments) tuples

        Returns:
            List of refinement results for each verse

        Example:
            >>> verse_pairs = [
            ...     ("神<WH0430>說<WH0559>", ["上", "帝", "說"]),
            ...     ("神<WH0430>看<WH07200>", ["上", "帝", "看"])
            ... ]
            >>> batch_results = pipeline.refine_batch(verse_pairs)
        """
        results = []

        for unv_text, target_segs in verse_pairs:
            verse_results = self.refine_verse(unv_text, target_segs)
            results.append(verse_results)

        return results

    def build_corpus_knowledge(self, unv_verses: List[str]) -> Dict:
        """Build knowledge base from UNV+SN corpus.

        Scans corpus to learn Strong's-to-Chinese mappings.

        Args:
            unv_verses: List of UNV+SN verse texts

        Returns:
            Corpus knowledge map

        Example:
            >>> verses = [
            ...     "神<WH0430>說<WH0559>",
            ...     "神<WH0430>看<WH07200>"
            ... ]
            >>> knowledge = pipeline.build_corpus_knowledge(verses)
            >>> knowledge["H0430"]
            Counter({'神': 2})
        """
        corpus_map = self.extractor.build_corpus_map(unv_verses)

        self.logger.info(f"Built corpus knowledge from {len(unv_verses)} verses")
        self.logger.info(f"Learned mappings for {len(corpus_map)} Strong's numbers")

        return corpus_map

    def get_statistics(self) -> Dict:
        """Get pipeline statistics.

        Returns:
            Dictionary with pipeline metrics
        """
        cache_stats = self.semantic_engine.get_cache_stats()

        return {
            'semantic_engine': self.semantic_engine.__repr__(),
            'similarity_threshold': self.semantic_engine.similarity_threshold,
            'cache_stats': cache_stats
        }

    def clear_cache(self):
        """Clear all pipeline caches."""
        self.semantic_engine.clear_cache()
        self.logger.info("Pipeline caches cleared")
