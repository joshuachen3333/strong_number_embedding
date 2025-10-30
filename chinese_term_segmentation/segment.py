#!/usr/bin/env python3
"""CLI tool for fetching Bible verses and segmenting Chinese terms (中文分詞).

Segmentation (分詞) is the process of splitting Chinese text into meaningful words,
which is essential for aligning Chinese translations with Strong's Numbers.

Usage:
    python segment.py --verse "Gen 1:3" --version unv
    python segment.py --verse "John 3:16-17" --version lcc --seg jieba pkuseg
    python segment.py --verse "創 1:1" --version unv --strong
"""

import argparse
import sys
import logging
from typing import Optional

from src.api.fhl_client import FHLClient, VerseData
from src.api.verse_parser import VerseParser, VerseReference
from src.core.plugin_manager import PluginManager
from src.plugins.segmenters.jieba_plugin import JiebaPlugin
from src.plugins.segmenters.pkuseg_plugin import PKUSegPlugin
from src.plugins.segmenters.lac_plugin import LACPlugin
from src.plugins.segmenters.stanza_plugin import StanzaPlugin


def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def display_verse(verse: VerseData, show_reference: bool = True):
    """Display a single verse in formatted output."""
    if show_reference:
        print(f"\n{verse.book.title()} {verse.chapter}:{verse.verse}")
    print(f"  {verse.text}")


def display_segmentation(text: str, tokens: list, segmenter_name: str):
    """Display Chinese word segmentation results (分詞結果)."""
    print(f"\n📊 Segmentation ({segmenter_name}):")
    print(f"  Original: {text}")
    print(f"  Segments: {' | '.join(tokens)}")
    print(f"  Segment count: {len(tokens)}")


def show_version_help():
    """Display available Bible versions."""
    print("\n📖 Available Bible Versions:")
    print("=" * 60)
    versions = [
        ("unv", "和合本 (Chinese Union Version)", "Chinese"),
        ("rcuv2010", "和合本2010 (Revised Chinese Union 2010)", "Chinese"),
        ("lcc", "呂振中譯本 (Lü Zhènzhōng Translation)", "Chinese"),
        ("kjv", "King James Version", "English"),
        ("esv", "English Standard Version", "English"),
        ("nasb", "New American Standard Bible", "English"),
    ]
    for code, name, lang in versions:
        print(f"  {code:12} - {name:45} [{lang}]")
    print("=" * 60)
    print("\nUsage: --version unv")
    print("See FHL_API_REFERENCE.md for complete list\n")


def show_segmenter_help():
    """Display available Chinese word segmenters."""
    print("\n🔧 Available Chinese Word Segmenters (分詞工具):")
    print("=" * 80)

    segmenters = [
        {
            "cli": "jieba",
            "chinese": "結巴分詞",
            "english": "Jieba Chinese Word Segmentation",
            "speed": "⚡⚡⚡ Fast",
            "accuracy": "⭐⭐⭐ Good",
            "custom_dict": "✅ Yes",
            "install": "pip install jieba",
            "url": "https://github.com/fxsjy/jieba"
        },
        {
            "cli": "pkuseg",
            "chinese": "北大分詞",
            "english": "PKU Segmenter (Peking University)",
            "speed": "⚡⚡ Moderate",
            "accuracy": "⭐⭐⭐⭐ High",
            "custom_dict": "✅ Yes",
            "install": "pip install pkuseg",
            "url": "https://github.com/lancopku/pkuseg-python"
        },
        {
            "cli": "lac",
            "chinese": "百度LAC",
            "english": "LAC - Lexical Analysis of Chinese (Baidu)",
            "speed": "⚡ Slower (neural)",
            "accuracy": "⭐⭐⭐⭐ High",
            "custom_dict": "✅ Yes",
            "install": "pip install LAC",
            "url": "https://github.com/baidu/lac"
        },
        {
            "cli": "stanza",
            "chinese": "斯坦福NLP",
            "english": "Stanza - Stanford NLP Group",
            "speed": "⚡ Slower (neural)",
            "accuracy": "⭐⭐⭐⭐⭐ Very High",
            "custom_dict": "❌ No (pre-trained models)",
            "install": "pip install stanza && python -c \"import stanza; stanza.download('zh')\"",
            "url": "https://stanfordnlp.github.io/stanza/"
        },
    ]

    for seg in segmenters:
        print(f"\n📦 {seg['cli'].upper()}")
        print(f"   CLI Name:     {seg['cli']}")
        print(f"   Chinese Name: {seg['chinese']}")
        print(f"   English Name: {seg['english']}")
        print(f"   Speed:        {seg['speed']}")
        print(f"   Accuracy:     {seg['accuracy']}")
        print(f"   Custom Dict:  {seg['custom_dict']}")
        print(f"   Install:      {seg['install']}")
        print(f"   URL:          {seg['url']}")

    print("\n" + "=" * 80)
    print("\n💡 Usage Examples:")
    print("   --seg jieba                        # Use single segmenter")
    print("   --seg jieba pkuseg                 # Compare two segmenters")
    print("   --seg jieba pkuseg lac stanza      # Compare all four")
    print("\n" + "=" * 80 + "\n")


