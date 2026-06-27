# test_morph.py — run: python3 test_morph.py
import morph as M


def main():
    bridge = {"vqp": 8804, "vqw": 8799}
    out = "起初<09002><07225>，神<0430>創造<01254>天地"

    # verb 創造 (lex 1254, vqp) -> morph 8804 inserted right after its lexical tag
    res = M.attach_morph(out, [(1254, "vqp")], bridge)
    assert "<01254><WTH8804>" in res, res

    # unknown form_key -> skip (no morph)
    res2 = M.attach_morph(out, [(1254, "vZZ")], bridge)
    assert "WTH" not in res2, res2

    # no anchor (verb's lexical tag absent) -> skip
    res3 = M.attach_morph(out, [(9999, "vqp")], bridge)
    assert "WTH" not in res3, res3

    # two verbs sharing a lexical number -> paired left-to-right, both attached
    out2 = "a<0559>b<0559>c"
    res4 = M.attach_morph(out2, [(559, "vqw"), (559, "vqp")], bridge)
    assert res4 == "a<0559><WTH8799>b<0559><WTH8804>c", res4

    print("test_morph OK")


if __name__ == "__main__":
    main()
