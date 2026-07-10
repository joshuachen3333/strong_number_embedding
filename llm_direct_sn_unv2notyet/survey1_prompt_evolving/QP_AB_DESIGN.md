# QP Evidence A/B Design — measuring whether the parsing code helps consensus

**Status: DESIGN ONLY — DO NOT RUN.** This document specifies the experiment;
executing it burns opus / gemini-3-pro / gpt-5.4 quota and is deferred to the
next s10 Gen batch. No LLM call is made by anything in this document.

Governing plan: [`../../parsing/QP_ENRICHMENT_PLAN.md`](../../parsing/QP_ENRICHMENT_PLAN.md) §3.
Conceptual root: [`../../parsing/PARSING_FOUNDATIONS.md`](../../parsing/PARSING_FOUNDATIONS.md).
Capability under test: `--qp-evidence` on `run_gold_standard.py`
(see `ONBOARDING_qp_parsing.md`).

## Hypothesis

Injecting the FHL qp parsing-code table (word/lemma/SN/morph/gloss, original
word order) plus deterministic morph pre-validator findings into R2/R3 judge
context turns verb-attachment and null-legitimacy questions from 3-model
guessing into rule-anchored arbitration — so contested verses resolve in
fewer rounds without hurting objective SN coverage.

## Arms

| Arm | Command core | qp evidence |
|-----|--------------|-------------|
| A (control) | `python3 run_gold_standard.py --book 創 --chap <batch> --force --gold-dir gold_ab_A` | OFF (default) |
| B (treatment) | `python3 run_gold_standard.py --book 創 --chap <batch> --qp-evidence --force --gold-dir gold_ab_B` | ON |

- **Same verse set both arms**: the next s10 Gen batch (fix the exact
  chapter/verse list before starting; record it here).
- **Same model trio** (default panel), **same pinned prompt version**
  (`--prompt-file`/`--prompt-version` pinned explicitly — do NOT rely on
  auto-detect, an auto-evolved prompt mid-experiment invalidates the batch).
- `--naked` default (ON) in both arms.

## Protocol notes (cache hygiene — IMPORTANT)

`round1_results/` / `round2_results/` / `round3_results/` caches are keyed by
(model, book, chap, sec) only — they are NOT aware of prompt content or the
qp flag. A flag flip over existing caches would silently reuse judgments made
under the other arm. Therefore **each arm runs with `--force`** and its own
`--gold-dir` scratch dir, arm A fully completing before arm B starts.
(`--force` also re-runs R1/convergence — accepted: fresh independent samples
per arm.)

The round-level caches are SHARED between arms: arm B's `--force` run
overwrites arm A's round1/2/3 JSONs. If round-level forensics for arm A are
wanted (metric 4 context, judge `reasoning` JSONs), **archive (copy)
`round1_results/`, `round2_results/`, `round3_results/` between arm A
completion and arm B start.**

If a Trigger 1 / R3 prompt evolution fires mid-run the run STOPS by design;
treat that batch as invalidated for A/B purposes, pin the prompt, restart.

## Metrics (primary first)

1. **Consensus rounds** — `resolved_at` histogram per arm (`round1`, `round2`,
   `r2_model_patch`, `round3`, `r2_early_evolution`, `prompt_evolution`,
   `unresolved`), computed by reading the gold JSONs in each arm's
   `--gold-dir` directly. (NOTE: `--show-summary` always reads the canonical
   `gold_standard/` dir — it does NOT see `gold_ab_A`/`gold_ab_B`; do not use
   it for arm metrics.) Success direction: mass shifts toward earlier
   resolution; specifically fewer `round3` + `unresolved`. NOTE: qp evidence
   enters at R2 debate, so `round1` counts should be statistically equal
   between arms — a large R1 gap flags noise, not treatment effect.
2. **Objective SN coverage** — `verify_sn_coverage` perfect-rate over resolved
   verses (already printed at end of every run). Guardrail: arm B must not
   regress vs arm A.
3. **Disagreement rate** — share of verses leaving R1 (`1 − unanimous/total`).
   Randomization check between arms (treatment cannot affect R1), plus the
   denominator for metrics 1's per-contested-verse comparison.
4. Secondary / qualitative: per-verse morph pre-validator violation counts
   (`_qp_morph_errors` in round1 JSONs, violations echoed in run logs); judge
   `reasoning` fields citing the qp table; R2-debate winner margin.

## Analysis

Paired per-verse comparison on the contested subset (verses that left R1 in
BOTH arms): resolution level A vs B (round2 < round3 < unresolved ordinal).
Small-n (one Gen batch) → report counts + sign-test-style summary; no
significance theater.

## Decision rule

- B strictly reduces (round3 + unresolved) count AND coverage guardrail holds
  → propose flipping `--qp-evidence` default to ON (separate review).
- Mixed / null → keep DEFAULT OFF, keep capability for judge-side debugging.
- B regresses coverage or increases unresolved → investigate the evidence
  block wording before any re-run (evidence-not-verdict framing may need
  strengthening, as with WLC).

## Cost estimate

Per contested verse arm-B adds ~0 LLM calls (evidence is injected into calls
that happen anyway); total cost ≈ 2 full-batch runs (the `--force` re-runs),
i.e. roughly 2× a normal batch. Schedule against the colleague token
reservation policy.
