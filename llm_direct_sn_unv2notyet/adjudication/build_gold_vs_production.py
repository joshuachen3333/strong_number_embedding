#!/usr/bin/env python3
"""Score the production pipeline against the consensus gold, on the verses both cover.

Why this comparison and no other: LCC has no FHL Strong's answer key, so the
3-model consensus gold (s1 + s10) is the ONLY trustworthy LCC+SN reference that
exists. Everywhere else you can measure whether SNs *survived* (inventory
coverage against unv_sn_reference); only here can you measure whether each SN
landed on the *right word*.

Three metrics, deliberately kept separate because they fail independently:

  text_fidelity  does plain(output) == the authoritative LCC text?
                 THIS IS A GATE. A verse whose Chinese was altered is not
                 "LCC + SN" at all, and its SN placement cannot even be
                 compared, because there is no common token sequence to align.
  coverage       fraction of gold's bare numbers present anywhere in the output
  placement      fraction of gold's tags sitting at the SAME character boundary
                 (placement <= coverage; the gap is "right number, wrong place")

Gold is itself tiered and only some tiers are a legitimate answer key:
  c_consensus / c_consensus+wlc_corroborated  -> usable
  c_consensus_over_wlc_divergence             -> usable but WEAKER (consensus
                                                 overrode the Hebrew source)
  null / d_deliberation                       -> EXCLUDED (never settled;
                                                 scoring against it is scoring
                                                 against nothing)

Reads only. Writes adjudication/gold_vs_production.json.

Usage:
    python3 adjudication/build_gold_vs_production.py
    python3 adjudication/build_gold_vs_production.py --models sonnet,opus
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
LLM_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(LLM_DIR)

GOLD_SOURCES = {
    "s1": os.path.join(LLM_DIR, "survey1_prompt_evolving", "gold_standard"),
    "s10": os.path.join(LLM_DIR, "survey10_s1_but_obe_insteadOf_oneshot", "gold_standard"),
}
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")
LCC_DB = os.path.join(REPO_ROOT, "original_text_preparation", "source_sqlite", "bible_lcc.db")
DEFAULT_OUT = os.path.join(HERE, "gold_vs_production.json")

USABLE_TIERS = {"c_consensus", "c_consensus+wlc_corroborated"}
WEAK_TIERS = {"c_consensus_over_wlc_divergence"}

TAG_RE = re.compile(r"\{?<[^>]*>\}?")
PUNCT = set("，。；：、「」『』（）？！…—　 　【】《》〈〉,.;:!?()")


def plain(text):
    return TAG_RE.sub("", text or "")


def strip_punct(text):
    return "".join(c for c in text if c not in PUNCT)


def bare(tag):
    m = re.search(r"\d+", tag)
    return m.group(0).lstrip("0") or "0" if m else None


def parse_slots(text):
    """(chars, slots) — slots[i] = bare numbers sitting at character boundary i.

    Boundary 0 is before the first character; boundary len(chars) is trailing.
    This is the same representation the viewer's diff uses, and it works because
    gold and production are both LCC: identical hanzi, only SN positions move.
    """
    chars, slots = [], defaultdict(list)
    i, s = 0, str(text or "")
    while i < len(s):
        m = TAG_RE.match(s, i)
        if m:
            b = bare(m.group(0))
            if b:
                slots[len(chars)].append(b)
            i = m.end()
        else:
            chars.append(s[i])
            i += 1
    return chars, slots


def score_against_gold(gold_sn, prod_sn):
    """coverage + placement, or None when the two cannot be aligned."""
    g_chars, g_slots = parse_slots(gold_sn)
    p_chars, p_slots = parse_slots(prod_sn)
    if "".join(g_chars) != "".join(p_chars):
        return None                      # different hanzi: no common alignment

    gold_total = sum(len(v) for v in g_slots.values())
    if not gold_total:
        return None

    # placement: same number at the same boundary (multiset per boundary)
    placed = 0
    for i, nums in g_slots.items():
        have = Counter(p_slots.get(i, []))
        for n in nums:
            if have[n] > 0:
                have[n] -= 1
                placed += 1

    # coverage: same number anywhere in the verse
    g_all, p_all = Counter(), Counter()
    for v in g_slots.values():
        g_all.update(v)
    for v in p_slots.values():
        p_all.update(v)
    covered = sum(min(g_all[k], p_all[k]) for k in g_all)

    return {
        "gold_tags": gold_total,
        "placed": placed,
        "placement": round(placed / gold_total, 4),
        "covered": covered,
        "coverage": round(covered / gold_total, 4),
        "exact": plain(gold_sn) == plain(prod_sn) and gold_sn.strip() == prod_sn.strip(),
    }


def load_lcc_truth():
    """{(book, chap, sec): txt} — the authoritative LCC text, offline."""
    truth = {}
    if not os.path.exists(LCC_DB):
        return truth
    try:
        con = sqlite3.connect(f"file:{LCC_DB}?mode=ro", uri=True, timeout=5)
        try:
            for engs, chap, sec, txt in con.execute(
                    "SELECT engs, chap, sec, txt FROM lcc"):
                truth[(engs, int(chap), int(sec))] = txt
        finally:
            con.close()
    except sqlite3.Error:
        pass
    return truth


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError:
        return None, "parse_failed"
    except OSError:
        return None, "io_error"


def classify_drift(out_plain, truth):
    if out_plain == truth:
        return "faithful"
    if strip_punct(out_plain) == strip_punct(truth):
        return "punctuation_only"
    if len(out_plain) < len(truth):
        return "chars_dropped"
    if len(out_plain) > len(truth):
        return "chars_added"
    return "chars_substituted"


def collect_gold():
    """{(book, chap, sec): {survey: record}} for every gold verse that parses."""
    gold = defaultdict(dict)
    for sid, root in GOLD_SOURCES.items():
        if not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if not fn.endswith(".json"):
                    continue
                m = re.search(r"([^/]+)[/\\](\d+)[/\\](\d+)\.json$",
                              os.path.join(dirpath, fn))
                if not m:
                    continue
                key = (m.group(1), int(m.group(2)), int(m.group(3)))
                data, err = load_json(os.path.join(dirpath, fn))
                if err:
                    continue
                tier = data.get("trust_tier")
                gold[key][sid] = {
                    "survey": sid,
                    "lcc_sn": data.get("lcc_sn"),
                    "lcc_original": data.get("lcc_original"),
                    "trust_tier": tier,
                    "resolved_at": data.get("resolved_at"),
                    "key_quality": ("usable" if tier in USABLE_TIERS else
                                    "weak" if tier in WEAK_TIERS else "unusable"),
                }
    return gold


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models", default=None, help="comma list; default all")
    ap.add_argument("-o", "--output", default=DEFAULT_OUT)
    args = ap.parse_args()

    truth = load_lcc_truth()
    gold = collect_gold()
    if not gold:
        print("No gold verses found.", file=sys.stderr)
        return 1

    version_dir = os.path.join(OUTPUT_DIR, "lcc")
    if not os.path.isdir(version_dir):
        print(f"No production output at {version_dir}", file=sys.stderr)
        return 1
    models = sorted(os.listdir(version_dir))
    if args.models:
        want = {m.strip() for m in args.models.split(",")}
        models = [m for m in models if m in want]

    agg = {m: Counter() for m in models}
    place_sum = defaultdict(float)
    cov_sum = defaultdict(float)
    drift_kinds = {m: Counter() for m in models}
    verses = []

    for key in sorted(gold):
        book, chap, sec = key
        lcc_truth = truth.get(key)
        gold_variants = gold[key]

        prod = {}
        for model in models:
            path = os.path.join(version_dir, model, book, str(chap), f"{sec}.json")
            data, err = load_json(path)
            if err == "missing":
                continue
            agg[model]["overlap"] += 1
            if err:
                agg[model]["unparseable"] += 1
                prod[model] = {"model": model, "error": err}
                continue
            sn = data.get("lcc_sn") or ""
            if not sn.strip():
                agg[model]["empty"] += 1
                prod[model] = {"model": model, "error": "empty"}
                continue

            out_plain = plain(sn).strip()
            drift = classify_drift(out_plain, (lcc_truth or "").strip()) if lcc_truth else "unknown"
            drift_kinds[model][drift] += 1
            if drift == "faithful":
                agg[model]["faithful"] += 1

            entry = {
                "model": model,
                "brand": data.get("brand"),
                "lcc_sn": sn,
                "confidence": data.get("confidence"),
                "text_fidelity": drift,
                "scores": {},
            }
            for sid, g in gold_variants.items():
                if g["key_quality"] == "unusable":
                    continue
                sc = score_against_gold(g["lcc_sn"], sn)
                if sc is None:
                    agg[model][f"unalignable_vs_{sid}"] += 1
                    continue
                entry["scores"][sid] = sc
                # aggregate only on the strong key AND a faithful text
                if g["key_quality"] == "usable" and drift == "faithful":
                    agg[model][f"scored_vs_{sid}"] += 1
                    place_sum[(model, sid)] += sc["placement"]
                    cov_sum[(model, sid)] += sc["coverage"]
            prod[model] = entry

        if not prod:
            continue
        verses.append({
            "book": book, "chap": chap, "sec": sec,
            "lcc_truth": lcc_truth,
            "gold": gold_variants,
            "production": prod,
        })

    # ── aggregate table ──────────────────────────────────────────────────────
    table = []
    for model in models:
        a = agg[model]
        if not a["overlap"]:
            continue
        row = {
            "model": model,
            "overlap": a["overlap"],
            "faithful": a["faithful"],
            "faithful_pct": round(a["faithful"] / a["overlap"] * 100, 1),
            "drift": dict(drift_kinds[model]),
            "unparseable": a["unparseable"],
            "empty": a["empty"],
            "vs": {},
        }
        for sid in GOLD_SOURCES:
            n = a[f"scored_vs_{sid}"]
            if n:
                row["vs"][sid] = {
                    "n": n,
                    "mean_placement": round(place_sum[(model, sid)] / n, 4),
                    "mean_coverage": round(cov_sum[(model, sid)] / n, 4),
                    "unalignable": a[f"unalignable_vs_{sid}"],
                }
        table.append(row)

    tiers = Counter()
    for variants in gold.values():
        for g in variants.values():
            tiers[g["key_quality"]] += 1

    bundle = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "gold_verses": len(gold),
            "gold_key_quality": dict(tiers),
            "usable_tiers": sorted(USABLE_TIERS),
            "weak_tiers": sorted(WEAK_TIERS),
            "note": ("placement/coverage are aggregated ONLY over verses with a "
                     "usable gold tier AND faithful production text — a verse "
                     "whose Chinese was altered has no common alignment"),
            "leaderboard": table,
        },
        "verses": verses,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, separators=(",", ":"))

    # ── report ───────────────────────────────────────────────────────────────
    print(f"-> {args.output}  ({os.path.getsize(args.output)/1024:.0f} KB)")
    print(f"\ngold 節數 {len(gold)}  答案鑰匙品質: {dict(tiers)}")
    print("\n模型 × gold 對照(僅計「gold 可用 + 產線文字忠實」的節):")
    hdr = f"  {'model':32s} {'重疊':>5s} {'文字忠實':>9s}"
    for sid in GOLD_SOURCES:
        hdr += f" {'vs '+sid+' n':>10s} {'placement':>10s} {'coverage':>9s}"
    print(hdr)
    for row in sorted(table, key=lambda r: -r["faithful_pct"]):
        line = f"  {row['model']:32s} {row['overlap']:5d} {row['faithful_pct']:8.1f}%"
        for sid in GOLD_SOURCES:
            v = row["vs"].get(sid)
            line += (f" {v['n']:10d} {v['mean_placement']:10.4f} {v['mean_coverage']:9.4f}"
                     if v else f" {'—':>10s} {'—':>10s} {'—':>9s}")
        print(line)
    print("\n文字漂移分類:")
    for row in table:
        d = row["drift"]
        bad = sum(v for k, v in d.items() if k not in ("faithful", "punctuation_only", "unknown"))
        print(f"  {row['model']:32s} {dict(sorted(d.items()))}"
              + (f"   ← 實質損壞 {bad}" if bad else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
