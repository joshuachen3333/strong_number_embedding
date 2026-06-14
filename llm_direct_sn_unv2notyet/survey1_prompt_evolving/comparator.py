#!/usr/bin/env python3
"""Compare Round 1 outputs from 3 models. Strict: only unanimous passes."""

import os
import re
import sys

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import count_sns


def extract_sn_sequence(text: str) -> list:
    """Extract ordered list of SN tags (with context) from annotated text.

    Returns list of full tag strings like '<WH0430>', '{<WH0853>}', '<WTH8804>'
    in shelled mode, or bare '<0430>' tags in --naked mode. Order matters — we
    compare placement, not just presence. Mode-agnostic: matches both shelled
    FHL tags and bare-number tags so disagreement diagnostics stay legible
    whether or not the run is naked.
    """
    pattern = r'(\{<W[ATH]*[HG]?\d+>\}|<W[ATH]*[HG]?\d+>|<\d+[a-z]?>)'
    return re.findall(pattern, text)


def texts_match(sn_text_a: str, sn_text_b: str) -> bool:
    """Check if two SN-annotated texts are equivalent.

    Compares the full annotated text after normalizing whitespace.
    This is strict: same SN tags at the same positions.
    """
    def normalize(t):
        # Collapse whitespace, strip
        return re.sub(r'\s+', '', t.strip())
    return normalize(sn_text_a) == normalize(sn_text_b)


def compare_round1(round1_results: dict, sn_field: str = "lcc_sn",
                   verse_keys: list = None):
    """Compare Round 1 outputs from all models.

    Args:
        round1_results: {model_name: {(chap, sec): result_dict}}
        sn_field: field name containing the SN-annotated text
        verse_keys: optional list of specific verse keys to compare
                    (default: all verses in round1_results)

    Returns:
        (unanimous, disagreed) where:
        - unanimous: list of (chap, sec) where all 3 models produced identical output
        - disagreed: list of (chap, sec) where any difference exists
    """
    models = list(round1_results.keys())
    if len(models) < 2:
        raise ValueError(f"Need at least 2 models, got {len(models)}")

    # Collect verse keys
    if verse_keys is not None:
        all_verses = set(verse_keys)
    else:
        all_verses = set()
        for model_results in round1_results.values():
            all_verses.update(model_results.keys())

    unanimous = []
    disagreed = []

    for verse_key in sorted(all_verses):
        chap, sec = verse_key

        # Collect outputs for this verse
        outputs = {}
        for model_name in models:
            result = round1_results[model_name].get(verse_key)
            if result and result.get(sn_field) and not result.get("error"):
                outputs[model_name] = result[sn_field]

        # If any model failed, it's a disagreement
        if len(outputs) < len(models):
            disagreed.append(verse_key)
            continue

        # Check unanimous: all texts must match
        texts = list(outputs.values())
        all_same = all(texts_match(texts[0], t) for t in texts[1:])

        if all_same:
            unanimous.append(verse_key)
        else:
            disagreed.append(verse_key)

    return unanimous, disagreed


def summarize_disagreement(verse_key, round1_results, sn_field="lcc_sn"):
    """Produce a human-readable summary of how models differ on a verse."""
    chap, sec = verse_key
    models = list(round1_results.keys())

    lines = [f"\n{'='*60}", f"  {chap}:{sec} — Disagreement"]

    for model_name in models:
        result = round1_results[model_name].get(verse_key, {})
        sn_text = result.get(sn_field, "(no output)")
        confidence = result.get("confidence", "?")
        sn_seq = extract_sn_sequence(sn_text) if sn_text else []
        lines.append(f"  [{model_name}] (conf={confidence}) {len(sn_seq)} SNs")
        lines.append(f"    {sn_text[:200]}")

    # Show SN differences
    sn_sets = {}
    for model_name in models:
        result = round1_results[model_name].get(verse_key, {})
        sn_text = result.get(sn_field, "")
        sn_sets[model_name] = set(extract_sn_sequence(sn_text))

    all_sns = set()
    for s in sn_sets.values():
        all_sns.update(s)

    diff_sns = []
    for sn in sorted(all_sns):
        present_in = [m for m in models if sn in sn_sets[m]]
        if len(present_in) < len(models):
            absent_from = [m for m in models if m not in present_in]
            diff_sns.append(f"    {sn}: present in {present_in}, absent from {absent_from}")

    if diff_sns:
        lines.append("  SN differences:")
        lines.extend(diff_sns)

    return '\n'.join(lines)
