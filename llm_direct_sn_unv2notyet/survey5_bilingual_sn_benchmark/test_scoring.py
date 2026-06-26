# test_scoring.py — run: python3 test_scoring.py
import scoring as S


def main():
    # bare model output vs FHL-shell gold — same numbers, same positions.
    out = "起初<09002><07225>，神<0430>創造天<08064>地<0776>"
    gold = "起初<WAH09002><WH07225>，神<WH0430>創造天<WH08064>地<WH0776>"

    # normalisation collapses both to the same canonical string
    canon = "起初<H9002><H7225>，神<H430>創造天<H8064>地<H776>"
    assert S.normalize_tags(out) == canon, S.normalize_tags(out)
    assert S.normalize_tags(gold) == canon, S.normalize_tags(gold)

    # format-agnostic score: bare-but-correct output now scores ~perfect coverage
    sc = S.num_score(out, gold)
    assert sc["coverage"] > 0.99, sc
    assert sc["placement"] > 0.99, sc

    # a genuine miss (dropped the 09xxx) still costs coverage
    miss = "起初<07225>，神<0430>創造天<08064>地<0776>"
    sc2 = S.num_score(miss, gold)
    assert sc2["coverage"] < sc["coverage"], (sc2, sc)

    print("test_scoring OK", round(sc["coverage"], 3), round(sc["placement"], 3))


if __name__ == "__main__":
    main()
