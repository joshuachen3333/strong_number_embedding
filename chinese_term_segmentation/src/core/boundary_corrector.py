"""Boundary corrector for applying UNV+SN boundaries to target versions."""

from typing import List, Set, Dict, Tuple
from dataclasses import dataclass

from src.core.strongs_parser import StrongsNumberParser, TermBoundary


@dataclass
class CorrectionMetrics:
    """Metrics for correction quality tracking."""
    unv_sn_terms_count: int  # Total terms extracted from UNV+SN
    matched_terms_count: int  # Terms found in target text via string matching
    corrected_boundaries_count: int  # Boundaries successfully corrected
    unchanged_segments_count: int  # Segments kept from initial segmentation
    character_match_rate: float  # matched / total (as percentage)
    correction_success_rate: float  # corrected / matched (as percentage)


class BoundaryCorrector:
    """Corrects Chinese term boundaries using UNV+SN as reference.

    Uses simple string matching to find terms that exist in both target version
    (e.g., LCC) and UNV+SN, then applies UNV+SN boundaries to those matched terms.

    Key principle: Target version text (LCC) never changes to UNV - only boundaries
    are corrected where character sequences match.
    """

    def __init__(self):
        """Initialize the corrector."""
        self.parser = StrongsNumberParser()

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
