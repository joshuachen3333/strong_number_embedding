# /obe2 R-1 synthesis — `wlc_phaseB-20260630-m01`, topic `wlc_phase_b`

Chair digest of the three R-1 positions. Cites `obe:e0001:0002` (agenda),
`lala:e0001:0002`, `erha:e0001:0002`. Refutable by a `review` event.

## Q2 — evidence stage → **R3-only** (3/3 UNANIMOUS, ADOPT)
All three: feed WLC evidence to the judge only at R3. Smallest anchoring surface;
matches "WLC adds late scrutiny, never drives the panel." No dissent.

## Q3 — override gate for `wlc_corrected` → **UNANIMOUS gate** (3/3 UNANIMOUS, ADOPT)
All three: overriding a 3-model consensus *toward WLC* is the highest-risk action and
requires **all 3 judges** to agree `collective_error`. One informed dissent keeps the
result FHL-faithful. Consistent with the conservative weighting Joshua locked in Phase A.

## Q1 — ledger write → **provisional auto-append** (RECONCILED)
- lala: human-confirm (queue; preserve Joshua's ledger as authoritative).
- erha: provisional auto-append (flag prevents stall, preserves human authority).
- obe synthesis: **auto-append the D-entry as `provisional: true`, and a provisional
  entry does NOT yet suppress escalation** — it is a queued candidate. Only a human
  ratification flips `provisional → active`, at which point it suppresses forever after.
  This captures BOTH positions: erha's no-stall auto-capture AND lala's
  human-authority + no premature suppression (a wrong bucket call cannot silently
  suppress before a human sees it). Operationally lala's "queue" == erha's "provisional,
  non-suppressing" — same behavior, pre-filled. **Needs Joshua to bless the semantics.**

## Q4 — Gen 1:1-21 mixed-state → **2/3 re-run 1:22-31, but Joshua's gold** (ESCALATE)
- lala + obe: **re-run 1:22-31** — 1:1-21 is already validated + WLC-annotated; reverting
  discards good work and leaves Gen 1 un-WLC-annotated (defeats Phase A's purpose for
  Gen 1). Once the tail is re-run + regression-passed, Gen 1 is a uniform NEW baseline.
- erha (dissent): **revert 1:1-21 to prior gold** — a mixed-state chapter destroys the
  regression control baseline; revert for a stable control.
- obe note: erha's baseline concern is real but addressable — a uniform NEW Gen 1 is a
  better baseline than a uniform OLD one lacking WLC annotation. Still, this mutates the
  gold standard Joshua owns → **his adjudication.**

## To `/workflows` once Joshua settles
Adopt now: **Q2 = R3-only, Q3 = unanimous gate.** Pending blessing: **Q1 provisional
semantics, Q4 direction.** Then implement Phase B (`judge.py` WLC-evidence block +
bucket schema; `consensus.py` bucket→resolution mapping + `wlc_corrected` tier +
provisional ledger append) and re-validate (regression gate).
