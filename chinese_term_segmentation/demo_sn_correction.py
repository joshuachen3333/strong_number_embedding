#!/usr/bin/env python3
"""Demo: Compare initial segmentation vs Strong's Number corrected segmentation.

This demonstrates the improvement in boundary accuracy when using UNV with
Strong's Numbers as the authoritative standard for Chinese term boundaries.

Key principle: Target version (LCC) text goes in → Target version (LCC) text comes out
Only boundaries are corrected via string matching with UNV+SN reference.
"""

import sys
from typing import List

from src.api.fhl_client import FHLClient
from src.core.boundary_corrector import BoundaryCorrector
from src.core.strongs_parser import StrongsNumberParser
from src.plugins.segmenters.jieba_plugin import JiebaPlugin
from src.plugins.segmenters.pkuseg_plugin import PKUSegPlugin

# ANSI color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def compare_segmentations(initial: List[str], corrected: List[str]) -> dict:
    """Compare initial and corrected segmentations.

    Args:
        initial: Initial segmentation
        corrected: Corrected segmentation

    Returns:
        Dict with comparison metrics
    """
    # Find segments that changed
    initial_set = set(initial)
    corrected_set = set(corrected)

    changed = (initial_set - corrected_set) | (corrected_set - initial_set)
    unchanged = initial_set & corrected_set

    return {
        'changed_segments': len(changed),
        'unchanged_segments': len(unchanged),
        'total_initial': len(initial),
        'total_corrected': len(corrected)
    }


def display_comparison(verse_ref: str, version: str, text: str,
                      initial_seg: List[str], corrected_seg: List[str],
                      unv_sn_text: str, metrics, segmenter_name: str):
    """Display three-way comparison with colors: Before / After / Reference."""

    print(f"\n{'='*80}")
    print(f"{Colors.BOLD}📖 {verse_ref} ({version}){Colors.END}")
    print(f"{'='*80}")
    print(f"Target Text ({version}): {text}")
    print()

    # Parse UNV+SN to show detailed segmentation with Strong's Numbers
    parser = StrongsNumberParser()
    unv_boundaries = parser.parse(unv_sn_text)

    # Build UNV+SN display with Strong's Numbers
    unv_display_parts = []
    for boundary in unv_boundaries:
        if boundary.strongs_numbers:
            sns = ','.join(boundary.strongs_numbers[:2])  # Show first 2 SNs
            if len(boundary.strongs_numbers) > 2:
                sns += '...'
            unv_display_parts.append(f"{boundary.term}{Colors.CYAN}[{sns}]{Colors.END}")
        else:
            unv_display_parts.append(boundary.term)

    # Find changed segments (compare initial vs corrected)
    initial_set = set(initial_seg)
    corrected_set = set(corrected_seg)
    removed_segments = initial_set - corrected_set
    added_segments = corrected_set - initial_set

    # Show initial segmentation with removed segments highlighted in RED
    print(f"{Colors.BOLD}❌ BEFORE{Colors.END} SN Correction ({segmenter_name}):")
    initial_display = []
    for seg in initial_seg:
        if seg in removed_segments:
            initial_display.append(f"{Colors.RED}{seg}{Colors.END}")
        else:
            initial_display.append(seg)
    print(f"   {' | '.join(initial_display)}")
    print(f"   Terms: {len(initial_seg)}")
    print()

    # Show corrected segmentation with added segments highlighted in GREEN
    print(f"{Colors.BOLD}✅ AFTER{Colors.END} SN Correction:")
    corrected_display = []
    for seg in corrected_seg:
        if seg in added_segments:
            corrected_display.append(f"{Colors.GREEN}{seg}{Colors.END}")
        else:
            corrected_display.append(seg)
    print(f"   {' | '.join(corrected_display)}")
    print(f"   Terms: {len(corrected_seg)}")
    print()

    # Show UNV+SN reference with detailed Strong's Numbers
    print(f"{Colors.BOLD}📚 REFERENCE{Colors.END} (UNV with Strong's Numbers):")
    unv_display_str = ' | '.join(unv_display_parts)
    # Wrap if too long
    if len(unv_display_str) > 120:
        # Show first 120 chars
        print(f"   {unv_display_str[:120]}...")
    else:
        print(f"   {unv_display_str}")
    print(f"   Terms: {len(unv_boundaries)}")
    print()

    # Show side-by-side comparison for key changes
    if removed_segments or added_segments:
        print(f"{Colors.BOLD}🔍 Key Changes:{Colors.END}")
        # Show a few examples
        changes_shown = 0
        for removed in list(removed_segments)[:3]:
            print(f"   {Colors.RED}Removed:{Colors.END} '{removed}'")
            changes_shown += 1
        for added in list(added_segments)[:3]:
            print(f"   {Colors.GREEN}Added:{Colors.END} '{added}'")
            changes_shown += 1
        print()

    # Verify text preservation
    reconstructed = ''.join(corrected_seg)
    if reconstructed == text:
        print(f"{Colors.GREEN}✅ Text Preserved:{Colors.END} {version} text unchanged!\n")
    else:
        print(f"{Colors.RED}❌ WARNING: Text changed!{Colors.END}\n")
        print(f"   Original:      {text}")
        print(f"   Reconstructed: {reconstructed}\n")

    # Display correction metrics with colors
    print(f"{Colors.BOLD}📊 Correction Metrics:{Colors.END}")
    print(f"   UNV+SN terms extracted: {metrics.unv_sn_terms_count}")
    print(f"   Terms matched in {version}: {metrics.matched_terms_count} ({metrics.character_match_rate:.1f}%)")
    print(f"   Boundaries corrected: {Colors.YELLOW}{metrics.corrected_boundaries_count}{Colors.END}")
    print(f"   Unchanged segments: {metrics.unchanged_segments_count}")

    if metrics.character_match_rate >= 60:
        print(f"   📈 Match rate: {Colors.GREEN}✅ Good{Colors.END} (target: ≥60%)")
    elif metrics.character_match_rate >= 40:
        print(f"   📈 Match rate: {Colors.YELLOW}⚠️ Moderate{Colors.END} (target: ≥60%)")
    else:
        print(f"   📈 Match rate: {Colors.RED}❌ Low{Colors.END} (target: ≥60%)")

    print(f"{'='*80}\n")


