# LLM Benchmark — SN Embedding Quality (Gen 1:1–31)

Task: Transfer Strong's Numbers from UNV to LCC for Genesis chapter 1 (31 verses).

## Summary

### Cloud Models (Mac Mini, 2026-03-14)

| Model                  | Brand  | Time | Avg/verse | SN Mismatches                   | Avg Confidence |
|------------------------|--------|------|-----------|----------------------------------|----------------|
| gemini-3-flash-preview | gemini | 26m  | 0.8 min   | **0/31 perfect**                | **0.96**       |
| gemini-2.5-flash       | gemini | 11m  | 0.4 min   | 5/31 (−8 SNs total)            | **0.97**       |
| haiku                  | claude | 40m  | 1.3 min   | 14/31 (−27 SNs total)          | 0.91           |
| gpt-5.1-codex-mini     | codex  | 21m  | 0.7 min   | 4/31 (+11 extra), 2 parse fails | 0.79          |

### TranslateGemma (an NVIDIA GB10 ollama host, 2026-03-16)

Google's translation-specific model (55 languages incl. Chinese), built on Gemma 3. Tested all 12 Ollama variants: 3 base sizes × (base + 3 quantizations).

| Model                          | Brand  | Time | Avg/verse | SN Mismatches                  | Avg Confidence |
|---------------------------------|--------|------|-----------|--------------------------------|----------------|
| translategemma:4b               | local  | 32m  | 1.0 min   | 16/31 (−92, +38 extra)         | 0.95           |
| translategemma:12b              | local  | 10m  | 0.3 min   | 27/31 (−192, +10 extra)        | 0.97           |
| translategemma:27b              | local  | 15m  | 0.5 min   | 29/31 (−359, +1 extra)         | 0.95           |
| translategemma:4b-it-q4_K_M     | local  | 54m  | 1.8 min   | 17/31 (−105, +39 extra)        | 0.95           |
| translategemma:4b-it-q8_0       | local  | 4m   | 0.1 min   | 20/31 (−279, +5 extra)         | 0.97           |
| translategemma:4b-it-bf16       | local  | 7m   | 0.2 min   | 20/31 (−282, +2 extra)         | 0.97           |
| translategemma:12b-it-q4_K_M    | local  | 10m  | 0.3 min   | 27/31 (−204, +10 extra)        | 0.97           |
| translategemma:12b-it-q8_0      | local  | 12m  | 0.4 min   | 29/31 (−337, +6 extra)         | 0.95           |
| translategemma:12b-it-bf16      | local  | 22m  | 0.7 min   | 29/31 (−346, +4 extra)         | 0.95           |
| translategemma:27b-it-q4_K_M    | local  | 17m  | 0.5 min   | 29/31 (−332)                   | 0.95           |
| translategemma:27b-it-q8_0      | local  | 26m  | 0.8 min   | 31/31 (−426, +1 extra)         | 0.94           |
| translategemma:27b-it-bf16      | local  | 41m  | 1.3 min   | 30/31 (−381, +1 extra)         | 0.94           |

## Per-Verse Confidence

### gemini-3-flash-preview (0 mismatches)

| Verse | Conf | Verse | Conf | Verse | Conf | Verse | Conf |
|-------|------|-------|------|-------|------|-------|------|
| 1:1   | 1.0  | 1:9   | 0.98 | 1:17  | 0.95 | 1:25  | 0.95 |
| 1:2   | 0.95 | 1:10  | 0.95 | 1:18  | 0.95 | 1:26  | 0.95 |
| 1:3   | 1.0  | 1:11  | 0.95 | 1:19  | 1.0  | 1:27  | 0.95 |
| 1:4   | 0.95 | 1:12  | 0.95 | 1:20  | 0.95 | 1:28  | 0.95 |
| 1:5   | 0.98 | 1:13  | 1.0  | 1:21  | 0.95 | 1:29  | 0.95 |
| 1:6   | 0.95 | 1:14  | 0.95 | 1:22  | 0.95 | 1:30  | 0.95 |
| 1:7   | 0.95 | 1:15  | 0.95 | 1:23  | 1.0  | 1:31  | 0.95 |
| 1:8   | 1.0  | 1:16  | 0.95 | 1:24  | 0.95 |       |      |

### gemini-2.5-flash (5 mismatches)

| Verse | Conf | SN Issue                         |
|-------|------|----------------------------------|
| 1:1   | 0.99 |                                  |
| 1:2   | 0.98 |                                  |
| 1:3   | 1.0  |                                  |
| 1:4   | 0.98 |                                  |
| 1:5   | 0.98 |                                  |
| 1:6   | 0.95 |                                  |
| 1:7   | 0.98 |                                  |
| 1:8   | 1.0  |                                  |
| 1:9   | 0.98 |                                  |
| 1:10  | 0.98 |                                  |
| 1:11  | 0.95 | missing: WH06529                 |
| 1:12  | 0.98 |                                  |
| 1:13  | 1.0  |                                  |
| 1:14  | 0.98 |                                  |
| 1:15  | 0.95 |                                  |
| 1:16  | 0.98 | missing: WH0853 x4               |
| 1:17  | 0.98 |                                  |
| 1:18  | 0.98 |                                  |
| 1:19  | 1.0  |                                  |
| 1:20  | 0.98 |                                  |
| 1:21  | 0.98 | missing: WH0834                  |
| 1:22  | 0.98 |                                  |
| 1:23  | 1.0  |                                  |
| 1:24  | 0.95 |                                  |
| 1:25  | 0.95 |                                  |
| 1:26  | 0.98 |                                  |
| 1:27  | 0.95 |                                  |
| 1:28  | 0.98 | missing: WH0430                  |
| 1:29  | 0.9  |                                  |
| 1:30  | 0.9  | missing: WH0853                  |
| 1:31  | 0.98 |                                  |

