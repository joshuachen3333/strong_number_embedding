# survey4_annotation_consistency_test/ — Self-Supervised Prompt Evaluation

## Concept

Use FHL's existing UNV+SN annotations as ground truth to objectively evaluate prompt quality — without needing 3-model consensus.

## The Idea

### Current task (cross-lingual projection, no ground truth)

```
Input1: UNV+SN (v1)  ← source with annotations
Input2: LCC (v1)      ← target without annotations
Output: LCC+SN (v1)   ← no standard answer exists
```

### New task (same-language re-annotation, ground truth exists)

```
Few-shot example:
  Input1: UNV+SN (v1)  ← annotated verse as example
  Input2: UNV (v1)      ← same verse without annotations (shows the pattern)

Task:
  Input:  UNV (v2)      ← different verse, no annotations
  Output: UNV+SN (v2)   ← model's attempt

Evaluation:
  Compare output vs FHL's actual UNV+SN (v2) ← ground truth!
```

## What This Tests

| Capability | Tested? | Needed for LCC task? |
|-----------|---------|---------------------|
| Format preservation (zero-padding, WAH/WTH) | ✅ | ✅ |
| Implicit marker handling ({<WH0853>}) | ✅ | ✅ |
| Morphology code placement | ✅ | ✅ |
| SN count correctness | ✅ | ✅ |
| **Cross-lingual alignment** (神→上帝) | ❌ | ✅ |
| **Different word order** | ❌ | ✅ |
| **Different vocabulary/rephrasing** | ❌ | ✅ |

**Necessary but not sufficient**: a prompt that fails this test is definitely bad for LCC. A prompt that passes might still fail on LCC alignment.

## Primary Application: Prompt Regression Accelerator

### Current 回測 cost
18 verses × 3 models × R1 = 54 API calls (+ R2 convergence if needed)

### New pre-filter
100 verses × 1 model × 1 call = 100 calls → automatic scoring vs ground truth

### Workflow

```
Prompt改動後
  → Step 1: UNV→UNV+SN benchmark (100 verses × 1 model)
    → Score drops → reject immediately (save expensive 3-model 回測)
    → Score holds/improves → proceed to full 3-model regression
```

Filters out obviously bad prompt changes at ~20% of the cost.

## Extensions

- **KJV+SN benchmark**: Same test with English KJV (also has FHL annotations) → tests cross-language generalization
- **Difficulty gradient**: Short vs long verses, few vs many SNs → calibrated difficulty curves
- **Prompt version comparison**: v1.0 vs v1.1 vs v1.2 score curves → quantify evolution effect

## Academic Framing

This is a form of **Annotation Consistency Test** (自我一致性標注測試):
- Use existing annotations as self-supervised ground truth
- Measure a model's ability to reproduce known-correct annotations
- Proxy metric for the harder cross-lingual task

To be documented in `AI_PROBLEM_CLASSIFICATION.md` when finalized.

## Status

Concept stage. Implementation pending.

## Scoring Metrics (proposed)

1. **Exact match rate**: output == FHL ground truth (strictest)
2. **SN coverage score**: missing + extra SNs / total SNs
3. **Placement accuracy**: SN present but wrong position
4. **Format compliance**: zero-padding, braces, prefix markers
