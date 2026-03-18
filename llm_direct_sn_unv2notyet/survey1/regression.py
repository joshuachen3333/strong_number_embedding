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


def load_gold_standard():
    """Load all existing gold standard verses."""
    gs_dir = os.path.join(SURVEY_DIR, "gold_standard")
    gold = {}
    if not os.path.isdir(gs_dir):
        return gold

    for chap_name in os.listdir(gs_dir):
        chap_dir = os.path.join(gs_dir, chap_name)
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

    # Sample according to rates
    def sample(verses, rate):
        n = max(1, int(len(verses) * rate)) if verses else 0
        return random.sample(verses, min(n, len(verses)))

    selected = list(trigger_set)  # 100% of triggers
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
