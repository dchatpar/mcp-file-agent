"""Tests for Microsoft Learn MCP connectivity."""

from __future__ import annotations

import pytest
from langchain_mcp_adapters.client import MultiServerMCPClient

from file_search_agent.config import MICROSOFT_LEARN_MCP_URL


@pytest.mark.asyncio
async def test_learn_mcp_connects_and_lists_tools():
    client = MultiServerMCPClient(
        {
            "microsoft_learn": {
                "url": MICROSOFT_LEARN_MCP_URL,
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()
    names = {tool.name for tool in tools}
    assert "microsoft_docs_search" in names
    assert len(tools) >= 1
