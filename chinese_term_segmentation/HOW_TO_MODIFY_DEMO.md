# How to Modify demo_custom.py

## Quick Start: Adding Your Own Verses

### Step 1: Open the file
```bash
# Use your favorite editor:
code demo_custom.py          # VS Code
vim demo_custom.py           # Vim
open -a TextEdit demo_custom.py  # macOS TextEdit
```

### Step 2: Find the verses section (around line 24)
```python
verses = {
    "Genesis 1:1": "起初上帝創造天地",
    "Psalm 23:1": "耶和華是我的牧者，我必不致缺乏",
    "John 3:16": "上帝愛世人，甚至將他的獨生子賜給他們",
    "Matthew 5:3": "虛心的人有福了，因為天國是他們的",

    # 👇 ADD YOUR VERSES HERE 👇
}
```

### Step 3: Add your verses

#### Example 1: Add Single Verse
```python
verses = {
    # ... existing verses ...

    # Your new verses:
    "John 1:1": "太初有道，道與上帝同在，道就是上帝",
}
```

#### Example 2: Add Multiple Verses
```python
verses = {
    # ... existing verses ...

    # Famous verses:
    "Romans 8:28": "我們曉得萬事都互相效力，叫愛上帝的人得益處",
    "Philippians 4:13": "我靠著那加給我力量的，凡事都能做",
    "Proverbs 3:5": "你要專心仰賴耶和華，不可倚靠自己的聰明",
}
```

#### Example 3: Add Full Chapter
```python
# Genesis 1 (first 5 verses)
verses = {
    "Genesis 1:1": "起初上帝創造天地",
    "Genesis 1:2": "地是空虛混沌，淵面黑暗；上帝的靈運行在水面上",
    "Genesis 1:3": "上帝說：要有光，就有了光",
    "Genesis 1:4": "上帝看光是好的，就把光暗分開了",
    "Genesis 1:5": "上帝稱光為晝，稱暗為夜。有晚上，有早晨，這是頭一日",
}
```

### Step 4: Run your modified demo
```bash
python demo_custom.py
```

---

## Advanced Modifications

### Modification 1: Load Custom Dictionary

Add this after line 53 (after jieba_plugin.initialize):

```python
jieba_plugin.initialize({"hmm": True, "mode": "accurate"})

# Add this:
try:
    jieba_plugin.load_dictionary("dictionaries/lcc_bible_terms.txt")
    print("✅ Loaded custom dictionary")
except:
    print("⚠️  Custom dictionary not found")
```

### Modification 2: Compare Two Segmenters

Replace the segmentation section with:

```python
# Load both jieba and pkuseg
jieba_tokenizer = pm.get("tokenizer.jieba")
pkuseg_tokenizer = pm.get("tokenizer.pkuseg")  # Requires: pip install pkuseg

for ref, text in verses.items():
    print(f"📖 {ref}")
    print(f"   原文: {text}")

    # Tokenize with both
    jieba_tokens = jieba_tokenizer.tokenize(text)
    pkuseg_tokens = pkuseg_tokenizer.tokenize(text)

    print(f"   jieba:  {' | '.join(jieba_tokens)}")
    print(f"   pkuseg: {' | '.join(pkuseg_tokens)}")

    # Show differences
    if jieba_tokens != pkuseg_tokens:
        print("   ⚠️  Different results!")
    else:
        print("   ✅ Both agree!")
    print()
```

### Modification 3: Export Results to JSON

Add at the end:

```python
import json

# Prepare output
output = {
    "verses": [],
    "statistics": {
        "total_verses": total_verses,
        "total_tokens": total_tokens,
        "average_tokens": total_tokens / total_verses
    }
}

for ref, text in verses.items():
    tokens = tokenizer.tokenize(text)
    tokens_meta = tokenizer.tokenize_with_metadata(text)

    output["verses"].append({
        "reference": ref,
        "text": text,
        "tokens": tokens,
        "tokens_with_metadata": tokens_meta
    })

# Save to file
with open("segmentation_results.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("✅ Saved to segmentation_results.json")
```

### Modification 4: Load Verses from File

Create `my_verses.txt`:
```
Genesis 1:1|起初上帝創造天地
John 3:16|上帝愛世人，甚至將他的獨生子賜給他們
Psalm 23:1|耶和華是我的牧者，我必不致缺乏
```

