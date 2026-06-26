# Survey5 Multi-source SN Bake-off (Round 1: A vs B) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bake-off harness that scores two source configs — A (WLC-only) and B (WLC+KJV) — for transferring Strong's Numbers onto UNV, against FHL gold, with split reporting (09xxx recall + per trust-tier recall).

**Architecture:** Three small survey5-local modules. `wlc_bridge.py` re-exports the s10 WLC loader (import, never mutate). `gate.py` is a pure tier-labeller over `build_exclusion.tag_multiset` (classifies each gold tag as 🟢 rock / 🟡 wlc_only / 🔵 orphan by which sources carry it). `run_bakeoff.py` orchestrates per-verse: build source strings, call the model for each config, score. Reuses survey5's `call_model`, survey4's `auto_score`, s10's `nines_recall`.

**Tech Stack:** Python 3 (stdlib only), existing FHL fetch + Claude CLI caller. No new deps. No pytest in this dir — tests are plain-assert scripts run with `python3` (matches repo convention "scripts run directly").

**Scope:** Round 1 = A vs B (both zero-build, all sources ready). Round 2 (build BSB+SN, add config C) is a **separate follow-up plan**, written only if R1 shows an English bridge helps.

---

### Task 1: WLC bridge shim

**Files:**
- Create: `survey5_bilingual_sn_benchmark/wlc_bridge.py`

The s10 import path is verified working (`import run_stage2_harsh` succeeds; `load_wlc_verse('01',1,1)` → 11 morphemes, gloss2 dropped). This shim isolates the cross-dir import to one place.

- [ ] **Step 1: Write the shim**

```python
# wlc_bridge.py — re-export s10's WLC primitives (import, do NOT mutate s10 files).
# Per CLEAR_BIBLE_HANDOVER_from_s10obe.md: reuse the loader + lemma->FHL-09xxx bridge.
import os
import sys

_S10 = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "survey10_s1_but_obe_insteadOf_oneshot")
)
if _S10 not in sys.path:
    sys.path.insert(0, _S10)

import run_stage2_harsh as _H  # noqa: E402

load_wlc_verse = _H.load_wlc_verse        # (wlc_book, chap, sec) -> [(hebrew, fhl_num|None), ...]
build_wlc_source = _H.build_wlc_source    # tokens -> "hebrew<num>..."  (gloss2 already dropped)
build_harsh_prompt = _H.build_harsh_prompt  # (wlc_source, unv_plain, book_eng, chap, sec) -> str
nines_recall = _H.nines_recall            # (model_output, unv_sn) -> (placed, total)
CHI_TO_WLC_BOOK = _H.CHI_TO_WLC_BOOK      # {"創": "01"}
```

- [ ] **Step 2: Smoke-verify the shim**

Run:
```bash
cd survey5_bilingual_sn_benchmark
python3 -c "import wlc_bridge as W; t=W.load_wlc_verse('01',1,1); print(len(t)); print(W.build_wlc_source(t))"
```
Expected: prints `11` then a Hebrew line containing `<09002>` and `<7225>` and **no Chinese characters** (gloss2 dropped).

- [ ] **Step 3: Commit**

```bash
git add survey5_bilingual_sn_benchmark/wlc_bridge.py
git commit -m "feat(survey5): wlc_bridge shim re-exporting s10 WLC loader"
```

---

### Task 2: Gate (pure trust-tier labeller)

**Files:**
- Create: `survey5_bilingual_sn_benchmark/gate.py`
- Test: `survey5_bilingual_sn_benchmark/test_gate.py`

Gate logic: `tag_multiset` parses bare `<7225>` (WLC) AND `<WH0430>` (KJV/UNV) — verified. Each gold (UNV) tag is labelled by which sources carry it: 🟢 rock = WLC∩KJV, 🟡 wlc_only = WLC not KJV, 🔵 orphan = neither. (Round 1 has no BSB, so 🟡/🔵 are not further split; Round 2 adds that.)

- [ ] **Step 1: Write the failing test**

