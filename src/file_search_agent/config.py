"""Application configuration from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEARCH_ROOT = PROJECT_ROOT / "data" / "samples" / "zoology"


def _resolve_search_root(raw: str | None) -> Path:
    if not raw:
        return DEFAULT_SEARCH_ROOT
    path = Path(raw)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


SEARCH_ROOT: Path = _resolve_search_root(
    os.getenv("SEARCH_ROOT") or os.getenv("FILE_SEARCH_ROOT")
)
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL: str = (
    os.getenv("OPENAI_BASE_URL")
    or os.getenv("OPENAI_API_BASE_URL")
    or "https://api.minimax.io/v1"
)
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "MiniMax-M2.7")
MICROSOFT_LEARN_MCP_URL: str = os.getenv(
    "MICROSOFT_LEARN_MCP_URL", "https://learn.microsoft.com/api/mcp"
)
SKILL_PATH: Path = PROJECT_ROOT / "SKILL.md"
MS_ANSWER_MAX_CHARS: int = int(os.getenv("MS_ANSWER_MAX_CHARS", "2000"))
