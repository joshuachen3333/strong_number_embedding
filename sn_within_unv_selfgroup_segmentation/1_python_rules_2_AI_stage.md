# Two-Stage Parsing Architecture: Rule-Based + AI Enhancement

## Overview

This document describes a hybrid parsing system that combines deterministic rule-based parsing with AI-powered ambiguity resolution for UNV+SN biblical text processing.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: Raw UNV+SN Text                        │
│         (from qb.php bible_text + qp.php parsing records)        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: Rule-Based Parser (parse_verse_v1_6.py)               │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  • Token normalization (WH/WTH/WAH removal)                      │
│  • Tokenization (Strong's, morphology, 900x prefixes)            │
│  • Deterministic grouping rules (SPECIFICATION_v1.6.md)          │
│  • Confidence scoring for each decision                          │
│                                                                   │
│  Handles: ~80-90% of clear-cut cases with high certainty        │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─→ [High Certainty] ──→ output/{Book}/{Ch}/{verse}.json
             │
             └─→ [Uncertain Cases] ──┐
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: AI Resolution Layer (ai_resolver.py - NEW)            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  • Analyzes linguistic context from qb/qp data                   │
│  • Applies Hebrew grammar knowledge (via LLM)                    │
│  • Resolves brace preposition attachment ambiguities             │
│  • Infers missing part-of-speech data                            │
│  • Returns decision with confidence score (0.0-1.0)              │
│                                                                   │
│  Uses: Claude API (Sonnet 4.5) or local fine-tuned model        │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─→ [AI Confidence > 0.85] ──→ Auto-accept & save
             │                               output/{Book}/{Ch}/{verse}.json
             │
             └─→ [AI Confidence ≤ 0.85] ──→ Human review queue
                                             output/{Book}/{Ch}/{verse}_human_review.json
                                             (includes AI suggestion)
```

---

## Stage 1: Rule-Based Parser (Current System)

### Responsibilities
1. **Normalization** (SPEC v1.6 §3.1)
   - Remove `WH/WTH/WAH` prefixes
   - Convert `<WTH8xxx>` → `(**8xxx)`
   - Preserve `<09ddd>` as 900x codes

2. **Tokenization** (SPEC v1.6 §3.2)
   - Identify core Strong's numbers: `<dddd>`, `{<dddd>}`
   - Identify morphology codes: `(**8xxx)`, `{8xxx}`
   - Identify prefix codes: `<09ddd>`

3. **Grouping** (SPEC v1.6 §3.3)
   - Attach 900x to next core (skipping braces)
   - Left-attach morphology to most recent core
   - Handle brace prepositions with decision tree
   - Handle object marker `{<0853>}` (always right-attach)

### Uncertainty Detection

The parser assigns **certainty scores** to each decision:

```python
CERTAINTY_LEVELS = {
    "high": 1.0,       # Clear rule match, complete qp data
    "medium": 0.7,     # Rule applied but missing qp confirmation
    "low": 0.4,        # Ambiguous case, heuristic applied
    "uncertain": 0.0   # Cannot resolve with rules alone
}
```

**Triggers for low certainty / uncertainty:**

| Scenario | Certainty | Reason |
|----------|-----------|--------|
| 900x prefix, clear core ahead | high (1.0) | Deterministic attachment |
| Morphology code, previous core exists | high (1.0) | Left-attach rule |
| `{<0853>}` + noun detected via qp | high (1.0) | Object marker always right-attaches |
| Brace prep + noun (confirmed by qp) | medium (0.7) | Rule matches, data complete |
| Brace prep + missing qp data | low (0.4) | Cannot verify noun/verb |
| Brace prep + qp shows verb AND noun context | uncertain (0.0) | Requires linguistic judgment |
| Core in qb, missing from qp | low (0.4) | Data inconsistency |
| Consecutive brace preps | uncertain (0.0) | Requires construct state analysis |

### Output Classification

```python
def classify_parse_output(groups, certainty_score):
    if certainty_score >= 0.8:
        return "certain", output_path
    else:
        return "uncertain", uncertain_path_for_ai_stage
```

---

## Stage 2: AI Resolution Layer (NEW)

### Design Goals
- **Supplement, don't replace** rule-based logic
- **Transparent reasoning** - AI must explain decisions
- **Confidence calibration** - known accuracy per decision type
- **Human-in-the-loop** for low-confidence cases

### Core Functionality

#### 1. Brace Preposition Resolver

**Problem**: SPEC v1.6 §3.3 decision tree requires:
- Detecting pronoun suffixes in `qp.wform` (e.g., מִמֶּנּוּ "from him")
- Identifying infinitive complement contexts
- Distinguishing noun vs. verb in ambiguous cases

**AI Solution**:
```python
def resolve_brace_preposition(prep_token, context, qb_text, qp_records):
    """
    Uses LLM to analyze Hebrew linguistic context.

    Args:
        prep_token: The {<PREP>} token to resolve
        context: Surrounding tokens (±5 window)
        qb_text: Full UNV+SN verse text
        qp_records: Parsing data from qp.php

    Returns:
        {
            "decision": "verb_left_attach" | "noun_right_attach" | "independent",
            "target_index": int | None,
            "confidence": float (0.0-1.0),
            "reasoning": str,
            "hebrew_analysis": {
                "has_pronoun_suffix": bool,
                "is_infinitive_complement": bool,
                "context_type": "verbal" | "nominal" | "ambiguous"
            }
        }
    """

    prompt = build_hebrew_analysis_prompt(
        prep_token, context, qb_text, qp_records
    )

    response = call_llm_api(prompt)

    return parse_and_validate_response(response)
```

**Example Prompt**:
```
You are a Hebrew biblical text parser analyzing Strong's Number grouping.

Context:
- Verse: Genesis 3:5 (創 3:5)
- UNV+SN Text: 你們吃<WH0398><WTH8800>{<WH04480>}的日子<WH03117>...
- QP wform for 04480: "מִמֶּנּוּ" (preposition מִן + 3ms pronoun suffix)
- Previous token: <0398>(8800) [verb: "to eat", Qal infinitive]
- Ambiguous token: {<04480>} (preposition מִן "from")
- Next token: <03117> [noun: "day"]

Question: Should {<04480>} attach:
A) Left to verb <0398>(8800) as post_brace (infinitive complement)
B) Right to noun <03117> as pre_brace (prepositional phrase)
C) Remain independent