```python
# test_gate.py — run: python3 test_gate.py
import gate as G


def main():
    # gold has 6 tags: H9002 (09xxx prefix), 4 content words, and H1234 (no source).
    unv = "<09002><07225><0430><8064><0776><1234>"
    wlc = "<09002><07225><0430><8064><0776>"          # carries everything except H1234
    kjv = "<07225><0430><8064><0776>"                  # English drops the 09xxx prefix

    tiers = G.gold_tiers(unv, wlc, kjv)
    by = {k[1]: v["tier"] for k, v in tiers.items()}
    assert by["H9002"] == "wlc_only", by
    assert by["H7225"] == "rock", by
    assert by["H1234"] == "orphan", by

    # full placement -> every tier fully recalled
    full = "<09002><07225><0430><8064><0776><1234>"
    rec = G.tier_recall(full, unv, wlc, kjv)
    assert rec["rock"]["frac"] == 1.0, rec
    assert rec["wlc_only"]["frac"] == 1.0, rec

    # model misses the 09xxx prefix -> wlc_only recall drops to 0
    miss = "<07225><0430><8064><0776><1234>"
    rec2 = G.tier_recall(miss, unv, wlc, kjv)
    assert rec2["wlc_only"]["placed"] == 0, rec2

    print("test_gate OK")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd survey5_bilingual_sn_benchmark && python3 test_gate.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'gate'` (or `AttributeError: gold_tiers`).

- [ ] **Step 3: Write the implementation**

```python
# gate.py — pure trust-tier labeller over build_exclusion (answer-blind for tiering;
# gold-anchored for recall). No LLM. See docs/.../2026-06-26-...-design.md §3.
import os
import sys

_S10 = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "survey10_s1_but_obe_insteadOf_oneshot")
)
if _S10 not in sys.path:
    sys.path.insert(0, _S10)

import build_exclusion as BX  # noqa: E402


def gold_tiers(unv_sn, wlc_sn, kjv_sn):
    """Label each gold (UNV) tag by which sources carry it.

    Returns {key: {"tier": rock|wlc_only|orphan, "family": str, "need": int}}.
    key is build_exclusion's (testament, "H<n>") tuple.
    """
    gold, fam = BX.tag_multiset(unv_sn)
    wlc, _ = BX.tag_multiset(wlc_sn)
    kjv, _ = BX.tag_multiset(kjv_sn)
    tiers = {}
    for key, need in gold.items():
        in_w = wlc.get(key, 0) > 0
        in_k = kjv.get(key, 0) > 0
        tier = "rock" if (in_w and in_k) else ("wlc_only" if in_w else "orphan")
        tiers[key] = {"tier": tier, "family": fam.get(key), "need": need}
    return tiers


def tier_recall(model_output, unv_sn, wlc_sn, kjv_sn):
    """Number-level recall of gold tags, grouped by trust tier.

    Returns {tier: {"placed": int, "total": int, "frac": float}}.
    """
    tiers = gold_tiers(unv_sn, wlc_sn, kjv_sn)
    out, _ = BX.tag_multiset(model_output)
    agg = {}
    for key, info in tiers.items():
        d = agg.setdefault(info["tier"], {"placed": 0, "total": 0})
        d["placed"] += min(info["need"], out.get(key, 0))
        d["total"] += info["need"]
    for d in agg.values():
        d["frac"] = d["placed"] / d["total"] if d["total"] else 1.0
    return agg
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd survey5_bilingual_sn_benchmark && python3 test_gate.py`
Expected: PASS — prints `test_gate OK`.

- [ ] **Step 5: Real-data sanity check (Gen 1:1)**

Run:
```bash
cd survey5_bilingual_sn_benchmark
python3 -c "
import wlc_bridge as W, gate as G
from run_survey5 import fetch_chap_cached
unv=fetch_chap_cached('創',1,'unv',strong=1); kjv=fetch_chap_cached('創',1,'kjv',strong=1)
wlc=W.build_wlc_source(W.load_wlc_verse('01',1,1))
t=G.gold_tiers(unv[1], wlc, kjv[1])
print({k[1]: v['tier'] for k,v in t.items()})
"
```
Expected: a dict where `H9002` → `wlc_only` and the content words (`H7225`,`H430`,`H1254`,`H8064`,`H776`) → `rock`.

- [ ] **Step 6: Commit**

```bash
git add survey5_bilingual_sn_benchmark/gate.py survey5_bilingual_sn_benchmark/test_gate.py
git commit -m "feat(survey5): gate.py trust-tier labeller + test"
```

