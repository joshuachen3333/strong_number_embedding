# WLC into the S1 consensus loop — design

> survey1-obe + Joshua, 2026-06-29. Develops the s10 seed
> [`WLC_FOR_S1_SEED_from_s10obe.md`](WLC_FOR_S1_SEED_from_s10obe.md). Moves WLC
> (Clear Bible independent Hebrew alignment) from post-hoc validator
> (`…/survey10_…/eval_gold_vs_wlc.py`) into S1's consensus loop, **without**
> breaking AD-1 (`build_gold_standard()` sole authority) or the FHL-faithful task.

## Decisions locked (Joshua, 2026-06-29)

1. **Asymmetric triage — ACCEPTED.** WLC can only *add* scrutiny, never remove it
   (it is placement-blind). §2.
2. **Conservative default weighting — AGREED.** WLC is advisory; FHL-faithfulness is
   the default tie-break; the `FHL_DIVERGENCE_LOG` ledger earns WLC any future weight.
   §4.
3. **A before B, but BOTH are in scope.** Phase A (escalator, gold-safe) ships first
   and is validated; Phase B (WLC-as-evidence in the judge) follows. **Neither is
   dropped — the full design is A *then* B, not A-only.** §7.

## 0. The rails (boundary — read first)

- **WLC = independent human alignment of the original Hebrew**, bridged to FHL 8xxx
  via `…/survey5_…/morph_bridge.json` (leave-one-out ~100%).
- **WLC speaks ONLY to the IDENTITY axis**: (1) SN *inventory* (which numbers), (2)
  original-language *lemma/identity* questions.
- **WLC is BLIND to placement** (which Chinese token gets the tag) — it has **no
  Chinese**. This is the load-bearing limit; it constrains both mechanisms below.
- **WLC is a tiebreaker INPUT, never an override** — FHL-faithful can win (the 2:20
  ruling). A divergence is a *flag for attention*, not an automatic correction.

## 1. One shared primitive: `wlc_check(verse)`

Both mechanisms consume a single free (no-LLM) per-verse signal, lifted from s10's
`eval_gold_vs_wlc.py` into a callable S1 can import:

```
wlc_check(verse) -> {
  status: "match" | "divergence" | "no_signal",
  divergences: [ { bare_num, fhl_tag, wlc_lemma, wlc_strong, source_token,
                   kind: "methodology_divergence_logged" | "unresolved" } ],
  coverage: float,   # fraction of FHL numbers WLC could speak to
}
```

- Reads [`FHL_DIVERGENCE_LOG.md`](FHL_DIVERGENCE_LOG.md): already-ruled cases (e.g.
  D1 = 2:20) come back pre-tagged `methodology_divergence_logged` and do **not**
  re-flag. Only **new** divergences are `unresolved`.
