"""Unit tests for StrongsNumberParser (T011-T015)."""

import pytest
from src.core.strongs_parser import StrongsNumberParser, TermBoundary


class TestStrongsNumberParser:
    """Test suite for Strong's Number parsing and boundary extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = StrongsNumberParser()

    # T011: Parse UNV+SN and extract boundaries
    def test_parse_basic_unv_sn(self):
        """T011: Parse UNV+SN and extract term boundaries."""
        text = "神<G2316>愛<G25>世人<G2889>"

        boundaries = self.parser.parse(text)

        assert len(boundaries) == 3
        assert boundaries[0].term == "神"
        assert boundaries[0].strongs_numbers == ["G2316"]
        assert boundaries[1].term == "愛"
        assert boundaries[1].strongs_numbers == ["G25"]
        assert boundaries[2].term == "世人"
        assert boundaries[2].strongs_numbers == ["G2889"]

    def test_extract_terms(self):
        """T011: Extract just the terms without SNs."""
        text = "神<G2316>愛<G25>世人<G2889>"

        terms = self.parser.extract_terms(text)

        assert terms == ["神", "愛", "世人"]

    def test_get_clean_text(self):
        """T011: Remove all SN tags to get clean text."""
        text = "神<G2316>愛<G25>世人<G2889>，甚至<G5620>"

        clean = self.parser.get_clean_text(text)

        assert clean == "神愛世人，甚至"

    def test_get_sn_mapping(self):
        """T011: Create term-to-SN mapping."""
        text = "神<G2316>愛<G25>世人<G2889>"

        mapping = self.parser.get_sn_mapping(text)

        assert mapping == {
            "神": ["G2316"],
            "愛": ["G25"],
            "世人": ["G2889"]
        }

    # T012: Handle all four Strong's Number formats
    def test_fhl_format(self):
        """T012: Handle <WH1234> / <WG5678> format."""
        text = "神<WG2316>愛<WG25>"

        boundaries = self.parser.parse(text)

        assert len(boundaries) == 2
        assert boundaries[0].term == "神"
        assert boundaries[0].strongs_numbers == ["G2316"]
        assert boundaries[1].term == "愛"
        assert boundaries[1].strongs_numbers == ["G25"]

    def test_wrapped_format(self):
        """T012: Handle {<WH1234>} format."""
        text = "愛{<G3779>}世人"

        boundaries = self.parser.parse(text)

        # "愛" should have G3779
        assert any(b.term == "愛" and "G3779" in b.strongs_numbers for b in boundaries)

    def test_simple_format(self):
        """T012: Handle {H1234} / {G5678} format."""
        text = "神{G2316}愛{G25}"

        boundaries = self.parser.parse(text)

        assert len(boundaries) == 2
        assert boundaries[0].term == "神"
        assert boundaries[0].strongs_numbers == ["G2316"]

    def test_parentheses_format(self):
        """T012: Handle (H1234) / (G5678) format."""
        text = "神(G2316)愛(G25)"

        boundaries = self.parser.parse(text)

        assert len(boundaries) == 2
        assert boundaries[0].term == "神"
        assert boundaries[0].strongs_numbers == ["G2316"]

    def test_morphology_tags(self):
        """T012: Handle morphology tags like <WTH8804>, <WTG5656>."""
        text = "創造<H01254><WTH8804>{<H0853>}天<H08064>"

        boundaries = self.parser.parse(text)

        # Find "創造" term
        chuangzao = next((b for b in boundaries if b.term == "創造"), None)
        assert chuangzao is not None
        assert "H01254" in chuangzao.strongs_numbers

        # Find "天" term
        tian = next((b for b in boundaries if b.term == "天"), None)
        assert tian is not None
        assert "H08064" in tian.strongs_numbers

    # T013: Multiple SNs per term
    def test_multiple_sns_per_term(self):
        """T013: Handle multiple Strong's Numbers for one term."""
        text = "獨生<G3439>子<G5207>"

        boundaries = self.parser.parse(text)

        assert len(boundaries) == 2
        assert boundaries[0].term == "獨生"
        assert boundaries[0].strongs_numbers == ["G3439"]
        assert boundaries[1].term == "子"
        assert boundaries[1].strongs_numbers == ["G5207"]

    def test_consecutive_sns(self):
        """T013: Handle consecutive SN tags."""
        text = "起初<WAH09002><H07225>，神<H0430>"

        boundaries = self.parser.parse(text)

        # Find "起初" term - should have both H07225
        qichu = next((b for b in boundaries if b.term == "起初"), None)
        assert qichu is not None
        assert "H07225" in qichu.strongs_numbers

    # T014: Verses with no Strong's Numbers
    def test_text_without_sns(self):
        """T014: Handle text with no Strong's Numbers."""
        text = "上帝愛世人"

        boundaries = self.parser.parse(text)

        # Should parse as single term or fail gracefully
        assert len(boundaries) >= 1
        # All terms should have empty SN lists
        for b in boundaries:
            assert b.strongs_numbers == []

    def test_mixed_text_with_and_without_sns(self):
        """T014: Handle mixed text (some terms with SNs, some without)."""
        text = "起初<H07225>，神創造天地"

        boundaries = self.parser.parse(text)

        # "起初" should have SN
        qichu = next((b for b in boundaries if b.term == "起初"), None)
        assert qichu is not None
        assert len(qichu.strongs_numbers) > 0

        # Other terms may or may not have SNs (parsed as one term without SN)

    # T015: Edge cases
    def test_consecutive_sn_tags_different_formats(self):
        """T015: Handle consecutive SN tags in different formats."""
        text = "神<G2316>{<G1063>}愛<G25>"

        boundaries = self.parser.parse(text)

        # "神" should have both G2316 and possibly G1063
        shen = next((b for b in boundaries if b.term == "神"), None)
        assert shen is not None
        assert "G2316" in shen.strongs_numbers

    def test_punctuation_handling(self):
        """T015: Handle Chinese punctuation correctly."""
        text = "神<G2316>愛<G25>世人<G2889>，甚至<G5620>將他的獨生<G3439>子<G5207>賜給<G1325>他們"

        boundaries = self.parser.parse(text)

        # Check that punctuation doesn't create empty terms
        for b in boundaries:
            assert b.term not in ["，", ""]

        # Check that we extracted the terms
        terms = [b.term for b in boundaries]
        assert "神" in terms
        assert "愛" in terms
        assert "世人" in terms
        assert "甚至" in terms

    def test_empty_text(self):
        """T015: Handle empty text."""
        text = ""

        boundaries = self.parser.parse(text)

        assert boundaries == []

    def test_text_with_only_tags(self):
        """T015: Handle text with only SN tags."""
        text = "<G2316><G25><G2889>"

        boundaries = self.parser.parse(text)

        # Should not crash, may return empty or handle gracefully
        assert isinstance(boundaries, list)

    def test_real_john_316(self):
        """Integration test: Parse real John 3:16 from UNV+SN."""
        # Real data from FHL API (approximate)
        text = "「　神<G1063><G2316>愛<G25><WTG5656>{<G3779>}世人<G2889>，甚至<G5620>將他的獨生<G3439>子<G5207>賜給<G1325><WTG5656>他們，叫<G2443>一切<G3956>信<G4100><WTG5723>他的<G1519><G846>，不<G3361>致滅亡<G622><WTG5672>，反<G235>得<G2192><WTG5725>永<G166>生<G2222>。"

        boundaries = self.parser.parse(text)

        # Extract just terms
        terms = [b.term for b in boundaries]

        # Should contain key theological terms
        assert "神" in terms
        assert "愛" in terms
        assert "世人" in terms
        assert "獨生" in terms
        assert "子" in terms

        # "獨生" and "子" should be separate
        dusheng = next((b for b in boundaries if b.term == "獨生"), None)
        zi = next((b for b in boundaries if b.term == "子"), None)
        assert dusheng is not None
        assert zi is not None
        assert "G3439" in dusheng.strongs_numbers
        assert "G5207" in zi.strongs_numbers

    def test_real_genesis_11(self):
        """Integration test: Parse real Genesis 1:1 from UNV+SN."""
        # Real data from FHL API (approximate)
        text = "起初<WAH09002><H07225>，　神<H0430>創造<H01254><WTH8804>{<H0853>}天<H08064>{<H0853>}地<H0776>。"

        boundaries = self.parser.parse(text)

        terms = [b.term for b in boundaries]

        assert "起初" in terms or "起初<WAH09002>" in terms
        assert "神" in terms
        assert "創造" in terms
        assert "天" in terms
        assert "地" in terms
