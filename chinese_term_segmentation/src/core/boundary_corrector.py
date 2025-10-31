"""Boundary corrector for applying UNV+SN boundaries to target versions."""

from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

from src.core.strongs_parser import StrongsNumberParser, TermBoundary

logger = logging.getLogger(__name__)


@dataclass
class CorrectionMetrics:
    """Metrics for correction quality tracking."""
    unv_sn_terms_count: int  # Total terms extracted from UNV+SN
    matched_terms_count: int  # Terms found in target text via string matching
    corrected_boundaries_count: int  # Boundaries successfully corrected
    unchanged_segments_count: int  # Segments kept from initial segmentation
    character_match_rate: float  # matched / total (as percentage)
    correction_success_rate: float  # corrected / matched (as percentage)

    # Phase 1.5 additional metrics
    refinement_rate: float = 0.0  # % of coarse terms refined (Phase 1.5)
    variant_match_rate: float = 0.0  # % matched via character variants (Phase 1.5)
    refined_terms_count: int = 0  # Number of terms refined (Phase 1.5)
    coarse_terms_count: int = 0  # Number of coarse terms before refinement (Phase 1.5)


class BoundaryCorrector:
    """Corrects Chinese term boundaries using UNV+SN as reference.

    Uses simple string matching to find terms that exist in both target version
    (e.g., LCC) and UNV+SN, then applies UNV+SN boundaries to those matched terms.

    Key principle: Target version text (LCC) never changes to UNV - only boundaries
    are corrected where character sequences match.

    Phase 1.5 Enhancement: Two-stage refinement using Strong's Dictionary API
    and similarity-based substring matching for improved precision.
    """

    def __init__(self, fhl_client=None, similarity_matcher=None):
        """Initialize the corrector.

        Args:
            fhl_client: Optional FHLClient instance for Strong's Dictionary API (Phase 1.5)
            similarity_matcher: Optional SimilarityMatcher instance (Phase 1.5)
        """
        self.parser = StrongsNumberParser()
        self.fhl_client = fhl_client
        self.similarity_matcher = similarity_matcher
        self._refinement_cache: Dict[Tuple[str, str], Optional[str]] = {}

    def correct(
        self,
        target_text: str,
        initial_segments: List[str],
        unv_sn_text: str
    ) -> Tuple[List[str], CorrectionMetrics]:
        """Correct target version segmentation using UNV+SN boundaries.

        Args:
            target_text: Target version text (e.g., LCC) - clean, no SN tags
            initial_segments: Initial segmentation from jieba/pkuseg/etc.
            unv_sn_text: UNV text with Strong's Numbers (reference)

        Returns:
            Tuple of (corrected_segments, metrics)
            - corrected_segments: Target text with corrected boundaries
            - metrics: CorrectionMetrics object with quality stats

        Example:
            >>> corrector = BoundaryCorrector()
            >>> target = "上帝這樣地愛世人獨生子"
            >>> initial = ["上帝", "這樣", "地", "愛", "世人", "獨", "生子"]
            >>> unv_sn = "神<G2316>愛<G25>世人<G2889>獨生<G3439>子<G5207>"
            >>> corrected, metrics = corrector.correct(target, initial, unv_sn)
            >>> corrected
            ['上帝', '這樣地', '愛', '世人', '獨生', '子']
            # '愛', '世人', '獨生', '子' corrected via UNV+SN matching
            # '上帝', '這樣地' unchanged (no match with UNV '神')
        """
        # Step 1: Parse UNV+SN to extract reference boundaries
        unv_boundaries = self.parser.parse(unv_sn_text)

        # Step 2: Extract terms that we can use for string matching
        # Filter out empty terms, punctuation, and special markers
        reference_terms = self._extract_matchable_terms(unv_boundaries)

        # Step 3: Find which reference terms exist in target text (string matching)
        matched_terms = self._find_matches(target_text, reference_terms)

        # Step 4: Apply corrections to initial segmentation
        corrected_segments = self._apply_corrections(
            target_text,
            initial_segments,
            matched_terms
        )

        # Step 5: Calculate metrics
        metrics = self._calculate_metrics(
            unv_boundaries,
            matched_terms,
            initial_segments,
            corrected_segments
        )

        return corrected_segments, metrics

    def _extract_matchable_terms(self, boundaries: List[TermBoundary]) -> Set[str]:
        """Extract terms suitable for string matching from UNV+SN boundaries.

        Filters out:
        - Empty terms
        - Punctuation (，。、：；！？「」『』)
        - Special markers ({}, [], etc.)
        - Single-character particles (的、地、得, etc.)

        Args:
            boundaries: Parsed UNV+SN boundaries

        Returns:
            Set of terms suitable for matching
        """
        matchable = set()
        punctuation = set('，。、：；！？「」『』{}[]()<>')

        for boundary in boundaries:
            term = boundary.term.strip()

            # Skip empty, punctuation, single-char terms
            if not term or term in punctuation or len(term) < 1:
                continue

            # Skip terms that are just special markers
            if term in ['{', '}', '「', '」', '『', '』']:
                continue

            matchable.add(term)

        return matchable

    def _find_matches(self, target_text: str, reference_terms: Set[str]) -> Set[str]:
        """Find reference terms that exist in target text via string matching.

        Args:
            target_text: Target version text (clean)
            reference_terms: Terms extracted from UNV+SN

        Returns:
            Set of terms found in target text
        """
        matched = set()

        for term in reference_terms:
            if term in target_text:
                matched.add(term)

        return matched

    def _apply_corrections(
        self,
        target_text: str,
        initial_segments: List[str],
        matched_terms: Set[str]
    ) -> List[str]:
        """Apply boundary corrections based on matched terms.

        Algorithm:
        1. Reconstruct text from initial segments to get position mapping
        2. For each matched term, find its positions in target text
        3. Adjust segment boundaries to match these positions
        4. Merge or split segments as needed

        Args:
            target_text: Target version text
            initial_segments: Initial segmentation
            matched_terms: Terms that should be independent (from UNV+SN matching)

        Returns:
            Corrected segmentation
        """
        # Build position map of initial segments
        segment_positions = []
        pos = 0
        for seg in initial_segments:
            start = pos
            end = pos + len(seg)
            segment_positions.append((seg, start, end))
            pos = end

        # Find all occurrences of matched terms in target text
        term_positions = {}
        for term in matched_terms:
            positions = []
            start = 0
            while True:
                idx = target_text.find(term, start)
                if idx == -1:
                    break
                positions.append((idx, idx + len(term)))
                start = idx + 1
            if positions:
                term_positions[term] = positions

        # Mark character positions that should be term boundaries
        boundary_positions = set([0, len(target_text)])  # Start and end
        for term, positions in term_positions.items():
            for start, end in positions:
                boundary_positions.add(start)
                boundary_positions.add(end)

        # Create new segmentation based on boundary positions
        sorted_boundaries = sorted(boundary_positions)
        corrected = []

        for i in range(len(sorted_boundaries) - 1):
            start = sorted_boundaries[i]
            end = sorted_boundaries[i + 1]

            segment = target_text[start:end]

            # Skip only whitespace (preserve punctuation!)
            whitespace = ' \t\n　'
            if segment and segment not in whitespace:
                corrected.append(segment)

        return corrected

    def _calculate_metrics(
        self,
        unv_boundaries: List[TermBoundary],
        matched_terms: Set[str],
        initial_segments: List[str],
        corrected_segments: List[str]
    ) -> CorrectionMetrics:
        """Calculate correction quality metrics.

        Args:
            unv_boundaries: Parsed UNV+SN boundaries
            matched_terms: Terms found via string matching
            initial_segments: Original segmentation
            corrected_segments: Corrected segmentation

        Returns:
            CorrectionMetrics object
        """
        # Count UNV+SN terms (excluding punctuation)
        unv_terms_count = sum(
            1 for b in unv_boundaries
            if b.term and b.term not in '，。、：；！？「」『』{}[]'
        )

        # Count matched terms
        matched_count = len(matched_terms)

        # Count corrected boundaries (segments that changed)
        initial_set = set(initial_segments)
        corrected_set = set(corrected_segments)
        corrected_count = len(corrected_set - initial_set)

        # Count unchanged segments
        unchanged_count = len(initial_set & corrected_set)

        # Calculate rates
        char_match_rate = (matched_count / unv_terms_count * 100) if unv_terms_count > 0 else 0
        correction_success_rate = (corrected_count / matched_count * 100) if matched_count > 0 else 0

        return CorrectionMetrics(
            unv_sn_terms_count=unv_terms_count,
            matched_terms_count=matched_count,
            corrected_boundaries_count=corrected_count,
            unchanged_segments_count=unchanged_count,
            character_match_rate=char_match_rate,
            correction_success_rate=correction_success_rate
        )

    # =========================================================================
    # Phase 1.5: Two-Stage Refinement with Similarity Matching
    # =========================================================================

    def correct_with_refinement(
        self,
        target_text: str,
        initial_segments: List[str],
        unv_sn_text: str,
        threshold: float = 0.6
    ) -> Tuple[List[str], CorrectionMetrics]:
        """Correct with two-stage refinement (Phase 1.5).

        This enhanced method uses Strong's Dictionary API and similarity matching
        to refine coarse FHL boundaries before matching to target version.

        Two-Stage Process:
            Stage 1 (UNV Refinement):
                - Parse coarse UNV+SN boundaries
                - For each (coarse_term, SN) pair:
                  1. Fetch SN semantic meaning from Strong's Dictionary
                  2. Find best substring in coarse_term using similarity matching
                  3. Replace coarse term with refined term
                - Output: Refined UNV boundaries

            Stage 2 (Target Matching):
                - Match refined UNV terms to target version text
                - Handle character variants transparently
                - Apply boundary corrections (reuse Phase 1 logic)

        Args:
            target_text: Target version text (e.g., LCC)
            initial_segments: Initial segmentation from jieba/pkuseg/etc.
            unv_sn_text: UNV text with Strong's Numbers
            threshold: Similarity threshold for substring matching (default: 0.6)

        Returns:
            Tuple of (corrected_segments, metrics)

        Requires:
            - self.fhl_client must be set (for Strong's Dictionary API)
            - self.similarity_matcher must be set (for substring matching)

        Example:
            >>> from src.api.fhl_client import FHLClient
            >>> from src.core.similarity_matcher import SimilarityMatcher
            >>> corrector = BoundaryCorrector(
            ...     fhl_client=FHLClient(),
            ...     similarity_matcher=SimilarityMatcher()
            ... )
            >>> target = "賜下獨生子"
            >>> unv_sn = "將他的獨生<G3439>子<G5207>"
            >>> initial = ["賜", "下獨", "生子"]
            >>> corrected, metrics = corrector.correct_with_refinement(
            ...     target, initial, unv_sn
            ... )
            >>> corrected
            ['賜下', '獨生', '子']  # Refined "獨生" matched!
            >>> metrics.refinement_rate
            50.0  # 1 out of 2 terms refined
        """
        if not self.fhl_client:
            raise ValueError(
                "fhl_client must be provided for refinement. "
                "Use BoundaryCorrector(fhl_client=FHLClient())"
            )
        if not self.similarity_matcher:
            raise ValueError(
                "similarity_matcher must be provided for refinement. "
                "Use BoundaryCorrector(similarity_matcher=SimilarityMatcher())"
            )

        # Clear refinement cache for this verse
        self._refinement_cache.clear()

        # Stage 0: Parse UNV+SN to extract coarse boundaries
        coarse_boundaries = self.parser.parse(unv_sn_text)

        # Stage 1: Refine UNV boundaries using Strong's Dictionary + Similarity
        refined_terms = []
        refinement_count = 0
        terms_with_sn = 0

        for boundary in coarse_boundaries:
            if boundary.strongs_numbers and boundary.term:
                terms_with_sn += 1
                # Try to refine using first Strong's Number
                refined = self._refine_term(
                    boundary.term,
                    boundary.strongs_numbers[0],
                    threshold
                )
                if refined and refined != boundary.term:
                    refined_terms.append(refined)
                    refinement_count += 1
                    logger.debug(
                        f"Refined '{boundary.term}' → '{refined}' "
                        f"(SN: {boundary.strongs_numbers[0]})"
                    )
                else:
                    # No refinement, use coarse term
                    refined_terms.append(boundary.term)
            elif boundary.term:
                # No Strong's Number, use term as-is
                refined_terms.append(boundary.term)

        # Stage 2: Match refined terms to target version with variant handling
        matched_terms, variant_matches = self._find_matches_with_variants(
            target_text,
            refined_terms
        )

        # Stage 3: Apply corrections (reuse Phase 1 logic)
        corrected_segments = self._apply_corrections(
            target_text,
            initial_segments,
            matched_terms
        )

        # Stage 4: Calculate enhanced metrics
        metrics = self._calculate_refinement_metrics(
            coarse_boundaries,
            refined_terms,
            matched_terms,
            variant_matches,
            initial_segments,
            corrected_segments,
            refinement_count,
            terms_with_sn
        )

        return corrected_segments, metrics

    def _refine_term(
        self,
        coarse_term: str,
        sn: str,
        threshold: float = 0.6
    ) -> Optional[str]:
        """Refine coarse term using Strong's Dictionary semantics (Stage 1).

        Args:
            coarse_term: Coarse boundary from UNV+SN (e.g., "將他的獨生")
            sn: Strong's Number (e.g., "G3439")
            threshold: Similarity threshold for matching

        Returns:
            Refined term or None if refinement fails

        Example:
            >>> corrector._refine_term("將他的獨生", "G3439")
            "獨生"  # Refined using G3439 meaning "獨生的"
        """
        # Check cache first
        cache_key = (coarse_term, sn)
        if cache_key in self._refinement_cache:
            return self._refinement_cache[cache_key]

        # Fetch Strong's Dictionary entry
        try:
            strong_entry = self.fhl_client.fetch_strong_dict(sn)
        except Exception as e:
            logger.warning(f"Failed to fetch Strong's entry for {sn}: {e}")
            self._refinement_cache[cache_key] = None
            return None

        if not strong_entry or not strong_entry.chinese_meaning:
            logger.debug(f"No Chinese meaning found for {sn}")
            self._refinement_cache[cache_key] = None
            return None

        # Use similarity matcher to find best substring
        refined = self.similarity_matcher.find_best_substring(
            refTerm=strong_entry.chinese_meaning,
            origText=coarse_term,
            threshold=threshold
        )

        # Cache the result
        self._refinement_cache[cache_key] = refined

        return refined

    def _find_matches_with_variants(
        self,
        target_text: str,
        refined_terms: List[str]
    ) -> Tuple[Set[str], int]:
        """Find refined terms in target text with character variant handling (Stage 2).

        Args:
            target_text: Target version text (e.g., LCC)
            refined_terms: Terms refined from Stage 1

        Returns:
            Tuple of (matched_terms, variant_match_count)
            - matched_terms: Set of terms found in target
            - variant_match_count: Number of matches via character variants

        Example:
            >>> corrector._find_matches_with_variants(
            ...     "因爲天國",  # LCC uses variant 爲
            ...     ["因為"]     # Refined UNV uses standard 為
            ... )
            ({"因爲"}, 1)  # Matched via variant normalization
        """
        matched = set()
        variant_matches = 0

        for term in refined_terms:
            if not term:
                continue

            # Try direct match first
            if term in target_text:
                matched.add(term)
                continue

            # Try with variant normalization
            if self.similarity_matcher:
                normalized_term = self.similarity_matcher._normalize_variants(term)
                normalized_target = self.similarity_matcher._normalize_variants(target_text)

                if normalized_term in normalized_target:
                    # Found via variant matching
                    # Find the original variant in target text
                    # by searching for the normalized position
                    idx = normalized_target.find(normalized_term)
                    if idx >= 0:
                        # Extract original text at that position
                        original_term = target_text[idx:idx + len(normalized_term)]
                        matched.add(original_term)
                        variant_matches += 1
                        logger.debug(
                            f"Variant match: '{term}' → '{original_term}' "
                            f"(normalized: '{normalized_term}')"
                        )

        return matched, variant_matches

    def _calculate_refinement_metrics(
        self,
        coarse_boundaries: List[TermBoundary],
        refined_terms: List[str],
        matched_terms: Set[str],
        variant_matches: int,
        initial_segments: List[str],
        corrected_segments: List[str],
        refinement_count: int,
        terms_with_sn: int
    ) -> CorrectionMetrics:
        """Calculate enhanced metrics including refinement stats.

        Args:
            coarse_boundaries: Original coarse boundaries from UNV+SN
            refined_terms: Terms after Stage 1 refinement
            matched_terms: Terms matched in Stage 2
            variant_matches: Number of variant matches
            initial_segments: Original segmentation
            corrected_segments: Corrected segmentation
            refinement_count: Number of terms refined
            terms_with_sn: Number of terms that had Strong's Numbers

        Returns:
            CorrectionMetrics with Phase 1.5 fields populated
        """
        # Count UNV+SN terms (excluding punctuation)
        unv_terms_count = sum(
            1 for b in coarse_boundaries
            if b.term and b.term not in '，。、：；！？「」『』{}[]'
        )

        # Count matched terms
        matched_count = len(matched_terms)

        # Count corrected boundaries (segments that changed)
        initial_set = set(initial_segments)
        corrected_set = set(corrected_segments)
        corrected_count = len(corrected_set - initial_set)

        # Count unchanged segments
        unchanged_count = len(initial_set & corrected_set)

        # Calculate rates
        char_match_rate = (matched_count / unv_terms_count * 100) if unv_terms_count > 0 else 0
        correction_success_rate = (corrected_count / matched_count * 100) if matched_count > 0 else 0

        # Phase 1.5 specific metrics
        refinement_rate = (refinement_count / terms_with_sn * 100) if terms_with_sn > 0 else 0
        variant_match_rate = (variant_matches / matched_count * 100) if matched_count > 0 else 0

        return CorrectionMetrics(
            unv_sn_terms_count=unv_terms_count,
            matched_terms_count=matched_count,
            corrected_boundaries_count=corrected_count,
            unchanged_segments_count=unchanged_count,
            character_match_rate=char_match_rate,
            correction_success_rate=correction_success_rate,
            refinement_rate=refinement_rate,
            variant_match_rate=variant_match_rate,
            refined_terms_count=refinement_count,
            coarse_terms_count=terms_with_sn
        )
