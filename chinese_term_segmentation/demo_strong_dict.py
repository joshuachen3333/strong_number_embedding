#!/usr/bin/env python3
"""Demo: FHL Strong's Dictionary API (Phase 1.5.1)

Shows how the API can fetch semantic meanings for Strong's Numbers,
which will be used in Phase 1.5.2-1.5.3 for term refinement.
"""

from src.api.fhl_client import FHLClient

def main():
    print("\n" + "="*70)
    print("📚 FHL Strong's Dictionary API Demo (Phase 1.5.1)")
    print("="*70)
    print("\nThis demonstrates fetching semantic meanings for Strong's Numbers.")
    print("These meanings will be used to refine coarse UNV boundaries.")
    print()

    client = FHLClient(timeout=15)

    # Example Strong's Numbers from John 3:16
    test_cases = [
        ("G2316", "神 (God)", "UNV: 神<G2316>"),
        ("G25", "愛 (love)", "UNV: 愛<G25>"),
        ("G2889", "世人 (world)", "UNV: 世人<G2889>"),
        ("G5620", "甚至 (so that)", "UNV: 甚至<G5620>"),
        ("G3439", "獨生 (only begotten)", "UNV: 將他的獨生<G3439> ← coarse!"),
        ("G5207", "子 (son)", "UNV: 子<G5207>"),
        ("G1325", "賜給 (give)", "UNV: 賜給<G1325>"),
    ]

    print("Test Case: John 3:16 (約翰福音 3:16)")
    print("-" * 70)

    for sn, expected, context in test_cases:
        print(f"\n📖 {sn} - {expected}")
        print(f"   Context: {context}")

        entry = client.fetch_strong_dict(sn)

        if entry:
            print(f"   ✅ Found:")
            print(f"      Original: {entry.original}")
            print(f"      Chinese:  {entry.chinese_meaning}")

            # Show the refinement potential
            if sn == "G3439":
                print(f"\n   🔍 Refinement Preview (Phase 1.5.2):")
                print(f"      Coarse UNV:  '將他的獨生' (FHL boundary)")
                print(f"      SN Meaning:  '{entry.chinese_meaning}'")
                print(f"      → Refined:   '獨生' (best substring match)")
                print(f"      → Then match in LCC: '賜下獨生子' ✓")
        else:
            print(f"   ❌ Not found")

    # Show caching
    print("\n" + "="*70)
    print("⚡ Caching Demo")
    print("="*70)

    print("\nFetching G3439 again (should be instant from cache)...")
    entry = client.fetch_strong_dict("G3439")
    print(f"✅ Cached result: {entry.chinese_meaning}")

    print("\nFetching G25 again...")
    entry = client.fetch_strong_dict("G25")
    print(f"✅ Cached result: {entry.chinese_meaning}")

    # Hebrew example
    print("\n" + "="*70)
    print("🕎 Hebrew Strong's Numbers (Old Testament)")
    print("="*70)

    hebrew_cases = [
        ("H430", "神/上帝", "Genesis 1:1"),
        ("H1254", "創造", "Genesis 1:1"),
        ("H8064", "天", "Genesis 1:1"),
        ("H776", "地", "Genesis 1:1"),
    ]

    for sn, expected, verse in hebrew_cases:
        entry = client.fetch_strong_dict(sn)
        if entry:
            print(f"\n{sn} ({verse}): {entry.original}")
            print(f"   Chinese: {entry.chinese_meaning}")

    print("\n" + "="*70)
    print("✅ Phase 1.5.1 Complete!")
    print("="*70)
    print("\n📊 What this enables:")
    print("  • Fetch semantic meanings for any Strong's Number")
    print("  • Use meanings to refine coarse FHL boundaries")
    print("  • Example: '將他的獨生<G3439>' → extract just '獨生'")
    print()
    print("🚀 Next Phase (1.5.2): Similarity Matcher")
    print("  • Find best substring match using edit distance")
    print("  • Handle character variants (爲/為, 衞/衛)")
    print("  • Use SN meanings to refine UNV terms")
    print()

    client.close()

if __name__ == "__main__":
    main()
