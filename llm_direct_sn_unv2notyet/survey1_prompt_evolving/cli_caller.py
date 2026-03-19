#!/usr/bin/env python3
"""Unified CLI wrapper for calling claude/gemini/codex CLIs.

Simplified version of the parent's brand-specific callers — no retry loops,
no rate-limit handling. For survey use: fail fast, let orchestrator decide.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

# Add parent to path for imports
SURVEY_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SURVEY_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

from llm_direct_sn_unv2notyet import (
    parse_stream_json, parse_gemini_stream_json, parse_codex_jsonl,
    _extract_json, build_json_schema,
)

# Default models for the 3-model consensus
DEFAULT_MODELS = [
    {"name": "opus",                "brand": "claude", "model": "opus"},
    {"name": "gemini-3-pro-preview","brand": "gemini", "model": "gemini-3-pro-preview"},
    {"name": "gpt-5.4",            "brand": "codex",  "model": "gpt-5.4"},
]

DEFAULT_TIMEOUT = 300  # 5 min


def call_llm(brand: str, model: str, system_prompt: str, user_prompt: str,
             target_version: str = "lcc", timeout: int = DEFAULT_TIMEOUT,
             verbose: bool = False, mode: str = "production") -> dict:
    """Call LLM via CLI, return parsed result dict.

    mode="production": uses JSON schema for {lcc_sn, confidence, notes}.
    mode="judge": free-form prompt, parses JSON from raw text.
                  Returns raw parsed dict (e.g. {best, corrected, reasoning}).
    mode="freeform": free-form prompt, returns {"text": raw_text}.
                     For feedback/patch generation where plain text is expected.
    """
    sn_field = f"{target_version}_sn"

    if brand == "claude":
        return _call_claude(model, system_prompt, user_prompt,
                            target_version, sn_field, timeout, verbose, mode)
    elif brand == "gemini":
        return _call_gemini(model, system_prompt, user_prompt,
                            target_version, sn_field, timeout, verbose, mode)
    elif brand == "codex":
        return _call_codex(model, system_prompt, user_prompt,
                           target_version, sn_field, timeout, verbose, mode)
    else:
        return {"error": True, "notes": [f"Unknown brand: {brand}"]}


def _call_claude(model, system_prompt, user_prompt, target_version,
                 sn_field, timeout, verbose, mode="production"):
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return {"error": True, "notes": ["'claude' CLI not found"]}

    prompt = system_prompt + "\n\n" + user_prompt

    cmd = [
        claude_bin, "-p",
        "--output-format", "stream-json",
        "--model", model,
        "--no-session-persistence",
        "--disallowed-tools", "Bash,Edit,Write,Read,Glob,Grep,Task",
    ]

    if mode == "production":
        json_schema = build_json_schema(target_version)
        cmd.extend(["--json-schema", json_schema])

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    if verbose:
        print(f"  [claude {model}] calling ({mode})...", flush=True)

    try:
        result_proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            env=env, input=prompt
        )
    except subprocess.TimeoutExpired:
        return {"error": True, "notes": [f"Timeout ({timeout}s)"]}

    if result_proc.returncode != 0:
        return {"error": True, "notes": [f"CLI error: {result_proc.stderr[:300]}"]}

    if mode == "production":
        result, _ = parse_stream_json(result_proc.stdout, sn_field)
        return result

    if mode == "freeform":
        return _parse_claude_freeform_text(result_proc.stdout)

    # Judge mode: extract text from stream-json, then parse as JSON
    return _parse_claude_freeform(result_proc.stdout)


def _call_gemini(model, system_prompt, user_prompt, target_version,
                 sn_field, timeout, verbose, mode="production"):
    gemini_bin = shutil.which("gemini")
    if not gemini_bin:
        return {"error": True, "notes": ["'gemini' CLI not found"]}

    if mode == "production":
        json_schema = build_json_schema(target_version)
        full_prompt = (system_prompt + "\n\n" + user_prompt +
                       "\n\nRespond with ONLY valid JSON matching this schema:\n" +
                       json_schema)
    else:
        full_prompt = system_prompt + "\n\n" + user_prompt

    cmd = [
        gemini_bin,
        "-p", full_prompt,
        "-y",
        "--output-format", "stream-json",
        "--model", model,
    ]

    if verbose:
        print(f"  [gemini {model}] calling ({mode})...", flush=True)

    try:
        result_proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"error": True, "notes": [f"Timeout ({timeout}s)"]}

    if result_proc.returncode != 0:
        return {"error": True, "notes": [f"CLI error: {result_proc.stderr[:300]}"]}

    if mode == "production":
        result, _ = parse_gemini_stream_json(result_proc.stdout, sn_field)
        return result

    if mode == "freeform":
        return _parse_gemini_freeform_text(result_proc.stdout)

    # Judge mode: extract text, parse JSON
    return _parse_gemini_freeform(result_proc.stdout)


def _call_codex(model, system_prompt, user_prompt, target_version,
                sn_field, timeout, verbose, mode="production"):
    codex_bin = shutil.which("codex")
    if not codex_bin:
        return {"error": True, "notes": ["'codex' CLI not found"]}

    full_prompt = system_prompt + "\n\n" + user_prompt

    if mode == "production":
        json_schema = build_json_schema(target_version)
        full_prompt += ("\n\nRespond with ONLY valid JSON matching this schema:\n" +
                        json_schema)

    last_msg_file = os.path.join(SURVEY_DIR, ".codex_last_message.txt")

    cmd = [
        codex_bin, "exec",
        "--sandbox", "read-only",
        "--model", model,
        "--output-last-message", last_msg_file,
        "-",
    ]

    if mode == "production":
        # Write schema file (OpenAI requires additionalProperties: false)
        json_schema_str = build_json_schema(target_version)
        schema_obj = json.loads(json_schema_str)
        schema_obj["additionalProperties"] = False
        schema_file = os.path.join(SURVEY_DIR, ".codex_schema.json")
        with open(schema_file, "w", encoding="utf-8") as f:
            json.dump(schema_obj, f)
        cmd.extend(["--output-schema", schema_file])

    if verbose:
        print(f"  [codex {model}] calling ({mode})...", flush=True)

    try:
        result_proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            input=full_prompt,
        )
    except subprocess.TimeoutExpired:
        if os.path.isfile(last_msg_file):
            try:
                with open(last_msg_file, "r", encoding="utf-8") as f:
                    partial = f.read().strip()
                if partial:
                    return _extract_json(partial, sn_field if mode == "production" else "best")
            except IOError:
                pass
        return {"error": True, "notes": [f"Timeout ({timeout}s)"]}

    if result_proc.returncode != 0:
        return {"error": True,
                "notes": [f"CLI error: {(result_proc.stderr + result_proc.stdout)[:300]}"]}

    # Read clean final answer from --output-last-message
    if os.path.isfile(last_msg_file):
        try:
            with open(last_msg_file, "r", encoding="utf-8") as f:
                last_msg = f.read().strip()
            if last_msg:
                if mode == "production":
                    return _extract_json(last_msg, sn_field)
                elif mode == "freeform":
                    return {"text": last_msg}
                else:
                    return _extract_json(last_msg, "best")
        except IOError:
            pass

    if result_proc.stdout.strip():
        if mode == "freeform":
            return {"text": result_proc.stdout.strip()}
        key = sn_field if mode == "production" else "best"
        return _extract_json(result_proc.stdout.strip(), key)

    return {"error": True, "notes": ["codex: no output received"]}


# ── Freeform (judge mode) parsers ──────────────────────────────────────────

def _parse_claude_freeform(raw_stdout: str) -> dict:
    """Parse claude stream-json output as free-form JSON (no schema)."""
    text_parts = []
    for line in raw_stdout.strip().split('\n'):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        # result event with text result
        if obj.get("type") == "result":
            result_text = obj.get("result", "")
            if isinstance(result_text, str) and result_text.strip():
                return _extract_json(result_text, "best")
        # content_block_delta
        if obj.get("type") == "content_block_delta":
            delta = obj.get("delta", {})
            if delta.get("type") == "text_delta":
                text_parts.append(delta.get("text", ""))
    if text_parts:
        return _extract_json(''.join(text_parts), "best")
    return {"error": True, "notes": [f"Failed to parse claude freeform: {raw_stdout[:300]}"]}


def _parse_gemini_freeform(raw_stdout: str) -> dict:
    """Parse gemini stream-json output as free-form JSON."""
    text_parts = []
    for line in raw_stdout.strip().split('\n'):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "message" and obj.get("role") == "assistant":
            content = obj.get("content", "")
            if content:
                text_parts.append(content)
    if text_parts:
        return _extract_json(''.join(text_parts), "best")
    return {"error": True, "notes": [f"Failed to parse gemini freeform: {raw_stdout[:300]}"]}


def _parse_claude_freeform_text(raw_stdout: str) -> dict:
    """Parse claude stream-json output as plain text (no JSON extraction)."""
    text_parts = []
    for line in raw_stdout.strip().split('\n'):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "result":
            result_text = obj.get("result", "")
            if isinstance(result_text, str) and result_text.strip():
                return {"text": result_text.strip()}
        if obj.get("type") == "content_block_delta":
            delta = obj.get("delta", {})
            if delta.get("type") == "text_delta":
                text_parts.append(delta.get("text", ""))
    if text_parts:
        return {"text": ''.join(text_parts).strip()}
    return {"error": True, "text": "", "notes": ["Failed to parse claude freeform text"]}


def _parse_gemini_freeform_text(raw_stdout: str) -> dict:
    """Parse gemini stream-json output as plain text (no JSON extraction)."""
    text_parts = []
    for line in raw_stdout.strip().split('\n'):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("type") == "message" and obj.get("role") == "assistant":
            content = obj.get("content", "")
            if content:
                text_parts.append(content)
    if text_parts:
        return {"text": ''.join(text_parts).strip()}
    return {"error": True, "text": "", "notes": ["Failed to parse gemini freeform text"]}
