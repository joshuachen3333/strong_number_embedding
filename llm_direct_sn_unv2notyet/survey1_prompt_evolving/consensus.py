#!/usr/bin/env python3
"""Build gold standard from round results. Track all opinions per round."""

import json
import os
import sys

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from judge import tally_r2_debate, tally_r3_judgments


def resolve_winner_text(winner_label, verse_key, convergence_results,
                        corrected_texts):
    """Get the actual SN text for the winning label.

    Uses stable outputs from convergence (not R1 originals).
    """
    models = list(convergence_results.keys())
    label_to_model = {"A": models[0], "B": models[1], "C": models[2]}

    if winner_label == "corrected" and corrected_texts:
        return corrected_texts[0]
    elif winner_label in label_to_model:
        model = label_to_model[winner_label]
        conv = convergence_results[model].get(verse_key, {})
        return conv.get("stable_result", "")
    return ""


def build_gold_standard(unanimous, disagreed, round1_results,
                        convergence_results, round2_judgments,
                        round3_judgments, verse_data,
                        prompt_version="v1.0", sn_field="lcc_sn"):
    """Build gold standard JSONs from all round results.

    Args:
        unanimous: list of (chap, sec) — passed Round 1 unanimously
        disagreed: list of (chap, sec) — went to Round 2+
        round1_results: {model_name: {(chap,sec): result_dict}}
        convergence_results: {model_name: {(chap,sec): convergence_dict}}
        round2_judgments: {(chap,sec): {judge_key: judgment_dict}}
        round3_judgments: {(chap,sec): {judge_key: judgment_dict}} or None
        verse_data: {(chap,sec): {"unv_sn", "lcc_original", "book"}}
        prompt_version: version string for tracking

    Returns:
        (gold_standard, unresolved, prompt_evolutions)
        gold_standard: {(chap,sec): gold_dict}
        unresolved: list of (chap, sec)
        prompt_evolutions: list of {verse_key, error_descriptions, improvements}
    """
    models = list(round1_results.keys())
    gold_standard = {}
    unresolved = []
    prompt_evolutions = []

    # Process unanimous verses
    for verse_key in unanimous:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})

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

        # Build Round 1 opinions
        round1_opinions = {}
        for model_name in models:
            r = round1_results[model_name].get(verse_key, {})
            round1_opinions[model_name] = {
                "lcc_sn": r.get(sn_field, ""),
                "confidence": r.get("confidence", 0),
                "opinion": "disagree",
            }

        # Build convergence info
        convergence_info = {}
        for model_name in models:
            conv = convergence_results.get(model_name, {}).get(verse_key, {})
            convergence_info[model_name] = {
                "stable_result": conv.get("stable_result", ""),
                "converged": conv.get("converged", False),
                "stable_at": conv.get("stable_at", "?"),
                "attempt_count": len(conv.get("attempts", [])),
            }

        # Try Round 2 debate
        r2 = round2_judgments.get(verse_key, {})
        resolved_at = None
        winning_text = ""
        round2_with_opinions = None
        round3_with_opinions = None

        if r2:
            winner_label, opinion_map = tally_r2_debate(
                r2, convergence_results, sn_field)

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
                    winner_label, verse_key, convergence_results,
                    corrected_texts)

                # Update R1 opinions
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
                outcome, details = tally_r3_judgments(r3, convergence_results)

                round3_with_opinions = {}
                for judge_key, judgment in r3.items():
                    round3_with_opinions[judge_key] = {**judgment}

                if outcome == "resolved":
                    winner_label, opinion_map = details
                    resolved_at = "round3"

                    corrected_texts = [
                        j.get("corrected") for j in r3.values()
                        if j.get("corrected")
                    ]
                    winning_text = resolve_winner_text(
                        winner_label, verse_key, convergence_results,
                        corrected_texts)

                    # Update opinions
                    for judge_key in round3_with_opinions:
                        round3_with_opinions[judge_key]["opinion"] = opinion_map.get(judge_key, "?")

                    label_to_model = {"A": models[0], "B": models[1], "C": models[2]}
                    winner_model = label_to_model.get(winner_label)
                    for model_name in models:
                        if winner_label == "corrected":
                            round1_opinions[model_name]["opinion"] = "superseded"
                        elif model_name == winner_model:
                            round1_opinions[model_name]["opinion"] = "majority"
                        else:
                            round1_opinions[model_name]["opinion"] = "minority"

                elif outcome == "prompt_evolution":
                    resolved_at = "prompt_evolution"
                    prompt_evolutions.append({
                        "verse_key": verse_key,
                        "error_descriptions": details["error_descriptions"],
                        "improvements": details["improvements"],
                        "aligned": details["aligned"],
                    })
                    # Use first model's stable output as placeholder
                    winning_text = convergence_results[models[0]].get(
                        verse_key, {}).get("stable_result", "")

                    for judge_key in round3_with_opinions:
                        round3_with_opinions[judge_key]["opinion"] = "all_wrong"

                else:  # unresolved
                    for judge_key in round3_with_opinions:
                        round3_with_opinions[judge_key]["opinion"] = details.get(judge_key, "minority")

        if resolved_at is None:
            resolved_at = "unresolved"
            unresolved.append(verse_key)
            winning_text = convergence_results.get(models[0], {}).get(
                verse_key, {}).get("stable_result",
                round1_results[models[0]].get(verse_key, {}).get(sn_field, ""))

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
            "round2_convergence": convergence_info,
            "round3": round3_with_opinions,
        }

    return gold_standard, unresolved, prompt_evolutions


