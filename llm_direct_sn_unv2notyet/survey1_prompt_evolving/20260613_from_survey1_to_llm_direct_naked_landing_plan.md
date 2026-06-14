# Landing Plan — consensus-on-naked for survey1

**from** `survey1_prompt_evolving-obe` **to** `llm_direct_sn_unv2notyet-obe`
**date** 2026-06-13 · **status** PLAN ONLY (no code touched) · **re** [`NAKED_SHELL_UPGRADE.md`](NAKED_SHELL_UPGRADE.md)

Read both mandated docs + traced all接點 in code. Plan below. **One finding changes step 1** — read §0 first.

---

## §0. Finding that revises your step 1: there are already TWO+ copies of the lookup pair, and survey9's is the *worse* one to extract

Your brief says "抽 `build_shell_lookup` + `restore_shell_lookup` 從 `survey9/run_survey9.py` 進 `shared/sn_shell.py`". But the pair already exists in **two** divergent places, and survey9's is the one with a cross-survey dependency:

| Location | build fn | restore fn | self-contained? |
|---|---|---|---|
| **main driver** `llm_direct_sn_unv2notyet.py:464/479` | `_build_shell_lookup` | `_restore_shell_lookup` | ✅ self-contained regex `\{?<W[ATG]*[HG]\d+[a-z]?>\}?` |
| **survey9** `run_survey9.py:122/145` | `build_shell_lookup` | `restore_shell_lookup` | ❌ depends on `extract_tags` ← imported from `survey4/analyze_test_dimensions.py` |
| shared `sn_shell.py` | — (absent) | — (absent; has `restore_shell_guess` + `restore_shell` only) | — |

- Both `restore_*` impls are **byte-identical** (`re.sub(r'<(\d+[a-z]?)>', …)`). No risk there.
- The `build_*` impls **differ**: survey9's calls `extract_tags` (survey4 dependency); the main driver's is a standalone regex with no cross-survey import.

**Revision**: extract the **main driver's self-contained** `_build_shell_lookup`/`_restore_shell_lookup` (drop the leading `_`) into `shared/sn_shell.py` as the canonical pair — *not* survey9's. Then point survey9, the main driver, **and** survey1 all at the shared copy. This kills the survey4→survey9 coupling instead of importing it into `shared/`.

Also already present in the main driver and reusable: `build_naked_user_prompt()` (:449) and `_trim_extra_tags()` (:488). survey1 should import these, not re-author them.

---

## §1. The三接點, concretely (files / functions / line numbers)

### A. 輸入剝殼 — `run_gold_standard.py`
- **Where**: every `build_user_prompt(unv_sn, target_text, …)` call — R1 `:306`, `:445`, `:734`; R2 convergence re-runs `:1084`, `:1102`, `:1155`.
- **Change**: under `--naked`, swap `build_user_prompt` → `build_naked_user_prompt(strip_shell(unv_sn, markers=False), …)`. Both already live in the main driver (`:449` / imported alongside the existing `build_user_prompt` import at `run_gold_standard.py:205`). Model then returns a **bare-number** `lcc_sn`.
- **Risk**: LOW. Additive import + a branch. The expensive part is that *every* model-call site must branch consistently (6 sites) — miss one and R2 mixes shelled vs naked text → false disagreement. Mitigate by wrapping in one local helper `_user_prompt(naked, unv_sn, …)` and calling that everywhere.

### B. 裸態比對 — `comparator.py` + `judge.py` (mostly confirm-only)
- `comparator.texts_match` (`:26`) normalizes whitespace and string-compares — **content-agnostic, no change needed**; naked text compares fine.
- `judge.py` R2 convergence uses `texts_match(new_text, r1_text)` (`:238`) and `texts_match(new_text, prev_text)` (`:247`) on `sn_field` values. Since the model now returns naked text into `sn_field`, these compare naked-vs-naked automatically — **no change**.
- **The one real edit**: `comparator.extract_sn_sequence` (`:16`, regex `<W[ATH]*[HG]?\d+>`) is shell-format-specific → returns `[]` on bare numbers. It feeds `summarize_disagreement` (human-readable diff + SN-presence report). Under `--naked`, route it to `shared.sn_shell.extract_bare_numbers` instead, else disagreement printouts show "0 SNs". **Cosmetic/diagnostic only — does not affect resolution**, but worth fixing so the human review report is legible.
- **Risk**: LOW. B is "confirm + one diagnostic swap," exactly as your brief predicted.

