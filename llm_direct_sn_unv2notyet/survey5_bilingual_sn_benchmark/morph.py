# morph.py — deterministic morph attach (apply time). NO LLM.
#
# The model places only lexical/09xxx tags onto UNV. For each WLC verb, we look up
# its FHL morph code in the frozen MORPH_BRIDGE and insert <WTH{code}> immediately
# after the verb's lexical tag in the model output (morph co-locates 101/101).
# See docs/.../2026-06-26-survey5-morph-mechanism-design.md §3b.
import json
import os
import re
from collections import defaultdict, deque

from learn_morph_bridge import load_wlc_verbs  # whole-TSV verb index (cached)

_HERE = os.path.dirname(os.path.abspath(__file__))
# Same shape as the lexical tag matcher: optional W + letters, 2-5 digits, optional suffix.
_TAG = re.compile(r"<\s*W?[A-Za-z]*?(\d{2,5})[a-z]?\s*>")
_verb_index = None


def load_bridge(path=None):
    path = path or os.path.join(_HERE, "morph_bridge.json")
    with open(path, encoding="utf-8") as f:
        return {k: int(v) for k, v in json.load(f).items()}


def wlc_verbs_for(book2, chap, sec):
    """Ordered [(lexical_int, form_key), ...] verbs for one verse (form_key = morph[:3])."""
    global _verb_index
    if _verb_index is None:
        _verb_index = load_wlc_verbs()
    return _verb_index.get((book2, chap, sec), [])


def attach_morph(output, wlc_verbs, bridge):
    """Insert <WTH{code}> after each verb's lexical tag in the model output.

    Anchors on the placed lexical tag whose number matches the verb's lexical SN
    (left-to-right when several share a number). Skips a verb if its form_key is
    unknown or its lexical tag isn't present (no anchor) — so morph recall is
    bounded by lexical-verb recall.
    """
    tag_pos = defaultdict(deque)
    for m in _TAG.finditer(output):
        tag_pos[int(m.group(1))].append(m.end())
    inserts = []
    for lex, form_key in wlc_verbs:
        code = bridge.get(form_key)
        if code is None:
            continue
        q = tag_pos.get(lex)
        if not q:
            continue
        inserts.append((q.popleft(), f"<WTH{code}>"))
    for pos, txt in sorted(inserts, reverse=True):  # descending so positions stay valid
        output = output[:pos] + txt + output[pos:]
    return output
