#!/usr/bin/env python3
"""wlc_check.py — the ONE shared, importable WLC identity-axis signal per verse.

Lifted out of eval_gold_vs_wlc.py per the WLC-INTO-S1 design
(survey1_prompt_evolving/WLC_INTO_S1_DESIGN.md §1). Both consumers use this single
primitive:
  - s10  : post-hoc gold eval (eval_gold_vs_wlc.py).
  - s1   : in-loop consensus escalator (Phase A) + R3 evidence (Phase B).

WLC (Clear Bible's manual Hebrew alignment) is the IDENTITY axis ONLY — which
Strong's numbers / original-lemma identity. It is structurally BLIND to placement
(which Chinese token gets the tag): WLC has no Chinese. This module therefore emits
IDENTITY-AXIS SIGNALS ONLY — it never speaks to placement.

Contract (design §1, enriched):

    wlc_check(book_chi, chap, sec, fhl_sn) -> {
      "status":   "match" | "divergence" | "no_signal",
      "coverage": float,          # fraction of FHL numbers WLC could speak to
      "divergences": [
         { "side": "fhl_only" | "wlc_only",
           "bare_num": "H0120",
           "family": "core_content" | "core_function" | "obj_marker"
                     | "morph" | "prefix_09",
           "kind": "methodology_divergence_logged" | "unresolved" | "expected_drop",
           # wlc-side evidence (present on wlc_only items, and on fhl_only items
           # when a candidate WLC substitution exists at the same family):
           "wlc_lemma": str | None,
           "wlc_strong": str | None,
           "source_token": str | None },
        ...],
    }

`fhl_sn` is ANY FHL-tagged string — the primitive is agnostic to its provenance:
  - s1 pre-R1 pre-pass : pass the UNV+SN reference inventory (the FHL source).
  - post-hoc eval      : pass the gold's lcc_sn.

`status` is the escalation gate Phase A consumes:
  - "divergence"  iff >=1 *unresolved* CONTENT-identity divergence exists
                  (FHL carries a content number the Hebrew lacks, and it is NOT
                  already ruled in FHL_DIVERGENCE_LOG). -> Phase A: wlc_contested.
  - "match"       FHL inventory consistent with WLC, OR every divergence is an
                  already-ruled methodology_divergence (2:20 etc.). -> wlc_corroborated.
  - "no_signal"   WLC has no rows for this verse. -> fall back to pure consensus.

Ruled cases (FHL_DIVERGENCE_LOG) return kind=methodology_divergence_logged and do
NOT trip `status="divergence"` — so 2:20 (D1) never re-escalates.

NOTE on the contract vs the design: the design sketched one merged divergence record
with both fhl_tag and wlc_lemma. A multiset diff has no positional alignment, so we
honestly emit two sides — `fhl_only` (FHL has it, Hebrew doesn't) and `wlc_only`
(Hebrew has it, FHL dropped it) — each carrying the evidence it can. For the common
substitution (2:20: FHL H0120 vs WLC H0121 on the same אדם), the judge reads the
fhl_only(H0120) + wlc_only(H0121, lemma אדם, token) pair together. Positional pairing
can be a Phase-B enrichment if the judge needs it.
"""

import json
import os
import re
import sys
from collections import Counter

_S10 = os.path.dirname(os.path.abspath(__file__))
_S5 = os.path.join(os.path.dirname(_S10), "survey5_bilingual_sn_benchmark")
if _S10 not in sys.path:
    sys.path.insert(0, _S10)

import build_exclusion as BX          # noqa: E402  (_TAG_RE, classify, family sets)
import run_stage2_harsh as S2         # noqa: E402  (WLC loader, _bridge_number)

# s5's WLC-morph -> FHL-8xxx table (import the data; never mutate s5's files).
with open(os.path.join(_S5, "morph_bridge.json"), encoding="utf-8") as _f:
    MORPH_BRIDGE = json.load(_f)        # form_key (e.g. "vqp") -> 8804

# Same Hebrew particle, different FHL-vs-WLC numbering -> canonicalise both sides.
EQUIV = {"H9006": "H4480", "H3509": "H9003"}

