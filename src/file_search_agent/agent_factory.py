"""Build LangChain agent with local in-memory MCP and Microsoft Learn MCP."""

from __future__ import annotations

from pathlib import Path

from fastmcp import Client
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI

from file_search_agent.config import (
    MICROSOFT_LEARN_MCP_URL,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    SKILL_PATH,
)
from file_search_agent.mcp.local_file_search import create_server


def _is_minimax_provider(base_url: str = OPENAI_BASE_URL) -> bool:
    """Return True when the configured base URL targets MiniMax."""
    return "minimax" in base_url.lower()


def load_skill_prompt(skill_path: Path = SKILL_PATH) -> str:
    if not skill_path.exists():
        return "You are a file search and Microsoft documentation assistant."
    return skill_path.read_text(encoding="utf-8")


async def load_local_mcp_tools():
    server = create_server()
    client = Client(server)
    await client.__aenter__()
    tools = await load_mcp_tools(client.session)
    return tools, client


async def load_learn_mcp_tools():
    client = MultiServerMCPClient(
        {
            "microsoft_learn": {
                "url": MICROSOFT_LEARN_MCP_URL,
                "transport": "streamable_http",
            }
        }
    )
    return await client.get_tools()


def _create_chat_model() -> ChatOpenAI:
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is required. Set it in .env (see .env.example)."
        )
    kwargs: dict = {
        "model": OPENAI_MODEL,
        "api_key": OPENAI_API_KEY,
        "base_url": OPENAI_BASE_URL,
        "temperature": 0,
        "timeout": 120,
        "max_retries": 2,
    }
    if _is_minimax_provider(OPENAI_BASE_URL):
        kwargs["extra_body"] = {
            "reasoning_split": True,
            "thinking": {"type": "disabled"},
        }
    return ChatOpenAI(**kwargs)


async def create_file_search_agent():
    local_tools, local_client = await load_local_mcp_tools()
    learn_tools = await load_learn_mcp_tools()
    tools = [*local_tools, *learn_tools]
    system_prompt = load_skill_prompt()
    agent = create_agent(
        model=_create_chat_model(),
        tools=tools,
        system_prompt=system_prompt,
    )
    agent._local_mcp_client = local_client  # type: ignore[attr-defined]
    return agent


async def close_agent(agent) -> None:
    client = getattr(agent, "_local_mcp_client", None)
    if client is not None:
        await client.__aexit__(None, None, None)
