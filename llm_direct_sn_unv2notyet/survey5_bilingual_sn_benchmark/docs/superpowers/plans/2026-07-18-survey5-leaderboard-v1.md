# Survey5 Leaderboard v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a model × prompt × arm benchmark leaderboard for survey5's WLC→UNV SN-placement task, scored against FHL UNV+SN gold, including a one-off bridge ablation (`wlc`/`wlc+bsb`/`wlc+ylt`) that settles survey10's YLT question.

**Architecture:** One general matrix runner (`run_leaderboard.py`) over the frozen OT subset of `iteration_set_52.json`. Each `(model, prompt, arm)` cell runs every OT verse: compose prompt (system = a WLC-ready `prompts/survey5_wlc_*.md`; user = WLC+SN source `[+ English gloss if arm≠wlc]` + plain UNV) → call the model in an **isolated cwd** → strip morph-range tags → `attach_morph()` → score with `scoring.num_score`. Per-cell results are disk-cached and resumable; aggregation emits a ranked leaderboard + per-dimension breakdown + paired-arm delta tables as JSON and markdown. Decisions locked in the spec: (①) ranking metric excludes the deterministic morph layer; (②) OT-only (WLC).

**Tech Stack:** Python 3 (no framework), plain-assert tests run with `python3 test_*.py` (repo convention — no pytest). Reuses `wlc_bridge.py`, `scoring.py`, `gate.py`, `morph.py`, `auto_score.strip_sn`, `iteration_set_52.json`, and the Clear Bible alignment data under `../Alignments/data/eng/`.

**Spec:** `docs/superpowers/specs/2026-07-10-survey5-leaderboard-design.md`

---

## File Structure

All paths relative to `survey5_bilingual_sn_benchmark/`.

| File | Responsibility | Status |
|---|---|---|
| `prompts/survey5_wlc_v1.0_terse.md` | WLC-ready system prompt — terse (the "less is more" bet) | create |
| `prompts/survey5_wlc_v1.0_std.md` | WLC-ready system prompt — standard/explicit | create |
| `bridge_gloss.py` | Build per-Hebrew-word English gloss (YLT/BSB) from Clear Bible alignment | create |
| `build_bridge_snapshot.py` | One-time freeze of YLT/BSB glosses for the OT subset → `bridge_snapshot_52.json` | create |
| `bridge_snapshot_52.json` | Frozen glosses (generated artifact) | generated |
| `leaderboard_cell.py` | Per-`(model,prompt,arm,verse)` execution: prompt composition, isolated model call, morph guard, morph attach, scoring | create |
| `run_leaderboard.py` | Matrix driver: OT-subset load, cell cache/resume, aggregation, leaderboard + delta reports (JSON+md) | create |
| `test_bridge_gloss.py` | Unit tests for gloss lookup | create |
| `test_leaderboard_cell.py` | Unit tests for prompt composition + scoring/morph-guard | create |
| `test_leaderboard_agg.py` | Unit tests for ranking + paired-delta aggregation | create |
| `run_logs/leaderboard_cache/` | Per-cell cached JSON (generated) | generated |

Reused unchanged: `wlc_bridge.py` (`load_wlc_verse`, `build_wlc_source`, `build_harsh_prompt`, `nines_recall`, `CHI_TO_WLC_BOOK`), `scoring.py` (`num_score`, `normalize_tags`), `gate.py` (`morph_recall`, `tier_recall`), `morph.py` (`load_bridge`, `wlc_verbs_for`, `attach_morph`), `iteration_set_52.json`.

---

## Phase 1 — WLC-ready prompts

### Task 1: Author the terse WLC prompt

**Files:**
- Create: `prompts/survey5_wlc_v1.0_terse.md`

- [ ] **Step 1: Write the prompt file**

```markdown
# Survey5 WLC Prompt v1.0 terse — Original-Language SN Transfer (WLC → UNV)

You are TRANSFERRING Strong's Number (SN) tags from the Hebrew original (WLC) to UNV (Chinese 和合本) by semantic alignment. The WLC tags are ground truth — do not second-guess them.

Your job: place each bare SN number after the corresponding Chinese word in UNV.

## Rules
1. Every WLC SN number must appear in the output. Place it AFTER its Chinese word: 起初<07225>, never before.
2. UNV may need the same number more than once, or a number with no Chinese equivalent — attach the latter to the nearest governing word.
3. Output ONLY the annotated UNV text on a single line. No commentary, no code fences.
```

- [ ] **Step 2: Verify it loads**

Run: `python3 -c "print(len(open('prompts/survey5_wlc_v1.0_terse.md').read()))"`
Expected: a positive integer (file readable).

- [ ] **Step 3: Commit**

```bash
git add prompts/survey5_wlc_v1.0_terse.md
git commit -m "feat(s5-leaderboard): terse WLC-ready prompt v1.0"
```

