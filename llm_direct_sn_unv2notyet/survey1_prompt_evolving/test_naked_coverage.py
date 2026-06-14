"""Option-2 wrinkle: R1-time SN coverage check must be naked-aware.

count_sns() requires the <W...> prefix, so on bare-number (naked) output it
matches nothing and every source SN reads as 'missing' (cosmetic MISMATCH noise
during R1). The _coverage() helper restores the naked output first, so coverage
is checked apples-to-apples (same basis as the final gold-standard check).
"""

from run_gold_standard import _coverage
from llm_direct_sn_unv2notyet import verify_sn_coverage
from shared.sn_shell import strip_shell

GEN_1_1 = (
    "起初<WAH09002><WH07225>，　神<WH0430>創造<WH01254><WTH8804>"
    "{<WH0853>}天<WH08064>{<WH0853>}地<WH0776>。"
)
# A correct naked placement carries exactly the source bare numbers.
NAKED_OUTPUT = strip_shell(GEN_1_1, markers=False)


def test_naked_coverage_is_perfect_when_all_source_sns_present():
    cov = _coverage(GEN_1_1, NAKED_OUTPUT, naked=True)
    assert cov["perfect"], cov
    assert cov["missing"] == []


def test_plain_verify_would_falsely_report_mismatch_on_naked_output():
    # Demonstrates the bug the helper fixes: direct verify sees 0 SNs in naked.
    bug = verify_sn_coverage(GEN_1_1, NAKED_OUTPUT)
    assert not bug["perfect"]          # all source SNs falsely 'missing'
    assert len(bug["missing"]) > 0


def test_naked_coverage_flags_genuinely_missing_sn():
    # Drop one SN from the naked output → should be reported missing.
    dropped = NAKED_OUTPUT.replace("<0776>", "", 1)
    cov = _coverage(GEN_1_1, dropped, naked=True)
    assert not cov["perfect"]
    assert "0776" in cov["missing"]


def test_coverage_shelled_mode_delegates_unchanged():
    # naked=False must behave exactly like verify_sn_coverage.
    assert _coverage(GEN_1_1, GEN_1_1, naked=False) == verify_sn_coverage(GEN_1_1, GEN_1_1)
