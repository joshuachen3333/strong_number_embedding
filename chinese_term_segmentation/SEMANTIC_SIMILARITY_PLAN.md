# Semantic Similarity Testing & Implementation Plan

## Executive Summary

Replace the current character-based edit distance approach in `SimilarityMatcher` with true semantic similarity engines. Test multiple approaches systematically to find the best solution for biblical Chinese term refinement.

## Problem Statement

Current limitations:
- Edit distance fails for semantically similar but lexically different terms
- Examples:
  - "獨一無二的" vs "將他的獨生" (semantically related, but high edit distance)
  - "神" vs "上帝" (synonyms, zero character overlap)
  - "愛" vs "珍愛" (related, but still fails)

## Proposed Architecture

### 1. Plugin-Based Semantic Engine Architecture

```python
# Abstract base for all semantic engines
class SemanticEngine(ABC):
    @abstractmethod
    def similarity(self, text1: str, text2: str) -> float:
        """Return semantic similarity score [0, 1]"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return engine identifier"""
        pass

# Refactored SimilarityMatcher
class SimilarityMatcher:
    def __init__(self, engine: SemanticEngine = None):
        self.engine = engine or EditDistanceEngine()  # Default fallback

    def find_best_substring(self, refTerm: str, origText: str, threshold: float = 0.6):
        # Use pluggable engine for similarity calculation
        candidates = self._generate_candidates(origText)
        best = max(candidates,
                  key=lambda x: self.engine.similarity(refTerm, x))
        return best if self.engine.similarity(refTerm, best) > threshold else None
```

### 2. Semantic Engines to Implement

#### A. EditDistanceEngine (Baseline)
- **Tech**: Levenshtein distance (current implementation)
- **Pros**: Fast, no dependencies
- **Cons**: No semantic understanding
- **Use case**: Baseline comparison

#### B. ChineseBertEngine
- **Tech**: Chinese-BERT-wwm pretrained model
- **Library**: `transformers`
- **Pros**: State-of-the-art Chinese NLP
- **Cons**: Large model (400MB+), slower
- **Implementation**:
```python
class ChineseBertEngine(SemanticEngine):
    def __init__(self):
        from transformers import AutoTokenizer, AutoModel
        self.tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-bert-wwm")
        self.model = AutoModel.from_pretrained("hfl/chinese-bert-wwm")
```

#### C. SentenceTransformerEngine
- **Tech**: Multilingual sentence embeddings
- **Library**: `sentence-transformers`
- **Model options**:
  - `distiluse-base-multilingual-cased-v2` (135MB, fast)
  - `paraphrase-multilingual-MiniLM-L12-v2` (470MB, accurate)
- **Pros**: Designed for semantic similarity, good multilingual support
- **Cons**: Not biblical-specific
- **Implementation**:
```python
class SentenceTransformerEngine(SemanticEngine):
    def __init__(self, model_name='distiluse-base-multilingual-cased-v2'):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
```

#### D. Word2VecEngine
- **Tech**: Word2Vec trained on Chinese Bible corpus
- **Library**: `gensim`
- **Data source**: UNV + LCC + RCUV parallel texts
- **Pros**: Biblical domain-specific, lightweight
- **Cons**: Requires training, word-level only

#### E. OpenAIEmbeddingEngine
- **Tech**: OpenAI text-embedding-3-small API
- **Pros**: High quality, no local compute
- **Cons**: API costs, network dependency
- **Implementation**:
```python
class OpenAIEmbeddingEngine(SemanticEngine):
    def __init__(self):
        import openai
        self.client = openai.Client()

    def similarity(self, text1: str, text2: str) -> float:
        emb1 = self.client.embeddings.create(input=text1, model="text-embedding-3-small")
        emb2 = self.client.embeddings.create(input=text2, model="text-embedding-3-small")
        return cosine_similarity(emb1, emb2)
```

#### F. LlamaChineseEngine (Future)
- **Tech**: Llama-3 Chinese fine-tuned
- **Pros**: Open source, can be fine-tuned on biblical text
- **Cons**: Requires GPU, large model

### 3. Testing Framework

#### Test Dataset Structure
```json
{
  "test_cases": [
    {
      "sn": "G3439",
      "dict_meaning": "獨一無二的, 唯一的",
      "coarse_term": "將他的獨生",
      "expected": "獨生",
      "category": "substring_extraction"
    },
    {
      "sn": "G2316",
      "dict_meaning": "神",
      "coarse_term": "上帝",
      "expected": "上帝",
      "category": "synonym_matching"
    }
  ]
}
```

#### Evaluation Metrics
1. **Accuracy**: % of correct extractions
2. **Precision@k**: Top-k candidates contain correct answer
3. **Speed**: Time per similarity calculation
4. **Memory**: Model size and RAM usage
5. **Domain accuracy**: Performance on biblical-specific terms

