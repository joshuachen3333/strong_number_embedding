# s10 vs s1 — the gold contest, judged by FHL ground truth

> Settles empirically the open question from s10 `prompt.history`
> (*"作為黃金標準 S1 比較好還是 S10?"*). Companion:
> [`SURVEY10_DESIGN.md`](../survey10_s1_but_obe_insteadOf_oneshot/SURVEY10_DESIGN.md),
> [`CONVENTIONS_PIPELINE.md`](../survey10_s1_but_obe_insteadOf_oneshot/CONVENTIONS_PIPELINE.md).

## 🏛️ Cornerstone source — LOCKED (Joshua 2026-07-11)

**Whole-canon base = macula-hebrew / WLC (OT, books 01–39) + macula-greek / SBLGNT
(NT, books 40–66); the BSB English bridge spans both testaments.**

- **OT** — `Alignments/data/sources/WLC.tsv` (macula-hebrew: strongs `H0871a`, morph, lemma).
  NB our SN extractor consumes **WLC.tsv**, not `WLCM.tsv` (WLCM's schema — no lemma,
  `H`-less strongs, full-word pos — breaks `_bridge_number`; WLC/WLCM share ids ~99.3%).
- **NT** — `Alignments/data/sources/SBLGNT.tsv` (macula-greek: strongs `G0976`, Robinson/
  MorphGNT morph `N-NSF`). Bridge: `SBLGNT-BSB-manual.json`.
- **Bridge** — **NONE by default (WLC-only)** as of the Gen 1 result below: the bare
  original+SN source scored best; BSB *hurt* placement and 09xxx recall, so the readable
  English gloss is retired to an **optional** experiment (`--eng-source {none(default),BSB,YLT}`).

Implemented end-to-end 2026-07-11: OT (WLC) + NT (SBLGNT/BGNT selectable + macula-greek, built
via /workflows). Selectable dims: OT `WLC.tsv` · NT `--nt-source {SBLGNT,BGNT}` · bridge
`--eng-source {none (default),BSB,YLT}`. **Default source = WLC-only** (Joshua 2026-07-11,
per the Gen 1 contest).

### Source files we use (`Alignments/data/sources/`) — recorded 2026-07-11

| 檔案 | 是什麼 | strongs 格式 | 我們用嗎 |
|---|---|---|---|
| `WLC.tsv` | OT 希伯來(馬所拉/列寧格勒) | `H0871a` + lemma | ✅ 用這個 |
| `SBLGNT.tsv` | NT 希臘(**批判** / 亞歷山大系,≈NA/UBS) | `G0976` + lemma | ✅ NT 預設 |
| `BGNT.tsv` | NT 希臘(**拜占庭** / 公認經文家族代理) | `G0976` + lemma | ✅ `--nt-source BGNT` |

NOT used: `WLCM.tsv`/`WLCM+required.tsv` (schema breaks `_bridge_number`: no lemma, `H`-less
strongs, full-word pos), `SBLGNT+required.tsv`. **TR (公認經文) is NOT local** — Byzantine
family, KJV's base; BGNT is our proxy (BGNT ≠ literal TR: no Comma Johanneum). Family tree:
Alexandrian/critical WH→NA/UBS→**SBLGNT**; Byzantine **BGNT**(modern majority)+ TR(early
printed)→KJV. Alignments: BSB has `WLCM-BSB`(OT)/`SBLGNT-BSB`/`BGNT-BSB`(NT); YLT has
`WLC-YLT`(OT)/`SBLGNT-YLT` (Clear Bible's own naming is inconsistent — both OT files align to
`WLC.tsv`).