- `no_signal` (WLC doesn't cover the word) → verse falls back to pure consensus.

## 2. Mechanism A — WLC pre-pass = **asymmetric** cost-triage (gold-safe)

Run `wlc_check` **before R1**, per verse. **Key correction to the seed**: the triage
is **asymmetric — WLC can only ADD scrutiny, never remove it.**

- **`unresolved` divergence → `wlc_contested`**: **escalate this verse** to full
  R2/R3 scrutiny **even if R1 is unanimous**. This is the headline value: WLC catches
  the **"unanimous-but-wrong on identity"** blind spot that consensus alone cannot
  see (all 3 models can share the same error; WLC is the independent witness).
- **`match` → `wlc_corroborated` (annotation only)**: a confidence boost recorded in
  gold; it does **NOT** license skipping R2/R3.

**Why no symmetric skip** (the sharp point): WLC is **placement-blind**, so
WLC-agreement on *inventory* does **not** certify *placement*. Most S1 R2/R3
escalations resolve placement disputes — which WLC cannot see — so WLC-agree cannot
safely suppress them. The cost win is therefore indirect: stop over-investing blind,
and force investment exactly where independent truth flags an identity problem.
(Symmetric skip can be revisited later, only for verses whose only open question is
inventory, once the ledger calibrates it.)

## 3. Mechanism B — WLC as **evidence** in R2-debate / R3 judge

When the panel splits, inject the WLC binding into the judge prompt as **EVIDENCE,
not the answer**: per contested number, "WLC aligns this to lemma X (Strong WLC_S),
morph Y, source token Z." The judge must **classify** into a bucket and justify it:

| Bucket | Meaning | Action |
|---|---|---|
| `collective_error` | all models share a tag WLC + reasoning show is wrong **on identity** | correct toward WLC (this is where WLC breaks consensus circularity) |
| `methodology_divergence` | FHL-faithful tag differs from WLC but is justified by the translation anchor (2:20) | keep FHL; append to `FHL_DIVERGENCE_LOG` |
| `placement_or_silent` | WLC can't speak (placement) / WLC abstains | resolve by normal consensus |

This reuses the bucketing we already built for the contest scorer. WLC informs the
first two; it is structurally barred from the third.

## 4. The weighting rule (the heart — not a number, a decision rule)

The judge applies, **conservatively by default**:

1. WLC-evidence acts **only on the identity axis**, never placement.
2. **Default: FHL-faithfulness wins** when the target word anchors the FHL tag (2:20
   principle).
3. WLC **tips** to `collective_error` only when **BOTH**: (i) the question is
   original-language identity that the Chinese rendering is **silent/neutral** on,
   **AND** (ii) FHL's tag is an **apparent error**, not a defensible translation
   choice.
4. **Calibration ledger**: every ruling is logged — `methodology_divergence` (WLC
   lost) and `collective_error` (WLC won). The ratio + patterns over Gen 1–5 tell us
   whether to loosen or tighten. **Start conservative** (WLC advisory; FHL-faithful
   default) and let the ledger earn any increase in WLC's weight.

## 5. Trust tiers (extend the existing `trust_tier` field — make WLC visible)

- `c_consensus + wlc_corroborated` — consensus AND WLC agree → **highest** trust
  (independent cross-check passed).
- `c_consensus` — consensus; WLC silent/placement.
- `c_consensus_over_wlc_divergence` — consensus held; WLC diverged but ruled
  methodology_divergence (logged).
- `wlc_corrected` — consensus was a collective error; WLC-evidence corrected it
  (rare, audit-worthy).

## 6. AD-1 compliance (non-negotiable)

`build_gold_standard()` stays the **sole `resolved_at` authority**. `wlc_check` is a
**data provider** (like `round1_results`); WLC evidence is *collected* and fed into
R2/R3 judge prompts and *recorded*. The **LLM judge** makes the call; build_gold
records it. **WLC never writes gold directly.** Architecture preserved.

## 7. Phased implementation

1. **Primitive**: lift `wlc_check` into a shared importable callable (from
   `eval_gold_vs_wlc.py`), reading `FHL_DIVERGENCE_LOG`. Pure data, no pipeline change.
2. **Phase A (escalator)**: wire `wlc_check` before R1; `wlc_contested` forces R2/R3
   even on R1-unanimous; record `wlc_corroborated`/`wlc_contested` in gold. Additive,
   gold-safe. Validate on Gen 1–2 (2:20 is the known divergence).
3. **Phase B (evidence)**: extend `build_r3_prompt` (+ r2_debate) to inject WLC
   evidence and require bucket output; extend `consensus.py` to record the bucket +
   new trust tiers + auto-append rulings to `FHL_DIVERGENCE_LOG`.
4. **Calibrate**: run Gen 1–5; inspect every `wlc_contested` ruling; tune judge
   conservatism.
5. **Regression**: every WLC change must pass the existing regression gate (no
   settled verse silently changes).

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| WLC-as-override creep (B) | bucket + justification + conservative default + ledger audit; WLC structurally barred from placement |
| survey5 morph-bridge errors | WLC evidence is advisory; judge can discount; bridge already LOO ~100% |
| placement blindness misused | hard boundary in `wlc_check` output — it emits **identity-axis signals only** |
| WLC coverage gaps | `no_signal` → fall back to pure consensus |
| circularity oversell | be precise: WLC breaks circularity for **inventory/identity only**, not placement |

## 9. What this buys S1

- An **independent, free, non-LLM** check that catches **unanimous-but-wrong-on-
  identity** — the one failure pure consensus structurally cannot see.
- **Budget routing** toward genuinely-hard verses (escalator).
- A **visible, auditable** WLC contribution per verse (trust tiers + ledger).
- All **without** ceding the FHL-faithful task or AD-1.
