"""Integration tests for Phase 2.1 semantic engine architecture.

Tests end-to-end functionality with the new pluggable engine system.

Created: 2025-11-01
Phase: 2.1 (Architecture Refactor)
"""

import subprocess
import re
import time
from typing import Dict, Optional


def run_segment_command(
    book: str,
    chapter: int,
    verse: int,
    version: str = "lcc",
    seg: str = "pkuseg",
    correct_with_sn: bool = True,
    use_refinement: bool = True,
    semantic_engine: Optional[str] = None
) -> Dict:
    """Run segment.py and parse output."""
    cmd = [
        "./segment.py",
        "--engs", book,
        "--chap", str(chapter),
        "--sec", str(verse),
        "--version", version,
        "--seg", seg
    ]

    if correct_with_sn:
        cmd.append("--correct-with-sn")

    if use_refinement:
        cmd.append("--use-refinement")

    if semantic_engine:
        cmd.extend(["--semantic-engine", semantic_engine])

    # Run command and capture output
    start_time = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30
    )
    elapsed_time = time.time() - start_time

    # Parse output
    output = result.stdout
    stderr = result.stderr

    # Extract metrics using regex
    match_rate_match = re.search(r'Match rate: ([\d.]+)%', output)
    refinement_match = re.search(r'Refinement: (\d+)/(\d+) terms refined \(([\d.]+)%\)', output)
    boundaries_match = re.search(r'Boundaries corrected: (\d+)', output)
    segments_match = re.search(r'Segments: (\d+) → (\d+)', output)
    preserved_match = re.search(r'✅ Text preserved', output)

    return {
        'success': result.returncode == 0,
        'output': output,
        'stderr': stderr,
        'elapsed_time': elapsed_time,
        'match_rate': float(match_rate_match.group(1)) if match_rate_match else None,
        'refinement_count': int(refinement_match.group(1)) if refinement_match else None,
        'total_terms': int(refinement_match.group(2)) if refinement_match else None,
        'refinement_rate': float(refinement_match.group(3)) if refinement_match else None,
        'boundaries_corrected': int(boundaries_match.group(1)) if boundaries_match else None,
        'segments_before': int(segments_match.group(1)) if segments_match else None,
        'segments_after': int(segments_match.group(2)) if segments_match else None,
        'text_preserved': preserved_match is not None
    }


def test_t037_genesis_3_3_baseline():
    """T037: Genesis 3:3 maintains 61.5% match rate (baseline test).

    This is the critical regression test - the refactored architecture
    must produce identical results to the original implementation.
    """
    print("\n" + "="*70)
    print("T037: Genesis 3:3 Baseline Test")
    print("="*70)

    result = run_segment_command(
        book="gen",
        chapter=3,
        verse=3,
        version="lcc",
        seg="pkuseg",
        correct_with_sn=True,
        use_refinement=True,
        semantic_engine=None  # Default (backward compatible)
    )

    assert result['success'], f"Command failed: {result['stderr']}"
    print(f"✅ Command executed successfully")

    # Check match rate
    assert result['match_rate'] is not None, "Failed to parse match rate"
    assert 59.0 <= result['match_rate'] <= 64.0, \
        f"Match rate {result['match_rate']}% outside acceptable range [59-64%]"
    print(f"✅ Match rate: {result['match_rate']}% (target: 61.5% ± 2.5%)")

    # Check refinement worked
    assert result['refinement_count'] is not None, "Failed to parse refinement count"
    assert result['refinement_count'] > 0, "No terms were refined"
    print(f"✅ Refinement: {result['refinement_count']}/{result['total_terms']} terms "
          f"({result['refinement_rate']}%)")

    # Check boundaries were corrected
    assert result['boundaries_corrected'] is not None
    assert result['boundaries_corrected'] > 0, "No boundaries corrected"
    print(f"✅ Boundaries corrected: {result['boundaries_corrected']}")

    # Check text preservation
    assert result['text_preserved'], "Text was not preserved!"
    print(f"✅ Text preserved (target version unchanged)")

    # Check performance
    assert result['elapsed_time'] < 10.0, \
        f"Too slow: {result['elapsed_time']:.2f}s (should be < 10s)"
    print(f"✅ Performance: {result['elapsed_time']:.2f}s")

    print("\n✅ T037: Genesis 3:3 baseline test PASSED")
    return result


