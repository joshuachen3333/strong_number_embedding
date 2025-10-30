#!/usr/bin/env python3
"""
Custom demo - Add your own verses here!

This is YOUR playground to experiment with segmentation.
Modify the verses dictionary to test your own Chinese biblical text.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.plugin_manager import PluginManager

print("=" * 70)
print("Custom Verse Segmentation Demo")
print("=" * 70)
print()

# ============================================
# 📝 ADD YOUR VERSES HERE!
# ============================================
# Format: {"Reference": "Chinese text"}
# You can add as many verses as you want!

verses = {
    # Old Testament examples (you can add more!)
    "Genesis 1:1": "起初上帝創造天地",
    "Psalm 23:1": "耶和華是我的牧者，我必不致缺乏",

    # New Testament examples (you can add more!)
    "John 3:16": "上帝愛世人，甚至將他的獨生子賜給他們",
    "Matthew 5:3": "虛心的人有福了，因為天國是他們的",

    # 👇 NEWLY ADDED VERSES! 👇
    "John 1:1": "太初有道，道與上帝同在，道就是上帝",
    "Romans 8:28": "我們曉得萬事都互相效力，叫愛上帝的人得益處",
    "Proverbs 3:5": "你要專心仰賴耶和華，不可倚靠自己的聰明",
    "Philippians 4:13": "我靠著那加給我力量的，凡事都能做",
}

# ============================================
# Load segmenter plugins
# ============================================
pm = PluginManager()

# Try to load jieba
jieba_available = False
try:
    import jieba
    from src.plugins.segmenters.jieba_plugin import JiebaPlugin

    jieba_plugin = JiebaPlugin()
    pm.register("segmenter.jieba", jieba_plugin)
    jieba_plugin.initialize({"hmm": True, "mode": "accurate"})
    jieba_available = True
    print("✅ Using jieba segmenter")
except ImportError:
    print("❌ jieba not installed - using simple segmenter")
    print("   Install with: pip install jieba")

# Fallback to simple segmenter if jieba not available
if not jieba_available:
    from src.core.plugin_interfaces import SegmenterPlugin
    from typing import List, Dict, Optional

    class SimpleSegmenter(SegmenterPlugin):
        @property
        def name(self) -> str:
            return "segmenter.simple"

        @property
        def version(self) -> str:
            return "1.0.0"

        def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
            # Simple: 2-char chunks
            words = []
            text_clean = ''.join(c for c in text if c not in '，。、；：！？')
            for i in range(0, len(text_clean), 2):
                if i + 1 < len(text_clean):
                    words.append(text_clean[i:i+2])
                else:
                    words.append(text_clean[i])
            return words

        def tokenize_with_metadata(self, text: str, context: Optional[Dict] = None) -> List[Dict]:
            tokens = self.tokenize(text)
            return [{"word": t, "position": i, "pos": None, "confidence": 1.0}
                    for i, t in enumerate(tokens)]

        def supports_custom_dictionary(self) -> bool:
            return False

    simple = SimpleSegmenter()
    pm.register("segmenter.simple", simple)
    simple.initialize({})
    print("✅ Using simple segmenter")

print()

# ============================================
# Process all verses
# ============================================
print("=" * 70)
print("Segmentation Results")
print("=" * 70)
print()

for ref, text in verses.items():
    print(f"📖 {ref}")
    print(f"   原文: {text}")
    print()

    # Get segmenter
    if jieba_available:
        segmenter = pm.get("segmenter.jieba")
    else:
        segmenter = pm.get("segmenter.simple")

    # Tokenize
    tokens = segmenter.tokenize(text)

    # Display results
    print(f"   分詞: {' | '.join(tokens)}")
    print(f"   共 {len(tokens)} 個詞")

    # Optional: Show with metadata if using jieba
    if jieba_available:
        tokens_meta = segmenter.tokenize_with_metadata(text)
        print()
        print("   詳細資訊:")
        for token in tokens_meta:
            pos = token.get('pos', 'N/A')
            print(f"     • {token['word']:<6} (詞性: {pos})")

    print()
    print("-" * 70)
    print()

# ============================================
# Statistics
# ============================================
print("=" * 70)
print("統計資訊 (Statistics)")
print("=" * 70)
print()

total_verses = len(verses)
total_chars = sum(len(text) for text in verses.values())

if jieba_available:
    segmenter = pm.get("segmenter.jieba")
else:
    segmenter = pm.get("segmenter.simple")

all_tokens = []
for text in verses.values():
    all_tokens.extend(segmenter.tokenize(text))

total_tokens = len(all_tokens)

print(f"處理的經文數量: {total_verses}")
print(f"總字元數:      {total_chars}")
print(f"總詞彙數:      {total_tokens}")
print(f"平均每節詞數:  {total_tokens / total_verses:.1f}")
print()

# Find longest/shortest tokens
if all_tokens:
    longest = max(all_tokens, key=len)
    shortest = min(all_tokens, key=len)
    print(f"最長的詞: {longest} ({len(longest)} 字元)")
    print(f"最短的詞: {shortest} ({len(shortest)} 字元)")
    print()

# ============================================
# Word frequency
# ============================================
print("=" * 70)
print("高頻詞彙 (Most Common Words)")
print("=" * 70)
print()

from collections import Counter
word_freq = Counter(all_tokens)
most_common = word_freq.most_common(10)

print("Top 10 most frequent words:")
for word, count in most_common:
    print(f"  {word:<6} : {count} 次")
print()

# ============================================
# Tips
# ============================================
print("=" * 70)
print("💡 Tips for Experimenting")
print("=" * 70)
print()

print("1. Add more verses:")
print('   verses["Matthew 6:9"] = "我們在天上的父，願人都尊你的名為聖"')
print()

print("2. Try different segmenters:")
print("   pip install pkuseg")
print("   # Then modify the code to use pkuseg")
print()

print("3. Load custom dictionary:")
print("   jieba_plugin.load_dictionary('dictionaries/lcc_bible_terms.txt')")
print("   # Add biblical terms to prevent wrong segmentation")
print()

print("4. Process Bible books:")
print("   # Load from ../original_text_preparation/bible_text_json/")
print()

print("5. Compare with other versions:")
print("   # Add UNV, RCUV2010, etc. and compare segmentation")
print()

print("🎉 Happy experimenting!")
print()
