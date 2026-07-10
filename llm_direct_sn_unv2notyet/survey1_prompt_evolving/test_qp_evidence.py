"""Unit tests for qp_evidence (parsing/QP_ENRICHMENT_PLAN.md §3).

FIXTURE-ONLY: no network, no SQLite, no LLM — exercises the pure functions
validate_morph_attachment / is_verb_record / format_qp_evidence.

Run from survey1_prompt_evolving/:  python3 -m pytest test_qp_evidence.py -v
"""

from qp_evidence import (
    format_qp_evidence, is_verb_record, validate_morph_attachment,
)

# Gen 1:1-style OT fixture — the shape build_qp_table() returns.
QP_GEN_1_1 = [
    {"wid": 1, "word": "בְּרֵאשִׁית", "orig": "רֵאשִׁית", "sn": "WH07225",
     "pro": None, "wform": "介系詞 בְּ + 名詞，陰性單數", "exp": "開始、首要"},
    {"wid": 2, "word": "בָּרָא", "orig": "בָּרָא", "sn": "WH01254",
     "pro": None, "wform": "動詞，Qal 完成式 3 單陽", "exp": "創造"},
    {"wid": 3, "word": "אֱלֹהִים", "orig": "אֱלֹהִים", "sn": "WH0430",
     "pro": None, "wform": "名詞，陽性複數", "exp": "上帝、神"},
    {"wid": 4, "word": "אֵת", "orig": "אֵת", "sn": "WH0853",
     "pro": None, "wform": "受詞記號", "exp": "不必翻譯"},
]


def test_correct_attachment_passes():
    text = "起初<WH07225>，上帝<WH0430>創造<WH01254><WTH8804>天地"
    assert validate_morph_attachment(text, QP_GEN_1_1) == []


def test_morph_before_any_sn_fails():
    text = "創造<WTH8804><WH01254>上帝<WH0430>"
    errs = validate_morph_attachment(text, QP_GEN_1_1)
    assert len(errs) == 1
    assert errs[0]["code"] == "morph_before_any_sn"


def test_morph_after_non_verb_sn_fails():
    text = "起初<WH07225>上帝<WH0430><WTH8804>創造<WH01254>"
    errs = validate_morph_attachment(text, QP_GEN_1_1)
    assert len(errs) == 1
    assert errs[0]["code"] == "morph_after_non_verb_sn"
    assert errs[0]["attached_to"] == "<WH0430>"
    assert "WH01254" in errs[0]["expected_verb_sns"]


def test_verse_with_no_morph_codes_passes():
    text = "起初<WH07225>上帝<WH0430>創造<WH01254>天地"
    assert validate_morph_attachment(text, QP_GEN_1_1) == []


def test_morph_separated_by_text_fails_not_adjacent():
    text = "創造<WH01254>天<WTH8804>"
    errs = validate_morph_attachment(text, QP_GEN_1_1)
    assert len(errs) == 1
    assert errs[0]["code"] == "morph_not_adjacent"
    assert errs[0]["gap"] == "天"


def test_morph_chain_after_verb_passes():
    text = "創造<WH01254><WTH8804><WTH8752>"
    assert validate_morph_attachment(text, QP_GEN_1_1) == []


def test_braced_morph_token_is_recognized():
    text = "上帝<WH0430>{<WTH8804>}創造<WH01254>"
    errs = validate_morph_attachment(text, QP_GEN_1_1)
    assert len(errs) == 1
    assert errs[0]["code"] == "morph_after_non_verb_sn"


def test_900x_prefix_is_meaning_stream_not_morph():
    # WAH09002 (900x prefix) is a meaning-stream token, not a morph code.
    text = "起初<WAH09002><WH07225>創造<WH01254><WTH8804>"
    assert validate_morph_attachment(text, QP_GEN_1_1) == []
    bad = "起初<WAH09002><WTH8804>創造<WH01254>"
    errs = validate_morph_attachment(bad, QP_GEN_1_1)
    assert len(errs) == 1
    assert errs[0]["code"] == "morph_after_non_verb_sn"


