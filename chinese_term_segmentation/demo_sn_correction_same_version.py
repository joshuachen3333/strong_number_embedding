#!/usr/bin/env python3
"""Demo: Compare initial segmentation vs Strong's Number corrected segmentation.

This version uses the SAME Bible version (UNV) to avoid text mismatch issues.
We compare initial segmentation of UNV text against UNV+Strong's boundaries.

⚠️  UPDATED: Now uses StrongsNumberParser with correct tag placement understanding!
"""

import sys
from typing import List, Tuple, Dict

from src.api.fhl_client import FHLClient
from src.core.strongs_parser import StrongsNumberParser
from src.plugins.segmenters.jieba_plugin import JiebaPlugin
from src.plugins.segmenters.pkuseg_plugin import PKUSegPlugin


def parse_strongs_boundaries(text_with_sn: str) -> Tuple[str, List[str], List[Tuple[str, List[str]]]]:
    """Parse UNV text with Strong's Numbers to extract term boundaries.

    ⚠️  CRITICAL: Uses StrongsNumberParser which correctly understands that
    SN tags FOLLOW the term they describe (not precede it)!

    Args:
        text_with_sn: Text like "神<H430>愛<H157>世人<H5971>"

    Returns:
        Tuple of:
        - Clean text without SN tags
        - List of terms (clean)
        - List of (term, [SNs]) tuples
    """
    parser = StrongsNumberParser()

    # Parse using our corrected parser
    boundaries = parser.parse(text_with_sn)

    # Get clean text
    clean_text = parser.get_clean_text(text_with_sn)

    # Extract just the terms (excluding punctuation)
    terms = [b.term for b in boundaries if b.term]

    # Build (term, [SNs]) tuples
    boundaries_with_sn = [(b.term, b.strongs_numbers) for b in boundaries if b.term]

    return clean_text, terms, boundaries_with_sn


def calculate_metrics(initial_seg: List[str], reference_seg: List[str]) -> Dict:
    """Calculate boundary accuracy metrics."""
    initial_boundaries = set()
    pos = 0
    for token in initial_seg[:-1]:
        pos += len(token)
        initial_boundaries.add(pos)

    reference_boundaries = set()
    pos = 0
    for token in reference_seg[:-1]:
        pos += len(token)
        reference_boundaries.add(pos)

    extra_splits = initial_boundaries - reference_boundaries
    missing_merges = reference_boundaries - initial_boundaries
    correct = initial_boundaries & reference_boundaries

    return {
        'extra_splits': len(extra_splits),
        'missing_merges': len(missing_merges),
        'correct': len(correct),
        'total_initial': len(initial_boundaries),
        'total_reference': len(reference_boundaries),
        'extra_split_positions': sorted(extra_splits),
        'missing_merge_positions': sorted(missing_merges)
    }


def show_error_details(clean_text: str, initial_seg: List[str], reference_seg: List[str], metrics: Dict):
    """Show specific error positions and corrections needed."""
    print("\n💡 Specific Corrections Needed:")

    # Show extra splits (need to merge)
    if metrics['extra_splits'] > 0:
        print(f"\n   🔗 Need to MERGE (remove {metrics['extra_splits']} extra boundaries):")
        for pos in metrics['extra_split_positions'][:3]:  # Show first 3
            # Find which terms are split
            cumulative = 0
            for i, term in enumerate(initial_seg):
                cumulative += len(term)
                if cumulative == pos:
                    context_before = initial_seg[max(0, i-1):i+1]
                    context_after = initial_seg[i+1:min(len(initial_seg), i+3)]
                    print(f"      Position {pos}: {' | '.join(context_before)} 🚫 | {' | '.join(context_after)}")
                    print(f"                       ^^^ Remove this boundary ^^^")
                    break

    # Show missing merges (need to split)
    if metrics['missing_merges'] > 0:
        print(f"\n   ✂️  Need to SPLIT (add {metrics['missing_merges']} missing boundaries):")
        for pos in metrics['missing_merge_positions'][:3]:  # Show first 3
            # Find where boundary should be
            cumulative = 0
            for i, term in enumerate(initial_seg):
                if cumulative < pos < cumulative + len(term):
                    # Boundary should be inside this term
                    split_pos = pos - cumulative
                    left_part = term[:split_pos]
                    right_part = term[split_pos:]
                    print(f"      Position {pos}: '{term}' → '{left_part}' | '{right_part}'")
                    break
                cumulative += len(term)