### haiku (14 mismatches)

| Verse | Conf | SN Issue                                      |
|-------|------|-----------------------------------------------|
| 1:1   | 0.97 |                                               |
| 1:2   | 0.92 |                                               |
| 1:3   | 0.98 |                                               |
| 1:4   | 0.88 | missing: WH03588, WH0853, WH0996 x2           |
| 1:5   | 0.94 |                                               |
| 1:6   | 0.88 |                                               |
| 1:7   | 0.93 |                                               |
| 1:8   | 0.98 |                                               |
| 1:9   | 0.9  |                                               |
| 1:10  | 0.91 |                                               |
| 1:11  | 0.95 | missing: WH05921, WH0834, WAH09002            |
| 1:12  | 0.93 | missing: WH0834, WAH09002                     |
| 1:13  | 0.98 |                                               |
| 1:14  | 0.82 | missing: WAH09001                              |
| 1:15  | 0.87 | missing: WAH09001, WAH09002                   |
| 1:16  | 0.88 | missing: WH0853 x2                             |
| 1:17  | 0.88 | missing: WH0853                                |
| 1:18  | 0.88 |                                               |
| 1:19  | 0.98 |                                               |
| 1:20  | 0.92 |                                               |
| 1:21  | 0.82 | missing: WH0853 x2                             |
| 1:22  | 0.92 |                                               |
| 1:23  | 0.98 |                                               |
| 1:24  | 0.91 |                                               |
| 1:25  | 0.87 | missing: WH0853 x2, extra: WH0127             |
| 1:26  | 0.85 | extra: WH06213, WTH8799                        |
| 1:27  | 0.87 | missing: WH0853 x3                             |
| 1:28  | 0.88 | missing: WH0430, WH0853, WAH09001, WAH09002 x2|
| 1:29  | 0.87 | missing: WAH09001                              |
| 1:30  | 0.8  | extra: WH02416                                 |
| 1:31  | 0.94 |                                               |

### gpt-5.1-codex-mini (4 mismatches + 2 parse fails)

| Verse | Conf | SN Issue                                       |
|-------|------|------------------------------------------------|
| 1:1   | 0.85 |                                                |
| 1:2   | 0.82 |                                                |
| 1:3   | 0.95 |                                                |
| 1:4   | 0.95 |                                                |
| 1:5   | 0.92 |                                                |
| 1:6   | 0.95 | extra: WH04325, WH0996                         |
| 1:7   | 0.95 |                                                |
| 1:8   | 0.95 |                                                |
| 1:9   | 0.95 |                                                |
| 1:10  | 0.73 |                                                |
| 1:11  | 0.95 |                                                |
| 1:12  | 0.82 |                                                |
| 1:13  | 0.95 |                                                |
| 1:14  | 0.72 |                                                |
| 1:15  | 0.95 |                                                |
| 1:16  | 0.3  | JSON parse fail; extra: WH03974 x2, WH0853 x3  |
| 1:17  | 0.3  | JSON parse fail; extra: WH0430 x2, WH0853       |
| 1:18  | 0.78 |                                                |
| 1:19  | 0.78 | missing: WH0996                                |
| 1:20  | 0.95 |                                                |
| 1:21  | 0.61 |                                                |
| 1:22  | 0.72 |                                                |
| 1:23  | 0.68 |                                                |
| 1:24  | 0.95 |                                                |
| 1:25  | 0.95 |                                                |
| 1:26  | 0.95 |                                                |
| 1:27  | 0.78 |                                                |
| 1:28  | 0.76 |                                                |
| 1:29  | 0.74 |                                                |
| 1:30  | 0.74 |                                                |
| 1:31  | 0.62 |                                                |

## Observations

### Implicit Marker Handling

The main differentiator between models is handling of implicit Hebrew markers:
- `{<WH0853>}` — direct object marker (את), no Chinese equivalent
- `{<WAH09001>}` / `{<WAH09002>}` — inseparable prefixes (ל, ב)
- `{<WH0834>}` — relative pronoun (אשר)
- `{<WH03588>}` — conjunction (כי)

**gemini-3-flash-preview** preserves all implicit markers perfectly.
**gemini-2.5-flash** occasionally drops WH0853 and WH0834.
**haiku** systematically drops WH0853, WAH09001, WAH09002 — the most common implicit markers.
**gpt-5.1-codex-mini** adds extra SNs and sometimes fails to produce valid JSON.

### TranslateGemma Assessment

**Not suitable for SN embedding.** All 12 variants show catastrophic SN loss:
- Best case: 4b base with 16/31 mismatches (−92 missing, +38 extra SNs)
- Worst case: 27b-it-q8_0 with 31/31 mismatches (−426 missing SNs)
- Larger models perform **worse** (more missing SNs), likely because they "understand" translation better and strip annotation markers they consider non-translatable
- Confidence scores (0.94–0.97) are **misleadingly high** — the model self-reports high confidence while dropping most SNs
- The model appears to treat SN annotations as noise to be removed rather than semantic tags to be transferred

### Recommendations

1. **Production quality**: gemini-3-flash-preview — zero mismatches, consistent 0.95+ confidence
2. **Speed priority**: gemini-2.5-flash — 3x faster, minor implicit marker drops
3. **Avoid for this task**: haiku (too many drops), gpt-5.1-codex-mini (parse failures, low confidence)
4. **Not viable**: TranslateGemma (all sizes) — translation-specific models are counterproductive for SN annotation transfer

See [CONFIDENCE_BASIS.md](CONFIDENCE_BASIS.md) for how confidence scores are determined.
See [OSS_MODEL.md](OSS_MODEL.md) for local/open-source model benchmarks on a private ollama host.
