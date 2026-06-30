# ➡️ MOVED — see survey11_gold_factory_selection/

> 2026-06-30 (Joshua): the s1-vs-s10 gold contest grew into its own survey. The full
> design now lives at
> [`../survey11_gold_factory_selection/S10_VS_S1_GOLD_EXPERIMENT.md`](../survey11_gold_factory_selection/S10_VS_S1_GOLD_EXPERIMENT.md)
> (git history preserved), framed by
> [`../survey11_gold_factory_selection/CLAUDE.md`](../survey11_gold_factory_selection/CLAUDE.md).

**Why moved**: the contest is a *gold-factory selection* (which method **and** which WLC
source config produces gold closest to FHL truth) — a cross-survey question, no longer an
s10-internal doc.

**Harness stays here** (`run_a2_contest.py`, `run_stage2_harsh.py`, `build_exclusion.py`,
`wlc_check.py`, `eval_gold_vs_wlc.py`) and is referenced cross-dir by the moved design;
it may migrate to survey11 when the contest moves in full.

This stub is left so existing links resolve. Update references to point at survey11.
