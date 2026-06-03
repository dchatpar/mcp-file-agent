"""Routing constants and helpers for agent response contracts."""

from __future__ import annotations

import json

OUT_OF_SCOPE_ERROR = (
    "Query out of scope. Only file search and Microsoft/Azure queries are supported."
)

OUT_OF_SCOPE_JSON = json.dumps({"error": OUT_OF_SCOPE_ERROR}, separators=(",", ":"))

LOCAL_FILE_TOOL_NAMES = frozenset(
    {
        "search_files",
        "search_pdf_content",
        "list_all_files",
        "read_pdf_content",
    }
)

MICROSOFT_LEARN_TOOL_PREFIXES = ("microsoft_",)
