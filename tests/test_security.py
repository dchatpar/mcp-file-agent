"""Security-related tests (sandbox, secrets not in repo)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from file_search_agent.mcp.local_file_search import read_pdf_content_impl, search_files_impl


def test_no_live_api_keys_in_tracked_files():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("not a git repository")
    tracked = result.stdout.splitlines()
    for rel_path in tracked:
        if rel_path == ".env":
            pytest.fail(".env must not be tracked by git")
        path = root / rel_path
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert "sk-cp-" not in content, f"possible API key in tracked file: {rel_path}"


def test_read_pdf_outside_sandbox_rejected():
    result = read_pdf_content_impl("../../../etc/passwd")
    assert isinstance(result.model_dump(), dict)
    data = json.loads(result.model_dump_json())
    assert "error" in data


def test_read_pdf_nonexistent_rejected():
    result = read_pdf_content_impl("nonexistent_file.pdf")
    data = json.loads(result.model_dump_json())
    assert "error" in data


def test_search_files_sandbox_root_exists():
    result = search_files_impl()
    assert result.total >= 1
