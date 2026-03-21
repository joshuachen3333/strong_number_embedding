#!/usr/bin/env python3
"""Round 2-3: R2 convergence + debate, R3 dual-capability judging."""

import json
import os
import sys
import time

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from cli_caller import call_llm, DEFAULT_MODELS
from comparator import texts_match

# ── R2 Debate Prompt ─────────────────────────────────────────────────────────

ROUND2_DEBATE_PROMPT = """\
You are judging Strong's Number (SN) placement quality in Chinese Bible text.

Given the UNV source (with correct SN tags) and 3 model outputs that annotated \
the LCC (呂振中譯本) text with the same SNs, determine which output has the most \
accurate SN placement.

UNV+SN (source of truth for which SNs exist):
{unv_sn}

LCC original (unannotated):
{lcc_original}

Output A ({model_a}) [convergence: {convergence_a}]:
{output_a}

Output B ({model_b}) [convergence: {convergence_b}]:
{output_b}

Output C ({model_c}) [convergence: {convergence_c}]:
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

# ── R3 Dual-Capability Prompt ────────────────────────────────────────────────

ROUND3_PROMPT = """\
You are making a FINAL, independent judgment on Strong's Number (SN) placement.

This verse had no consensus in Round 2. You now see ALL prior evidence.
Your task has TWO possible outcomes — choose the one that honestly fits:

**Option 1 — PICK the best output**: One of the outputs (or a corrected version) \
is good enough to be the gold standard.

**Option 2 — ALL WRONG**: ALL outputs share the same systematic error that none \
got right. This is NOT about minor differences — it means a fundamental issue \
(e.g., all dropped implicit markers, all lost prefix tags). If you choose this, \
you MUST identify the specific error and propose how the prompt should be improved.

Be honest. If one output is genuinely better, pick it. Only choose "all_wrong" if \
you independently see a systematic problem that affects all outputs equally.

UNV+SN (source of truth):
{unv_sn}

LCC original (unannotated):
{lcc_original}

=== Round 1 stable outputs ===
Output A ({model_a}) [convergence: {convergence_a}]:
{output_a}

Output B ({model_b}) [convergence: {convergence_b}]:
{output_b}

Output C ({model_c}) [convergence: {convergence_c}]:
{output_c}

=== Round 2 debate judgments ===
{round2_judgments_text}

Based on ALL the above, give your final answer.

Return ONLY a JSON object matching ONE of these formats:

If picking a winner:
{{
  "verdict": "pick",
  "best": "A" or "B" or "C",
  "corrected": null or "the corrected LCC+SN text",
  "reasoning": "your final reasoning"
}}

