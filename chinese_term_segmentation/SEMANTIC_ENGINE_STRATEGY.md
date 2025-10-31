# Semantic Engine Strategy Document

## Executive Summary

This document outlines 10 strategic considerations for implementing semantic similarity engines in the Chinese biblical term segmentation project, along with specific recommendations for each area.

---

## 1. Hybrid Engine Strategy - Combining Multiple Approaches

### Current Gap
Our design assumes one engine at a time, missing potential synergies from combining approaches.

### Proposed Solution
```python
class HybridEngine(SemanticEngine):
    def __init__(self, engines: List[SemanticEngine], weights: List[float] = None):
        """Combine multiple engines with weighted voting"""
        self.engines = engines
        self.weights = weights or [1.0] * len(engines)

    def similarity(self, text1: str, text2: str) -> float:
        scores = []
        for engine, weight in zip(self.engines, self.weights):
            try:
                score = engine.similarity(text1, text2)
                scores.append(score * weight)
            except:
                continue  # Skip failed engines

        return sum(scores) / sum(self.weights[:len(scores)])
```

### Use Cases
- **Exact + Semantic**: EditDistance (weight=2.0) for exact matches + BERT (weight=1.0) for semantics
- **Fast + Accurate**: Word2Vec (weight=1.5) for speed + SentenceTransformer (weight=1.0) for accuracy
- **Consensus voting**: Multiple engines vote, take weighted average

### Recommendation
✅ **Implement HybridEngine as a core feature**, not an afterthought. Start with EditDistance + SentenceTransformer combination.

---

## 2. Cascading Strategy - Speed vs Accuracy Tradeoff

### Problem
Running expensive models on every query wastes resources when simpler solutions suffice.

### Proposed Architecture
```python
class CascadingEngine(SemanticEngine):
    def find_best_substring(self, refTerm: str, origText: str) -> str:
        # Level 1: Exact match (0ms)
        if refTerm in origText:
            return refTerm

        # Level 2: Normalized exact match (0.1ms)
        normalized_ref = self.normalize_variants(refTerm)
        normalized_text = self.normalize_variants(origText)
        if normalized_ref in normalized_text:
            return self.extract_original(normalized_ref, origText)

        # Level 3: Edit distance for near matches (1ms)
        result = self.edit_engine.find(refTerm, origText)
        if result and self.edit_engine.similarity(refTerm, result) > 0.8:
            return result

        # Level 4: Semantic embedding (50ms)
        result = self.semantic_engine.find(refTerm, origText)
        if result and self.semantic_engine.similarity(refTerm, result) > 0.6:
            return result

        # Level 5: LLM extraction (500ms)
        if self.enable_llm_fallback:
            return self.llm_engine.extract(refTerm, origText)

        return None
```

### Performance Impact
- 60% of cases resolved at Level 1-2 (< 1ms)
- 30% resolved at Level 3 (< 2ms)
- 8% need Level 4 (< 50ms)
- 2% need Level 5 (< 500ms)
- **Average response time: ~8ms** instead of uniform 50ms

### Recommendation
✅ **Implement cascading as default behavior**. Make it configurable via `--cascade-levels 1,2,3,4`.

---

## 3. Biblical Domain Knowledge Integration

### Current Limitation
General-purpose engines lack biblical/theological understanding.