# Canonical list of FHL-vs-WLC methodology divergences — FHL-faithful tags that
# legitimately differ from WLC original-language morphology (NOT gold errors). s1 is
# the authority; this primitive only READS the ledger.
DIVERGENCE_LOG = os.path.join(
    os.path.dirname(_S10), "survey1_prompt_evolving", "FHL_DIVERGENCE_LOG.md")

# Chinese abbrev -> WLC 2-digit book number (mirrors run_stage2_harsh).
CHI_TO_WLC_BOOK = S2.CHI_TO_WLC_BOOK


def load_divergences(path=DIVERGENCE_LOG):
    """Parse '## D<n> — Gen C:V … H<fhl> (FHL) vs H<wlc> (WLC)' -> {(chap,sec,'H<fhl>')}."""
    out = set()
    if not os.path.isfile(path):
        return out
    hdr = re.compile(r"^##\s*D\d+\s*—\s*Gen\s*(\d+):(\d+).*?H0*(\d+)\s*\(FHL\)", re.I)
    with open(path, encoding="utf-8") as f:
        for ln in f:
            m = hdr.match(ln.strip())
            if m:
                out.add((int(m.group(1)), int(m.group(2)), f"H{int(m.group(3))}"))
    return out


def _canon(c):
    out = Counter()
    for (t, norm), n in c.items():
        out[(t, EQUIV.get(norm, norm))] += n
    return out


def fhl_sn_multiset(fhl_sn):
    """SN multiset (testament, canon-norm) from ANY FHL-tagged string — morph INCLUDED.

    n==0 (unmarked) is DROPPED — mirrors run_stage2_harsh._bridge_number; a `<0>` is
    noise, not an identity, and must never trip the escalator.
    """
    c = Counter()
    for letters, num, suffix in BX._TAG_RE.findall(fhl_sn or ""):
        testament, n_int, _ = BX.classify(letters, num)
        if n_int == 0:
            continue
        c[(testament, f"{testament}{n_int}{suffix}")] += 1
    return _canon(c)


def _wlc_rows(wlc_book, chap, sec):
    S2.load_wlc_verse(wlc_book, chap, sec)             # populate S2._WLC_CACHE
    return S2._WLC_CACHE.get(wlc_book, {}).get((chap, sec), [])


def wlc_sn_detail(wlc_book, chap, sec):
    """Return (multiset, evidence) for one verse.

    multiset  : Counter {(testament, canon-norm): count}  (lexical+prefix+morph)
    evidence  : dict canon-norm -> list of {lemma, strongs, token}  (WLC-side detail)
    """
    c = Counter()
    ev = {}

    def _add(norm, lemma, strongs, token):
        c[("H", norm)] += 1
        ev.setdefault(norm, []).append(
            {"lemma": lemma, "strongs": strongs, "token": token})

    for row in _wlc_rows(wlc_book, chap, sec):
        num = S2._bridge_number(row["lemma"], row["strongs"], row["pos"])
        if num:
            _add(f"H{int(num)}", row["lemma"], row["strongs"], row.get("text"))
        if row["pos"] == "verb":
            code = MORPH_BRIDGE.get(row["morph"][:3])
            if code:
                _add(f"H{int(code)}", row["lemma"], row.get("morph"), row.get("text"))
    # canonicalise the multiset keys; remap evidence to the canon key too.
    cc = _canon(c)
    cev = {}
    for norm, items in ev.items():
        cev.setdefault(EQUIV.get(norm, norm), []).extend(items)
    return cc, cev


def family_of(key_norm):
    """Identity family of a canon key like 'H120' / 'H9002' / 'H8804'."""
    n = int(re.match(r"[HG](\d+)", key_norm).group(1))
    if n >= 9000:
        return "prefix_09"
    if 8674 < n < 9000:
        return "morph"
    if n == 853:
        return "obj_marker"
    if n in BX.HEBREW_FUNCTION_WORDS:
        return "core_function"
    return "core_content"


# families whose FHL-only presence is an IDENTITY problem worth escalating; the rest
# (prefix/morph/obj_marker/function) commonly drop in translation and never escalate.
_ESCALATING = {"core_content"}