If all are wrong:
{{
  "verdict": "all_wrong",
  "error_identified": "specific description of what ALL outputs got wrong",
  "prompt_improvement": "concrete suggestion for fixing the prompt to prevent this",
  "reasoning": "why this is a prompt deficiency, not a model-specific error"
}}"""


# ── R2 Convergence ───────────────────────────────────────────────────────────

def run_r2_convergence(verses, round1_results, verse_data, models=None,
                       system_prompt="", target_version="lcc",
                       sn_field="lcc_sn", max_retries=3, verbose=False,
                       force=False):
    """Run R2 convergence: each model re-does the task blindly until stable.

    For each model+verse:
      1. Produce R2a (blind, same prompt as R1)
      2. If R2a == R1 → stable at R1
      3. If different → retry up to max_retries times until consecutive match
      4. Store convergence history

    Args:
        verses: list of (chap, sec) tuples (disagreed verses)
        round1_results: {model_name: {(chap,sec): result_dict}}
        verse_data: {(chap,sec): {"unv_sn", "lcc_original", "book"}}
        models: list of model dicts
        system_prompt: the system prompt to use for blind re-do
        target_version: target Bible version
        sn_field: field name for SN text
        max_retries: max retries after R2a (default 3 → R2a,b,c,d)
        verbose: print progress

    Returns:
        convergence_results: {model_name: {(chap,sec): convergence_dict}}
        Where convergence_dict = {
            "stable_result": str,
            "converged": bool,
            "attempts": [str, ...],  # R1, R2a, R2b, ...
            "stable_at": "R1" or "R2a" or "R2b" etc,
        }
    """
    if models is None:
        models = DEFAULT_MODELS

    # Import here to avoid circular — build_user_prompt is in parent
    from llm_direct_sn_unv2notyet import build_user_prompt

    conv_dir = os.path.join(SURVEY_DIR, "round2_results")
    os.makedirs(conv_dir, exist_ok=True)

    convergence_results = {m["name"]: {} for m in models}

    for verse_key in verses:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})
        unv_sn = vdata.get("unv_sn", "")
        lcc_original = vdata.get("lcc_original", "")
        book_eng = vdata.get("book", "")
        book_chi = _eng_to_chi(book_eng)

        print(f"\n  R2 convergence {chap}:{sec}...", flush=True)

        for model_info in models:
            model_name = model_info["name"]
            brand = model_info["brand"]
            model_id = model_info["model"]

            # Check cache
            conv_file = os.path.join(
                conv_dir, model_name, book_eng, f"{chap}_{sec}_convergence.json")
            if not force and os.path.isfile(conv_file):
                with open(conv_file, "r", encoding="utf-8") as f:
                    convergence_results[model_name][verse_key] = json.load(f)
                print(f"    [{model_name}] convergence cached", flush=True)
                continue

            # Get R1 output
            r1_result = round1_results[model_name].get(verse_key, {})
            r1_text = r1_result.get(sn_field, "")
            r1_was_error = r1_result.get("error", False) or not r1_text.strip()

            attempts = [r1_text]  # index 0 = R1
            # Track R2 valid attempts for back-comparison (R1 excluded)
            r2_valid = {}  # {label: text} — only R2 attempts, not R1
            converged = False
            stable_at = None

            if r1_was_error:
                print(f"    [{model_name}] R1 was error/empty — ignoring as baseline", flush=True)

            effective_max = max_retries if max_retries > 0 else 702  # 0 = unlimited (a-z + aa-zz)
            consecutive_errors = 0
            MAX_CONSECUTIVE_ERRORS = 3  # bail out after 3 consecutive errors
            for i in range(1 + effective_max):  # R2a + up to effective_max
                label = _r2_label(i)

                print(f"    [{model_name}] {label}...", end=" ", flush=True)

                # Blind re-do: same prompt as R1
                user_prompt = build_user_prompt(
                    unv_sn, lcc_original, target_version, book_chi, chap, sec)

                t_start = time.time()
                result = call_llm(
                    brand=brand, model=model_id,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    target_version=target_version,
                    verbose=verbose,
                )
                elapsed_s = int(time.time() - t_start)

                new_text = result.get(sn_field, "")
                new_is_error = result.get("error", False) or not new_text.strip()
                attempts.append(new_text)

                # Never treat empty/error as stable
                if new_is_error:
                    consecutive_errors += 1
                    print(f"ERROR (empty/timeout) {elapsed_s}s [consecutive: {consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}]", flush=True)
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        print(f"    [{model_name}] BAILED OUT — {MAX_CONSECUTIVE_ERRORS} consecutive errors (model may be rate-limited)", flush=True)
                        break
                    continue
                consecutive_errors = 0  # reset on success

                # R2a: compare with R1 only (special case)
                if i == 0 and not r1_was_error and r1_text.strip():
                    if texts_match(new_text, r1_text):
                        stable_at = "R1"
                        converged = True
                        print(f"STABLE (matches R1) {elapsed_s}s", flush=True)
                        break

                # R2b+: compare against all previous R2 attempts (not R1)
                matched_label = None
                for prev_label, prev_text in r2_valid.items():
                    if texts_match(new_text, prev_text):
                        matched_label = prev_label
                        break

                if matched_label is not None:
                    stable_at = matched_label
                    converged = True
                    print(f"STABLE (matches {matched_label}) {elapsed_s}s", flush=True)
                    break
                else:
                    if not r2_valid and (i > 0 or r1_was_error):
                        print(f"first valid attempt {elapsed_s}s", flush=True)
                    elif i == 0 and not r1_was_error:
                        print(f"differs from R1 {elapsed_s}s", flush=True)
                    else:
                        print(f"differs from all previous {elapsed_s}s", flush=True)
                    r2_valid[label] = new_text

            if not converged:
                stable_at = "unstable"
                print(f"    [{model_name}] NOT CONVERGED after {1+max_retries} attempts", flush=True)

            # Stable result = the matched text, or last valid attempt if unstable
            if converged and stable_at == "R1":
                stable_result = r1_text
            elif converged:
                stable_result = new_text  # the text that matched a previous R2 attempt
            elif r2_valid:
                stable_result = list(r2_valid.values())[-1]  # last valid R2
            else:
                stable_result = ""

            conv_data = {
                "stable_result": stable_result,
                "converged": converged,
                "attempts": attempts,
                "stable_at": stable_at,
            }
            convergence_results[model_name][verse_key] = conv_data

            # Save to disk
            os.makedirs(os.path.dirname(conv_file), exist_ok=True)
            with open(conv_file, "w", encoding="utf-8") as f:
                json.dump(conv_data, f, indent=2, ensure_ascii=False)

    return convergence_results


# ── R2 Debate ────────────────────────────────────────────────────────────────

def build_r2_debate_prompt(verse_key, convergence_results, verse_data,
                           sn_field="lcc_sn"):
    """Build the R2 debate prompt showing stable outputs + convergence info."""
    models = list(convergence_results.keys())
    model_a, model_b, model_c = models

    vdata = verse_data.get(verse_key, {})

    def _get_output_and_conv(model_name):
        conv = convergence_results[model_name].get(verse_key, {})
        text = conv.get("stable_result", "(no output)")
        stable = conv.get("stable_at", "?")
        converged = conv.get("converged", False)
        if converged:
            conv_str = f"stable at {stable}"
        else:
            conv_str = f"UNSTABLE after {len(conv.get('attempts', [])) - 1} attempts"
        return text, conv_str

    output_a, conv_a = _get_output_and_conv(model_a)
    output_b, conv_b = _get_output_and_conv(model_b)
    output_c, conv_c = _get_output_and_conv(model_c)

    return ROUND2_DEBATE_PROMPT.format(
        unv_sn=vdata.get("unv_sn", ""),
        lcc_original=vdata.get("lcc_original", ""),
        model_a=model_a, model_b=model_b, model_c=model_c,
        output_a=output_a, output_b=output_b, output_c=output_c,
        convergence_a=conv_a, convergence_b=conv_b, convergence_c=conv_c,
    )


def run_r2_debate(verses, convergence_results, verse_data, models=None,
                  target_version="lcc", sn_field="lcc_sn", verbose=False,
                  force=False):
    """Run R2 debate: each model judges the 3 stable outputs.

    Returns:
        {(chap,sec): {model_name + "_as_judge": judgment_dict}}
    """
    if models is None:
        models = DEFAULT_MODELS

    results_dir = os.path.join(SURVEY_DIR, "round2_results")
    all_judgments = {}

    for verse_key in verses:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})
        book_eng = vdata.get("book", "")
        verse_judgments = {}

        print(f"\n  R2 debate {chap}:{sec}...", flush=True)

        for model_info in models:
            model_name = model_info["name"]
            brand = model_info["brand"]
            model_id = model_info["model"]
            judge_key = f"{model_name}_as_judge"

            # Check cache
            result_file = os.path.join(results_dir, model_name, book_eng, f"{chap}_{sec}.json")
            if not force and os.path.isfile(result_file):
                with open(result_file, "r", encoding="utf-8") as f:
                    verse_judgments[judge_key] = json.load(f)
                print(f"    [{model_name}] debate cached", flush=True)
                continue

            prompt = build_r2_debate_prompt(
                verse_key, convergence_results, verse_data, sn_field)

            print(f"    [{model_name}] debating...", end=" ", flush=True)

            t_start = time.time()
            result = call_llm(
                brand=brand, model=model_id,
                system_prompt="You are a biblical Hebrew and Chinese translation expert.",
                user_prompt=prompt,
                target_version=target_version,
                verbose=verbose,
                mode="judge",
            )
            elapsed_s = int(time.time() - t_start)

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

            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(judgment, f, indent=2, ensure_ascii=False)

            print(f"    [{model_name}] → best={judgment.get('best', '?')} {elapsed_s}s", flush=True)

        all_judgments[verse_key] = verse_judgments

    return all_judgments


# ── R3 Dual-Capability ───────────────────────────────────────────────────────

def build_r3_prompt(verse_key, convergence_results, round2_judgments,
                    verse_data, sn_field="lcc_sn"):
    """Build R3 prompt with dual capability (pick or all_wrong)."""
    models = list(convergence_results.keys())
    model_a, model_b, model_c = models

    vdata = verse_data.get(verse_key, {})

    def _get_output_and_conv(model_name):
        conv = convergence_results[model_name].get(verse_key, {})
        text = conv.get("stable_result", "(no output)")
        stable = conv.get("stable_at", "?")
        converged = conv.get("converged", False)
        if converged:
            conv_str = f"stable at {stable}"
        else:
            conv_str = f"UNSTABLE after {len(conv.get('attempts', [])) - 1} attempts"
        return text, conv_str

    output_a, conv_a = _get_output_and_conv(model_a)
    output_b, conv_b = _get_output_and_conv(model_b)
    output_c, conv_c = _get_output_and_conv(model_c)

    # Format R2 debate judgments
    r2_for_verse = round2_judgments.get(verse_key, {})
    r2_lines = []
    for judge_model, judgment in r2_for_verse.items():
        best = judgment.get("best", "?")
        reasoning = judgment.get("reasoning", "")
        r2_lines.append(f"{judge_model} chose: {best}")
        r2_lines.append(f"  Reasoning: {reasoning}")
    round2_text = '\n'.join(r2_lines) if r2_lines else "(no Round 2 judgments)"

    return ROUND3_PROMPT.format(
        unv_sn=vdata.get("unv_sn", ""),
        lcc_original=vdata.get("lcc_original", ""),
        model_a=model_a, model_b=model_b, model_c=model_c,
        output_a=output_a, output_b=output_b, output_c=output_c,
        convergence_a=conv_a, convergence_b=conv_b, convergence_c=conv_c,
        round2_judgments_text=round2_text,
    )


def run_round3(verses, convergence_results, round2_judgments, verse_data,
               models=None, target_version="lcc", sn_field="lcc_sn",
               verbose=False, force=False):
    """Run Round 3: dual-capability judging (pick or all_wrong).

    Returns:
        {(chap,sec): {model_name + "_as_judge": judgment_dict}}
        Where judgment_dict has "verdict" = "pick" or "all_wrong"
    """
    if models is None:
        models = DEFAULT_MODELS

    results_dir = os.path.join(SURVEY_DIR, "round3_results")
    os.makedirs(results_dir, exist_ok=True)

    all_judgments = {}

    for verse_key in verses:
        chap, sec = verse_key
        vdata = verse_data.get(verse_key, {})
        book_eng = vdata.get("book", "")
        verse_judgments = {}

        print(f"\n  R3 judging {chap}:{sec}...", flush=True)

        for model_info in models:
            model_name = model_info["name"]
            brand = model_info["brand"]
            model_id = model_info["model"]
            judge_key = f"{model_name}_as_judge"

            # Check cache
            result_file = os.path.join(results_dir, model_name, book_eng, f"{chap}_{sec}.json")
            if not force and os.path.isfile(result_file):
                with open(result_file, "r", encoding="utf-8") as f:
                    verse_judgments[judge_key] = json.load(f)
                print(f"    [{model_name}] cached", flush=True)
                continue

            prompt = build_r3_prompt(
                verse_key, convergence_results, round2_judgments,
                verse_data, sn_field)

            print(f"    [{model_name}] judging...", end=" ", flush=True)

            t_start = time.time()
            result = call_llm(
                brand=brand, model=model_id,
                system_prompt="You are a biblical Hebrew and Chinese translation expert.",
                user_prompt=prompt,
                target_version=target_version,
                verbose=verbose,
                mode="judge",
            )
            elapsed_s = int(time.time() - t_start)

            # Parse dual-format response
            judgment = _parse_r3_judgment(result)
            verse_judgments[judge_key] = judgment

            os.makedirs(os.path.dirname(result_file), exist_ok=True)
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(judgment, f, indent=2, ensure_ascii=False)

            verdict = judgment.get("verdict", "?")
            if verdict == "pick":
                print(f"    [{model_name}] → PICK best={judgment.get('best', '?')} {elapsed_s}s", flush=True)
            elif verdict == "all_wrong":
                print(f"    [{model_name}] → ALL_WRONG: {judgment.get('error_identified', '')[:80]} {elapsed_s}s", flush=True)
            else:
                print(f"    [{model_name}] → UNKNOWN verdict {elapsed_s}s", flush=True)

        all_judgments[verse_key] = verse_judgments

    return all_judgments


def _parse_r3_judgment(result):
    """Parse R3 response into standardized judgment dict."""
    verdict = result.get("verdict", "").lower()

    if verdict == "all_wrong":
        return {
            "verdict": "all_wrong",
            "error_identified": result.get("error_identified", ""),
            "prompt_improvement": result.get("prompt_improvement", ""),
            "reasoning": result.get("reasoning", ""),
        }
    elif verdict == "pick" or result.get("best"):
        return {
            "verdict": "pick",
            "best": result.get("best", "?"),
            "corrected": result.get("corrected"),
            "reasoning": result.get("reasoning", ""),
        }
    else:
        # Fallback: try to infer from fields
        if result.get("error_identified"):
            return {
                "verdict": "all_wrong",
                "error_identified": result.get("error_identified", ""),
                "prompt_improvement": result.get("prompt_improvement", ""),
                "reasoning": result.get("reasoning", ""),
            }
        return {
            "verdict": "unknown",
            "reasoning": f"Could not parse R3 response: {str(result)[:200]}",
            "error": True,
        }


# ── R2 Tally (debate phase) ─────────────────────────────────────────────────

def tally_r2_debate(judgments_for_verse, convergence_results, sn_field="lcc_sn"):
    """Tally R2 debate votes for a single verse.

    Uses stable outputs from convergence (not R1 originals) as A/B/C.

    Returns:
        (winner_label, opinion_map) or (None, opinion_map) if no 2/3 agreement.
    """
    models = list(convergence_results.keys())
    label_to_model = {"A": models[0], "B": models[1], "C": models[2]}

    votes = {}
    for judge_key, judgment in judgments_for_verse.items():
        best = judgment.get("best", "?").upper()
        corrected = judgment.get("corrected")

        # best vote takes priority; corrected only counts when best is missing
        if best in ("A", "B", "C"):
            votes[best] = votes.get(best, 0) + 1
        elif corrected:
            votes["corrected"] = votes.get("corrected", 0) + 1

    total_judges = len(judgments_for_verse)
    threshold = total_judges * 2 / 3

    winner_label = None
    for label, count in votes.items():
        if count >= threshold:
            winner_label = label
            break

    opinion_map = {}
    for judge_key, judgment in judgments_for_verse.items():
        best = judgment.get("best", "?").upper()
        corrected = judgment.get("corrected")
        if best in ("A", "B", "C"):
            judge_label = best
        elif corrected:
            judge_label = "corrected"
        else:
            judge_label = "?"
        opinion_map[judge_key] = "majority" if judge_label == winner_label else "minority"

    return winner_label, opinion_map


# ── R3 Tally (dual-capability) ──────────────────────────────────────────────

def tally_r3_judgments(judgments_for_verse, convergence_results):
    """Tally R3 judgments with dual-capability (pick or all_wrong).

    Returns:
        (outcome, details)

        outcome is one of:
        - "resolved": a winner was picked (details = (winner_label, opinion_map))
        - "prompt_evolution": 2/3+ said all_wrong with aligned errors
          (details = {"error_descriptions": [...], "improvements": [...], "aligned": bool})
        - "unresolved": no consensus (details = opinion_map)
    """
    total = len(judgments_for_verse)
    threshold = total * 2 / 3

    # Count verdicts
    pick_votes = {}  # label -> count
    all_wrong_judges = []
    corrected_texts = []

    for judge_key, judgment in judgments_for_verse.items():
        verdict = judgment.get("verdict", "unknown")

        if verdict == "all_wrong":
            all_wrong_judges.append(judgment)
        elif verdict == "pick":
            best = judgment.get("best", "?").upper()
            corrected = judgment.get("corrected")
            if corrected:
                corrected_texts.append(corrected)
                pick_votes["corrected"] = pick_votes.get("corrected", 0) + 1
            elif best in ("A", "B", "C"):
                pick_votes[best] = pick_votes.get(best, 0) + 1

    # Check if 2/3+ say all_wrong
    if len(all_wrong_judges) >= threshold:
        errors = [j.get("error_identified", "") for j in all_wrong_judges]
        improvements = [j.get("prompt_improvement", "") for j in all_wrong_judges]
        aligned = _check_error_alignment(errors)
        return "prompt_evolution", {
            "error_descriptions": errors,
            "improvements": improvements,
            "aligned": aligned,
            "all_wrong_count": len(all_wrong_judges),
        }

    # Check if 2/3+ pick same winner
    winner_label = None
    for label, count in pick_votes.items():
        if count >= threshold:
            winner_label = label
            break

    if winner_label is not None:
        opinion_map = {}
        for judge_key, judgment in judgments_for_verse.items():
            verdict = judgment.get("verdict", "unknown")
            if verdict == "all_wrong":
                opinion_map[judge_key] = "minority"
            elif verdict == "pick":
                best = judgment.get("best", "?").upper()
                corrected = judgment.get("corrected")
                if corrected:
                    judge_label = "corrected"
                elif best in ("A", "B", "C"):
                    judge_label = best
                else:
                    judge_label = "?"
                opinion_map[judge_key] = "majority" if judge_label == winner_label else "minority"
            else:
                opinion_map[judge_key] = "minority"
        return "resolved", (winner_label, opinion_map)

    # No consensus
    opinion_map = {}
    for judge_key in judgments_for_verse:
        opinion_map[judge_key] = "minority"
    return "unresolved", opinion_map


def _check_error_alignment(error_descriptions):
    """Check if error descriptions align (mention same issue).

    Simple keyword heuristic: extract SN-tag-like patterns and common
    error keywords, check for overlap.
    """
    import re

    if len(error_descriptions) < 2:
        return True  # single description is trivially aligned

    # Extract keywords of interest from each description
    keyword_sets = []
    for desc in error_descriptions:
        desc_lower = desc.lower()
        keywords = set()

        # SN tags mentioned
        sn_tags = re.findall(r'<W[ATH]*[HG]?\d+>', desc)
        keywords.update(t.upper() for t in sn_tags)

        # Common error categories
        categories = [
            ("implicit", ["implicit", "brace", "{<", "braces"]),
            ("prefix", ["prefix", "WAH", "09001", "09002"]),
            ("zero-pad", ["zero", "padding", "leading zero", "0430", "07225"]),
            ("missing", ["missing", "dropped", "lost", "omit"]),
            ("format", ["format", "exact", "copy"]),
        ]
        for cat_name, cat_words in categories:
            if any(w.lower() in desc_lower for w in cat_words):
                keywords.add(cat_name)

        keyword_sets.append(keywords)

    # Check pairwise overlap: all pairs must share at least one keyword
    for i in range(len(keyword_sets)):
        for j in range(i + 1, len(keyword_sets)):
            if not keyword_sets[i] & keyword_sets[j]:
                return False

    return True


# ── Model Patch Generation ───────────────────────────────────────────────────

FEEDBACK_PROMPT_MILD = """\
You are reviewing another model's attempts at Strong's Number (SN) placement \
in Chinese Bible text.

