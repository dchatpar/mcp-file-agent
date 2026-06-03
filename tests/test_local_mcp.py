"""Tests for in-process local file search MCP tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client

from file_search_agent.config import SEARCH_ROOT
from file_search_agent.mcp.local_file_search import (
    create_server,
    search_files_impl,
    search_pdf_content_impl,
)


@pytest.fixture(scope="module", autouse=True)
def ensure_samples():
    samples = Path(__file__).resolve().parents[1] / "data" / "samples" / "zoology"
    if not samples.exists() or not any(samples.rglob("*")):
        from scripts.generate_samples import write_samples

        write_samples(samples)


def test_search_files_pdf_extension():
    result = search_files_impl(extension=".pdf")
    assert result.total == 4, f"expected exactly 4 PDFs, got {result.total}"
    assert all(match.extension == ".pdf" for match in result.matches)


def test_search_files_name_filter():
    result = search_files_impl(file_name="*elephant*")
    assert result.total >= 1
    assert any("elephant" in match.name.lower() for match in result.matches)


def test_search_files_extension_filters():
    # Exactly 4 PDFs in the assignment file set
    result = search_files_impl(extension=".pdf")
    assert result.total == 4, f"expected 4 PDFs, got {result.total}"
    assert all(match.extension == ".pdf" for match in result.matches)


def test_search_pdf_content_keyword():
    result = search_pdf_content_impl("migration")
    assert result.total >= 1
    assert any("migration" in match.snippet.lower() for match in result.matches)


@pytest.mark.asyncio
async def test_mcp_tools_return_json_only():
    server = create_server()
    async with Client(server) as client:
        files_result = await client.call_tool("search_files", {"extension": ".pdf"})
        payload = files_result.content[0].text
        data = json.loads(payload)
        assert "matches" in data
        assert "total" in data

        pdf_result = await client.call_tool(
            "search_pdf_content", {"keyword": "migration"}
        )
        pdf_payload = pdf_result.content[0].text
        pdf_data = json.loads(pdf_payload)
        assert pdf_data["keyword"] == "migration"


def test_search_root_is_sandboxed():
    assert SEARCH_ROOT.exists()


def test_search_all_files_returns_eight():
    # Assignment spec: 8 files across 5 extensions
    result = search_files_impl()
    assert result.total == 8, f"expected 8 files total, got {result.total}"


def test_search_files_by_extension_non_pdf():
    for ext, count in ((".docx", 1), (".xlsx", 1), (".txt", 1), (".jpg", 1)):
        result = search_files_impl(extension=ext)
        assert result.total == count, f"expected {count} {ext} file(s), got {result.total}"
