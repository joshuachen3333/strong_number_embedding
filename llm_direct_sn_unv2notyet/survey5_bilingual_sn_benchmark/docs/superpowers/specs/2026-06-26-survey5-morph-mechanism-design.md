# Survey5 morph-handling mechanism (design)

Date: 2026-06-26 · Author: survey5_bilingual_sn_benchmark-obe
Status: **draft, pending Joshua review**

## 1. Context & goal

Round-1 settled survey5 on a **WLC-only** source (no English bridge). The remaining
coverage hole is the **FHL morphology codes (8xxx)** — verbal stem/form tags like
`<WTH8804>` (Qal Perfect). On Gen 1 there are 91 such tags, and both bake-off
configs recalled ~0–5% of them: the WLC→FHL lexical bridge drops codes >8674, and
the *model* is bad at placing morph even when handed it.

Joshua's decision: morph is **in-scope**, handled by a dedicated mechanism (not by
adding another translation source).

## 2. Key facts (grounding, verified on real data)

- **WLC carries source morphology** per verb token in ETCBC notation:
  `בָּרָא  strongs=H1254  pos=verb  morph=vqp3ms` (v=verb, q=Qal, p=Perfect, 3ms=PGN).
- **FHL's code is stem+form only** — `8804` = Qal Perfect, covering vqp3ms / vqp3fs /
  vqp1cs alike. Person/gender/number is dropped. Documented in survey2 §6.
- **Morph always co-locates**: 101/101 morph tags in Gen 1 sit immediately after their
  verb's lexical tag (`創造<WH01254><WTH8804>`). Morph never floats free.
- **The model can't place morph**: config B (handed morph via KJV) recalled only 5%.
- The model *can* place the verb's **lexical** tag well (rock tier = 99%).

## 3. Architecture — learn → freeze → apply, with deterministic attach

Two decisions are locked (Joshua): **deterministic attach** (the model never handles
morph) and **learn the bridge from FHL↔WLC alignment** (not hand-coded from the doc).

### 3a. Bridge learner (offline, one-time) — `learn_morph_bridge.py`

Goal: produce a frozen `MORPH_BRIDGE` mapping **WLC verb form-key → FHL 8xxx code**.

This is a **one-time sweep over the entire Old Testament** (all 39 books) — the same
family of work as the hand-coded 09xxx `PREFIX_BRIDGE`: a definitive WLC→FHL bridge
built once. Sweeping the whole OT (not a subset) guarantees every stem+form
combination is seen, so there are no "unseen form_key" gaps at apply time. The sweep
also **re-validates the existing 09xxx PREFIX_BRIDGE** against FHL gold as a free
by-product (same alignment, prefix tokens instead of verbs).

1. Over **every OT verse**, for each verse:
   - Parse FHL UNV+SN gold into ordered `(lexical_SN, morph_code)` pairs (a morph tag
     `<WTH8804>` binds to the lexical tag immediately before it).
   - Load WLC verb tokens (`pos == "verb"`) in order, each with `(lexical_SN, form_key)`.
   - **Align by lexical Strong's number in order**: pair each WLC verb with the gold
     morph tag whose lexical SN matches. Record `(form_key → fhl_code)`.
2. `form_key` = the stem+form prefix of the WLC morph string, PGN/markers stripped.
   For verbs the key is the first three characters after the leading `v`-stem-form
   (e.g. `vqp3ms → vqp`, `vqw3msXa → vqw`, `vhi3fsXa{1}Jt → vhi`, `vqPmsa → vqP`,
   `vhc → vhc`). The exact parser is pinned in the implementation plan.
3. **Consistency check**: every `form_key` must map to exactly one `fhl_code`. Any
   form_key seen with ≥2 codes is a **conflict** — reported, not silently resolved
   (likely a parser bug or a genuine FHL split to encode by hand).
4. Emit the frozen table to `morph_bridge.json` (form_key → code) plus a coverage
   report: how many distinct form_keys, how many verses/verbs aligned, any unaligned
   verbs, any conflicts.

This uses gold legitimately: it learns a **universal linguistic mapping**
(form → code), not any verse's answer.

### 3b. Deterministic morph attach (apply time) — `attach_morph()`

Input: the model's UNV output (lexical tags placed), the verse's WLC verb tokens, and
the frozen `MORPH_BRIDGE`. For each WLC verb token, in order:

1. Look up its `form_key` in `MORPH_BRIDGE` → `fhl_code` (skip + log if form_key unseen).
2. Find the **anchor**: the placed lexical tag in the model output whose number matches
   the verb's lexical SN (match by number; if several verbs share a lexical SN, pair
   them in left-to-right order).
3. Insert `<WTH{code}>` immediately after that anchor tag.
4. If the anchor isn't present (model didn't place that verb's lexical tag), skip —
   no anchor to attach to. So **morph recall ≤ lexical-verb recall** by construction.