#### Benchmark Script
```python
def benchmark_engines(engines: List[SemanticEngine], test_data: List[dict]):
    results = {}
    for engine in engines:
        matcher = SimilarityMatcher(engine)

        correct = 0
        total_time = 0

        for test_case in test_data:
            start = time.time()
            result = matcher.find_best_substring(
                test_case['dict_meaning'],
                test_case['coarse_term']
            )
            elapsed = time.time() - start

            if result == test_case['expected']:
                correct += 1
            total_time += elapsed

        results[engine.get_name()] = {
            'accuracy': correct / len(test_data),
            'avg_time': total_time / len(test_data),
            'memory_mb': get_model_size(engine)
        }

    return results
```

### 4. Implementation Phases

#### Phase 2.1: Refactor Architecture (1 day)
- [ ] Extract SemanticEngine interface
- [ ] Refactor SimilarityMatcher to use engines
- [ ] Keep EditDistanceEngine as default
- [ ] Add engine selection to CLI (`--semantic-engine bert`)

#### Phase 2.2: Implement Basic Engines (2 days)
- [ ] ChineseBertEngine
- [ ] SentenceTransformerEngine (2 models)
- [ ] Create test dataset (50-100 cases)
- [ ] Run initial benchmarks

#### Phase 2.3: Biblical-Specific Optimization (3 days)
- [ ] Collect biblical parallel corpus
- [ ] Train Word2Vec on biblical Chinese
- [ ] Fine-tune sentence transformer on biblical text
- [ ] Create biblical-specific test cases

#### Phase 2.4: Advanced Engines (Optional, 1 week)
- [ ] OpenAI embeddings integration
- [ ] Llama Chinese integration
- [ ] Hybrid engine (combine multiple approaches)

### 5. Expected Results

| Engine | Expected Accuracy | Speed | Memory | Best For |
|--------|------------------|-------|--------|----------|
| EditDistance | 30-40% | <1ms | 1MB | Exact matches |
| ChineseBERT | 60-70% | 50ms | 400MB | General Chinese |
| SentenceTransformer | 65-75% | 20ms | 135MB | Semantic similarity |
| Word2Vec (biblical) | 70-80% | 5ms | 50MB | Biblical terms |
| OpenAI | 75-85% | 100ms | 0MB | High accuracy |

### 6. CLI Integration

```bash
# Test different engines
./segment.py --verse "John 3:16" --semantic-engine edit-distance
./segment.py --verse "John 3:16" --semantic-engine bert
./segment.py --verse "John 3:16" --semantic-engine sentence-transformer

# Compare all engines
./segment.py --verse "John 3:16" --benchmark-engines

# Output comparison table
Engine               Accuracy  Time    Refined  Match%
EditDistance         30%       0.8ms   2/10     55.6%
ChineseBERT         65%       48ms    6/10     72.3%
SentenceTransformer 70%       22ms    7/10     78.4%
```

### 7. Configuration File

```yaml
# config/semantic_engines.yaml
semantic_engines:
  default: edit-distance

  engines:
    edit-distance:
      class: EditDistanceEngine

    chinese-bert:
      class: ChineseBertEngine
      model: hfl/chinese-bert-wwm
      cache_dir: ~/.cache/transformers

    sentence-transformer:
      class: SentenceTransformerEngine
      model: distiluse-base-multilingual-cased-v2

    word2vec-biblical:
      class: Word2VecEngine
      model_path: models/biblical_chinese_w2v.bin

  thresholds:
    edit-distance: 0.6
    chinese-bert: 0.5
    sentence-transformer: 0.55
```

### 8. Testing on Real Verses

Test verses covering different challenges:
1. **Genesis 3:3** - Good baseline, many refinements possible
2. **John 3:16** - "獨生" challenge, synonyms needed
3. **Matthew 5:3** - "虛心" vs "心靈貧窮", different translations
4. **Romans 8:1** - Complex theological terms

### 9. Success Criteria

The new semantic approach is successful if:
1. **Match rate improvement**: Average +15% over edit distance
2. **Refinement rate**: >50% of terms successfully refined
3. **Speed**: <100ms per verse for production engine
4. **Accuracy**: >70% on biblical test set

### 10. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Large model sizes | Offer lightweight alternatives, lazy loading |
| Slow inference | Cache embeddings, batch processing |
| Poor biblical performance | Fine-tune on biblical corpus |
| API costs (OpenAI) | Use as optional premium feature |

## Next Steps for OpenSpec

This plan should be converted to an OpenSpec proposal:

```bash
openspec create add-semantic-similarity-engines
```

### Proposal Structure
1. **proposal.md**: This plan summarized
2. **tasks.md**: Phase 2.1-2.4 broken into checkboxes
3. **design.md**: Technical architecture details
4. **specs/**: New specs for SemanticEngine interface

### Key Requirements (R-numbers)
- R201: SemanticEngine interface definition
- R202: Minimum 3 engine implementations
- R203: Benchmark framework with metrics
- R204: CLI integration with engine selection
- R205: Configuration file support
- R206: Backward compatibility with edit distance

## Conclusion

This plan provides a systematic approach to evolving from character-based to semantic similarity matching. The plugin architecture ensures flexibility, while the testing framework enables data-driven decisions about which engine to use in production.

The key insight: **Different engines excel at different challenges**. The architecture should support using the best tool for each specific task.