Correct output (agreed by 2 models):
{stable_output}

UNV source (with correct SNs):
{unv_sn}

The struggling model produced these attempts (could not converge):
{attempt_list}

What specific mistakes is this model making? Give brief, actionable feedback \
about SN placement errors, missing tags, or format issues."""

FEEDBACK_PROMPT_MODERATE = """\
You are reviewing another model's attempts at Strong's Number (SN) placement \
in Chinese Bible text. This model showed significant instability — it produced \
{unique_count} different outputs before converging.

Correct output (agreed by 2 models):
{stable_output}

UNV source (with correct SNs):
{unv_sn}

Full attempt history (note how the output changes each time):
{attempt_list}

Analyze:
1. What specific SN placement mistakes does this model make?
2. WHERE is it oscillating — which SNs or positions keep changing between attempts?
3. WHY might it be oscillating — what ambiguity or confusion is causing the instability?
Give actionable feedback that addresses the root cause of the oscillation."""

FEEDBACK_PROMPT_STRONG = """\
You are reviewing another model's attempts at Strong's Number (SN) placement \
in Chinese Bible text. This model is SEVERELY unstable — it produced \
{unique_count} different outputs and {convergence_status}.
{past_trigger2_section}
Correct output (agreed by 2 models):
{stable_output}

