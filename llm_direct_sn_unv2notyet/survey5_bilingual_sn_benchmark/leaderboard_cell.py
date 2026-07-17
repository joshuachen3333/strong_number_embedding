# leaderboard_cell.py — per-(model,prompt,arm,verse) execution. Reuses Round-2 primitives.
import os
import re
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
for p in (_PARENT, os.path.join(_PARENT, "survey4_self_supervised_prompt_tuning")):
    if p not in sys.path:
        sys.path.insert(0, p)

import scoring          # noqa: E402
import gate as G         # noqa: E402
import morph as M        # noqa: E402
import wlc_bridge as W   # noqa: E402
from auto_score import strip_sn                    # noqa: E402
from run_survey5 import call_model, detect_brand    # noqa: E402


def _gloss_block(label, gloss):
    lines = [f"{label} (English, per Hebrew word; annotation only — copy no tags):"]
    for heb, eng in gloss:
        if eng:
            lines.append(f"  {heb} → {eng}")
    return "\n".join(lines)


def compose_user(arm, wlc_source, unv_plain, gloss, book_eng, chap, sec):
    parts = [
        f"Here is {book_eng} {chap}:{sec} in the Hebrew original (WLC), each word tagged "
        f"with its Strong's Number:",
        "",
        wlc_source,
    ]
    if arm == "wlc+ylt" and gloss:
        parts += ["", _gloss_block("YLT literal gloss", gloss)]
    elif arm == "wlc+bsb" and gloss:
        parts += ["", _gloss_block("BSB gloss", gloss)]
    parts += [
        "",
        "Here is the same verse in UNV (和合本), plain, no annotations:",
        "",
        unv_plain,
        "",
        "Place the Strong's Number tags into the correct positions in the UNV text. "
        "Output ONLY the annotated UNV text on a single line.",
    ]
    return "\n".join(parts)


# Decision ①: strip morph-range tags (canonical H8675-H8999, after
# scoring.normalize_tags collapses WTH.../W.../padding to <H{n}>) from BOTH the model
# output and the gold before scoring, so the deterministic morph layer (morph.py /
# attach_morph, applied post-hoc) does not affect the headline placement/coverage metric.
_MORPH = re.compile(r"<H(\d{3,4})>")


def _strip_morph(text):
    def repl(m):
        n = int(m.group(1))
        return "" if 8675 <= n <= 8999 else m.group(0)
    return _MORPH.sub(repl, scoring.normalize_tags(text))


def score_cell_output(model_output, unv_sn):
    stripped = _strip_morph(model_output)
    gold = _strip_morph(unv_sn)
    return scoring.score_verse(stripped, gold)


# The model-under-test must run in an isolated cwd. Running `claude -p` from this repo
# dir makes it inherit this project's CLAUDE.md + /ph//logoutput skills and behave as an
# agent instead of annotating (a real bug hit in Round-2 / run_bakeoff.py).
_ISO_DIR = None


def _iso_dir():
    global _ISO_DIR
    if _ISO_DIR is None:
        _ISO_DIR = tempfile.mkdtemp(prefix="s5_leaderboard_iso_")
    return _ISO_DIR


def _call_isolated(model, brand, system, user, timeout=600):
    if brand == "claude":
        r = subprocess.run(["claude", "--model", model, "-p", f"{system}\n\n{user}"],
                           capture_output=True, text=True, timeout=timeout, cwd=_iso_dir())
        return r.stdout.strip()
    return call_model(model, brand, None, system, user)


def run_cell_verse(model, brand, system_prompt, arm, wlc_source, unv_sn, gloss,
                   morph_bridge, book_eng, wlc_book2, chap, sec):
    unv_plain = strip_sn(unv_sn)
    user = compose_user(arm, wlc_source, unv_plain, gloss, book_eng, chap, sec)
    out = _call_isolated(model, brand, system_prompt, user)
    if not out:
        return None
    out = M.attach_morph(out, M.wlc_verbs_for(wlc_book2, chap, sec), morph_bridge)
    score = score_cell_output(out, unv_sn)
    n9p, n9t = W.nines_recall(out, unv_sn)
    mp, mt = G.morph_recall(out, unv_sn)
    return {"score": score, "n9_placed": n9p, "n9_total": n9t,
            "morph_placed": mp, "morph_total": mt, "output": out}
