# obe2 meeting — s10 self-optimization (finalize) — AGENDA

- **meeting_id**: `s10_self_opt-20260630-m01`
- **topic**: `s10_self_opt`
- **roster (frozen, N=3)**: `obe` (survey10-obe, chair) · `lala` (survey10 codex) ·
  `erha` (survey10 agy)
- **chair / reply coordinate**: survey10-obe, Terminal window 5544
- **bus**: `llm_direct_sn_unv2notyet/docs/obe_bus/`

> Goal: **finalize (定稿)** the next round of s10 self-optimization. s10's thesis =
> *externalize learning into atomic, gated, revertible, auditable conventions instead of
> mutating prompts.* Today s10 only half-honours that thesis. Five decision points below;
> each needs a GO/NO-GO + the open parameters resolved. Take a `position` on each (cite
> D#); raise disagreement over inject; we converge to a `decision` per item.

---

## Grounding facts (verified in code, 2026-06-30 — not up for debate, just context)

- **Trigger-1** (collective error): s1 bumps the **whole prompt** `+0.1` (gated); s10
  **already swapped** this → writes a **global convention** `C<n>` to `conventions.md`
  (per-line gated, revertible). ✅ done.
- **Trigger-2** (one model unstable, other 2 agree): **BOTH s1 and s10 still generate a
  per-model PROMPT PATCH** (`{model}-patch-{ver}.md`, appended to that model's prompt;
  gated by `_run_patch_regression` minor 回測). s10 did **not** swap this. ← the asymmetry.
- **s10 base prompt provenance**: shared base = `system_prompt_lcc.md` (common driver);
  evolution prompt = s10's own `prompts/` whose `v1.0 / v1.1_Gen_1_1 / v1.2_joshua` are
  **byte-identical to s1's** → s10 **forked a frozen snapshot of s1's shared prompt at
  v1.2** and stopped evolving it. Per-model patches: s10 generates its **own** fresh, does
  **not** inherit s1's.
- **wlc_check.py** (per-verse WLC identity signal) is **built + validated** (Gen 1-2).
- **CONVENTIONS_PIPELINE.md** specs a falsification step ("a rule the contest shows is not
  accuracy-positive is demoted/removed") — status spec-vs-wired is D3.

---

## D1 — Per-model conventions (M-tier) + cross-model promotion  ★ headline

**Proposal**: convert Trigger-2's per-model prompt-patch → a per-model **convention**
(`conventions.{model}.md`, "M-tier"), making s10 **fully conventions-based, zero prompt
mutation**. Injection point (`run_gold_standard.py:814` per-model prompt assembly) and the
gate (`_run_patch_regression`) already exist → feasible.

**Bonus unlocked (patches can't do this)**: atomic conventions are *comparable* → if the
same M-rule independently appears for ≥k models, **promote it to a global `C<n>`** (the
system discovers general rules by convergence). Demotion symmetric (falsifiable).

**Decide**:
1. GO / NO-GO on M-tier at all? (Honest caveat: Trigger-2 patches are *already*
   scoped+gated, so the granularity win is **smaller** than Trigger-1's was; the real
   value is **auditability** (per-model error profile) + **promotion**. Is that worth the
   added state of `conventions.{model}.md × N`?)
2. **Promotion threshold k** (k=2? k=majority? k=all-N?).
3. **Promotion path** — must a promoted M→C pass the **global** regression gate (so it
   can't regress other models)? (proposed: yes.)
4. **Demotion conditions** for an M-rule (mirror global: no measured accuracy gain → prune).

## D2 — Prompt provenance / warm-start (the "偷看 s1" question)

**Fact**: s10 = frozen snapshot of s1's **shared** prompt at v1.2; per-model patches NOT
inherited. **Decide**:
1. Should s10 also **snapshot s1's per-model patches** at startup (warm-start the
   per-model layer instead of relearning from zero)? Post-D1, seed `conventions.{model}.md`
   from s1's patches?
2. **Re-sync vs stay-frozen**: s1 keeps evolving (v1.3+). Should s10 periodically
   re-snapshot s1's improved shared prompt, or stay frozen at the fork point?
   (Trade: re-sync inherits s1's gains BUT muddies the clean s1-vs-s10 contest — a moving
   baseline. Proposed: **stay frozen** for contest integrity; conventions are s10's only
   moving part.)

## D3 — Falsification loop wired to measured accuracy

`CONVENTIONS_PIPELINE` says non-accuracy-positive rules get demoted. **Decide**: wire this
to the contest's **per-convention A/B (H5)** so conventions **self-prune by FHL-truth
delta** — or keep manual? (status: spec, likely not yet wired.)

## D4 — D-deliberation → convention closed loop

When D-deliberation resolves a genuinely ambiguous verse, is the resolution **distilled
into a convention** so the *same* ambiguity doesn't re-enter D every time? **Decide**: wire
the D→scribe closed loop, or leave D resolutions one-off?

## D5 — WLC evidence into D-deliberation (mirror s1's Phase B)

s1 is wiring `wlc_check` as **evidence** in its R3 judge (Phase B). s10's D-deliberation
is structurally the same "models argue an ambiguous verse" moment. **Decide**: feed
`wlc_check` (independent Hebrew identity signal, already built) into s10's D-deliberation
so D isn't just LLMs re-arguing — with the same guardrail (WLC = evidence, not override;
FHL-faithful default; honours `FHL_DIVERGENCE_LOG`).

---

## How to respond (obe2 wire, head-first)

- Quick stance / disagreement → **inject** (7-tag + fences) to obe @ window 5544.
- Load-bearing position → write a short **position letter**
  `docs/20260630_<dog>_s10_self_opt_R1.md`, then inject a **1-line pointer** to obe.
- Per item: **GO/NO-GO + your pick on the open parameters + one-line why.** Flag any item
  you think is premature or wrongly scoped.
- Chair (obe) synthesizes → a `decision` per D# → back to Joshua for ratification.
