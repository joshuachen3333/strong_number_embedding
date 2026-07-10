#!/usr/bin/env python3
"""D3 objective scorer — the FHL-truth delta of a single convention.

Reuses the ALREADY-VALIDATED Stage-2 harsh objective harness (`run_stage2_harsh`):
project the WLC/aligned source onto UNV, then score the model's SN placement against
UNV's REAL FHL tags via `build_exclusion.score_placement`. This is the same objective
signal survey5/survey10 Stage-2 uses — no consensus, no answer leak.

`convention_fhl_delta(rule)` isolates ONE convention's marginal contribution: it runs
the harness with a preamble containing JUST that rule ("with") vs an empty preamble
("without") and returns mean(with) − mean(without). D3 (`conventions_mtier.falsify_
conventions`) quarantines a rule whose delta ≤ 0 — the *positive* check the non-
regression gate cannot provide.
"""

import os
import sys

S10_DIR = os.path.dirname(os.path.abspath(__file__))
if S10_DIR not in sys.path:
    sys.path.insert(0, S10_DIR)

import build_exclusion as BX
import run_a2_contest as A2
from run_stage2_harsh import (load_wlc_verse, build_wlc_source, build_harsh_prompt,
                              nines_recall)
from llm_direct_sn_unv2notyet import fetch_chap_cached, CHI_TO_ENG
from auto_score import strip_sn

# 創 → WLC book id map (Stage-2 harsh uses the same; kept local to avoid a cycle).
_WLC_BOOK = {"創": "Gen", "出": "Exod", "利": "Lev", "民": "Num", "申": "Deut"}


def _rule_preamble(rule_text):
    """A minimal one-rule preamble mirroring conventions.build_conventions_preamble
    shape, so the 'with' arm sees exactly this rule and nothing else."""
    return (
        "## Settled conventions (s10) — APPLY THIS\n"
        f"- {rule_text.strip().splitlines()[0].strip()}\n\n"
    )


def _sample_verses(book_chi, chaps):
    """Yield (wlc_book, chap, sec, unv_sn) for verses that have BOTH FHL SN and WLC."""
    book_eng = CHI_TO_ENG.get(book_chi, book_chi)
    wlc_book = _WLC_BOOK.get(book_chi)
    if not wlc_book:
        return []
    out = []
    for chap in chaps:
        try:
            recs = fetch_chap_cached(book_chi, chap, strong=1)
        except Exception:
            continue
        for r in recs:
            sec = int(r.get("sec", 0))
            unv_sn = r.get("bible_text", "")
            if sec and unv_sn and load_wlc_verse(wlc_book, chap, sec):
                out.append((wlc_book, chap, sec, unv_sn))
    return out


def _arm_score(system, verses, model, samples, verbose, label):
    """Mean placement fraction over sample verses for one system prompt (one arm)."""
    fracs = []
    for (wlc_book, chap, sec, unv_sn) in verses:
        unv_plain = strip_sn(unv_sn)
        tokens = load_wlc_verse(wlc_book, chap, sec)
        if not tokens:
            continue
        user = build_harsh_prompt(build_wlc_source(tokens), unv_plain,
                                  wlc_book, chap, sec)
        shared = BX.tag_multiset(unv_sn)[0]
        per = []
        for _ in range(samples):
            out = A2.call_guarded(system, user, model)
            if not out:
                continue          # quota-empty — drop, never score 0
            per.append(BX.score_placement(out, shared)["fraction"])
        if per:
            fracs.append(sum(per) / len(per))
            if verbose:
                print(f"    [{label}] {chap}:{sec} frac={fracs[-1]:.3f}", flush=True)
    return sum(fracs) / len(fracs) if fracs else None


def convention_fhl_delta(rule_text, model_info, target_version="unv",
                         book_chi="創", chaps=(1,), samples=1, verbose=False):
    """Objective marginal FHL-truth delta of ONE convention.

    delta = mean_placement(base + rule) − mean_placement(base). Positive ⇒ the rule
    improves FHL-faithful placement on held-out UNV; ≤ 0 ⇒ D3 quarantines it.
    Returns a float (0.0 if the sample could not be scored — treated as neutral).
    """
    model = model_info["model"] if isinstance(model_info, dict) else model_info
    verses = _sample_verses(book_chi, list(chaps))
    if not verses:
        if verbose:
            print("  [D3 delta] no scorable sample verses", flush=True)
        return 0.0
    with_sys = _rule_preamble(rule_text) + A2.SYSTEM_BASE
    without_sys = A2.SYSTEM_BASE
    with_score = _arm_score(with_sys, verses, model, samples, verbose, "with")
    without_score = _arm_score(without_sys, verses, model, samples, verbose, "without")
    if with_score is None or without_score is None:
        return 0.0
    delta = with_score - without_score
    if verbose:
        print(f"  [D3 delta] with={with_score:.3f} without={without_score:.3f} "
              f"→ Δ={delta:+.4f}", flush=True)
    return delta