def show_english_books_help():
    """Display available English book names."""
    from src.api.book_mappings import BOOK_MAP_EN_TO_ZH, BOOK_ABBREVIATIONS

    print("\n📚 Available English Book Names:")
    print("=" * 60)
    print("Old Testament (39 books):")
    print("-" * 60)

    ot_books = list(BOOK_MAP_EN_TO_ZH.keys())[:39]
    for i, book in enumerate(ot_books, 1):
        chinese = BOOK_MAP_EN_TO_ZH[book]
        # Find abbreviations
        abbrevs = [abbr for abbr, full in BOOK_ABBREVIATIONS.items() if full == book]
        abbrev_str = ", ".join(abbrevs[:3]) if abbrevs else "-"
        print(f"  {i:2}. {book.title():<20} ({chinese}) - Abbrev: {abbrev_str}")
        if i % 13 == 0:
            print()

    print("\nNew Testament (27 books):")
    print("-" * 60)
    nt_books = list(BOOK_MAP_EN_TO_ZH.keys())[39:]
    for i, book in enumerate(nt_books, 40):
        chinese = BOOK_MAP_EN_TO_ZH[book]
        abbrevs = [abbr for abbr, full in BOOK_ABBREVIATIONS.items() if full == book]
        abbrev_str = ", ".join(abbrevs[:3]) if abbrevs else "-"
        print(f"  {i:2}. {book.title():<20} ({chinese}) - Abbrev: {abbrev_str}")

    print("=" * 60)
    print("\nUsage: --engs Gen --chap 1 --sec 3")
    print("       --engs Matthew --chap 5 --sec 1\n")


def show_chinese_books_help():
    """Display available Chinese book abbreviations."""
    from src.api.book_mappings import BOOK_MAP_EN_TO_ZH

    print("\n📚 Available Chinese Book Abbreviations (書卷):")
    print("=" * 60)
    print("Old Testament (39 books):")
    print("-" * 60)

    ot_books = list(BOOK_MAP_EN_TO_ZH.items())[:39]
    for i, (eng, zh) in enumerate(ot_books, 1):
        print(f"  {i:2}. {zh:3} - {eng.title():<20}")
        if i % 13 == 0:
            print()

    print("\nNew Testament (27 books):")
    print("-" * 60)
    nt_books = list(BOOK_MAP_EN_TO_ZH.items())[39:]
    for i, (eng, zh) in enumerate(nt_books, 40):
        print(f"  {i:2}. {zh:3} - {eng.title():<20}")

    print("=" * 60)
    print("\nUsage: --chineses 創 --chap 1 --sec 3")
    print("       --chineses 太 --chap 5 --sec 1-5\n")


