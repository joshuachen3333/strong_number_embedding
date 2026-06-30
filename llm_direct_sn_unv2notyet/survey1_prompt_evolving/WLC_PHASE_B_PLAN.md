# WLC Phase B — plan (for Joshua's review, like Phase A)

> Implements Phase B of [`WLC_INTO_S1_DESIGN.md`](WLC_INTO_S1_DESIGN.md): WLC as
> **evidence** in the R3 (and R2-debate) judge, with bucket classification +
> conservative weighting. Phase A (escalator + annotation) is **done & validated**
> (Gen 2: 2:9 contested, 2:20 suppressed). Phase B touches the **judge** — higher
> risk than A — so this plan goes to review (and the open Qs below to a lala/erha
> /obe2 deliberation) before any code.

## Goal
When the panel splits and a verse is **WLC-contested**, give the judge the WLC
original-language binding as **evidence, not the answer**, and make it **classify +
justify** the divergence into a bucket — so a genuine *collective error* (all models
wrong on identity) is caught, while a *methodology divergence* (FHL-faithful wins,
like 2:20) is kept and logged. WLC **earns** weight via the ledger; it never overrides.

## What Phase A already gives us (no new data plumbing)
`verse_data[vk]["wlc"].divergences[]` is already collected pre-R1 and persisted onto
each gold entry (`wlc_status`, `wlc_divergences`) — including the two-sided
`fhl_only`/`wlc_only` evidence pairs with `wlc_lemma`/`wlc_strong`/`source_token`
(2:20 = H0120 fhl_only paired with H0121 wlc_only). Phase B **consumes** this; no new
extraction needed.

## Mechanism
1. **Evidence into the judge prompt** (`judge.py`):
   - `build_r3_prompt` (and optionally `build_r2_debate_prompt`): when the verse is
     `wlc_status == "divergence"`, append a clearly-fenced **WLC EVIDENCE** block —
     per contested number, the `fhl_only`/`wlc_only` pair + lemma/strong/token —
     framed explicitly as *"independent original-language evidence, NOT the answer;
     identity-axis only; FHL-faithful may still be correct."*
2. **Judge outputs a bucket + justification** (extend the R3 judge schema):
   `{ verdict, best, bucket, bucket_reason }` where
   `bucket ∈ {collective_error, methodology_divergence, placement_or_silent}`.
3. **Resolution mapping** (`consensus.py`, still AD-1 — judge decides, build_gold records):
   - `collective_error` (≥2/3 judges) → gold corrected toward WLC; `trust_tier =
     wlc_corrected` (rare, audit-worthy).
   - `methodology_divergence` (≥2/3) → keep FHL consensus; **auto-append a new D-entry
     to `FHL_DIVERGENCE_LOG.md`** so it's suppressed forever after (like 2:20);
     `trust_tier = c_consensus_over_wlc_divergence`.
   - `placement_or_silent` / no majority → normal consensus; WLC abstains.
4. **Ledger feedback loop**: methodology_divergence rulings grow the log → Phase A's
   primitive auto-suppresses them next run. Calibration data accrues.

## Weighting rule (conservative — from design §4, unchanged)
FHL-faithfulness is the default; WLC tips to `collective_error` only when (i) it's an
identity question the Chinese rendering is silent/neutral on AND (ii) the FHL tag is
an apparent error, not a translation choice. Start advisory; the ledger earns weight.

## Files
| File | Change |
|---|---|
| `judge.py` | WLC-evidence block in `build_r3_prompt` (+maybe `build_r2_debate_prompt`); bucket fields in R3 judge schema/parse |
| `consensus.py` | bucket → resolution mapping; `wlc_corrected` tier; auto-append methodology_divergence to FHL_DIVERGENCE_LOG |
| `run_gold_standard.py` | thread the bucket result through (data already on verse_data) |

## AD-1 / invariants
`build_gold_standard` stays sole `resolved_at` authority; WLC is evidence the **LLM
judge** weighs. WLC identity-axis only — **structurally barred from placement**
buckets. Guarded like Phase A: no WLC evidence ⇒ judge behaves exactly as today.

## Validation
Need a live case where a WLC-contested verse reaches R3 split. 2:9 is contested but
resolved at R2; we may need to find/force an R3 case, or validate on a constructed
fixture. Regression gate as always.

## OPEN QUESTIONS for the lala/erha /obe2 deliberation
1. **Auto-append vs human-confirm**: should a `methodology_divergence` ruling
   auto-write a D-entry to `FHL_DIVERGENCE_LOG`, or queue it for human sign-off
   (like the 2:20 ruling Joshua made by hand)? Trade: speed/automation vs the log
   being a human-authoritative ledger.
2. **R2-debate too, or R3-only?**: feed WLC evidence only at R3 (terminal, cleaner),
   or also at R2-debate (earlier help, but more judge surface to anchor on)?
3. **`wlc_corrected` gate strength**: how many judges must agree `collective_error`
   before overriding consensus toward WLC — 2/3, or unanimous (since overriding a
   3-model consensus on WLC's word is the highest-risk action)?

These three are genuine judgment calls → take to lala (codex) + erha (agy) via /obe2;
Joshua adjudicates ties. Once settled, /workflows implements + validates.
