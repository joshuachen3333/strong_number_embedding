"""Unit tests for BoundaryCorrector (T016-T020)."""

import pytest
from src.core.boundary_corrector import BoundaryCorrector, CorrectionMetrics


class TestBoundaryCorrector:
    """Test suite for boundary correction using UNV+SN reference."""

    def setup_method(self):
        """Set up test fixtures."""
        self.corrector = BoundaryCorrector()

    # T016: Basic correction workflow
    def test_basic_correction(self):
        """T016: Correct target segmentation using UNV+SN boundaries."""
        target_text = "上帝愛世人"
        initial_segments = ["上帝", "愛", "世", "人"]
        unv_sn_text = "神<G2316>愛<G25>世人<G2889>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # "愛" and "世人" should be corrected based on UNV+SN
        assert "愛" in corrected
        assert "世人" in corrected
        # Verify metrics
        assert metrics.unv_sn_terms_count == 3
        assert metrics.matched_terms_count == 2  # "愛" and "世人"

    def test_no_changes_needed(self):
        """T016: No correction when initial segmentation is already correct."""
        target_text = "起初上帝創造天地。"
        initial_segments = ["起初", "上帝", "創造", "天地", "。"]
        unv_sn_text = "起初<H07225>神<H0430>創造<H01254>天<H08064>地<H0776>。"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # "起初" and "創造" match, but boundaries already correct
        assert "起初" in corrected
        assert "創造" in corrected
        assert "。" in corrected  # Punctuation preserved

    def test_complex_verse(self):
        """T016: Handle complex verse with multiple corrections."""
        target_text = "甚至賜下獨生子"
        initial_segments = ["甚至", "賜", "下獨", "生子"]
        unv_sn_text = "甚至<G5620>將他的獨生<G3439>子<G5207>賜給<G1325>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # "甚至" matches and should be preserved
        assert "甚至" in corrected
        # "子" should be independent based on G5207
        assert "子" in corrected
        # Verify text preserved
        assert ''.join(corrected) == target_text

    # T017: Text preservation
    def test_text_preservation(self):
        """T017: Target version text must be preserved exactly."""
        target_text = "上帝這樣地愛世人，甚至賜下獨生子。"
        initial_segments = ["上帝", "這樣", "地", "愛", "世人", "，", "甚至", "賜", "下獨", "生子", "。"]
        unv_sn_text = "神<G2316>愛<G25>{}世人<G2889>，甚至<G5620>將他的獨生<G3439>子<G5207>。"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # Reconstruct and verify
        reconstructed = ''.join(corrected)
        assert reconstructed == target_text, \
            f"Text changed: '{target_text}' → '{reconstructed}'"

    def test_lcc_stays_lcc(self):
        """T017: LCC text stays LCC, never becomes UNV."""
        target_text = "上帝愛世人"  # LCC uses "上帝"
        initial_segments = ["上帝", "愛", "世", "人"]
        unv_sn_text = "神<G2316>愛<G25>世人<G2889>"  # UNV uses "神"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # "上帝" should remain (no match with "神")
        # Only "愛" and "世人" are corrected
        reconstructed = ''.join(corrected)
        assert "上帝" in reconstructed  # LCC text preserved
        assert "神" not in reconstructed  # UNV text NOT introduced

    # T018: Punctuation preservation
    def test_punctuation_independent(self):
        """T018: All punctuation marks should be independent segments."""
        target_text = "起初上帝創造天地。"
        initial_segments = ["起初", "上帝", "創造", "天地。"]  # Period attached
        unv_sn_text = "起初<H07225>神<H0430>創造<H01254>天<H08064>地<H0776>。"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # Period should be independent
        assert "。" in corrected
        # Verify text preserved
        assert ''.join(corrected) == target_text

    def test_chinese_punctuation(self):
        """T018: Handle all Chinese punctuation marks."""
        target_text = "愛世人，甚至：信他！得永生？「阿們」『哈利路亞』"
        initial_segments = ["愛世人，", "甚至：", "信他！", "得永生？", "「阿們」", "『哈利路亞』"]
        unv_sn_text = "愛<G25>世人<G2889>，甚至<G5620>：信<G4100>他<G846>！得<G2192>永生<G2222>？「阿們」『哈利路亞』"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # All punctuation should be independent
        assert "，" in corrected
        assert "：" in corrected
        assert "！" in corrected
        assert "？" in corrected
        assert "「" in corrected
        assert "」" in corrected
        assert "『" in corrected
        assert "』" in corrected
        # Verify text preserved
        assert ''.join(corrected) == target_text

    def test_english_punctuation(self):
        """T018: Handle English punctuation marks."""
        target_text = "God loves (all) people."
        initial_segments = ["God", " ", "loves", " ", "(all)", " ", "people."]
        unv_sn_text = "God<G2316> loves<G25> (all<G3956>) people<G2889>."

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # Punctuation should be independent
        assert "(" in corrected
        assert ")" in corrected
        assert "." in corrected
        # Note: Whitespace is filtered out by corrector, so we check main text
        reconstructed = ''.join(corrected)
        assert "God" in reconstructed
        assert "loves" in reconstructed
        assert "all" in reconstructed
        assert "people" in reconstructed

    # T019: Metrics calculation
    def test_metrics_match_rate(self):
        """T019: Calculate match rate correctly."""
        target_text = "神愛世人"
        initial_segments = ["神", "愛", "世", "人"]
        unv_sn_text = "神<G2316>愛<G25>世人<G2889>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # 3 UNV terms: "神", "愛", "世人"
        assert metrics.unv_sn_terms_count == 3
        # All 3 matched in target
        assert metrics.matched_terms_count == 3
        # Match rate should be 100%
        assert metrics.character_match_rate == 100.0

    def test_metrics_partial_match(self):
        """T019: Calculate partial match rate."""
        target_text = "上帝愛世人"  # "上帝" ≠ "神"
        initial_segments = ["上帝", "愛", "世", "人"]
        unv_sn_text = "神<G2316>愛<G25>世人<G2889>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # 3 UNV terms
        assert metrics.unv_sn_terms_count == 3
        # Only 2 matched: "愛" and "世人"
        assert metrics.matched_terms_count == 2
        # Match rate should be ~66.7%
        assert 66 <= metrics.character_match_rate <= 67

    def test_metrics_corrections_count(self):
        """T019: Count actual boundary corrections."""
        target_text = "神愛世人"
        initial_segments = ["神", "愛", "世", "人"]  # "世人" incorrectly split
        unv_sn_text = "神<G2316>愛<G25>世人<G2889>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # "世人" should be corrected
        assert "世人" in corrected
        # Boundaries corrected count should be > 0
        assert metrics.corrected_boundaries_count > 0

    # T020: Edge cases
    def test_empty_target_text(self):
        """T020: Handle empty target text."""
        target_text = ""
        initial_segments = []
        unv_sn_text = "神<G2316>愛<G25>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        assert corrected == []
        assert metrics.matched_terms_count == 0

    def test_empty_unv_sn(self):
        """T020: Handle empty UNV+SN reference."""
        target_text = "上帝愛世人"
        initial_segments = ["上帝", "愛", "世人"]
        unv_sn_text = ""

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # With no UNV reference, corrector falls back to boundary positions
        # Text should still be preserved
        assert ''.join(corrected) == target_text
        assert metrics.unv_sn_terms_count == 0
        assert metrics.matched_terms_count == 0

    def test_no_matches(self):
        """T020: Handle case with no character matches."""
        target_text = "上帝這樣地"  # LCC text
        initial_segments = ["上帝", "這樣", "地"]
        unv_sn_text = "神<G2316>{<G3779>}"  # UNV text (completely different)

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # No matches, should keep initial
        assert metrics.matched_terms_count == 0
        assert ''.join(corrected) == target_text

    def test_special_markers(self):
        """T020: Handle special markers {}, [], etc."""
        target_text = "神愛世人"
        initial_segments = ["神", "愛", "世人"]
        unv_sn_text = "神<G2316>愛<G25>{<G3779>}世人<G2889>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # "{}" should be filtered out
        # Verify text preserved
        assert ''.join(corrected) == target_text

    def test_whitespace_handling(self):
        """T020: Handle text with whitespace."""
        target_text = "神 愛 世人"
        initial_segments = ["神", " ", "愛", " ", "世人"]
        unv_sn_text = "神<G2316>愛<G25>世人<G2889>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # Whitespace should be skipped, not preserved as segments
        # But text should still reconstruct correctly
        reconstructed = ''.join(corrected)
        # Whitespace might be normalized, but main text preserved
        assert "神" in reconstructed
        assert "愛" in reconstructed
        assert "世人" in reconstructed

    def test_multiple_consecutive_tags(self):
        """T020: Handle terms with multiple Strong's Numbers."""
        target_text = "起初創造"
        initial_segments = ["起初", "創造"]
        unv_sn_text = "起初<WAH09002><WH07225>創造<WH01254><WTH8804>"

        corrected, metrics = self.corrector.correct(
            target_text, initial_segments, unv_sn_text
        )

        # Both terms should be matched
        assert "起初" in corrected
        assert "創造" in corrected
        assert ''.join(corrected) == target_text
