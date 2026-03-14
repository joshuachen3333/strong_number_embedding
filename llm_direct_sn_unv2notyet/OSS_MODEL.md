# Open-Source / Local Model Benchmark for SN Embedding

Tested on `sai.fhl.net` — NVIDIA GB10 GPU, 119GB RAM, Ollama in Docker.
Task: Transfer Strong's Numbers from UNV to LCC (Genesis 1:1–3).

## Results (2026-03-14)

### Local Models via Ollama (sai.fhl.net)

| Model          | Size  | Gen 1:1 | Gen 1:2 | Gen 1:3 | Time/verse | JSON OK? | Verdict                          |
|----------------|-------|---------|---------|---------|------------|----------|----------------------------------|
| **qwen3:32b**  | 20 GB | 0.98    | 0.90    | 0.98    | ~8–15 min  | Yes      | **Only usable local model**      |
| qwen3:30b      | 18 GB | —       | 0.3 ✗   | 0.3 ✗   | ~3–8 min   | No       | MoE variant, can't follow schema |
| gpt-oss:120b   | 65 GB | —       | 0.3 ✗   | 0.3 ✗   | ~5–8 min   | No       | Can't produce structured JSON    |

- Confidence 0.3 with "JSON parse failed" = model returned unstructured text
- qwen3:30b is a Mixture-of-Experts (MoE) variant, not the same as 32b dense
- gpt-oss:120b is large but untested for Chinese biblical text tasks

### Cloud Models for Comparison (Mac Mini)

| Brand/Model              | Gen 1:1 | Time    | SN Match | Notes                              |
|--------------------------|---------|---------|----------|------------------------------------|
| claude/sonnet (default)  | ref     | ~1 min  | perfect  | Reference baseline                 |
| gemini-3-flash-preview   | 1.0     | 27s     | perfect  | Best speed + quality               |
| gemini-3-pro-preview     | 1.0     | 20 min  | perfect  | Hit rate limits, slow              |
| codex/gpt-5.2            | 0.96    | 25s     | perfect  | Fast, good quality                 |
| local/qwen3:32b          | 0.98    | 2.5 min | −2 SNs   | Misses implicit markers sometimes  |

## Recommendations

1. **For quality**: gemini-3-flash-preview or claude/sonnet — confidence 1.0, perfect SN match
2. **For free/unlimited**: qwen3:32b on sai.fhl.net — decent quality (0.9–0.98), no token cost, but slow (~8 min/verse)
3. **Don't bother with**: qwen3:30b, gpt-oss:120b — can't follow structured JSON output instructions

## Notes

- qwen3:32b sometimes merges compound terms (天地 = 天+地) and drops implicit object markers {<WH0853>}
- Cloud models handle implicit markers and complex verse structures more reliably
- Running two Ollama requests in parallel on the same GPU roughly doubles per-verse time
- Ollama auto-unloads models after ~5 min idle; use `ollama stop <model>` to free GPU immediately
