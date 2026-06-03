#!/usr/bin/env python3
"""Assignment spot-check: 3 sample queries (non-interactive)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from file_search_agent.agent_factory import close_agent, create_file_search_agent
from file_search_agent.config import MS_ANSWER_MAX_CHARS, OPENAI_API_KEY
from file_search_agent.output_guard import guard_agent_output, message_used_local_tools
from file_search_agent.routing import OUT_OF_SCOPE_ERROR

CREATE_TIMEOUT_S = 60
QUERY_TIMEOUT_S = 120

SPOT_CHECKS = (
    (
        "What PDF files are available in our system?",
        "pdf_json",
    ),
    (
        "What is Azure Blob Storage?",
        "azure_learn",
    ),
    (
        "What is the capital of France?",
        "out_of_scope",
    ),
)


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


def _pdf_entries(data: dict) -> list[dict]:
    items = data.get("matches") or data.get("files") or []
    pdfs: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        ext = str(item.get("extension", "")).lower()
        name = str(item.get("name") or item.get("file_name") or "").lower()
        if ext == ".pdf" or name.endswith(".pdf"):
            pdfs.append(item)
    return pdfs


def _check_pdf_json(out: str, used_local: bool) -> list[str]:
    failures: list[str] = []
    if not used_local:
        failures.append("expected local file tools")
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        failures.append("output must be JSON only")
        return failures
    pdfs = _pdf_entries(data)
    if len(pdfs) != 4:
        total = data.get("total") or data.get("total_found")
        failures.append(
            f"expected 4 PDF entries, got pdf_count={len(pdfs)} total={total}"
        )
    return failures


def _check_azure(out: str, used_local: bool) -> list[str]:
    failures: list[str] = []
    if used_local:
        failures.append("must not use local file tools")
    if len(out) > MS_ANSWER_MAX_CHARS:
        failures.append(f"answer exceeds {MS_ANSWER_MAX_CHARS} chars ({len(out)})")
    if not out.strip():
        failures.append("empty answer")
    return failures


def _check_out_of_scope(out: str) -> list[str]:
    failures: list[str] = []
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        if OUT_OF_SCOPE_ERROR.lower() not in out.lower():
            failures.append("expected out-of-scope JSON error")
        return failures
    if OUT_OF_SCOPE_ERROR not in json.dumps(data):
        failures.append("missing assignment out-of-scope error text")
    return failures


async def run_spot_checks() -> list[str]:
    failures: list[str] = []
    _log("Creating agent...")
    agent = await asyncio.wait_for(create_file_search_agent(), timeout=CREATE_TIMEOUT_S)
    _log("Agent ready.\n")
    try:
        for idx, (query, kind) in enumerate(SPOT_CHECKS, start=1):
            _log(f"[{idx}/3] {query}")
            out, used_local = await _ask(agent, query)
            _log(f"      local_tools={used_local} len={len(out)}")
            check_failures: list[str] = []
            if kind == "pdf_json":
                check_failures = _check_pdf_json(out, used_local)
            elif kind == "azure_learn":
                check_failures = _check_azure(out, used_local)
            else:
                check_failures = _check_out_of_scope(out)
            failures.extend(check_failures)
            if check_failures:
                _log(f"      FAIL: {check_failures[-1]}")
            else:
                _log("      OK")
            _log("")
    finally:
        await close_agent(agent)
    return failures


def main() -> int:
    if not OPENAI_API_KEY:
        _log("SKIP: OPENAI_API_KEY not set")
        return 0
    _log("Running assignment spot-check (3 queries)...")
    try:
        failures = asyncio.run(run_spot_checks())
    except asyncio.TimeoutError:
        _log("FAILED: timed out")
        return 1
    if failures:
        _log("FAILED:")
        for f in failures:
            _log(f"  - {f}")
        return 1
    _log("PASSED: all 3 assignment spot-checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
