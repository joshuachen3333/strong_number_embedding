#!/usr/bin/env python3
"""
Simple demo - works WITHOUT installing jieba or pkuseg.

This shows the plugin architecture working with a mock segmenter.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.plugin_manager import PluginManager
from src.core.plugin_interfaces import SegmenterPlugin
from typing import List, Dict, Optional

print("=" * 60)
print("Simple Plugin Architecture Demo")
print("=" * 60)
print()

# Create a simple mock segmenter
class MockSegmenter(SegmenterPlugin):
    """Mock segmenter that splits Chinese into meaningful words."""

    @property
    def name(self) -> str:
        return "segmenter.mock"

    @property
    def version(self) -> str:
        return "1.0.0"

    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        # Simple rules for demo (not accurate Chinese segmentation!)
        # This is just to show the plugin system working
        words = []
        i = 0
        while i < len(text):
            # Skip punctuation
            if text[i] in '，。、；：！？':
                i += 1
                continue

            # Take 2-character words (biblical terms are often 2 chars)
            if i + 1 < len(text):
                words.append(text[i:i+2])
                i += 2
            else:
                words.append(text[i])
                i += 1

        return words

    def tokenize_with_metadata(self, text: str, context: Optional[Dict] = None) -> List[Dict]:
        tokens = self.tokenize(text)
        return [
            {
                "word": word,
                "position": i,
                "pos": None,
                "confidence": 1.0
            }
            for i, word in enumerate(tokens)
        ]

    def supports_custom_dictionary(self) -> bool:
        return False

# Initialize plugin system
print("1. Creating PluginManager...")
pm = PluginManager()
print("   ✅ PluginManager created (singleton)")
print()

# Register plugin
print("2. Registering MockSegmenter plugin...")
mock = MockSegmenter()
pm.register("segmenter.mock", mock)
print(f"   ✅ Registered: {mock.name} v{mock.version}")
print()

# Initialize plugin
print("3. Initializing plugin...")
mock.initialize({})
print("   ✅ Plugin initialized")
print()

# List registered plugins
print("4. Listing registered plugins...")
plugins = pm.list_plugins()
print(f"   Registered plugins: {plugins}")
print()

# Tokenize a verse
print("5. Tokenizing Bible verses...")
print()

verses = {
    "Genesis 1:1": "起初上帝創造天地",
    "John 3:16": "上帝愛世人",
    "Psalm 23:1": "耶和華是我的牧者"
}

for ref, verse in verses.items():
    print(f"   📖 {ref}")
    print(f"      Input:  {verse}")

    # Get plugin and tokenize
    segmenter = pm.get("segmenter.mock")
    tokens = segmenter.tokenize(verse)

    print(f"      Output: {' | '.join(tokens)}")
    print(f"      Tokens: {len(tokens)}")
    print()

# Show metrics
print("6. Plugin usage metrics:")
metrics = pm.get_metrics("segmenter.mock")
print(f"   Usage count: {metrics['usage_count']}")
print(f"   Errors:      {metrics['errors']}")
print()

# Demonstrate hot-swapping
print("7. Demonstrating hot-swap...")
print("   Creating second segmenter...")

class MockSegmenter2(SegmenterPlugin):
    """Second mock segmenter (different strategy)."""

    @property
    def name(self) -> str:
        return "segmenter.mock2"

    @property
    def version(self) -> str:
        return "2.0.0"

    def tokenize(self, text: str, context: Optional[Dict] = None) -> List[str]:
        # Different strategy: 1-character tokens
        return [c for c in text if c not in '，。、；：！？']

    def tokenize_with_metadata(self, text: str, context: Optional[Dict] = None) -> List[Dict]:
        tokens = self.tokenize(text)
        return [{"word": t, "position": i, "pos": None, "confidence": 1.0}
                for i, t in enumerate(tokens)]

    def supports_custom_dictionary(self) -> bool:
        return False

mock2 = MockSegmenter2()
mock2.initialize({})

print("   Replacing segmenter.mock with new version...")
old_plugin = pm.replace("segmenter.mock", mock2)
print(f"   ✅ Swapped: v{old_plugin.version} → v{mock2.version}")
print()

# Tokenize again with new plugin
verse = verses["Genesis 1:1"]
segmenter = pm.get("segmenter.mock")
tokens = segmenter.tokenize(verse)
print(f"   New result: {' | '.join(tokens)}")
print()

print("=" * 60)
print("✅ Demo Complete!")
print("=" * 60)
print()
print("What this demonstrated:")
print("  ✅ Plugin registration")
print("  ✅ Plugin retrieval")
print("  ✅ Chinese segmentation")
print("  ✅ Hot-swapping at runtime")
print("  ✅ Usage metrics")
print()
print("Next: Run demo.py for real segmenters (jieba, pkuseg)")
print("      Install with: pip install jieba pkuseg")
print()
