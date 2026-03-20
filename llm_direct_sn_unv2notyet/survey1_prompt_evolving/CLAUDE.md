# survey1_prompt_evolving/ — 3-Model Gold Standard with Live Prompt Evolution

## Architecture

**MUST READ [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md)** before modifying resolution logic. Key principle: `build_gold_standard()` is the **sole authority** for all `resolved_at` judgments. Main loop only collects data — never directly saves gold standard.

## Purpose

Establish the "best" SN embedding result using 3 top models (opus, gemini-3-pro-preview, gpt-5.4) as a consensus panel. The prompt evolves live during the run, not after.

## 3-Round Consensus

| Round | What happens | Pass criteria | On fail |
|-------|-------------|---------------|---------|
| Round 1 | All 3 models produce output independently | **Unanimous only** (all 3 identical; no 2/3 shortcut — R1 tests if the task is "easy enough" that all 3 independently agree; if even one differs, we want R2 convergence + debate to figure out why) | → Round 2 |
| Round 2 | Convergence (blind re-do) + Debate (judge stable outputs) | **2/3 majority** in debate | → Round 3 |
| Round 3 | Dual-capability: pick winner OR identify collective error | **2/3 majority** or **prompt evolution** | → unresolved (human) |

### Round 2 Detail — Convergence + Debate

**Phase 1: Convergence** (per model, per verse)
1. Model re-does the task **blindly** (same input as R1, no memory of R1 output)
2. Compare R1 vs R2a:
   - Identical → stable at R1
   - Different → retry blindly: R2b, R2c, ... up to `--max-r2-retries` (default 3)
3. Stability = two consecutive identical outputs
4. If never converges → marked "unstable", carries last attempt

**Phase 1.5: Convergence Analysis** (before debate)
After convergence, classify each model as "easy" (stable at R1/R2a) or "hard" (R2b+ or unstable):

| Pattern | Action |
|---------|--------|
| All 3 hard/unstable | **Trigger 1**: early +0.1 prompt evolution. Skip debate & R3. |
| 2 easy + agree, 1 hard | **Trigger 2**: auto-resolve with 2/3 output. Generate model-specific patch for the unstable model. |
| Otherwise | Normal → proceed to debate |

**Trigger 2 — Model-specific patch generation:**
1. Each of the 2 stable models independently gives feedback to the unstable model
2. The unstable model writes its own patch from both feedbacks (self-improvement)
3. Saved as `v1.1.{model}-patch-0.1.md`, version increments if flagged again
4. Next verse loads: base prompt + latest model patch

**Trigger 2 — Instability Score → Patch Intensity**:
Patch intensity scales with instability (unique output count before convergence):

| Score | stable_at      | Level        | Feedback style                                    | 回測 sampling |
|-------|----------------|--------------|---------------------------------------------------|---------------|
| 3     | R2b            | **mild**     | Standard: identify mistakes                       | 10%           |
| 4     | R2c            | **moderate** | + full attempt history + root cause analysis      | 20%           |
| 5+    | R2d+/unstable  | **strong**   | + past trigger2 history + prescriptive rules      | 30%           |

**Trigger 2 — Patch 回測 (minor, solo)**:
After patch generation, re-run only the patched model on past gold standard verses.
Sampling rate scales with instability level (mild=10%, moderate=20%, strong=30%).
Compare to **its own previous stability** (not other models, not gold standard output).
Pass: new stability ≤ old (R1 < R2a < R2b < ... < unstable). Any regression → revert patch.

**Phase 2: Debate** (per verse, if no trigger fired)
- Each model sees all 3 stable outputs + convergence info
- Picks best (A/B/C) or provides corrected version
- 2/3 majority → resolved

### Round 3 Detail — Dual Capability

Each model independently submits one of:

**Option 1 — PICK**: One output is good enough → `{"verdict": "pick", "best": "A/B/C", ...}`

**Option 2 — ALL WRONG**: ALL outputs share the same systematic error → `{"verdict": "all_wrong", "error_identified": "...", "prompt_improvement": "...", ...}`

Resolution:
| R3 result | Next step |
|-----------|-----------|
| 2/3+ pick same winner | → gold standard |
| 2/3+ all_wrong, aligned errors | → **auto prompt evolution (+0.1)** |
| 2/3+ all_wrong, conflicting | → human review |
| No consensus | → unresolved (human) |

"Aligned" = keyword overlap check on `error_identified` fields (same SN tags or error category).

## Live Prompt Evolution

The prompt evolves **during** the gold standard run:

1. Process a batch of verses with current prompt
2. R3 judges identify collective error → prompt weakness found
3. Auto-draft new prompt version (v1.x+1) from judge suggestions
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
  "resolved_at": "round1|round2|round3|prompt_evolution|unresolved",
  "prompt_version": "v1.1",
  "round1": {
    "opus": {"lcc_sn": "...", "confidence": 0.95, "opinion": "unanimous|majority|minority"},
    "gemini-3-flash-preview": {"lcc_sn": "...", "confidence": 0.98, "opinion": "..."},
    "gpt-5.4": {"lcc_sn": "...", "confidence": 0.90, "opinion": "..."}
  },
  "round2_convergence": {
    "opus": {"stable_result": "...", "converged": true, "stable_at": "R1", "attempt_count": 2},
    ...
  },
  "round2": {
    "opus_as_judge": {"best": "A", "corrected": null, "reasoning": "...", "opinion": "majority"},
    ...
  },
  "round3": {
    "opus_as_judge": {"verdict": "pick", "best": "A", "reasoning": "...", "opinion": "majority"},
    ...
  }
}
```

## File Structure

```
survey1_prompt_evolving/
├── run_gold_standard.py     # Main orchestrator + CLI (per-verse pipeline)
├── cli_caller.py            # Unified CLI wrapper (claude/gemini/codex)
│                            #   modes: production, judge, freeform
├── comparator.py            # Strict unanimous check for Round 1
├── judge.py                 # R2 convergence + debate, R3 dual-capability,
│                            #   model patch generation (feedback + self-patch)
├── consensus.py             # Tally votes → gold standard output
├── regression.py            # 回測: sampling + execution + pass/fail gate
├── prompts/                 # Versioned prompt files
│   ├── v1.0.md              # Baseline (copy of system_prompt_lcc.md)
│   ├── v1.1.md              # +implicit markers, +format preservation, +self-check
│   ├── v1.1.opus-patch-0.1.md        # Model-specific patch (auto-generated)
│   ├── v1.1.gpt-5.4-patch-0.1.md    # Model-specific patch (auto-generated)
│   └── ...
├── gold_standard/{Book}/{chap}/{sec}.json     # Final consensus JSONs
├── round1_results/{model}/{Book}/{chap}/{sec}.json
├── round2_results/{model}/{Book}/{chap}_{sec}_convergence.json
├── round2_results/{model}/{Book}/{chap}_{sec}.json          # debate
├── round2_results/{model}/{Book}/trigger2_patches/          # Trigger 2 records
│   └── {chap}_{sec}_patch_record.json   # feedbacks + self-patch + attempts
├── round2_results/prompt_evolution/{Book}/                  # Trigger 1 records
│   └── {chap}_{sec}_evolution_record.json
├── round3_results/{model}/{Book}/{chap}_{sec}.json
├── round3_results/prompt_evolution/{Book}/                  # R3 evolution records
│   └── {chap}_{sec}_evolution_record.json
└── run_logs/                # Timestamped logs with verse range
    └── run_{timestamp}_{Book}_{chap}_{sec}-{end}.log
```

## Records Persisted

| Event | What's saved | Location |
|-------|-------------|----------|
| R1 output | Each model's lcc_sn, confidence, SN coverage | `round1_results/` |
| R2 convergence | Full attempt history, stable_at, converged flag | `round2_results/..._convergence.json` |
| R2 debate | Each judge's pick, corrected, reasoning | `round2_results/..._debate.json` |
| R2 Trigger 1 (all unstable) | Convergence data for all 3 models | `round2_results/prompt_evolution/` |
| R2 Trigger 2 (model patch) | Both stable models' feedback text, unstable attempts, self-written patch | `round2_results/.../trigger2_patches/` |
| R3 judgments | verdict (pick/all_wrong), reasoning | `round3_results/` |
| R3 prompt evolution | All judges' error_identified + prompt_improvement | `round3_results/prompt_evolution/` |
| Gold standard | Everything consolidated + resolved_at + opinions | `gold_standard/` |
| Run log | Full console output with timestamps | `run_logs/` |

## CLI Usage

```bash
# Default: Gen 1-2, auto-detects latest prompt (e.g., v1.1), skips cached results
python3 run_gold_standard.py

# Small batch: first 3 verses only
python3 run_gold_standard.py --book 創 --chap 1 --verse-count 3

# Custom scope
python3 run_gold_standard.py --book 創 --chap 1-5
python3 run_gold_standard.py --book 創 --chap 1 --sec 1-10

# Re-run even if cached (default: skip cached)
python3 run_gold_standard.py --force

# Override prompt (default: auto-detect latest in prompts/)
python3 run_gold_standard.py --prompt-file prompts/v1.0.md

# Control R2 convergence retries (default: 3)
python3 run_gold_standard.py --max-r2-retries 2

# Phases
python3 run_gold_standard.py --round1-only
python3 run_gold_standard.py --skip-round1

# Inspect results
python3 run_gold_standard.py --show-summary
python3 run_gold_standard.py --show-disagreements

# Regression testing
python3 run_gold_standard.py --regression --trigger-verses 1:4,1:16
```

### Defaults
- **Prompt**: auto-detects highest version in `prompts/` (e.g., `v1.1.md` over `v1.0.md`)
- **Cached results**: skipped by default (use `--force` to re-run)
- **R2 retries**: 3 (R2a + up to 3 retries = max 4 attempts)

## Convergence

The prompt has converged when:
- Round 1 unanimous rate > 80%
- R3 stops triggering "all_wrong" (no more prompt evolutions)
- No new weakness patterns emerge

Expected: **3-4 generations** (v1.0 → v1.1 → v1.2 → maybe v1.3).

## Known Issues (from v1.0 3-verse test)

1. **Gemini-3-pro-preview** returned 0 SNs for 2/3 verses → **swapped to gemini-3-flash-preview**
2. **SN zero-padding** inconsistent → **addressed in v1.1 prompt**
3. **Implicit markers** `{<WH0853>}` dropped → **addressed in v1.1 prompt**
4. **Prefix markers** `<WAH09002>` dropped → **addressed in v1.1 prompt**