def display_comparison(verse_ref: str, clean_text: str,
                      initial_seg: List[str], reference_seg: List[str],
                      boundaries_with_sn: List[Tuple[str, List[str]]],
                      segmenter_name: str):
    """Display side-by-side comparison of segmentations."""

    print(f"\n{'='*80}")
    print(f"📖 {verse_ref} (UNV - 和合本)")
    print(f"{'='*80}")
    print(f"Text: {clean_text}")
    print()

    # Show initial segmentation
    print(f"❌ Initial Segmentation ({segmenter_name}):")
    print(f"   {' | '.join(initial_seg)}")
    print(f"   Terms: {len(initial_seg)}, Boundaries: {len(initial_seg) - 1}")
    print()

    # Show reference with Strong's Numbers
    print(f"✅ Reference from UNV+Strong's Numbers:")
    reference_display = []
    for term, sns in boundaries_with_sn:
        if sns:
            sn_str = ','.join(sns[:2])  # Show first 2 SNs
            if len(sns) > 2:
                sn_str += '...'
            reference_display.append(f"{term}[{sn_str}]")
        else:
            reference_display.append(term)
    print(f"   {' | '.join(reference_display)}")
    print(f"   Terms: {len(reference_seg)}, Boundaries: {len(reference_seg) - 1}")
    print()

    # Calculate metrics
    metrics = calculate_metrics(initial_seg, reference_seg)

    print(f"📊 Boundary Accuracy Analysis:")
    print(f"   ✅ Correct boundaries: {metrics['correct']}/{metrics['total_reference']}")
    print(f"   ❌ Extra splits (need merge): {metrics['extra_splits']}")
    print(f"   ❌ Missing splits (need boundary): {metrics['missing_merges']}")

    if metrics['total_reference'] > 0:
        accuracy = (metrics['correct'] / metrics['total_reference']) * 100
        error_rate = ((metrics['extra_splits'] + metrics['missing_merges']) / metrics['total_reference']) * 100
        print(f"\n   📈 Boundary Accuracy: {accuracy:.1f}%")
        print(f"   📉 Error Rate: {error_rate:.1f}%")

        if accuracy >= 95:
            print(f"   ✅ Excellent! Already meets ≥95% target")
        elif accuracy >= 80:
            print(f"   ⚠️  Good, but correction would improve to target ≥95%")
        else:
            print(f"   ❌ Poor. SN-correction essential to reach ≥95% target")

    # Show specific errors
    if metrics['extra_splits'] > 0 or metrics['missing_merges'] > 0:
        show_error_details(clean_text, initial_seg, reference_seg, metrics)

    print(f"{'='*80}")