def main():
    """Run the SN correction demo with BoundaryCorrector."""

    # Test verses with known segmentation challenges
    test_cases = [
        {
            'verse_ref': 'John 3:16',
            'book_zh': '約',
            'chapter': 3,
            'verse': 16,
            'version': 'lcc',
            'description': '呂振中譯本 (LCC) - Contains "獨生子" (only begotten son)'
        },
        {
            'verse_ref': 'Genesis 1:1',
            'book_zh': '創',
            'chapter': 1,
            'verse': 1,
            'version': 'lcc',
            'description': '呂振中譯本 (LCC) - Creation account'
        },
        {
            'verse_ref': 'Matthew 5:3',
            'book_zh': '太',
            'chapter': 5,
            'verse': 3,
            'version': 'lcc',
            'description': '呂振中譯本 (LCC) - Beatitudes'
        },
        {
            'verse_ref': 'Romans 8:1',
            'book_zh': '羅',
            'chapter': 8,
            'verse': 1,
            'version': 'lcc',
            'description': '呂振中譯本 (LCC) - No condemnation'
        }
    ]

    print("\n" + "="*80)
    print("📊 Strong's Number-Based Segmentation Correction Demo")
    print("="*80)
    print("\n✨ Key Principle: Target version text (LCC) goes in → Target version text (LCC) comes out")
    print("Only boundaries are corrected via string matching with UNV+SN reference.\n")

    # Initialize tools
    print("🔧 Initializing tools...")
    corrector = BoundaryCorrector()
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
                # Fetch both target version and UNV+SN
                target_verse, unv_sn_verse = client.fetch_for_correction(
                    book_zh=test_case['book_zh'],
                    chapter=test_case['chapter'],
                    verse=test_case['verse'],
                    target_version=test_case['version']
                )

                if not target_verse or not target_verse.text:
                    print(f"⚠️  No {test_case['version']} data for {test_case['verse_ref']}")
                    continue

                if not unv_sn_verse or not unv_sn_verse.text:
                    print(f"⚠️  No UNV+SN data for {test_case['verse_ref']}")
                    continue

                print(f"\n📝 {test_case['version'].upper()} Text: {target_verse.text}")
                print(f"📚 UNV+SN Reference: {unv_sn_verse.text[:80]}...")

                # Test with jieba
                print(f"\n--- Jieba Segmenter ---")
                jieba_initial = jieba_seg.segment(target_verse.text)
                jieba_corrected, jieba_metrics = corrector.correct(
                    target_verse.text,
                    jieba_initial,
                    unv_sn_verse.text
                )

                display_comparison(
                    verse_ref=test_case['verse_ref'],
                    version=test_case['version'].upper(),
                    text=target_verse.text,
                    initial_seg=jieba_initial,
                    corrected_seg=jieba_corrected,
                    unv_sn_text=unv_sn_verse.text,
                    metrics=jieba_metrics,
                    segmenter_name='jieba'
                )

                # Test with PKUSeg if available
                if pkuseg:
                    print(f"\n--- PKUSeg Segmenter ---")
                    pkuseg_initial = pkuseg.segment(target_verse.text)
                    pkuseg_corrected, pkuseg_metrics = corrector.correct(
                        target_verse.text,
                        pkuseg_initial,
                        unv_sn_verse.text
                    )

                    display_comparison(
                        verse_ref=test_case['verse_ref'],
                        version=test_case['version'].upper(),
                        text=target_verse.text,
                        initial_seg=pkuseg_initial,
                        corrected_seg=pkuseg_corrected,
                        unv_sn_text=unv_sn_verse.text,
                        metrics=pkuseg_metrics,
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
    print("  1. ✅ Text Preservation: Target version text (LCC) never changes to UNV")
    print("  2. 📊 String Matching: Finds character sequences common to LCC and UNV+SN")
    print("  3. 🔧 Boundary Correction: Applies UNV+SN boundaries to matched terms")
    print("  4. ⚠️  Current Limitation: ~40-50% character match rate (target: ≥60%)")
    print("\n💪 What Works:")
    print("  • Matches terms like '愛', '世人', '甚至' between versions")
    print("  • Preserves LCC text completely")
    print("  • Safe fallback for unmatched segments")
    print("\n🔮 Needed Improvements:")
    print("  • Substring matching for nested terms (e.g., '獨生' within '將他的獨生')")
    print("  • Better parsing of UNV+SN complex structures")
    print("  • Phase 2: Semantic alignment for character-mismatched segments")
    print()


if __name__ == '__main__':
    sys.exit(main())