### Proposed Biblical Knowledge Base
```python
class BiblicalKnowledgeBase:
    def __init__(self):
        # Divine names and titles
        self.divine_names = {
            'primary': ['耶和華', '上帝', '神', '主'],
            'titles': ['全能者', '至高者', '創造主', '救主'],
            'trinity': ['聖父', '聖子', '聖靈']
        }

        # Theological concept clusters
        self.concept_clusters = {
            'salvation': ['救恩', '救贖', '拯救', '贖罪', '稱義'],
            'covenant': ['約', '舊約', '新約', '恩約', '律法之約'],
            'worship': ['敬拜', '讚美', '頌讚', '崇拜', '事奉'],
            'sin': ['罪', '過犯', '罪孽', '惡', '不義']
        }

        # Book-specific terminology
        self.book_specific = {
            'Psalms': ['細拉', '流離歌', '訓誨詩'],
            'Leviticus': ['燔祭', '素祭', '平安祭', '贖罪祭'],
            'Revelation': ['獸', '印', '號筒', '碗']
        }

        # Denominational variations
        self.denominational = {
            'catholic': {'聖母': '馬利亞', '彌撒': '崇拜'},
            'protestant': {'馬利亞': '馬利亞', '崇拜': '崇拜'}
        }

class BiblicalContextEngine(SemanticEngine):
    def __init__(self, kb: BiblicalKnowledgeBase):
        self.kb = kb
        self.base_engine = SentenceTransformerEngine()

    def similarity(self, text1: str, text2: str) -> float:
        # Check for known theological synonyms
        if self._are_theological_synonyms(text1, text2):
            return 0.95

        # Check concept clusters
        cluster_boost = self._get_cluster_boost(text1, text2)

        # Base similarity
        base_score = self.base_engine.similarity(text1, text2)

        # Apply domain knowledge boost
        return min(1.0, base_score + cluster_boost)
```

### Benefits
- Handles divine name variations correctly
- Preserves theological meaning
- Respects denominational differences