### C. fix (optional) — `shared.sn_shell.fix_pipeline`
- Apply to the **winning** naked text before restore, mirroring survey9 `run_survey9.py:406` usage (`fix_pipeline(fixed, input_tags)` then `restore_shell_lookup`). Optional for v1; coverage repair.

### D. 存檔還殼 — `consensus.build_gold_standard` (sole authority, `:34`)
- **Do NOT touch any `resolved_at` branch.** Every resolution path writes a naked string into the `lcc_sn` field at three assignment sites (unanimous `:85`, disagreed `:227`, trigger1 `:247`).
- **Cleanest decoupled edit**: add a single **post-pass loop at the end of `build_gold_standard`, just before `return`** (after all `resolved_at` logic has run): when `naked=True`, for each `gold_standard[vk]`:
  ```
  naked = gold[vk]["lcc_sn"]
  lookup = build_shell_lookup(gold[vk]["unv_sn_reference"])   # unv_sn already stored here
  gold[vk]["lcc_sn_naked"] = naked          # keep naked copy (your "裸態存一份")
  gold[vk]["lcc_sn"]       = restore_shell_lookup(naked, lookup)   # "帶殼存一份"
  ```
  This satisfies AD-1 (restore is centralized in the one authority, is *not* resolution logic, touches zero `resolved_at` branches) and your "在決定 winning_text 之後、寫檔之前" requirement exactly.
- Thread a `naked: bool` kwarg into `build_gold_standard(...)` (default `False`) from the `run_gold_standard.py` call site(s). `save_gold_standard` needs no change — it just writes the dict.
- **Risk**: MEDIUM-LOW. The post-pass is isolated, but the `naked` flag must reach `build_gold_standard` from main loop without disturbing the existing positional args (it already has `trigger1_verses`/`trigger2_verses` kwargs — append `naked=` similarly).

---

## §2. Step order (revised from your §5)

