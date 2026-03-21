# survey1_prompt_evolving/ — 3-Model Gold Standard with Live Prompt Evolution

## Architecture

**MUST READ [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md)** before modifying resolution logic. Key principle: `build_gold_standard()` is the **sole authority** for all `resolved_at` judgments. Main loop only collects data — never directly saves gold standard.

**Visual overview**: [`SYSTEM_DIAGRAMS.html`](SYSTEM_DIAGRAMS.html) — 8 interactive diagrams (Mermaid) covering the full R1→R2→R3 pipeline, trigger mechanisms, prompt evolution, and architecture components. Open in browser.

## Purpose

Establish the "best" SN embedding result using 3 top models (opus, gemini-3-pro-preview, gpt-5.4) as a consensus panel. The prompt evolves live during the run, not after.

## Full Flow

```
R1 → UNANIMOUS → gold standard (done)
R1 → DISAGREED → R2 convergence → classify Level 0-3
  → avg ≥ 2.0? → TRIGGER 1 (prompt +0.1, stop)
  → 2 agree + distance ≥ 2.0? → TRIGGER 2 (auto-resolve + model patch)
  → neither → R2 debate (2/3 majority)
    → resolved → gold standard
    → no 2/3 → R3 (dual: pick OR all_wrong)
      → pick 2/3 → gold standard
      → all_wrong 2/3 → prompt +0.1
      → no consensus → unresolved (human)
```

## R1 — Unanimous Check

All 3 models produce output independently. **Unanimous only** — no 2/3 shortcut.
R1 tests if the task is "easy enough" that all 3 independently agree.
If even one differs → R2.

## R2 — Convergence + Triggers + Debate

### Phase 1: Convergence

Each model re-does the task **blindly** (no memory of R1). R2a compared with R1 only.
R2b+ compared with all previous R2 attempts (back-comparison, not R1).
Unlimited retries by default (`--max-r2-retries 0`). Bail out after 3 consecutive errors.

### Phase 1.5: Stability Classification (AD-2)

| Level | Name | Condition | Unique outputs |
|-------|------|-----------|----------------|
| 0 | Easy | stable at R1 or R2a | ≤2 |
| 1 | Mild | stable at R2b | 3 |
| 2 | Moderate | stable at R2c-R2d | 4 |
| 3 | Strong | stable at R2e+ or never converged | 5+ |

### Trigger 1 — 共通 Prompt +0.1 (全體掙扎)

| 條件 | 行動 |
|------|------|
| 三模型 avg level ≥ 2.0 | prompt +0.1，停止 pipeline |

三模型各自生成新 prompt → 互評投票（2/3 多數決）→ 回測 → 部署。

### Trigger 2 — Model-Specific Patch (一弱二強)

| 條件 | 行動 |
|------|------|
| 2 模型 agree (`texts_match`) + distance ≥ 2.0 | auto-resolve + 弱模型 patch |

**Distance = 弱模型 level − 一致模型 avg level**

| Agreed | Weak | Distance | Trigger? |
|--------|------|----------|----------|
| 0, 0 | 2 | 2.0 | Yes |
| 0, 0 | 3 | 3.0 | Yes |
| 0, 1 | 3 | 2.5 | Yes |
| 1, 1 | 3 | 2.0 | Yes |
| 0, 0 | 1 | 1.0 | No |
| 1, 1 | 2 | 1.0 | No |
| 2, 2 | 3 | 1.0 | No |

Patch 生成：2 穩定模型各自給 feedback → 弱模型自己寫 patch（含已有 patch 的進化）。
Patch 力度隨 level 調整（mild=標準, moderate=+root cause, strong=+prescriptive rules）。
Patch 回測：solo self-comparison（mild=10%, moderate=20%, strong=30%）。

### Phase 2: Debate

No trigger fired → 三模型互評 stable outputs → 2/3 majority → gold standard。

## R3 — Dual Capability

進入 R3 = R2 debate 沒有 2/3 共識。每個模型獨立判斷：

| 選項 | 條件 | 行動 |
|------|------|------|
| **pick** 2/3 同一個 | 多數選同一個 winner | → gold standard |
| **all_wrong** 2/3 + errors aligned | 多數認為全錯 + 原因一致 | → prompt +0.1 |
| **all_wrong** 2/3 + errors conflict | 多數認為全錯但原因不同 | → human review |
| no consensus | 沒有任何 2/3 | → unresolved (human) |

## 觸發共通 Prompt +0.1 的三種情形

| 情形 | 觸發時機 | 條件 |
|------|---------|------|
| **R2 Trigger 1** | R2 convergence 之後 | 三模型 avg level ≥ 2.0 |
| **R3 all_wrong** | R3 判決時 | 2/3 judge 說 all_wrong + error aligned |
| **人類決定** | 任何時候 | 人類主動提出改進（如 v1.2 annotation projection）|

三者都走同一流程：三模型各自生成新 prompt → 互評投票 → 回測 → 部署。
差別只在檔名 trigger 標記（`_Gen_1_7` vs `_joshua`）。

## Live Prompt Evolution

The prompt evolves **during** the gold standard run. Per-verse pipeline:
each verse completes R1 → R2 → R3 before moving to the next.
If any trigger fires prompt +0.1, pipeline stops immediately.

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