Then replace the verses dictionary:

```python
# Load verses from file
verses = {}
with open("my_verses.txt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        ref, text = line.split("|")
        verses[ref] = text
```

### Modification 5: Color Output (Terminal)

Add color to make output prettier:

```python
# Add these color codes at the top
class Color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# Then use in output:
print(f"{Color.BLUE}📖 {ref}{Color.END}")
print(f"   {Color.GREEN}分詞: {' | '.join(tokens)}{Color.END}")
```

---

## Practical Examples

### Example 1: Find Verses with Specific Words

```python
# After tokenizing all verses, find ones containing "上帝"
god_verses = []
for ref, text in verses.items():
    tokens = tokenizer.tokenize(text)
    if "上帝" in tokens:
        god_verses.append(ref)

print(f"Found '上帝' in {len(god_verses)} verses:")
for ref in god_verses:
    print(f"  - {ref}")
```

### Example 2: Compare Segmentation Accuracy

```python
# Manually create "correct" segmentation
gold_standard = {
    "Genesis 1:1": ["起初", "上帝", "創造", "天地"],
}

for ref, correct_tokens in gold_standard.items():
    text = verses[ref]
    predicted_tokens = tokenizer.tokenize(text)

    if predicted_tokens == correct_tokens:
        print(f"✅ {ref}: Perfect!")
    else:
        print(f"❌ {ref}: Differences found")
        print(f"   Expected: {correct_tokens}")
        print(f"   Got:      {predicted_tokens}")
```

### Example 3: Process Full Bible Book

```python
import json

# Load Genesis from parent project
with open("../original_text_preparation/bible_text_json/lcc/genesis.json") as f:
    genesis = json.load(f)

# Process all verses
for verse_data in genesis["verses"]:
    ref = f"Genesis {verse_data['chapter']}:{verse_data['verse']}"
    text = verse_data['text']
    tokens = tokenizer.tokenize(text)

    verses[ref] = text

print(f"Loaded {len(verses)} verses from Genesis")
```

---

## Tips & Tricks

### Tip 1: Quick Verse Lookup
Keep a separate file `common_verses.txt` with frequently used verses.

### Tip 2: Batch Processing
Process multiple books at once and save results.

### Tip 3: Error Checking
Add try-except blocks for file operations:

```python
try:
    with open("verses.txt") as f:
        # process file
except FileNotFoundError:
    print("❌ File not found!")
except Exception as e:
    print(f"❌ Error: {e}")
```

### Tip 4: Performance Testing
Measure segmentation speed:

```python
import time

start = time.time()
for text in verses.values():
    tokens = tokenizer.tokenize(text)
end = time.time()

print(f"Processed {len(verses)} verses in {end - start:.3f} seconds")
print(f"Average: {(end - start) / len(verses) * 1000:.1f} ms per verse")
```

---

## Common Issues

### Issue 1: UnicodeDecodeError
**Solution**: Always use `encoding="utf-8"` when opening files:
```python
with open("file.txt", encoding="utf-8") as f:
    # ...
```

### Issue 2: Dictionary Key Already Exists
**Solution**: Each reference must be unique. Use different keys:
```python
verses = {
    "Genesis 1:1 (UNV)": "起初神創造天地",
    "Genesis 1:1 (LCC)": "起初上帝創造天地",
}
```

### Issue 3: Tokenizer Not Available
**Solution**: Check if installed and handle gracefully:
```python
try:
    tokenizer = pm.get("tokenizer.jieba")
except KeyError:
    print("jieba not available, using fallback")
    tokenizer = pm.get("tokenizer.simple")
```

---

## Next Level: Integration

After experimenting with demo_custom.py, you can:

1. **Export to dual_reader format**
   - Convert segmentation results to JSON that dual_reader can display

2. **Build Bible processing pipeline**
   - Process entire books automatically

3. **Create custom dictionaries**
   - Extract biblical terms from UNV
   - Build LCC-specific dictionary

4. **Compare versions**
   - Tokenize same verses in UNV, LCC, RCUV2010
   - Analyze differences

---

## Quick Reference

**Add verse**:
```python
verses["Reference"] = "Chinese text"
```

**Run**:
```bash
python demo_custom.py
```

**Export results**:
Add JSON export code from Modification 3

**Compare segmenters**:
Add comparison code from Modification 2

---

Happy experimenting! 🎉
