"""Step 3 (存檔還殼) — consensus naked restore post-pass.

In --naked mode build_gold_standard collects bare-number winning text into
lcc_sn; a post-pass at the end restores the original FHL shell by table lookup
from unv_sn_reference, keeps the naked copy in lcc_sn_naked, and flags §2.1
same-number-different-shell nodes for human review. resolved_at logic untouched.
"""

from consensus import _restore_gold_shells


def _entry(lcc_sn, unv_sn_reference, resolved_at="round1"):
    return {
        "book": "Gen", "chap": 1, "sec": 1,
        "lcc_sn": lcc_sn,
        "lcc_original": "起初上帝创造天地",
        "unv_sn_reference": unv_sn_reference,
        "resolved_at": resolved_at,
    }


def test_restore_shells_turns_naked_lcc_sn_into_shelled_and_keeps_naked():
    # Naked winning text (bare numbers placed on LCC) + shelled source reference.
    gold = {(1, 1): _entry(
        lcc_sn="起初<09002><07225>上帝<0430>创造<01254><8804>天地",
        unv_sn_reference="起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>天地",
    )}
    flagged = _restore_gold_shells(gold)

    g = gold[(1, 1)]
    assert g["lcc_sn_naked"] == "起初<09002><07225>上帝<0430>创造<01254><8804>天地"
    assert g["lcc_sn"] == "起初<WAH09002><WH07225>上帝<WH0430>创造<WH01254><WTH8804>天地"
    assert flagged == []  # no same-number-different-shell here


def test_restore_shells_does_not_touch_resolved_at_or_other_fields():
    gold = {(1, 1): _entry(
        lcc_sn="天<08064>",
        unv_sn_reference="天<WH08064>地",
        resolved_at="round3",
    )}
    _restore_gold_shells(gold)
    assert gold[(1, 1)]["resolved_at"] == "round3"
    assert gold[(1, 1)]["lcc_original"] == "起初上帝创造天地"


def test_restore_shells_flags_same_number_different_shell_for_review():
    # 0853 appears as plain and braced in the source → §2.1 boundary.
    gold = {(1, 2): _entry(
        lcc_sn="甲<0853>乙<0853>",
        unv_sn_reference="甲<WH0853>乙{<WH0853>}",
    )}
    flagged = _restore_gold_shells(gold)
    assert (1, 2) in [vk for vk, _num in flagged]
    assert any(num == "0853" for _vk, num in flagged)


def test_restore_shells_leaves_unknown_number_bare_as_red_flag():
    # LLM emitted an SN not present in the source → stays bare for human/judge.
    gold = {(1, 1): _entry(
        lcc_sn="天<08064>幻觉<99999>",
        unv_sn_reference="天<WH08064>",
    )}
    _restore_gold_shells(gold)
    assert "<99999>" in gold[(1, 1)]["lcc_sn"]
    assert gold[(1, 1)]["lcc_sn"].startswith("天<WH08064>")


def test_restore_shells_skips_entries_with_empty_lcc_sn():
    # Trigger1 verses store lcc_sn="" — must not crash, no naked copy needed.
    gold = {(1, 9): _entry(lcc_sn="", unv_sn_reference="天<WH08064>")}
    _restore_gold_shells(gold)
    assert gold[(1, 9)]["lcc_sn"] == ""
