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
    scored = []
    for c in cells:
        cov, place = _cell_means(c)
        scored.append({**c, "cov": cov, "place": place})
    return sorted(scored, key=lambda c: (c["place"], c["cov"]), reverse=True)


def paired_deltas(cells, base_arm="wlc"):
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


def per_dim_winners(board):
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


_PARENT = os.path.dirname(_HERE)
for _p in (_HERE, os.path.join(_HERE, "..", "survey4_self_supervised_prompt_tuning")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import leaderboard_cell as LC                # noqa: E402
import wlc_bridge as W                        # noqa: E402
import morph as M                             # noqa: E402
from run_survey5 import fetch_chap_cached     # noqa: E402
from auto_score import strip_sn               # noqa: E402

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