### Recommendation
✅ **Build BiblicalKnowledgeBase from strong_dict_json/**. Use as enhancement layer over base engines.

---

## 4. Context Window Problem - Beyond Single Terms

### Problem
Biblical meaning often depends on context:
- "約" alone → could be "approximately" or "covenant"
- "新約" → "New Testament"
- "立約" → "make covenant"

### Proposed Solution
```python
class ContextAwareEngine(SemanticEngine):
    def __init__(self, window_size: int = 3):
        self.window_size = window_size
        self.base_engine = ChineseBertEngine()

    def find_with_context(self, refTerm: str, origText: str,
                         left_context: str = "", right_context: str = "") -> str:
        """Consider surrounding context when matching"""

        # Get all candidates from origText
        candidates = self._generate_candidates(origText)

        best_score = 0
        best_match = None

        for candidate in candidates:
            # Find candidate's context in origText
            cand_left, cand_right = self._extract_context(candidate, origText)

            # Compute context-aware similarity
            # Compare: (left_context + refTerm + right_context)
            #     with: (cand_left + candidate + cand_right)

            full_ref = f"{left_context}{refTerm}{right_context}"
            full_cand = f"{cand_left}{candidate}{cand_right}"

            score = self.base_engine.similarity(full_ref, full_cand)

            if score > best_score:
                best_score = score
                best_match = candidate

        return best_match if best_score > 0.6 else None
```

### Real Example
```python
# Without context: "約" might match wrong meaning
find("約", "這約是用血立的")  # Might return "約" from "大約"

# With context: Correct match
find_with_context("約", "這約是用血立的",
                 left_context="這", right_context="是")  # Returns correct "約"
```

### Recommendation
✅ **Add context window as optional enhancement**. Default to no context, enable with `--use-context-window 3`.

---

## 5. Evaluation Metrics - Beyond Simple Accuracy

### Current Metrics
- Accuracy: % correct
- Speed: ms per query
- Memory: MB used

### Proposed Comprehensive Metrics
```python
class BiblicalEvaluationMetrics:
    def evaluate(self, test_set: List[TestCase]) -> Dict:
        return {
            # Accuracy metrics
            'exact_match_accuracy': self._exact_match_rate(),
            'theological_accuracy': self._theological_correctness(),
            'semantic_accuracy': self._semantic_preservation(),

            # Quality metrics
            'denominational_sensitivity': self._check_denominational_bias(),
            'poetic_preservation': self._evaluate_poetry_quality(),
            'rare_term_handling': self._rare_term_accuracy(),

            # Performance metrics
            'p50_latency': self._percentile(50),
            'p95_latency': self._percentile(95),
            'throughput': self._queries_per_second(),

            # Robustness metrics
            'variant_handling': self._character_variant_success(),
            'typo_tolerance': self._typo_robustness(),
            'ooV_handling': self._out_of_vocabulary_rate()
        }

    def _theological_correctness(self) -> float:
        """Check if theological meaning is preserved"""
        test_cases = [
            ("三位一體", ["聖父", "聖子", "聖靈"], True),  # Should recognize trinity
            ("救恩", ["救贖", "拯救"], True),  # Salvation synonyms
            ("邪靈", ["聖靈"], False)  # Should NOT match opposites
        ]
        # ... evaluate
```

### Benchmark Dataset Structure
```yaml
biblical_benchmark:
  categories:
    - name: "Divine Names"
      test_cases:
        - ref: "神"
          text: "上帝創造天地"
          expected: "上帝"
          weight: 2.0  # Important case

    - name: "Rare Terms"
      test_cases:
        - ref: "細拉"
          text: "當讚美神細拉"
          expected: "細拉"
          weight: 1.0

    - name: "Poetry"
      test_cases:
        - ref: "慈愛"
          text: "你的慈愛比生命更好"
          expected: "慈愛"
          preserve_rhythm: true
```

### Recommendation
✅ **Create biblical_benchmark_v1.yaml** with 200+ test cases across categories. Weight theological accuracy 2x higher than general accuracy.

---

## 6. Adaptive Engine Selection - Learning from Usage

### Current Approach
Static rules in YAML configuration.

### Proposed Adaptive System
```python
class AdaptiveEngineSelector:
    def __init__(self):
        self.performance_history = defaultdict(list)
        self.context_features = ContextFeatureExtractor()
        self.selection_model = self._initialize_model()

    def select_engine(self, refTerm: str, origText: str,
                     verse_ref: VerseReference) -> SemanticEngine:
        # Extract features
        features = {
            'term_length': len(refTerm),
            'text_length': len(origText),
            'has_variants': self._has_char_variants(refTerm),
            'is_poetry': verse_ref.book in ['Psalms', 'Proverbs'],
            'is_ot': verse_ref.is_old_testament(),
            'term_frequency': self._get_term_frequency(refTerm),
            'last_successful_engine': self._get_last_success(refTerm)
        }

        # Predict best engine
        if self.has_sufficient_history():
            engine_name = self.selection_model.predict(features)
        else:
            engine_name = self._rule_based_selection(features)

        return self.engines[engine_name]

    def record_feedback(self, engine: str, refTerm: str,
                       result: str, user_accepted: bool):
        """Learn from user corrections"""
        self.performance_history[engine].append({
            'ref': refTerm,
            'result': result,
            'accepted': user_accepted,
            'timestamp': time.time()
        })

        # Retrain selection model periodically
        if len(self.performance_history[engine]) % 100 == 0:
            self._retrain_selection_model()
```

### User Feedback Collection
```python
# In CLI:
if args.interactive_mode:
    result = engine.find(refTerm, origText)
    print(f"Found: {result}")
    response = input("Accept? (y/n/correct): ")

    if response.startswith('correct:'):
        correct_answer = response.split(':', 1)[1]
        selector.record_feedback(engine_name, refTerm,
                                result, False)
        # Train on correct answer
```

### Recommendation
✅ **Start with rule-based, add learning after collecting 1000+ feedback samples**. Store feedback in SQLite for analysis.

---

## 7. Three-Tier Caching Strategy

### Architecture
```python
class ThreeTierCache:
    def __init__(self):
        # Tier 1: In-memory LRU cache (instant, limited size)
        self.memory_cache = LRUCache(max_size=10000)

        # Tier 2: SQLite cache (fast, persistent, unlimited)
        self.sqlite_cache = SqliteCache("cache/embeddings.db")

        # Tier 3: Redis cache (shared across instances, optional)
        self.redis_cache = RedisCache("redis://localhost") if REDIS_AVAILABLE else None

    def get_embedding(self, text: str, engine: str) -> Optional[np.array]:
        key = f"{engine}:{hashlib.md5(text.encode()).hexdigest()}"

        # Try each tier
        if result := self.memory_cache.get(key):
            return result

        if result := self.sqlite_cache.get(key):
            self.memory_cache.set(key, result)  # Promote to memory
            return result

        if self.redis_cache and (result := self.redis_cache.get(key)):
            self.memory_cache.set(key, result)
            self.sqlite_cache.set(key, result)  # Cache locally
            return result

        return None

    def set_embedding(self, text: str, engine: str, embedding: np.array):
        key = f"{engine}:{hashlib.md5(text.encode()).hexdigest()}"

        # Write to all tiers
        self.memory_cache.set(key, embedding)
        self.sqlite_cache.set(key, embedding)
        if self.redis_cache:
            self.redis_cache.set(key, embedding, ttl=86400)  # 1 day TTL
```

### Cache Warming Strategy
```python
def warm_cache_for_common_terms():
    """Pre-compute embeddings for frequent biblical terms"""
    common_terms = load_frequent_terms("data/biblical_term_frequency.txt")

    for engine in engines:
        for term in common_terms[:1000]:  # Top 1000 terms
            embedding = engine.get_embedding(term)
            cache.set_embedding(term, engine.name, embedding)
```

### Storage Estimates
- Memory cache: 10K terms × 768 dims × 4 bytes = ~30MB
- SQLite cache: 100K terms × 768 dims × 4 bytes = ~300MB
- Redis cache: Unlimited, but use TTL for cleanup

### Recommendation
✅ **Implement SQLite cache immediately** (easy win). Add Redis when scaling to multiple instances. Pre-warm cache with common biblical terms.

---

## 8. Failure Mode Design - Graceful Degradation

### Failure Scenarios & Handlers
```python
class ResilientEngineWrapper:
    def __init__(self, primary: SemanticEngine, fallback_chain: List[SemanticEngine]):
        self.primary = primary
        self.fallback_chain = fallback_chain
        self.health_monitor = HealthMonitor()

    def find_best_substring(self, refTerm: str, origText: str) -> str:
        # Track engine health
        if not self.health_monitor.is_healthy(self.primary):
            return self._use_fallback(refTerm, origText)

        try:
            # Try primary engine with timeout
            with timeout(seconds=5):
                result = self.primary.find(refTerm, origText)
                self.health_monitor.record_success(self.primary)
                return result

        except ModelNotFoundError as e:
            # Model needs downloading
            logger.warning(f"Model not found: {e}")
            self._async_download_model(self.primary)
            return self._use_fallback(refTerm, origText)

        except APIRateLimitError as e:
            # API limit reached
            logger.warning(f"API rate limit: {e}")
            self.health_monitor.record_failure(self.primary)
            return self._use_fallback(refTerm, origText)

        except torch.cuda.OutOfMemoryError:
            # GPU OOM - switch to CPU
            logger.warning("GPU OOM, switching to CPU")
            self.primary.to_cpu()
            return self.primary.find(refTerm, origText)

        except Exception as e:
            # Unknown failure
            logger.error(f"Engine failed: {e}")
            self.health_monitor.record_failure(self.primary)

            # Last resort: longest common substring
            return self._baseline_lcs(refTerm, origText)

    def _use_fallback(self, refTerm: str, origText: str) -> str:
        """Try each fallback engine in order"""
        for engine in self.fallback_chain:
            if self.health_monitor.is_healthy(engine):
                try:
                    return engine.find(refTerm, origText)
                except:
                    continue

        # All engines failed - use deterministic baseline
        return self._baseline_lcs(refTerm, origText)

    def _baseline_lcs(self, s1: str, s2: str) -> str:
        """Longest common substring - always works"""
        # Simple DP solution that requires no external dependencies
        # ... implementation
```

### Health Monitoring
```python
class HealthMonitor:
    def __init__(self, failure_threshold: int = 3, recovery_time: int = 60):
        self.failure_counts = defaultdict(int)
        self.last_failure_time = {}
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time

    def is_healthy(self, engine: SemanticEngine) -> bool:
        if engine.name not in self.last_failure_time:
            return True

        # Check if enough time has passed for recovery
        time_since_failure = time.time() - self.last_failure_time[engine.name]
        if time_since_failure > self.recovery_time:
            # Reset failure count after recovery period
            self.failure_counts[engine.name] = 0
            return True

        return self.failure_counts[engine.name] < self.failure_threshold
```

### Recommendation
✅ **Wrap all engines in ResilientEngineWrapper**. Define clear fallback chain: BERT → SentenceTransformer → Word2Vec → EditDistance → LCS.

---

## 9. Batch Processing Optimization

### Current Issue
Processing terms sequentially wastes GPU/API resources.

### Batching Implementation
```python
class BatchOptimizedEngine(SemanticEngine):
    def __init__(self, base_engine: SemanticEngine, batch_size: int = 32):
        self.base_engine = base_engine
        self.batch_size = batch_size
        self.pending_queue = []
        self.result_futures = {}

    def find_best_substring_batch(self,
                                  pairs: List[Tuple[str, str]]) -> List[str]:
        """Process multiple term pairs efficiently"""

        # Group by target text for better caching
        grouped = defaultdict(list)
        for refTerm, origText in pairs:
            grouped[origText].append(refTerm)

        results = []

        for origText, refTerms in grouped.items():
            # Generate all candidates once
            candidates = self._generate_all_candidates(origText)

            # Batch compute embeddings
            all_texts = refTerms + candidates
            embeddings = self.base_engine.encode_batch(all_texts)

            # Split embeddings
            ref_embeddings = embeddings[:len(refTerms)]
            cand_embeddings = embeddings[len(refTerms):]

            # Compute similarity matrix
            similarity_matrix = cosine_similarity(ref_embeddings, cand_embeddings)

            # Find best match for each refTerm
            for i, refTerm in enumerate(refTerms):
                best_idx = similarity_matrix[i].argmax()
                best_score = similarity_matrix[i][best_idx]

                if best_score > 0.6:
                    results.append(candidates[best_idx])
                else:
                    results.append(None)

        return results

    def find_async(self, refTerm: str, origText: str) -> Future:
        """Async interface for concurrent processing"""
        future = Future()

        self.pending_queue.append((refTerm, origText, future))

        if len(self.pending_queue) >= self.batch_size:
            self._process_pending_batch()

        return future

    def _process_pending_batch(self):
        """Process accumulated requests as batch"""
        if not self.pending_queue:
            return

        batch = self.pending_queue[:self.batch_size]
        self.pending_queue = self.pending_queue[self.batch_size:]

        pairs = [(ref, orig) for ref, orig, _ in batch]
        results = self.find_best_substring_batch(pairs)

        for (_, _, future), result in zip(batch, results):
            future.set_result(result)
```

### Performance Comparison
```python
# Sequential: O(n) API calls, O(n * model_time)
for refTerm, origText in pairs:
    result = engine.find(refTerm, origText)  # 50ms each
# Total: 100 terms × 50ms = 5000ms

# Batched: O(1) API calls, O(model_time + overhead)
results = engine.find_batch(pairs)  # 200ms total
# Total: 200ms (25x faster!)
```

### Recommendation
✅ **Implement batching for all neural engines**. Use async interface for real-time applications. Critical for API-based engines to reduce costs.

---

## 10. Build vs Buy vs Fine-tune Decision Matrix

### Option A: Use Pre-trained Models

```python
# Immediate implementation
engine = SentenceTransformer('shibing624/text2vec-base-chinese')
```

| Pros | Cons |
|------|------|
| ✅ Fast deployment (1 day) | ❌ Not biblical-specific |
| ✅ Well-tested | ❌ May miss theological nuances |
| ✅ Good baseline | ❌ Generic embeddings |

**Cost**: $0 (open source)
**Time**: 1-2 days
**Expected Accuracy**: 65-70%

### Option B: Fine-tune Existing Models

```python
# Fine-tuning approach
from sentence_transformers import SentenceTransformer, InputExample, losses

# Prepare biblical training data
train_examples = [
    InputExample(texts=['神', '上帝'], label=0.95),
    InputExample(texts=['獨生子', 'only begotten son'], label=0.90),
    InputExample(texts=['救恩', '救贖'], label=0.85),
    # ... thousands more
]

# Fine-tune model
model = SentenceTransformer('base-model')
train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16)
train_loss = losses.CosineSimilarityLoss(model)

model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=10,
    warmup_steps=100
)
```

| Pros | Cons |
|------|------|
| ✅ Biblical-specific | ❌ Needs labeled data |
| ✅ Better accuracy | ❌ Training time |
| ✅ Customizable | ❌ Risk of overfitting |

**Cost**: $50-200 (GPU hours)
**Time**: 1-2 weeks
**Expected Accuracy**: 75-85%

### Option C: Train from Scratch

```python
# Custom architecture for biblical Chinese
class BiblicalChineseEmbedder(nn.Module):
    def __init__(self):
        super().__init__()
        self.char_embeddings = nn.Embedding(10000, 128)  # Character level
        self.word_embeddings = nn.Embedding(50000, 256)  # Word level
        self.positional = PositionalEncoding()
        self.transformer = nn.TransformerEncoder(...)

    def forward(self, text):
        # Custom architecture for biblical text
        char_emb = self.char_embeddings(text.chars)
        word_emb = self.word_embeddings(text.words)
        combined = torch.cat([char_emb, word_emb], dim=-1)
        return self.transformer(combined)
```

| Pros | Cons |
|------|------|
| ✅ Perfect fit | ❌ Expensive development |
| ✅ Full control | ❌ Needs large corpus |
| ✅ Optimal performance | ❌ 3-6 months |

**Cost**: $5,000-20,000 (development + compute)
**Time**: 3-6 months
**Expected Accuracy**: 85-95%

### Option D: Hybrid Progressive Approach (RECOMMENDED)

```yaml
Phase 1 (Week 1): Pre-trained baseline
  - Use text2vec-base-chinese
  - Establish performance baseline
  - Collect error cases

Phase 2 (Week 2-3): Enhanced with domain knowledge
  - Add BiblicalKnowledgeBase
  - Implement hybrid engine
  - Measure improvement

Phase 3 (Month 2): Fine-tuning
  - Use collected error cases as training data
  - Fine-tune on biblical pairs
  - A/B test against baseline

Phase 4 (Month 3+): Custom development (if needed)
  - Only if accuracy < 80%
  - Focus on specific failure modes
  - Consider commercial APIs
```

---

## Implementation Priorities

### Immediate (Week 1)
1. ✅ Implement SentenceTransformerEngine with Chinese model
2. ✅ Add SQLite caching layer
3. ✅ Create cascading engine with EditDistance → SentenceTransformer

### Short-term (Week 2-3)
4. ✅ Build BiblicalKnowledgeBase from Strong's dictionary
5. ✅ Implement batch processing for efficiency
6. ✅ Add resilient wrapper with fallback chain

### Medium-term (Month 2)
7. ✅ Collect user feedback for adaptive selection
8. ✅ Fine-tune model on biblical corpus
9. ✅ Implement context-aware matching

### Long-term (Month 3+)
10. ✅ Evaluate custom model development
11. ✅ Add commercial API integration for premium features
12. ✅ Build comprehensive benchmark suite

---

## Success Metrics

### Target Performance
- **Accuracy**: > 80% on biblical benchmark
- **Speed**: < 10ms p50, < 50ms p95
- **Memory**: < 500MB for base deployment
- **Cache hit rate**: > 70% after warm-up
- **Fallback rate**: < 5% in production

### Decision Criteria for Phase Transitions
- Move to Phase 2: When baseline accuracy plateaus
- Move to Phase 3: If accuracy < 75% after domain enhancement
- Move to Phase 4: If business requires > 85% accuracy

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|-------------------|
| Model too large for deployment | Use quantization, distillation |
| API costs too high | Implement aggressive caching, use free tiers |
| Accuracy too low | Hybrid approach, human-in-the-loop |
| Latency spikes | Cascading strategy, timeout controls |
| Data privacy concerns | On-premise deployment option |

---

## Final Recommendation

**Start with Hybrid Progressive Approach (Option D)**

1. **Immediate action**: Deploy SentenceTransformer with Chinese model
2. **Quick win**: Add caching and cascading for 10x speed improvement
3. **Differentiator**: Biblical knowledge base for domain expertise
4. **Future-proof**: Collect feedback data for continuous improvement
5. **Flexibility**: Architecture supports swapping engines based on results

This strategy balances:
- ⚡ Speed to market (working system in 1 week)
- 📈 Progressive improvement (each phase adds value)
- 💰 Cost efficiency (start free, pay only if needed)
- 🎯 Risk management (multiple fallback options)
- 🔬 Data-driven decisions (measure before investing)

The modular architecture ensures that work in any phase contributes to the final system, with no wasted effort.