"""Tests for output_guard."""

from __future__ import annotations

import json

import pytest

from file_search_agent.output_guard import (
    enforce_json_only,
    extract_json_payload,
    guard_agent_output,
    truncate_ms_answer,
)


def test_enforce_json_only_accepts_raw_json():
    payload = '{"matches":[],"total":0}'
    assert enforce_json_only(payload) == payload


def test_enforce_json_only_extracts_from_fence():
    text = 'Here is data:\n```json\n{"total": 1}\n```'
    assert json.loads(enforce_json_only(text)) == {"total": 1}


def test_enforce_json_only_error_on_prose():
    result = json.loads(enforce_json_only("not json at all"))
    assert result["error"] == "response_must_be_json_only"


def test_truncate_ms_answer():
    text = "a" * 2500
    truncated = truncate_ms_answer(text, max_chars=2000)
    assert len(truncated) == 2000
    assert truncated.endswith("...")


def test_guard_agent_output_local_json():
    raw = '{"matches":[{"name":"a.pdf"}],"total":1}'
    assert guard_agent_output(raw, used_local_tools=True) == raw


def test_guard_agent_output_learn_truncation():
    raw = "x" * 3000
    out = guard_agent_output(raw, used_local_tools=False)
    assert len(out) <= 2000


def test_extract_json_payload_array():
    assert extract_json_payload('[{"a":1}]') == '[{"a":1}]'
