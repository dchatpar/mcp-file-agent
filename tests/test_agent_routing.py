"""Unit tests for routing constants and output guards."""

from __future__ import annotations

import json

from file_search_agent.output_guard import (
    enforce_json_only,
    extract_json_payload,
    guard_agent_output,
    message_used_local_tools,
    strip_model_artifacts,
    truncate_ms_answer,
)
from file_search_agent.routing import OUT_OF_SCOPE_ERROR, OUT_OF_SCOPE_JSON


def test_out_of_scope_json_shape():
    data = json.loads(OUT_OF_SCOPE_JSON)
    assert data["error"] == OUT_OF_SCOPE_ERROR


def test_enforce_json_only_on_tool_payload():
    payload = '{"matches":[],"total":4,"query":{}}'
    assert enforce_json_only(payload) == payload


def test_enforce_json_only_strips_thinking_then_extracts():
    wrapped = (
        "<think>internal</think>\n"
        '{"total": 8, "matches": []}'
    )
    result = enforce_json_only(wrapped)
    assert json.loads(result)["total"] == 8


def test_strip_model_artifacts():
    text = "<think>secret</think>Hello"
    assert strip_model_artifacts(text) == "Hello"


def test_truncate_ms_answer_at_boundary():
    long_text = "a" * 2500
    out = truncate_ms_answer(long_text, max_chars=2000)
    assert len(out) <= 2000


def test_guard_agent_output_local_json():
    raw = '{"matches":[{"name":"x.pdf"}],"total":1}'
    assert guard_agent_output(raw, used_local_tools=True) == raw


def test_guard_agent_output_learn_truncation():
    raw = "x" * 3000
    out = guard_agent_output(raw, used_local_tools=False)
    assert len(out) <= 2000


def test_message_used_local_tools_detects_list_all():
    class FakeCall:
        def __init__(self, name: str):
            self.name = name

    class FakeMessage:
        def __init__(self, tool_calls):
            self.tool_calls = tool_calls
            self.name = None

    messages = [FakeMessage([FakeCall("list_all_files")])]
    assert message_used_local_tools(messages) is True


def test_extract_json_from_fence():
    text = 'Here is data:\n```json\n{"total": 4}\n```'
    payload = extract_json_payload(text)
    assert payload is not None
    assert json.loads(payload)["total"] == 4
