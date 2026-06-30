# obe2 DECISION (chair synthesis) — s10 self-optimization

- **meeting_id**: `s10_self_opt-20260630-m01` · roster obe/lala/erha (N=3)
- **inputs**: lala R1 (`20260630_lala_s10_self_opt_R1.md`), erha R1 (`20260630_erha_s10_self_opt_R1.md`)
- **status**: 🔒 **LOCKED 2026-07-01** — chair-synthesized, both dogs endorsed (lala [ACK] +
  erha [ACK], no objections), Joshua ratified. D1–D5 + D2-X final. Build spec folded into
  `../survey10_s1_but_obe_insteadOf_oneshot/CONVENTIONS_PIPELINE.md`; build gated on token recovery.

**Result: 4/5 unanimous GO; D2 had the one split (warm-start), reconciled below.**
Closed design = **frozen prompt, zero prompt mutation, all learning in atomic gated
conventions — global + per-model — with measured falsification and WLC evidence in D.**

---

## D1 — Per-model conventions (M-tier) + cross-model promotion — ✅ GO (unanimous)
- Convert Trigger-2's per-model prompt-patch → `conventions.{model}.md` ("M-tier").
  s10 becomes **fully conventions-based, zero prompt mutation.**
- **Promotion threshold**: `k = roster majority` (k=2 at N=3). Same M-rule independently
  appearing in ≥k models → promote to global `C<n>`.
- **Promotion path**: M→C **must pass the global regression gate** (cannot regress the
  non-promoting model). [both]
- **Demotion**: symmetric + automated — measure the M-rule against **that model's own
  FHL-truth delta** first; prune when delta is neutral/negative after the support window.

## D2 — Prompt provenance / warm-start — ✅ GO (freeze) + 🔀 RECONCILED (the only split)
- **Shared prompt STAYS FROZEN at v1.2** — no re-sync of s1's evolving prompt. (both agree;
  contest hygiene — a stable baseline so measured gains belong to s10's conventions.)
- **Warm-start split**: lala = NO active inheritance (import s1 patches only as *inactive*
  candidates); erha = GO warm-start (seed from s1 patches for a head start).
- **Chair reconciliation (gives both what they asked)**: **import s1's per-model patches
  converted to M-tier candidate format but INACTIVE — each must pass the SAME convention
  gate (regression + FHL-truth delta) before activation.** → erha's head-start (candidates
  pre-staged, no relearn from zero) + lala's hygiene (nothing pre-enabled; every M-rule,
  s1-derived included, earns activation against FHL truth). No pre-enabled inheritance.

### D2-X — Re-sync safeguard (added 2026-06-30, Joshua — "I'll likely re-sync on a whim, often")

The freeze decision protects the *automated* pipeline, but does NOT stop a human manually
copying s1's latest prompt into s10. Joshua flagged he will likely do this often. Damage if
done as a silent file-copy: corpus provenance fragments (Gen 1-2 under v1.2 vintage vs Gen 3+
under the new prompt — and `--force` would regenerate & possibly *change* completed verses);
every convention's gate verdict is invalidated (they were regression-gated against v1.2);
D3's falsification baseline starts moving (deltas measured against a shifting prompt = noise);
and the s1-vs-s10 contest attribution collapses (s10's gains become "conventions + inherited
s1 prompt", unattributable).

**Therefore a manual re-sync is NEVER a silent copy — it is a first-class, versioned event
that MUST do all three atomically:**
1. **Auto-snapshot** the current state (gold + `conventions*.md` + baseline version) before
   touching anything → the clean frozen experiment is preserved. **The contest always pins a
   frozen baseline snapshot**, so re-syncs can never move the measured arm.
2. **Bump the baseline version** (`v1.2 → v1.4-synced`) and **provenance-tag every gold file**
   with the baseline that produced it → no silent mixed-vintage corpus.
3. **Re-run the full convention regression against the new prompt** → auto-quarantine any
   convention that no longer passes (was gated against the old baseline).

Effect: re-sync as many times as wanted → each yields a provenance-tagged, snapshotted,
re-gated *variant*; the frozen contest arm stays intact. Whim becomes a **controlled fork**,
never silent corruption. (Completed verses are untouched unless `--force`; the real risk is
forward mixed-provenance + stale conventions, which 1–3 neutralise.)

## D3 — Falsification loop wired to measured accuracy — ✅ GO (unanimous, automated)
- Wire convention falsification to **per-convention A/B using FHL-truth delta (H5)**.
- **Automated** quarantine/demotion for neutral/negative deltas; **manual override only for
  explicitly documented theological / text-critical exceptions** (lala's guardrail).

## D4 — D-deliberation → convention closed loop — ✅ GO (unanimous, gated)
- D outcomes produce **candidate conventions ONLY when the resolution exposes a
  reusable/general rule** — never verse-specific hardcoding (both stressed this).
- Candidate must pass the **standard convention gate** before activation.
- Store the **originating D case as provenance** so later regressions cite the source.

## D5 — WLC evidence into D-deliberation — ✅ GO (unanimous)
- Feed `wlc_check` (built + validated) into D-deliberation as **independent evidence, not
  an override**. Preserve **FHL-faithful default**; route real WLC/FHL tensions through
  `FHL_DIVERGENCE_LOG`. (Mirrors s1's Phase B guardrail.)

---

## Build order (when greenlit; token-hold aware)
1. **D1 + D2 (+ D2-X)** together (they share the M-tier representation + the gate): add
   `conventions.{model}.md`, teach `build_conventions_preamble(model=...)`, route Trigger-2
   to the scribe, wire promotion (k-majority → global gate) + demotion; stage s1 patches as
   inactive M-candidates. **D2-X**: build the versioned re-sync op (auto-snapshot + baseline
   bump + provenance-tag + convention re-gate) + pin a frozen baseline snapshot for the contest.
2. **D3**: wire per-convention A/B (H5) → auto quarantine/demote on FHL-truth delta.
3. **D4**: D→scribe candidate path (reusable-only) + provenance.
4. **D5**: `wlc_check` into the D-deliberation prompt as evidence.

Lands in `CONVENTIONS_PIPELINE.md` (the M-tier + promotion + falsification spec) once ratified.
