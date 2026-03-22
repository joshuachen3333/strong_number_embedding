# survey3_whether_feeding_prompt_comment/

## Purpose

Test whether # comment headers in prompt files (evolution story, experiment results, meta-commentary) affect model output quality when fed as part of the system prompt.

## Hypothesis

Prompt files like `v1.2_joshua.md` contain human-readable # comments at the top. `load_prompt_file()` sends the ENTIRE file to models, including these comments. This experiment tests:

1. **No difference** → comments neutral (strip to save tokens)
2. **Stripped is better** → comments confuse/bias models
3. **Comments help** → models learn from evolution story

## Method

A/B test using `--strip-prompt-comment` flag in `run_gold_standard.py`:

| Group | Command | What's fed to models |
|-------|---------|---------------------|
| A (default) | No flag | Full prompt including # comments |
| B (stripped) | `--strip-prompt-comment` | Only actual prompt content |

Stripping removes leading `# ` lines (not `##` markdown headers). Applied to both main prompt and model patches.

## Test Configuration

- Verses: Gen 1:1, 1:4, 1:5, 1:7, 1:11, 1:16, 1:21 (3 easy + 4 hard)
- Models: opus, gemini-3-pro-preview, gpt-5.4 (default trio)
- Prompt: v1.2_joshua.md
- Both groups use `--force` for fresh results

## Metrics

| Metric | Higher = better? |
|--------|-----------------|
| R1 unanimous count | Yes |
| Total R2 convergence attempts | Lower = better |
| Average stability level | Lower = better |
| Gold standard match rate | Higher = better |

## Commands

```bash
# Group A (with comments):
python3 survey1_prompt_evolving/run_gold_standard.py \
  --book 創 --chap 1 --sec 1,4,5,7,11,16,21 --force

# Group B (stripped):
python3 survey1_prompt_evolving/run_gold_standard.py \
  --book 創 --chap 1 --sec 1,4,5,7,11,16,21 --force --strip-prompt-comment
```

## Results

See `results.md` (populated after experiment runs).