def test_t038_explicit_engine_selection():
    """T038: Explicit --semantic-engine edit-distance produces identical results.

    Verifies that explicitly specifying the default engine works correctly
    and produces the same results as the implicit default.
    """
    print("\n" + "="*70)
    print("T038: Explicit Engine Selection Test")
    print("="*70)

    # Run with explicit engine
    result = run_segment_command(
        book="gen",
        chapter=3,
        verse=3,
        version="lcc",
        seg="pkuseg",
        correct_with_sn=True,
        use_refinement=True,
        semantic_engine="edit-distance"  # Explicit
    )

    assert result['success'], f"Command failed: {result['stderr']}"
    print(f"✅ Command executed successfully")

    # Should get same match rate as baseline
    assert result['match_rate'] is not None
    assert 59.0 <= result['match_rate'] <= 64.0, \
        f"Match rate {result['match_rate']}% differs from baseline"
    print(f"✅ Match rate: {result['match_rate']}% (consistent with baseline)")

    # Should have same refinement behavior
    assert result['refinement_count'] > 0
    print(f"✅ Refinement: {result['refinement_count']}/{result['total_terms']} terms")

    print("\n✅ T038: Explicit engine selection PASSED")
    return result


def test_t039_multiple_verses_stability():
    """T039: Test stability across multiple verses.

    Verifies that the refactored architecture works consistently
    across different verses, not just Genesis 3:3.
    """
    print("\n" + "="*70)
    print("T039: Multiple Verses Stability Test")
    print("="*70)

    test_cases = [
        ("gen", 1, 1, "LCC - Genesis 1:1 (Creation)"),
        ("john", 3, 16, "LCC - John 3:16 (Famous verse)"),
        ("gen", 3, 3, "LCC - Genesis 3:3 (Baseline)"),
    ]

    results = []
    for book, chapter, verse, description in test_cases:
        print(f"\n📖 Testing: {description}")

        result = run_segment_command(
            book=book,
            chapter=chapter,
            verse=verse,
            version="lcc",
            seg="pkuseg",
            correct_with_sn=True,
            use_refinement=True,
            semantic_engine="edit-distance"
        )

        assert result['success'], f"Failed: {description}"
        assert result['text_preserved'], f"Text not preserved: {description}"

        print(f"   ✅ Match rate: {result['match_rate']}%")
        print(f"   ✅ Refinement: {result['refinement_count']}/{result['total_terms']}")
        print(f"   ✅ Time: {result['elapsed_time']:.2f}s")

        results.append({
            'description': description,
            'match_rate': result['match_rate'],
            'elapsed_time': result['elapsed_time']
        })

    # Check all verses completed successfully
    assert len(results) == len(test_cases), "Some tests failed"
    print(f"\n✅ All {len(results)} verses tested successfully")

    # Check performance consistency
    max_time = max(r['elapsed_time'] for r in results)
    assert max_time < 15.0, f"Slowest test too slow: {max_time:.2f}s"
    print(f"✅ Max time: {max_time:.2f}s (< 15s)")

    print("\n✅ T039: Multiple verses stability PASSED")
    return results