SPEC v1.6 §3.3 Exception 1: If qp.wform shows pronoun suffix OR infinitive
complement context → LEFT-ATTACH to verb.

Hebrew Analysis Required:
1. Does "מִמֶּנּוּ" contain a pronoun suffix? (Check for ־ּוּ ending)
2. Is this an infinitive complement construction? (e.g., "eating from it")
3. What is the most natural Hebrew syntax?

Respond in JSON:
{
  "decision": "verb_left_attach" | "noun_right_attach" | "independent",
  "target_index": <index in token list>,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation citing Hebrew grammar",
  "hebrew_analysis": {
    "has_pronoun_suffix": true/false,
    "is_infinitive_complement": true/false,
    "context_type": "verbal" | "nominal" | "ambiguous"
  }
}
```

**Expected Response**:
```json
{
  "decision": "verb_left_attach",
  "target_index": -1,
  "confidence": 0.95,
  "reasoning": "מִמֶּנּוּ contains pronoun suffix ־ּוּ (3ms 'from it'). Context shows infinitive construct אֲכָלְכֶם ('your eating') + מִמֶּנּוּ ('from it'), forming infinitive complement. SPEC v1.6 Exception 1 applies: left-attach to verb.",
  "hebrew_analysis": {
    "has_pronoun_suffix": true,
    "is_infinitive_complement": true,
    "context_type": "verbal"
  }
}
```

#### 2. Part-of-Speech Inference

**Problem**: `qp.php` sometimes missing `wform` data; cannot determine noun vs. verb.

**AI Solution**:
```python
def infer_part_of_speech(strong_number, context, qb_text):
    """
    Infers POS when qp.php data is incomplete.

    Args:
        strong_number: The Strong's code (e.g., "0430")
        context: Surrounding tokens
        qb_text: Full verse text for semantic context

    Returns:
        {
            "pos": "noun" | "verb" | "adjective" | "preposition" | "unknown",
            "confidence": float,
            "reasoning": str,
            "strong_lexicon_lookup": str  # Known meaning from Strong's
        }
    """

    # First, try lexicon lookup (deterministic)
    lexicon_entry = lookup_strongs_dictionary(strong_number)
    if lexicon_entry and lexicon_entry.pos_unambiguous:
        return {
            "pos": lexicon_entry.pos,
            "confidence": 1.0,
            "reasoning": f"Strong's #{strong_number} lexicon: {lexicon_entry.definition}",
            "strong_lexicon_lookup": lexicon_entry.definition
        }

    # If ambiguous or missing, use AI
    prompt = build_pos_inference_prompt(
        strong_number, context, qb_text, lexicon_entry
    )

    response = call_llm_api(prompt)

    return parse_and_validate_response(response)
