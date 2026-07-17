# test_bridge_gloss.py — run: python3 test_bridge_gloss.py
import bridge_gloss as BG


def main():
    g = BG.ylt_gloss_for_verse("01", 1, 1)
    assert isinstance(g, list) and g, g
    heb, eng = g[0]
    assert heb and eng, g[0]
    joined = " ".join(e for _, e in g).lower()
    assert "beginning" in joined, joined

    b = BG.bsb_gloss_for_verse("01", 1, 1)
    assert isinstance(b, list) and b, b
    assert "beginning" in " ".join(e for _, e in b).lower(), b

    print("test_bridge_gloss OK")


if __name__ == "__main__":
    main()
