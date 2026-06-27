# Survey5 Round-2 results — WLC-only + morph mechanism

Date: 2026-06-27 · survey5_bilingual_sn_benchmark-obe

## TL;DR

Survey5's cross-lingual SN-placement task converged on a **single original-language
source (WLC, Hebrew) + two deterministic post-steps (09xxx prefix bridge, morph
attach)**. The model does only what it's good at — place lexical tags onto UNV (99%) —
and zero-loss table work fills the rest. On Genesis 1:

| metric | Round-1 (WLC-only, lexical only) | Round-2 (+ morph attach) |
|---|---|---|
| overall coverage | 0.524 | **0.697** |
| 09xxx recall | 89% | 89% |
| **morph (8xxx) recall** | **0%** | **100% (101/101)** |

The morph table is **leave-one-out validated**: a table learned without Genesis still
recovers 100% of Gen 1's morph tags — the mapping is a universal linguistic rule, not
memorization. Total LLM cost of the whole Round-2 (table build + validation): **zero**
(the morph work is pure alignment; results reuse Round-1's saved model outputs).

## The journey

1. **Round-1 source bake-off** (`run_bakeoff.py`): KJV is a lossy SN source — on Gen 1,
   ~31% of UNV's gold tags (09xxx prefixes + function words English drops) cannot come
   from KJV. We compared, on 31 verses × opus:
   - **A** = WLC-only (Hebrew original)
   - **B** = WLC + KJV (English bridge)

   | config | cov | place | 09xxx | rock | wlc_only |
   |---|---|---|---|---|---|
   | A | 0.524 | 0.552 | 89% | 99% | 89% |
   | B | 0.547 | 0.516 | 94% | 98% | 86% |

   The English bridge was **~a wash** (within opus single-sample noise), so **WLC-only
   won**: simpler, zero build, and it recovers the 09xxx KJV structurally cannot.
   → Decision: drop the English bridge (KJV config B + the planned BSB Round-2).

2. **The remaining hole = morphology codes (8xxx).** 91 FHL verbal stem/form tags in
   Gen 1 that the WLC→FHL lexical bridge drops (>8674) and that the model placed at
   only 5% even when handed them. Decision: morph is **in-scope**, via a dedicated
   mechanism (not another source).

## The morph mechanism (learn → freeze → deterministic attach)

Two facts make it clean: morph **always** sits immediately after its verb's lexical tag
(101/101 in Gen 1), and the FHL code is a pure **stem+form** function (`vqp → 8804`,
PGN dropped). So:

- **`learn_morph_bridge.py`** — a one-time, **whole-OT, zero-LLM** sweep. Aligns FHL
  UNV+SN gold against WLC verbs by lexical Strong's number, learns
  `form_key → FHL code` (`form_key` = WLC ETCBC morph prefix, e.g. `vqp3ms → vqp`).
  Result: **115 form_keys, 62,750 verbs aligned, all 39 OT books**. Common forms are
  98–99% pure (`vqp→8804`, `vqw→8799`, `vqi→8799`, the full Qal/Niphal/Piel/Hiphil/
  Hophal/Pual/Hitpael grid); rare forms (n≤13) resolve by majority vote. Frozen to
  `morph_bridge.json`.
- **`morph.py` — `attach_morph()`** — at apply time, for each WLC verb, insert
  `<WTH{code}>` immediately after the verb's lexical tag in the model output (anchored
  on the number the model already placed). The model never sees or handles morph.
  Morph recall is bounded by lexical-verb recall.

Wired into `run_bakeoff.py`; scored by `gate.morph_recall()` + the format-agnostic
`scoring.num_score()`.

### Why learning beats hand-coding
The bridge automatically resolved ETCBC↔FHL edge cases that the partial doc table
would miss — e.g. Qal **wayyiqtol** `vqw` maps to **8799** (same as imperfect), learned
straight from 10,026 aligned examples. No hand-coding of irregulars.

### No-leak discipline
The table is a universal mapping, frozen once. Apply time uses only the frozen table +
the verse's WLC form-keys — never the scored verse's own gold morph.

## Leave-one-out validation (zero opus)

Re-learned the table from **books 2–39 (Genesis excluded)**, re-scored the saved Gen 1
outputs:

- Gen 1 form_keys missing from the Genesis-excluded table: **none** (all 14 present).
- morph recall: **101/101 = 100%** (identical to the full table).
- Genesis contributed only 1 unique form_key to the 115-key table, unused by Gen 1.

→ The 100% is generalization, not memorization.

## Final pipeline

```
WLC+SN (Hebrew, lexical+09xxx)  +  UNV (plain)
   --model-->          UNV with lexical + 09xxx tags placed   (the only graded job, 99% rock)
   --attach_morph()--> UNV+SN with morph codes glued on verbs (deterministic, frozen table)
   --score vs FHL UNV+SN gold--> cov / placement / 09xxx recall / morph recall
```

Single original-language source; the model does semantic placement; two zero-loss
deterministic layers (09xxx prefix bridge + morph attach) handle the FHL mechanics.

## Retired / out of scope

- **English bridge** — KJV (config B) and the planned BSB Round-2: retired (marginal).
- **Morph by model** — rejected (5% vs deterministic 100%).

## Components

| File | Role |
|---|---|
| `run_bakeoff.py` | Bake-off harness (configs, isolated model caller, attach, scoring, summary) |
| `wlc_bridge.py` | Re-export of s10's WLC loader (lexical + 09xxx) |
| `learn_morph_bridge.py` | Whole-OT morph-bridge learner (zero LLM) |
| `morph_bridge.json` | Frozen `form_key → FHL code` table |
| `morph.py` | `attach_morph()` deterministic morph insert |
| `gate.py` | Trust-tier labeller + `morph_recall()` |
| `scoring.py` | Format-agnostic ("naked") scoring |
| `test_gate.py` / `test_scoring.py` / `test_morph.py` | Unit tests |

## Status

**Survey5 Round-2 complete.** WLC-only + 09xxx + morph attach is the validated SN+morph
parity pipeline for OT.

### Future (separate work, not survey5)
- **Production** — apply this pipeline to no-gold targets (survey9 / LCC / RCUV).
- **New Testament** — WLC is OT-only; NT needs a Greek source (SBLGNT) + a Greek morph
  bridge (`WTG` 5xxx codes).
- **Thin-key cleanup** — fix the `vq!` form-key parsing artifact and hand-verify the
  ~32 rare low-purity forms against the FHL doc (low priority; near-zero real frequency).