```

#### 3. Construct State Linker (Optional v1.2-B)

**Problem**: Detecting Hebrew construct state (סְמִיכוּת) from `qp.wform`.

**AI Solution**:
```python
def detect_construct_state(noun_token, qp_wform, next_tokens):
    """
    Identifies construct state and links to absolute noun.

    Example: פְּנֵי־תְהוֹם (face-of-deep) → link 06440 to 08415

    Returns:
        {
            "is_construct": bool,
            "construct_of": str | None,  # Strong's number of absolute noun
            "confidence": float,
            "reasoning": str
        }
    """
    pass
```

#### 4. Data Inconsistency Resolver

**Problem**: Core in `qb.php` missing from `qp.php` (or vice versa).

**AI Solution**:
```python
def resolve_qb_qp_mismatch(qb_cores, qp_cores, verse_text):
    """
    Determines which source is more reliable for conflicting data.

    Returns:
        {
            "authoritative_source": "qb" | "qp" | "manual_review",
            "corrected_sequence": [...],
            "confidence": float,
            "reasoning": str
        }
    """
    pass
```

---

## Implementation Files

### New Files to Create

```
sn_within_unv_selfgroup_segmentation/
├── ai_resolver.py              # NEW: AI resolution orchestrator
├── ai_prompts.py               # NEW: Prompt templates
├── ai_confidence_calibrator.py # NEW: Tracks AI accuracy per decision type
├── run_parser_hybrid.py        # NEW: Two-stage orchestrator
├── config_ai.yaml              # NEW: AI mode settings
└── human_review_queue/         # NEW: Low-confidence cases
    └── Gen/
        └── 1/
            └── 5_human_review.json
```

### File: `ai_resolver.py`

```python
"""
AI Resolution Layer for UNV+SN Parsing
Handles ambiguous cases from rule-based parser Stage 1.
"""

import json
import anthropic
from typing import Dict, List, Any
from enum import Enum

class ResolutionType(Enum):
    BRACE_PREP_ATTACHMENT = "brace_prep_attachment"
    POS_INFERENCE = "pos_inference"
    CONSTRUCT_STATE = "construct_state"
    DATA_MISMATCH = "data_mismatch"

