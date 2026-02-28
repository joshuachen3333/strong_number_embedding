#!/usr/bin/env python3
"""
AI Resolution Layer for UNV+SN Parsing
Handles ambiguous cases from rule-based parser Stage 1.
"""

import json
import os
from typing import Dict, List, Any, Optional
from enum import Enum


class ResolutionType(Enum):
    BRACE_PREP_ATTACHMENT = "brace_prep_attachment"
    POS_INFERENCE = "pos_inference"
    CONSTRUCT_STATE = "construct_state"
    DATA_MISMATCH = "data_mismatch"


class AIResolver:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize AI resolver.

        Args:
            api_key: Anthropic API key (or reads from ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        try:
            import anthropic
            self.anthropic = anthropic
            api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
            self.confidence_tracker = ConfidenceCalibrator()
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

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
        resolved_groups = uncertain_output.copy() if isinstance(uncertain_output, list) else uncertain_output.get("groups", [])
        resolved_groups = [g.copy() for g in resolved_groups]  # Deep copy

        for i, group in enumerate(resolved_groups):
            warnings = group.get("warnings", [])

            if "brace_attach_ambiguous" in warnings:
                decision = self.resolve_brace_preposition(
                    group, i, resolved_groups, qb_text, qp_records
                )
                ai_decisions.append(decision)

                if decision.get("confidence", 0) > 0.85 and not decision.get("error"):
                    self._apply_brace_decision(resolved_groups, i, decision)

            if "qb_qp_core_mismatch" in warnings:
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
            "prep_index": prep_index,
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
        if not decision.get("error"):
            calibrated_confidence = self.confidence_tracker.calibrate(
                decision.get("confidence", 0.5),
                ResolutionType.BRACE_PREP_ATTACHMENT,
                context_features=self._extract_features(context)
            )
            decision["calibrated_confidence"] = calibrated_confidence
        else:
            decision["calibrated_confidence"] = 0.0

        return decision

    def resolve_data_mismatch(
        self,
        group: Dict,
        qb_text: str,
        qp_records: List[Dict]
    ) -> Dict[str, Any]:
        """
        Resolves inconsistencies between qb and qp data.
        """
        # Simple strategy: trust qb as primary source
        return {
            "decision": "trust_qb",
            "confidence": 0.8,
            "reasoning": "QB is primary source for Strong's numbers; QP provides supplementary morphology",
            "resolution_type": "data_mismatch"
        }

    def _build_brace_prep_prompt(self, context: Dict) -> str:
        """
        Constructs detailed prompt for brace preposition resolution.
        """

        prep = context["prep"]
        left = context["left_context"]
        right = context["right_context"]
        qb_text = context["qb_text"]

        prompt = f"""You are a Hebrew biblical text parser analyzing Strong's Number grouping according to SPECIFICATION v1.6.

**Task**: Determine attachment for brace preposition {{<{prep.get('core', 'UNKNOWN')}>}}.

**Context**:
- Full verse (UNV+SN): {qb_text[:200]}...
- Ambiguous token: {{<{prep.get('core', 'UNKNOWN')}>}} ({self._get_prep_meaning(prep.get('core', ''))})
- Left context (up to 3 tokens): {self._format_context(left)}
- Right context (up to 3 tokens): {self._format_context(right)}
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
}}"""
        return prompt

    def _call_claude(self, prompt: str) -> str:
        """
        Calls Claude API with error handling.
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
            # Try to extract JSON if wrapped in markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()

            decision = json.loads(response)

            # Validation
            assert decision["decision"] in ["verb_left_attach", "noun_right_attach", "independent"], \
                f"Invalid decision: {decision['decision']}"
            assert 0.0 <= decision["confidence"] <= 1.0, \
                f"Invalid confidence: {decision['confidence']}"
            assert "reasoning" in decision

            return decision
        except Exception as e:
            return {
                "decision": "independent",
                "confidence": 0.0,
                "reasoning": f"Parse error: {str(e)}",
                "error": True,
                "raw_response": response[:500]
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

        prep_core = groups[prep_index].get("core")

        if decision["decision"] == "verb_left_attach":
            # Find target verb to the left
            target = decision.get("target_strong_number")
            for i in range(prep_index - 1, -1, -1):
                if groups[i].get("core") == target or target is None:
                    if "post_brace" not in groups[i]:
                        groups[i]["post_brace"] = []
                    groups[i]["post_brace"].append(prep_core)
                    if "ai_modified" not in groups[i]:
                        groups[i]["ai_modified"] = []
                    groups[i]["ai_modified"].append({
                        "type": "brace_verb_attach",
                        "confidence": decision.get("calibrated_confidence", decision["confidence"]),
                        "reasoning": decision["reasoning"]
                    })
                    # Mark prep group for removal
                    groups[prep_index]["_remove"] = True
                    break

        elif decision["decision"] == "noun_right_attach":
            # Find target noun to the right
            target = decision.get("target_strong_number")
            for i in range(prep_index + 1, len(groups)):
                if groups[i].get("core") == target or target is None:
                    if "pre_brace" not in groups[i]:
                        groups[i]["pre_brace"] = []
                    groups[i]["pre_brace"].append(prep_core)
                    if "ai_modified" not in groups[i]:
                        groups[i]["ai_modified"] = []
                    groups[i]["ai_modified"].append({
                        "type": "brace_noun_attach",
                        "confidence": decision.get("calibrated_confidence", decision["confidence"]),
                        "reasoning": decision["reasoning"]
                    })
                    # Mark prep group for removal
                    groups[prep_index]["_remove"] = True
                    break

        # If independent, keep as-is but add AI note
        else:
            if "ai_modified" not in groups[prep_index]:
                groups[prep_index]["ai_modified"] = []
            groups[prep_index]["ai_modified"].append({
                "type": "brace_independent",
                "confidence": decision.get("calibrated_confidence", decision["confidence"]),
                "reasoning": decision["reasoning"]
            })

    def _calculate_overall_confidence(self, ai_decisions: List[Dict]) -> float:
        """
        Aggregates confidence scores across all AI decisions.
        Uses harmonic mean to penalize any low-confidence decisions.
        """
        if not ai_decisions:
            return 1.0

        confidences = [d.get("calibrated_confidence", d.get("confidence", 0.5))
                      for d in ai_decisions if not d.get("error")]

        if not confidences:
            return 0.0

        # Harmonic mean (conservative aggregation)
        return len(confidences) / sum(1/c if c > 0 else 999999 for c in confidences)

    def _get_prep_meaning(self, strong_code: str) -> str:
        """Returns Chinese/English meaning for preposition."""
        meanings = {
            "05921": "עַל (upon, over, 在…之上)",
            "04480": "מִן (from, out of, 從)",
            "0413": "אֶל (to, toward, 向)",
            "00996": "בֵּין (between, 在…之間)"
        }
        return meanings.get(strong_code, f"Strong's #{strong_code}")

    def _format_context(self, token_list: List[Dict]) -> str:
        """Formats token context for prompt."""
        if not token_list:
            return "[none]"

        formatted = []
        for t in token_list:
            core = t.get('core', '?')
            morph = t.get('morph', [])
            morph_str = f"({','.join(morph)})" if morph else ""
            formatted.append(f"<{core}>{morph_str}")

        return " → ".join(formatted)

    def _format_qp_relevant(self, qp_records: List[Dict], prep: Dict) -> str:
        """Extracts relevant qp.php data for the prep and neighbors."""
        if not qp_records:
            return "No qp data available"

        relevant = []
        prep_core = prep.get("core")

        for rec in qp_records:
            rec_strong = rec.get("strong", "")
            # Match with or without leading zeros
            if rec_strong == prep_core or rec_strong.lstrip('0') == prep_core.lstrip('0'):
                wform = rec.get('wform', 'N/A')
                exp = rec.get('exp', 'N/A')
                relevant.append(f"Strong's {rec_strong}: wform='{wform}', meaning='{exp}'")

        return "\n".join(relevant) if relevant else f"No qp data found for {prep_core}"

    def _extract_features(self, context: Dict) -> Dict:
        """Extracts features for confidence calibration."""
        return {
            "has_qp_data": bool(context["qp_records"]),
            "left_context_length": len(context["left_context"]),
            "right_context_length": len(context["right_context"]),
            "prep_type": context["prep"].get("core", "unknown")
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
        if stats["total"] == 0:
            return raw_confidence

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


# Example usage and testing
if __name__ == "__main__":
    # Test mode - requires ANTHROPIC_API_KEY in environment
    try:
        resolver = AIResolver()

        # Simulate uncertain output from Stage 1
        uncertain_output = [
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

        qb_text = "...淵面{<05921>}<06440>..."
        qp_records = [
            {"strong": "06440", "wform": "פְּנֵי", "exp": "面", "type": "N"}
        ]

        result = resolver.resolve_uncertain_verse(
            uncertain_output, qb_text, qp_records
        )

        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure ANTHROPIC_API_KEY is set in environment")
