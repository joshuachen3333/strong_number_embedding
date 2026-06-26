# wlc_bridge.py — re-export s10's WLC primitives (import, do NOT mutate s10 files).
# Per CLEAR_BIBLE_HANDOVER_from_s10obe.md: reuse the loader + lemma->FHL-09xxx bridge.
import os
import sys

_S10 = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "survey10_s1_but_obe_insteadOf_oneshot")
)
if _S10 not in sys.path:
    sys.path.insert(0, _S10)

import run_stage2_harsh as _H  # noqa: E402

load_wlc_verse = _H.load_wlc_verse        # (wlc_book, chap, sec) -> [(hebrew, fhl_num|None), ...]
build_wlc_source = _H.build_wlc_source    # tokens -> "hebrew<num>..."  (gloss2 already dropped)
build_harsh_prompt = _H.build_harsh_prompt  # (wlc_source, unv_plain, book_eng, chap, sec) -> str
nines_recall = _H.nines_recall            # (model_output, unv_sn) -> (placed, total)
CHI_TO_WLC_BOOK = _H.CHI_TO_WLC_BOOK      # {"創": "01"}