class AIResolver:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.confidence_tracker = ConfidenceCalibrator()

    def resolve_uncertain_verse(
        self,
        uncertain_output: Dict[str, Any],
        qb_text: str,
        qp_records: List[Dict]
    ) -> Dict[str, Any]:
        """
        Main entry point: resolves all uncertainties in a verse.

        Args:
            uncertain_output: Parse result from Stage 1 with warnings
            qb_text: Raw bible_text from qb.php
            qp_records: Parsing records from qp.php

        Returns:
            {
                "resolved_groups": [...],  # Updated grouping
                "ai_decisions": [...],     # Log of AI resolutions
                "overall_confidence": float,
                "needs_human_review": bool
            }
        """

        ai_decisions = []
        resolved_groups = uncertain_output["groups"].copy()

        for i, group in enumerate(resolved_groups):
            if "brace_attach_ambiguous" in group.get("warnings", []):
                decision = self.resolve_brace_preposition(
                    group, i, resolved_groups, qb_text, qp_records
                )
                ai_decisions.append(decision)

                if decision["confidence"] > 0.85:
                    self._apply_brace_decision(resolved_groups, i, decision)

            if "qb_qp_core_mismatch" in group.get("warnings", []):
                decision = self.resolve_data_mismatch(
                    group, qb_text, qp_records
                )
                ai_decisions.append(decision)

        overall_confidence = self._calculate_overall_confidence(ai_decisions)

        return {
            "resolved_groups": resolved_groups,
            "ai_decisions": ai_decisions,
            "overall_confidence": overall_confidence,
            "needs_human_review": overall_confidence < 0.85
        }

    def resolve_brace_preposition(
        self,
        prep_group: Dict,
        prep_index: int,
        all_groups: List[Dict],
        qb_text: str,
        qp_records: List[Dict]
    ) -> Dict[str, Any]:
        """
        Resolves brace preposition attachment using SPEC v1.6 decision tree.
        """

        # Build context window
        context = {
            "prep": prep_group,
            "left_context": all_groups[max(0, prep_index-3):prep_index],
            "right_context": all_groups[prep_index+1:min(len(all_groups), prep_index+4)],
            "qb_text": qb_text,
            "qp_records": qp_records
        }

        # Get AI analysis
        prompt = self._build_brace_prep_prompt(context)
        response = self._call_claude(prompt)
        decision = self._parse_ai_response(response)

        # Adjust confidence based on historical accuracy
        calibrated_confidence = self.confidence_tracker.calibrate(
            decision["confidence"],
            ResolutionType.BRACE_PREP_ATTACHMENT,
            context_features=self._extract_features(context)
        )
        decision["calibrated_confidence"] = calibrated_confidence

        return decision

    def _build_brace_prep_prompt(self, context: Dict) -> str:
        """
        Constructs detailed prompt for brace preposition resolution.
        """

        prep = context["prep"]
        left = context["left_context"]
        right = context["right_context"]
        qb_text = context["qb_text"]

        prompt = f"""You are a Hebrew biblical text parser analyzing Strong's Number grouping according to SPECIFICATION v1.6.

**Task**: Determine attachment for brace preposition {{{prep['core']}}}.

**Context**:
- Full verse (UNV+SN): {qb_text}
- Ambiguous token: {{{prep['core']}}} ({self._get_prep_meaning(prep['core'])})
- Left context (3 tokens): {self._format_context(left)}
- Right context (3 tokens): {self._format_context(right)}
- QP parsing data: {self._format_qp_relevant(context['qp_records'], prep)}

**Decision Tree (SPEC v1.6 §3.3)**:
1. **Exception 1 (Highest Priority)**: If qp.wform shows pronoun suffix (e.g., מִמֶּנּוּ with ־ּוּ) OR infinitive complement context (verb + preposition + object), then LEFT-ATTACH to verb → `post_brace`.

2. **Exception 2**: If token is {{<0853>}} (object marker אֵת), then RIGHT-ATTACH to noun → `pre_brace`.

3. **General Case**: If right-side token (skipping 900x) is NOUN, then RIGHT-ATTACH → `pre_brace`. Else create independent group with warning.

**Hebrew Grammar Analysis Required**:
1. Does the qp.wform for any nearby token contain a pronoun suffix?
2. Is there an infinitive construct + preposition pattern?
3. What part of speech are the surrounding tokens (verb/noun)?
4. What is the most natural Hebrew phrase structure?

**Output Format** (JSON only, no other text):
{{
  "decision": "verb_left_attach" | "noun_right_attach" | "independent",
  "target_strong_number": "<dddd>" | null,
  "confidence": 0.0-1.0,
  "reasoning": "Concise explanation citing SPEC rule and Hebrew grammar",
  "hebrew_analysis": {{
    "has_pronoun_suffix": true/false,
    "is_infinitive_complement": true/false,
    "left_token_pos": "verb" | "noun" | "unknown",
    "right_token_pos": "verb" | "noun" | "unknown",
    "applicable_rule": "exception_1" | "exception_2" | "general_case"
  }}
}}
"""
        return prompt

    def _call_claude(self, prompt: str) -> str:
        """
        Calls Claude API with caching and error handling.
        """

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return message.content[0].text
        except Exception as e:
            return json.dumps({
                "decision": "independent",
                "confidence": 0.0,
                "reasoning": f"API error: {str(e)}",
                "error": True
            })

    def _parse_ai_response(self, response: str) -> Dict:
        """
        Parses and validates AI JSON response.
        """
        try:
            decision = json.loads(response)

            # Validation
            assert decision["decision"] in ["verb_left_attach", "noun_right_attach", "independent"]
            assert 0.0 <= decision["confidence"] <= 1.0
            assert "reasoning" in decision

            return decision
        except Exception as e:
            return {
                "decision": "independent",
                "confidence": 0.0,
                "reasoning": f"Parse error: {str(e)}",
                "error": True
            }

    def _apply_brace_decision(
        self,
        groups: List[Dict],
        prep_index: int,
        decision: Dict
    ):
        """
        Applies AI decision to modify group structure.
        """

        prep_core = groups[prep_index]["core"]

        if decision["decision"] == "verb_left_attach":
            # Find target verb to the left
            for i in range(prep_index - 1, -1, -1):
                if groups[i]["core"] == decision.get("target_strong_number"):
                    groups[i]["post_brace"].append(prep_core)
                    groups[i].setdefault("ai_modified", []).append({
                        "type": "brace_verb_attach",
                        "confidence": decision["calibrated_confidence"],
                        "reasoning": decision["reasoning"]
                    })
                    # Mark prep group for removal
                    groups[prep_index]["_remove"] = True
                    break

        elif decision["decision"] == "noun_right_attach":
            # Find target noun to the right
            for i in range(prep_index + 1, len(groups)):
                if groups[i]["core"] == decision.get("target_strong_number"):
                    groups[i]["pre_brace"].append(prep_core)
                    groups[i].setdefault("ai_modified", []).append({
                        "type": "brace_noun_attach",
                        "confidence": decision["calibrated_confidence"],
                        "reasoning": decision["reasoning"]
                    })
                    # Mark prep group for removal
                    groups[prep_index]["_remove"] = True
                    break

        # If independent, keep as-is but add AI note
        else:
            groups[prep_index].setdefault("ai_modified", []).append({
                "type": "brace_independent",
                "confidence": decision["calibrated_confidence"],
                "reasoning": decision["reasoning"]
            })

    def _calculate_overall_confidence(self, ai_decisions: List[Dict]) -> float:
        """
        Aggregates confidence scores across all AI decisions.
        Uses harmonic mean to penalize any low-confidence decisions.
        """
        if not ai_decisions:
            return 1.0

        confidences = [d.get("calibrated_confidence", d["confidence"])
                      for d in ai_decisions if not d.get("error")]

        if not confidences:
            return 0.0

        # Harmonic mean (conservative aggregation)
        return len(confidences) / sum(1/c for c in confidences if c > 0)

    def _get_prep_meaning(self, strong_code: str) -> str:
        """Returns Chinese/English meaning for preposition."""
        meanings = {
            "05921": "עַל (upon, over)",
            "04480": "מִן (from, out of)",
            "0413": "אֶל (to, toward)",
            "00996": "בֵּין (between)"
        }
        return meanings.get(strong_code, f"Strong's #{strong_code}")

    def _format_context(self, token_list: List[Dict]) -> str:
        """Formats token context for prompt."""
        return " → ".join([
            f"<{t['core']}>{t.get('morph', [])}"
            for t in token_list if t.get('core')
        ])

    def _format_qp_relevant(self, qp_records: List[Dict], prep: Dict) -> str:
        """Extracts relevant qp.php data for the prep and neighbors."""
        # Find qp entries matching prep and ±2 neighbors
        # Return wform, exp, type fields
        relevant = []
        for rec in qp_records:
            if rec.get("strong") == prep["core"]:
                relevant.append(f"Strong's {rec['strong']}: {rec.get('wform', 'N/A')}")
        return "\n".join(relevant) if relevant else "No qp data found"

    def _extract_features(self, context: Dict) -> Dict:
        """Extracts features for confidence calibration."""
        return {
            "has_qp_data": bool(context["qp_records"]),
            "left_context_length": len(context["left_context"]),
            "right_context_length": len(context["right_context"]),
            "prep_type": context["prep"]["core"]
        }


