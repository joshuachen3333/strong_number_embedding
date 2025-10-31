"""Unit tests for SimilarityMatcher (T029-T033)."""

from src.core.similarity_matcher import SimilarityMatcher


def test_t029_substring_extraction():
    """T029: Extract precise term from coarse boundary."""
    matcher = SimilarityMatcher()

    # Test Case 1: G3439 example from John 3:16
    refTerm = "獨生的"  # From Strong's Dictionary
    origText = "將他的獨生"  # FHL's coarse boundary
    result = matcher.find_best_substring(refTerm, origText)

    assert result is not None, "Should find a match"
    assert result == "獨生", f"Expected '獨生', got '{result}'"
    print("✅ T029a: '獨生的' matches '獨生' in '將他的獨生'")

    # Test Case 2: Exact match should also work
    result = matcher.find_best_substring("天國", "天國是")
    assert result == "天國", "Should match exact substring"
    print("✅ T029b: Exact match works")

    # Test Case 3: Partial match with good similarity
    result = matcher.find_best_substring("創造", "創造天地")
    assert result == "創造", "Should match beginning of text"
    print("✅ T029c: Match at beginning of text")

    print("✅ T029: Substring extraction passed")


def test_t030_character_variant_matching():
    """T030: Handle character variants (爲/為, 衞/衛, 綫/線)."""
    matcher = SimilarityMatcher()

    # Test Case 1: 爲/為 variant (U+7232 vs U+70BA)
    refTerm = "因為"  # Standard form U+70BA
    origText = "因爲天國"  # Variant form U+7232
    result = matcher.find_best_substring(refTerm, origText)

    assert result is not None, "Should find variant match"
    assert result == "因爲", f"Expected '因爲' (variant preserved), got '{result}'"
    print("✅ T030a: Character variant 爲/為 matched")

    # Test Case 2: Direct normalization test
    normalized = matcher._normalize_variants("因爲")
    assert normalized == "因為", "Should normalize 爲 to 為"
    print("✅ T030b: Normalization works correctly")

    # Test Case 3: 衞/衛 variant (David)
    normalized = matcher._normalize_variants("大衞")
    assert normalized == "大衛", "Should normalize 衞 to 衛"
    print("✅ T030c: David variant (衞/衛) normalized")

    # Test Case 4: 綫/線 variant (line)
    normalized = matcher._normalize_variants("界綫")
    assert normalized == "界線", "Should normalize 綫 to 線"
    print("✅ T030d: Line variant (綫/線) normalized")

    print("✅ T030: Character variant matching passed")


def test_t031_edit_distance_accuracy():
    """T031: Edit distance calculation accuracy."""
    matcher = SimilarityMatcher()

    # Test Case 1: Identical strings
    dist = matcher._edit_distance("abc", "abc")
    assert dist == 0, "Identical strings should have distance 0"
    print("✅ T031a: Identical strings (distance = 0)")

    # Test Case 2: Single character difference
    dist = matcher._edit_distance("獨生的", "獨生")
    assert dist == 1, "Should be 1 deletion"
    print("✅ T031b: Single deletion (distance = 1)")

    # Test Case 3: Substitution
    dist = matcher._edit_distance("天", "地")
    assert dist == 1, "Should be 1 substitution"
    print("✅ T031c: Single substitution (distance = 1)")

    # Test Case 4: Classic example (kitten → sitting)
    dist = matcher._edit_distance("kitten", "sitting")
    assert dist == 3, "Classic edit distance example"
    print("✅ T031d: Classic example (distance = 3)")

    # Test Case 5: Similarity score
    sim = matcher._similarity("獨生的", "獨生")
    expected = 1.0 - (1.0 / 3.0)  # 1 edit out of 3 chars
    assert abs(sim - expected) < 0.01, f"Expected {expected:.2f}, got {sim:.2f}"
    print(f"✅ T031e: Similarity score correct ({sim:.2f})")

    print("✅ T031: Edit distance accuracy passed")