### Task 2: Author the standard WLC prompt

**Files:**
- Create: `prompts/survey5_wlc_v1.0_std.md`

- [ ] **Step 1: Write the prompt file** (more explicit contrast to terse)

```markdown
# Survey5 WLC Prompt v1.0 std — Original-Language SN Transfer (WLC → UNV)

## Task
Project Strong's Number annotations from the tagged Hebrew original (WLC) onto the plain Chinese Union Version (UNV) by meaning-based word alignment. The Hebrew SN numbers are authoritative ground truth.

## How
For each Hebrew word `<number>`, find the Chinese word in UNV that expresses the same meaning and place `<number>` immediately AFTER it.

## Rules
1. Coverage: every SN number in the WLC source must appear in the output. A missing number is a failure.
2. Position: the tag goes AFTER the Chinese word — 神<0430>創造<01254>, never <0430>神.
3. Repetition: if one Chinese word covers two Hebrew words, place both numbers after it, source order preserved.
4. No-equivalent numbers (Hebrew particles with no Chinese surface word): attach to the nearest governing Chinese word.
5. Output ONLY the annotated UNV text on one line. No explanation, no code fences, no extra whitespace.
```

- [ ] **Step 2: Verify it loads**

Run: `python3 -c "print(len(open('prompts/survey5_wlc_v1.0_std.md').read()))"`
Expected: positive integer.

- [ ] **Step 3: Commit**

```bash
git add prompts/survey5_wlc_v1.0_std.md
git commit -m "feat(s5-leaderboard): standard WLC-ready prompt v1.0"
```

