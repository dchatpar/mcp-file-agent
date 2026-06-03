"""Tests for agent factory LLM provider configuration."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from file_search_agent import agent_factory


@pytest.mark.parametrize(
    ("base_url", "expected"),
    [
        ("https://api.minimax.io/v1", True),
        ("https://api.MINIMAX.io/v1", True),
        ("https://api.openai.com/v1", False),
        ("https://api.openai.com/v1/", False),
    ],
)
def test_is_minimax_provider(base_url: str, expected: bool) -> None:
    assert agent_factory._is_minimax_provider(base_url) is expected


def test_create_chat_model_openai_omits_extra_body() -> None:
    with (
        patch.object(agent_factory, "OPENAI_API_KEY", "sk-test-key"),
        patch.object(agent_factory, "OPENAI_BASE_URL", "https://api.openai.com/v1"),
        patch.object(agent_factory, "OPENAI_MODEL", "gpt-4o"),
        patch.object(agent_factory, "ChatOpenAI") as mock_chat,
    ):
        agent_factory._create_chat_model()

    mock_chat.assert_called_once()
    call_kwargs = mock_chat.call_args.kwargs
    assert "extra_body" not in call_kwargs


def test_create_chat_model_minimax_includes_extra_body() -> None:
    with (
        patch.object(agent_factory, "OPENAI_API_KEY", "sk-test-key"),
        patch.object(agent_factory, "OPENAI_BASE_URL", "https://api.minimax.io/v1"),
        patch.object(agent_factory, "OPENAI_MODEL", "MiniMax-M2.7"),
        patch.object(agent_factory, "ChatOpenAI") as mock_chat,
    ):
        agent_factory._create_chat_model()

    mock_chat.assert_called_once()
    call_kwargs = mock_chat.call_args.kwargs
    assert call_kwargs["extra_body"] == {
        "reasoning_split": True,
        "thinking": {"type": "disabled"},
    }
