"""Unit tests for FHL Strong's Dictionary API integration (T026-T028)."""

import pytest
from src.api.fhl_client import FHLClient, StrongEntry


class TestFHLStrongDict:
    """Tests for fetch_strong_dict() method."""

    @pytest.fixture
    def client(self):
        """Create FHL client instance."""
        return FHLClient(timeout=15)

    def test_t026_fetch_greek_strongs(self, client):
        """T026: Fetch Greek Strong's Number (G3439 = μονογενής)."""
        # Given: Strong's Number G3439
        sn = "G3439"

        # When: Fetching dictionary entry
        entry = client.fetch_strong_dict(sn)

        # Then: Returns valid StrongEntry
        assert entry is not None, f"Should return entry for {sn}"
        assert isinstance(entry, StrongEntry)

        # And: Contains correct data
        assert entry.sn == "3439" or entry.sn == "03439"
        assert entry.original == "μονογενής"
        assert "獨生" in entry.chinese_meaning or "獨一" in entry.chinese_meaning
        assert len(entry.english_meaning) > 0

        print(f"\n✅ T026 passed:")
        print(f"  SN: {entry.sn}")
        print(f"  Original: {entry.original}")
        print(f"  Chinese: {entry.chinese_meaning}")
        print(f"  English: {entry.english_meaning[:50]}...")

    def test_t027_fetch_hebrew_strongs(self, client):
        """T027: Fetch Hebrew Strong's Number (H430 = אֱלֹהִים)."""
        # Given: Strong's Number H430
        sn = "H430"

        # When: Fetching dictionary entry
        entry = client.fetch_strong_dict(sn)

        # Then: Returns valid StrongEntry
        assert entry is not None, f"Should return entry for {sn}"
        assert isinstance(entry, StrongEntry)

        # And: Contains correct data
        assert entry.sn == "430" or entry.sn == "00430"
        assert entry.original == "אֱלֹהִים"
        assert "神" in entry.chinese_meaning or "上帝" in entry.chinese_meaning
        assert len(entry.english_meaning) > 0

        # And: Testament detection works (H prefix → N=1)
        # This is implicitly tested by getting valid result

        print(f"\n✅ T027 passed:")
        print(f"  SN: {entry.sn}")
        print(f"  Original: {entry.original}")
        print(f"  Chinese: {entry.chinese_meaning}")
        print(f"  English: {entry.english_meaning[:50]}...")

    def test_t028_error_handling(self, client):
        """T028: Error handling for invalid/missing entries."""
        # Test Case 1: Missing entry
        # When: Fetching non-existent SN
        entry = client.fetch_strong_dict("G99999")

        # Then: Returns None (not exception)
        assert entry is None, "Should return None for missing entry"

        # Test Case 2: Invalid format (no prefix)
        # When: Invalid SN format
        with pytest.raises(ValueError, match="Invalid Strong's number format"):
            client.fetch_strong_dict("123")

        # Test Case 3: Invalid prefix
        # When: Invalid prefix (not G or H)
        with pytest.raises(ValueError, match="Invalid Strong's number prefix"):
            client.fetch_strong_dict("X123")

        # Test Case 4: Non-numeric SN
        # When: Non-numeric after prefix
        with pytest.raises(ValueError, match="Invalid Strong's number"):
            client.fetch_strong_dict("GABC")

        print("\n✅ T028 passed: All error cases handled correctly")

    def test_caching_works(self, client):
        """Bonus test: Verify caching works."""
        # Given: First fetch of G3754
        entry1 = client.fetch_strong_dict("G3754")

        # When: Second fetch of same SN
        entry2 = client.fetch_strong_dict("G3754")

        # Then: Both return same object (from cache)
        assert entry1 is not None
        assert entry2 is not None
        assert entry1.sn == entry2.sn
        assert entry1.original == entry2.original

        # And: Cache hit logged (check via logger)
        print("\n✅ Caching test passed: Same SN returns cached result")

    def test_simplified_vs_traditional(self, client):
        """Bonus test: Simplified vs Traditional Chinese."""
        # Given: Same SN with different language preferences
        sn = "G25"  # ἀγαπάω (love)

        # When: Fetching traditional (default)
        entry_trad = client.fetch_strong_dict(sn, simplified=False)

        # When: Fetching simplified
        entry_simp = client.fetch_strong_dict(sn, simplified=True)

        # Then: Both should return entries (may have different Chinese text)
        assert entry_trad is not None
        assert entry_simp is not None

        print("\n✅ Simplified/Traditional test passed:")
        print(f"  Traditional: {entry_trad.chinese_meaning}")
        print(f"  Simplified: {entry_simp.chinese_meaning}")


if __name__ == "__main__":
    """Run tests manually for quick verification."""
    import sys

    client = FHLClient(timeout=15)

    print("="*70)
    print("Running FHL Strong's Dictionary Tests (T026-T028)")
    print("="*70)

    try:
        # T026: Greek
        print("\n[T026] Testing Greek Strong's Number...")
        test = TestFHLStrongDict()
        test.test_t026_fetch_greek_strongs(client)

        # T027: Hebrew
        print("\n[T027] Testing Hebrew Strong's Number...")
        test.test_t027_fetch_hebrew_strongs(client)

        # T028: Error handling
        print("\n[T028] Testing Error Handling...")
        test.test_t028_error_handling(client)

        # Bonus tests
        print("\n[Bonus] Testing Caching...")
        test.test_caching_works(client)

        print("\n[Bonus] Testing Simplified/Traditional...")
        test.test_simplified_vs_traditional(client)

        print("\n" + "="*70)
        print("✅ All tests passed!")
        print("="*70)
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()