UNV source (with correct SNs):
{unv_sn}

Full attempt history (note the oscillation pattern):
{attempt_list}

This model needs PRESCRIPTIVE rules, not hints. Analyze:
1. What specific SN placement mistakes does this model make?
2. WHERE exactly is it oscillating — list every SN tag or position that changes?
3. WHY — what systematic confusion is causing repeated instability?
4. Write EXPLICIT rules (not suggestions) that would eliminate each oscillation.
Be thorough and prescriptive — this model has failed to self-correct."""

SELF_PATCH_PROMPT_MILD = """\
Two expert reviewers analyzed your Strong's Number placement attempts and gave \
this feedback:

Reviewer 1: {feedback_1}
Reviewer 2: {feedback_2}
{existing_patch_section}
Based on ALL the above, write a COMPLETE, self-contained set of additional \
instructions for yourself that would prevent these mistakes in future SN \
placement tasks. This must be a full replacement — include everything you \
need, not just the new fixes.
Output ONLY the instructions — no preamble, no examples, just rules."""

SELF_PATCH_PROMPT_MODERATE = """\
Two expert reviewers analyzed your Strong's Number placement attempts and gave \
this feedback. You produced {unique_count} different outputs before converging \
— you need to understand WHY you oscillated.

Reviewer 1: {feedback_1}
Reviewer 2: {feedback_2}
{existing_patch_section}
Based on ALL the above:
1. First, write a ROOT CAUSE ANALYSIS: why did you produce {unique_count} \
different outputs? What was ambiguous or confusing?
2. Then, write a COMPLETE, self-contained set of instructions that would \
prevent these mistakes AND the oscillation. Include explicit decision rules \
for the ambiguous cases you identified.
This must be a full replacement — include everything you need.
Output ONLY the analysis and instructions — no preamble."""

SELF_PATCH_PROMPT_STRONG = """\
Two expert reviewers analyzed your Strong's Number placement attempts. You are \
SEVERELY unstable — you produced {unique_count} different outputs and \
{convergence_status}. This is a recurring problem.

