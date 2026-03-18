#!/usr/bin/env python3
"""Round 2-3: Each model judges disagreed verses."""

import json
import os
import sys

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from cli_caller import call_llm, DEFAULT_MODELS

ROUND2_PROMPT = """\
You are judging Strong's Number (SN) placement quality in Chinese Bible text.

Given the UNV source (with correct SN tags) and 3 model outputs that annotated \
the LCC (呂振中譯本) text with the same SNs, determine which output has the most \
accurate SN placement.

UNV+SN (source of truth for which SNs exist):
{unv_sn}

LCC original (unannotated):
{lcc_original}

Output A ({model_a}):
{output_a}

Output B ({model_b}):
{output_b}

Output C ({model_c}):
{output_c}

Evaluate each output on:
1. SN completeness — are ALL SNs from UNV present? Count them.
2. Placement accuracy — is each SN attached to the semantically correct LCC word?
3. Implicit marker handling — are {{<...>}} braces preserved when LCC has no explicit \
word for the Hebrew particle?
4. Morphology placement — are <WTH8xxx> codes attached to the correct verb?
5. Text preservation — is the LCC original text completely unchanged (only SN tags inserted)?

Return ONLY a JSON object:
{{
  "best": "A" or "B" or "C",
  "corrected": null or "the corrected LCC+SN text if none of A/B/C is fully correct",
  "reasoning": "brief explanation of your judgment",
  "sn_count_unv": <number of SNs in UNV>,
  "sn_counts": {{"A": <count>, "B": <count>, "C": <count>}}
}}"""

ROUND3_PROMPT = """\
You are making a FINAL judgment on Strong's Number (SN) placement quality.

This verse had no consensus in Round 2. You now see ALL prior evidence.

UNV+SN (source of truth):
{unv_sn}

LCC original (unannotated):
{lcc_original}

=== Round 1 outputs ===
Output A ({model_a}):
{output_a}

Output B ({model_b}):
{output_b}

Output C ({model_c}):
{output_c}

=== Round 2 judgments ===
{round2_judgments_text}

Based on ALL the above, give your final answer.

Return ONLY a JSON object:
{{
  "best": "A" or "B" or "C",
  "corrected": null or "the corrected LCC+SN text if none is fully correct",
  "reasoning": "your final reasoning considering all prior judgments"
}}"""


def build_judge_prompt(round_num, verse_key, round1_results, round2_judgments,
                       unv_sn, lcc_original, sn_field="lcc_sn"):
    """Build the judge prompt for a single verse."""
    models = list(round1_results.keys())
    model_a, model_b, model_c = models

    output_a = round1_results[model_a].get(verse_key, {}).get(sn_field, "(no output)")
    output_b = round1_results[model_b].get(verse_key, {}).get(sn_field, "(no output)")
    output_c = round1_results[model_c].get(verse_key, {}).get(sn_field, "(no output)")

    if round_num == 2:
        return ROUND2_PROMPT.format(
            unv_sn=unv_sn, lcc_original=lcc_original,
            model_a=model_a, model_b=model_b, model_c=model_c,
            output_a=output_a, output_b=output_b, output_c=output_c,
        )
    elif round_num == 3:
        # Format Round 2 judgments
        r2_lines = []
        if round2_judgments:
            for judge_model, judgment in round2_judgments.items():
                best = judgment.get("best", "?")
                reasoning = judgment.get("reasoning", "")
                r2_lines.append(f"{judge_model} chose: {best}")
                r2_lines.append(f"  Reasoning: {reasoning}")
        round2_text = '\n'.join(r2_lines) if r2_lines else "(no Round 2 judgments)"

        return ROUND3_PROMPT.format(
            unv_sn=unv_sn, lcc_original=lcc_original,
            model_a=model_a, model_b=model_b, model_c=model_c,
            output_a=output_a, output_b=output_b, output_c=output_c,
            round2_judgments_text=round2_text,
        )


