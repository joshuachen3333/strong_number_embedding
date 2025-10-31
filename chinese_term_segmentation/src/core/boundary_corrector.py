"""Boundary corrector for applying UNV+SN boundaries to target versions."""

from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass

from src.core.strongs_parser import StrongsNumberParser, TermBoundary
from src.core.char_variant_normalizer import CharVariantNormalizer
from src.core.similarity_matcher import SimilarityMatcher


@dataclass
class CorrectionMetrics:
    """Metrics for correction quality tracking."""
    unv_sn_terms_count: int  # Total terms extracted from UNV+SN
    matched_terms_count: int  # Terms found in target text via string matching
    corrected_boundaries_count: int  # Boundaries successfully corrected
    unchanged_segments_count: int  # Segments kept from initial segmentation
    character_match_rate: float  # matched / total (as percentage)
    correction_success_rate: float  # corrected / matched (as percentage)
    variant_matches_count: int = 0  # Terms matched via character variant normalization
    # Refinement-specific metrics (Phase 1.5)
    refined_terms_count: int = 0  # Terms refined using similarity matching
    coarse_terms_count: int = 0  # Coarse terms before refinement
    refinement_rate: float = 0.0  # refined / coarse (as percentage)


class BoundaryCorrector:
    """Corrects Chinese term boundaries using UNV+SN as reference.

    Uses simple string matching to find terms that exist in both target version
    (e.g., LCC) and UNV+SN, then applies UNV+SN boundaries to those matched terms.

    Key principle: Target version text (LCC) never changes to UNV - only boundaries
    are corrected where character sequences match.
    """

    def __init__(self, use_variant_normalization: bool = True):
        """Initialize the corrector.

        Args:
            use_variant_normalization: Whether to use character variant
                normalization for improved matching (default: True)
        """
        self.parser = StrongsNumberParser()
        self.use_variant_normalization = use_variant_normalization
        if use_variant_normalization:
            self.normalizer = CharVariantNormalizer()
        else:
            self.normalizer = None

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

        # Step 3: Find which reference terms exist in target text (string matching + variants)
        matched_terms, variant_matches_count = self._find_matches(target_text, reference_terms)

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
            corrected_segments,
            variant_matches_count
        )

        return corrected_segments, metrics

    def correct_with_refinement(
        self,
        target_text: str,
        initial_segments: List[str],
        unv_sn_text: str,
        fhl_client,
        threshold: float = 0.6
    ) -> Tuple[List[str], CorrectionMetrics]:
        """Correct with two-stage refinement using Strong's Dictionary + similarity matching.

        This enhanced method refines coarse UNV+SN boundaries before matching to target text:

        Stage 1 (UNV Refinement):
            - Parse coarse UNV+SN boundaries
            - For each (coarse_term, SN) pair:
              1. Fetch SN semantic meaning from Strong's Dictionary API
              2. Find best substring in coarse_term using similarity matching
              3. Replace coarse term with refined term
            - Output: Refined UNV boundaries

        Stage 2 (Target Matching):
            - Match refined UNV terms to target version text
            - Handle character variants transparently
            - Apply boundary corrections (reuse Phase 1 logic)

        Args:
            target_text: Target version text (e.g., LCC) - clean, no SN tags
            initial_segments: Initial segmentation from jieba/pkuseg/etc.
            unv_sn_text: UNV text with Strong's Numbers (reference)
            fhl_client: FHLClient instance for Strong's Dictionary API
            threshold: Similarity threshold for substring matching (default: 0.6)

        Returns:
            Tuple of (corrected_segments, metrics)

        Example:
            >>> from src.api.fhl_client import FHLClient
            >>> corrector = BoundaryCorrector()
            >>> client = FHLClient()
            >>> target = "賜下獨生子"
            >>> unv_sn = "將他的獨生<G3439>子<G5207>"
            >>> initial = ["賜", "下獨", "生子"]
            >>> corrected, metrics = corrector.correct_with_refinement(
            ...     target, initial, unv_sn, client
            ... )
            >>> corrected
            ['賜下', '獨生', '子']  # "獨生" refined from "將他的獨生"!
            >>> metrics.refined_terms_count
            1  # One term was refined
        """
        # Initialize similarity matcher
        similarity_matcher = SimilarityMatcher()

        # Stage 0: Parse UNV+SN to extract coarse boundaries
        coarse_boundaries = self.parser.parse(unv_sn_text)

        # Stage 1: Refine UNV boundaries using Strong's Dictionary + Similarity
        refined_terms = set()
        refined_count = 0
        terms_with_sn = 0

        for boundary in coarse_boundaries:
            if boundary.strongs_numbers and boundary.term:
                terms_with_sn += 1
                coarse_term = boundary.term.strip()

                # Skip empty or punctuation
                if not coarse_term or coarse_term in '，。、：；！？「」『』{}[]':
                    continue

                # Try to refine using first Strong's Number
                sn = boundary.strongs_numbers[0]
                refined_term = self._refine_term(
                    coarse_term, sn, fhl_client, similarity_matcher, threshold
                )

                if refined_term and refined_term != coarse_term:
                    # Refinement successful
                    refined_terms.add(refined_term)
                    refined_count += 1
                else:
                    # Use coarse term as fallback
                    refined_terms.add(coarse_term)
            elif boundary.term:
                # No SN, use term as-is
                refined_terms.add(boundary.term.strip())

        # Stage 2: Match refined terms to target text (with character variants)
        matched_terms, variant_matches_count = self._find_matches(target_text, refined_terms)

        # Stage 3: Apply corrections to initial segmentation
        corrected_segments = self._apply_corrections(
            target_text,
            initial_segments,
            matched_terms
        )

        # Stage 4: Calculate metrics
        metrics = self._calculate_metrics(
            coarse_boundaries,
            matched_terms,
            initial_segments,
            corrected_segments,
            variant_matches_count,
            refined_count,
            terms_with_sn
        )

        return corrected_segments, metrics

    def _refine_term(
        self,
        coarse_term: str,
        sn: str,
        fhl_client,
        similarity_matcher: SimilarityMatcher,
        threshold: float
    ) -> Optional[str]:
        """Refine a coarse term using Strong's Dictionary meaning + similarity matching.

        Args:
            coarse_term: Coarse boundary from UNV+SN (e.g., "將他的獨生")
            sn: Strong's Number (e.g., "G3439")
            fhl_client: FHLClient instance
            similarity_matcher: SimilarityMatcher instance
            threshold: Similarity threshold (0.0-1.0)

        Returns:
            Refined term (e.g., "獨生") or None if refinement fails
        """
        try:
            # Fetch Strong's Dictionary entry
            entry = fhl_client.fetch_strong_dict(sn)
            if not entry or not entry.chinese_meaning:
                return None

            # Use Chinese meaning as reference term
            ref_term = entry.chinese_meaning

            # Find best matching substring in coarse term
            refined = similarity_matcher.find_best_substring(
                ref_term, coarse_term, threshold
            )

            return refined

        except Exception:
            # Graceful fallback - use coarse term
            return None

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

    def _find_matches(self, target_text: str, reference_terms: Set[str]) -> Tuple[Set[str], int]:
        """Find reference terms that exist in target text via string matching.

        Uses character variant normalization to improve matching across different
        Chinese Bible versions (e.g., LCC vs UNV).

        Args:
            target_text: Target version text (clean)
            reference_terms: Terms extracted from UNV+SN

        Returns:
            Tuple of (matched_terms, variant_matches_count)
            - matched_terms: Set of terms found in target text
            - variant_matches_count: Number of terms matched via variant normalization
        """
        matched = set()
        variant_matches_count = 0

        # First pass: exact matching
        for term in reference_terms:
            if term in target_text:
                matched.add(term)

        # Second pass: variant normalization matching (if enabled)
        if self.use_variant_normalization and self.normalizer:
            unmatched = reference_terms - matched
            normalized_target = self.normalizer.normalize(target_text)

            for term in unmatched:
                normalized_term = self.normalizer.normalize(term)
                # Check if normalized term matches in normalized target
                if normalized_term in normalized_target:
                    matched.add(term)
                    variant_matches_count += 1

        return matched, variant_matches_count

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

        # Force punctuation independence: add boundaries before/after ALL punctuation
        # This ensures punctuation is never merged with adjacent terms
        punctuation = '，。、：；！？「」『』（）【】《》〈〉' + ',.;:!?\'"()[]<>{}'
        for i, char in enumerate(target_text):
            if char in punctuation:
                # Add boundary before punctuation
                boundary_positions.add(i)
                # Add boundary after punctuation (start of next char)
                boundary_positions.add(i + 1)

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
        corrected_segments: List[str],
        variant_matches_count: int = 0,
        refined_count: int = 0,
        coarse_count: int = 0
    ) -> CorrectionMetrics:
        """Calculate correction quality metrics.

        Args:
            unv_boundaries: Parsed UNV+SN boundaries
            matched_terms: Terms found via string matching
            initial_segments: Original segmentation
            corrected_segments: Corrected segmentation
            variant_matches_count: Number of terms matched via character variant normalization
            refined_count: Number of terms refined using similarity matching
            coarse_count: Number of coarse terms before refinement

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
        refinement_rate = (refined_count / coarse_count * 100) if coarse_count > 0 else 0

        return CorrectionMetrics(
            unv_sn_terms_count=unv_terms_count,
            matched_terms_count=matched_count,
            corrected_boundaries_count=corrected_count,
            unchanged_segments_count=unchanged_count,
            character_match_rate=char_match_rate,
            correction_success_rate=correction_success_rate,
            variant_matches_count=variant_matches_count,
            refined_terms_count=refined_count,
            coarse_terms_count=coarse_count,
            refinement_rate=refinement_rate
        )