Reviewer 1: {feedback_1}
Reviewer 2: {feedback_2}
{existing_patch_section}{past_trigger2_section}
You MUST write PRESCRIPTIVE rules, not hints or suggestions. For each rule, \
include a concrete BEFORE→AFTER example from your own failed attempts.

Based on ALL the above:
1. ROOT CAUSE ANALYSIS: why do you keep oscillating? What systematic confusion \
persists across multiple verses?
2. EXPLICIT DECISION RULES: for each ambiguous case, write an if/then rule \
that leaves NO room for interpretation.
3. SELF-CHECK PROCEDURE: a step-by-step verification checklist to run before \
finalizing output.
This must be a full replacement — include everything you need.
Output ONLY the analysis, rules, and checklist — no preamble."""

SELF_PATCH_EXISTING = """
You also have existing self-improvement instructions from previous rounds:

Your current patch:
{existing_patch}

Incorporate what is still relevant from your current patch, plus the new \
feedback above, into one unified set of instructions."""


def _count_unique_attempts(attempts):
    """Count unique non-empty outputs in attempt history."""
    seen = set()
    for a in attempts:
        stripped = a.strip()
        if stripped:
            seen.add(stripped)
    return len(seen)


def _stability_level(unique_count, converged):
    """Classify stability using unified 4-level scale (AD-2).

    Level 0: Easy     — stable at R1 or R2a (≤2 unique outputs)
    Level 1: Mild     — stable at R2b (3 unique outputs)
    Level 2: Moderate — stable at R2c-R2d (4 unique outputs)
    Level 3: Strong   — stable at R2e+ or never converged (5+ unique outputs)

    Returns (level_name, level_int).
    """
    if not converged:
        return "strong", 3
    if unique_count >= 5:
        return "strong", 3
    if unique_count >= 4:
        return "moderate", 2
    if unique_count >= 3:
        return "mild", 1
    return "easy", 0


def generate_model_patch(unstable_model, unstable_attempts, stable_output,
                         unv_sn, stable_models, models, target_version,
                         verse_key=None, book_eng="", existing_patch="",
                         verbose=False, converged=True,
                         past_trigger2_verses=None):
    """Generate a model-specific patch via feedback from stable models.

    Patch intensity scales with instability:
      - mild   (3 unique outputs): standard feedback + self-patch
      - moderate (4 unique):       + full attempt history analysis + root cause
      - strong  (5+ or unstable):  + past trigger2 history + prescriptive rules

    Step 1: Each stable model gives feedback on what the unstable model got wrong.
    Step 2: The unstable model writes its own patch from both feedbacks.
    All artifacts are saved to round2_results/{model}/trigger2_patches/.

    Returns (patch_text, record) where record has all feedbacks and patch.
    patch_text is "" if generation fails.
    """
    chap, sec = verse_key if verse_key else (0, 0)

    # Calculate instability score
    unique_count = _count_unique_attempts(unstable_attempts)
    level, score = _stability_level(unique_count, converged)
    convergence_status = "never converged" if not converged else f"converged after {len(unstable_attempts)} attempts"

    # Build attempt list for prompt
    attempt_lines = []
    labels = ["R1", "R2a", "R2b", "R2c", "R2d", "R2e", "R2f"]
    for i, attempt in enumerate(unstable_attempts):
        label = labels[i] if i < len(labels) else f"attempt_{i}"
        if attempt.strip():
            attempt_lines.append(f"{label}: {attempt}")
    attempt_text = "\n".join(attempt_lines) if attempt_lines else "(all empty)"

    # Build past trigger2 section for strong level
    past_trigger2_section = ""
    if level == "strong" and past_trigger2_verses:
        lines = [f"\nThis model has triggered instability patches on {len(past_trigger2_verses)} previous verse(s):"]
        for pv in past_trigger2_verses:
            lines.append(f"  - {pv}")
        lines.append("Look for COMMON PATTERNS across these failures.\n")
        past_trigger2_section = "\n".join(lines)

    # Select feedback prompt template by level
    if level == "strong":
        feedback_prompt = FEEDBACK_PROMPT_STRONG.format(
            stable_output=stable_output,
            unv_sn=unv_sn,
            attempt_list=attempt_text,
            unique_count=unique_count,
            convergence_status=convergence_status,
            past_trigger2_section=past_trigger2_section,
        )
    elif level == "moderate":
        feedback_prompt = FEEDBACK_PROMPT_MODERATE.format(
            stable_output=stable_output,
            unv_sn=unv_sn,
            attempt_list=attempt_text,
            unique_count=unique_count,
        )
    else:  # mild
        feedback_prompt = FEEDBACK_PROMPT_MILD.format(
            stable_output=stable_output,
            unv_sn=unv_sn,
            attempt_list=attempt_text,
        )

    print(f"  Instability: {level} (score={score}, unique_outputs={unique_count}, converged={converged})")

    # Record everything
    record = {
        "verse": f"{chap}:{sec}",
        "unstable_model": unstable_model,
        "stable_models": stable_models,
        "stable_output": stable_output,
        "unstable_attempts": unstable_attempts,
        "instability_level": level,
        "instability_score": score,
        "unique_output_count": unique_count,
        "feedbacks": {},
        "self_patch": "",
        "feedback_prompt": feedback_prompt,
    }

    # Step 1: Get feedback from each stable model
    feedbacks = []
    for stable_name in stable_models:
        model_info = _find_model(stable_name, models)
        if not model_info:
            continue

        print(f"    [{stable_name}] giving feedback to {unstable_model}...", end=" ", flush=True)
        t_start = time.time()
        result = call_llm(
            brand=model_info["brand"], model=model_info["model"],
            system_prompt="You are a biblical Hebrew and Chinese translation expert.",
            user_prompt=feedback_prompt,
            target_version=target_version,
            verbose=verbose,
            mode="freeform",
        )
        elapsed_s = int(time.time() - t_start)

        feedback = result.get("text", "")
        if not feedback or len(feedback) < 10:
            feedback = str(result)

        feedbacks.append(feedback)
        record["feedbacks"][stable_name] = feedback
        print(f"{len(feedback)} chars {elapsed_s}s", flush=True)

    if len(feedbacks) < 2:
        print(f"    Failed to get 2 feedbacks, skipping patch generation")
        _save_patch_record(record, unstable_model, book_eng, chap, sec)
        return "", record

    # Step 2: Unstable model writes its own patch (intensity by level)
    existing_section = ""
    if existing_patch:
        existing_section = SELF_PATCH_EXISTING.format(existing_patch=existing_patch)

    # Build past trigger2 section for self-patch prompt (strong level)
    self_past_section = ""
    if level == "strong" and past_trigger2_verses:
        self_past_section = f"\nYou have triggered instability patches on {len(past_trigger2_verses)} previous verse(s): {', '.join(past_trigger2_verses)}. This is a recurring problem.\n"

    if level == "strong":
        self_patch_prompt = SELF_PATCH_PROMPT_STRONG.format(
            feedback_1=feedbacks[0],
            feedback_2=feedbacks[1],
            existing_patch_section=existing_section,
            unique_count=unique_count,
            convergence_status=convergence_status,
            past_trigger2_section=self_past_section,
        )
    elif level == "moderate":
        self_patch_prompt = SELF_PATCH_PROMPT_MODERATE.format(
            feedback_1=feedbacks[0],
            feedback_2=feedbacks[1],
            existing_patch_section=existing_section,
            unique_count=unique_count,
        )
    else:  # mild
        self_patch_prompt = SELF_PATCH_PROMPT_MILD.format(
            feedback_1=feedbacks[0],
            feedback_2=feedbacks[1],
            existing_patch_section=existing_section,
        )
    record["self_patch_prompt"] = self_patch_prompt

    unstable_info = _find_model(unstable_model, models)
    if not unstable_info:
        _save_patch_record(record, unstable_model, book_eng, chap, sec)
        return "", record

    print(f"    [{unstable_model}] writing self-patch...", end=" ", flush=True)
    t_start = time.time()
    result = call_llm(
        brand=unstable_info["brand"], model=unstable_info["model"],
        system_prompt="You are writing additional instructions for yourself to improve SN placement accuracy.",
        user_prompt=self_patch_prompt,
        target_version=target_version,
        verbose=verbose,
        mode="freeform",
    )
    elapsed_s = int(time.time() - t_start)

    patch_text = result.get("text", "")
    record["self_patch"] = patch_text

    print(f"{len(patch_text)} chars {elapsed_s}s", flush=True)

    # Save full record
    _save_patch_record(record, unstable_model, book_eng, chap, sec)

    return (patch_text, record) if len(patch_text) > 10 else ("", record)


def _save_patch_record(record, unstable_model, book_eng, chap, sec):
    """Save the full patch generation record to disk."""
    patch_dir = os.path.join(SURVEY_DIR, "round2_results", unstable_model,
                             book_eng, "trigger2_patches")
    os.makedirs(patch_dir, exist_ok=True)
    filepath = os.path.join(patch_dir, f"{chap}_{sec}_patch_record.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    print(f"    Patch record saved: {filepath}", flush=True)


def _r2_label(i):
    """Generate R2 attempt label: R2a, R2b, ..., R2z, R2aa, R2ab, ..., R2zz."""
    if i < 26:
        return f"R2{chr(97 + i)}"
    else:
        i2 = i - 26
        return f"R2{chr(97 + i2 // 26)}{chr(97 + i2 % 26)}"


TRIGGER2_VALIDATE_PROMPT = """\
Two other models independently produced and stabilized on the same output \
for this verse. You were unstable (could not converge easily).

