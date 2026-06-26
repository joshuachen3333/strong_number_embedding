# test_gate.py — run: python3 test_gate.py
import gate as G


def main():
    # gold tags: H9002 (09xxx, WLC-only), 4 content words (rock), H1234 (no source),
    # H8804 (FHL morph code: KJV carries it, the WLC bridge drops it -> kjv_only).
    unv = "<09002><07225><0430><8064><0776><1234><8804>"
    wlc = "<09002><07225><0430><8064><0776>"          # no H1234, no morph H8804
    kjv = "<07225><0430><8064><0776><8804>"            # drops 09xxx; keeps morph H8804

    tiers = G.gold_tiers(unv, wlc, kjv)
    by = {k[1]: v["tier"] for k, v in tiers.items()}
    assert by["H9002"] == "wlc_only", by
    assert by["H7225"] == "rock", by
    assert by["H1234"] == "orphan", by
    assert by["H8804"] == "kjv_only", by

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
