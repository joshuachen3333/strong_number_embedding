# Confidence Scoring Basis

How the `confidence` field (0.0–1.0) in output JSON is determined.

## Two Layers of Quality Assessment

### 1. LLM Self-Reported Confidence (`confidence` field)

The LLM assigns its own confidence score based on the system prompt instruction:

> "confidence: 0.0 to 1.0. Lower if word boundaries are ambiguous or LCC rephrases heavily."

This is **subjective** — the LLM decides how confident it is in its SN placement.

#### Recommended Interpretation

| Score   | Meaning                                                          |
|---------|------------------------------------------------------------------|
| **1.0** | All SNs map one-to-one; no ambiguity in word boundaries          |
| **0.9** | Compound words merged (e.g., 天地 = 天+地), minor position shifts |
| **0.8** | Uncertain mappings — LCC rephrases heavily or word order differs |
| **0.7** | Some SNs have no clear LCC counterpart; educated guesses made    |
| **< 0.7** | Significant uncertainty; likely missing or misplaced SNs       |

#### Special Values

- **0.3** — Not LLM-reported. This is the **code fallback** when `_extract_json()` fails to parse structured JSON from the LLM response (fell through to raw-text regex extraction). Treat as unreliable.
- **0.0** — Error state: API failure, timeout, empty response, or network error.

### 2. Objective SN Coverage Check (`verify_sn_coverage()`)

After receiving the LLM response, the pipeline runs `verify_sn_coverage()` which counts Strong's Numbers in both the UNV source and the LLM output:

```
UNV SNs:    [WH03068, WH0430, WAH04480, WH06924, ...]  → count = N
Output SNs: [WH03068, WH0430, WAH04480, WH06924, ...]  → count = M
```

Result fields:
- `unv_count` / `lcc_count` — total SN count in source vs output
- `missing` — SNs present in UNV but absent from output
- `extra` — SNs in output that don't exist in UNV
- `perfect` — `true` if missing = 0 and extra = 0

This check is **objective** — it catches dropped or hallucinated SNs regardless of what the LLM self-reports.

### How They Interact

| LLM Confidence | SN Coverage | Interpretation                              |
|----------------|-------------|---------------------------------------------|
| High (≥ 0.9)   | Perfect     | Good result — trust it                      |
| High (≥ 0.9)   | Missing SNs | LLM overconfident — needs human review      |
| Low (< 0.8)    | Perfect     | Placement may be wrong even though all SNs present |
| Low (< 0.8)    | Missing SNs | Poor result — likely needs reprocessing     |

## Reprocessing Threshold

`--reprocess-low-confidence` reprocesses verses with `confidence < 0.85` using a stronger model (defaults to opus). This threshold balances:
- Catching genuinely uncertain results (< 0.85)
- Not wasting tokens re-running already-good results (≥ 0.85)

## Model-Specific Observations

| Brand/Model            | Typical Confidence | SN Coverage | Notes                                      |
|------------------------|--------------------|-----------  |--------------------------------------------|
| claude/sonnet           | 0.90–1.0          | Perfect     | Reference baseline                         |
| gemini-3-flash-preview  | 0.95–1.0          | Perfect     | Occasionally over-confident                |
| codex/gpt-5.2           | 0.90–0.98         | Perfect     | Conservative, reliable                     |
| local/qwen3:32b         | 0.90–0.98         | −1~2 SNs    | Misses implicit markers, merges compounds  |
| local/qwen3:30b         | 0.3 (parse fail)  | N/A         | Cannot produce structured JSON             |
| local/gpt-oss:120b      | 0.3 (parse fail)  | N/A         | Cannot produce structured JSON             |

See [OSS_MODEL.md](OSS_MODEL.md) for detailed local model benchmarks.
