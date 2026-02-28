# Quick Start: Hybrid Parser

**5-Minute Guide to Using the Two-Stage UNV+SN Parser**

---

## Installation

### 1. Install Dependencies

```bash
pip install anthropic pyyaml
```

### 2. Set API Key (Optional - only needed for AI resolution)

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

---

## Basic Usage

### Parse a Single Verse (Stage 1 Only)

```bash
# Parse Genesis 1:1 without AI
python run_parser_hybrid.py 1 1 --book Gen --no-ai

# Output: output/Gen/1/1.json
```

### Parse with AI Resolution (if uncertain)

```bash
# Parse Genesis 1:1 with AI enabled
python run_parser_hybrid.py 1 1 --book Gen

# If certainty < 0.8, AI will attempt resolution
```

### Parse Entire Chapter

```bash
# Parse all 31 verses of Genesis 1
for verse in {1..31}; do
    python run_parser_hybrid.py 1 $verse --book Gen --no-ai
done
```

---

## Understanding Output

### Output Files

```
output/Gen/1/1.json              # Certain result (Stage 1)
output/Gen/1/2_uncertain.json    # Uncertain (AI disabled)
output/Gen/1/3.json              # AI-resolved (Stage 2)
human_review_queue/Gen/1/4_review.json  # Needs human review
```

### JSON Structure

```json
{
  "groups": [
    {
      "core": "07225",           // Strong's number
      "implicit": false,          // Hidden in braces?
      "prefixes": ["09002"],      // 900x codes
      "morph": ["8804"],          // Morphology codes
      "pre_brace": [],            // Right-attached preps
      "post_brace": [],           // Left-attached preps
      "warnings": [],             // Issues detected
      "source_type": "strong"
    }
  ],
  "status": "certain",           // or "uncertain", "ai_resolved", "needs_review"
  "timestamp": "2025-11-06T23:42:47.026609"
}
```

---

## Configuration

### Edit `config_ai.yaml`

```yaml
# AI Mode: disabled | conservative | aggressive
ai_mode: conservative

# Model: claude-sonnet-4-5-20250929 | claude-sonnet-3-5-20240620
ai_model: claude-sonnet-4-5-20250929

# Thresholds
certainty_threshold: 0.8          # Stage 1 auto-accept
ai_auto_accept_threshold: 0.85    # Stage 2 auto-accept
```

### Use Custom Config

```bash
python run_parser_hybrid.py 1 1 --book Gen --config my_config.yaml
```

---

## Common Commands

```bash
# Parse without AI (fastest, free)
python run_parser_hybrid.py 1 1 --book Gen --no-ai

# Parse with AI fallback (recommended)
python run_parser_hybrid.py 1 1 --book Gen

# Batch parse Genesis 1-5
for ch in {1..5}; do
    for v in {1..31}; do
        python run_parser_hybrid.py $ch $v --book Gen 2>/dev/null || break
    done
done

# Check results
ls -lh output/Gen/1/
cat output/Gen/1/1.json | jq '.groups[] | {core, prefixes, morph}'
```

---

## Interpreting Status

| Status | Meaning | Action |
|--------|---------|--------|
| `certain` | Stage 1 confident (≥0.8) | ✅ Use directly |
| `uncertain` | Stage 1 unsure, AI disabled | ⚠️ Manual review |
| `ai_resolved` | AI resolved with high confidence | ✅ Use (but verify) |
| `needs_review` | AI unsure (<0.85) | ⚠️ Human review required |

---

## Troubleshooting

### Error: "ANTHROPIC_API_KEY not set"

**Solution**: Either:
1. Set the environment variable: `export ANTHROPIC_API_KEY="..."`
2. Disable AI: add `--no-ai` flag

### Error: "parse_verse_v1_6.py not found"

**Solution**: Make sure you're in the correct directory:
```bash
cd sn_within_unv_selfgroup_segmentation
ls parse_verse_v1_6.py  # Should exist
```

### Error: "fetch_text.sh not found"

**Solution**: Make sure fetch_text.sh is executable:
```bash
chmod +x fetch_text.sh
```

### Output file not created

**Check**:
1. Exit code: `echo $?` (0 = success, 1 = error)
2. Look for error messages in stderr
3. Check if directory exists: `ls -la output/Gen/1/`

---

## Performance Tips

### Speed

- **Stage 1 only**: ~2 seconds per verse
- **With AI**: ~3-5 seconds per verse (only if uncertain)

### Cost (Stage 2)

- **Per verse**: ~$0.006 if AI is called
- **Genesis 1**: $0.00 (100% certain, no AI needed)
- **Expected**: ~20% of verses need AI = ~$27 for full OT

### Optimization

```yaml
# Use faster model for simple tasks
ai_model: claude-haiku-3-5-20241022  # $0.25/$1.25 per million tokens

# Raise certainty threshold to use AI more aggressively
certainty_threshold: 0.95  # More verses go to AI
```

---

## Example Workflow

### 1. Parse and Check Certainty

```bash
python run_parser_hybrid.py 1 5 --book Gen --no-ai
# Output: ✓ Stage 1 certain (score: 1.00)
```

### 2. Inspect Output

```bash
cat output/Gen/1/5.json | jq .
```

### 3. If Uncertain, Enable AI

```bash
python run_parser_hybrid.py 1 5 --book Gen
# Output: ⚠ Stage 1 uncertain (score: 0.65) → AI resolution
#         ✓ Stage 2 resolved (AI confidence: 0.92)
```

### 4. Review AI Decisions

```bash
cat output/Gen/1/5.json | jq '.metadata.ai_decisions'
```

### 5. Manual Review (if needed)

```bash
cat human_review_queue/Gen/1/5_review.json
```

---

## Next Steps

- **Full Documentation**: See `1_python_rules_2_AI_stage.md`
- **Research Ideas**: See `AI_Integration_Additional_Thoughts.md`
- **Implementation Summary**: See `HYBRID_PARSER_IMPLEMENTATION_SUMMARY.md`
- **Parsing Rules**: See `SPECIFICATION_v1.6.md`

---

## Quick Reference

```bash
# Most common usage
python run_parser_hybrid.py <chapter> <verse> --book <Book> [--no-ai]

# Examples
python run_parser_hybrid.py 1 1 --book Gen --no-ai      # Gen 1:1, no AI
python run_parser_hybrid.py 3 16 --book Exod             # Exod 3:16, with AI
python run_parser_hybrid.py 119 1 --book Ps --no-ai     # Psalm 119:1
```

---

**Ready to parse!** Start with Genesis 1-10, then expand to full Pentateuch.
