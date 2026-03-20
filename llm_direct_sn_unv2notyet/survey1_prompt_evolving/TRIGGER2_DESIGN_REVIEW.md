# Trigger 2 Design Review

## What Trigger 2 currently does

Fires when: 2 models converge easily (stable at R1 or R2a) AND their outputs agree AND 1 model is hard/unstable.

Action: auto-resolve with the 2 agreeing models' output, generate a model-specific patch for the unstable model, run a minor patch regression (stability-only).

The debate phase (R2 Phase 2) is skipped entirely.

---

## What the current design is optimizing for

**Stability as a proxy for quality.** If two models independently stabilize at the same output, that is treated as sufficient evidence to auto-resolve — without running the debate.

This is a pragmatic shortcut. The full R2 debate costs 3 more LLM calls per verse. Trigger 2 skips them.

---

## Where the assumption breaks down

### 1. Stability ≠ correctness

A model that confidently produces the same wrong output every time is "easy convergence." Two such models agreeing doesn't make the output right — it means they share the same blind spot. No quality check is done on the agreed output before accepting it. The SN coverage from R1 is already stored in `round1_results[m][verse_key]["_sn_coverage"]` but Trigger 2 never consults it.

### 2. The unstable model has no voice

The unstable model's attempts are mined for the patch, but it never gets to judge the resolution. Its instability might not be noise — it might be trying to get something right that the two stable models both miss. That signal is currently discarded.

Specifically: if the unstable model's attempts cluster into two groups — one matching the stable agreement, one different — that is a very different situation from attempts that are all scattered. The current code does not distinguish these cases.

### 3. The debate phase is bypassed, but this is where it matters most

Normal R2 requires 2/3 of judges to *argue and agree*. Trigger 2 gets 2/3 convergence agreement without any reasoning. The stable models were never asked "is this actually correct?" — they were only asked to produce output twice.

Hard verses that reach Trigger 2 may be exactly the ones most in need of scrutiny. Skipping debate here may be precisely the wrong call.

### 4. Patch regression only checks stability, not correctness

`_run_patch_regression()` passes if new stability ≤ old stability. But a patch could make the unstable model consistently produce a *different wrong answer* and still pass. There is no comparison against the gold standard outputs on those verses.

---

## Proposed improvements (three levels)

### Level 1 — Quality gate before auto-resolving (zero extra LLM calls)

Before accepting the 2-model agreement, verify:
- SN coverage is perfect for both stable models (already in `_sn_coverage`)
- Optionally: the unstable model's best attempt (by SN coverage) does not contradict the agreement on coverage

Data is already available. No additional cost.

### Level 2 — Give the unstable model a validation role (1 extra LLM call)

Instead of only mining its attempts for a patch, ask the unstable model:
"Models A and B agree on this output. Do you agree or disagree, and why?"

This:
- Catches cases where it was right and the others were wrong
- Produces reasoned evidence for the resolution, not just convergence agreement
- Preserves the 2/3 spirit: if the unstable model validates the agreement, you have genuine 3/3 with reasoning

### Level 3 — Trigger 2 routes into the debate path (same cost as full R2)

Rather than a special bypass, treat Trigger 2 as: skip Phase 1 (convergence) for the stable models — they already have stable outputs — and go directly to Phase 2 (debate) with all 3 as judges. The unstable model judging its own instability vs. the stable agreement is meaningful signal. The patch generation can happen in parallel or after.

---

## The deeper framing

Trigger 2 conflates two things:

- **Epistemic confidence**: 2 models agree → the answer is probably right
- **Efficiency**: skip the debate to save LLM calls

These are only compatible when the task is easy. Trigger 2 fires on the harder verses (those that didn't pass R1 unanimity) — exactly the ones where epistemic confidence needs to be *earned*, not assumed from convergence alone.

**Suggested reframe**: Trigger 2 should fast-track patch generation, not fast-track resolution. Let the patch happen; still run the debate (or at minimum the Level 2 validation pass) before committing the gold standard entry. The unstable model gets patched for future verses; this verse gets proper scrutiny.

---

## Open questions for implementation

1. If Level 2 validation is added and the unstable model *disagrees* with the stable agreement, what happens? Route to full debate? Route to R3?
2. Should the patch regression compare against gold standard outputs (not just stability)? Would require gold standard to exist for those verses at regression time.
3. Is "2 easy models agree with perfect SN coverage" a strong enough gate for Level 1, or can models agree on wrong placement while still having perfect SN *count*?