---

### Task 3: Bake-off harness — config A (WLC-only)

**Files:**
- Create: `survey5_bilingual_sn_benchmark/run_bakeoff.py`

- [ ] **Step 1: Write the harness skeleton with config A only**

```python
#!/usr/bin/env python3
"""run_bakeoff.py — Survey5 v2 multi-source bake-off (Round 1: A vs B).

A = WLC-only (Hebrew original -> UNV).
B = WLC + KJV (Hebrew original + English bridge -> UNV).
Scores vs FHL UNV+SN gold: overall (auto_score) + 09xxx recall + per trust-tier recall.
Spec: docs/superpowers/specs/2026-06-26-survey5-multisource-bakeoff-design.md
"""
import argparse
import json
import os
import sys
import time

import wlc_bridge as W
import gate as G
# Importing run_survey5 puts the parent dir and survey4 dir on sys.path, so the
# following imports resolve afterwards.
from run_survey5 import call_model, detect_brand, fetch_chap_cached  # noqa: E402
from auto_score import score_verse, strip_sn  # noqa: E402
from llm_direct_sn_unv2notyet import CHI_TO_ENG  # noqa: E402

SYSTEM = (
    "You are an expert in Strong's Number annotation of biblical texts. "
    "Given a source text already tagged with Strong's Numbers, place those tags "
    "onto the correct positions of the plain Chinese (UNV) text. "
    "Output ONLY the annotated UNV text on a single line, no commentary."
)


def build_a_prompt(wlc_source, unv_plain, book_eng, chap, sec):
    """Config A user prompt: WLC (Hebrew+SN) -> UNV. Reuses s10's harsh prompt."""
    return W.build_harsh_prompt(wlc_source, unv_plain, book_eng, chap, sec)


def run_config(label, build_user, verses, model, brand):
    rows = []
    for (chap, sec, unv_sn, wlc_source, kjv_plain, kjv_sn) in verses:
        unv_plain = strip_sn(unv_sn)
        user = build_user(wlc_source, kjv_plain, kjv_sn, unv_plain,
                          verses_book_eng, chap, sec)
        t0 = time.time()
        out = call_model(model, brand, None, SYSTEM, user)
        if not out:
            print(f"  [{label}] {chap}:{sec}  EMPTY (skip)", flush=True)
            continue
        sc = score_verse(out, unv_sn)
        n9p, n9t = W.nines_recall(out, unv_sn)
        tiers = G.tier_recall(out, unv_sn, wlc_source, kjv_sn)
        rows.append({"chap": chap, "sec": sec, "score": sc,
                     "n9_placed": n9p, "n9_total": n9t, "tiers": tiers,
                     "output": out})
        r9 = f"{n9p}/{n9t}" if n9t else "—"
        print(f"  [{label}] {chap}:{sec}  cov={sc['coverage']:.3f} "
              f"place={sc['placement']:.3f} 09xxx={r9} {time.time()-t0:.0f}s",
              flush=True)
    return rows


# NOTE: build_user signature is unified as
#   build_user(wlc_source, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec)
# Config A ignores kjv_plain/kjv_sn. `verses_book_eng` is set in main() (single book per run).
verses_book_eng = None


def main():
    global verses_book_eng
    ap = argparse.ArgumentParser(description="Survey5 multi-source bake-off (A vs B)")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", type=int, default=1)
    ap.add_argument("--sec", default=None, help="e.g. 1 or 1-5 or 1,3,5")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--configs", default="A,B")
    ap.add_argument("--out", nargs="?", const="", default=None)
    args = ap.parse_args()

    book_chi = args.book
    verses_book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    wlc_book = W.CHI_TO_WLC_BOOK.get(book_chi)
    if not wlc_book:
        sys.exit(f"No WLC book number for {book_chi}; add to s10 CHI_TO_WLC_BOOK.")
    brand = detect_brand(args.model, None)

    unv = fetch_chap_cached(book_chi, args.chap, "unv", strong=1)
    kjv = fetch_chap_cached(book_chi, args.chap, "kjv", strong=1)
    secs = sorted(set(unv) & set(kjv))
    if args.sec:
        from llm_direct_sn_unv2notyet import parse_sec_arg
        want = set(parse_sec_arg([args.sec]))
        secs = [s for s in secs if s in want]

    verses = []
    for sec in secs:
        wlc_source = W.build_wlc_source(W.load_wlc_verse(wlc_book, args.chap, sec))
        if not wlc_source:
            continue
        verses.append((args.chap, sec, unv[sec], wlc_source,
                       strip_sn(kjv[sec]), kjv[sec]))

    print(f"\n{'='*60}\n  Survey5 BAKE-OFF — {verses_book_eng} {args.chap} "
          f"({len(verses)} verses)  model={args.model}  configs={args.configs}\n{'='*60}")

    builders = {"A": build_a_prompt}  # B added in Task 4
    results = {}
    for cfg in [c.strip() for c in args.configs.split(",") if c.strip()]:
        if cfg not in builders:
            print(f"  (config {cfg} not implemented yet — skip)")
            continue
        print(f"\n── Config {cfg} ──", flush=True)
        bu = builders[cfg]
        results[cfg] = run_config(
            cfg, lambda ws, kp, ks, up, be, ch, se, _bu=bu: _bu(ws, up, be, ch, se),
            verses, args.model, brand)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-run config A on one verse**

Run:
```bash
cd survey5_bilingual_sn_benchmark
python3 run_bakeoff.py --book 創 --chap 1 --sec 1 --model opus --configs A
```
Expected: one line `[A] 1:1  cov=… place=… 09xxx=…/…  Ns` with no traceback. (Consumes real opus quota — one call.)

- [ ] **Step 3: Commit**

```bash
git add survey5_bilingual_sn_benchmark/run_bakeoff.py
git commit -m "feat(survey5): bake-off harness with config A (WLC-only)"
```

---

### Task 4: Config B (WLC + KJV bridge)

**Files:**
- Modify: `survey5_bilingual_sn_benchmark/run_bakeoff.py`

- [ ] **Step 1: Add the config B prompt builder**

Insert after `build_a_prompt` in `run_bakeoff.py`:

```python
def build_b_prompt(wlc_source, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec):
    """Config B user prompt: WLC (Hebrew+SN) + KJV (plain & +SN) -> UNV."""
    return f"""Here is {book_eng} {chap}:{sec} in the original Hebrew (WLC), each \
morpheme tagged with its FHL Strong's Number (inseparable prefixes use the 09xxx \
codes: 09001=לְ to/for, 09002=בְּ in, 09003=כְּ as, 09006=מִ from, 09009=הַ the):

{wlc_source}

Here is the same verse in KJV (plain, no tags):

{kjv_plain}

Here is the same verse in KJV with Strong's Number annotations:

{kjv_sn}

Here is the same verse in UNV (和合本), plain, no annotations:

{unv_plain}

Using the Hebrew and the KJV annotation pair above as your references, insert the \
Strong's Number tags into the correct positions in the UNV text, INCLUDING the \
09xxx inseparable-prefix tags where the Chinese expresses them. Output ONLY the \
annotated UNV text on a single line, no commentary."""
```

- [ ] **Step 2: Register config B in the builders map**

In `main()`, change:
```python
    builders = {"A": build_a_prompt}  # B added in Task 4
