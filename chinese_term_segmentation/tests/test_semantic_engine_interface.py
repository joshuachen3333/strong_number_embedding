"""Unit tests for SemanticEngine interface (T034-T036).

Tests the pluggable semantic engine architecture added in Phase 2.1.

Created: 2025-11-01
Phase: 2.1 (Architecture Refactor)
"""

import pytest
from unittest.mock import Mock
from src.core.semantic_engine import SemanticEngine
from src.core.engines.edit_distance_engine import EditDistanceEngine
from src.core.similarity_matcher import SimilarityMatcher


def test_t034_edit_distance_engine_implements_interface():
    """T034: EditDistanceEngine implements SemanticEngine interface correctly.

    Verifies that EditDistanceEngine:
    1. Inherits from SemanticEngine
    2. Implements similarity() method correctly
    3. Returns float in [0, 1] range
    4. Implements get_name() method correctly
    5. Returns "edit-distance" as name
    """
    engine = EditDistanceEngine()

    # Test 1: Instance check
    assert isinstance(engine, SemanticEngine), \
        "EditDistanceEngine must inherit from SemanticEngine"
    print("✅ T034a: EditDistanceEngine is instance of SemanticEngine")

    # Test 2: similarity() method exists and returns float
    result = engine.similarity("神", "神")
    assert isinstance(result, float), \
        "similarity() must return float"
    print(f"✅ T034b: similarity() returns float ({result})")

    # Test 3: Similarity score range [0, 1]
    test_cases = [
        ("神", "神", 1.0),      # Exact match
        ("神", "上帝", 0.0),    # No overlap
        ("神的", "神", None),   # Partial (should be in [0, 1])
    ]

    for text1, text2, expected in test_cases:
        score = engine.similarity(text1, text2)
        assert 0.0 <= score <= 1.0, \
            f"similarity({text1}, {text2}) must be in [0, 1], got {score}"

        if expected is not None:
            assert score == expected, \
                f"Expected {expected}, got {score} for similarity({text1}, {text2})"

    print("✅ T034c: Similarity scores in range [0, 1]")

    # Test 4: get_name() method exists and returns string
    name = engine.get_name()
    assert isinstance(name, str), "get_name() must return string"
    print(f"✅ T034d: get_name() returns string ('{name}')")

    # Test 5: get_name() returns "edit-distance"
    assert name == "edit-distance", \
        f"Expected 'edit-distance', got '{name}'"
    print("✅ T034e: get_name() returns 'edit-distance'")

    # Test 6: Edge cases
    assert engine.similarity("", "") == 1.0, "Empty strings should match"
    assert engine.similarity("a", "") == 0.0, "One empty should be 0.0"
    assert engine.similarity("", "a") == 0.0, "One empty should be 0.0"
    print("✅ T034f: Edge cases handled correctly")

    # Test 7: Various Chinese text pairs
    chinese_tests = [
        ("獨生的", "獨生", 0.666),  # ~0.67
        ("因爲", "因為", 1.0),      # Variant match
        ("天地", "天", 0.5),        # Partial match
    ]

    for text1, text2, expected_min in chinese_tests:
        score = engine.similarity(text1, text2)
        assert score >= expected_min - 0.01, \
            f"similarity({text1}, {text2}) should be >= {expected_min}, got {score}"

    print("✅ T034g: Chinese text pairs scored correctly")

    print("✅ T034: EditDistanceEngine implements interface correctly")