**Literal-TR sources (GitHub, for the backlog — blocked on a missing TR-BSB alignment):** the
`byztxt` org (Robinson / Sandborg-Petersen — likely our BGNT's own ecosystem) is the home.

| Repo | 內容 | 適用 |
|---|---|---|
| [byztxt/greektext-textus-receptus](https://github.com/byztxt/greektext-textus-receptus) | TR + 形態解析 + Strong's | ⭐ 要的就是這個 |
| [byztxt/greektext-elzevir](https://github.com/byztxt/greektext-elzevir) | Elzevir TR + morph + Strong's | 另一版 TR |
| [byztxt/greektext-scrivener](https://github.com/byztxt/greektext-scrivener) | Scrivener 1894 TR(純文本,無 Strong's) | 純底本 |
| [STEPBible/STEPBible-Data](https://github.com/STEPBible/STEPBible-Data) | TAGNT:Strong's+morph+TR/Byz/critical 標記,CC-BY | 綜合、含變異標記 |
| [Center-for-New-Testament-Restoration/KJTR](https://github.com/Center-for-New-Testament-Restoration/KJTR) | KJV Textus Receptus | KJV 對應版 |

Org home: [github.com/byztxt](https://github.com/byztxt) — multiple Byzantine + TR editions,
public domain.

## 📊 First contest run — Gen 1, opus, WLC+BSB (2026-07-11)

`run_a2_wlc_eng.py --book 創 --chap 1 --arms B,B0,B_noeng --model opus` (31 verses, 0 drops,
clean quota). PAIRED deltas (same-verse only), full_frac vs UNV FHL truth:

| Factor | delta | reading |
|---|---|---|
| **s10 conventions** Δ(B − B0) | **−0.0014** (n=31, FINAL) | **neutral / zero** — conventions.md at C1, no measured lift (matches the scribe's fruitless-回測 observation) |
| **BSB bridge** Δ(B − B_noeng) | **−0.0227** (n=31, FINAL) | **HARMFUL** — WLC-only *beats* WLC+BSB on BOTH metrics |

Final arm means (n=31): `B` (WLC+BSB, conv ON) full=0.774 09xxx=0.935 · `B0` (WLC+BSB, conv
OFF) full=0.775 09xxx=0.887 · **`B_noeng` (WLC-only) full=0.797 09xxx=0.984** ← best on both.
So on Gen 1 the bare WLC+SN source is the *strongest*; adding the BSB gloss costs both full
placement and 09xxx-prefix recall.

**Contrast with the earlier YLT probe** (Gen 1, opus): YLT bridge Δ = **+0.0385** (n=24) —
*helpful*. So the two English bridges point OPPOSITE ways:

| bridge | Δ | why (hypothesis) |
|---|---|---|
| **YLT** (literal, tracks Hebrew word order) | **+0.039** helps | per-morpheme gloss aligns with WHERE the SN goes |
| **BSB** (natural, readable English) | **−0.021** hurts | natural word-order diverges from Hebrew → gloss misleads placement |

**Implication:** the objective SN-placement score **challenges the BSB pivot and vindicates the
original YLT choice.** A readable-but-word-order-misaligned bridge actively costs placement
accuracy — the survey6 "info-overload" / bridge-quality lesson, measured.

**Caveat (not yet apples-to-apples):** YLT and BSB deltas come from *different runs* (different
verse subsets, single-model single-sample). Direction is clear (+0.039 vs −0.021) but a rigorous
confirmation needs a **single run with both bridges as arms** (WLC+YLT vs WLC+BSB vs WLC-only).
→ recommended next step.

## s10's identity — founding intent vs current reality (2026-06-30)

Read this before assuming what s10 *is*. The name is now a fossil.

**Founding intent.** `s10 = s1_but_obe_insteadOf_oneshot` — do s1's gold task, but via
**live, injectable CLI sessions** (lala=codex, erha=agy) **instead of** s1's stateless
`oneshot` API calls. The point was that a *live session carries context across verses*,
so the model would **accumulate learned conventions chapter-by-chapter** like a scribe
who gets fluent as it copies. "How lala/erha reuse context" was the whole raison d'être.

**What actually happened — the intent was overturned by its own discovery.** The
**per-call `/clear` blindness** finding (each call must start blank to prevent
answer-leak / cross-verse contamination) collapsed the premise: blind-live ≡ headless
in quality, so there is no quality reason to keep the live session. s10 went **fully
headless** (`cli_caller.LIVE_WINDOWS = {}`). Fully headless = **no session
context-carry at all** — lala/erha have no cross-verse memory.

**So s10's context-reuse mechanism migrated from session-memory → an externalized
file.** Cross-verse learning now lives in [`conventions.md`](../survey10_s1_but_obe_insteadOf_oneshot/conventions.md): a
disk-resident, **regression-gated**, scribe-distilled ledger (one atomic `## C<n>` rule
per heading, gate-PASS provenance) that is **re-injected into every blind call** as a
preamble. Context isn't *carried*; it's *externalized and re-fed*.

**Consequence — s10 and s1 have converged more than the name implies.** Both are now
**blind per-call** and both **externalize accumulated learning to disk and re-feed it**.
The original differentiator (live context-carry) is gone.

**⚠️ Same model count — NOT single-vs-multi.** Both s10 and s1 run the **same 3-model
consensus** (`run_gold_standard.py`: opus / agy / gpt panel; R1 unanimous → R2 debate →
R3 judge; shared `consensus.py`). A natural-but-wrong simplification is to call s10
"single model" — that comes from the **A2 contest probe** (`run_a2_contest.py`,
`run_stage2_harsh.py`), which deliberately runs **one model** (opus, arm B vs B0) to
*isolate the conventions effect*. That single-model setup is the **measurement
instrument**, not s10's gold method. s10's gold production is 3-model, same cost base
as s1.

**The genuine remaining difference is ONE added subsystem — `s10 ⊇ s1`:**

| | s1 | s10 |
|---|---|---|
| **Model panel** | 3-model consensus (R1→R2→R3) | **same** 3-model consensus (R1→R2→R3) |
| **Externalized learning** | mutate the **instruction prompt** | **swaps ONE path** (see Trigger table) + adds the conventions subsystem |
| **s10-only machinery** | — | `conventions.md` **C/D ledger** (atomic gate-PASS rules, prepended to every leg's R1/R2/R3 prompt) + the **scribe** (distils resolved gold → conventions) + **regression gate** (Trigger-1 write-path) + **D-deliberation** (escalation for genuinely ambiguous verses) |

**Precisely which learning path s10 swaps — it swaps only Trigger-1.** Both pipelines
escalate a verse two ways; s10 replaces the *collective-error* path with conventions
and leaves the *per-model* path byte-for-byte identical to s1
(`run_gold_standard.py`: *"Trigger-2's model-patch path is untouched"*):

| Trigger | Fires when | s1 does | s10 does |
|---|---|---|---|
| **Trigger-1** | collective error (all 3 models unstable in R2 / R3 declares collective error) | bump the **whole instruction prompt** `+0.1` under a regression gate | **SWAPPED → write a CONVENTION** (per-line, independently gated, revertible); if no candidate passes the gate → **D-deliberation**; run continues (no break, no human prompt-fix) |
| **Trigger-2** | one model unstable, the other 2 agree (distance ≥ threshold, AD-2) | generate a **model-specific prompt patch** (`{model}-patch-{ver}`) | **IDENTICAL — untouched.** same per-model patch path |

So the headline "s1 iterates prompts, s10 iterates conventions" is true **only for the
collective-error (Trigger-1) path**. The per-model patch (Trigger-2) is **shared,
unchanged** — both still patch individual models. **Why swap Trigger-1**: a whole-prompt
`+0.1` bump is coarse — one global edit can regress many already-settled verses (real
case: `v1.3 → REGRESSION_FAILED` on 8 verses). Conventions deliver the *same* cross-verse
learning at **per-line granularity** — each rule independently gated against the settled
corpus and individually revertible (see [`CONVENTIONS_PIPELINE.md`](../survey10_s1_but_obe_insteadOf_oneshot/CONVENTIONS_PIPELINE.md)).

Infrastructure/truth-source layer is shared bidirectionally (WLC tooling
[`wlc_check.py`](../survey10_s1_but_obe_insteadOf_oneshot/wlc_check.py)/`eval_gold_vs_wlc.py` + `FHL_DIVERGENCE_LOG` + trust
tiers + buckets flowed s10→s1; s10 reads s1's gold as baseline). What still
distinguishes s10 is therefore **purely the added conventions subsystem** — same panel,
same per-call blindness, same cost base. s10's bet (Q2): does that extra scribe+ledger+
gate machinery produce **better gold** and/or **fewer escalations over time** (H4
"cheaper over time"), earning its keep? Still only answered by a B-vs-B0 proxy — the
head-on **A-vs-B** contest below is unrun. That contest is the final exam for s10's
reason to exist.

## The measurement problem (and the trick)

The production gold task is **UNV → LCC**, but **LCC has no FHL Strong's truth**,
so a UNV→LCC gold can only be judged by *consensus*, not against an answer key —
which is circular for comparing two consensus methods.

**Trick (borrowed from survey5):** run the contest on a task where ground truth
**does** exist — project onto **UNV** (which has FHL tags) **from a different
annotated source** so the answer is never shown:
1. **Source = WLC + aligned English** (WLC carries *every* FHL SN incl. the 09xxx
   prefixes; BSB/YLT give a readable English bridge — *not* the answer).
   **⚡ Updated 2026-06-30 — this supersedes the original `KJV+SN` source; see
   [§ Source pivot](#-source-pivot-2026-06-30--decouple-from-kjv--wlc--aligned-english)
   immediately below for why KJV was retired.**
2. **Target = UNV stripped** of its SN (`strip_shell`).
3. Have each method (**s1** and **s10**) project the Strong's numbers
   cross-lingually source→UNV.
4. Score each method's UNV output against UNV's **original FHL tags** with
   `survey4/auto_score.py:score_verse` → objective `{exact, coverage, placement,
   format}` per verse.

The method whose UNV output matches FHL truth more often is the better gold
producer — no consensus circularity, and (critically) **no answer leak**: the
projection source is WLC+English (non-Chinese), not the UNV answer. See **A2** below
for the leak trap this avoids (a naive "strip UNV → re-place onto UNV" hands the
model its own answer via the projection source + the system-prompt worked examples).

## ⚡ Source pivot (2026-06-30): decouple from KJV → WLC + aligned English

> Joshua, 2026-06-30. **The contest's job is unchanged — settle "s1 or s10 produces
> better gold" objectively. What changes is the *source*: retire KJV, adopt WLC + its
> aligned English translations.** This supersedes the KJV-based two-stage design that
> follows (kept below as rationale + the evidence that motivated this pivot).

**Why KJV had to go — it is a structurally crippled source.** KJV is English, and
English cannot express Hebrew inseparable prefixes / many function words, so KJV's FHL
annotation **drops ~31 % of UNV's tags** (measured: [Stage-1](#-stage-1-empirical-result-build_exclusionpy-2026-06-25--run-before-any-paid-contest)
below, Gen 1: 183/592 UNV tags KJV-unsupplyable) — and it carries **none** of the
09xxx prefixes (FHL 9000-range). A contest run on KJV can therefore only score a
*subset* of the real task, and needs an awkward two-stage workaround to ever touch the
09xxx tail.

**Why WLC + English is strictly better.** WLC (Clear Bible's manual Hebrew alignment)
carries **every** SN — content words, `0853` את, function words, **and** the 09xxx
prefixes (bridged to FHL by lemma, `run_stage2_harsh.PREFIX_BRIDGE`; verbs' 8xxx morph
via survey5's `morph_bridge.json`). The catch — WLC is Hebrew, unreadable to the
projection model — is solved by the **aligned English translation** that replaces KJV's
old readability role **without** KJV's SN loss:

- **Verified available**: Clear Bible ships **two** English translations word-aligned
  to WLC, both with `WLCM-{TRANS}-manual.json` manual alignments —
  **BSB** (Berean Standard, modern/readable) and **YLT** (Young's Literal, tracks
  Hebrew morphology closely, may surface more prefixes). `eng/targets/{BSB,YLT}` +
  `eng/alignments/{BSB,YLT}`.
- **Leak-safe**: the English is *not Chinese* → it cannot hand over "which Chinese
  token". (The `gloss2` Chinese column stays dropped, as before.)

**The big structural win — the two-stage split collapses into ONE complete contest.**
The only reason Stage-1/Stage-2 existed was KJV's incompleteness (Stage-1 *excluded*
09xxx because KJV can't supply them; Stage-2 *added them back* via WLC). With WLC as the
source, **the full inventory is supplied at once** → a single unified contest scoring
**everything incl. 09xxx recall**. No `kept_set` exclusion.

| | OLD (KJV, two-stage) | NEW (WLC+English, unified) |
|---|---|---|
| Source | KJV+SN (English, drops 31 %) | **WLC** (complete) **+ BSB/YLT** (readable bridge) |
| 09xxx / FHL-9000 | KJV can't supply → Stage-1 excludes, Stage-2 re-adds | **supplied natively**, scored in one pass (09xxx recall) |
| Stages | 2 (workaround) | **1 (complete)** |
| Scoring boundary | `kept_set` = UNV-FHL ∩ KJV-FHL | **full UNV-FHL inventory** |

**Roles of the existing artifacts after the pivot** (nothing wasted):
- `build_exclusion.py` / `kept_set_*.json` → no longer the *scoring boundary*; becomes
  the **fairness diagnostic** that *measured* KJV's 31 % gap (the evidence for this
  pivot) and still partitions tags into families for analysis.
- `run_stage2_harsh.py` (WLC loader + `PREFIX_BRIDGE` + `morph_bridge`) → promoted from
  "harsh tail probe" to **THE contest source loader**; needs the **English bridge**
  added.
- The [WLC answer-key methodology-divergence rule](#️-wlc-answer-key--methodology-divergence-rule-s1-gold-ruling-2026-06-29)
  still applies — FHL-faithful tags that differ from WLC morphology are **not** scored
  as errors (2:20 lesson).

**Two subtleties to keep honest:**
1. **09xxx is a *sparse-selection* problem (feature, not bug).** WLC carries **every**
   Hebrew prefix, but UNV tags 09xxx **only where a Chinese token surfaces**. So the
   model must place the *subset* UNV would tag — that selection IS the genuine
   difficulty, measured directly by **09xxx recall**. KJV couldn't even pose this.
2. **English-overload risk (survey6 lesson).** survey6 died of info-overload (+7pp
   placement, −10pp coverage) from a 5-input prompt. Adding English to the WLC source is
   +1 input → **test, don't assume**: run **BSB-on vs off** (and **BSB vs YLT**) as an
   ablation to confirm English *aids readability* rather than *drowns* the signal.

**Build status**: `run_stage2_harsh.py` is ~80 % of the new contest already. Remaining
(the **paid** arm, gated on token recovery): (a) load `eng/targets` + `WLCM-eng`
alignment and attach per-token English to the WLC source line; (b) promote to the
primary contest; (c) wire real **A (s1 consensus) vs B (s10)** arms + **N-sample** to
beat sampling noise.

## 🔀 ~~OPEN QUESTION~~ → RESOLVED: **WLC + BSB** (Joshua 2026-07-11, revised same day)

**Decision: base source config = WLC + BSB.** (First picked WLC+YLT; revised to WLC+BSB the
same day — BSB is now the DEFAULT; YLT stays a selectable option, not expected to be used.)
WLC always supplies the SN inventory incl. 09xxx; BSB (Berean Standard Bible, modern readable)
is the readable bridge that disambiguates which Chinese word each tag belongs to.

**Implementation** 2026-07-11 in `../survey10_s1_but_obe_insteadOf_oneshot/`:
`english_bridge.py` — a **parameterized** WLC↔English bridge (config-driven, `SOURCES` for
BSB + YLT; Clear Bible manual `WLCM-BSB-manual.json` / `WLC-YLT-manual.json` alignment →
per-morpheme gloss + full verse) + `run_a2_wlc_eng.py` (`--eng-source BSB` **default**, YLT
optional; arms B / B0 / B_noeng, PAIRED deltas on UNV FHL truth). Parameterized precisely
because the base source is revisable — swapping bridges needs no new code.

**Empirical note (superseded YLT probe, Gen 1, opus, partial run):** the literal-bridge YLT
probe measured paired Δ(B − B_noeng) = **+0.0385 over n=24** — i.e. a literal English gloss
*does* help placement (WLC+YLT 0.792 vs WLC-only 0.753). This validates the general
"readable English bridge helps" premise; BSB is now the chosen bridge for the base. The
conventions delta from that run was unusable (B0 quota-starved, n=4) — pending a fresh-quota
re-run on the BSB base.

The four-config table below is kept as the rationale record.

The pivot settles "WLC instead of KJV", but **which readable bridge** rides along with
WLC *was* left open — the question this survey (survey11) existed to answer. **WLC supplies
the SN inventory in every config; the variable is the English/KJV bridge layered on for
readability.** Four candidate configs (YLT chosen):

| Config | Source line per WLC token | Hypothesis it tests |
|---|---|---|
| **BSB** | `hebrew<FHLnum> [BSB word]` | modern/readable English is enough bridge; minimal tokens, lowest overload risk |
| **YLT** | `hebrew<FHLnum> [YLT word]` | a *literal* translation tracks Hebrew morphology closer → **surfaces more prefixes/particles**, maybe better 09xxx selection |
| **BSB + YLT** | `hebrew<FHLnum> [BSB / YLT]` | two glosses = redundancy/disambiguation; does more readable signal help, or start to overload? |
| **BSB + YLT + KJV** | `… + KJV English+its-own-SN` | KJV adds a *second annotated* English (its own FHL tags) as corroboration — accepting KJV's 31 % drop as additive-only, never subtractive |

**Selection axis** (scored exactly like the contest, on UNV FHL truth): which config
maximises **placement / coverage / 09xxx recall** *without* tipping into **survey6-style
info-overload** (survey6: +7pp placement but −10pp coverage from too many inputs). So the
config sweep is itself an **ablation** — more English is not automatically better.

**Method note**: run the **same** model (single-model, like the B-vs-B0 probe) across all
four configs first to pick the source winner *cheaply*; only then run the expensive
A-vs-B (s1-vs-s10) contest on the chosen config. (Decouples "best source" from "best
method" so the two questions don't confound each other.)

**Status**: open — no config run yet. Harness + this sweep are the survey11 build, gated
on token recovery. The harness primitives currently live in
[`../survey10_s1_but_obe_insteadOf_oneshot/`](../survey10_s1_but_obe_insteadOf_oneshot/)
(`run_stage2_harsh.py` WLC loader, `build_exclusion.py` family diagnostic,
`wlc_check.py` identity signal); they may migrate into survey11 when the contest moves
here in full.

## Two comparison flavors — A1 vs A2 (read before running any contest)

"Run s1 on the same verses and compare" can mean two very different things. They
answer different questions and only one yields an objective score, because the
production gold we already have (Gen 1) is **UNV→LCC and LCC has no FHL truth**.

### A1 — direct method diff (same UNV→LCC verses, NO objective truth)
- **What**: run `../survey1_prompt_evolving/run_gold_standard.py` on the *same*
  UNV→LCC verses we already did in s10, producing **s1's gold**; then **diff
  s1-gold vs s10-gold** verse by verse.
- **Answers**: *where* the two methods place differently — e.g. did s10's
  convention C1 make it agree/disagree with s1 on verb-morphology verses.
- **Cannot answer**: *who is right.* LCC has no FHL answer key, so this is
  similarity-only ("do they match?"), not accuracy.
- **Cost**: low-ish. s1 is headless one-shot (faster per call than s10's live
  panel) but still runs full R1→R2→R3 consensus over 31 verses on 3 accounts.
- **Use as**: a cheap warm-up / sanity diff, NOT a credibility verdict.

### A2 — objective contest (HAS FHL truth) ★

> ⚠️ **ANSWER-LEAK TRAP (Joshua, 2026-06-25) — read first.** s1/s10 are
> **projection** engines: `_user_prompt(unv_sn, target, …)` feeds an annotated
> **source** (text *with* SN) to project *from*, and the system prompt embeds
> **UNV+SN worked examples**. So the *naive* "strip UNV, ask to re-place onto
> UNV" leaks: if the target is UNV, the projection source (UNV+SN) and the
> system-prompt examples literally **contain the answer** → the model just copies
> the reference. A2 MUST NOT hand the model an annotated copy of the test text.

- **Leak-free design (survey5 framing — source ≠ answer; post-[pivot](#-source-pivot-2026-06-30--decouple-from-kjv--wlc--aligned-english) 2026-06-30):**
  - **Source = WLC + aligned English (BSB/YLT)** — WLC carries every FHL SN incl.
    09xxx; the English is a readable bridge, *non-Chinese* so it is *not* the answer
    being scored. *(was `KJV+SN` before the pivot.)*
  - **Target = UNV stripped** (SN removed).
  - Both s1 and s10 **project the source's SN cross-lingually onto UNV**.
  - **Score the projected UNV-SN against UNV's original FHL tags** with
    `survey4/auto_score.py:score_verse` — now on the **full inventory incl. 09xxx
    recall** (no `kept_set` exclusion). The answer never enters the prompt.
- **Worked-example audit (second leak vector):** the prompt's
  *"Worked examples"* must contain **no verse in the test set** (use held-out
  examples, or strip the examples for the contest). Verify before running.
- **Answers**: *who is more accurate vs ground truth* — mean placement/coverage
  per arm (H1), whether each accepted convention (e.g. C1) **raises** held-out
  placement accuracy (H5, per-convention A/B), false-disagreement reduction (H2).
- **Honest caveat**: source→UNV is **cross-lingual** (Hebrew/English→Chinese),
  *harder* than production's same-language UNV→LCC. Unavoidable: only UNV/CUV carry
  FHL SN in Chinese, so two independent *Chinese* annotated texts don't exist — WLC
  (with its English bridge) is the leak-free annotated source that, unlike KJV, is
  also **complete** (every SN incl. 09xxx). The contest is fair (s1 and s10 face the
  identical WLC→UNV task).
- **Key**: a **separate run** — task is WLC→UNV, NOT the UNV→LCC gold we already
  produced; the Gen 1 LCC gold does **not** feed A2.
- **Cost**: higher (fresh s10 run + s1 run on WLC→UNV), but the **only**
  path that can claim "s10 is as accurate as / beats s1 vs truth."
- **Use as**: the authoritative credibility verdict (H1–H5 below).

**One line**: *A1 measures likeness (cheap, "do they look the same?"); A2
measures correctness (heavier, "who is closer to FHL truth?"). Only A2 uses
`auto_score` against ground truth.* The Arms / Metrics / Hypotheses sections
below describe **A2** (the real contest); A1 is the optional warm-up diff.

## A2 scoring — two-stage divide-and-conquer (Joshua, 2026-06-25)

> **⤳ SUPERSEDED (2026-06-30) by the [§ Source pivot](#-source-pivot-2026-06-30--decouple-from-kjv--wlc--aligned-english)
> above.** This two-stage KJV design existed only to work around KJV's incompleteness;
> the pivot to a WLC+English source collapses it into one complete contest. Retained
> below because (a) its Stage-1 measurement *is* the evidence that KJV drops 31 % (why
> the pivot happened), and (b) its Stage-2 WLC loader is the foundation the unified
> contest builds on. Read it as rationale + components, not the current plan.

> **Scheme correction (supersedes an earlier draft).** An earlier draft made the
> original WLC/SBLGNT the *direct* SN answer key — that over-reached. **FHL's
> 09xxx prefix range is FHL-specific**: standard Strong's tops at H8674 and
> `WLC.tsv` has **zero** 9xxx. Clear Bible *does* tokenize the Hebrew prefixes but
> numbers them in an **augmented standard-range scheme** (Gen 1:1: ב=`H0871a`,
> ה=`H1886a`, ו=`H2050b`), NOT FHL's 09xxx. So **FHL ≠ Clear Bible numbering**;
> WLC-as-answer-key needs a scheme bridge. Since s1/s10 emit **FHL** tags, the
> primary scoring stays **FHL-internal**; Clear Bible is brought in deliberately —
> in Stage 2, as a *source*, not as the answer key.

The KJV/UNV count mismatch (survey5's bottleneck) unfairly penalizes coverage: a
source can't supply SNs its language doesn't express (the 09xxx prefixes, 0853 את,
some 8xxx). On Gen 1:1 the only UNV-only SN was `09002` (the ב prefix). Fix = **two
stages**, each its own divide-and-conquer, escalating rigor.

### Stage 1 — clean baseline (exclude 09xxx; zero scheme bridge)
- **source = KJV+SN, target = UNV-stripped**; score **placement only on
  `UNV-FHL ∩ KJV-FHL`** (the content-word core). The UNV-only 09xxx prefixes are
  **excluded, not scored**.
- Stays **entirely inside FHL's numbering** (what s1/s10 actually emit) → **zero
  bridge, zero extra cost**. The "easy 80%": settle the s1-vs-s10 placement verdict
  on the bulk first.
- `build_exclusion.py` builds it: per verse `shared = UNV-FHL ∩ KJV-FHL`,
  `excluded = UNV-only`; report the excluded-cluster distribution on Gen 1 to
  confirm it is the 09xxx/0853/8xxx families before any paid contest. Plus
  `score_placement(model_output, unv_fhl, shared)`. Cheap (FHL reads, zero model
  cost).

#### ✅ Stage-1 empirical result (`build_exclusion.py`, 2026-06-25 — run BEFORE any paid contest)

Built and run; **the kept set is fair, confirmed.** Key design correction made
during the build: intersection must be on the **bare Strong's NUMBER**
(family-agnostic), NOT on (number+role) — in naked mode the model transfers a
bare number, so an `'A'`-augmented attached form `WAH1961` and a plain `WH1961`
are the *same* supplyable number. Keying identity on role falsely excluded ~74
shared numbers; fixed → number-level multiset `shared = min(unv, kjv)`.

| corpus | UNV tags | kept (shared) | excluded (UNV-only) | excl % | content-lemma excess |
|---|---|---|---|---|---|
| **Gen 1** | 592 | 409 | 183 | 30.9% | **0** |
| **Gen 2** | 443 | 323 | 120 | 27.1% | 2 (H5117 rest, H120 man) |
| **Gen 1–5** | 2438 | 1819 | 619 | 25.4% | 7 (1.1%) |

The family profile is **stable across chapters** (ch1: prefix_09 62 / obj 23 / morph 24
/ core_func 74; ch2: prefix_09 36 / obj 13 / morph 5 / core_func 64) — same four
structural classes dominate, so the kept-set methodology generalises verse-to-verse.

Excluded-family distribution (Gen 1): `prefix_09` 62 · `obj_marker` (את 853) 23 ·
`morph` (UNV-only 8xxx codes) 24 · `core_function` 74 · **`core_content` 0**.

**Finding — the exclusion is broader than "just 09xxx", and that is the point.**
FHL's KJV annotation is *sparser* than UNV's because English structurally drops
Hebrew function words. Verified by hand: 1:3 UNV tags היה(1961) twice
(要有/就有了) but KJV tags "Let there be" once and leaves "and there was light"
**untagged**; 1:13 "有晚上有早晨"=1961×2 vs KJV "were" tagged **zero** (its own
footnote admits "Heb. …was, …was"); 1:31 一切=כל(3605) vs KJV "every thing"
untagged. So the excluded set = `{09xxx prefixes} ∪ {את} ∪ {UNV-only morph} ∪
{English-dropped function words: היה/כל/על/בין/אשר/הנה/מן/כן/כי/מה/שם/…}`.

**Fairness is by construction**: `shared = min(unv, kjv)` per number ⇒ every
KJV-supplyable instance is kept; `excluded` is strictly UNV's *excess*, which the
KJV source genuinely lacks (whether a function word or one extra count of a
content lemma like a repeated 神/上帝 where English used a pronoun). Gen 1 has
**zero** content-lemma excess; Gen 1–5 has 7 (LORD/God/Adam/man/rest/lift, all
count-mismatch). → **kept_set is a fair placement answer key for the contest.**

Artifacts: `kept_set_gen1-5.json` (per-verse kept + excluded-by-family for the
138-verse corpus); `score_placement(model_output, shared)` scores number presence
on the kept set (true *positional* placement defers to `survey4/auto_score.py`).

### Stage 2 — harsh full test (include 09xxx) with Clear Bible as the source
The hard tail: can the model place even the **09xxx prefixes**? KJV can't help —
English has no token for ב/ה/ו. **Clear Bible's WLC is the only source that carries
the prefixes explicitly** (Gen 1:1: `בְּ` H0871a `prep`, `הַ` H1886a `art`, `וְ`
H2050b `cj`), so it is the right — and only — input for this test.
- **source = original Hebrew (Clear Bible WLC), bridged to FHL numbering** via a
  small fixed table mapping the handful of inseparable prefixes (בכלמ + ה + ו + ש)
  → FHL 09xxx. Built once, reused everywhere.
- **target = UNV-stripped; score on the FULL set including 09xxx.**
- **Leak-free**: source tokens are Hebrew; the answer is *which Chinese token* —
  not in the Hebrew source. ⚠️ **`WLC.tsv` has a `gloss2` column with Chinese
  glosses** (创造/神/起初/地…); feeding it leaks Chinese hints, so the harsh test
  must feed **Hebrew word + number + morph only, `gloss2` stripped** (or treat
  gloss2 as a separate "with-hint vs no-hint" variable).

| | Stage 1 (baseline) | Stage 2 (harsh) |
|---|---|---|
| scores | content-word core placement | **full placement incl. 09xxx prefixes** |
| source | KJV+SN | **Clear Bible WLC** (explicit prefixes) |
| 09xxx | excluded | **included** (lemma→09xxx bridge) |
| numbering | all FHL, zero bridge | FHL + small fixed prefix bridge |
| role | clean, uncontested verdict | upper-bound stress test |
| cost | lowest (do first) | higher (do after) |

#### 🟢 Stage-2 feasibility CONFIRMED (data inspected 2026-06-25 — NOT yet built)

`Alignments/data/sources/WLC.tsv` exists and carries every column the harsh test
needs: `id · altId · text · strongs · gloss · gloss2 · lemma · pos · morph`. Gen
1:1 verified row-by-row:
- Inseparable prefixes are **separate tokens** with augmented numbering —
  `בְּ`=`H0871a`(prep), `הַ`=`H1886a`(art), `וְ`=`H2050b`(cj) — and **empty
  `gloss2`** (no Chinese gloss, since they aren't standalone Chinese words). So the
  bridge is **by lemma** (בְּ/הַ/וְ/כְּ/לְ/מִן/שֶׁ → FHL 09xxx), NOT by number —
  confirms the scheme-correction above.
- `אֵת`=`H0853` matches FHL `0853` directly (no bridge).
- `gloss2` leak is real (起初/创造/神/诸天/与/地) → **strip `gloss2`** for the
  no-hint test; `pos`/`morph` are safe non-leaking signal to keep.

Remaining build (when greenlit — this is the **paid** arm, do AFTER ch2/contest):
1. derive the FHL-09xxx ↔ prefix-lemma map empirically (cross-ref UNV 09xxx
   positions against WLC lemmas) — a ~7-entry fixed table;
2. WLC source loader (Hebrew text + strongs→FHL-normalized + pos + morph, gloss2
   dropped); 3. score on the FULL set incl. 09xxx via the kept_set's complement.

### ⚖️ WLC answer key — methodology-divergence rule (s1 gold ruling, 2026-06-29)

When WLC is used to validate/score gold (`eval_gold_vs_wlc.py`), some FHL-faithful
tags legitimately differ from WLC original-language morphology — these are
**methodology divergences, NOT gold errors**, and the WLC key must NOT penalise
them (else it wrongly punishes FHL-faithful gold and skews the s1-vs-s10 contest).

- **Canonical list**: `../survey1_prompt_evolving/FHL_DIVERGENCE_LOG.md` (s1 is the
  gold authority; the gold is FHL-faithful — it *transfers* FHL's SN, it does not
  *correct* FHL with WLC). `eval_gold_vs_wlc.py` reads this log and buckets matches
  as `methodology_divergence`, excluded from the error count.
- **Ruled example — D1 / Gen 2:20** 2nd אדם: gold `H0120` ("the man", matches 那人)
  vs WLC `H0121` ("Adam"). Article-less `וּלְאָדָם` + KJV/ESV/NIV "Adam" make WLC's
  reading sound, but the Chinese 那人 anchors H0120 → **keep H0120**, log as
  divergence + FHL-feedback candidate.
- **Whole-gold WLC check (Gen 1–2, 56 verses)**: 982/986 SN-inventory-consistent
  (lexical + 09xxx prefix + s5 morph bridge); after excluding the 1 ruled
  divergence, residual gold-only = an FHL `<WH00>` artifact + a verb-doubling
  count + an את-companion 854/853 nuance — **zero hallucinated content words**.

### Clear Bible as a cross-check (supporting role, both stages)
The 10+ aligned languages × translations (each a finished **manual** word-level SN
alignment gold) serve as a **robustness vote** for *why* an SN is excluded: bridge
the FHL 09xxx prefix by **lemma** (ב/ה/ו/את) to the Clear Bible token and confirm
it is either unaligned or aligned only to function words across languages. This
corroborates the Stage-1 exclusion without making Clear Bible the answer key. A
**pure-alignment arena** (project among the aligned languages, score vs their
manual gold — no FHL, no Chinese) remains available for *method* validation, but
is non-Chinese so it does not directly judge the UNV→LCC product.

## Arms

| Arm | Method | Cross-verse learning |
|---|---|---|
| **A — s1** | `../survey1_prompt_evolving` consensus, unchanged | prompt evolution (`+0.1`, gated) |
| **B — s10-E** | this dir: per-verse `/clear`, blind R1/R2 (C tier), gated D-deliberation (post-C), conventions.md | `conventions.md` (gated, versioned) |
| **B0 — s10 ablation** (optional) | s10 with `conventions.md` **frozen empty** | none (isolates the conventions contribution) |

A and B see the **same WLC→UNV corpus** (source = WLC + aligned English (BSB/YLT),
target UNV-stripped, score vs UNV FHL truth on the **full inventory incl. 09xxx**;
post-pivot 2026-06-30 — source was KJV+SN before) and the **same panel roster**
(opus/agy/codex). Only the method differs. B0 isolates how much the conventions
pipeline itself contributes vs the transport.

## Corpus

- **Primary**: Genesis 1–5 (138 verses) — the corpus already partially run; UNV
  has full FHL truth across it. 68 verses already produced clean last session
  provide a warm cache for arm A baselining.
- **Held-out for convention scoring**: split each chapter into *train* (scribe may
  extract conventions from these resolved verses) and *test* (never extracted
  from; used only to measure whether a convention generalizes).
- Extendable to a second book (e.g. a NT chapter) to test convention transfer
  across Testaments.

## Metrics (all from `survey4/auto_score.py`)

Per verse, against FHL truth:
- **placement** (primary) — fraction of truth tags placed on the right token.
- **coverage** — fraction of truth tags present (no missing/extra).
- **exact** — whole-verse exact match (strict).
- **format** — FHL-format compliance.

Aggregated per arm: mean placement/coverage, exact-match rate, and the
**disagreement profile** below.

### Secondary / mechanism metrics
- **Cost**: total LLM calls + tokens per arm (s10 should fall over time as
  conventions settle and re-rolls drop).
- **Genuine-ambiguity resolution**: # verses where blind R2 flagged instability,
  split by *resolved by D-deliberation* (s10 only) vs *left flagged* (s1).
- **False-disagreement removed**: # R1 panel splits in arm A that **do not occur**
  in arm B because a convention pre-aligned them. This is s10's headline claim —
  measure it directly.
- **Per-convention delta**: for each rule in `conventions.md`, placement accuracy
  on the *test* split **with vs without** that rule. Positive = real; ≤0 = demote
  (closes the `CONVENTIONS_PIPELINE.md` step-5 loop).

## Hypotheses (falsifiable)

- **H1 (parity-or-better)**: mean placement(B) ≥ placement(A). *Refuted if s10 is
  worse → s10 stays a propagation engine, s1 remains gold authority.*
- **H2 (false-disagreement)**: B has materially fewer R1 panel splits than A on
  convention-covered phenomena (implicit markers, rebinding, 神/上帝).
- **H3 (resolves the hard ones)**: among R2-flagged unstable verses, B resolves a
  higher fraction via D-deliberation than A leaves flagged.
- **H4 (cheaper over time)**: B's per-verse cost trends **down** across chapters
  as conventions settle; A's stays flat.
- **H5 (conventions are real)**: most accepted conventions show **positive**
  held-out placement delta (H5 fails → the scribe is overfitting; tighten the
  gate / budget).

## Procedure

```
0. Freeze panel roster (opus/agy/codex); erha → Gemini 3.1 Pro (High).
1. build_exclusion.py (Stage 1, CHEAP, FHL-internal, zero model cost — run FIRST):
   - per verse: shared = UNV-FHL ∩ KJV-FHL ; excluded = UNV-only (the 09xxx etc.).
   - kept_set[verse] = shared. Report exclusion-cluster distribution on Gen 1 to
     CONFIRM the 09xxx/0853/8xxx hypothesis before paying for a contest.
   - (optional cross-check) corroborate excluded SNs via Clear Bible alignment by
     lemma bridge — NOT the answer key, just a robustness vote.
2. Build the contest corpus: source = KJV+SN (or a manually-aligned translation),
   target = UNV stripped (strip_shell, Gen 1–5); UNV-FHL = placement answer key.
   Audit prompt worked-examples to exclude any tested verse (no answer leak).
3. Arm A: run s1 consensus over the corpus → gold_A/{book}/{ch}/{sec}.json
4. Arm B: run s10-E (this dir), scribe active per-chapter → gold_B/... + conventions
   history. (B0 ablation: same but conventions.md frozen empty.)
5. Score: score_placement(gold_X, unv_fhl, kept_set[verse]) per verse, both arms —
   placement only on the kept set; excluded SNs reported separately, not scored.
6. Aggregate: placement/coverage/exact per arm + the secondary metrics.
7. Per-convention A/B on the test split → annotate conventions.md deltas; demote ≤0.
8. Verdict table (below).
```

## ▶ First contest result — B vs B0 (conventions isolation), Gen 1–2, opus (2026-06-26)

Ran `run_a2_contest.py` (the first cut: same single-pass opus annotates each verse
twice, conventions ON vs OFF; full Arm A = s1 consensus is a later layer). Harness
validated; two bugs fixed first — raw `claude -p` inherits this repo's CLAUDE.md
and drifts into project-assistant meta-chatter ("Recorded to prompt.history…") →
routed through `cli_caller.call_llm` **structured output** (forces clean `{unv_sn}`);
and `clean_output` now picks the tag-bearing line with the most CJK chars (avoids
grabbing an echoed C1-example line).

| arm | placement* | coverage* | **kept_place** |
|---|---|---|---|
| **B** (conv ON) | 0.7274 | 0.6524 | **0.9971** |
| **B0** (conv OFF) | 0.7284 | 0.6555 | **0.9914** |
| **Δ (B − B0)** | −0.0011 | −0.0031 | **+0.0058** |

\* `auto_score.placement`/`coverage` are noisy here (position-shift artifacts from
KJV-unsupplyable prefixes shifting char offsets); **`kept_place`** (Stage-1 kept-set
number coverage) is the trustworthy metric.

**Aggregate is tiny but directionally positive; the signal lives in the hard
verses.** 50/56 verses are at the kept-place ceiling (~1.0) for BOTH arms — opus
already nails the KJV-supplyable numbers, so conventions have nothing to fix there.
On the **6 verses where B0 actually erred**, B helped 5:1 — full fixes on 1:6
(9/10→10/10), 1:17 (7/8→8/8), 1:24 (13/14→14/14), 2:5 (20/21→21/21); partial on
1:11 (18/20→19/20); tie on 1:28; one regression (1:4). Net +4 kept tags.

**Honest caveats / what this dictates next:**
1. **Ceiling**: opus on easy Genesis can't discriminate. Use a **weaker model**
   (more headroom) or **focus on hard verses** to see convention value.
2. **Sampling noise**: 1 sample/arm/verse + a stochastic model means the 5:1 fix
   ratio is confounded (a fresh re-run of 1:17 fixed a *different* tag, 0430, not
   the C1 morph pattern). A rigorous number needs **N samples/verse/arm** (or
   low-temp) to separate convention-effect from sampling variance.
3. **One narrow rule**: with only C1 in `conventions.md`, the achievable Δ is
   small by construction. Effect should compound as the scribe adds gated rules.

→ **Verdict so far: H5 directionally supported (conventions help where the model
errs, ~zero cost where it doesn't), not yet significant.** The B-vs-B0 design is
sound but ceiling+noise-limited on opus/Genesis; harden with multi-sample or a
weaker model before treating the number as decisive.

## Verdict table (to fill)

| Metric | Arm A (s1) | Arm B (s10-E) | B0 (no conv) | Winner |
|---|---|---|---|---|
| mean placement | | | | |
| mean coverage | | | | |
| exact-match rate | | | | |
| false-disagreements (R1 splits) | | | | |
| genuine-ambiguity verses resolved (D-deliberation) | n/a | | n/a | |
| total cost (calls / tokens) | | | | |
| conventions w/ positive delta | n/a | / | n/a | |

## Decision rule

- **B ≥ A on placement AND H5 holds** → s10-E is a **co-equal or superior** gold
  producer; promote it from "propagation engine" to gold authority (or run both
  and reconcile). This is the brief's stretch goal ("甚至超越").
- **B ≈ A but cheaper (H4) and removes false-disagreements (H2)** → s10-E is the
  **preferred production** path (same trust, less cost, cleaner residual
  disagreements), with s1 retained as an audit cross-check.
- **B < A** → s1 stays the authoritative gold; s10 reverts to cheap propagation,
  and the conventions pipeline is re-examined (likely H5 failure = overfit).

## Why this is a fair test
- Same panel, same corpus, same objective scorer — only the *method* varies.
- Ground truth is FHL's own tags, not either method's consensus → no circularity.
- The B0 ablation isolates the conventions contribution from the transport, so a
  win can be **attributed**, not just observed.
