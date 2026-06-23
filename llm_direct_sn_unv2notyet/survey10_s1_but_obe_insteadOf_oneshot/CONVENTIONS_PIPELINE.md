# s10 Conventions Pipeline — the scribe (extract → regression-gate → version)

> The engine behind **D1-E + D3-Q3-D-batched**. `conventions.md` is s10's
> externalized, auditable cross-verse memory; this doc specifies how it is
> populated, gated, versioned, and re-injected — and the `judge.py` D-deliberation delta.
> Companion: [`SURVEY10_DESIGN.md`](SURVEY10_DESIGN.md),
> [`S10_VS_S1_GOLD_EXPERIMENT.md`](S10_VS_S1_GOLD_EXPERIMENT.md).

## Why this exists

In s1, cross-verse learning happens by **prompt evolution**: when R3 finds a
collective error, the whole prompt is bumped `+0.1` under a regression gate
(`regression.py:run_prompt_regression`). That is coarse — one whole-prompt edit
can regress many verses (cf. v1.3 → REGRESSION_FAILED on 8 verses).

s10 replaces "evolve the prompt" with "**accumulate conventions**": the same
learning, but at **per-line granularity**, each line independently gated and
revertible. `conventions.md` is the artifact; the **scribe** is the process that
grows it.

## `conventions.md` schema

A versioned, human-readable list of atomic rules. Each rule is one reviewable
unit:

```markdown
# conventions.md — v0.4   (gold corpus: Gen 1:1 – 3:13, 68 verses)

## C1  implicit object-marker binding            [added v0.1 · gate PASS · acc +3 verses]
A bare/implicit 受詞記號 (Strong 0853, often unshelled `<...0853>`) binds to the
group of the **following** noun; it is never a standalone group.
  ex: 創 1:1  {<WH0853>}天<WH08064> → 0853 joins 天's group, not its own.

## C2  per-occurrence rebinding                  [added v0.2 · gate PASS · acc +2 verses]
A Strong's number that recurs in a verse rebinds **per occurrence** to its local
noun; do not collapse repeats to a single placement.

## C3  神/上帝 lexical divergence is not a placement signal  [added v0.3 · gate PASS · acc +1]
UNV 神 vs LCC 上帝 is a systematic lexical difference; never treat it as evidence
of a different Strong's placement.
```

Each rule carries provenance metadata in its heading: **version added**,
**gate verdict**, and (post-experiment) its **measured accuracy delta** vs FHL
truth. A rule that the contest shows is *not* accuracy-positive is demoted/removed
— conventions are falsifiable, not sacred.

### Storage & versioning
- `conventions.md` is the live file (prepended to every verse prompt).
- Each accepted batch bumps the version (`v0.3 → v0.4`) and writes a snapshot to
  `conventions_history/v0.4.md` (parallels `prompts/` versioning in s1).
- A **budget cap** (e.g. ≤ 25 active rules, or ≤ ~1.5k tokens) bounds injection
  cost and forces the scribe to generalize/merge rather than hoard narrow rules.

## The scribe — per-chapter cadence (D3-Q3-D-batched)

Runs **after each chapter's verses are resolved** by `build_gold_standard()`
(never mid-chapter — the verses being learned from must already be settled gold).

```
for each completed chapter C:
  1. EXTRACT   candidate conventions from C's gold verses
  2. DEDUP     against existing conventions.md (merge/skip near-duplicates)
  3. GATE      each surviving candidate through the regression gate
  4. VERSION   append gate-PASS candidates; bump version; snapshot
  5. (contest) score each new convention vs FHL truth  → keep/demote
```

### Step 1 — EXTRACT (who & how)
A dedicated **scribe call** (not a panel leg — keeps the panel independent). The
scribe is a single LLM call (default opus, the orchestrator's own model) given:
- the chapter's resolved gold verses (UNV+SN reference, the consensus placement,
  and *why* it resolved — `resolved_at` + any R3 error notes),
- the current `conventions.md`,
- instruction: *"What new, GENERALIZABLE rule (if any) does this chapter teach
  that is not already covered? State it atomically. Cite the verse(s). If nothing
  generalizable, return none."*

Output is a list of candidate rules (often 0–2 per chapter). The bias is toward
**few, general** rules — the prompt explicitly penalizes per-verse-specific
"rules."

### Step 2 — DEDUP
Cheap similarity check (string + embedding optional) against active rules. A
candidate that restates an existing rule is dropped; one that *refines* an
existing rule becomes a proposed **edit** to that rule (which must itself pass the
gate, since editing a rule changes all verses it touches).

### Step 3 — GATE (reuse s1's regression machinery)
This is the safety core. Reuse `regression.py:run_prompt_regression`'s logic,
generalized to `run_convention_regression`:

```python
# conceptual — wraps the existing gate
def run_convention_regression(candidate_rule, conventions_before, gold_standard):
    conventions_after = conventions_before + [candidate_rule]
    # re-run a sampled set of ALREADY-RESOLVED gold verses with the new
    # conventions.md prepended; a candidate that changes any previously-correct
    # placement to a different one is a regression.
    sample = select_regression_verses(gold_standard, trigger_verses=[...])
    for v in sample:
        before = gold_standard[v].placement
        after  = rerun_verse(v, conventions_after)
        if after != before:           # changed a settled verse
            return REGRESSION_FAILED(v, before, after)
    return PASS
```

- **PASS** → the candidate is safe to add (it did not disturb any settled gold).
- **REGRESSION_FAILED** → reject the candidate, log it (same surfacing as s1's
  v1.3 block). A rejected rule is *evidence of a real tension* — logged for human
  review, not silently dropped.
