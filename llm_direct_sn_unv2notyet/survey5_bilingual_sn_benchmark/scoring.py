# scoring.py — format-agnostic ("naked") scoring for the bake-off.
#
# The model emits bare tags like <7225> / <09002>; FHL gold wears the shell
# <WH07225> / <WAH09002>. auto_score.score_verse compares format-strictly, so a
# correct placement in the wrong shell scores 0 coverage (survey8's lesson). We
# normalise BOTH sides to a canonical <H{n}> form first, so cov/place measure the
# numbers-in-position, not the shell (which is a zero-loss table-restore step).
import os
import re
import sys

_S4 = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "survey4_self_supervised_prompt_tuning")
)
if _S4 not in sys.path:
    sys.path.insert(0, _S4)

from auto_score import score_verse  # noqa: E402

# Same shape as build_exclusion._TAG_RE: optional W, optional letters, 2-5 digits,
# optional a/b suffix. Matches <WH07225>, <07225>, <09002>, <WTH8804>, <WAH09002>.
_ANY_TAG = re.compile(r"<\s*W?([A-Za-z]*?)(\d{2,5})([a-z]?)\s*>")


def normalize_tags(text):
    """Canonicalise every SN tag to <H{int}{suffix}> (strip W / padding / morph T)."""
    def repl(m):
        letters, num, suf = m.groups()
        t = letters[-1].upper() if letters and letters[-1].upper() in "HG" else "H"
        return f"<{t}{int(num)}{suf}>"
    return _ANY_TAG.sub(repl, text or "")


def num_score(model_output, gold):
    """Format-agnostic score: normalise both sides, then auto_score.score_verse.

    Returns the same dict as score_verse (coverage/placement/format/exact_match);
    here `format` is uninformative (both sides canonical) — judge by coverage/placement.
    """
    return score_verse(normalize_tags(model_output), normalize_tags(gold))
