# Architecture Deep Dive: What We Built and Why

## 📖 Table of Contents

1. [The Big Picture](#the-big-picture)
2. [What We Built (Layer by Layer)](#what-we-built-layer-by-layer)
3. [How the Pieces Fit Together](#how-the-pieces-fit-together)
4. [What's Missing (and Why)](#whats-missing-and-why)
5. [The Complete Flow (When Finished)](#the-complete-flow-when-finished)
6. [Why This Architecture?](#why-this-architecture)
7. [Real-World Examples](#real-world-examples)

---

## The Big Picture

### The Problem We're Solving

**Goal**: Automatically add Strong's Numbers to Chinese Bible translations (like LCC) that don't have them yet.

**Challenge**: Chinese has no word boundaries!
```
English: "God created heaven earth" ← spaces separate words
Chinese: "上帝創造天地"                ← no spaces! Where do words start/end?
```

**Solution**: A multi-step process:

```
┌──────────────────────────────────────────────────────────────┐
│  COMPLETE PIPELINE (What We're Building)                     │
└──────────────────────────────────────────────────────────────┘

Step 1: TOKENIZATION         ✅ DONE (What we just built)
   "起初上帝創造天地"  →  ["起初", "上帝", "創造", "天地"]
   (break into words)

Step 2: EMBEDDING            ⏳ NEXT
   "上帝"  →  [0.2, -0.5, 0.8, ...] (300-dimensional vector)
   (convert to numbers that capture meaning)

Step 3: ALIGNMENT            ⏳ FUTURE
   Match: "上帝" (LCC) ↔ "אֱלֹהִים" (Hebrew) ↔ H430
   (find which Chinese word = which Hebrew/Greek word)

Step 4: ASSIGNMENT           ⏳ FUTURE
   "上帝" → H430
   (assign Strong's Number to Chinese word)

Step 5: OUTPUT               ⏳ FUTURE
   Export to: JSON, dual_reader format, etc.
```

**We just completed Step 1!** But built it in a way that makes Steps 2-5 much easier.

---

## What We Built (Layer by Layer)

Think of our system like a building with 4 floors:

```
┌─────────────────────────────────────────────────┐
│  FLOOR 4: USER INTERFACE (Not built yet)        │
│  • CLI commands                                 │
│  • Web UI                                       │
│  • dual_reader integration                      │
└─────────────────────────────────────────────────┘
                     ⬇️
┌─────────────────────────────────────────────────┐
│  FLOOR 3: BUSINESS LOGIC (Not built yet)        │
│  • Bible verse processing                       │
│  • Strong's Number assignment                   │
│  • Alignment algorithms                         │
└─────────────────────────────────────────────────┘
                     ⬇️
┌─────────────────────────────────────────────────┐
│  FLOOR 2: PLUGIN IMPLEMENTATIONS (Partial)      │
│  ✅ JiebaPlugin - Chinese tokenizer            │
│  ✅ PKUSegPlugin - Chinese tokenizer           │
│  ⏳ Word2Vec plugin - Embeddings               │
│  ⏳ Alignment plugins                           │
└─────────────────────────────────────────────────┘
                     ⬇️
┌─────────────────────────────────────────────────┐
│  FLOOR 1: PLUGIN INFRASTRUCTURE (✅ Complete)   │
│  • Plugin base classes                          │
│  • PluginManager (registration system)          │
│  • Plugin discovery (auto-find plugins)         │
│  • Configuration management                     │
└─────────────────────────────────────────────────┘
```

**We built Floor 1 (foundation) + 2 rooms on Floor 2 (segmenters)**

---

## How the Pieces Fit Together

Let me explain each file and what it does:

### 1. Core Infrastructure (`src/core/`)

#### `plugin_base.py` - The Blueprint
```python
class Plugin(ABC):
    # Every plugin must have:
    - name          # Who are you? "tokenizer.jieba"
    - version       # Which version? "1.0.0"
    - initialize()  # Setup with config
    - shutdown()    # Cleanup
```

**Analogy**: Like a **passport template** - every plugin must have these fields.

---

#### `plugin_interfaces.py` - The Contracts
```python
class SegmenterPlugin(Plugin):
    # Every tokenizer must provide:
    - tokenize()                    # Break text into words
    - tokenize_with_metadata()      # With extra info (POS tags, positions)
    - supports_custom_dictionary()  # Can you load custom words?
    - load_dictionary()             # Load custom words

class EmbeddingPlugin(Plugin):
    # Every embedding plugin must provide:
    - embed()           # Convert text to vector
    - dimension         # How long is the vector?

class AlignmentPlugin(Plugin):
    # Every alignment plugin must provide:
    - align()           # Match source words to target words

class ScorerPlugin(Plugin):
    # Every scorer must provide:
    - score()           # Calculate accuracy metrics
```

**Analogy**: Like **job descriptions** - if you want to be a Tokenizer, you MUST be able to do these tasks.

---

#### `plugin_manager.py` - The Registry/Hotel Reception
```python
class PluginManager:
    # Singleton pattern - only ONE manager for entire system

    register("tokenizer.jieba", jieba_plugin)  # Check-in
    get("tokenizer.jieba")                      # Retrieve
    replace("tokenizer.jieba", new_jieba)      # Hot-swap!
    list_plugins()                              # Who's checked in?
```

**Analogy**: Like a **hotel reception desk**
- Plugins "check in" when registered
- You ask reception when you need a plugin
- Reception keeps track of who's staying
- You can swap guests without closing the hotel!

**Why singleton?**: One central place to manage all plugins. No confusion about which plugins are available.

---

#### `plugin_discovery.py` - The Scout
```python
class PluginDiscovery:
    discover()          # Scan directories for plugin.json files
    load_plugin()       # Dynamically load plugin class
    find_by_name()      # Search for specific plugin
```

**Analogy**: Like a **talent scout** who:
1. Walks through directories looking for `plugin.json` files
2. Reads the metadata (what plugin, where is it?)
3. Loads the plugin code into memory

**Example**:
```
src/plugins/segmenters/
├── plugin.json          ← Scout finds this!
│   {
│     "name": "tokenizer.jieba",
│     "class_name": "JiebaPlugin",
│     "module_path": "jieba_plugin.py"
│   }
├── jieba_plugin.py      ← Scout loads this
└── pkuseg_plugin.py
```

---

#### `plugin_loader.py` - The Lazy Manager
```python
class PluginLoader:
    discover_plugins()   # Find all available plugins
    load()              # Load a plugin (lazy - only when needed!)
    is_cached()         # Already loaded?
    clear_cache()       # Forget loaded plugins
```

**Analogy**: Like a **lazy librarian**
- First visit: Makes a list of all books (discover)
- When you ask for a book: Goes and gets it (lazy load)
- Next time: "I already got that book for you!" (cache)
- Clear shelves: Puts books back (clear cache)

**Why lazy loading?**: Loading all plugins at startup wastes time/memory. Load only what you need, when you need it.

---

#### `config_manager.py` - The Settings Manager
```python
class ConfigManager:
    load("config.yaml")              # Load config file
    get("plugins.segmenters.jieba")  # Get specific setting
    save("output.yaml")              # Save config
```

**Analogy**: Like **user preferences** in an app
- YAML/JSON files store settings
- Environment variables can override
- Hierarchical: `plugins → segmenters → jieba → config`

**Example config**:
```yaml
plugins:
  segmenters:
    default: jieba
    jieba:
      enabled: true
      config:
        dict_path: dictionaries/unv_bible_terms.txt
        hmm: true
```

---

### 2. Plugin Implementations (`src/plugins/segmenters/`)

#### `jieba_plugin.py` - The Fast Tokenizer
```python
class JiebaPlugin(SegmenterPlugin):
    tokenize("起初上帝創造天地")
    # → ["起初", "上帝", "創造", "天地"]

    # Can load custom dictionary!
    load_dictionary("unv_bible_terms.txt")
    # Now knows: 耶和華, 尼布甲尼撒, etc. = single words
```

**Analogy**: Like a **Chinese language teacher** who:
- Knows where to split Chinese sentences
- Can learn specialized vocabulary (biblical terms)
- Fast but sometimes less accurate

**Why jieba?**
- ⚡ Very fast
- 📚 Supports custom dictionaries (essential for biblical terms!)
- 🔥 Most popular Chinese tokenizer

---

#### `pkuseg_plugin.py` - The Accurate Tokenizer
```python
class PKUSegPlugin(SegmenterPlugin):
    tokenize("起初上帝創造天地")
    # → ["起初", "上帝", "創造", "天地"]

    # Can use domain-specific models!
    initialize({"model_name": "medicine"})  # For medical texts
    initialize({"model_name": "news"})      # For news texts
```

**Analogy**: Like a **specialist translator** who:
- More accurate than jieba
- Can specialize in different domains
- Slower but higher quality

**Why pkuseg?**
- 🎯 Higher accuracy
- 🏥 Domain-specific models available
- 🔬 Better for specialized text (like biblical language)

---

### 3. Configuration (`config/`)

#### `default.yaml` - The Defaults
```yaml
plugins:
  segmenters:
    default: jieba    # Use jieba by default

    jieba:
      config:
        dict_path: ""  # No custom dictionary by default
        hmm: true      # Use HMM for unknown words
        mode: accurate # Accurate mode (vs. full or search)
```

**Purpose**: Sensible defaults that work out of the box.

---

#### `testing.yaml` - The Test Config
```yaml
plugins:
  segmenters:
    default: jieba

    jieba:
      config:
        hmm: false     # Disable HMM for predictable tests

logging:
  level: DEBUG         # Verbose logging for debugging

performance:
  cache_enabled: false # Disable cache to test fresh loads
```

**Purpose**: Special settings for testing.

---

### 4. Tests (`tests/`)

#### `test_plugin_base.py` - Tests the Blueprint
```python
def test_plugin_initialization():
    plugin = MockPlugin()
    assert plugin.name == "test.mock"
    assert not plugin.is_initialized

    plugin.initialize({"key": "value"})
    assert plugin.is_initialized
    assert plugin.config == {"key": "value"}
```

**What it tests**: T001 - Plugin Interface Validation
- Can we create plugins?
- Does initialization work?
- Does config validation work?

---

#### `test_plugin_manager.py` - Tests the Registry
```python
def test_register_plugin():
    pm = PluginManager()
    pm.register("tokenizer.mock", MockPlugin())
    assert pm.is_registered("tokenizer.mock")

def test_hot_swap():
    pm.replace("tokenizer.mock", NewPlugin())
    # Old plugin shut down, new plugin active!
```

**What it tests**: T003, T007 - Plugin Manager & Lifecycle
- Can we register plugins?
- Can we retrieve them?
- Can we hot-swap at runtime?
- Are operations thread-safe?

---

#### `test_plugin_discovery.py` - Tests the Scout
```python
def test_discover_plugins(temp_plugin_dir):
    discovery = PluginDiscovery(str(temp_plugin_dir))
    plugins = discovery.discover()

    assert len(plugins) == 1
    assert plugins[0]['name'] == 'tokenizer.test'

def test_lazy_loading():
    loader = PluginLoader()
    loader.discover_plugins()

    assert not loader.is_cached('tokenizer.test')  # Not loaded yet

    plugin = loader.load('tokenizer.test')         # Load now!

    assert loader.is_cached('tokenizer.test')      # Now cached
```

**What it tests**: T006, T008 - Discovery & Loading
- Can we find plugins automatically?
- Does lazy loading work?
- Does caching work?

---

#### `test_tokenizer_plugins.py` - Tests the Segmenters
```python
def test_tokenizer_basic():
    plugin = JiebaPlugin()
    plugin.initialize({"hmm": True})

    tokens = plugin.tokenize("起初上帝創造天地")

    assert isinstance(tokens, list)
    assert len(tokens) > 0
    assert all(isinstance(t, str) for t in tokens)
```

**What it tests**: T002 - Tokenizer Plugins
- Do segmenters work?
- Can they load dictionaries?
- Do they return correct format?

---

## What's Missing (and Why)

### What We Have ✅
```
Foundation Layer: 100% Complete
├── Plugin system
├── Plugin manager
├── Plugin discovery
├── Configuration
└── 2 segmenter plugins (jieba, pkuseg)
```

### What's Missing ⏳

#### 1. **No Bible Text Processing Yet**
```python
# This doesn't exist yet:
def process_verse(book, chapter, verse, version):
    # Load verse from JSON
    # Tokenize with chosen plugin
    # Return tokenized result
```

**Why missing?**: We built the tools first. Now we need to use them.

---

#### 2. **No Embedding Plugins**
```python
# This doesn't exist yet:
class Word2VecPlugin(EmbeddingPlugin):
    def embed(self, text):
        # Convert "上帝" to [0.2, -0.5, 0.8, ...]
```

**Why missing?**: Step 2 of the pipeline. Need Step 1 (segmentation) first.

---

#### 3. **No Alignment Algorithms**
```python
# This doesn't exist yet:
class SemanticAlignmentPlugin(AlignmentPlugin):
    def align(self, source_tokens, target_tokens):
        # Match Chinese words to Hebrew/Greek
        # Return: [("上帝", "H430"), ...]
```

**Why missing?**: Step 3 of the pipeline. Need Steps 1-2 first.

---

#### 4. **No Command-Line Tool**
```bash
# This doesn't work yet:
$ python segment.py --version lcc --book Genesis --chapter 1
Genesis 1:1 - 起初上帝創造天地
Tokenized: ['起初', '上帝', '創造', '天地']
```

**Why missing?**: CLI is "Floor 4" (user interface). We built "Floor 1" (foundation).

---

#### 5. **No Integration with dual_reader**
```javascript
// This doesn't exist yet:
fetch('/api/segment', {
  method: 'POST',
  body: JSON.stringify({
    text: "起初上帝創造天地",
    version: "lcc"
  })
})
```

**Why missing?**: Integration comes after the core system works.

---

## The Complete Flow (When Finished)

Let me show you how it will work end-to-end:

### Example: Process Genesis 1:1 in LCC

```python
# ============================================
# STEP 1: TOKENIZATION (✅ Works now!)
# ============================================
from src.core.plugin_manager import PluginManager
from src.plugins.segmenters.jieba_plugin import JiebaPlugin

pm = PluginManager()
jieba = JiebaPlugin()
pm.register("tokenizer.jieba", jieba)
jieba.initialize({
    "dict_path": "dictionaries/lcc_bible_terms.txt",
    "hmm": True
})

lcc_text = "起初上帝創造天地"
tokens = jieba.tokenize(lcc_text)
# Result: ["起初", "上帝", "創造", "天地"]

# ============================================
# STEP 2: EMBEDDING (⏳ Future)
# ============================================
from src.plugins.embeddings.word2vec_plugin import Word2VecPlugin

w2v = Word2VecPlugin()
w2v.initialize({"model_path": "models/chinese_word2vec.bin"})

embeddings = {}
for token in tokens:
    embeddings[token] = w2v.embed(token)
# Result: {
#   "起初": [0.2, -0.5, 0.8, ...],  # 300-dim vector
#   "上帝": [0.1, 0.3, -0.2, ...],
#   ...
# }

# ============================================
# STEP 3: GET ORIGINAL TEXT (⏳ Future)
# ============================================
# Load UNV (Chinese with Strong's) and Hebrew (BHS)
unv_text = "起初<H7225>上帝<H430>創造<H1254>天<H8064>地<H776>"
unv_tokens = extract_with_strongs(unv_text)
# Result: [
#   ("起初", "H7225"),
#   ("上帝", "H430"),
#   ("創造", "H1254"),
#   ("天", "H8064"),
#   ("地", "H776")
# ]

hebrew_text = load_hebrew("Genesis", 1, 1)
# Result: "בְּרֵאשִׁית בָּרָא אֱלֹהִים אֵת הַשָּׁמַיִם וְאֵת הָאָרֶץ"

# ============================================
# STEP 4: ALIGNMENT (⏳ Future)
# ============================================
from src.plugins.aligners.semantic_aligner import SemanticAligner

aligner = SemanticAligner()
aligner.initialize({
    "semantic_weight": 0.7,
    "positional_weight": 0.3
})

alignments = aligner.align(
    source=unv_tokens,      # Chinese with Strong's
    target=tokens,          # LCC Chinese
    original=hebrew_text    # Hebrew
)
# Result: [
#   ("起初", "H7225", 0.95),  # 95% confidence
#   ("上帝", "H430", 0.92),
#   ("創造", "H1254", 0.88),
#   ("天地", "H8064+H776", 0.85)  # Compound
# ]

# ============================================
# STEP 5: OUTPUT (⏳ Future)
# ============================================
result = {
    "book": "Genesis",
    "chapter": 1,
    "verse": 1,
    "version": "lcc",
    "text": "起初上帝創造天地",
    "tokens": [
        {"word": "起初", "strong": "H7225", "confidence": 0.95},
        {"word": "上帝", "strong": "H430", "confidence": 0.92},
        {"word": "創造", "strong": "H1254", "confidence": 0.88},
        {"word": "天地", "strong": "H8064+H776", "confidence": 0.85}
    ]
}

# Export to dual_reader format
export_to_json(result, "output/genesis_1_1.json")

# ============================================
# STEP 6: INTEGRATE WITH DUAL READER (⏳ Future)
# ============================================
# In dual_reader_right_editor:
# - Load this JSON
# - Display LCC text with clickable Strong's numbers
# - Enable A2 cross-reader highlighting
# - Allow manual corrections
```

---

## Why This Architecture?

### Design Principle 1: **Strategy Pattern**
```python
# WITHOUT plugin architecture:
if tokenizer == "jieba":
    tokens = jieba_tokenize(text)
elif tokenizer == "pkuseg":
    tokens = pkuseg_tokenize(text)
elif tokenizer == "lac":
    tokens = lac_tokenize(text)
# ❌ Have to modify code for each new tokenizer!

# WITH plugin architecture:
tokenizer = pm.get(config['tokenizer'])
tokens = tokenizer.tokenize(text)
# ✅ Add new segmenters without changing code!
```

**Benefits**:
- Easy to add new segmenters
- Easy to experiment (swap jieba ↔ pkuseg)
- Test different strategies without code changes

---

### Design Principle 2: **Hot-Swapping**
```python
# Start with jieba
pm.register("tokenizer.main", jieba_plugin)

# Mid-processing: Realize pkuseg is better!
pm.replace("tokenizer.main", pkuseg_plugin)
# ✅ Switch WITHOUT restarting the program
```

**Benefits**:
- A/B testing in production
- Gradual rollout of new algorithms
- Zero downtime upgrades

---

### Design Principle 3: **Lazy Loading**
```python
# Discover 50 plugins at startup
loader.discover_plugins()  # Fast! Just reads metadata

# Load only what you need
tokenizer = loader.load("tokenizer.jieba")  # Now loads jieba code
# Other 49 plugins still not loaded → saves memory
```

**Benefits**:
- Fast startup
- Low memory usage
- Only pay for what you use

---

### Design Principle 4: **Configuration Over Code**
```yaml
# Change behavior without touching code:
plugins:
  segmenters:
    default: pkuseg  # Just change this line!

    pkuseg:
      config:
        model_name: medicine  # Switch to medical model
```

**Benefits**:
- Non-programmers can configure
- Different configs for different use cases
- Easy to version control settings

---

## Real-World Examples

### Example 1: Experimenting with Segmenters
```python
# Test which tokenizer is better for biblical Chinese

pm = PluginManager()

# Try jieba
jieba = JiebaPlugin()
pm.register("tokenizer.test", jieba)
jieba.initialize({"dict_path": "lcc_terms.txt"})
jieba_result = jieba.tokenize("起初上帝創造天地")
# ['起初', '上帝', '創造', '天地']

# Try pkuseg
pkuseg = PKUSegPlugin()
pm.replace("tokenizer.test", pkuseg)
pkuseg.initialize({"model_name": "default"})
pkuseg_result = pkuseg.tokenize("起初上帝創造天地")
# ['起初', '上帝', '創造', '天', '地']  ← Different!

# Compare and pick the better one
evaluate(jieba_result, pkuseg_result)
```

---

### Example 2: Processing Multiple Versions
```python
# Process both UNV and LCC with appropriate dictionaries

pm = PluginManager()

# Setup UNV tokenizer
jieba_unv = JiebaPlugin()
pm.register("tokenizer.unv", jieba_unv)
jieba_unv.initialize({"dict_path": "dictionaries/unv_bible_terms.txt"})

# Setup LCC tokenizer
jieba_lcc = JiebaPlugin()
pm.register("tokenizer.lcc", jieba_lcc)
jieba_lcc.initialize({"dict_path": "dictionaries/lcc_bible_terms.txt"})

# Process
unv_tokens = pm.get("tokenizer.unv").tokenize(unv_text)
lcc_tokens = pm.get("tokenizer.lcc").tokenize(lcc_text)
```

---

### Example 3: Custom Dictionary Impact
```python
# Without custom dictionary
jieba.initialize({"dict_path": ""})
tokens = jieba.tokenize("尼布甲尼撒王")
# Result: ['尼', '布', '甲', '尼', '撒', '王']  ❌ Wrong!

# With custom dictionary (has "尼布甲尼撒" = Nebuchadnezzar)
jieba.initialize({"dict_path": "unv_bible_terms.txt"})
tokens = jieba.tokenize("尼布甲尼撒王")
# Result: ['尼布甲尼撒', '王']  ✅ Correct!
```

**Why it matters**: Biblical names/terms are often split incorrectly without custom dictionaries.

---

## Summary: What We Have vs. What We Need

### ✅ What We Built (Foundation)
- Plugin system (can register/swap/discover plugins)
- 2 segmenter plugins (jieba, pkuseg)
- Configuration management
- Test suite proving it works

### ⏳ What We Need (Applications)
- Bible text processing pipeline
- Embedding plugins (Word2Vec, BERT)
- Alignment plugins (semantic + positional)
- Command-line tool
- Integration with dual_reader

### 🎯 The Analogy
We built a **professional kitchen** with:
- ✅ Commercial stove (plugin system)
- ✅ Sharp knives (segmenters)
- ✅ Recipe book (configuration)
- ⏳ But no ingredients yet (Bible data)
- ⏳ And no dishes cooked yet (aligned verses)

---

**The kitchen is ready. Now we need to start cooking!**

Would you like to:
1. Create a simple demo to "taste test" what we built?
2. Start building the next layer (embedding plugins)?
3. Skip to integration (connect to dual_reader)?