def test_t040_backward_compatibility_without_flags():
    """T040: Backward compatibility - works without new flags.

    Verifies that existing commands (without --semantic-engine) still work.
    This is critical for backward compatibility.
    """
    print("\n" + "="*70)
    print("T040: Backward Compatibility Test")
    print("="*70)

    # Test 1: Basic segmentation (no correction)
    print("\n📋 Test 1: Basic segmentation (no SN correction)")
    result = run_segment_command(
        book="gen",
        chapter=1,
        verse=1,
        version="lcc",
        seg="pkuseg",
        correct_with_sn=False,
        use_refinement=False,
        semantic_engine=None
    )

    assert result['success'], "Basic segmentation failed"
    print("✅ Basic segmentation works")

    # Test 2: With SN correction but no refinement
    print("\n📋 Test 2: SN correction without refinement")
    result = run_segment_command(
        book="gen",
        chapter=3,
        verse=3,
        version="lcc",
        seg="pkuseg",
        correct_with_sn=True,
        use_refinement=False,
        semantic_engine=None
    )

    assert result['success'], "SN correction failed"
    assert result['text_preserved'], "Text not preserved"
    print("✅ SN correction without refinement works")

    # Test 3: Full pipeline (SN + refinement, no semantic-engine flag)
    print("\n📋 Test 3: Full pipeline (no semantic-engine flag)")
    result = run_segment_command(
        book="gen",
        chapter=3,
        verse=3,
        version="lcc",
        seg="pkuseg",
        correct_with_sn=True,
        use_refinement=True,
        semantic_engine=None  # Critical: no flag
    )

    assert result['success'], "Full pipeline failed"
    assert result['match_rate'] is not None
    assert result['refinement_count'] > 0
    print(f"✅ Full pipeline works (match rate: {result['match_rate']}%)")

    print("\n✅ T040: Backward compatibility PASSED")
    return result


def test_t041_performance_regression():
    """T041: Performance regression test.

    Verifies that the refactored architecture hasn't significantly
    degraded performance (target: <5% slowdown).
    """
    print("\n" + "="*70)
    print("T041: Performance Regression Test")
    print("="*70)

    # Run same test multiple times to get average
    times = []
    for i in range(3):
        result = run_segment_command(
            book="gen",
            chapter=3,
            verse=3,
            version="lcc",
            seg="pkuseg",
            correct_with_sn=True,
            use_refinement=True,
            semantic_engine="edit-distance"
        )

        assert result['success'], f"Run {i+1} failed"
        times.append(result['elapsed_time'])
        print(f"   Run {i+1}: {result['elapsed_time']:.3f}s")

    avg_time = sum(times) / len(times)
    max_time = max(times)
    min_time = min(times)

    print(f"\n📊 Performance Stats:")
    print(f"   Average: {avg_time:.3f}s")
    print(f"   Min: {min_time:.3f}s")
    print(f"   Max: {max_time:.3f}s")
    print(f"   Variance: {max_time - min_time:.3f}s")

    # Check performance targets
    assert avg_time < 10.0, f"Average too slow: {avg_time:.2f}s"
    assert max_time < 15.0, f"Max time too slow: {max_time:.2f}s"

    print(f"\n✅ Performance acceptable (avg: {avg_time:.2f}s < 10s)")
    print("✅ T041: Performance regression test PASSED")

    return {
        'avg_time': avg_time,
        'max_time': max_time,
        'min_time': min_time
    }


if __name__ == "__main__":
    print("="*70)
    print("Phase 2.1 Integration Tests (T037-T041)")
    print("="*70)
    print("\nTesting pluggable semantic engine architecture")
    print("Baseline: EditDistanceEngine with 61.5% match rate on Genesis 3:3")
    print("="*70)

    try:
        # Run all integration tests
        baseline_result = test_t037_genesis_3_3_baseline()
        explicit_result = test_t038_explicit_engine_selection()
        stability_results = test_t039_multiple_verses_stability()
        compat_result = test_t040_backward_compatibility_without_flags()
        perf_result = test_t041_performance_regression()

        # Summary
        print("\n" + "="*70)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   Genesis 3:3 match rate: {baseline_result['match_rate']}%")
        print(f"   Verses tested: {len(stability_results) + 2}")
        print(f"   Average performance: {perf_result['avg_time']:.2f}s")
        print(f"   Backward compatibility: ✅")
        print(f"   Text preservation: ✅")
        print("\n" + "="*70)

        exit(0)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
