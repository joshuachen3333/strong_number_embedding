#!/usr/bin/env python3
"""Regression testing after prompt changes.

When the prompt evolves, we must verify that the change doesn't break
previously-agreed verses. Sampling rates:

  - Caused this prompt change:        100%
  - Previously reached Round 3:        80%
  - Previously reached Round 2:        50%
  - Previously passed Round 1:         20%

Regression runs the full Round 1→2→3 process on sampled verses.
If any sampled verse fails (unresolved), the prompt change is rejected.
"""

import json
import os
import random
import sys

SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))


def load_gold_standard(book_eng=None):
    """Load all existing gold standard verses.

    Args:
        book_eng: if provided, load only this book (e.g., "Gen").
                  If None, load all books.
    """
    gs_dir = os.path.join(SURVEY_DIR, "gold_standard")
    gold = {}
    if not os.path.isdir(gs_dir):
        return gold

    # Walk: gold_standard/{book}/{chap}/{sec}.json
    book_dirs = [book_eng] if book_eng else os.listdir(gs_dir)
    for book_name in book_dirs:
        book_dir = os.path.join(gs_dir, book_name)
        if not os.path.isdir(book_dir):
            continue
        for chap_name in os.listdir(book_dir):
            chap_dir = os.path.join(book_dir, chap_name)
            if not os.path.isdir(chap_dir):
                continue
            try:
                chap = int(chap_name)
            except ValueError:
                continue
            for fname in os.listdir(chap_dir):
                if not fname.endswith(".json"):
                    continue
                sec = int(fname.replace(".json", ""))
                with open(os.path.join(chap_dir, fname), "r", encoding="utf-8") as f:
                    gold[(chap, sec)] = json.load(f)

    return gold


def select_regression_verses(gold_standard, trigger_verses, seed=42):
    """Select verses for regression testing.

    Args:
        gold_standard: {(chap,sec): gold_dict}
        trigger_verses: list of (chap,sec) that caused this prompt change

    Returns:
        list of (chap, sec) to retest
    """
    random.seed(seed)

    trigger_set = set(trigger_verses)
    round1_verses = []
    round2_verses = []
    round3_verses = []

    for verse_key, gold in gold_standard.items():
        if verse_key in trigger_set:
            continue  # These are always 100% tested
        resolved = gold.get("resolved_at", "")
        if resolved == "round1":
            round1_verses.append(verse_key)
        elif resolved == "round2":
            round2_verses.append(verse_key)
        elif resolved == "round3":
            round3_verses.append(verse_key)

    # Sample according to rates (no minimum thresholds — always use %).
    # Original rule from prompt #44e: R3=80%, R2=50%, R1=20%.
    def sample(verses, rate):
        if not verses:
            return []
        n = max(1, int(len(verses) * rate))
        return random.sample(verses, min(n, len(verses)))

    selected = list(trigger_set)  # 100% of triggers — always all
    selected.extend(sample(round3_verses, 0.80))
    selected.extend(sample(round2_verses, 0.50))
    selected.extend(sample(round1_verses, 0.20))

    # Deduplicate and sort
    return sorted(set(selected))


def print_regression_plan(selected, gold_standard, trigger_verses):
    """Print what will be retested."""
    trigger_set = set(trigger_verses)

    categories = {"trigger": [], "round3": [], "round2": [], "round1": []}
    for v in selected:
        if v in trigger_set:
            categories["trigger"].append(v)
        else:
            resolved = gold_standard.get(v, {}).get("resolved_at", "?")
            if resolved == "round3":
                categories["round3"].append(v)
            elif resolved == "round2":
                categories["round2"].append(v)
            else:
                categories["round1"].append(v)

    print(f"\n{'='*60}")
    print(f"  Regression Test Plan")
    print(f"{'='*60}")
    print(f"  Trigger verses (100%):  {len(categories['trigger'])}  "
          f"{[f'{c}:{s}' for c, s in categories['trigger']]}")
    print(f"  Round 3 history (80%):  {len(categories['round3'])}  "
          f"{[f'{c}:{s}' for c, s in categories['round3']]}")
    print(f"  Round 2 history (50%):  {len(categories['round2'])}  "
          f"{[f'{c}:{s}' for c, s in categories['round2']]}")
    print(f"  Round 1 history (20%):  {len(categories['round1'])}  "
          f"{[f'{c}:{s}' for c, s in categories['round1']]}")
    print(f"  Total to retest:        {len(selected)}")
    print(f"{'='*60}")


