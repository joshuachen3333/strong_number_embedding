# Demo Scripts Guide

This directory contains demo scripts that showcase the plugin architecture in action.

## Quick Start

### Option 1: Simple Demo (No Installation Required) ⚡

Run this first - **works immediately without installing anything**:

```bash
python demo_simple.py
```

**What it shows:**
- ✅ Plugin registration and management
- ✅ Segmentation of Chinese verses
- ✅ Runtime hot-swapping
- ✅ Usage metrics
- ⚡ Uses mock tokenizer (no external dependencies)

**Expected output:**
```
Simple Plugin Architecture Demo
================================

1. Creating PluginManager...
   ✅ PluginManager created (singleton)

2. Registering MockSegmenter plugin...
   ✅ Registered: tokenizer.mock v1.0.0

3. Initializing plugin...
   ✅ Plugin initialized

...

📖 Genesis 1:1
   Input:  起初上帝創造天地
   Output: 起初 | 上帝 | 創造 | 天地
   Tokens: 4
```

---

### Option 2: Full Demo (Requires jieba/pkuseg) 🚀

Install segmenters first:
```bash
pip install jieba pkuseg
```

Then run:
```bash
python demo.py
```

**What it shows:**
- ✅ Everything from simple demo
- ✅ Real Chinese segmentation with jieba
- ✅ Real Chinese segmentation with pkuseg
- ✅ Side-by-side comparison
- ✅ POS tagging and metadata
- 🎯 Production-quality segmentation

**Expected output:**
```
Chinese Term Segmentation - Plugin Architecture Demo
=====================================================

📖 Sample Bible Verses (LCC):
----------------------------------------------------------------------
  Genesis 1:1: 起初上帝創造天地
  John 3:16: 上帝愛世人，甚至將他的獨生子賜給他們
  Psalm 23:1: 耶和華是我的牧者，我必不致缺乏

...

DEMO 3: Compare Segmentation Results
=====================================

📖 Genesis 1:1
   Original: 起初上帝創造天地

   jieba:    起初 | 上帝 | 創造 | 天地
             (4 tokens)

   pkuseg:   起初 | 上帝 | 創造 | 天地
             (4 tokens)

...

DEMO 4: Plugin Hot-Swapping
============================

1. Registered jieba as 'tokenizer.main'
   Result: 起初 | 上帝 | 創造 | 天地

2. Hot-swapped to pkuseg (no restart needed!)
   Result: 起初 | 上帝 | 創造 | 天地

✅ Successfully swapped segmenters at runtime!
```

---

## What Each Demo Shows

### Demo Simple (`demo_simple.py`)

**Purpose**: Prove the plugin architecture works without external dependencies.

**Demonstrates**:
1. `PluginManager` singleton creation
2. Plugin registration via `.register()`
3. Plugin retrieval via `.get()`
4. Segmentation of Chinese biblical text
5. Runtime plugin replacement via `.replace()`
6. Usage metrics collection

**Best for**:
- First-time users
- Quick validation
- Understanding the architecture
- CI/CD testing (no dependencies)

---

### Demo Full (`demo.py`)

**Purpose**: Show real-world segmentation with production-ready libraries.

**Demonstrates**:
1. Everything from simple demo
2. **Real segmentation** with jieba (結巴分詞)
3. **Real segmentation** with pkuseg (北大分詞)
4. **Comparison** of different segmenters
5. **POS tagging** (Part-of-Speech: noun, verb, etc.)
6. **Metadata** (position, confidence, etc.)
7. **Hot-swapping** between real segmenters

**Best for**:
- Production use
- Algorithm comparison
- Quality evaluation
- Real Bible verse processing

---

## Understanding the Output

### Segmentation Formats

#### Standard Output
```python
tokens = ['起初', '上帝', '創造', '天地']
```
- List of strings
- Each string is a word/term
- Order preserved from original text