```
to:
```python
    builders = {
        "A": lambda ws, kp, ks, up, be, ch, se: build_a_prompt(ws, up, be, ch, se),
        "B": build_b_prompt,
    }
```
And change the `run_config` call to pass builders uniformly (the unified 7-arg signature):
```python
        print(f"\n── Config {cfg} ──", flush=True)
        results[cfg] = run_config(cfg, builders[cfg], verses, args.model, brand)
```
(Both builders now take the unified `(wlc_source, kjv_plain, kjv_sn, unv_plain, book_eng, chap, sec)` signature, so the lambda wrapper from Task 3 Step 1 is removed.)

- [ ] **Step 3: Smoke-run A vs B on one verse**

Run:
```bash
cd survey5_bilingual_sn_benchmark
python3 run_bakeoff.py --book 創 --chap 1 --sec 1 --model opus --configs A,B
```
Expected: two lines `[A] 1:1 …` and `[B] 1:1 …`, no traceback. (Two opus calls.)

- [ ] **Step 4: Commit**

```bash
git add survey5_bilingual_sn_benchmark/run_bakeoff.py
git commit -m "feat(survey5): bake-off config B (WLC+KJV bridge)"
```

---

### Task 5: Aggregation, split summary, JSON output

**Files:**
- Modify: `survey5_bilingual_sn_benchmark/run_bakeoff.py`

- [ ] **Step 1: Add a summary printer**

Insert before `main()` in `run_bakeoff.py`:

```python
def print_summary(results):
    print(f"\n{'='*60}\n  SUMMARY\n{'='*60}")
    print(f"  {'cfg':<5}{'cov':>8}{'place':>8}{'fmt':>8}"
          f"{'09xxx':>12}{'rock':>10}{'wlc_only':>12}")
    for cfg, rows in results.items():
        if not rows:
            continue
        n = len(rows)
        cov = sum(r["score"]["coverage"] for r in rows) / n
        place = sum(r["score"]["placement"] for r in rows) / n
        fmt = sum(r["score"]["format"] for r in rows) / n
        n9p = sum(r["n9_placed"] for r in rows)
        n9t = sum(r["n9_total"] for r in rows)
        n9 = f"{n9p}/{n9t} ({100*n9p/n9t:.0f}%)" if n9t else "n/a"

        def tier_frac(tier):
            p = sum(r["tiers"].get(tier, {}).get("placed", 0) for r in rows)
            t = sum(r["tiers"].get(tier, {}).get("total", 0) for r in rows)
            return f"{100*p/t:.0f}%" if t else "—"

        print(f"  {cfg:<5}{cov:>8.3f}{place:>8.3f}{fmt:>8.3f}"
              f"{n9:>12}{tier_frac('rock'):>10}{tier_frac('wlc_only'):>12}")
