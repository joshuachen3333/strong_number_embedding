# Semantic Engine Technical Specifications

## Engine Implementation Details

### 1. EditDistanceEngine (Baseline)

**Current Implementation Status**: ✅ Already exists in `SimilarityMatcher`

```python
class EditDistanceEngine(SemanticEngine):
    def __init__(self):
        self.variant_map = {
            '爲': '為',  # U+7232 → U+70BA
            '衞': '衛',  # U+885E → U+885B
            '綫': '線',  # U+7DAB → U+7DDA
        }

    def similarity(self, text1: str, text2: str) -> float:
        # Step 1: Normalize character variants
        text1_norm = self._normalize_variants(text1)
        text2_norm = self._normalize_variants(text2)

        # Step 2: Calculate Levenshtein distance
        distance = self._edit_distance(text1_norm, text2_norm)

        # Step 3: Normalize to [0, 1]
        max_len = max(len(text1_norm), len(text2_norm))
        if max_len == 0:
            return 0.0
        return 1.0 - (distance / max_len)
```

**Technical Notes**:
- Time complexity: O(m×n) for strings of length m, n
- Space complexity: O(m×n) for DP table
- Character variant normalization adds preprocessing step
- No external dependencies

---

### 2. ChineseBertEngine

**Model**: [hfl/chinese-bert-wwm](https://huggingface.co/hfl/chinese-bert-wwm) or alternatives

```python
class ChineseBertEngine(SemanticEngine):
    def __init__(self, model_name='hfl/chinese-bert-wwm-ext',
                 device='cpu', cache_dir='~/.cache/transformers'):
        from transformers import AutoTokenizer, AutoModel
        import torch

        self.device = torch.device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir
        )
        self.model = AutoModel.from_pretrained(
            model_name,
            cache_dir=cache_dir
        ).to(self.device)
        self.model.eval()

        # Cache for repeated terms
        self._embedding_cache = {}

    def get_embedding(self, text: str):
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use [CLS] token embedding (first token)
            embedding = outputs.last_hidden_state[:, 0, :].squeeze()

        self._embedding_cache[text] = embedding
        return embedding

    def similarity(self, text1: str, text2: str) -> float:
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)

        # Cosine similarity
        cos_sim = torch.nn.functional.cosine_similarity(
            emb1.unsqueeze(0),
            emb2.unsqueeze(0)
        )
        return cos_sim.item()
```

**Model Options**:
- `hfl/chinese-bert-wwm`: Base model, 102M parameters
- `hfl/chinese-bert-wwm-ext`: Extended vocab, better coverage
- `hfl/chinese-roberta-wwm-ext`: RoBERTa architecture, often better
- `hfl/chinese-macbert-base`: MacBERT, handles typos better

**Installation**:
```bash
pip install transformers torch
# Download model (first run)
# Size: ~400MB per model
```

**Performance Considerations**:
- GPU acceleration: 10x speedup with CUDA
- Batch processing: Process multiple candidates together
- Embedding cache: Store computed embeddings
- Quantization: Use `torch.quantization` for 4x smaller model

---

### 3. SentenceTransformerEngine

**Library**: [sentence-transformers](https://www.sbert.net/)

```python
class SentenceTransformerEngine(SemanticEngine):
    def __init__(self, model_name='distiluse-base-multilingual-cased-v2',
                 device='cpu', cache_folder='~/.cache/torch/sentence_transformers'):
        from sentence_transformers import SentenceTransformer, util

        self.model = SentenceTransformer(
            model_name,
            device=device,
            cache_folder=cache_folder
        )
        self.util = util

        # Pre-compute common biblical terms
        self.biblical_cache = {}

    def encode_batch(self, texts: List[str]):
        """Batch encoding for efficiency"""
        return self.model.encode(
            texts,
            convert_to_tensor=True,
            normalize_embeddings=True,  # L2 normalization
            show_progress_bar=False
        )

    def similarity(self, text1: str, text2: str) -> float:
        embeddings = self.encode_batch([text1, text2])
        similarity = self.util.cos_sim(embeddings[0], embeddings[1])
        return similarity.item()

    def find_best_substring_optimized(self, refTerm: str, origText: str,
                                      threshold: float = 0.6) -> str:
        """Optimized version using batch processing"""
        # Generate all candidates
        candidates = self._generate_candidates(origText)

        # Batch encode all at once
        all_texts = [refTerm] + candidates
        embeddings = self.encode_batch(all_texts)

        ref_emb = embeddings[0]
        cand_embs = embeddings[1:]

        # Compute all similarities at once
        similarities = self.util.cos_sim(ref_emb, cand_embs)[0]

        # Find best match
        best_idx = similarities.argmax()
        best_score = similarities[best_idx].item()

        if best_score > threshold:
            return candidates[best_idx]
        return None
```

**Model Options & Characteristics**:

| Model | Size | Languages | Speed | Quality | Use Case |
|-------|------|-----------|-------|---------|----------|
| `paraphrase-multilingual-MiniLM-L12-v2` | 470MB | 50+ | Fast | High | Best overall |
| `paraphrase-multilingual-mpnet-base-v2` | 1.1GB | 100+ | Medium | Highest | Maximum accuracy |
| `distiluse-base-multilingual-cased-v2` | 540MB | 15 | Fast | Good | European + Chinese |
| `LaBSE` | 1.9GB | 109 | Slow | High | Most languages |
| `m3e-base` | 410MB | Chinese | Fast | High | Chinese-specific |

**Chinese-Specific Models**:
```python
# For better Chinese performance
model_name = 'moka-ai/m3e-base'  # Chinese sentence embeddings
# or
model_name = 'shibing624/text2vec-base-chinese'  # Trained on Chinese corpora
```

**Installation**:
```bash
pip install sentence-transformers
# Models download automatically on first use
```

---

### 4. Word2VecEngine (Biblical Domain-Specific)

**Training Data Preparation**:
```python
class Word2VecEngine(SemanticEngine):
    def __init__(self, model_path=None, vector_size=300, window=5):
        import gensim
        from gensim.models import Word2Vec
        import jieba

        self.jieba = jieba

        if model_path and os.path.exists(model_path):
            self.model = Word2Vec.load(model_path)
        else:
            self.model = None
            self.vector_size = vector_size
            self.window = window

    def train_on_biblical_corpus(self, corpus_files: List[str]):
        """Train Word2Vec on Chinese biblical texts"""
        # Step 1: Prepare sentences
        sentences = []
        for file_path in corpus_files:
            # Read UNV, LCC, RCUV2010 texts
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Tokenize with jieba
                    words = list(self.jieba.cut(line.strip()))
                    if len(words) > 1:
                        sentences.append(words)

        # Step 2: Train Word2Vec
        self.model = Word2Vec(
            sentences=sentences,
            vector_size=self.vector_size,
            window=self.window,
            min_count=2,
            workers=4,
            sg=1,  # Skip-gram
            hs=0,  # Negative sampling
            negative=5,
            epochs=10
        )

        # Step 3: Build biblical synonym mappings
        self._build_biblical_synonyms()

    def _build_biblical_synonyms(self):
        """Discover biblical synonyms from trained model"""
        self.biblical_synonyms = {}

        # Key biblical terms to find synonyms for
        key_terms = ['神', '上帝', '耶和華', '基督', '聖靈', '救恩',
                     '罪', '愛', '信心', '恩典', '十字架', '復活']

        for term in key_terms:
            if term in self.model.wv:
                # Find top 5 similar terms
                similar = self.model.wv.most_similar(term, topn=5)
                self.biblical_synonyms[term] = [w for w, score in similar if score > 0.6]

    def similarity(self, text1: str, text2: str) -> float:
        if not self.model:
            return 0.0

        # Tokenize
        words1 = list(self.jieba.cut(text1))
        words2 = list(self.jieba.cut(text2))

        # Get valid words (in vocabulary)
        valid1 = [w for w in words1 if w in self.model.wv]
        valid2 = [w for w in words2 if w in self.model.wv]

        if not valid1 or not valid2:
            return 0.0

        # Compute average vectors
        vec1 = sum(self.model.wv[w] for w in valid1) / len(valid1)
        vec2 = sum(self.model.wv[w] for w in valid2) / len(valid2)

        # Cosine similarity
        from numpy import dot
        from numpy.linalg import norm
        return dot(vec1, vec2) / (norm(vec1) * norm(vec2))
```

**Training Script**:
```bash
# Prepare corpus from FHL data
python prepare_biblical_corpus.py \
    --versions unv,lcc,rcuv2010 \
    --output corpus/biblical_chinese.txt

# Train Word2Vec
python train_word2vec.py \
    --input corpus/biblical_chinese.txt \
    --output models/biblical_w2v.model \
    --size 300 \
    --window 5
```

---

### 5. FastTextEngine (Subword-Aware)

**Advantage**: Handles out-of-vocabulary words using character n-grams

```python
class FastTextEngine(SemanticEngine):
    def __init__(self, model_path=None):
        import fasttext

        if model_path:
            self.model = fasttext.load_model(model_path)
        else:
            # Use pretrained Chinese model
            # Download from: https://fasttext.cc/docs/en/crawl-vectors.html
            self.model = fasttext.load_model('cc.zh.300.bin')  # 4GB file

    def train_on_biblical(self, corpus_path: str):
        """Fine-tune on biblical text"""
        import fasttext

        self.model = fasttext.train_unsupervised(
            corpus_path,
            model='skipgram',
            dim=300,
            ws=5,
            epoch=10,
            minCount=2,
            minn=3,  # Character n-grams
            maxn=6,
            neg=5,
            thread=4
        )

    def similarity(self, text1: str, text2: str) -> float:
        # FastText handles phrases naturally
        vec1 = self.model.get_sentence_vector(text1)
        vec2 = self.model.get_sentence_vector(text2)

        from numpy import dot
        from numpy.linalg import norm
        return dot(vec1, vec2) / (norm(vec1) * norm(vec2))
```

---

### 6. LLM-Based Engines (Commercial APIs)

#### 6a. OpenAI Engine

```python
class OpenAIEngine(SemanticEngine):
    def __init__(self, api_key: str = None, model: str = 'text-embedding-3-small'):
        import openai
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        self.model = model  # or 'text-embedding-3-large' for better quality
        self._cache = {}

    def get_embedding(self, text: str) -> List[float]:
        if text in self._cache:
            return self._cache[text]

        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        embedding = response.data[0].embedding
        self._cache[text] = embedding
        return embedding

    def similarity(self, text1: str, text2: str) -> float:
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)

        # Cosine similarity
        from numpy import dot
        from numpy.linalg import norm
        return dot(emb1, emb2) / (norm(emb1) * norm(emb2))

    def semantic_search_gpt(self, refTerm: str, origText: str) -> str:
        """Alternative: Use GPT for direct extraction"""
        prompt = f"""
        Given the Strong's Dictionary term: {refTerm}
        Find the best matching substring in: {origText}

        Consider semantic similarity, not just character matching.
        Return only the substring, no explanation.

        Substring:
        """

        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a biblical Chinese expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=50
        )

        return response.choices[0].message.content.strip()
```

**Cost Analysis**:
- text-embedding-3-small: $0.02 / 1M tokens (~$0.001 per verse)
- text-embedding-3-large: $0.13 / 1M tokens (~$0.007 per verse)
- GPT-4 extraction: ~$0.01 per query

#### 6b. Claude Engine (Anthropic)

```python
class ClaudeEngine(SemanticEngine):
    def __init__(self, api_key: str = None):
        import anthropic

        self.client = anthropic.Anthropic(
            api_key=api_key or os.getenv('ANTHROPIC_API_KEY')
        )

    def semantic_extraction(self, refTerm: str, origText: str) -> str:
        """Use Claude for semantic substring extraction"""
        message = self.client.messages.create(
            model="claude-3-haiku-20240307",  # Fast and cheap
            max_tokens=50,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": f"""找出語意最相似的子字串。

參考詞（Strong's Dictionary）: {refTerm}
原文: {origText}

只返回子字串，不要解釋。
子字串必須是原文的連續部分。

答案:"""
                }
            ]
        )

        return message.content[0].text.strip()

    def batch_process(self, test_cases: List[dict]) -> List[str]:
        """Process multiple cases for efficiency"""
        # Claude supports batching for better pricing
        batch_prompt = "Process each case:\n\n"
        for i, case in enumerate(test_cases):
            batch_prompt += f"Case {i+1}:\n"
            batch_prompt += f"Reference: {case['refTerm']}\n"
            batch_prompt += f"Text: {case['origText']}\n\n"

        # Single API call for all cases
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            temperature=0,
            messages=[{"role": "user", "content": batch_prompt}]
        )

        # Parse results
        return self._parse_batch_results(response.content[0].text)
```

**Cost Analysis**:
- Claude 3 Haiku: $0.25/$1.25 per 1M tokens (input/output)
- Claude 3 Sonnet: $3/$15 per 1M tokens
- ~$0.0001 per verse with Haiku

#### 6c. Google Gemini Engine

```python
class GeminiEngine(SemanticEngine):
    def __init__(self, api_key: str = None):
        import google.generativeai as genai

        genai.configure(api_key=api_key or os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Or 'gemini-pro'

        # Use embedding model
        self.embed_model = genai.GenerativeModel('models/text-embedding-004')

    def get_embedding(self, text: str) -> List[float]:
        result = self.embed_model.embed_content(
            content=text,
            task_type="semantic_similarity",
            title="Biblical Chinese"
        )
        return result.embedding

    def semantic_extraction(self, refTerm: str, origText: str) -> str:
        prompt = f"""
        任務：語意子字串匹配

        參考詞義（來自Strong's Dictionary）: {refTerm}
        搜尋文本: {origText}

        找出搜尋文本中與參考詞義最相似的連續子字串。
        只返回子字串本身。

        答案：
        """

        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=50
            )
        )

        return response.text.strip()
```

**Cost Analysis**:
- Gemini 1.5 Flash: Free tier (15 RPM, 1M tokens/day)
- Gemini 1.5 Pro: $3.50/$10.50 per 1M tokens
- text-embedding-004: Free up to limit

#### 6d. Local LLM Engine (Ollama)

```python
class OllamaEngine(SemanticEngine):
    def __init__(self, model: str = 'qwen2.5:7b', host: str = 'http://localhost:11434'):
        import ollama

        self.client = ollama.Client(host=host)
        self.model = model

        # Pull model if not exists
        try:
            self.client.show(model)
        except:
            print(f"Pulling model {model}...")
            self.client.pull(model)

    def get_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings(
            model=self.model,
            prompt=text
        )
        return response['embedding']

    def semantic_extraction(self, refTerm: str, origText: str) -> str:
        prompt = f"""找出最相似的子字串：
參考: {refTerm}
文本: {origText}
子字串:"""

        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            options={
                'temperature': 0.1,
                'num_predict': 50
            }
        )

        return response['response'].strip()
```

**Model Options**:
- `qwen2.5:7b` - Good Chinese support, 7B parameters
- `llama3.2:3b` - Smaller, faster
- `gemma2:9b` - Google's model, good multilingual
- `yi:6b` - Chinese-focused model

---

## Performance Comparison Matrix

| Engine | Speed | Memory | Accuracy | Cost | Offline | Setup Complexity |
|--------|-------|--------|----------|------|---------|------------------|
| EditDistance | ⚡⚡⚡⚡⚡ | 1MB | ⭐⭐ | Free | ✅ | None |
| ChineseBERT | ⚡⚡ | 400MB | ⭐⭐⭐⭐ | Free | ✅ | Medium |
| SentenceTransformer | ⚡⚡⚡ | 135-1900MB | ⭐⭐⭐⭐ | Free | ✅ | Low |
| Word2Vec | ⚡⚡⚡⚡ | 50MB | ⭐⭐⭐ | Free | ✅ | High (training) |
| FastText | ⚡⚡⚡⚡ | 4GB | ⭐⭐⭐⭐ | Free | ✅ | Medium |
| OpenAI | ⚡⚡⚡ | 0MB | ⭐⭐⭐⭐⭐ | $$ | ❌ | Low |
| Claude | ⚡⚡⚡ | 0MB | ⭐⭐⭐⭐⭐ | $$ | ❌ | Low |
| Gemini | ⚡⚡⚡ | 0MB | ⭐⭐⭐⭐⭐ | Free/$ | ❌ | Low |
| Ollama | ⚡⚡ | 4-8GB | ⭐⭐⭐⭐ | Free | ✅ | Medium |

## Configuration Example

```yaml
# config/semantic_engines.yaml
engines:
  # Offline engines
  edit-distance:
    class: EditDistanceEngine
    enabled: true

  chinese-bert:
    class: ChineseBertEngine
    model: hfl/chinese-bert-wwm-ext
    device: cuda  # or cpu
    cache_dir: ~/.cache/transformers
    enabled: true

  sentence-transformer:
    class: SentenceTransformerEngine
    model: shibing624/text2vec-base-chinese  # Chinese-specific
    device: cuda
    enabled: true

  word2vec:
    class: Word2VecEngine
    model_path: models/biblical_chinese_w2v.model
    enabled: false  # Requires training

  # API-based engines
  openai:
    class: OpenAIEngine
    model: text-embedding-3-small
    api_key: ${OPENAI_API_KEY}  # From environment
    enabled: false

  claude:
    class: ClaudeEngine
    model: claude-3-haiku-20240307
    api_key: ${ANTHROPIC_API_KEY}
    enabled: false

  gemini:
    class: GeminiEngine
    model: gemini-1.5-flash
    api_key: ${GEMINI_API_KEY}
    enabled: true  # Free tier available

  ollama:
    class: OllamaEngine
    model: qwen2.5:7b
    host: http://localhost:11434
    enabled: false  # Requires local setup

# Engine selection strategy
strategy:
  default: sentence-transformer
  fallback_chain:
    - sentence-transformer
    - chinese-bert
    - edit-distance

  # Use different engines for different scenarios
  rules:
    - condition: "verse_length > 100"
      engine: chinese-bert  # Better for long text
    - condition: "is_poetry"
      engine: word2vec  # Better for poetic language
    - condition: "require_highest_accuracy"
      engine: claude  # Best accuracy but costs money
```

## Implementation Checklist

```python
# Test script to verify all engines
def test_all_engines():
    test_case = {
        'refTerm': '獨一無二的',
        'origText': '將他的獨生',
        'expected': '獨生'
    }

    engines = [
        EditDistanceEngine(),
        ChineseBertEngine(),
        SentenceTransformerEngine(),
        # Word2VecEngine('models/biblical.model'),
        # OpenAIEngine(),  # Requires API key
        # ClaudeEngine(),  # Requires API key
        # GeminiEngine(),  # Requires API key
        # OllamaEngine(),  # Requires local setup
    ]

    for engine in engines:
        matcher = SimilarityMatcher(engine)
        result = matcher.find_best_substring(
            test_case['refTerm'],
            test_case['origText']
        )
        print(f"{engine.get_name()}: {result}")
```

## Notes for Future Implementation

1. **Start with**: SentenceTransformer (best balance)
2. **For production**: Cache embeddings in Redis/SQLite
3. **For accuracy**: Ensemble multiple engines
4. **For speed**: Batch processing, GPU acceleration
5. **For Chinese**: Use Chinese-specific models when available
6. **For cost**: Implement usage quotas for API engines