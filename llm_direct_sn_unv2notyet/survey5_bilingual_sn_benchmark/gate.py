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

    Returns {key: {"tier": rock|wlc_only|kjv_only|orphan, "family": str, "need": int}}.
    key is build_exclusion's (testament, "H<n>") tuple.

    Four tiers, because neither source is a superset of the other: KJV drops the
    09xxx prefixes + function words English merges away, while the WLC->FHL bridge
    drops FHL morphology codes (>8674, e.g. verb-stem 8804) that KJV/FHL do carry.
      rock     : in WLC and KJV  (content words, multi-witness)
      wlc_only : in WLC, not KJV (09xxx prefixes + dropped function words)
      kjv_only : in KJV, not WLC (FHL morphology codes the bridge omits)
      orphan   : in neither (gold tag no source supplies)
    """
    gold, fam = BX.tag_multiset(unv_sn)
    wlc, _ = BX.tag_multiset(wlc_sn)
    kjv, _ = BX.tag_multiset(kjv_sn)
    tiers = {}
    for key, need in gold.items():
        in_w = wlc.get(key, 0) > 0
        in_k = kjv.get(key, 0) > 0
        if in_w and in_k:
            tier = "rock"
        elif in_w:
            tier = "wlc_only"
        elif in_k:
            tier = "kjv_only"
        else:
            tier = "orphan"
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