def run_judge_round(round_num, disagreed_verses, round1_results,
                    verse_data, models=None, round2_judgments=None,
                    target_version="lcc", sn_field="lcc_sn",
                    verbose=False):
    """Run a judge round for all disagreed verses.

    Args:
        round_num: 2 or 3
        disagreed_verses: list of (chap, sec) tuples
        round1_results: {model_name: {(chap,sec): result_dict}}
        verse_data: {(chap,sec): {"unv_sn": str, "lcc_original": str}}
        models: list of model dicts (default: DEFAULT_MODELS)
        round2_judgments: {(chap,sec): {model_name: judgment_dict}} (for Round 3)
        target_version: target Bible version
        sn_field: field name for SN text
        verbose: print progress

    Returns:
        {(chap,sec): {model_name + "_as_judge": judgment_dict}}
    """
    if models is None:
        models = DEFAULT_MODELS

    results_dir = os.path.join(SURVEY_DIR, f"round{round_num}_results")
    os.makedirs(results_dir, exist_ok=True)

    all_judgments = {}

    for verse_key in disagreed_verses:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})
        unv_sn = vdata.get("unv_sn", "")
        lcc_original = vdata.get("lcc_original", "")

        verse_judgments = {}
        r2_for_verse = round2_judgments.get(verse_key, {}) if round2_judgments else {}

        print(f"\n  Round {round_num} judging {chap}:{sec}...", flush=True)

        for model_info in models:
            model_name = model_info["name"]
            brand = model_info["brand"]
            model_id = model_info["model"]
            judge_key = f"{model_name}_as_judge"

            # Check for cached result
            result_file = os.path.join(results_dir, model_name, f"{chap}_{sec}.json")
            if os.path.isfile(result_file):
                with open(result_file, "r", encoding="utf-8") as f:
                    verse_judgments[judge_key] = json.load(f)
                print(f"    [{model_name}] cached", flush=True)
                continue

            prompt = build_judge_prompt(
                round_num, verse_key, round1_results, r2_for_verse,
                unv_sn, lcc_original, sn_field
            )

            print(f"    [{model_name}] judging...", flush=True)

            # Use judge mode — no JSON schema forced, free-form response
            result = call_llm(
                brand=brand, model=model_id,
                system_prompt="You are a biblical Hebrew and Chinese translation expert.",
                user_prompt=prompt,
                target_version=target_version,
                verbose=verbose,
                mode="judge",
            )

            # Result should be {best, corrected, reasoning, ...}
            judgment = {}
            for key in ["best", "corrected", "reasoning", "sn_count_unv", "sn_counts"]:
                if key in result:
                    judgment[key] = result[key]

            if not judgment.get("best"):
                judgment = {
                    "best": "?",
                    "corrected": None,
                    "reasoning": f"Failed to parse judgment: {str(result)[:200]}",
                    "error": True
                }

            verse_judgments[judge_key] = judgment

            # Save to disk
            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(judgment, f, indent=2, ensure_ascii=False)

            print(f"    [{model_name}] → best={judgment.get('best', '?')}", flush=True)

        all_judgments[verse_key] = verse_judgments

    return all_judgments


def tally_judgments(judgments_for_verse, round1_results, sn_field="lcc_sn"):
    """Tally judge votes for a single verse.

    Returns:
        (winner_output, opinion_map) or (None, opinion_map) if no 2/3 agreement.

        winner_output: the SN text that won, or corrected text
        opinion_map: {judge_key: "majority"|"minority"}
    """
    models = list(round1_results.keys())
    label_to_model = {"A": models[0], "B": models[1], "C": models[2]}

    votes = {}  # label -> count
    corrected_texts = []

    for judge_key, judgment in judgments_for_verse.items():
        best = judgment.get("best", "?").upper()
        corrected = judgment.get("corrected")

        if corrected:
            corrected_texts.append(corrected)
            votes["corrected"] = votes.get("corrected", 0) + 1
        elif best in ("A", "B", "C"):
            votes[best] = votes.get(best, 0) + 1

    # Find winner (2/3 majority)
    total_judges = len(judgments_for_verse)
    threshold = total_judges * 2 / 3  # for 3 judges, need >= 2

    winner_label = None
    for label, count in votes.items():
        if count >= threshold:
            winner_label = label
            break

    # Build opinion map
    opinion_map = {}
    for judge_key, judgment in judgments_for_verse.items():
        best = judgment.get("best", "?").upper()
        corrected = judgment.get("corrected")
        if corrected:
            judge_label = "corrected"
        elif best in ("A", "B", "C"):
            judge_label = best
        else:
            judge_label = "?"

        opinion_map[judge_key] = "majority" if judge_label == winner_label else "minority"

    if winner_label is None:
        return None, opinion_map

    # Return the winning label (A/B/C/corrected) — caller resolves to text
    return winner_label, opinion_map
