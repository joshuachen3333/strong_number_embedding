#!/usr/bin/env python3
"""Build gold standard from round results. Track all opinions per round."""

import json
import os
import sys

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from judge import tally_judgments


def resolve_winner_text(winner_label, verse_key, round1_results,
                        corrected_texts, sn_field="lcc_sn"):
    """Get the actual SN text for the winning label."""
    models = list(round1_results.keys())
    label_to_model = {"A": models[0], "B": models[1], "C": models[2]}

    if winner_label == "corrected" and corrected_texts:
        return corrected_texts[0]
    elif winner_label in label_to_model:
        model = label_to_model[winner_label]
        return round1_results[model].get(verse_key, {}).get(sn_field, "")
    return ""


def build_gold_standard(unanimous, disagreed, round1_results,
                        round2_judgments, round3_judgments,
                        verse_data, prompt_version="v1.0",
                        sn_field="lcc_sn"):
    """Build gold standard JSONs from all round results.

    Args:
        unanimous: list of (chap, sec) — passed Round 1 unanimously
        disagreed: list of (chap, sec) — went to Round 2+
        round1_results: {model_name: {(chap,sec): result_dict}}
        round2_judgments: {(chap,sec): {judge_key: judgment_dict}}
        round3_judgments: {(chap,sec): {judge_key: judgment_dict}} or None
        verse_data: {(chap,sec): {"unv_sn", "lcc_original", "book"}}
        prompt_version: version string for tracking

    Returns:
        (gold_standard, unresolved)
        gold_standard: {(chap,sec): gold_dict}
        unresolved: list of (chap, sec)
    """
    models = list(round1_results.keys())
    gold_standard = {}
    unresolved = []

    # Process unanimous verses
    for verse_key in unanimous:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})

        # All models agree — take first model's output
        first_model = models[0]
        result = round1_results[first_model].get(verse_key, {})

        round1_opinions = {}
        for model_name in models:
            r = round1_results[model_name].get(verse_key, {})
            round1_opinions[model_name] = {
                "lcc_sn": r.get(sn_field, ""),
                "confidence": r.get("confidence", 0),
                "opinion": "unanimous",
            }

        gold_standard[verse_key] = {
            "book": vdata.get("book", ""),
            "chap": chap,
            "sec": sec,
            "lcc_sn": result.get(sn_field, ""),
            "lcc_original": vdata.get("lcc_original", ""),
            "unv_sn_reference": vdata.get("unv_sn", ""),
            "resolved_at": "round1",
            "prompt_version": prompt_version,
            "round1": round1_opinions,
            "round2": None,
            "round3": None,
        }

    # Process disagreed verses
    for verse_key in disagreed:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})

        # Build Round 1 opinions (all different, so no majority/minority yet)
        round1_opinions = {}
        for model_name in models:
            r = round1_results[model_name].get(verse_key, {})
            round1_opinions[model_name] = {
                "lcc_sn": r.get(sn_field, ""),
                "confidence": r.get("confidence", 0),
                "opinion": "disagree",  # updated below if resolved
            }

        # Try Round 2
        r2 = round2_judgments.get(verse_key, {})
        resolved_at = None
        winning_text = ""
        round2_with_opinions = None
        round3_with_opinions = None

        if r2:
            winner_label, opinion_map = tally_judgments(
                r2, round1_results, sn_field)

            # Collect corrected texts from judges
            corrected_texts = [
                j.get("corrected") for j in r2.values()
                if j.get("corrected")
            ]

            round2_with_opinions = {}
            for judge_key, judgment in r2.items():
                round2_with_opinions[judge_key] = {
                    **judgment,
                    "opinion": opinion_map.get(judge_key, "?"),
                }

            if winner_label is not None:
                resolved_at = "round2"
                winning_text = resolve_winner_text(
                    winner_label, verse_key, round1_results,
                    corrected_texts, sn_field)

                # Update Round 1 opinions based on Round 2 winner
                label_to_model = {"A": models[0], "B": models[1], "C": models[2]}
                winner_model = label_to_model.get(winner_label)
                for model_name in models:
                    if winner_label == "corrected":
                        round1_opinions[model_name]["opinion"] = "superseded"
                    elif model_name == winner_model:
                        round1_opinions[model_name]["opinion"] = "majority"
                    else:
                        round1_opinions[model_name]["opinion"] = "minority"

        # Try Round 3 if needed
        if resolved_at is None and round3_judgments:
            r3 = round3_judgments.get(verse_key, {})
            if r3:
                winner_label, opinion_map = tally_judgments(
                    r3, round1_results, sn_field)

                corrected_texts = [
                    j.get("corrected") for j in r3.values()
                    if j.get("corrected")
                ]

                round3_with_opinions = {}
                for judge_key, judgment in r3.items():
                    round3_with_opinions[judge_key] = {
                        **judgment,
                        "opinion": opinion_map.get(judge_key, "?"),
                    }

                if winner_label is not None:
                    resolved_at = "round3"
                    winning_text = resolve_winner_text(
                        winner_label, verse_key, round1_results,
                        corrected_texts, sn_field)

                    label_to_model = {"A": models[0], "B": models[1], "C": models[2]}
                    winner_model = label_to_model.get(winner_label)
                    for model_name in models:
                        if winner_label == "corrected":
                            round1_opinions[model_name]["opinion"] = "superseded"
                        elif model_name == winner_model:
                            round1_opinions[model_name]["opinion"] = "majority"
                        else:
                            round1_opinions[model_name]["opinion"] = "minority"

        if resolved_at is None:
            resolved_at = "unresolved"
            unresolved.append(verse_key)
            # Use first model's output as placeholder
            winning_text = round1_results[models[0]].get(verse_key, {}).get(sn_field, "")

        gold_standard[verse_key] = {
            "book": vdata.get("book", ""),
            "chap": chap,
            "sec": sec,
            "lcc_sn": winning_text,
            "lcc_original": vdata.get("lcc_original", ""),
            "unv_sn_reference": vdata.get("unv_sn", ""),
            "resolved_at": resolved_at,
            "prompt_version": prompt_version,
            "round1": round1_opinions,
            "round2": round2_with_opinions,
            "round3": round3_with_opinions,
        }

    return gold_standard, unresolved


def save_gold_standard(gold_standard, output_dir=None):
    """Save gold standard JSONs to disk."""
    if output_dir is None:
        output_dir = os.path.join(SURVEY_DIR, "gold_standard")

    for verse_key, gold in gold_standard.items():
        chap, sec = verse_key
        chap_dir = os.path.join(output_dir, str(chap))
        os.makedirs(chap_dir, exist_ok=True)
        filepath = os.path.join(chap_dir, f"{sec}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(gold, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved {len(gold_standard)} gold standard verses to {output_dir}")


def print_summary(gold_standard, unresolved):
    """Print a summary of the gold standard."""
    total = len(gold_standard)
    r1 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round1")
    r2 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round2")
    r3 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round3")
    ur = len(unresolved)

    print(f"\n{'='*60}")
    print(f"  Gold Standard Summary")
    print(f"{'='*60}")
    print(f"  Total verses:     {total}")
    print(f"  Round 1 (unanimous): {r1}")
    print(f"  Round 2 (2/3 judge): {r2}")
    print(f"  Round 3 (final arb): {r3}")
    print(f"  Unresolved:          {ur}")
    if unresolved:
        print(f"  Unresolved verses: {', '.join(f'{c}:{s}' for c, s in unresolved)}")
    print(f"{'='*60}")