#### With Metadata
```python
[
  {"word": "起初", "position": 0, "pos": "t", "confidence": 1.0},
  {"word": "上帝", "position": 1, "pos": "n", "confidence": 1.0},
  {"word": "創造", "position": 2, "pos": "v", "confidence": 1.0},
  {"word": "天地", "position": 3, "pos": "n", "confidence": 1.0}
]
```
- `word`: The token
- `position`: 0-indexed position in token list
- `pos`: Part-of-speech tag (n=noun, v=verb, t=time, etc.)
- `confidence`: Segmentation confidence (0.0-1.0)

### POS Tag Meanings

Common tags from jieba:
- `n` - Noun (名詞): 上帝, 天地
- `v` - Verb (動詞): 創造, 愛
- `t` - Time word (時間詞): 起初
- `r` - Pronoun (代詞): 我, 他
- `d` - Adverb (副詞): 必, 甚至
- `p` - Preposition (介詞): 的, 是

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'src'"

**Solution**: Run from project root:
```bash
cd chinese_term_segmentation
python demo_simple.py
```

---

### Issue: "ImportError: No module named 'jieba'"

**Solution**: Install jieba:
```bash
pip install jieba
```

Or use `demo_simple.py` which doesn't require jieba.

---

### Issue: Segmentation seems wrong

**Expected!** The mock tokenizer in `demo_simple.py` is deliberately simplistic.

For accurate segmentation, use `demo.py` with real libraries:
```bash
pip install jieba pkuseg
python demo.py
```

---

### Issue: "pkuseg model download failed"

**Solution**: PKUSeg downloads models on first use. Requires internet connection.

Alternative: Use jieba only (faster, no download needed):
```python
# In demo.py, comment out pkuseg sections
```

---

## Next Steps After Demo

After running the demos, you can:

### 1. Create Custom Dictionary

Create `dictionaries/lcc_bible_terms.txt`:
```
耶和華
尼布甲尼撒
所羅門
以馬內利
```

Then use it:
```python
jieba_plugin.load_dictionary("dictionaries/lcc_bible_terms.txt")
```

### 2. Process Real Bible Text

Load from parent project:
```python
import json

with open("../original_text_preparation/bible_text_json/lcc/genesis.json") as f:
    genesis = json.load(f)

for verse in genesis["verses"]:
    tokens = tokenizer.tokenize(verse["text"])
    print(f"{verse['chapter']}:{verse['verse']} → {tokens}")
```

### 3. Compare Segmenters

Run both and compare results:
```python
verse = "起初上帝創造天地"

jieba_result = jieba_plugin.tokenize(verse)
pkuseg_result = pkuseg_plugin.tokenize(verse)

if jieba_result != pkuseg_result:
    print(f"Different results!")
    print(f"  jieba:  {jieba_result}")
    print(f"  pkuseg: {pkuseg_result}")
```

### 4. Build Bible Processing Pipeline

Next OpenSpec proposal: Process full books
```python
def process_book(book_name, version, tokenizer_name):
    """Process an entire Bible book."""
    # Load book JSON
    # Tokenize each verse
    # Save results
```

---

## Demo Files

```
demo_simple.py      # Mock tokenizer, no dependencies (150 lines)
demo.py             # Real segmenters, requires jieba/pkuseg (300+ lines)
DEMO_README.md      # This file
```

---

## Sample Output Comparison

### Genesis 1:1 Segmentation

**Original**: 起初上帝創造天地

**Mock Tokenizer** (demo_simple.py):
```
['起初', '上帝', '創造', '天地']  # 2-char chunks
```

**jieba** (demo.py):
```
['起初', '上帝', '創造', '天地']  # Accurate Chinese words
```

**pkuseg** (demo.py):
```
['起初', '上帝', '創造', '天地']  # Also accurate, different algorithm
```

**Character-based** (wrong!):
```
['起', '初', '上', '帝', '創', '造', '天', '地']  # Too fine-grained
```

---

## Questions?

- Check `README.md` for overall project guide
- Check `ARCHITECTURE_EXPLAINED.md` for deep dive
- Check test files in `tests/` for examples
- Check OpenSpec docs in `openspec/specs/`

Happy tokenizing! 🎉