def save_gold_standard(gold_standard, output_dir=None):
    """Save gold standard JSONs to disk."""
    if output_dir is None:
        output_dir = os.path.join(SURVEY_DIR, "gold_standard")

    for verse_key, gold in gold_standard.items():
        chap, sec = verse_key
        book = gold.get("book", "")
        book_dir = os.path.join(output_dir, book, str(chap))
        os.makedirs(book_dir, exist_ok=True)
        filepath = os.path.join(book_dir, f"{sec}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(gold, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved {len(gold_standard)} gold standard verses to {output_dir}")


def print_summary(gold_standard, unresolved, prompt_evolutions=None):
    """Print a summary of the gold standard."""
    total = len(gold_standard)
    r1 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round1")
    r2 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round2")
    r3 = sum(1 for g in gold_standard.values() if g["resolved_at"] == "round3")
    pe = sum(1 for g in gold_standard.values() if g["resolved_at"] == "prompt_evolution")
    ur = len(unresolved)

    print(f"\n{'='*60}")
    print(f"  Gold Standard Summary")
    print(f"{'='*60}")
    print(f"  Total verses:        {total}")
    print(f"  Round 1 (unanimous):   {r1}")
    print(f"  Round 2 (2/3 debate):  {r2}")
    print(f"  Round 3 (2/3 final):   {r3}")
    print(f"  Prompt evolution:      {pe}")
    print(f"  Unresolved:            {ur}")
    if unresolved:
        print(f"  Unresolved verses: {', '.join(f'{c}:{s}' for c, s in unresolved)}")

    if prompt_evolutions:
        print(f"\n  {'─'*50}")
        print(f"  PROMPT EVOLUTION TRIGGERED ({len(prompt_evolutions)} verses)")
        print(f"  {'─'*50}")
        for pe_info in prompt_evolutions:
            vk = pe_info["verse_key"]
            print(f"\n  Verse {vk[0]}:{vk[1]}:")
            print(f"    Aligned: {pe_info['aligned']}")
            for i, (err, imp) in enumerate(zip(
                    pe_info["error_descriptions"], pe_info["improvements"])):
                print(f"    Judge {i+1} error: {err[:120]}")
                print(f"    Judge {i+1} fix:   {imp[:120]}")

    print(f"{'='*60}")