> Note: v1 ships these two prompts (terse vs explicit — directly tests survey5's "less is more" finding on WLC). Adding more is just another `prompts/survey5_wlc_*.md` file + a `--prompts` entry; no code change.

---

## Phase 2 — Bridge gloss builder

### Task 3: `bridge_gloss.py` — YLT gloss lookup

**Files:**
- Create: `bridge_gloss.py`
- Test: `test_bridge_gloss.py`

Data facts (verified): `../Alignments/data/eng/alignments/YLT/WLC-YLT-manual.json` has
`records: [{"source": ["o01001001001…"], "target": ["01001001001"], …}]` (WLC morpheme
ids → YLT word ids). `../Alignments/data/eng/targets/YLT/ot_YLT.tsv` columns:
`id  altId  text  transType  isPunc  isPrimary`. WLC token id (from `../Alignments/data/sources/WLC.tsv`,
col `id`) format `o` + book(2) + chap(3) + verse(3) + word(3) + part(1); verse key =
`id[1:9]` = book+chap+verse.

- [ ] **Step 1: Write the failing test**

```python
# test_bridge_gloss.py — run: python3 test_bridge_gloss.py
import bridge_gloss as BG


def main():
    # Gen 1:1 (wlc_book="01", chap=1, sec=1) must produce a non-empty per-word gloss
    g = BG.ylt_gloss_for_verse("01", 1, 1)
    assert isinstance(g, list) and g, g
    # each entry: (hebrew_text, english_gloss)
    heb, eng = g[0]
    assert heb and eng, g[0]
    # "beginning" should surface somewhere in the verse gloss
    joined = " ".join(e for _, e in g).lower()
    assert "beginning" in joined, joined
    print("test_bridge_gloss OK")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 test_bridge_gloss.py`
Expected: FAIL (`ModuleNotFoundError: bridge_gloss` or `AttributeError`).

- [ ] **Step 3: Implement `bridge_gloss.py`**

```python
# bridge_gloss.py — per-Hebrew-word English gloss from Clear Bible alignment. No LLM.
import json
import os
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
_ALIGN = os.path.abspath(os.path.join(_HERE, "..", "Alignments", "data", "eng"))
_WLC_TSV = os.path.abspath(os.path.join(_HERE, "..", "Alignments", "data", "sources", "WLC.tsv"))

_ylt_text = None          # {ylt_id: text}
_wlc_to_ylt = None        # {wlc_id: [ylt_id, ...]}
_wlc_rows = None          # {verse_key: [(wlc_id, hebrew_text), ...]}


def _load_ylt_text():
    global _ylt_text
    if _ylt_text is not None:
        return _ylt_text
    _ylt_text = {}
    path = os.path.join(_ALIGN, "targets", "YLT", "ot_YLT.tsv")
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idi, txi = header.index("id"), header.index("text")
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) > max(idi, txi):
                _ylt_text[c[idi]] = c[txi]
    return _ylt_text


def _load_alignment():
    global _wlc_to_ylt
    if _wlc_to_ylt is not None:
        return _wlc_to_ylt
    _wlc_to_ylt = defaultdict(list)
    path = os.path.join(_ALIGN, "alignments", "YLT", "WLC-YLT-manual.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for rec in data["records"]:
        for s in rec["source"]:
            for t in rec["target"]:
                _wlc_to_ylt[s].append(t)
    return _wlc_to_ylt


def _load_wlc_rows():
    global _wlc_rows
    if _wlc_rows is not None:
        return _wlc_rows
    _wlc_rows = defaultdict(list)
    with open(_WLC_TSV, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idi, txi = header.index("id"), header.index("text")
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) <= max(idi, txi):
                continue
            wid = c[idi]                 # e.g. o01001001001...
            vkey = wid[1:9]              # book(2)+chap(3)+verse(3)
            _wlc_rows[vkey].append((wid, c[txi]))
    return _wlc_rows


def ylt_gloss_for_verse(wlc_book, chap, sec):
    """[(hebrew_text, english_gloss)] for each WLC token in the verse (source order)."""
    ylt = _load_ylt_text()
    align = _load_alignment()
    rows = _load_wlc_rows()
    vkey = f"{int(wlc_book):02d}{int(chap):03d}{int(sec):03d}"
    out = []
    for wid, heb in rows.get(vkey, []):
        eng = " ".join(ylt.get(t, "") for t in align.get(wid, [])).strip()
        out.append((heb, eng))
    return out
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 test_bridge_gloss.py`
Expected: `test_bridge_gloss OK`

- [ ] **Step 5: Commit**

```bash
git add bridge_gloss.py test_bridge_gloss.py
git commit -m "feat(s5-leaderboard): YLT gloss builder from Clear Bible alignment"
```

### Task 4: Add BSB gloss to `bridge_gloss.py`

**Files:**
- Modify: `bridge_gloss.py`
- Test: `test_bridge_gloss.py`

BSB alignment (`alignments/BSB/WLCM-BSB-manual.json`) uses **WLCM** source ids, which differ
from WLC ids. Reconcile by strong's+position: build the WLCM verse rows the same way, map
WLCM id→WLC id by matching (verse_key, ordinal). BSB is the expected-harmful, secondary arm.

- [ ] **Step 1: Add failing test for BSB**

```python
    # append inside main(), before the print:
    b = BG.bsb_gloss_for_verse("01", 1, 1)
    assert isinstance(b, list) and b, b
    assert "beginning" in " ".join(e for _, e in b).lower(), b
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 test_bridge_gloss.py`
Expected: FAIL (`AttributeError: module 'bridge_gloss' has no attribute 'bsb_gloss_for_verse'`).

- [ ] **Step 3: Implement `bsb_gloss_for_verse`** by reconciling WLCM→WLC by verse-ordinal

```python
# add to bridge_gloss.py
_wlcm_rows = None
_wlcm_to_bsb = None
_bsb_text = None


def _load_generic_target(name):
    out = {}
    path = os.path.join(_ALIGN, "targets", name, f"ot_{name}.tsv")
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idi, txi = header.index("id"), header.index("text")
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) > max(idi, txi):
                out[c[idi]] = c[txi]
    return out


def _load_wlcm_rows():
    global _wlcm_rows
    if _wlcm_rows is not None:
        return _wlcm_rows
    _wlcm_rows = defaultdict(list)
    path = os.path.abspath(os.path.join(_HERE, "..", "Alignments", "data", "sources", "WLCM.tsv"))
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        idi = header.index("id")
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) > idi:
                _wlcm_rows[c[idi][1:9] if c[idi][0].isalpha() else c[idi][:8]].append(c[idi])
    return _wlcm_rows


def bsb_gloss_for_verse(wlc_book, chap, sec):
    global _wlcm_to_bsb, _bsb_text
    if _bsb_text is None:
        _bsb_text = _load_generic_target("BSB")
    if _wlcm_to_bsb is None:
        _wlcm_to_bsb = defaultdict(list)
        path = os.path.join(_ALIGN, "alignments", "BSB", "WLCM-BSB-manual.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for rec in data["records"]:
            for s in rec["source"]:
                for t in rec["target"]:
                    _wlcm_to_bsb[s].append(t)
    wlc_rows = _load_wlc_rows()
    wlcm_rows = _load_wlcm_rows()
    vkey = f"{int(wlc_book):02d}{int(chap):03d}{int(sec):03d}"
    wlc_v = wlc_rows.get(vkey, [])
    wlcm_v = wlcm_rows.get(vkey, [])
    out = []
    for i, (wid, heb) in enumerate(wlc_v):
        wlcm_id = wlcm_v[i] if i < len(wlcm_v) else None
        eng = ""
        if wlcm_id:
            eng = " ".join(_bsb_text.get(t, "") for t in _wlcm_to_bsb.get(wlcm_id, [])).strip()
        out.append((heb, eng))
    return out
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 test_bridge_gloss.py`
Expected: `test_bridge_gloss OK`. If BSB reconciliation is imperfect for some verses, the test still passes on Gen 1:1; note any mismatch counts in the snapshot builder (Task 5).

- [ ] **Step 5: Commit**

```bash
git add bridge_gloss.py test_bridge_gloss.py
git commit -m "feat(s5-leaderboard): BSB gloss via WLCM→WLC ordinal reconciliation"
```

---

## Phase 3 — Freeze the glosses

### Task 5: `build_bridge_snapshot.py`

**Files:**
- Create: `build_bridge_snapshot.py`

- [ ] **Step 1: Write the snapshot builder**

```python
#!/usr/bin/env python3
"""Freeze YLT+BSB glosses for the OT subset of iteration_set_52.json. No LLM.
Run: python3 build_bridge_snapshot.py
"""
import json
import os
import bridge_gloss as BG
import wlc_bridge as W

_HERE = os.path.dirname(os.path.abspath(__file__))
ITER = os.path.join(_HERE, "iteration_set_52.json")
OUT = os.path.join(_HERE, "bridge_snapshot_52.json")


def main():
    verses = json.load(open(ITER, encoding="utf-8"))["verses"]
    ot = [v for v in verses if v.get("testament") == "OT"]
    snap = {}
    missing = 0
    for v in ot:
        wlc_book = W.CHI_TO_WLC_BOOK.get(v["book_chi"])
        if not wlc_book:
            missing += 1
            continue
        key = f'{v["book_chi"]}|{v["chap"]}|{v["sec"]}'
        snap[key] = {
            "ylt": BG.ylt_gloss_for_verse(wlc_book, v["chap"], v["sec"]),
            "bsb": BG.bsb_gloss_for_verse(wlc_book, v["chap"], v["sec"]),
        }
    json.dump(snap, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(snap)} OT verses ({missing} skipped, no WLC book)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python3 build_bridge_snapshot.py`
Expected: `wrote …/bridge_snapshot_52.json: N OT verses (…)` with N > 0.

- [ ] **Step 3: Commit**

```bash
git add build_bridge_snapshot.py bridge_snapshot_52.json
git commit -m "feat(s5-leaderboard): freeze YLT/BSB glosses for OT subset"
```

---

## Phase 4 — Per-cell executor

### Task 6: `leaderboard_cell.py` — prompt composition

**Files:**
- Create: `leaderboard_cell.py`
- Test: `test_leaderboard_cell.py`

- [ ] **Step 1: Write the failing test for `compose_user`**

```python
# test_leaderboard_cell.py — run: python3 test_leaderboard_cell.py
import leaderboard_cell as LC


def main():
    wlc_source = "בְּרֵאשִׁית<07225> בָּרָא<01254>"
    unv_plain = "起初，神創造天地。"
    gloss = [("בְּרֵאשִׁית", "In the beginning"), ("בָּרָא", "created")]

    base = LC.compose_user("wlc", wlc_source, unv_plain, None, "Gen", 1, 1)
    assert wlc_source in base and unv_plain in base, base
    assert "In the beginning" not in base, "wlc arm must not leak gloss"

    ylt = LC.compose_user("wlc+ylt", wlc_source, unv_plain, gloss, "Gen", 1, 1)
    assert "In the beginning" in ylt and "created" in ylt, ylt
    assert wlc_source in ylt and unv_plain in ylt, ylt
    print("test compose_user OK")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 test_leaderboard_cell.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement `compose_user`**

```python
# leaderboard_cell.py — per-(model,prompt,arm,verse) execution. Reuses Round-2 primitives.
import os
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for p in (_PARENT, os.path.join(_PARENT, "survey4_self_supervised_prompt_tuning")):
    if p not in sys.path:
        sys.path.insert(0, p)

import scoring          # noqa: E402
import gate as G        # noqa: E402
import morph as M       # noqa: E402


def _gloss_block(label, gloss):
    lines = [f"{label} (English, per Hebrew word; annotation only — copy no tags):"]
    for heb, eng in gloss:
        if eng:
            lines.append(f"  {heb} → {eng}")
    return "\n".join(lines)


def compose_user(arm, wlc_source, unv_plain, gloss, book_eng, chap, sec):
    """User message: WLC+SN source [+ English gloss if arm≠wlc] + plain UNV."""
    parts = [
        f"Here is {book_eng} {chap}:{sec} in the Hebrew original (WLC), each word tagged "
        f"with its Strong's Number:",
        "",
        wlc_source,
    ]
    if arm == "wlc+ylt" and gloss:
        parts += ["", _gloss_block("YLT literal gloss", gloss)]
    elif arm == "wlc+bsb" and gloss:
        parts += ["", _gloss_block("BSB gloss", gloss)]
    parts += [
        "",
        "Here is the same verse in UNV (和合本), plain, no annotations:",
        "",
        unv_plain,
        "",
        "Place the Strong's Number tags into the correct positions in the UNV text. "
        "Output ONLY the annotated UNV text on a single line.",
    ]
    return "\n".join(parts)
```

- [ ] **Step 4: Run to verify it passes**

Run: `python3 test_leaderboard_cell.py`
Expected: `test compose_user OK`

- [ ] **Step 5: Commit**

```bash
git add leaderboard_cell.py test_leaderboard_cell.py
git commit -m "feat(s5-leaderboard): arm-aware prompt composition"
```

### Task 7: `leaderboard_cell.py` — morph guard + scoring

**Files:**
- Modify: `leaderboard_cell.py`
- Test: `test_leaderboard_cell.py`

Decision ①: strip morph-range tags from raw output in ALL arms before `num_score`, then
`attach_morph()` runs on the stripped output (morph column stays the deterministic constant).
Morph range = canonical H8675–H8999 after `scoring.normalize_tags` (which collapses `WTH…`→`H…`).

- [ ] **Step 1: Add failing test for the morph guard**

```python
    # append to main() before print:
    unv_sn = "起初<WH07225>，神<WH0430>創造<WH01254><WTH8804>天地。"
    out_with = "起初<07225>，神<0430>創造<01254><WTH8804>天地。"
    out_without = "起初<07225>，神<0430>創造<01254>天地。"
    s1 = LC.score_cell_output(out_with, unv_sn)
    s2 = LC.score_cell_output(out_without, unv_sn)
    assert abs(s1["coverage"] - s2["coverage"]) < 1e-9, (s1, s2)
    assert abs(s1["placement"] - s2["placement"]) < 1e-9, (s1, s2)
    print("test morph guard OK")
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 test_leaderboard_cell.py`
Expected: FAIL (`AttributeError: … score_cell_output`).

- [ ] **Step 3: Implement `score_cell_output`** (strip morph → num_score)

```python
# add to leaderboard_cell.py
import re
_MORPH = re.compile(r"<H(\d{3,4})>")   # applied AFTER normalize_tags


def _strip_morph(text):
    def repl(m):
        n = int(m.group(1))
        return "" if 8675 <= n <= 8999 else m.group(0)
    return _MORPH.sub(repl, scoring.normalize_tags(text))


def score_cell_output(model_output, unv_sn):
    """Headline cov/place on morph-stripped, normalized output (decision ①)."""
    stripped = _strip_morph(model_output)
    gold = _strip_morph(unv_sn)
    return scoring.score_verse(stripped, gold)
```

> `scoring.num_score` normalizes then calls `score_verse`; here we normalize+strip on both
> sides ourselves and call `score_verse` directly to avoid double-normalizing.

- [ ] **Step 4: Run to verify it passes**

Run: `python3 test_leaderboard_cell.py`
Expected: `test compose_user OK` / `test morph guard OK`

- [ ] **Step 5: Commit**

```bash
git add leaderboard_cell.py test_leaderboard_cell.py
git commit -m "feat(s5-leaderboard): morph-guarded headline scoring (decision 1)"
```

### Task 8: `leaderboard_cell.py` — isolated model call + `run_cell_verse`

**Files:**
- Modify: `leaderboard_cell.py`

Isolated cwd is mandatory (Round-2 contamination bug). No unit test (needs a live model);
covered by the Phase 6 smoke test.

- [ ] **Step 1: Implement the isolated caller + per-verse orchestration**

```python
# add to leaderboard_cell.py
from auto_score import strip_sn                    # noqa: E402
from run_survey5 import call_model, detect_brand   # noqa: E402

_ISO_DIR = None


def _iso_dir():
    global _ISO_DIR
    if _ISO_DIR is None:
        _ISO_DIR = tempfile.mkdtemp(prefix="s5_leaderboard_iso_")
    return _ISO_DIR


def _call_isolated(model, brand, system, user, timeout=600):
    if brand == "claude":
        r = subprocess.run(["claude", "--model", model, "-p", f"{system}\n\n{user}"],
                           capture_output=True, text=True, timeout=timeout, cwd=_iso_dir())
        return r.stdout.strip()
    return call_model(model, brand, None, system, user)


def run_cell_verse(model, brand, system_prompt, arm, wlc_source, unv_sn, gloss,
                   morph_bridge, book_eng, wlc_book2, chap, sec):
    """Run one verse for one (model,prompt,arm) cell → score dict or None on empty."""
    unv_plain = strip_sn(unv_sn)
    user = compose_user(arm, wlc_source, unv_plain, gloss, book_eng, chap, sec)
    out = _call_isolated(model, brand, system_prompt, user)
    if not out:
        return None
    out = M.attach_morph(out, M.wlc_verbs_for(wlc_book2, chap, sec), morph_bridge)
    score = score_cell_output(out, unv_sn)
    n9p, n9t = __import__("wlc_bridge").nines_recall(out, unv_sn)
    mp, mt = G.morph_recall(out, unv_sn)
    return {"score": score, "n9_placed": n9p, "n9_total": n9t,
            "morph_placed": mp, "morph_total": mt, "output": out}
```

- [ ] **Step 2: Smoke-check import**

Run: `python3 -c "import leaderboard_cell"`
Expected: no error.

- [ ] **Step 3: Commit**

```bash
git add leaderboard_cell.py
git commit -m "feat(s5-leaderboard): isolated per-verse cell execution"
```

---

## Phase 5 — Matrix runner + aggregation

### Task 9: `run_leaderboard.py` — aggregation (pure, TDD)

**Files:**
- Create: `run_leaderboard.py`
- Test: `test_leaderboard_agg.py`

- [ ] **Step 1: Write the failing test**

```python
# test_leaderboard_agg.py — run: python3 test_leaderboard_agg.py
import run_leaderboard as RL


def _cell(model, prompt, arm, cov, place, dim=1):
    return {"model": model, "prompt": prompt, "arm": arm,
            "verses": [{"dim": dim, "score": {"coverage": cov, "placement": place}}]}


def main():
    cells = [
        _cell("opus", "terse", "wlc", 0.80, 0.75),
        _cell("sonnet", "terse", "wlc", 0.60, 0.55),
        _cell("opus", "terse", "wlc+ylt", 0.83, 0.78),
    ]
    board = RL.rank_cells(cells)
    assert board[0]["model"] == "opus" and board[0]["arm"] == "wlc+ylt", board
    assert board[-1]["model"] == "sonnet", board

    deltas = RL.paired_deltas(cells, base_arm="wlc")
    d = [x for x in deltas if x["model"] == "opus" and x["arm"] == "wlc+ylt"][0]
    assert abs(d["dcov"] - 0.03) < 1e-9 and abs(d["dplace"] - 0.03) < 1e-9, d
    print("test aggregation OK")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 test_leaderboard_agg.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement the pure aggregation functions**

```python
#!/usr/bin/env python3
"""run_leaderboard.py — survey5 model×prompt×arm leaderboard over the OT-52 subset."""
import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))


def _cell_means(cell):
    vs = cell["verses"]
    n = len(vs) or 1
    return (sum(v["score"]["coverage"] for v in vs) / n,
            sum(v["score"]["placement"] for v in vs) / n)


def rank_cells(cells):
    """Sort cells by headline (placement, then coverage) descending."""
    scored = []
    for c in cells:
        cov, place = _cell_means(c)
        scored.append({**c, "cov": cov, "place": place})
    return sorted(scored, key=lambda c: (c["place"], c["cov"]), reverse=True)


def paired_deltas(cells, base_arm="wlc"):
    """For each (model,prompt), Δcov/Δplace of every non-base arm vs base_arm."""
    by_key = {(c["model"], c["prompt"], c["arm"]): _cell_means(c) for c in cells}
    out = []
    for (model, prompt, arm), (cov, place) in by_key.items():
        if arm == base_arm:
            continue
        base = by_key.get((model, prompt, base_arm))
        if not base:
            continue
        out.append({"model": model, "prompt": prompt, "arm": arm,
                    "dcov": cov - base[0], "dplace": place - base[1]})
    return out
```

- [ ] **Step 4: Run to verify it passes**

Run: `python3 test_leaderboard_agg.py`
Expected: `test aggregation OK`

- [ ] **Step 5: Commit**

```bash
git add run_leaderboard.py test_leaderboard_agg.py
git commit -m "feat(s5-leaderboard): pure ranking + paired-delta aggregation"
```

### Task 10: `run_leaderboard.py` — cache key + cell cache

**Files:**
- Modify: `run_leaderboard.py`
- Test: `test_leaderboard_agg.py`

- [ ] **Step 1: Add failing test for the cache key**

```python
    # append to main():
    k1 = RL.cell_key("opus", "prompts/survey5_wlc_v1.0_terse.md", "wlc")
    k2 = RL.cell_key("opus", "prompts/survey5_wlc_v1.0_terse.md", "wlc+ylt")
    assert k1 != k2 and k1.endswith(".json"), (k1, k2)
    print("test cache key OK")
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 test_leaderboard_agg.py`
Expected: FAIL (`AttributeError: … cell_key`).

- [ ] **Step 3: Implement `cell_key` + load/save**

```python
# add to run_leaderboard.py
CACHE_DIR = os.path.join(_HERE, "run_logs", "leaderboard_cache")


def _hash_file(path):
    try:
        return hashlib.sha1(open(path, "rb").read()).hexdigest()[:8]
    except OSError:
        return "nofile"


def cell_key(model, prompt_path, arm, iter_hash="", snap_hash=""):
    mm = model.replace(":", "-").replace("/", "-")
    pv = os.path.basename(prompt_path).replace(".md", "")
    ph = _hash_file(prompt_path)
    arm_data = snap_hash if arm != "wlc" else ""
    return f"{mm}__{pv}-{ph}__{arm}{('-' + arm_data) if arm_data else ''}__{iter_hash}.json"


def load_cell(key):
    p = os.path.join(CACHE_DIR, key)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def save_cell(key, cell):
    os.makedirs(CACHE_DIR, exist_ok=True)
    json.dump(cell, open(os.path.join(CACHE_DIR, key), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
```

- [ ] **Step 4: Run to verify it passes**

Run: `python3 test_leaderboard_agg.py`
Expected: `test aggregation OK` / `test cache key OK`

- [ ] **Step 5: Commit**

```bash
git add run_leaderboard.py test_leaderboard_agg.py
git commit -m "feat(s5-leaderboard): resumable per-cell disk cache"
```

### Task 11: `run_leaderboard.py` — driver `main()` + markdown report

**Files:**
- Modify: `run_leaderboard.py`

Wires everything: load OT subset, loop `models × prompts × arms`, per cell run verses
(skip cached), aggregate, write JSON + markdown. No unit test (I/O + live models); Phase 6
smoke covers it.

- [ ] **Step 1: Implement `run_cell` and `main`**

```python
# add to run_leaderboard.py
import leaderboard_cell as LC
import wlc_bridge as W
import morph as M
from run_survey5 import fetch_chap_cached  # noqa: E402
from auto_score import strip_sn            # noqa: E402

ITER = os.path.join(_HERE, "iteration_set_52.json")
SNAP = os.path.join(_HERE, "bridge_snapshot_52.json")


def _ot_verses():
    vs = json.load(open(ITER, encoding="utf-8"))["verses"]
    return [v for v in vs if v.get("testament") == "OT"]


def run_cell(model, prompt_path, arm, verses, snap, morph_bridge, iter_hash, snap_hash):
    key = cell_key(model, prompt_path, arm, iter_hash, snap_hash)
    cached = load_cell(key)
    if cached:
        print(f"  [cache] {key}")
        return cached
    system_prompt = open(prompt_path, encoding="utf-8").read().strip()
    brand = LC.detect_brand(model, None)
    _unv_cache = {}
    rows = []
    for v in verses:
        bc, chap, sec = v["book_chi"], v["chap"], v["sec"]
        wlc_book = W.CHI_TO_WLC_BOOK.get(bc)
        if not wlc_book:
            continue
        kk = (bc, chap)
        if kk not in _unv_cache:
            _unv_cache[kk] = fetch_chap_cached(bc, chap, "unv", strong=1)
        unv_sn = _unv_cache[kk].get(sec)
        if not unv_sn:
            continue
        wlc_source = W.build_wlc_source(W.load_wlc_verse(wlc_book, chap, sec))
        if not wlc_source:
            continue
        gloss = None
        if arm != "wlc":
            skey = f"{bc}|{chap}|{sec}"
            g = snap.get(skey, {})
            gloss = g.get("ylt" if arm == "wlc+ylt" else "bsb")
            if not gloss:
                print(f"    skip {v['ref']} (no gloss for {arm})")
                continue
        r = LC.run_cell_verse(model, brand, system_prompt, arm, wlc_source, unv_sn,
                              gloss, morph_bridge, v["book"], wlc_book, chap, sec)
        if r is None:
            print(f"    {v['ref']} EMPTY")
            continue
        r.update({"ref": v["ref"], "dim": v["dim"]})
        rows.append(r)
        print(f"    {v['ref']:12s} cov={r['score']['coverage']:.2f} place={r['score']['placement']:.2f}")
    cell = {"model": model, "prompt": os.path.basename(prompt_path), "arm": arm, "verses": rows}
    save_cell(key, cell)
    return cell


def per_dim_winners(board):
    """For each dim, the (model,prompt,arm) cell with the best mean placement on it."""
    best = {}
    for c in board:
        dim_place = defaultdict(list)
        for v in c["verses"]:
            dim_place[v["dim"]].append(v["score"]["placement"])
        for dim, ps in dim_place.items():
            mp = sum(ps) / len(ps)
            label = f"{c['model']}/{c['prompt']}/{c['arm']}"
            if dim not in best or mp > best[dim][1]:
                best[dim] = (label, mp)
    return best


def write_report(board, deltas, out_base):
    dim_win = per_dim_winners(board)
    json.dump({"leaderboard": board, "deltas": deltas, "per_dim_winners": dim_win},
              open(out_base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    lines = ["# Survey5 Leaderboard\n", "| rank | model | prompt | arm | cov | place | n |",
             "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(board, 1):
        lines.append(f"| {i} | {c['model']} | {c['prompt']} | {c['arm']} | "
                     f"{c['cov']:.3f} | {c['place']:.3f} | {len(c['verses'])} |")
    lines += ["\n## Per-dimension winners\n", "| dim | winning cell | place |",
              "|---|---|---|"]
    for dim in sorted(dim_win):
        label, mp = dim_win[dim]
        lines.append(f"| {dim} | {label} | {mp:.3f} |")
    if deltas:
        lines += ["\n## Paired arm deltas (vs wlc)\n",
                  "| model | prompt | arm | Δcov | Δplace |", "|---|---|---|---|---|"]
        for d in deltas:
            lines.append(f"| {d['model']} | {d['prompt']} | {d['arm']} | "
                         f"{d['dcov']:+.3f} | {d['dplace']:+.3f} |")
    open(out_base + ".md", "w", encoding="utf-8").write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description="Survey5 model×prompt×arm leaderboard (OT-52)")
    ap.add_argument("--models", required=True, help="comma list, e.g. opus,sonnet")
    ap.add_argument("--prompts", required=True, help="comma list of prompts/*.md paths")
    ap.add_argument("--arms", default="wlc", help="comma list: wlc,wlc+bsb,wlc+ylt")
    ap.add_argument("--out", default=os.path.join(_HERE, "run_logs", "leaderboard"))
    args = ap.parse_args()

    verses = _ot_verses()
    snap = json.load(open(SNAP, encoding="utf-8")) if os.path.exists(SNAP) else {}
    morph_bridge = M.load_bridge()
    iter_hash = _hash_file(ITER)
    snap_hash = _hash_file(SNAP)

    models = [x.strip() for x in args.models.split(",") if x.strip()]
    prompts = [x.strip() for x in args.prompts.split(",") if x.strip()]
    arms = [x.strip() for x in args.arms.split(",") if x.strip()]

    cells = []
    for model in models:
        for prompt_path in prompts:
            for arm in arms:
                print(f"\n== {model} × {os.path.basename(prompt_path)} × {arm} ==")
                cells.append(run_cell(model, prompt_path, arm, verses, snap,
                                      morph_bridge, iter_hash, snap_hash))

    board = rank_cells(cells)
    deltas = paired_deltas(cells, base_arm="wlc")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    write_report(board, deltas, args.out)
    print(f"\nwrote {args.out}.json / .md")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-check import + arg parsing**

Run: `python3 run_leaderboard.py --help`
Expected: argparse usage prints, no import error.

- [ ] **Step 3: Commit**

```bash
git add run_leaderboard.py
git commit -m "feat(s5-leaderboard): matrix driver + markdown report"
```

---

## Phase 6 — End-to-end smoke

### Task 12: One-cell live smoke

**Files:** none (verification only).

- [ ] **Step 1: Run one tiny cell** (1 model × 1 prompt × 1 arm; the runner still sweeps the OT-52, so interrupt after a few verses is fine, or trust the cache)

Run:
```bash
python3 run_leaderboard.py --models sonnet \
  --prompts prompts/survey5_wlc_v1.0_terse.md --arms wlc \
  --out run_logs/leaderboard_smoke
```
Expected: per-verse `cov=… place=…` lines; then `wrote …/leaderboard_smoke.json / .md`. A
cache file appears under `run_logs/leaderboard_cache/`.

- [ ] **Step 2: Verify resume** — rerun the same command.
Expected: `[cache] …` line (cell served from disk, no model calls).

- [ ] **Step 3: Verify the bridge-ablation delta path** (small, paired)

Run:
```bash
python3 run_leaderboard.py --models sonnet \
  --prompts prompts/survey5_wlc_v1.0_terse.md --arms wlc,wlc+ylt \
  --out run_logs/leaderboard_smoke_ablation
```
Expected: the `.md` has a "Paired arm deltas (vs wlc)" table with a `wlc+ylt` row.

- [ ] **Step 4: Commit any run_logs you want to keep** (optional)

```bash
git add run_logs/leaderboard_smoke*.md run_logs/leaderboard_smoke*.json
git commit -m "test(s5-leaderboard): smoke run + resume + ablation verified"
```

---

## Notes for the implementer

- **Token-burn awareness**: a shared account may be under concurrent load (survey10 gold runs). Isolated `claude -p` calls hit rate limits; the existing callers back off. Phases 1–5 are **zero-LLM** — do them first regardless of quota.
- **Isolated cwd is non-negotiable** (Task 8) — running the model in this repo dir makes it inherit `CLAUDE.md` + `/ph`//`logoutput` skills and behave as an agent instead of annotating.
- **Ranking excludes morph** (Task 7) and the **default arm is `wlc`** — do not rank on morph or treat a bridge arm as the production default.
- **Report to survey10**: after a real run with `--arms wlc,wlc+ylt` on the headline model(s), read the paired-delta table; if `wlc+ylt` Δplace > 0 robustly, flare survey10-obe (per spec §Bridge ablation reading table).
- **BSB reconciliation** (Task 4) is ordinal-based and may be imperfect; BSB is the secondary/expected-harmful arm, so YLT is the result that matters.
