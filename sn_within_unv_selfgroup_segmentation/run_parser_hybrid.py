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
import subprocess
from pathlib import Path
from datetime import datetime

# Import existing modules
try:
    from parse_verse_v1_6 import parse_verse_v1_6 as stage1_parse_raw

    def stage1_parse(bible_text, qp_records):
        """Wrapper to adapt parse_verse_v1_6 to expected interface."""
        # parse_verse_v1_6 expects JSON strings, returns JSON string or text
        qb_json = json.dumps({"record": [{"bible_text": bible_text}]})
        qp_json = json.dumps({"record": qp_records})
        result_json = stage1_parse_raw(qb_json, qp_json, output_format="json")
        # Result is JSON string, parse to get groups list
        return json.loads(result_json)

except ImportError:
    print("Error: parse_verse_v1_6.py not found")
    sys.exit(1)

try:
    from ai_resolver import AIResolver, ResolutionType
except ImportError:
    print("Error: ai_resolver.py not found")
    sys.exit(1)


def load_config(config_path="config_ai.yaml"):
    """Loads AI configuration."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Warning: {config_path} not found, using defaults")
        return {
            "ai_mode": "conservative",
            "ai_model": "claude-sonnet-4-5-20250929",
            "certainty_threshold": 0.8,
            "ai_auto_accept_threshold": 0.85,
            "enable_brace_prep_resolution": True,
            "output_dir": "output",
            "human_review_queue_dir": "human_review_queue",
            "log_ai_decisions": True,
            "ai_log_file": "logs/ai_decisions.log"
        }


def fetch_verse_data(book, chapter, verse):
    """
    Fetches verse data using fetch_text.sh script.

    Returns:
        (qb_data, qp_data) tuple with parsed JSON
    """
    try:
        # Run fetch_text.sh
        result = subprocess.run(
            ["./fetch_text.sh", "--engs", book, "--chap", str(chapter), "--sec", str(verse)],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse the two JSON outputs
        output = result.stdout.strip()

        # Split by the header lines to extract JSON
        lines = output.split('\n')

        # Find qb JSON section
        qb_start = -1
        qp_start = -1

        for i, line in enumerate(lines):
            if '=== qb.php' in line:
                qb_start = i + 1
            elif '=== qp.php' in line:
                qp_start = i + 1

        if qb_start == -1 or qp_start == -1:
            raise ValueError("Could not find qb or qp sections in output")

        # Extract JSON text
        qb_json_str = '\n'.join(lines[qb_start:qp_start-1])
        qp_json_str = '\n'.join(lines[qp_start:])

        qb_data = json.loads(qb_json_str)
        qp_data = json.loads(qp_json_str)

        return qb_data, qp_data

    except subprocess.CalledProcessError as e:
        print(f"Error fetching verse data: {e}")
        print(f"stderr: {e.stderr}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Output was: {output[:500]}")
        raise


def calculate_certainty(parse_result):
    """
    Calculates overall certainty score for Stage 1 output.
    Based on warnings present in groups.
    """

    groups = parse_result if isinstance(parse_result, list) else parse_result.get("groups", [])

    if not groups:
        return 0.0

    total_groups = len(groups)
    uncertain_groups = sum(
        1 for g in groups
        if g.get("warnings")
    )

    # Count severity of warnings
    high_severity_warnings = ["brace_attach_ambiguous", "qb_qp_core_mismatch"]
    high_severity_count = sum(
        1 for g in groups
        for w in g.get("warnings", [])
        if w in high_severity_warnings
    )

    # Calculate certainty score
    certainty = (total_groups - uncertain_groups) / total_groups

    # Penalty for high-severity warnings
    if high_severity_count > 0:
        certainty -= (high_severity_count * 0.1)

    return max(0.0, min(1.0, certainty))


def save_output(data, book, chapter, verse, status, config, metadata=None):
    """
    Saves parsed output to appropriate directory.

    Status types:
    - "certain": output/{Book}/{Chapter}/{verse}.json
    - "uncertain": output/{Book}/{Chapter}/{verse}_uncertain.json
    - "ai_resolved": output/{Book}/{Chapter}/{verse}.json (with ai_metadata)
    - "needs_review": human_review_queue/{Book}/{Chapter}/{verse}_review.json
    """

    if status == "needs_review":
        base_dir = Path(config.get("human_review_queue_dir", "human_review_queue"))
    else:
        base_dir = Path(config.get("output_dir", "output"))

    output_dir = base_dir / book / str(chapter)
    output_dir.mkdir(parents=True, exist_ok=True)

    if status == "uncertain":
        filename = f"{verse}{config.get('uncertain_suffix', '_uncertain')}.json"
    elif status == "needs_review":
        filename = f"{verse}{config.get('review_suffix', '_review')}.json"
    elif status == "ai_resolved":
        filename = f"{verse}.json"
    else:
        filename = f"{verse}.json"

    output_path = output_dir / filename

    output_data = {
        "groups": data if isinstance(data, list) else data.get("groups", []),
        "status": status,
        "timestamp": datetime.now().isoformat()
    }

    if metadata:
        output_data["metadata"] = metadata

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return output_path


def log_ai_decision(config, book, chapter, verse, decision, status):
    """Logs AI decision to log file."""
    if not config.get("log_ai_decisions", False):
        return

    log_file = config.get("ai_log_file", "logs/ai_decisions.log")
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    with open(log_file, 'a', encoding='utf-8') as f:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "verse": f"{book} {chapter}:{verse}",
            "status": status,
            "decision": decision
        }
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def run_hybrid_parse(book, chapter, verse, config):
    """
    Runs two-stage parsing pipeline.

    Returns:
        - "certain" if Stage 1 succeeds with high certainty
        - "ai_resolved" if Stage 2 successfully resolves
        - "needs_review" if AI confidence too low
        - "uncertain_no_ai" if AI disabled and Stage 1 uncertain
    """

    print(f"Processing {book} {chapter}:{verse}...")

    # Stage 1: Rule-based parsing
    try:
        qb_data, qp_data = fetch_verse_data(book, chapter, verse)

        # Extract bible_text and records
        if "record" in qb_data and len(qb_data["record"]) > 0:
            bible_text = qb_data["record"][0].get("bible_text", "")
        else:
            raise ValueError("No bible_text in qb_data")

        qp_records = qp_data.get("record", [])

        # Call Stage 1 parser
        stage1_result = stage1_parse(bible_text, qp_records)

        certainty = calculate_certainty(stage1_result)

        if certainty >= config["certainty_threshold"]:
            # High certainty - save directly
            output_path = save_output(stage1_result, book, chapter, verse, "certain", config)
            print(f"✓ Stage 1 certain (score: {certainty:.2f})")
            print(f"  Saved to: {output_path}")
            return "certain"

        else:
            print(f"⚠ Stage 1 uncertain (score: {certainty:.2f}) → AI resolution")

            # Stage 2: AI resolution
            if config["ai_mode"] == "disabled":
                output_path = save_output(stage1_result, book, chapter, verse, "uncertain", config)
                print(f"  AI disabled, saved as uncertain: {output_path}")
                return "uncertain_no_ai"

            # Check if ANTHROPIC_API_KEY is available
            if not os.environ.get("ANTHROPIC_API_KEY"):
                print(f"  ⚠ ANTHROPIC_API_KEY not set, skipping AI resolution")
                output_path = save_output(stage1_result, book, chapter, verse, "uncertain", config)
                print(f"  Saved as uncertain: {output_path}")
                return "uncertain_no_ai"

            resolver = AIResolver(
                api_key=os.environ.get("ANTHROPIC_API_KEY"),
                model=config["ai_model"]
            )

            ai_result = resolver.resolve_uncertain_verse(
                stage1_result,
                bible_text,
                qp_records
            )

            # Log AI decision
            log_ai_decision(config, book, chapter, verse, ai_result["ai_decisions"], "ai_attempt")

            if ai_result["overall_confidence"] >= config["ai_auto_accept_threshold"]:
                # AI confident - save resolved version
                output_path = save_output(
                    ai_result["resolved_groups"],
                    book, chapter, verse,
                    "ai_resolved",
                    config,
                    metadata={
                        "ai_decisions": ai_result["ai_decisions"],
                        "ai_confidence": ai_result["overall_confidence"],
                        "stage1_certainty": certainty
                    }
                )
                print(f"✓ Stage 2 resolved (AI confidence: {ai_result['overall_confidence']:.2f})")
                print(f"  Saved to: {output_path}")
                return "ai_resolved"

            else:
                # AI uncertain - queue for human review
                output_path = save_output(
                    ai_result["resolved_groups"],
                    book, chapter, verse,
                    "needs_review",
                    config,
                    metadata={
                        "ai_decisions": ai_result["ai_decisions"],
                        "ai_confidence": ai_result["overall_confidence"],
                        "stage1_certainty": certainty,
                        "stage1_output": stage1_result
                    }
                )
                print(f"⚠ Stage 2 low confidence ({ai_result['overall_confidence']:.2f}) → Human review queue")
                print(f"  Saved to: {output_path}")
                return "needs_review"

    except Exception as e:
        print(f"✗ Error processing {book} {chapter}:{verse}: {e}")
        import traceback
        traceback.print_exc()
        return "error"


def main():
    parser = argparse.ArgumentParser(
        description="Two-stage hybrid parser: Rule-based + AI"
    )
    parser.add_argument("chapter", type=int, help="Chapter number")
    parser.add_argument("verse", type=int, help="Verse number")
    parser.add_argument("--book", default="Gen", help="Book abbreviation")
    parser.add_argument("--config", default="config_ai.yaml", help="Config file")
    parser.add_argument("--no-ai", action="store_true", help="Disable AI resolution (Stage 1 only)")

    args = parser.parse_args()

    config = load_config(args.config)

    if args.no_ai:
        config["ai_mode"] = "disabled"

    result = run_hybrid_parse(args.book, args.chapter, args.verse, config)

    sys.exit(0 if result in ["certain", "ai_resolved"] else 1)


if __name__ == "__main__":
    main()