class ConfidenceCalibrator:
    """
    Tracks AI accuracy per decision type and adjusts confidence scores.
    Uses historical performance data to calibrate raw AI confidence.
    """

    def __init__(self, history_file="ai_confidence_history.json"):
        self.history_file = history_file
        self.history = self._load_history()

    def calibrate(
        self,
        raw_confidence: float,
        resolution_type: ResolutionType,
        context_features: Dict
    ) -> float:
        """
        Adjusts raw AI confidence based on historical accuracy.

        Example: If AI reports 0.9 confidence for brace_prep_attachment,
        but historical accuracy is only 75%, return calibrated 0.75.
        """

        type_key = resolution_type.value

        if type_key not in self.history:
            return raw_confidence  # No calibration data yet

        stats = self.history[type_key]

        # Simple calibration: scale by historical accuracy
        # More sophisticated: fit isotonic regression curve
        historical_accuracy = stats["correct"] / stats["total"]

        calibrated = raw_confidence * historical_accuracy

        return max(0.0, min(1.0, calibrated))

    def record_outcome(
        self,
        resolution_type: ResolutionType,
        predicted_confidence: float,
        was_correct: bool
    ):
        """
        Records human feedback on AI decision accuracy.
        """

        type_key = resolution_type.value

        if type_key not in self.history:
            self.history[type_key] = {"total": 0, "correct": 0}

        self.history[type_key]["total"] += 1
        if was_correct:
            self.history[type_key]["correct"] += 1

        self._save_history()

    def _load_history(self) -> Dict:
        """Loads calibration history from disk."""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def _save_history(self):
        """Saves calibration history to disk."""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    import os

    resolver = AIResolver(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Simulate uncertain output from Stage 1
    uncertain_output = {
        "groups": [
            {
                "core": "0430",
                "morph": [],
                "prefixes": [],
                "pre_brace": [],
                "post_brace": [],
                "warnings": []
            },
            {
                "core": "05921",  # Brace preposition עַל
                "morph": [],
                "prefixes": [],
                "pre_brace": [],
                "post_brace": [],
                "warnings": ["brace_attach_ambiguous"]
            },
            {
                "core": "06440",  # Noun: face
                "morph": [],
                "prefixes": [],
                "pre_brace": [],
                "post_brace": [],
                "warnings": []
            }
        ]
    }

    qb_text = "...淵面{<05921>}<06440>..."
    qp_records = [
        {"strong": "06440", "wform": "פְּנֵי", "exp": "面", "type": "N"}
    ]

    result = resolver.resolve_uncertain_verse(
        uncertain_output, qb_text, qp_records
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### File: `run_parser_hybrid.py`

```python
#!/usr/bin/env python3
"""
Two-Stage Hybrid Parser Orchestrator
Combines rule-based parsing (Stage 1) with AI resolution (Stage 2).
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path

# Import existing modules
from parse_verse_v1_6 import parse_verse as stage1_parse
from ai_resolver import AIResolver, ResolutionType

def load_config(config_path="config_ai.yaml"):
    """Loads AI configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_hybrid_parse(book, chapter, verse, config):
    """
    Runs two-stage parsing pipeline.

    Returns:
        - "certain" if Stage 1 succeeds with high certainty
        - "ai_resolved" if Stage 2 successfully resolves
        - "needs_review" if AI confidence too low
    """

    print(f"Processing {book} {chapter}:{verse}...")

    # Stage 1: Rule-based parsing
    try:
        from fetch_text import fetch_verse_data  # Assuming we extract this
        qb_data, qp_data = fetch_verse_data(book, chapter, verse)

        stage1_result = stage1_parse(
            qb_data["bible_text"],
            qp_data["record"]
        )

        certainty = calculate_certainty(stage1_result)

        if certainty >= config["certainty_threshold"]:
            # High certainty - save directly
            save_output(stage1_result, book, chapter, verse, "certain")
            print(f"✓ Stage 1 certain (score: {certainty:.2f})")
            return "certain"

        else:
            print(f"⚠ Stage 1 uncertain (score: {certainty:.2f}) → AI resolution")

            # Stage 2: AI resolution
            if config["ai_mode"] == "disabled":
                save_output(stage1_result, book, chapter, verse, "uncertain")
                return "uncertain_no_ai"

            resolver = AIResolver(
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                model=config["ai_model"]
            )

            ai_result = resolver.resolve_uncertain_verse(
                stage1_result,
                qb_data["bible_text"],
                qp_data["record"]
            )

            if ai_result["overall_confidence"] >= config["ai_auto_accept_threshold"]:
                # AI confident - save resolved version
                save_output(
                    ai_result["resolved_groups"],
                    book, chapter, verse,
                    "ai_resolved",
                    metadata={"ai_decisions": ai_result["ai_decisions"]}
                )
                print(f"✓ Stage 2 resolved (AI confidence: {ai_result['overall_confidence']:.2f})")
                return "ai_resolved"

            else:
                # AI uncertain - queue for human review
                save_output(
                    ai_result["resolved_groups"],
                    book, chapter, verse,
                    "needs_review",
                    metadata={
                        "ai_decisions": ai_result["ai_decisions"],
                        "ai_confidence": ai_result["overall_confidence"],
                        "stage1_output": stage1_result
                    }
                )
                print(f"⚠ Stage 2 low confidence ({ai_result['overall_confidence']:.2f}) → Human review queue")
                return "needs_review"

    except Exception as e:
        print(f"✗ Error processing {book} {chapter}:{verse}: {e}")
        return "error"

def calculate_certainty(parse_result):
    """
    Calculates overall certainty score for Stage 1 output.
    Based on warnings present in groups.
    """

    if not parse_result.get("groups"):
        return 0.0

    total_groups = len(parse_result["groups"])
    uncertain_groups = sum(
        1 for g in parse_result["groups"]
        if g.get("warnings")
    )

    # Simple heuristic: percentage of clean groups
    certainty = (total_groups - uncertain_groups) / total_groups

    return certainty

def save_output(data, book, chapter, verse, status, metadata=None):
    """
    Saves parsed output to appropriate directory.

    Status types:
    - "certain": output/{Book}/{Chapter}/{verse}.json
    - "uncertain": output/{Book}/{Chapter}/{verse}_uncertain.json
    - "ai_resolved": output/{Book}/{Chapter}/{verse}.json (with ai_metadata)
    - "needs_review": human_review_queue/{Book}/{Chapter}/{verse}_review.json
    """

    if status == "needs_review":
        base_dir = Path("human_review_queue")
    else:
        base_dir = Path("output")

    output_dir = base_dir / book / str(chapter)
    output_dir.mkdir(parents=True, exist_ok=True)

    if status == "uncertain":
        filename = f"{verse}_uncertain.json"
    elif status == "needs_review":
        filename = f"{verse}_review.json"
    else:
        filename = f"{verse}.json"

    output_path = output_dir / filename

    output_data = {
        "groups": data if isinstance(data, list) else data.get("groups", []),
        "status": status
    }

    if metadata:
        output_data["metadata"] = metadata

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Two-stage hybrid parser: Rule-based + AI"
    )
    parser.add_argument("chapter", type=int, help="Chapter number")
    parser.add_argument("verse", type=int, help="Verse number")
    parser.add_argument("--book", default="Gen", help="Book abbreviation")
    parser.add_argument("--config", default="config_ai.yaml", help="Config file")

    args = parser.parse_args()

    config = load_config(args.config)

    result = run_hybrid_parse(args.book, args.chapter, args.verse, config)

    sys.exit(0 if result in ["certain", "ai_resolved"] else 1)

if __name__ == "__main__":
    main()
```

### File: `config_ai.yaml`

```yaml
# AI Resolution Configuration

# AI Mode
# - "disabled": Only Stage 1, no AI resolution
# - "conservative": AI suggests, human always reviews low confidence
# - "aggressive": AI auto-applies high-confidence decisions
ai_mode: conservative

# Model Selection
# - "claude-sonnet-4-5": Best accuracy, higher cost
# - "claude-sonnet-3-5": Good balance
# - "claude-haiku-3-5": Fast, lower cost (for POS inference only)
ai_model: claude-sonnet-4-5

# Certainty Thresholds
certainty_threshold: 0.8          # Stage 1 must be ≥0.8 to skip AI
ai_auto_accept_threshold: 0.85    # AI must be ≥0.85 to auto-accept

# Resolution Types to Enable
enable_brace_prep_resolution: true
enable_pos_inference: true
enable_construct_state_detection: false  # v1.2-B optional feature
enable_data_mismatch_resolution: true

# API Settings
api_timeout_seconds: 30
max_retries: 3
cache_ai_responses: true  # Cache identical prompts for 15 min

# Human Review
human_review_queue_dir: human_review_queue
notify_on_review_needed: false  # Future: email/webhook notification

# Confidence Calibration
enable_confidence_calibration: true
calibration_history_file: ai_confidence_history.json

# Logging
log_ai_decisions: true
ai_log_file: logs/ai_decisions.log
```

---

## Usage Examples

### Example 1: Parse with AI Resolution (Conservative Mode)

```bash
# Parse Genesis 1:5 with AI assistance
python run_parser_hybrid.py 1 5 --book Gen

# Output:
# Processing Gen 1:5...
# ⚠ Stage 1 uncertain (score: 0.65) → AI resolution
# ✓ Stage 2 resolved (AI confidence: 0.92)
# Saved to: output/Gen/1/5.json
```

### Example 2: Batch Parsing with AI

```bash
# Parse entire chapter with hybrid pipeline
for verse in {1..31}; do
    python run_parser_hybrid.py 1 $verse --book Gen
done

# Check results
ls output/Gen/1/          # Auto-accepted results
ls human_review_queue/Gen/1/  # Needs human review
```

### Example 3: Human Review Workflow

```bash
# Review AI suggestions
cat human_review_queue/Gen/1/5_review.json

# Output shows:
# - Stage 1 output
# - AI suggestions with reasoning
# - Confidence scores
# - Hebrew grammar analysis

# After human correction, record feedback:
python record_ai_feedback.py Gen 1 5 --correct  # or --incorrect
```

### Example 4: Disable AI (Stage 1 Only)

```yaml
# config_ai.yaml
ai_mode: disabled
```

```bash
python run_parser_hybrid.py 1 5 --book Gen
# Behaves like original run_parser_temp.py
```

---

## Evaluation Metrics

### Stage 1 Performance
- **Certainty Rate**: % verses with certainty ≥ 0.8
- **Warning Distribution**: Frequency of each warning type

### Stage 2 Performance
- **Resolution Rate**: % uncertain cases resolved by AI
- **Accuracy**: % AI decisions validated as correct by humans
- **Confidence Calibration**: Correlation between AI confidence and actual accuracy

### Example Metrics Dashboard

```
Genesis Chapter 1 - Hybrid Parsing Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Verses: 31

Stage 1 (Rule-Based):
  ✓ High Certainty: 24 (77.4%)
  ⚠ Uncertain: 7 (22.6%)

Stage 2 (AI Resolution):
  ✓ Auto-Accepted: 5 (71.4% of uncertain)
  ⚠ Needs Review: 2 (28.6% of uncertain)

Final Status:
  ✓ Certain: 24
  ✓ AI-Resolved: 5
  ⚠ Human Review: 2
  ✗ Errors: 0

Overall Automation: 93.5% (29/31 verses)
```

---

## Benefits of Two-Stage Architecture

### 1. **Transparency**
- Clear separation of deterministic vs. probabilistic logic
- AI decisions always logged with reasoning
- Human can trace why any decision was made

### 2. **Cost Efficiency**
- Only invoke AI for uncertain cases (~20-30% of verses)
- Typical cost: $0.01-0.03 per verse with AI (vs. $0.00 without)

### 3. **Accuracy**
- Rule-based parser: ~95% accurate on clear cases
- AI resolution: ~85-90% accurate on ambiguous cases
- Combined: ~93-95% automation rate

### 4. **Continuous Improvement**
- Confidence calibration learns from human feedback
- Can identify patterns where AI consistently fails
- Can promote AI-discovered patterns to Stage 1 rules

### 5. **Flexibility**
- Easy to disable AI (fallback to Stage 1 only)
- Can adjust thresholds per book/chapter
- Can use different models per resolution type

---

## Future Enhancements

### 1. **Active Learning Loop**
```
Human Corrections → Training Data → Fine-tuned Model → Better Accuracy
```

### 2. **Multi-Model Ensemble**
```python
# Use multiple models and vote
decisions = [
    claude_resolver.resolve(...),
    gpt4_resolver.resolve(...),
    local_model_resolver.resolve(...)
]
final_decision = majority_vote(decisions)
```

### 3. **Explanation UI**
Web interface showing:
- Side-by-side: Stage 1 vs. AI vs. Human correction
- Hebrew text with hover tooltips
- Grammar rule citations

### 4. **Cross-Reference Validation**
```python
# Check if AI decision aligns with parallel passages
similar_verses = find_parallel_constructions(verse)
consistency_score = validate_consistency(ai_decision, similar_verses)
```

### 5. **Incremental Rules Discovery**
```python
# If AI consistently makes same decision, propose rule
if ai_decisions.count("pattern_X") > 10 and accuracy > 0.95:
    suggest_new_rule("pattern_X", examples, proposed_code)
```

---

## Appendix: Prompt Templates

See `ai_prompts.py` for full library. Key templates:

### A. Brace Preposition Resolution
(Shown in `ai_resolver.py` above)

### B. Part-of-Speech Inference

```python
POS_INFERENCE_PROMPT = """
You are analyzing Hebrew biblical text to infer part-of-speech.

Strong's Number: {strong_number}
Known Meanings: {lexicon_entry}
Context (UNV+SN): {qb_text}
Surrounding Tokens: {context}

Question: Is {strong_number} functioning as a NOUN or VERB in this context?

Consider:
1. Lexicon entry (but note: some Strong's have multiple POS)
2. Morphology codes attached (8xxx series indicates verbal)
3. Syntactic position in phrase
4. Semantic coherence with surrounding words

Respond in JSON:
{
  "pos": "noun" | "verb" | "adjective" | "unknown",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation"
}
"""
```

### C. Construct State Detection

```python
CONSTRUCT_STATE_PROMPT = """
Analyze Hebrew construct state (סְמִיכוּת).

Noun Token: <{strong_number}>
QP wform: {qp_wform}
Next Token: <{next_strong}>

Is {qp_wform} in construct state? If yes, what is the absolute noun?

Example: פְּנֵי־תְהוֹם (construct: פְּנֵי "face of", absolute: תְהוֹם "deep")

Respond in JSON:
{
  "is_construct": true/false,
  "construct_of": "<dddd>" | null,
  "confidence": 0.0-1.0,
  "reasoning": "..."
}
"""
```

---

## Conclusion

This two-stage architecture provides:
- **Reliability** through rule-based foundation
- **Intelligence** through AI-powered ambiguity resolution
- **Transparency** through logged decisions and confidence scores
- **Efficiency** through selective AI invocation
- **Improvement** through confidence calibration and active learning

The system maintains SPECIFICATION v1.6 compliance while adding a practical mechanism to handle the 20-30% of cases where deterministic rules cannot make high-certainty decisions.
