"""Async CLI REPL for the Local File Search MCP agent."""

from __future__ import annotations

import asyncio
import sys

from file_search_agent.agent_factory import close_agent, create_file_search_agent
from file_search_agent.output_guard import guard_agent_output, message_used_local_tools


def _extract_text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif "text" in block:
                    parts.append(str(block["text"]))
            else:
                text = getattr(block, "text", None)
                if text:
                    parts.append(str(text))
        return "".join(parts)
    return str(content)


async def run_repl() -> None:
    agent = await create_file_search_agent()
    print("Local File Search MCP Agent")
    print("Type a question, or 'exit' / Ctrl+C to quit.\n")
    try:
        while True:
            try:
                user_input = await asyncio.to_thread(input, "you> ")
            except EOFError:
                break
            query = user_input.strip()
            if not query:
                continue
            if query.lower() in {"exit", "quit", "q"}:
                break

            result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
            messages = result.get("messages", [])
            if not messages:
                print("agent> (no response)\n")
                continue

            last = messages[-1]
            raw = _extract_text(getattr(last, "content", ""))
            used_local = message_used_local_tools(messages)
            guarded = guard_agent_output(
                raw, used_local_tools=used_local, messages=messages
            )
            print(f"agent> {guarded}\n")
    finally:
        await close_agent(agent)


def main() -> None:
    try:
        asyncio.run(run_repl())
    except KeyboardInterrupt:
        print("\nBye.")
        sys.exit(0)


if __name__ == "__main__":
    main()
