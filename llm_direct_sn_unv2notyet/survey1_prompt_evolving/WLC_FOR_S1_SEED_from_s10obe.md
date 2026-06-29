# Seed — putting WLC *inside* S1's consensus loop (from survey10-obe)

> A beginning prompt for survey1-obe. Joshua will join you at your window (1314)
> to develop this. This is a seed, not a finished design. Reply-back / coordinate:
> survey10-obe at Terminal window **5544**.

## The core idea

S1 today validates **only against FHL** (UNV+SN) — a single-source circularity:
LLM consensus is treated as truth, but consensus ≠ truth. **WLC (Clear Bible) is a
second, INDEPENDENT human alignment of the original Hebrew.** We just proved it has
teeth: `…/survey10_…/eval_gold_vs_wlc.py` did an SN-inventory check of the current
gold (reusing *your* `FHL_DIVERGENCE_LOG.md` + survey5's morph bridge) →
**982/986 consistent**, and surfaced exactly **one** real judgment call: the 2:20
Adam case you just ruled. That post-hoc check works. The seed is: **move WLC from
post-hoc validator to an in-loop signal.**

## Two concrete mechanisms to develop

### (A) Cheap WLC pre-pass → consensus cost-triage
Before the expensive 3-model consensus, run the (free, no-LLM) WLC inventory check
per verse:
- **WLC agrees** with the FHL-projected annotation → high-confidence verse; it can
  take a *lighter* consensus path (or skip straight to R1-unanimous fast-track).
- **WLC diverges** → pre-flag as hard/contestable; route the *expensive* R2/R3
  scrutiny THERE.

This turns the validator into a **cost-router**: spend consensus budget where the
independent truth says it's actually needed. (Ties into H4 "cheaper over time".)

### (B) WLC as arbiter *evidence* in R3 / collective-error
When your 3 models split at R2/R3, inject the **WLC original-language binding**
(Hebrew lemma + morph via survey5 bridge + which source token) into the R3 judge
prompt as **EVIDENCE — not as the answer**. It gives the judge a non-LLM anchor to
tell a genuine *collective error* from a mere *methodology divergence*.

## THE KEY CAVEAT (your 2:20 ruling crystallised it)

**WLC is a tiebreaker INPUT, never an override.** FHL-faithful translation-anchoring
can legitimately win: 那人 = "the man" = `H0120` beat WLC's `H0121` ("Adam"),
because the task *transfers* FHL's SN and the Chinese word anchors H0120. So the
real open design question for you + Joshua:

> **How should the R3 judge WEIGH WLC-evidence against FHL-faithfulness?**

`FHL_DIVERGENCE_LOG.md` is the growing ledger of "WLC-grounded but FHL-faithful
wins" cases — that ledger is exactly the training signal for the weighting. A
divergence is a *flag for attention*, not an automatic correction.

## Artifacts to build on
- `…/survey10_…/eval_gold_vs_wlc.py` — the inventory validator (lexical + 09xxx
  prefix + s5 morph bridge; reads your divergence log).
- `./FHL_DIVERGENCE_LOG.md` — your divergence ledger (D1 = 2:20).
- `…/survey5_…/morph_bridge.json` — WLC morph → FHL 8xxx (leave-one-out 100%).
- `…/survey10_…/CLEAR_BIBLE_CROSS_SURVEY_VALUE.md` — the full cross-survey writeup
  (s1/s9/s10), incl. the no-Chinese limit (WLC is source-side/cross-check, never a
  Chinese-target answer key).

## Don't forget the limit
WLC has **no Chinese** → it can judge the SN *inventory* (which numbers) and arbitrate
*original-language* questions, but it **cannot** score *placement* (which Chinese
token). Keep WLC on the source/evidence side; FHL/UNV stays the Chinese-target truth.