def test_t032_threshold_filtering():
    """T032: Threshold filtering works correctly."""
    matcher = SimilarityMatcher()

    # Test Case 1: Match above threshold
    result = matcher.find_best_substring("獨生", "獨生子", threshold=0.5)
    assert result is not None, "Should find match above threshold"
    print("✅ T032a: Match above threshold found")

    # Test Case 2: No match below threshold
    result = matcher.find_best_substring("獨生的", "天國是", threshold=0.6)
    assert result is None, "Should return None when no match above threshold"
    print("✅ T032b: Returns None below threshold")

    # Test Case 3: Exact match always passes
    result = matcher.find_best_substring("天", "天地", threshold=0.9)
    assert result == "天", "Exact match should pass even with high threshold"
    print("✅ T032c: Exact match passes high threshold")

    # Test Case 4: Lower threshold accepts more matches
    result = matcher.find_best_substring("神", "上帝創造", threshold=0.3)
    # Might find some match with very low threshold
    # Just verify it doesn't crash
    print(f"✅ T032d: Low threshold result: {result}")

    print("✅ T032: Threshold filtering passed")


def test_t033_edge_cases():
    """T033: Edge cases and error handling."""
    matcher = SimilarityMatcher()

    # Test Case 1: Empty strings
    result = matcher.find_best_substring("", "test")
    assert result is None, "Empty refTerm should return None"
    print("✅ T033a: Empty refTerm handled")

    result = matcher.find_best_substring("test", "")
    assert result is None, "Empty origText should return None"
    print("✅ T033b: Empty origText handled")

    # Test Case 2: Single character origText (no substrings ≥ 2)
    result = matcher.find_best_substring("神", "天")
    assert result is None, "Single char origText has no substrings ≥2"
    print("✅ T033c: Single character origText handled")

    # Test Case 3: Completely different text
    result = matcher.find_best_substring("獨生的", "天國是主")
    # Might be None or very poor match
    if result:
        sim = matcher._similarity("獨生的", result)
        assert sim < 0.8, "Different text should have low similarity"
        print(f"✅ T033d: Different text low similarity ({sim:.2f})")
    else:
        print("✅ T033d: Different text returns None")

    # Test Case 4: Long vs short - single char refTerm should match single char
    result = matcher.find_best_substring("神", "神愛世人甚至賜下")
    # When refTerm is single char, exact match "神" is best (similarity 1.0)
    # "神愛" would have similarity ~0.5, "神愛世" ~0.33
    assert result is not None, "Should find a match"
    assert result == "神", f"Single char refTerm should match itself exactly, got '{result}'"
    print(f"✅ T033e: Single char exact match: '{result}'")

    # Test Case 5: Prefer longer matches with equal similarity
    # This tests the sort key (similarity, length)
    result = matcher.find_best_substring("天地", "天地天")
    # Both "天地" and "地天" might have similar scores, prefer longer
    assert len(result) >= 2, "Should return at least 2-char match"
    print(f"✅ T033f: Length preference: '{result}'")

    print("✅ T033: Edge cases passed")


def test_bonus_real_examples():
    """Bonus: Real examples from biblical text."""
    matcher = SimilarityMatcher()

    # Real Strong's Numbers from John 3:16
    test_cases = [
        ("獨一無二的, 唯一的", "將他的獨生", "獨生"),  # G3439
        ("愛上", "愛世人", "愛世"),  # G25 (might match "愛世" or "世人")
        ("兒子, 後代", "獨生子", "生子"),  # G5207
    ]

    print("\n🎯 Real Biblical Examples:")
    for ref, coarse, expected_contains in test_cases:
        result = matcher.find_best_substring(ref, coarse, threshold=0.5)
        if result:
            print(f"  '{ref}' in '{coarse}' → '{result}' ✓")
        else:
            print(f"  '{ref}' in '{coarse}' → None")


if __name__ == "__main__":
    print("="*70)
    print("SimilarityMatcher Tests (T029-T033)")
    print("="*70)

    try:
        test_t029_substring_extraction()
        print()
        test_t030_character_variant_matching()
        print()
        test_t031_edit_distance_accuracy()
        print()
        test_t032_threshold_filtering()
        print()
        test_t033_edge_cases()
        print()
        test_bonus_real_examples()

        print("\n" + "="*70)
        print("✅ All SimilarityMatcher tests passed!")
        print("="*70)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