def test_no_verb_in_qp_skips_verb_check_but_keeps_adjacency():
    no_verb = [r for r in QP_GEN_1_1 if "動詞" not in (r["wform"] or "")]
    ok = "上帝<WH0430><WTH8804>"        # verb-sense not judgeable → no error
    assert validate_morph_attachment(ok, no_verb) == []
    bad = "上帝<WH0430>天<WTH8804>"      # adjacency still enforced
    errs = validate_morph_attachment(bad, no_verb)
    assert len(errs) == 1
    assert errs[0]["code"] == "morph_not_adjacent"


def test_snless_verb_record_skips_verb_check_but_keeps_adjacency():
    # Data-gap conservatism (§11.4 qb/qp SN disagreement): a verb-sense record
    # whose sn is empty makes the true anchor invisible — morph_after_non_verb_sn
    # must NOT fire even though other verbs are listed. Adjacency still enforced.
    with_snless_verb = QP_GEN_1_1 + [
        {"wid": 5, "word": "וַיֹּאמֶר", "orig": "אָמַר", "sn": None,
         "pro": None, "wform": "動詞，Qal 敘述式 3 單陽", "exp": "說"},
    ]
    ok = "上帝<WH0430><WTH8804>創造<WH01254>"   # would fail without the skip
    assert validate_morph_attachment(ok, with_snless_verb) == []
    bad = "上帝<WH0430>天<WTH8804>"              # adjacency still enforced
    errs = validate_morph_attachment(bad, with_snless_verb)
    assert len(errs) == 1
    assert errs[0]["code"] == "morph_not_adjacent"


def test_empty_qp_records_returns_no_errors():
    assert validate_morph_attachment("創造<WH01254><WTH8804>", []) == []


def test_nt_verb_detection_across_sources():
    sqlite_rec = {"wid": 3, "word": "ἠγάπησεν", "orig": "ἀγαπάω",
                  "sn": "WG0025", "pro": "v", "wform": "aai3s", "exp": "愛"}
    api_rec = {"wid": 3, "word": "ἠγάπησεν", "orig": "ἀγαπάω", "sn": "WG0025",
               "pro": "動詞", "wform": "第一簡單過去 主動 直說語氣 第三人稱 單數",
               "exp": "愛"}
    article = {"wid": 4, "word": "ὁ", "orig": "ὁ ἡ τό", "sn": "WG03588",
               "pro": "ra", "wform": "nsm", "exp": "這"}
    assert is_verb_record(sqlite_rec)
    assert is_verb_record(api_rec)
    assert not is_verb_record(article)


def test_format_qp_evidence_empty_returns_empty_string():
    # "" keeps the judge prompt byte-for-byte identical (template contract).
    assert format_qp_evidence([]) == ""
    assert format_qp_evidence(None) == ""


def test_format_qp_evidence_block_contract_and_content():
    block = format_qp_evidence(QP_GEN_1_1)
    assert block.startswith("\n") and block.endswith("\n")
    assert "WH01254" in block
    assert "[VERB]" in block
    assert "בָּרָא" in block


def test_format_qp_evidence_renders_prevalidator_findings():
    findings = {"A": [], "B": validate_morph_attachment(
        "上帝<WH0430><WTH8804>創造<WH01254>", QP_GEN_1_1)}
    block = format_qp_evidence(QP_GEN_1_1, findings)
    assert "Output A: OK" in block
    assert "Output B: 1 violation(s)" in block


def test_format_qp_evidence_empty_findings_no_dangling_header():
    # findings dict with no entries (all candidates lacked text) must not
    # render a dangling pre-validator header with zero output lines.
    block = format_qp_evidence(QP_GEN_1_1, {})
    assert "Deterministic morph pre-validator" not in block