The model's prompt/source is **unchanged** (lexical-only WLC source); morph is purely
post-processing. This keeps the model's job minimal and is zero-loss table work — the
same separation of *semantic placement* (model) vs *mechanical attachment* (table)
that naked mode already uses.

### 3c. Integration & scoring

- A WLC-only run (config A) gets an `attach_morph()` pass on each output before scoring.
- Score as before (`scoring.num_score` format-agnostic + `gate` tiers). The morph tags
  now appear, so the morph tier recall (previously `kjv_only` ≈ 0%) should jump toward
  the lexical-verb recall ceiling.
- Add an explicit **morph recall** metric: of the gold's 8xxx morph tags, how many the
  attached output supplies (number-level), reported next to 09xxx recall.

## 4. The no-leak discipline

- **One-time whole-OT sweep, freeze, then apply.** The mapping (form → code) is a
  **universal linguistic fact** — a Qal Perfect is `8804` in every book — so building
  the table from the whole OT (Gen 1 included) and then scoring Gen 1 is **not a leak**:
  no verse-specific answer is memorised, only the universal rule. The earlier
  "held-out subset" hedge is dropped; the full sweep is both simpler and gives
  complete coverage.
- **Never read the scored verse's own gold morph at apply time.** Apply uses only the
  frozen table + the verse's WLC form-keys — never that verse's UNV+SN gold. (Reading
  per-verse gold would make morph recall a meaningless 100%.) This is the one and only
  leak rule; the universal table itself is leak-free.

## 4b. After the table: survey5 runs as the standard pipeline

Once `morph_bridge.json` is frozen, the survey5 morph run is just the normal WLC-only
flow with one extra deterministic step — no new model behaviour:

```
WLC+SN  +  UNV (plain)  --model-->  UNV with lexical+09xxx tags placed
                         --attach_morph(frozen table)-->  UNV+SN (lexical+09xxx+morph)
                         --score vs FHL UNV+SN gold-->  cov / placement / 09xxx / morph recall
```

So yes: build the table once, then run survey5 exactly as the bake-off already does,
plus the `attach_morph()` pass, and score against the answer.

## 5. Components / files (survey5-local)

| File | Responsibility |
|---|---|
| `learn_morph_bridge.py` | Align FHL↔WLC over training verses → emit `morph_bridge.json` + report |
| `morph_bridge.json` | Frozen `{form_key: fhl_code}` table (the learned artifact) |
| `morph.py` | `wlc_form_key(morph_str)`, `load_bridge()`, `attach_morph(output, wlc_tokens, bridge)` |
| `test_morph.py` | Unit tests for form-key parsing + attach (synthetic, no model) |
| `run_bakeoff.py` (modify) | Call `attach_morph()` on WLC-only output before scoring; add morph-recall metric |

`morph.py` needs WLC verb tokens **with their form** — extend the loader usage to keep
`(text, lexical_num, pos, morph_str)` (the s10 `load_wlc_verse` returns only
`(text, fhl_num)`; the bake-off will read the WLC TSV rows directly for pos/morph, or
add a thin local loader — pinned in the plan).

The whole-OT sweep also needs **all 39 OT book numbers** in a Chinese→WLC-book map
(s10's `CHI_TO_WLC_BOOK` has only `創:01`); the learner extends it to `01`–`39` with
the matching Chinese abbrevs for the UNV fetch.

## 6. Edge cases

- **Unseen form_key at apply time** → skip that morph, log it (don't guess). Surfaces
  as a coverage gap, not a wrong tag.
- **Multiple verbs sharing a lexical SN in one verse** → pair anchors left-to-right.
- **Model didn't place the verb's lexical tag** → no anchor, skip (bounded by lexical recall).
- **form_key → multiple codes conflict** in learning → reported; resolve by hand before freezing.
- **Non-verb morph** → out of scope; only `pos == "verb"` tokens carry 8xxx codes.

## 7. Success criteria

- **Bridge consistency**: every learned form_key maps to a single FHL code (zero
  unresolved conflicts after the learning pass).
- **Morph recall on Gen 1** rises from ~0% (Round-1 A) to near the lexical-verb recall
  ceiling (target: ≥80% of the 91 morph tags).
- **No regression** on lexical/09xxx tiers (attach only adds morph tags after existing
  anchors; it must not perturb lexical placements).
- **No leak**: the table is frozen and verse-independent at apply time.

## 8. Open decisions (for Joshua at review)

1. **Learning scope** = **one-time sweep of the entire OT (all 39 books)** — confirmed
   by Joshua. Gives complete form-key coverage; the universal mapping makes this
   leak-free even though Gen 1 is included.
2. **Output shell** = emit morph as `<WTH{code}>` (FHL form) — assumed; scoring is
   shell-agnostic anyway, but production output should match FHL.
3. **form_key parser** keys on stem+form, PGN/markers stripped — assumed (exact rule
   pinned in the plan).