Their agreed output:
{stable_output}

UNV+SN (source of truth):
{unv_sn}

LCC original (unannotated):
{lcc_original}

Do you AGREE that their output is correct, or do you DISAGREE?
If you disagree, explain specifically what they got wrong.

Return ONLY a JSON object:
{{
  "agree": true or false,
  "reasoning": "brief explanation"
}}"""


def validate_trigger2(unstable_model, stable_output, unv_sn, lcc_original,
                       models, target_version="lcc", verbose=False):
    """Ask the unstable model if it agrees with the stable pair's output.

    Returns (agrees: bool, reasoning: str)
    """
    model_info = _find_model(unstable_model, models)
    if not model_info:
        return True, "model not found, defaulting to agree"

    prompt = TRIGGER2_VALIDATE_PROMPT.format(
        stable_output=stable_output,
        unv_sn=unv_sn,
        lcc_original=lcc_original,
    )

    print(f"    [{unstable_model}] validating...", end=" ", flush=True)
    t_start = time.time()
    result = call_llm(
        brand=model_info["brand"], model=model_info["model"],
        system_prompt="You are a biblical Hebrew and Chinese translation expert.",
        user_prompt=prompt,
        target_version=target_version,
        verbose=verbose,
        mode="judge",
    )
    elapsed_s = int(time.time() - t_start)

    agrees = result.get("agree", True)
    reasoning = result.get("reasoning", "")

    # Handle string "true"/"false"
    if isinstance(agrees, str):
        agrees = agrees.lower() in ("true", "yes")

    if agrees:
        print(f"AGREES {elapsed_s}s", flush=True)
    else:
        print(f"DISAGREES {elapsed_s}s", flush=True)
        print(f"      Reason: {reasoning[:150]}", flush=True)

    return agrees, reasoning


def _find_model(model_name, models):
    """Find model info dict by name."""
    for m in models:
        if m["name"] == model_name:
            return m
    return None


# ── Auto Prompt Evolution ────────────────────────────────────────────────────

PROMPT_EVOLVE_GENERATE = """\
You are improving a system prompt for Strong's Number annotation projection.

