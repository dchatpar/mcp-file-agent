"""Output guards for agent responses."""

from __future__ import annotations

import json
import re
from typing import Any

from file_search_agent.config import MS_ANSWER_MAX_CHARS
from file_search_agent.routing import LOCAL_FILE_TOOL_NAMES

# MiniMax / reasoning models may emit thinking blocks in content
_THINKING_BLOCK_RE = re.compile(
    r"<think(?:ing)?>[\s\S]*?</think(?:ing)?>",
    re.IGNORECASE,
)
_REDACTED_THINKING_RE = re.compile(
    r"<think>[\s\S]*?</think>",
    re.IGNORECASE,
)


def strip_model_artifacts(text: str) -> str:
    """Remove model reasoning artifacts before JSON extraction or display."""
    cleaned = _THINKING_BLOCK_RE.sub("", text)
    cleaned = _REDACTED_THINKING_RE.sub("", cleaned)
    return cleaned.strip()


def is_valid_json(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    try:
        json.loads(text)
        return True
    except json.JSONDecodeError:
        return False


def extract_json_payload(text: str) -> str | None:
    stripped = strip_model_artifacts(text)
    if is_valid_json(stripped):
        return stripped

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped)
    if fence_match:
        candidate = fence_match.group(1).strip()
        if is_valid_json(candidate):
            return candidate

    for start_char, end_char in (("{", "}"), ("[", "]")):
        start = stripped.find(start_char)
        end = stripped.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            candidate = stripped[start : end + 1]
            if is_valid_json(candidate):
                return candidate
    return None


def enforce_json_only(text: str) -> str:
    """Return canonical JSON string or a JSON error payload."""
    payload = extract_json_payload(text)
    if payload is None:
        return json.dumps(
            {
                "error": "response_must_be_json_only",
                "original_preview": strip_model_artifacts(text)[:200],
            }
        )
    parsed: Any = json.loads(payload)
    return json.dumps(parsed, separators=(",", ":"))


def truncate_ms_answer(text: str, max_chars: int | None = None) -> str:
    limit = max_chars if max_chars is not None else MS_ANSWER_MAX_CHARS
    cleaned = strip_model_artifacts(text)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def guard_agent_output(text: str, *, used_local_tools: bool) -> str:
    if used_local_tools:
        return enforce_json_only(text)
    return truncate_ms_answer(text)


def message_used_local_tools(messages: list[Any]) -> bool:
    for message in messages:
        tool_calls = getattr(message, "tool_calls", None) or []
        for call in tool_calls:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name in LOCAL_FILE_TOOL_NAMES:
                return True
        name = getattr(message, "name", None)
        if name in LOCAL_FILE_TOOL_NAMES:
            return True
    return False
