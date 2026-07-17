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
