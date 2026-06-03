#!/usr/bin/env python3
"""Non-interactive E2E verification for the file search agent."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from file_search_agent.agent_factory import (
    _is_minimax_provider,
    close_agent,
    create_file_search_agent,
)
from file_search_agent.config import (
    MS_ANSWER_MAX_CHARS,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)
from file_search_agent.output_guard import guard_agent_output, message_used_local_tools
from file_search_agent.routing import OUT_OF_SCOPE_ERROR

CREATE_TIMEOUT_S = 60
QUERY_TIMEOUT_S = 120


def _log(msg: str) -> None:
    print(msg, flush=True)


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
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            else:
                text = getattr(block, "text", None)
                if text:
                    parts.append(str(text))
        return "".join(parts)
    return str(content)


async def _ask(agent, query: str) -> tuple[str, bool]:
    result = await asyncio.wait_for(
        agent.ainvoke({"messages": [{"role": "user", "content": query}]}),
        timeout=QUERY_TIMEOUT_S,
    )
    messages = result.get("messages", [])
    if not messages:
        return "", False
    raw = _extract_text(getattr(messages[-1], "content", ""))
    used_local = message_used_local_tools(messages)
    guarded = guard_agent_output(
        raw, used_local_tools=used_local, messages=messages
    )
    return guarded, used_local


def _assert_json(text: str, label: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{label}: output is not valid JSON: {text[:300]}") from exc


async def run_checks() -> list[str]:
    failures: list[str] = []

    provider = "MiniMax" if _is_minimax_provider(OPENAI_BASE_URL) else "OpenAI-compatible"
    _log(
        f"Creating agent (local MCP + Learn MCP + {provider}, "
        f"model={OPENAI_MODEL})..."
    )
    agent = await asyncio.wait_for(create_file_search_agent(), timeout=CREATE_TIMEOUT_S)
    _log("Agent ready.")

    try:
        _log("[1/5] PDF files query...")
        out, used_local = await _ask(agent, "What PDF files are available in our system?")
        _log(f"      done (local_tools={used_local}, len={len(out)})")
        if not used_local:
            failures.append("PDF query: expected local tools, none used")
        try:
            data = _assert_json(out, "PDF query")
            pdfs = data.get("matches") or data.get("files") or []
            if isinstance(data.get("total"), int) and data["total"] < 1 and not pdfs:
                failures.append("PDF query: no PDF entries in JSON")
            blob = json.dumps(data).lower()
            if "pdf" not in blob and not pdfs:
                failures.append("PDF query: JSON missing PDF entries")
        except AssertionError as e:
            failures.append(str(e))

        _log("[2/5] List all files...")
        out2, used_local2 = await _ask(agent, "List all files in the system")
        _log(f"      done (local_tools={used_local2}, len={len(out2)})")
        if not used_local2:
            failures.append("List all: expected local tools")
        try:
            data2 = _assert_json(out2, "List all")
            total = data2.get("total")
            if total != 8:
                count = len(data2.get("matches") or data2.get("files") or [])
                if count != 8:
                    failures.append(f"List all: expected 8 files, got total={total} count={count}")
        except AssertionError as e:
            failures.append(str(e))

        _log("[3/5] Elephant search...")
        out3, used_local3 = await _ask(agent, "Find files about elephants")
        _log(f"      done (local_tools={used_local3}, len={len(out3)})")
        if not used_local3:
            failures.append("Elephant: expected local tools")
        try:
            data3 = _assert_json(out3, "Elephant")
            if "elephant" not in json.dumps(data3).lower():
                failures.append("Elephant: no elephant match in JSON")
        except AssertionError as e:
            failures.append(str(e))

        _log("[4/5] Azure Blob Storage (Learn MCP)...")
        out4, used_local4 = await _ask(agent, "What is Azure Blob Storage?")
        _log(f"      done (local_tools={used_local4}, len={len(out4)})")
        if used_local4:
            failures.append("Azure: should not use local file tools")
        if len(out4) > MS_ANSWER_MAX_CHARS:
            failures.append(f"Azure: answer exceeds {MS_ANSWER_MAX_CHARS} chars ({len(out4)})")
        if not out4.strip():
            failures.append("Azure: empty answer")

        _log("[5/5] Out-of-scope query...")
        out5, _ = await _ask(agent, "What is the capital of France?")
        _log(f"      done (len={len(out5)})")
        try:
            data5 = _assert_json(out5, "Out of scope")
            if OUT_OF_SCOPE_ERROR not in json.dumps(data5):
                failures.append("Out of scope: expected assignment error JSON")
        except AssertionError:
            if OUT_OF_SCOPE_ERROR.lower() not in out5.lower():
                failures.append("Out of scope: not JSON and missing error text")

    finally:
        await close_agent(agent)

    return failures


def main() -> int:
    if not OPENAI_API_KEY:
        _log("SKIP: OPENAI_API_KEY not set - cannot run E2E agent checks")
        return 0

    _log("Running E2E verification (5 checks, ~1-2 min)...")
    try:
        failures = asyncio.run(run_checks())
    except asyncio.TimeoutError:
        _log("FAILED: timed out waiting for agent or query (increase QUERY_TIMEOUT_S)")
        return 1

    if failures:
        _log("FAILED:")
        for f in failures:
            _log(f"  - {f}")
        return 1
    _log("PASSED: all 5 E2E checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
