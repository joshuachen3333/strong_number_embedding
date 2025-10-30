#!/usr/bin/env python3
"""
Demo script showing the plugin architecture in action.

This demonstrates:
1. Plugin registration and management
2. Segmentation of Chinese biblical text
3. Hot-swapping between different segmenters
4. Comparison of segmentation results

Usage:
    python demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.plugin_manager import PluginManager

print("=" * 70)
print("Chinese Term Segmentation - Plugin Architecture Demo")
print("=" * 70)
print()

# Sample verses
verses = {
    "Genesis 1:1": "起初上帝創造天地",
    "John 3:16": "上帝愛世人，甚至將他的獨生子賜給他們",
    "Psalm 23:1": "耶和華是我的牧者，我必不致缺乏"
}

print("📖 Sample Bible Verses (LCC):")
print("-" * 70)
for ref, text in verses.items():
    print(f"  {ref}: {text}")
print()

# Initialize plugin manager
print("🔧 Initializing Plugin Manager...")
pm = PluginManager()
print("✅ Plugin Manager ready")
print()

# ============================================
# DEMO 1: Basic Segmentation with Mock Plugin
# ============================================
print("=" * 70)
print("DEMO 1: Basic Segmentation (Mock Plugin)")
print("=" * 70)
print()

print("Creating a simple mock segmenter plugin...")

from src.core.plugin_interfaces import SegmenterPlugin
from typing import List, Dict, Optional

class SimpleMockSegmenter(SegmenterPlugin):
    """Simple character-based segmenter for demo."""

    @property
    def name(self) -> str:
        return "segmenter.simple"

    @property
    def version(self) -> str:
        return "1.0.0"

    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        # Simple: just return each character that's not punctuation
        return [c for c in text if c not in '，。、；：！？']

    def tokenize_with_metadata(self, text: str, context: Optional[Dict] = None) -> List[Dict]:
        tokens = self.tokenize(text)
        return [{"word": t, "position": i, "pos": None, "confidence": 1.0}
                for i, t in enumerate(tokens)]

    def supports_custom_dictionary(self) -> bool:
        return False

# Register and use
simple = SimpleMockSegmenter()
pm.register("segmenter.simple", simple)
simple.initialize({})

print("✅ Mock segmenter registered")
print()

verse = verses["Genesis 1:1"]
print(f"Input:  {verse}")
tokens = simple.tokenize(verse)
print(f"Output: {tokens}")
print(f"Count:  {len(tokens)} tokens")
print()

print("⚠️  Notice: Character-level segmentation is not ideal!")
print("    We need word-level segmentation for Chinese.")
print()

# ============================================
# DEMO 2: Try to Load Real Segmenters
# ============================================
print("=" * 70)
print("DEMO 2: Real Segmenters (jieba & pkuseg)")
print("=" * 70)
print()

# Try jieba
jieba_available = False
try:
    import jieba
    from src.plugins.segmenters.jieba_plugin import JiebaPlugin

    print("✅ jieba library found!")
    jieba_available = True

    jieba_plugin = JiebaPlugin()
    pm.register("segmenter.jieba", jieba_plugin)
    jieba_plugin.initialize({"hmm": True, "mode": "accurate"})

    print("✅ JiebaPlugin registered and initialized")
    print()

except ImportError:
    print("❌ jieba library not installed")
    print("   Install with: pip install jieba")
    print()

# Try pkuseg
pkuseg_available = False
try:
    import pkuseg as pkg
    from src.plugins.segmenters.pkuseg_plugin import PKUSegPlugin

    print("✅ pkuseg library found!")
    pkuseg_available = True

    pkuseg_plugin = PKUSegPlugin()
    pm.register("segmenter.pkuseg", pkuseg_plugin)
    pkuseg_plugin.initialize({"model_name": "default", "postag": False})

    print("✅ PKUSegPlugin registered and initialized")
    print()

except ImportError:
    print("❌ pkuseg library not installed")
    print("   Install with: pip install pkuseg")
    print()

# Show available plugins
available_plugins = pm.list_plugins()
print(f"📋 Registered Plugins: {', '.join(available_plugins)}")
print()

# ============================================
# DEMO 3: Tokenize with Available Plugins
# ============================================
if jieba_available or pkuseg_available:
    print("=" * 70)
    print("DEMO 3: Compare Segmentation Results")
    print("=" * 70)
    print()

    for ref, verse_text in verses.items():
        print(f"📖 {ref}")
        print(f"   Original: {verse_text}")
        print()

        if jieba_available:
            segmenter = pm.get("segmenter.jieba")
            tokens = segmenter.tokenize(verse_text)
            print(f"   jieba:    {' | '.join(tokens)}")
            print(f"             ({len(tokens)} tokens)")
            print()

        if pkuseg_available:
            segmenter = pm.get("segmenter.pkuseg")
            tokens = segmenter.tokenize(verse_text)
            print(f"   pkuseg:   {' | '.join(tokens)}")
            print(f"             ({len(tokens)} tokens)")
            print()

        print("-" * 70)
        print()

# ============================================
# DEMO 4: Plugin Hot-Swapping
# ============================================
if jieba_available and pkuseg_available:
    print("=" * 70)
    print("DEMO 4: Plugin Hot-Swapping")
    print("=" * 70)
    print()

    print("Demonstrating runtime plugin replacement...")
    print()

    # Register jieba as "main"
    pm.register("segmenter.main", jieba_plugin)
    print("1. Registered jieba as 'segmenter.main'")

    verse_text = verses["Genesis 1:1"]
    segmenter = pm.get("segmenter.main")
    tokens1 = segmenter.tokenize(verse_text)
    print(f"   Result: {' | '.join(tokens1)}")
    print()

    # Hot-swap to pkuseg
    old_plugin = pm.replace("segmenter.main", pkuseg_plugin)
    print("2. Hot-swapped to pkuseg (no restart needed!)")

    segmenter = pm.get("segmenter.main")
    tokens2 = segmenter.tokenize(verse_text)
    print(f"   Result: {' | '.join(tokens2)}")
    print()

    print("✅ Successfully swapped segmenters at runtime!")
    print()

# ============================================
# DEMO 5: Plugin Metrics
# ============================================
print("=" * 70)
print("DEMO 5: Plugin Usage Metrics")
print("=" * 70)
print()

print("Plugin usage statistics:")
print()
for plugin_name in available_plugins:
    try:
        metrics = pm.get_metrics(plugin_name)
        print(f"  {plugin_name}:")
        print(f"    - Usage count: {metrics['usage_count']}")
        print(f"    - Total time:  {metrics['total_time']:.4f}s")
        print(f"    - Errors:      {metrics['errors']}")
        print()
    except KeyError:
        print(f"  {plugin_name}: No metrics available")
        print()

# ============================================
# DEMO 6: Segmentation with Metadata
# ============================================
if jieba_available:
    print("=" * 70)
    print("DEMO 6: Segmentation with Metadata (POS Tags)")
    print("=" * 70)
    print()

    verse_text = verses["Genesis 1:1"]

    # Create fresh jieba instance for metadata demo
    from src.plugins.segmenters.jieba_plugin import JiebaPlugin
    fresh_jieba = JiebaPlugin()
    fresh_jieba.initialize({"hmm": True, "mode": "accurate"})

    segmenter = fresh_jieba

    print(f"Verse: {verse_text}")
    print()

    tokens_with_meta = segmenter.tokenize_with_metadata(verse_text)

    print("Detailed token information:")
    print()
    print(f"  {'Token':<8} {'Position':<10} {'POS Tag':<10} {'Confidence':<12}")
    print("  " + "-" * 45)

    for token in tokens_with_meta:
        print(f"  {token['word']:<8} {token['position']:<10} "
              f"{str(token.get('pos', 'N/A')):<10} {token['confidence']:<12.2f}")
    print()

# ============================================
# Summary
# ============================================
print("=" * 70)
print("Summary")
print("=" * 70)
print()

print("✅ What this demo showed:")
print("  1. Plugin registration and management")
print("  2. Multiple segmentation strategies")
if jieba_available and pkuseg_available:
    print("  3. Side-by-side comparison of results")
    print("  4. Runtime plugin hot-swapping")
print("  5. Plugin usage metrics")
if jieba_available:
    print("  6. Rich metadata (POS tags, positions)")
print()

if not jieba_available:
    print("💡 Install jieba to see more features:")
    print("   pip install jieba")
    print()

if not pkuseg_available:
    print("💡 Install pkuseg to compare segmenters:")
    print("   pip install pkuseg")
    print()

print("🎉 Demo complete!")
print()
print("Next steps:")
print("  - Create custom dictionaries (unv_bible_terms.txt, lcc_bible_terms.txt)")
print("  - Process full Bible books")
print("  - Add embedding plugins for semantic similarity")
print("  - Build alignment algorithms")
print()