- The sample uses the **same `select_regression_verses` sampler** as s1 (seeded,
  rate-based) so the gate cost is bounded.

> **Key reuse**: this is literally s1's prompt-regression gate pointed at a
> finer-grained artifact. No new trust machinery is invented — the trust model is
> identical to s1's, just per-line.

### Step 4 — VERSION
Gate-PASS candidates are appended; version bumps; snapshot to
`conventions_history/`. The new `conventions.md` is what the next chapter's verses
see.

### Step 5 — CONTEST scoring (experiment-time only)
During the s10-vs-s1 contest (`S10_VS_S1_GOLD_EXPERIMENT.md`), each new convention
is A/B scored against FHL ground truth (accuracy on held-out verses with vs
without it). The measured delta is written back into the rule's heading. A rule
with delta ≤ 0 is **demoted** — proves the gate (which only checks *non-regression*
on the training gold) is not enough; the contest is the *positive* check.

## Two distinct learning channels — do NOT conflate (the load-bearing distinction)

s1 has **three** orthogonal responses to a verse; s10 keeps all three separate:

| s1 mechanism | Cause | s10 response | Where it writes |
|---|---|---|---|
| **Trigger 1** | the *prompt/convention* is wrong (collective error) | **evolve conventions** → feed the **scribe** (extract candidate → gate → `conventions.md`) | `conventions.md` (the unified learning artifact) |
| **Trigger 2** | a *single weak model* oscillates | **model patch** (`generate_model_patch`) — **s1's existing path, kept verbatim & separate** | per-model patch file (unchanged) |
| terminal **"→ human"** | the *verse itself* is irreducibly ambiguous (prompt & models fine) | **D-deliberation** (below) | `resolved_at = d_deliberation` |

**Trigger 1 and Q3-D are the same write-path.** A Trigger-1 collective-error
correction does **not** bump a separate prompt (`+0.1`); it produces a **candidate
convention** that goes through the *same* scribe extract → regression-gate →
version pipeline as the Q3-D per-chapter digest. One feedback artifact
(`conventions.md`), one gate. This unifies what would otherwise be two learning
channels.

## The D-deliberation tier (terminal, post-C) — `judge.py` delta

D is **not** R2.5 and **not** a stability/Trigger-2 escalation. It is the
**terminal tier that replaces s1's "→ human"**, fired **only after C is
exhausted**.

### Escalation trigger — pinned to "C exhausted", NOT to stability
D fires when, and only when, the C tier (blind R2 stability + independent R3) has
failed to resolve the verse:
- **R3 returns unresolved** (no majority / collective `all_wrong`), **OR**
- a **Trigger-1 convention-evolution attempt regression-FAILS** — i.e. the panel
  tried to fix the verse by evolving a convention and the gate rejected it,
  *proving* the verse is not a prompt/convention problem but an irreducible
  placement ambiguity.

Do **not** pin D to `_stability_level in {moderate, strong}` — that is the
**Trigger-2** (weak-model) condition, a *different* failure mode with a *different*
response (model patch). Conflating them would fire deliberation on stable,
model-weak verses and would double-fire alongside the patch path. Canonical D
case: **Gen 3:11** (Trigger-1 evolution regression-failed).

### Mechanism (reuse the sealed R1 bids → reveal → hold-or-revise)
1. **Sealed bids already exist**: the independent R1 answers were collected before
   any cross-leg reveal — they ARE the sealed bids. No re-collection needed.
2. **Reveal**: orchestrator builds a deliberation prompt (adapt
   `build_r2_debate_prompt`) showing the three sealed R1 bids + current
   `conventions.md`, and asks each leg: *"These three independent answers
   disagree and neither convention-evolution nor voting resolved it. Hold or
   revise yours? Give the placement rule that decides it."*
3. **Re-collect**: each leg returns hold/revise + reasoning — the round amnesia
   cannot run (it requires reasoning about each other's placements).
4. **Resolve**: `consensus.py:build_gold_standard()` remains the **sole
   authority** — D outputs are additional data it weighs; `resolved_at =
   d_deliberation` (a second, auditable trust tier below `c_consensus`). Still
   deadlocked → **human**.

### What stays untouched
- The **C tier**: blind R2 stability (`run_r2_convergence`, `_stability_level`),
  independent R3 (`run_round3`, `tally_r3_judgments`) — **unchanged**. s10 gets s1's
  full instability signal.
- **Trigger 2** (weak-model patch, `generate_model_patch`) — **unchanged and
  separate** from D.
- `build_gold_standard()` stays the sole `resolved_at` authority.
- The only changes to Trigger 1: its *target* is now `conventions.md` via the
  scribe (not a separate prompt `+0.1`); its *measurement* is unchanged.

## Failure modes & mitigations
| Risk | Mitigation |
|---|---|
| Scribe over-extracts narrow rules → overfit + bloat | per-chapter batching + budget cap + "penalize verse-specific rules" prompt + contest demotion |
| A wrong rule passes the gate (non-regression but still wrong) | contest's *positive* FHL-truth scoring catches it (gate only checks non-regression) |
| Rule edits silently change many verses | edits go through the **same gate** as additions |
| **D conflated with Trigger-2** (fires on stable weak-model verses, double-fires with patch) | pin D strictly to "C exhausted" (R3 unresolved / Trigger-1 regression-fail); keep Trigger-2's patch path separate |
| D over-fires (cost, anchoring) | D is terminal — it only sees the *genuine-ambiguity tail* that C could not resolve; the stable majority never reaches it |
| conventions.md becomes single trust-point | per-line revertible; versioned snapshots; same gate as s1's prompt; one unified gated write-path |
