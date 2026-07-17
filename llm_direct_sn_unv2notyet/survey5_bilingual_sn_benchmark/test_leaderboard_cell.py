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

    unv_sn = "起初<WH07225>，神<WH0430>創造<WH01254><WTH8804>天地。"
    out_with = "起初<07225>，神<0430>創造<01254><WTH8804>天地。"
    out_without = "起初<07225>，神<0430>創造<01254>天地。"
    s1 = LC.score_cell_output(out_with, unv_sn)
    s2 = LC.score_cell_output(out_without, unv_sn)
    assert abs(s1["coverage"] - s2["coverage"]) < 1e-9, (s1, s2)
    assert abs(s1["placement"] - s2["placement"]) < 1e-9, (s1, s2)
    print("test morph guard OK")


if __name__ == "__main__":
    main()