def test_t035_similarity_matcher_accepts_and_uses_engine():
    """T035: SimilarityMatcher accepts and uses custom SemanticEngine.

    Verifies that SimilarityMatcher:
    1. Accepts SemanticEngine via constructor
    2. Actually uses the provided engine for calculations
    3. Calls engine.similarity() method
    4. Default engine is EditDistanceEngine
    """
    # Test 1: Default engine is EditDistanceEngine
    matcher = SimilarityMatcher()
    assert isinstance(matcher.engine, EditDistanceEngine), \
        "Default engine must be EditDistanceEngine"
    print("✅ T035a: Default engine is EditDistanceEngine")

    # Test 2: Can provide custom EditDistanceEngine
    custom_engine = EditDistanceEngine()
    matcher = SimilarityMatcher(engine=custom_engine)
    assert matcher.engine is custom_engine, \
        "Custom engine should be used"
    print("✅ T035b: Custom EditDistanceEngine accepted")

    # Test 3: Matcher uses engine's similarity() method
    # Create a mock engine to verify method calls
    mock_engine = Mock(spec=SemanticEngine)
    mock_engine.similarity.return_value = 0.8
    mock_engine.get_name.return_value = "mock-engine"

    matcher = SimilarityMatcher(engine=mock_engine)

    # find_best_substring should call engine.similarity()
    result = matcher.find_best_substring("test", "testing")

    # Verify engine.similarity() was called
    assert mock_engine.similarity.called, \
        "engine.similarity() should be called"
    print("✅ T035c: Matcher calls engine.similarity()")

    # Test 4: Verify similarity() is called with correct arguments
    mock_engine.similarity.reset_mock()
    mock_engine.similarity.return_value = 1.0

    result = matcher.find_best_substring("神", "神愛世人")

    # Should be called with "神" and various substrings of "神愛世人"
    call_args_list = mock_engine.similarity.call_args_list
    assert len(call_args_list) > 0, \
        "similarity() should be called at least once"

    # Verify first argument is always the refTerm
    for call_args in call_args_list:
        args, kwargs = call_args
        assert args[0] == "神", \
            "First argument should always be refTerm"

    print(f"✅ T035d: similarity() called {len(call_args_list)} times")

    # Test 5: Real EditDistanceEngine produces correct results
    real_engine = EditDistanceEngine()
    matcher = SimilarityMatcher(engine=real_engine)

    result = matcher.find_best_substring("獨生的", "將他的獨生")
    assert result == "獨生", \
        f"Expected '獨生', got '{result}'"
    print("✅ T035e: Real engine produces correct results")

    print("✅ T035: SimilarityMatcher accepts and uses engine")


def test_t036_invalid_engine_raises_error():
    """T036: Invalid engine type raises appropriate error.

    Verifies that SimilarityMatcher:
    1. Raises TypeError for non-SemanticEngine objects
    2. Provides clear error message
    3. Error message includes expected type
    4. Error message includes actual type received
    """
    # Test 1: String is not a valid engine
    with pytest.raises(TypeError) as exc_info:
        SimilarityMatcher(engine="invalid-string")

    error_msg = str(exc_info.value)
    assert "SemanticEngine" in error_msg, \
        "Error message should mention SemanticEngine"
    assert "str" in error_msg, \
        "Error message should mention actual type (str)"
    print(f"✅ T036a: String raises TypeError: {error_msg}")

    # Test 2: Integer is not a valid engine
    with pytest.raises(TypeError) as exc_info:
        SimilarityMatcher(engine=42)

    error_msg = str(exc_info.value)
    assert "SemanticEngine" in error_msg
    assert "int" in error_msg
    print(f"✅ T036b: Integer raises TypeError: {error_msg}")

    # Test 3: Dict is not a valid engine
    with pytest.raises(TypeError) as exc_info:
        SimilarityMatcher(engine={"type": "invalid"})

    error_msg = str(exc_info.value)
    assert "SemanticEngine" in error_msg
    assert "dict" in error_msg
    print(f"✅ T036c: Dict raises TypeError: {error_msg}")

    # Test 4: None is allowed (defaults to EditDistanceEngine)
    try:
        matcher = SimilarityMatcher(engine=None)
        assert isinstance(matcher.engine, EditDistanceEngine), \
            "None should default to EditDistanceEngine"
        print("✅ T036d: None defaults to EditDistanceEngine (valid)")
    except TypeError:
        pytest.fail("None should be allowed and default to EditDistanceEngine")

    # Test 5: Object without SemanticEngine interface
    class NotAnEngine:
        pass

    with pytest.raises(TypeError) as exc_info:
        SimilarityMatcher(engine=NotAnEngine())

    error_msg = str(exc_info.value)
    assert "SemanticEngine" in error_msg
    assert "NotAnEngine" in error_msg
    print(f"✅ T036e: Custom object raises TypeError: {error_msg}")

    # Test 6: Partially implemented engine (missing methods)
    class IncompleteEngine(SemanticEngine):
        # Missing required abstract methods
        pass

    # Cannot even instantiate IncompleteEngine due to ABC
    with pytest.raises(TypeError) as exc_info:
        engine = IncompleteEngine()

    error_msg = str(exc_info.value)
    assert "abstract" in error_msg.lower(), \
        "Should raise error about abstract methods"
    print(f"✅ T036f: Incomplete engine cannot be instantiated")

    print("✅ T036: Invalid engine raises appropriate error")


if __name__ == "__main__":
    print("=" * 70)
    print("SemanticEngine Interface Tests (T034-T036)")
    print("=" * 70)

    try:
        test_t034_edit_distance_engine_implements_interface()
        print()
        test_t035_similarity_matcher_accepts_and_uses_engine()
        print()
        test_t036_invalid_engine_raises_error()

        print("\n" + "=" * 70)
        print("✅ All SemanticEngine interface tests passed!")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