def wlc_check(book_chi, chap, sec, fhl_sn, divergences=None):
    """The shared per-verse WLC identity signal. See module docstring for the contract."""
    wlc_book = CHI_TO_WLC_BOOK.get(book_chi)
    if divergences is None:
        divergences = load_divergences()

    fhl = fhl_sn_multiset(fhl_sn)
    if wlc_book is None:
        return {"status": "no_signal", "coverage": 0.0, "divergences": [],
                "note": f"no WLC book mapped for {book_chi}"}
    wlc, wlc_ev = wlc_sn_detail(wlc_book, chap, sec)
    if not wlc:
        return {"status": "no_signal", "coverage": 0.0, "divergences": []}

    fhl_total = sum(fhl.values())
    shared = sum((fhl & wlc).values())
    coverage = (shared / fhl_total) if fhl_total else 0.0

    divs = []
    unresolved_content = 0
    for key, cnt in (fhl - wlc).items():        # FHL has it, Hebrew lacks it
        norm = key[1]
        fam = family_of(norm)
        if fam in _ESCALATING:
            logged = (chap, sec, norm) in divergences
            kind = "methodology_divergence_logged" if logged else "unresolved"
            if not logged:
                unresolved_content += cnt
        else:
            kind = "expected_drop"
        # best-effort WLC-side substitution evidence: any wlc_only item of same family
        cand = None
        for wkey in (wlc - fhl):
            if family_of(wkey[1]) == fam and wlc_ev.get(wkey[1]):
                cand = wlc_ev[wkey[1]][0]
                break
        divs.append({"side": "fhl_only", "bare_num": norm, "family": fam, "kind": kind,
                     "count": cnt,
                     "wlc_lemma": cand["lemma"] if cand else None,
                     "wlc_strong": cand["strongs"] if cand else None,
                     "source_token": cand["token"] if cand else None})
    for key, cnt in (wlc - fhl).items():        # Hebrew has it, FHL dropped it
        norm = key[1]
        item = (wlc_ev.get(norm) or [{}])[0]
        divs.append({"side": "wlc_only", "bare_num": norm,
                     "family": family_of(norm), "kind": "expected_drop", "count": cnt,
                     "wlc_lemma": item.get("lemma"), "wlc_strong": item.get("strongs"),
                     "source_token": item.get("token")})

    status = "divergence" if unresolved_content else "match"
    return {"status": status, "coverage": round(coverage, 4), "divergences": divs}


def _selftest(book_chi="創", chap_range="1-2"):
    """Smoke: run against the current gold to confirm the primitive matches eval."""
    import build_exclusion as _BX
    gold_dir = os.path.join(_S10, "gold_standard", "Gen")
    if not os.path.isdir(gold_dir):
        print("no gold_standard/Gen — skip selftest"); return
    divergences = load_divergences()
    n = contested = corroborated = no_sig = 0
    for chap in _BX.parse_chap_arg(chap_range):
        gdir = os.path.join(gold_dir, str(chap))
        if not os.path.isdir(gdir):
            continue
        for fn in sorted(os.listdir(gdir), key=lambda x: int(x.split(".")[0])):
            sec = int(fn.split(".")[0])
            gold = json.load(open(os.path.join(gdir, fn)))
            r = wlc_check(book_chi, chap, sec, gold.get("lcc_sn", ""), divergences)
            n += 1
            contested += r["status"] == "divergence"
            corroborated += r["status"] == "match"
            no_sig += r["status"] == "no_signal"
            if r["status"] == "divergence":
                ex = [d["bare_num"] for d in r["divergences"]
                      if d["side"] == "fhl_only" and d["kind"] == "unresolved"]
                print(f"  {chap}:{sec}  CONTESTED  unresolved={ex}")
    print(f"\n  {n} verses: corroborated(match)={corroborated}  "
          f"contested(divergence)={contested}  no_signal={no_sig}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="WLC per-verse identity signal (shared primitive)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--book", default="創")
    ap.add_argument("--chap", default="1-2")
    a = ap.parse_args()
    if a.selftest:
        _selftest(a.book, a.chap)
    else:
        ap.print_help()