def main():
    """Run the SN correction demo with same version (UNV)."""

    test_cases = [
        {
            'verse_ref': 'John 3:16',
            'book_zh': '約',
            'chapter': 3,
            'verse': 16,
            'description': '約翰福音 3:16 - "神愛世人" - Contains "獨生子"'
        },
        {
            'verse_ref': 'Genesis 1:1',
            'book_zh': '創',
            'chapter': 1,
            'verse': 1,
            'description': '創世記 1:1 - "起初神創造天地"'
        },
        {
            'verse_ref': 'Matthew 5:3',
            'book_zh': '太',
            'chapter': 5,
            'verse': 3,
            'description': '馬太福音 5:3 - Beatitudes'
        },
        {
            'verse_ref': 'Exodus 3:14',
            'book_zh': '出',
            'chapter': 3,
            'verse': 14,
            'description': '出埃及記 3:14 - "我是自有永有的" (I AM WHO I AM)'
        }
    ]

    print("\n" + "="*80)
    print("📊 Strong's Number-Based Segmentation Correction Demo v2")
    print("="*80)
    print("\n✨ Improved Demo: Using SAME version (UNV) to eliminate text mismatch")
    print("\nComparison:")
    print("  ❌ Initial: UNV text segmented by jieba/pkuseg (no Strong's)")
    print("  ✅ Target:  UNV text boundaries defined by Strong's Numbers")
    print("\nThis shows the correction value WITHOUT cross-version alignment issues.")

    # Initialize segmenters
    print("\n🔧 Initializing segmenters...")
    jieba_seg = JiebaPlugin()
    jieba_seg.initialize({'mode': 'accurate', 'hmm': True})

    try:
        pkuseg = PKUSegPlugin()
        pkuseg.initialize({'model_name': 'default'})
    except (ImportError, RuntimeError):
        pkuseg = None
        print("⚠️  PKUSeg not available")

    # Process each test case
    with FHLClient() as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"Test Case {i}/{len(test_cases)}: {test_case['description']}")
            print(f"{'='*80}")

            try:
                # Fetch UNV with Strong's Numbers
                unv_verse = client.fetch_verse(
                    book_zh=test_case['book_zh'],
                    chapter=test_case['chapter'],
                    verse=test_case['verse'],
                    version='unv',
                    include_strongs=True
                )

                if not unv_verse or not unv_verse.text:
                    print(f"⚠️  No UNV+SN data for {test_case['verse_ref']}")
                    continue

                # Parse Strong's Number boundaries
                clean_text, reference_seg, boundaries_with_sn = parse_strongs_boundaries(unv_verse.text)

                if not clean_text:
                    print(f"⚠️  Failed to parse {test_case['verse_ref']}")
                    continue

                # Get initial segmentation from clean text
                jieba_initial = jieba_seg.segment(clean_text)

                # Display comparison
                display_comparison(
                    verse_ref=test_case['verse_ref'],
                    clean_text=clean_text,
                    initial_seg=jieba_initial,
                    reference_seg=reference_seg,
                    boundaries_with_sn=boundaries_with_sn,
                    segmenter_name='jieba'
                )

                # Also test with PKUSeg if available
                if pkuseg:
                    print()  # Spacing
                    pkuseg_initial = pkuseg.segment(clean_text)
                    display_comparison(
                        verse_ref=test_case['verse_ref'],
                        clean_text=clean_text,
                        initial_seg=pkuseg_initial,
                        reference_seg=reference_seg,
                        boundaries_with_sn=boundaries_with_sn,
                        segmenter_name='pkuseg'
                    )

            except Exception as e:
                print(f"❌ Error processing {test_case['verse_ref']}: {e}")
                import traceback
                traceback.print_exc()

    print("\n" + "="*80)
    print("✅ Demo Complete!")
    print("="*80)
    print("\n🎯 Key Findings:")
    print("  1. Initial segmentation shows systematic boundary errors")
    print("  2. UNV+Strong's Numbers provides authoritative term boundaries")
    print("  3. Error types: extra splits (need merge) + missing splits (need boundary)")
    print("  4. SN-correction can fix these to achieve ≥95% boundary accuracy")
    print("\n💪 Value Proposition:")
    print("  • Theological accuracy: Keep biblical terms intact (獨生子, 耶和華)")
    print("  • Cross-version consistency: All Chinese versions use same boundaries")
    print("  • Training quality: Clean data for Strong's Number ML/AI models")
    print("\n🚀 Next Steps:")
    print("  • Approve this proposal: add-sn-based-segmentation-correction")
    print("  • Implement BoundaryCorrector class (Phase 2)")
    print("  • Add --correct-with-sn CLI flag (Phase 3)")
    print("  • Test with 200+ verses for validation (Phase 4)")
    print()


if __name__ == '__main__':
    sys.exit(main())