The current prompt (v{current_version}) has a deficiency identified by multiple \
judges on verse {verse_ref}:

{judge_summaries}

Current prompt:
---
{current_prompt}
---

Based on the judges' feedback, write a COMPLETE, improved replacement prompt. \
This is v{new_version}. Include ALL existing content that is still valid, plus \
fixes for the identified issues. Output ONLY the prompt text — no preamble, \
no markdown fences, no commentary."""

PROMPT_EVOLVE_VOTE = """\
Three models each drafted a new version of the SN annotation prompt to fix \
the deficiency identified in verse {verse_ref}.

Current prompt version: v{current_version}
Identified problem: {error_summary}

Draft A ({model_a}):
---
{draft_a}
---

Draft B ({model_b}):
---
{draft_b}
---

Draft C ({model_c}):
---
{draft_c}
---

Which draft best addresses the identified problem while preserving all \
existing functionality? Consider: completeness, clarity, actionability.

Return ONLY a JSON object:
{{
  "best": "A" or "B" or "C",
  "reasoning": "brief explanation"
}}"""


def auto_evolve_prompt(current_prompt, current_version, verse_ref,
                       judge_opinions, models, target_version="lcc",
                       verbose=False):
    """Auto-generate new prompt via 3-model draft + vote.

    1. Each model reads current prompt + judge feedback → generates new prompt
    2. Each model votes on the 3 drafts (2/3 majority)

    Args:
        current_prompt: the current system prompt text
        current_version: e.g., "v1.2"
        verse_ref: e.g., "Gen 1:7"
        judge_opinions: list of dicts with error_identified + prompt_improvement
        models: list of model dicts
        target_version: target Bible version

    Returns:
        (winning_prompt, record) or ("", record) if vote fails
    """
    # Parse version for new version number
    import re
    m = re.match(r'v(\d+)\.(\d+)', current_version)
    if m:
        new_version = f"{m.group(1)}.{int(m.group(2)) + 1}"
    else:
        new_version = current_version + ".1"

    # Build judge summaries
    judge_lines = []
    for i, opinion in enumerate(judge_opinions):
        judge_lines.append(f"Judge {i+1}:")
        judge_lines.append(f"  Error: {opinion.get('error_identified', '')}")
        judge_lines.append(f"  Fix: {opinion.get('prompt_improvement', '')}")
    judge_summaries = '\n'.join(judge_lines)

    error_summary = judge_opinions[0].get('error_identified', '') if judge_opinions else ''

    generate_prompt = PROMPT_EVOLVE_GENERATE.format(
        current_version=current_version,
        new_version=new_version,
        verse_ref=verse_ref,
        judge_summaries=judge_summaries,
        current_prompt=current_prompt,
    )

    # Step 1: Each model generates a draft
    drafts = {}
    record = {
        "verse_ref": verse_ref,
        "current_version": current_version,
        "new_version": f"v{new_version}",
        "judge_opinions": judge_opinions,
        "drafts": {},
        "votes": {},
        "winner": None,
    }

    print(f"\n  ── Auto-Evolve: generating drafts ──")
    for model_info in models:
        model_name = model_info["name"]
        brand = model_info["brand"]
        model_id = model_info["model"]

        print(f"    [{model_name}] drafting v{new_version}...", end=" ", flush=True)
        t_start = time.time()
        result = call_llm(
            brand=brand, model=model_id,
            system_prompt="You are an expert prompt engineer for biblical NLP tasks.",
            user_prompt=generate_prompt,
            target_version=target_version,
            verbose=verbose,
            mode="freeform",
        )
        elapsed_s = int(time.time() - t_start)

        draft = result.get("text", "")
        drafts[model_name] = draft
        record["drafts"][model_name] = draft
        print(f"{len(draft)} chars {elapsed_s}s", flush=True)

    if len(drafts) < 3:
        print(f"  Failed to get 3 drafts, aborting auto-evolve")
        return "", record

    # Step 2: Each model votes
    model_names = [m["name"] for m in models]
    vote_prompt = PROMPT_EVOLVE_VOTE.format(
        verse_ref=verse_ref,
        current_version=current_version,
        error_summary=error_summary,
        model_a=model_names[0], draft_a=drafts[model_names[0]],
        model_b=model_names[1], draft_b=drafts[model_names[1]],
        model_c=model_names[2], draft_c=drafts[model_names[2]],
    )

    print(f"\n  ── Auto-Evolve: voting ──")
    votes = {}
    for model_info in models:
        model_name = model_info["name"]
        brand = model_info["brand"]
        model_id = model_info["model"]

        print(f"    [{model_name}] voting...", end=" ", flush=True)
        t_start = time.time()
        result = call_llm(
            brand=brand, model=model_id,
            system_prompt="You are evaluating prompt quality for biblical NLP.",
            user_prompt=vote_prompt,
            target_version=target_version,
            verbose=verbose,
            mode="judge",
        )
        elapsed_s = int(time.time() - t_start)

        best = result.get("best", "?").upper()
        reasoning = result.get("reasoning", "")
        votes[model_name] = {"best": best, "reasoning": reasoning}
        record["votes"][model_name] = votes[model_name]
        print(f"→ {best} {elapsed_s}s", flush=True)

    # Tally votes (2/3 majority)
    label_to_model = {"A": model_names[0], "B": model_names[1], "C": model_names[2]}
    vote_counts = {}
    for v in votes.values():
        b = v["best"]
        if b in ("A", "B", "C"):
            vote_counts[b] = vote_counts.get(b, 0) + 1

    winner_label = None
    for label, count in vote_counts.items():
        if count >= 2:
            winner_label = label
            break

    if winner_label is None:
        print(f"  No 2/3 majority in prompt vote — auto-evolve failed")
        return "", record

    winner_model = label_to_model[winner_label]
    winning_prompt = drafts[winner_model]
    record["winner"] = {"label": winner_label, "model": winner_model}

    print(f"  → Winner: {winner_label} ({winner_model}) with {vote_counts[winner_label]}/3 votes")

    return winning_prompt, record


# ── Backward compat alias ────────────────────────────────────────────────────
# Keep old name available for consensus.py imports during transition
def tally_judgments(judgments_for_verse, round1_results_or_conv, sn_field="lcc_sn"):
    """Legacy tally — delegates to tally_r2_debate."""
    return tally_r2_debate(judgments_for_verse, round1_results_or_conv, sn_field)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _eng_to_chi(book_eng):
    """Reverse lookup: English book name → Chinese abbreviation."""
    from llm_direct_sn_unv2notyet import CHI_TO_ENG
    for chi, eng in CHI_TO_ENG.items():
        if eng == book_eng:
            return chi
    return book_eng  # fallback