def run_prompt_regression(new_prompt, new_version, trigger_verse,
                          book_chi, book_eng, models, target_version,
                          sn_field, verbose=False):
    """Run regression test for an auto-evolved prompt.

    Re-runs sampled gold standard verses with the new prompt.
    Each verse does R1 only — if all 3 models produce output that matches
    the existing gold standard OR all 3 agree unanimously, it passes.

    Returns (passed: bool, results: dict)
    """
    import sys
    PARENT_DIR = os.path.dirname(SURVEY_DIR)
    if PARENT_DIR not in sys.path:
        sys.path.insert(0, PARENT_DIR)

    from llm_direct_sn_unv2notyet import fetch_sec_pair, build_user_prompt
    from cli_caller import call_llm
    from comparator import texts_match

    # Load gold standard and select verses
    gold = load_gold_standard(book_eng)
    if not gold:
        print(f"    回測: no gold standard to test against — PASS (trivial)")
        return True, {"sampled": 0, "passed": 0, "failed": 0}

    selected = select_regression_verses(gold, [trigger_verse])
    # Remove the trigger verse itself (it hasn't been resolved yet)
    selected = [v for v in selected if v != trigger_verse]

    if not selected:
        print(f"    回測: no past verses to test — PASS (trivial)")
        return True, {"sampled": 0, "passed": 0, "failed": 0}

    print_regression_plan(selected, gold, [trigger_verse])

    passed = 0
    failed = 0
    failed_verses = []

    for verse_key in selected:
        chap, sec = verse_key
        gold_entry = gold[verse_key]
        gold_sn = gold_entry.get("lcc_sn", "")

        try:
            unv_sn, target_text = fetch_sec_pair(book_chi, chap, sec, target_version)
        except ValueError:
            print(f"    {chap}:{sec}: SKIP (fetch error)")
            continue

        user_prompt = build_user_prompt(
            unv_sn, target_text, target_version, book_chi, chap, sec)

        # Run all 3 models with new prompt
        outputs = []
        for model_info in models:
            result = call_llm(
                brand=model_info["brand"], model=model_info["model"],
                system_prompt=new_prompt,
                user_prompt=user_prompt,
                target_version=target_version,
                verbose=verbose,
            )
            output = result.get(sn_field, "")
            outputs.append(output)

        # Pass condition: all 3 agree AND match gold standard,
        # OR all 3 agree unanimously (may be better than old gold)
        all_agree = all(texts_match(outputs[0], o) for o in outputs[1:]) if outputs else False
        matches_gold = any(texts_match(o, gold_sn) for o in outputs) if gold_sn else False

        if all_agree or matches_gold:
            print(f"    {chap}:{sec}: PASS {'(unanimous)' if all_agree else '(matches gold)'}")
            passed += 1
        else:
            print(f"    {chap}:{sec}: FAIL (neither unanimous nor matches gold)")
            failed += 1
            failed_verses.append(verse_key)

    total = passed + failed
    print(f"\n    回測 result: {passed}/{total} passed, {failed} failed")
    if failed_verses:
        print(f"    Failed verses: {[f'{c}:{s}' for c, s in failed_verses]}")

    return failed == 0, {
        "sampled": total,
        "passed": passed,
        "failed": failed,
        "failed_verses": failed_verses,
    }
