#!/usr/bin/env python3
"""build_exclusion.py — Stage-1 (FHL-internal, zero model cost) exclusion builder.

Part of the A2 s1-vs-s10 contest scaffolding (see S10_VS_S1_GOLD_EXPERIMENT.md,
"A2 scoring — two-stage divide-and-conquer"). Stage 1 settles the placement
verdict on the *content-word core* only, by excluding the SN tags UNV carries
that the KJV source cannot supply (the inseparable Hebrew prefixes, etc.).

Per verse, comparing UNV+SN against KJV+SN (both from FHL, same numbering):

    shared   = UNV-FHL  ∩  KJV-FHL     (multiset)   -> kept_set, the scored core
    excluded = UNV-FHL  −  KJV-FHL     (multiset)   -> reported, NOT scored

This is purely FHL reads (no LLM), so it is free and deterministic. Its job is
diagnostic: CONFIRM that the excluded tags really are the prefix/09xxx/obj-marker
families before any paid contest, and emit `kept_set[verse]` for the Stage-1
scorer `score_placement()`.

Tag identity is the bare Strong's NUMBER, family-agnostic: key = (testament, norm).
In naked mode the model transfers a bare number, so a number is "fairly supplyable"
iff that number appears in the KJV source — regardless of whether UNV tags it with
an 'A'-augment (attached-to-particle form WAH…) or a morph 'T'. Intersection is
therefore number-level; `family` is used ONLY to classify the excluded instances
for the report:
    prefix_09  : 5-digit 09xxx inseparable particle (ב/ל/כ/…) — KJV structurally
                 CANNOT carry these (English has no such token); always excluded
    morph      : a 'T'-tagged stem/tense code (WTH8799 …) — FHL morphology namespace
    obj_marker : 0853 (את, the untranslatable direct-object marker)
    core       : an ordinary content-word Strong's number

Critical correction (vs an earlier draft that keyed identity on family): the
'A'-augment letter must NOT make a normal number (1961 היה, 834 אשר, 3605 כל,
5921 על …) count as a prefix — those numbers ARE in KJV as plain WH… tags and so
belong in the kept core. Only the true 5-digit 09xxx range is KJV-impossible.
Empirically (Gen 1:1) the lone UNV-only tag is then WAH09002 (the ב prefix).

Usage:
    python3 build_exclusion.py --book 創 --chap 1
    python3 build_exclusion.py --book 創 --chap 1-5 --json kept_set.json
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

# Reuse the driver's FHL fetch (User-Agent header, caching) instead of re-rolling.
_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)
from llm_direct_sn_unv2notyet import fetch_chap_cached  # noqa: E402

# FHL SN tag:  <W? [augment/morph letters] [HG testament] digits [a-z suffix] >
# Surrounding {}/() wrappers are ignored — the inner <W…> is what we match.
# Non-SN formatting tags (<FI>, <Fi>, <CM>, …) carry no digits and never match.
_TAG_RE = re.compile(r"<\s*W?([A-Za-z]*?)(\d{2,5})([a-z]?)\s*>")

FAMILIES = ("prefix_09", "obj_marker", "morph", "core_function", "core_content")

# Hebrew FUNCTION-word Strong's numbers that English routinely drops/merges, so
# FHL's KJV annotation lacks them where UNV carries them (existential היה, the
# quantifier כל, prepositions, conjunctions, relative/demonstrative particles).
# An excluded number in this set is a STRUCTURAL drop (expected, fair to exclude);
# an excluded number OUTSIDE it is a potential real content-word leak to inspect.
# Empirically derived from Gen 1 + the common Genesis particle inventory.
HEBREW_FUNCTION_WORDS = {
    1961,   # היה  to be / existential "there was"
    3605,   # כל   all / every
    5921,   # על   upon / on
    996,    # בין  between
    3651,   # כן   so / thus
    3588,   # כי   for / that / because
    834,    # אשר  which / that (relative)
    4480,   # מן   from
    2009,   # הנה  behold
    8478,   # תחת  under
    413,    # אל   to / toward
    5973,   # עם   with
    854,    # את   with (companion-את, distinct from obj-marker 853)
    1571,   # גם   also
    3808,   # לא   not
    518,    # אם   if
    2088,   # זה   this
    1931,   # הוא  he / it
    4994,   # נא   please / now (particle)
    6310,   # פה   mouth / according to
    1115,   # בלתי except
    # Added from the Gen 1-5 corpus scan (all closed-class function words):
    8033,   # שם   there (adverb)
    4100,   # מה   what / why (interrogative)
    859,    # אתה  you (2ms pronoun)
    595,    # אנכי I (1cs pronoun)
    5048,   # נגד  before / opposite (preposition)
    2063,   # זאת  this (f. demonstrative)
    6258,   # עתה  now (adverb)
    905,    # בד   alone / by-itself (in לבד)
    5668,   # עבור for the sake of
    6435,   # פן   lest (conjunction)
    2005,   # הן   behold / if (particle)
    227,    # אז   then (adverb)
    369,    # אין  there-is-not (negative existential)
}


def classify(letters, num):
    """Return (testament, norm, family) for one FHL tag's parsed pieces.

    norm = testament + int(number) (+ a/b suffix handled by caller). Identity for
    intersection is (testament, norm) — family-agnostic. family is report-only.
    """
    letters = letters.upper()
    testament = letters[-1] if letters and letters[-1] in "HG" else "H"
    markers = letters[:-1] if letters and letters[-1] in "HG" else letters
    n_int = int(num)               # strips zero-padding: 09002 -> 9002, 0853 -> 853

    if len(num) == 5 and num.startswith("09"):
        family = "prefix_09"       # true inseparable particle — KJV-impossible
    elif "T" in markers:
        family = "morph"           # FHL morphology code namespace
    elif n_int == 853:
        family = "obj_marker"
    elif n_int in HEBREW_FUNCTION_WORDS:
        family = "core_function"   # English routinely drops these (fair to exclude)
    else:
        family = "core_content"    # real content word — leak here would be unfair
    return testament, n_int, family


def tag_multiset(text):
    """Return (counts, fam) where counts: (testament,norm)->n, fam: same->family."""
    counts = Counter()
    fam = {}
    if not text:
        return counts, fam
    for letters, num, suffix in _TAG_RE.findall(text):
        testament, n_int, family = classify(letters, num)
        key = (testament, f"{testament}{n_int}{suffix}")
        counts[key] += 1
        fam.setdefault(key, family)
    return counts, fam


def verse_split(unv_text, kjv_text):
    """Return (shared, excluded_by_fam, unv_total).

    shared            : Counter (testament,norm) -> kept count (number-level min)
    excluded_by_fam   : Counter family -> UNV-only excess count
    unv_total         : total UNV tags
    """
    unv, unv_fam = tag_multiset(unv_text)
    kjv, _ = tag_multiset(kjv_text)
    shared = unv & kjv            # number-level multiset intersection
    excess = unv - kjv            # number-level UNV-only excess (Counter)
    excluded_by_fam = Counter()
    excluded_keys = Counter()
    for key, n in excess.items():
        fam = unv_fam.get(key, "core")
        excluded_by_fam[fam] += n
        excluded_keys[f"{fam}:{key[1]}"] += n
    return shared, excluded_by_fam, excluded_keys, sum(unv.values())


def score_placement(model_output, shared):
    """Stage-1 score: how much of the kept (number-level) set did the model emit.

    `shared` is the (testament,norm) Counter from verse_split. Scores number
    presence restricted to the kept core — excluded UNV-only tags are neither
    required nor penalized. NOTE: true *positional* placement (right tag on the
    right token) defers to survey4/auto_score.py; this is the cheap kept-set
    coverage check used to sanity-rank arms before the full scorer runs.
    """
    out, _ = tag_multiset(model_output)
    placed = total = 0
    for key, need in shared.items():
        total += need
        placed += min(need, out.get(key, 0))
    frac = placed / total if total else 1.0
    return {"placed": placed, "total": total, "fraction": frac}


def parse_chap_arg(chap):
    if "-" in chap:
        a, b = chap.split("-", 1)
        return list(range(int(a), int(b) + 1))
    if "," in chap:
        return [int(x) for x in chap.split(",") if x.strip()]
    return [int(chap)]


def main():
    ap = argparse.ArgumentParser(description="Stage-1 FHL-internal exclusion builder")
    ap.add_argument("--book", default="創", help="Chinese book abbrev (default 創)")
    ap.add_argument("--chap", default="1", help="Chapter '1', '1-5', or '1,3'")
    ap.add_argument("--json", help="Write kept_set + excluded to this JSON path")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="Print per-verse excluded tags")
    args = ap.parse_args()

    chaps = parse_chap_arg(args.chap)
    fam_excluded = Counter()        # family -> total excluded instances
    fam_shared = Counter()          # family -> total shared instances
    excluded_keys = Counter()       # "family:norm" -> count (which numbers excluded)
    out_json = {"book": args.book, "verses": {}}
    n_verses = 0
    verses_with_exclusion = 0

    for chap in chaps:
        unv = fetch_chap_cached(args.book, chap, "unv", strong=1)
        kjv = fetch_chap_cached(args.book, chap, "kjv", strong=1)
        secs = sorted(set(unv) & set(kjv))
        for sec in secs:
            shared, ex_by_fam, ex_keys, unv_total = verse_split(unv[sec], kjv[sec])
            _, unv_fam = tag_multiset(unv[sec])
            n_verses += 1
            if sum(ex_by_fam.values()):
                verses_with_exclusion += 1
            for key, cnt in shared.items():
                fam_shared[unv_fam.get(key, "core")] += cnt
            fam_excluded.update(ex_by_fam)
            excluded_keys.update(ex_keys)
            vkey = f"{chap}:{sec}"
            out_json["verses"][vkey] = {
                "kept": [[k[1], unv_fam.get(k, "core"), c] for k, c in shared.items()],
                "excluded_by_family": dict(ex_by_fam),
            }
            if args.verbose and sum(ex_by_fam.values()):
                ex = ", ".join(f"{k}×{c}" for k, c in ex_keys.most_common())
                print(f"  {vkey:>6}  excluded: {ex}")

    # ── Report ──
    total_shared = sum(fam_shared.values())
    total_excluded = sum(fam_excluded.values())
    print("\n" + "=" * 60)
    print(f"  Stage-1 exclusion report — {args.book} chap {args.chap}")
    print("=" * 60)
    print(f"  verses analysed         : {n_verses}")
    print(f"  verses with exclusions  : {verses_with_exclusion}")
    print(f"  shared (kept) tags total: {total_shared}")
    print(f"  excluded (UNV-only) total: {total_excluded}")
    if total_shared + total_excluded:
        pct = 100 * total_excluded / (total_shared + total_excluded)
        print(f"  excluded fraction of UNV: {pct:.1f}%")
    print("\n  excluded by family:")
    for fam in FAMILIES:
        c = fam_excluded.get(fam, 0)
        if c:
            print(f"    {fam:<11}: {c}")
    print("\n  shared by family:")
    for fam in FAMILIES:
        c = fam_shared.get(fam, 0)
        if c:
            print(f"    {fam:<11}: {c}")
    print("\n  top excluded numbers:")
    for key, cnt in excluded_keys.most_common(12):
        print(f"    {key:<18}: {cnt}")

    # The kept set is fair BY CONSTRUCTION: shared = min(unv, kjv) per number, so
    # every KJV-supplied instance (up to UNV's count) is kept; excluded is strictly
    # UNV's *excess*. So nothing the source could supply is ever omitted. The split
    # below just characterises WHY each excess instance is unsupplyable:
    #   prefix_09 / obj_marker / morph / core_function = structural drop (English
    #     has no token, or KJV annotation merges it) — the bulk.
    #   core_content = a content lemma UNV tagged MORE times than KJV (count
    #     mismatch, e.g. repeated 神/上帝 where English used a pronoun). Still fair
    #     to exclude — the source genuinely lacks that extra instance — but worth
    #     eyeballing to confirm none is a mis-classified function word.
    content_excess = fam_excluded.get("core_content", 0)
    if total_excluded:
        struct_share = 100 * (total_excluded - content_excess) / total_excluded
        print(f"\n  structural drops = {struct_share:.1f}% of excluded; "
              f"content-lemma count-excess = {content_excess} "
              f"({100*content_excess/total_excluded:.1f}%)")
        print("  -> kept set fair by construction (shared = min); "
              "excess is unsupplyable from KJV either way")

    if args.json:
        out_json["summary"] = {
            "n_verses": n_verses,
            "excluded_by_family": dict(fam_excluded),
            "shared_by_family": dict(fam_shared),
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(out_json, f, ensure_ascii=False, indent=2)
        print(f"\n  wrote kept_set/excluded -> {args.json}")


if __name__ == "__main__":
    main()