```

- [ ] **Step 2: Call summary + write JSON at the end of `main()`**

Append to the end of `main()` (after the `for cfg ...` loop):

```python
    print_summary(results)

    if args.out is not None:
        out_path = args.out or os.path.join(
            "run_logs",
            f"bakeoff_{book_chi}{args.chap}_{args.model.replace(':','_')}.json")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"book": book_chi, "chap": args.chap, "model": args.model,
                       "configs": args.configs, "results": results},
                      f, ensure_ascii=False, indent=2)
        print(f"\n  wrote {out_path}")
```

- [ ] **Step 3: Run the full Round-1 bake-off on Gen 1**

Run:
```bash
cd survey5_bilingual_sn_benchmark
python3 run_bakeoff.py --book 創 --chap 1 --model opus --configs A,B --out
```
Expected: per-verse lines for A and B across Gen 1, a SUMMARY table with cov/place/fmt/09xxx/rock/wlc_only per config, and a `wrote run_logs/bakeoff_創1_opus.json` line. (This consumes ~`2 × verses` opus calls — Gen 1 is 31 verses ≈ 62 calls; expect rate-limit pauses.)

- [ ] **Step 4: Commit plan results**

```bash
git add survey5_bilingual_sn_benchmark/run_bakeoff.py survey5_bilingual_sn_benchmark/run_logs/
git commit -m "feat(survey5): bake-off summary + JSON; Round-1 Gen1 A vs B results"
```

---

## Self-review notes

- **Spec coverage:** §3 gate → Task 2 (`gate.py`, tiers + family). §3 Stage 1 configs A/B → Tasks 3–4. §3 Stage 2 split scoring (09xxx + tier) → Task 5 summary. §4 round plan (A vs B, Gen 1) → Task 5 Step 3. §5 reuse-not-mutate → Task 1 shim + gate import. §6 model=opus constant → harness `--model` default opus, single SYSTEM across configs.
- **Deferred (separate plan, by design):** config C / BSB+SN build (§4 Round 2), YLT, answer-blind production export of tiers (§3 note). These are intentionally out of Round-1 scope.
- **Type consistency:** gate returns `{key: {"tier","family","need"}}` and `{tier: {"placed","total","frac"}}`, consumed identically in `run_config`/`print_summary`. `build_user` 7-arg signature unified in Task 4 (Task 3's lambda wrapper removed there). `score_verse` keys used: `coverage`/`placement`/`format` — matches survey5's own `print_summary`.
- **Open decisions from spec §8** were approved: R1=A vs B, opus, numbers-only gate, no verse dropped.
