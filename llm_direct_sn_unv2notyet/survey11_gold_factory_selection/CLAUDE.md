# survey11_gold_factory_selection

> Created 2026-06-30 (Joshua). Spun out of survey10 so the **"which gold factory?"**
> question is a first-class survey, not an s10-internal doc.

## What this survey decides

**Which configuration produces the gold closest to FHL ground truth** — across two
independent axes that must not be confounded:

1. **Method axis** — `s1` (3-model consensus, prompt-evolution) vs `s10` (same consensus
   **+** externalized conventions subsystem). This is the original A-vs-B contest.
2. **Source axis** — *which readable bridge* rides along with the WLC Hebrew source:
   **BSB / YLT / BSB+YLT / BSB+YLT+KJV**. This is the open question that triggered the
   spin-out.

The unifying trick (from survey5): project an annotated **non-Chinese** source onto
**UNV** (which has FHL tags) and score against UNV's real FHL annotation — objective, no
consensus circularity, no answer leak.

## Design of record

- **[`S10_VS_S1_GOLD_EXPERIMENT.md`](S10_VS_S1_GOLD_EXPERIMENT.md)** — the full contest
  design (moved here from survey10, git history preserved). Read **§ Source pivot** (KJV
  retired → WLC + aligned English) and **§ OPEN QUESTION — which source config?** first.

## Key decisions already locked

- **KJV retired as the *sole* source** — it drops ~31 % of UNV's tags and carries no
  09xxx/FHL-9000 (measured by `build_exclusion.py`). WLC carries every SN.
- **WLC is the SN source in every config**; the English/KJV layer is *only* a readability
  bridge (leak-safe — non-Chinese). The Chinese `gloss2` column is always dropped.
- **Two-stage KJV split collapsed** into one complete contest scoring the full inventory
  incl. 09xxx recall.

## Open (the survey11 build, gated on token recovery)

1. **Source-config sweep** (cheap, single-model): score BSB / YLT / BSB+YLT / BSB+YLT+KJV
   on UNV FHL truth; pick the winner; watch for survey6-style info-overload (ablation).
2. **A-vs-B contest** (expensive): run s1 vs s10 on the chosen source config, with
   **N-sample** to beat sampling noise. This is the credibility verdict (Q2).

## Harness (currently in survey10 — may migrate here)

Reused cross-dir from `../survey10_s1_but_obe_insteadOf_oneshot/`:
- `run_stage2_harsh.py` — WLC loader + `PREFIX_BRIDGE` (09xxx) + s5 `morph_bridge` (8xxx).
  ~80 % of the new contest; needs the English bridge (`eng/targets/{BSB,YLT}` +
  `eng/alignments/{BSB,YLT}/WLCM-*-manual.json`) added.
- `build_exclusion.py` — fairness diagnostic (measured KJV's 31 % gap; family partition).
- `wlc_check.py` — per-verse WLC identity signal (also the WLC-into-S1 primitive).
- `run_a2_contest.py` — the (KJV-era) contest harness; arms A/B/B0.

Data: `../Alignments/data/` (Clear Bible) — `sources/WLC.tsv`, `eng/targets/{BSB,YLT}`,
`eng/alignments/{BSB,YLT}/WLCM-{TRANS}-manual.json`.

## Relationship to neighbours

- **survey10** keeps the s10 *method* (conventions subsystem) + the gold it produces;
  survey11 only *judges* s1 vs s10, it does not own either method.
- **survey1** owns the s1 method + the authoritative gold + `FHL_DIVERGENCE_LOG.md` (the
  methodology-divergence answer-key rule the scorer must honour).
- **survey5** owns Clear Bible integration + `morph_bridge.json` (reused here).
