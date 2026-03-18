# survey1/ — 3-Model Gold Standard with Live Prompt Evolution

## Purpose

Establish the "best" SN embedding result using 3 top models (opus, gemini-3-pro-preview, gpt-5.4) as a consensus panel. The prompt evolves live during the run, not after.

## 3-Round Consensus

| Round | Pass criteria | On fail |
|-------|-------------|---------|
| Round 1 | **Unanimous** (all 3 identical) | → Round 2 |
| Round 2 | **2/3 majority** (each model judges) | → Round 3 |
| Round 3 | **2/3 majority** (with full R1+R2 history) | → unresolved (human) |

## Live Prompt Evolution

The prompt evolves **during** the gold standard run:

1. Process a batch of verses with current prompt
2. If judges provide **corrections** (not just picking A/B/C) → prompt weakness found
3. Improve prompt → draft new version (v1.x+1)
4. **回測 (regression test)** against all past gold standard
5. Pass → switch to new prompt, continue forward
6. Fail → revert, try different fix

**The prompt is alive. Never wait to finish before evolving.**

## 回測 (Regression) Rules

### Sampling rates

| Category | Target % | Min count to start sampling |
|----------|----------|----------------------------|
| Trigger (caused this change) | 100% | always all |
| Past Round 3 verses | 80% | ≥ 5 → sample, else **all** |
| Past Round 2 verses | 50% | ≥ 10 → sample, else **all** |
| Past Round 1 unanimous | 20% | ≥ 20 → sample, else **all** |

**Early in the run**: few verses → test everything (effectively 100%).
**Later**: sampling kicks in naturally as gold standard grows.

### Pass/Fail criteria

| Result | Verdict |
|--------|---------|
| Matches old gold standard | PASS |
| Better (judges agree superior) | PASS (upgrade) |
| Worse or unresolved | **FAIL** |
| **Any single FAIL** | **Prompt change rejected** |

## Gold Standard JSON Format

Each verse in `gold_standard/{chap}/{sec}.json`:

```json
{
  "book": "Gen", "chap": 1, "sec": 1,
  "lcc_sn": "...(consensus result)...",
  "lcc_original": "...",
  "unv_sn_reference": "...",
  "resolved_at": "round1|round2|round3|unresolved",
  "prompt_version": "v1.1",
  "round1": {
    "opus": {"lcc_sn": "...", "confidence": 0.95, "opinion": "majority|minority|unanimous"},
    "gemini-3-pro-preview": {"lcc_sn": "...", "confidence": 0.98, "opinion": "..."},
    "gpt-5.4": {"lcc_sn": "...", "confidence": 0.90, "opinion": "..."}
  },
  "round2": {
    "opus_as_judge": {"best": "A", "corrected": null, "reasoning": "...", "opinion": "majority"},
    ...
  },
  "round3": null
}
```

## File Structure

```
survey1/
├── run_gold_standard.py     # Main orchestrator + CLI
├── cli_caller.py            # Unified CLI wrapper (claude/gemini/codex)
├── comparator.py            # Strict unanimous check for Round 1
├── judge.py                 # Rounds 2-3: each model judges
├── consensus.py             # Tally votes → gold standard output
├── regression.py            # 回測: sampling + execution + pass/fail gate
├── analyze.py               # Judge correction analysis (TODO)
├── prompts/                 # Versioned prompt files
│   ├── v1.0.md              # Baseline (copy of system_prompt_lcc.md)
│   ├── v1.1.md              # First evolution
│   └── ...
├── gold_standard/           # Final consensus JSONs
├── round1_results/          # Raw Round 1 outputs per model
├── round2_results/          # Round 2 judge decisions
└── round3_results/          # Round 3 final arbitration
```

## CLI Usage

```bash
# Full run (default: Gen 1-2)
python3 run_gold_standard.py

# Custom scope
python3 run_gold_standard.py --book 創 --chap 1-5
python3 run_gold_standard.py --book 創 --chap 1 --sec 1-10

# Resume interrupted run
python3 run_gold_standard.py --resume

# Use specific prompt version
python3 run_gold_standard.py --prompt-file prompts/v1.1.md

# Phases
python3 run_gold_standard.py --round1-only
python3 run_gold_standard.py --skip-round1

# Inspect results
python3 run_gold_standard.py --show-summary
python3 run_gold_standard.py --show-disagreements

# Regression testing
python3 run_gold_standard.py --regression --trigger-verses 1:4,1:16
```

## Convergence

The prompt has converged when:
- Round 1 unanimous rate > 80%
- Judges stop providing corrections (just pick among originals)
- No new weakness patterns emerge

Expected: **3-4 generations** (v1.0 → v1.1 → v1.2 → maybe v1.3).

## Known Issues (from 3-verse test)

1. **Gemini-3-pro-preview** returned 0 SNs for 2/3 verses (needs investigation)
2. **SN zero-padding** inconsistent: opus writes `<WH430>`, UNV has `<WH0430>`
3. **Implicit markers** `{<WH0853>}` dropped by all 3 models in Round 1
4. **Prefix markers** `<WAH09002>` dropped entirely