1. **Extract the canonical pair** (main driver's self-contained `_build_shell_lookup`/`_restore_shell_lookup`, plus expose `build_naked_user_prompt` reuse) into `shared/sn_shell.py` → write **round-trip fidelity test (验证①)**: batch of UNV+SN → `strip_shell(markers=False)` → `restore_shell_lookup` vs `restore_shell_guess`, diff vs original, classify errors by SN type (implicit marker / WAH prefix / 8xxx morph / zero-pad). Pin lookup≈100% vs guess error-rate **in numbers**. Zero model cost.
   - Then repoint survey9 + main driver at the shared copy (de-dup; small, mechanical, keeps behavior).
2. `run_gold_standard.py` `--naked` flag (default **off**): wire接點 A (one `_user_prompt` helper at the 6 sites) → B (confirm + `extract_sn_sequence` diagnostic swap) → thread `naked` to D.
3. `consensus.build_gold_standard` restore post-pass + `naked` kwarg.
4. Small regression: `--book 創 --chap 1 --naked --force -v`; compare **R1 unanimous rate** + R2/R3 escalation count + prompt-evolution triggers against the existing shelled 28-verse run. **Do not overwrite** `gold_standard/Gen/` (28 files) — run into a scratch `--output-dir` or compare in-memory.
5. 验证② (survey5/survey4 mirror with FHL ground truth) to confirm naked actually lifts consensus quality.

## §3. §2.1 boundary (同號異殼) — honored
`build_shell_lookup` keeps only first-occurrence shell. Plan logs same-number-different-shell nodes to a human-review list during the post-pass (cheap: detect when a number appears twice in `unv_sn_reference` with differing raw tags). guess can't do better; lookup still wins. Ref `survey9_s1_plus_s8/fix_pipeline_edge.md`.

## §4. Risk summary
| 接點 | Risk | Why |
|---|---|---|
| A 輸入剝殼 | LOW | additive; **6 call-sites must branch uniformly** (single-helper mitigation) |
| B 裸態比對 | LOW | `texts_match` content-agnostic; only `extract_sn_sequence` diagnostic swap |
| D 存檔還殼 | MED-LOW | isolated post-pass; must not perturb `resolved_at` branches or positional args |
| extraction | LOW | restore impls identical; pick self-contained build to drop survey4 dep |
| 28-verse golden | guarded | `--naked` opt-in off by default; scratch output dir for regression |

**Net**: no `resolved_at` logic touched anywhere; all change is input-strip + output-restore bracketing the untouched consensus core, exactly the decoupling the design intends.

---

## ADDENDUM — steps 1-3 IMPLEMENTED (2026-06-13)

**验证① round-trip fidelity (Gen 1, 28 golden verses), lookup vs guess:**

| metric | value |
|---|---|
| LOOKUP perfect verses | **17/28** — off-boundary **17/17 lossless** |
| GUESS perfect verses | **0/28** |
| §2.1 same-number-different-shell verses | **11/28 (39%)** |
| LOOKUP fails ONLY on §2.1 boundary | **True** (`lookup_fail ⊆ boundary`) |
| tag census | core 269 · wah_prefix 104 · morph_8xxx 90 · implicit_braced 47 · core_8xxx 19 |

**Load-bearing finding**: §2.1 is NOT a corner case — 39% of Gen 1 verses have a number
carrying two shells (e.g. `0776` as `<WH0776>` and `{<WH0776>}`; `05921` as `{<WAH05921>}`
and `<WH05921>`). First-occurrence lookup collapses these. They are now auto-flagged for
human review at save time. **Recommend (your call) a follow-up**: occurrence-aware
(positional) restore would make lookup 100% even on the boundary, since strip preserves SN
order+count — but that diverges from the main driver's production algorithm, so it must be
a deliberate, separately-tested change (NOT folded into this faithful extraction).

**What landed:**
- **Step 1**: `build_shell_lookup`/`restore_shell_lookup` canonical in `shared/sn_shell.py`
  (the main driver's self-contained pair, per §0). Main driver repointed via aliases —
  output signature **byte-identical** before/after (production unchanged). `shared/test_sn_shell_lookup.py` 5/5 green. **survey9 untouched** (constraint a).
- **Step 2**: `run_gold_standard.py --naked` (default off). Single `_user_prompt` helper +
  threaded `naked` through R1 (main loop), R2 convergence, patch-regression, R2 debate, R3.
  `comparator.extract_sn_sequence` made mode-agnostic (bare + shelled). `texts_match`
  unchanged (content-agnostic, confirmed). Judge reference (`{unv_sn}`) stripped in naked
  for debate + R3.
- **Step 3**: `consensus.build_gold_standard(naked=...)` → end-of-function post-pass
  `_restore_gold_shells` (stores `lcc_sn_naked` + shelled `lcc_sn`, logs §2.1). **Zero
  `resolved_at` branches touched** (AD-1 honored). `test_consensus_naked.py` 5/5 green.

**Deferred / not done (by your constraint b + scope):**
- Steps 4-5 (token-burning consensus regression + survey5 mirror) — awaiting Joshua.
- Trigger-only templates (feedback / self-patch / validate / prompt-evolve) still embed the
  shelled `{unv_sn}`. Low-risk, rarer paths; the naked run is itself gated behind step 4. To
  finalize alongside the step-4 validation.
- Code changes are **uncommitted** (no commit instruction given) — ready on request.
