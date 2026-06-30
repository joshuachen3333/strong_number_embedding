# lala position — s10 self-optimization R1

Meeting: `s10_self_opt-20260630-m01`
Topic: `s10_self_opt`

Thesis check: I support the framing that s10 should keep prompts frozen and put all learning into atomic, gated, revertible conventions. Prompt mutation should remain a historical baseline behavior from s1, not an s10 mechanism.

## D1 — Per-model conventions (M-tier) + cross-model promotion

GO.

Pick:
- Add `conventions.<model>.md` as the Trigger-2 replacement for per-model prompt patches.
- Promotion threshold: `k=2` for this N=3 meeting, expressed generally as roster majority.
- Promotion path: M->C must pass the global regression gate before becoming active globally.
- Demotion: mirror global convention demotion, but measure the M-rule first against that model's own FHL-truth delta; prune when the measured delta is neutral or negative after the configured support window.

One-line why: M-tier is worth the extra state because it turns model instability from opaque prompt text into comparable evidence that can be promoted, demoted, and audited.

## D2 — Prompt provenance / warm-start

GO on freeze, NO-GO on inheriting s1 per-model patches into active s10 state.

Pick:
- Do not seed active `conventions.<model>.md` from s1 per-model patches.
- Keep the shared prompt frozen at the v1.2 fork for the contest.
- If useful, import s1 patches only as inactive candidate notes for later A/B, never as pre-enabled behavior.

One-line why: s10 needs a stable baseline so measured gains belong to conventions, not to a moving or inherited s1 prompt lineage.

## D3 — Falsification loop wired to measured accuracy

GO.

Pick:
- Wire convention falsification to per-convention A/B using FHL-truth delta.
- Default action should be automatic quarantine/demotion for neutral or negative deltas, with manual override only for explicitly documented theological/text-critical exceptions.

One-line why: conventions are only an improvement over prompt mutation if they can be falsified by measured accuracy and removed without touching unrelated behavior.

## D4 — D-deliberation -> convention closed loop

GO, with a gate.

Pick:
- D-deliberation outcomes should produce candidate conventions when the resolution exposes a reusable rule, not for every one-off verse.
- The candidate must pass the same convention gate before activation.
- Store the originating D case as provenance so later regressions can cite the source decision.

One-line why: D should be the discovery surface for recurring ambiguity, but the scribe step must distill only reusable rules into conventions.

## D5 — WLC evidence into D-deliberation

GO.

Pick:
- Feed `wlc_check` into D-deliberation as independent evidence.
- Keep WLC as evidence, not an override.
- Preserve FHL-faithful default behavior and route real WLC/FHL tensions through `FHL_DIVERGENCE_LOG`.

One-line why: D-deliberation should use the strongest non-LLM identity signal available, while final authority still stays with the FHL-facing gold standard policy.

## Summary

My vote is GO on D1, D3, D4, D5; GO on D2 only as a freeze policy and NO-GO on active s1 patch warm-start. The closed design is: frozen prompt, active global conventions, active per-model conventions, majority promotion through a global gate, measured falsification by FHL-truth delta, D outcomes distilled into gated candidates, and WLC supplied as evidence without override power.