def main():
    # Check for help requests early (before argparse validation)
    import sys
    if len(sys.argv) >= 2:
        # Check if any argument is 'help'
        if 'help' in [arg.lower() for arg in sys.argv]:
            # Determine which help to show based on the flag before 'help'
            for i, arg in enumerate(sys.argv):
                if arg.lower() == 'help' and i > 0:
                    prev_arg = sys.argv[i-1]
                    if prev_arg in ['--version']:
                        show_version_help()
                        return 0
                    elif prev_arg in ['--seg', '-s']:
                        show_segmenter_help()
                        return 0
                    elif prev_arg == '--engs':
                        show_english_books_help()
                        return 0
                    elif prev_arg == '--chineses':
                        show_chinese_books_help()
                        return 0

            # If 'help' appears but not after a recognized flag, show general help
            if '--seg' in sys.argv or '-s' in sys.argv:
                show_segmenter_help()
                return 0

    parser = argparse.ArgumentParser(
        description='Fetch Bible verses from FHL API and segment Chinese terms.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Using --verse (convenience mode):
  %(prog)s --verse "Gen 1:3" --version unv
  %(prog)s --verse "John 3:16-17" --version kjv
  %(prog)s --verse "創 1:1" --version lcc --seg jieba

  # Using FHL Chinese parameters (--chineses, --chap, --sec):
  %(prog)s --chineses 創 --chap 1 --sec 3 --version unv
  %(prog)s --chineses 太 --chap 5 --sec 1-5 --version unv --strong

  # Using English book names (--engs, --chap, --sec):
  %(prog)s --engs Gen --chap 1 --sec 3 --version unv
  %(prog)s --engs Matt --chap 5 --sec 1-5 --version kjv --seg jieba pkuseg

  # Compare multiple segmenters (分詞工具比較):
  %(prog)s --verse "約 3:16" --version unv --seg jieba pkuseg lac stanza
  %(prog)s --verse "創 1:1" --version unv --seg jieba lac

  # Get help for available options:
  %(prog)s --version help      # List all Bible versions
  %(prog)s --seg help           # List all segmenters
  %(prog)s --engs help          # List all English book names
  %(prog)s --chineses help      # List all Chinese book abbreviations
        '''.strip()
    )

    # Verse reference (can use either combined --verse OR separate book/chap/sec)
    ref_group = parser.add_mutually_exclusive_group(required=True)
    ref_group.add_argument(
        '--verse',
        help='Verse reference (e.g., "Gen 1:3", "John 3:16-17", "創 1:1")'
    )
    ref_group.add_argument(
        '--chineses',
        help='Chinese book abbreviation (創, 出, 太, etc.) - use with --chap. Use "help" to list all.'
    )
    ref_group.add_argument(
        '--engs',
        help='English book name/abbreviation (Gen, Genesis, Matt, etc.) - use with --chap. Use "help" to list all.'
    )

    # FHL-style parameters (align with API naming)
    parser.add_argument(
        '--chap',
        type=int,
        help='Chapter number (required with --chineses)'
    )
    parser.add_argument(
        '--sec',
        help='Verse/section number or range (e.g., "3" or "16-17")'
    )

    # Bible version
    parser.add_argument(
        '--version',
        default='unv',
        help='Bible version (default: unv). Use "help" to list all versions.'
    )

    # Strong's numbers
    parser.add_argument(
        '--strong',
        action='store_true',
        help='Include Strong\'s numbers in output'
    )

    # Chinese Word Segmentation (分詞)
    parser.add_argument(
        '--seg', '-s',
        nargs='*',
        default=[],
        help='Chinese segmenter(s) to use (can specify multiple for comparison). '
             'Available: jieba, pkuseg, lac, stanza. Use "help" to see details.'
    )

    # Segmenter mode
    parser.add_argument(
        '--mode', '-m',
        choices=['accurate', 'search'],
        default='accurate',
        help='Segmenter mode (jieba only, default: accurate)'
    )

    # Output options
    parser.add_argument(
        '--compact', '-c',
        action='store_true',
        help='Compact output without segmentation details'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Check for help requests
    if args.version and args.version.lower() == 'help':
        show_version_help()
        return 0

    if args.seg and 'help' in [s.lower() for s in args.seg]:
        show_segmenter_help()
        return 0

    if args.engs and args.engs.lower() == 'help':
        show_english_books_help()
        return 0

    if args.chineses and args.chineses.lower() == 'help':
        show_chinese_books_help()
        return 0

    # Validate version
    valid_versions = ['unv', 'lcc', 'kjv', 'esv', 'nasb', 'rcuv2010']
    if args.version not in valid_versions:
        print(f"❌ Error: Invalid version '{args.version}'", file=sys.stderr)
        print(f"Valid versions: {', '.join(valid_versions)}", file=sys.stderr)
        print(f"Use --version help to see all available versions", file=sys.stderr)
        return 1

    # Validate segmenters
    valid_segmenters = ['jieba', 'pkuseg', 'lac', 'stanza']
    invalid_segs = [s for s in args.seg if s not in valid_segmenters]
    if invalid_segs:
        print(f"❌ Error: Invalid segmenter(s): {', '.join(invalid_segs)}", file=sys.stderr)
        print(f"Valid segmenters: {', '.join(valid_segmenters)}", file=sys.stderr)
        print(f"Use --seg help to see all available segmenters", file=sys.stderr)
        return 1

    # Setup logging
    setup_logging(args.verbose)

    try:
        # Handle three modes: --verse OR --chineses OR --engs (with --chap/--sec)
        if args.verse:
            # Convenience mode: parse verse reference
            print(f"📖 Parsing verse reference: {args.verse}")
            ref = VerseParser.parse(args.verse)
            print(f"   Book: {ref.book.title()} ({ref.book_zh})")
            print(f"   Chapter: {ref.chapter}")
            if ref.is_range:
                print(f"   Verses: {ref.verse_start}-{ref.verse_end}")
            else:
                print(f"   Verse: {ref.verse_start}")
        elif args.engs:
            # English book mode: convert to Chinese
            if not args.chap:
                print("❌ Error: --chap is required when using --engs", file=sys.stderr)
                return 1

            from src.api.book_mappings import get_chinese_book_abbr

            try:
                chinese_abbr = get_chinese_book_abbr(args.engs)
            except ValueError as e:
                print(f"❌ Error: {e}", file=sys.stderr)
                return 1

            # Parse sec parameter (handle ranges like "16-17")
            if args.sec:
                if '-' in args.sec:
                    verse_parts = args.sec.split('-')
                    verse_start = int(verse_parts[0])
                    verse_end = int(verse_parts[1])
                else:
                    verse_start = verse_end = int(args.sec)
            else:
                verse_start = verse_end = None

            from src.api.book_mappings import normalize_book_name, BOOK_ABBREVIATIONS

            normalized = normalize_book_name(args.engs)
            book_name = BOOK_ABBREVIATIONS.get(normalized, normalized)

            ref = VerseReference(
                book=book_name,
                book_zh=chinese_abbr,
                chapter=args.chap,
                verse_start=verse_start if verse_start else 1,
                verse_end=verse_end if verse_end else 999
            )

            print(f"📖 English Book Reference:")
            print(f"   English: {args.engs} → {book_name.title()}")
            print(f"   Chinese: {chinese_abbr}")
            print(f"   Chapter: {ref.chapter}")
            if verse_start:
                if verse_start != verse_end:
                    print(f"   Verses: {verse_start}-{verse_end}")
                else:
                    print(f"   Verse: {verse_start}")
            else:
                print(f"   Verses: entire chapter")
        else:
            # FHL-aligned mode: use chineses, chap, sec directly
            if not args.chap:
                print("❌ Error: --chap is required when using --chineses", file=sys.stderr)
                return 1

            # Parse sec parameter (handle ranges like "16-17")
            if args.sec:
                if '-' in args.sec:
                    verse_parts = args.sec.split('-')
                    verse_start = int(verse_parts[0])
                    verse_end = int(verse_parts[1])
                else:
                    verse_start = verse_end = int(args.sec)
            else:
                # No sec specified, will fetch entire chapter
                verse_start = verse_end = None

            # Create VerseReference manually
            from src.api.book_mappings import BOOK_MAP_EN_TO_ZH

            # Find book name from Chinese abbreviation (reverse lookup)
            book_name = None
            for eng, zh in BOOK_MAP_EN_TO_ZH.items():
                if zh == args.chineses:
                    book_name = eng
                    break

            if not book_name:
                print(f"❌ Error: Unknown Chinese book abbreviation: {args.chineses}", file=sys.stderr)
                return 1

            ref = VerseReference(
                book=book_name,
                book_zh=args.chineses,
                chapter=args.chap,
                verse_start=verse_start if verse_start else 1,
                verse_end=verse_end if verse_end else 999  # Will be limited by actual chapter
            )

            print(f"📖 FHL Reference:")
            print(f"   Chinese Book: {ref.book_zh}")
            print(f"   Chapter: {ref.chapter}")
            if verse_start:
                if verse_start != verse_end:
                    print(f"   Verses: {verse_start}-{verse_end}")
                else:
                    print(f"   Verse: {verse_start}")
            else:
                print(f"   Verses: entire chapter")

        # Fetch verses from FHL API
        print(f"\n🌐 Fetching from FHL API (version: {args.version})...")
        with FHLClient() as client:
            # Check if fetching entire chapter or specific verses
            if (args.chineses or args.engs) and not args.sec:
                # Fetch entire chapter
                verses = client.fetch_chapter(
                    book_zh=ref.book_zh,
                    chapter=ref.chapter,
                    version=args.version,
                    include_strongs=args.strong
                )
            else:
                # Fetch specific verses
                verses = client.fetch_verses(
                    book_zh=ref.book_zh,
                    chapter=ref.chapter,
                    verses=ref.verses,
                    version=args.version,
                    include_strongs=args.strong
                )

            if not verses:
                print(f"\n❌ No verses found for {ref}")
                return 1

            # Update book name from reference
            for verse in verses:
                verse.book = ref.book

            # Initialize plugin manager and segmenters once
            manager = PluginManager()
            active_segmenters = {}

            if args.seg:
                for seg_name in args.seg:
                    try:
                        if seg_name == 'jieba':
                            segmenter = JiebaPlugin()
                            config = {
                                'mode': args.mode,
                                'hmm': True
                            }
                        elif seg_name == 'pkuseg':
                            segmenter = PKUSegPlugin()
                            config = {
                                'model_name': 'default'  # Default model
                            }
                        elif seg_name == 'lac':
                            segmenter = LACPlugin()
                            config = {
                                'mode': 'seg'  # Segmentation only
                            }
                        elif seg_name == 'stanza':
                            segmenter = StanzaPlugin()
                            config = {
                                'lang': 'zh',
                                'processors': 'tokenize',
                                'use_gpu': False
                            }
                        else:
                            continue

                        # Initialize and register segmenter (once)
                        segmenter.initialize(config)
                        manager.register(f'segmenter.{seg_name}', segmenter)
                        active_segmenters[seg_name] = segmenter

                    except (ImportError, RuntimeError) as e:
                        print(f"\n⚠️  Warning: {seg_name} not available: {e}")
                        if args.verbose:
                            import traceback
                            traceback.print_exc()
                        continue

            # Display verses
            print(f"\n{'=' * 60}")
            print(f"📜 {ref} ({args.version.upper()})")
            print(f"{'=' * 60}")

            for verse in verses:
                display_verse(verse, show_reference=len(verses) > 1)

                # Segment if requested and text is not empty
                if args.seg and verse.text and active_segmenters:
                    # Process each active segmenter
                    for seg_name, segmenter in active_segmenters.items():
                        try:
                            # Segment the verse text
                            segments = segmenter.segment(verse.text)

                            if not args.compact:
                                display_segmentation(verse.text, segments, seg_name)

                        except Exception as e:
                            print(f"\n⚠️  Segmentation error ({seg_name}): {e}")
                            if args.verbose:
                                import traceback
                                traceback.print_exc()
                            continue

            print(f"\n{'=' * 60}")
            print(f"✅ Fetched {len(verses)} verse(s) successfully")
            print(f"{'=' * 60}")

        return 0

    except ValueError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
