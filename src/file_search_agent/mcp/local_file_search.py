"""In-process FastMCP server for sandboxed local file search."""

from __future__ import annotations

import fnmatch
import os
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP
from pypdf import PdfReader

from file_search_agent.config import SEARCH_ROOT
from file_search_agent.models import (
    ErrorResult,
    FileMatch,
    PdfContentMatch,
    ReadPdfContentResult,
    SearchFilesResult,
    SearchPdfContentResult,
)

mcp = FastMCP("Local File Search")

PDF_READ_MAX_PAGES = 3
PDF_READ_MAX_CHARS = 50_000


def _resolve_in_sandbox(path: str | None) -> Path | None:
    if path is None or path.strip() == "":
        return None
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = SEARCH_ROOT / candidate
    resolved = candidate.resolve()
    root = SEARCH_ROOT.resolve()
    if resolved == root or root in resolved.parents:
        return resolved
    return None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _file_matches_filters(
    file_path: Path,
    *,
    file_name: str | None,
    folder_path: str | None,
    extension: str | None,
    created_after: str | None,
    created_before: str | None,
    modified_after: str | None,
    modified_before: str | None,
    min_size_bytes: int | None,
    max_size_bytes: int | None,
) -> bool:
    stat = file_path.stat()
    rel_path = str(file_path.relative_to(SEARCH_ROOT.resolve()))

    if file_name and not fnmatch.fnmatch(file_path.name.lower(), file_name.lower()):
        return False

    if folder_path:
        folder = folder_path.strip("/\\")
        if folder and not rel_path.replace("\\", "/").startswith(folder.replace("\\", "/")):
            return False

    if extension:
        ext = extension if extension.startswith(".") else f".{extension}"
        if file_path.suffix.lower() != ext.lower():
            return False

    created = datetime.fromtimestamp(stat.st_ctime)
    modified = datetime.fromtimestamp(stat.st_mtime)

    created_after_dt = _parse_date(created_after)
    created_before_dt = _parse_date(created_before)
    modified_after_dt = _parse_date(modified_after)
    modified_before_dt = _parse_date(modified_before)

    if created_after_dt and created < created_after_dt:
        return False
    if created_before_dt and created > created_before_dt:
        return False
    if modified_after_dt and modified < modified_after_dt:
        return False
    if modified_before_dt and modified > modified_before_dt:
        return False
    if min_size_bytes is not None and stat.st_size < min_size_bytes:
        return False
    if max_size_bytes is not None and stat.st_size > max_size_bytes:
        return False

    return True


def search_files_impl(
    *,
    file_name: str | None = None,
    folder_path: str | None = None,
    extension: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    modified_after: str | None = None,
    modified_before: str | None = None,
    min_size_bytes: int | None = None,
    max_size_bytes: int | None = None,
) -> SearchFilesResult:
    root = SEARCH_ROOT.resolve()
    if not root.exists():
        return SearchFilesResult(
            matches=[],
            total=0,
            query={"error": f"search root missing: {root}"},
        )

    matches: list[FileMatch] = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            file_path = Path(dirpath) / name
            if not _file_matches_filters(
                file_path,
                file_name=file_name,
                folder_path=folder_path,
                extension=extension,
                created_after=created_after,
                created_before=created_before,
                modified_after=modified_after,
                modified_before=modified_before,
                min_size_bytes=min_size_bytes,
                max_size_bytes=max_size_bytes,
            ):
                continue
            stat = file_path.stat()
            matches.append(
                FileMatch(
                    name=file_path.name,
                    path=str(file_path.relative_to(root)),
                    extension=file_path.suffix.lower(),
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                )
            )

    matches.sort(key=lambda item: item.path)
    query = {
        "file_name": file_name,
        "folder_path": folder_path,
        "extension": extension,
        "created_after": created_after,
        "created_before": created_before,
        "modified_after": modified_after,
        "modified_before": modified_before,
        "min_size_bytes": min_size_bytes,
        "max_size_bytes": max_size_bytes,
    }
    return SearchFilesResult(matches=matches, total=len(matches), query=query)


def search_pdf_content_impl(keyword: str) -> SearchPdfContentResult | ErrorResult:
    if not keyword or not keyword.strip():
        return ErrorResult(error="keyword is required")

    root = SEARCH_ROOT.resolve()
    keyword_lower = keyword.lower()
    matches: list[PdfContentMatch] = []

    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            if not name.lower().endswith(".pdf"):
                continue
            file_path = Path(dirpath) / name
            try:
                reader = PdfReader(str(file_path))
            except Exception:
                continue
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                if keyword_lower not in text.lower():
                    continue
                idx = text.lower().index(keyword_lower)
                start = max(0, idx - 40)
                end = min(len(text), idx + len(keyword) + 40)
                snippet = text[start:end].replace("\n", " ").strip()
                matches.append(
                    PdfContentMatch(
                        file_path=str(file_path.relative_to(root)),
                        file_name=file_path.name,
                        page=page_num,
                        snippet=snippet,
                    )
                )

    return SearchPdfContentResult(keyword=keyword, matches=matches, total=len(matches))


def list_all_files_impl() -> SearchFilesResult:
    return search_files_impl()


def _extract_pdf_text(path: Path, *, max_pages: int = PDF_READ_MAX_PAGES) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    total_chars = 0
    for page in reader.pages[:max_pages]:
        text = page.extract_text() or ""
        if total_chars + len(text) > PDF_READ_MAX_CHARS:
            text = text[: PDF_READ_MAX_CHARS - total_chars]
        parts.append(text)
        total_chars += len(text)
        if total_chars >= PDF_READ_MAX_CHARS:
            break
    return " ".join(parts).strip()


def read_pdf_content_impl(file_path: str) -> ReadPdfContentResult | ErrorResult:
    if not file_path or not file_path.strip():
        return ErrorResult(error="file_path is required")

    resolved = _resolve_in_sandbox(file_path)
    if resolved is None:
        return ErrorResult(error="file_path outside sandbox or not found")

    if not resolved.is_file():
        return ErrorResult(error=f"not a file: {file_path}")

    if resolved.suffix.lower() != ".pdf":
        return ErrorResult(error=f"not a valid PDF: {file_path}")

    try:
        content = _extract_pdf_text(resolved)
    except Exception as exc:
        return ErrorResult(error=f"failed to read PDF: {exc}")

    rel = str(resolved.relative_to(SEARCH_ROOT.resolve()))
    return ReadPdfContentResult(file_path=rel, content=content)


@mcp.tool
def search_files(
    file_name: str | None = None,
    folder_path: str | None = None,
    extension: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    modified_after: str | None = None,
    modified_before: str | None = None,
    min_size_bytes: int | None = None,
    max_size_bytes: int | None = None,
) -> str:
    """Search files under SEARCH_ROOT using metadata filters."""
    resolved_folder = None
    if folder_path:
        folder = _resolve_in_sandbox(folder_path)
        if folder is None:
            return ErrorResult(error="folder_path outside sandbox").model_dump_json()
        resolved_folder = str(folder.relative_to(SEARCH_ROOT.resolve()))

    result = search_files_impl(
        file_name=file_name,
        folder_path=resolved_folder or folder_path,
        extension=extension,
        created_after=created_after,
        created_before=created_before,
        modified_after=modified_after,
        modified_before=modified_before,
        min_size_bytes=min_size_bytes,
        max_size_bytes=max_size_bytes,
    )
    return result.model_dump_json()


@mcp.tool
def search_pdf_content(keyword: str) -> str:
    """Full-text keyword search across PDF files under SEARCH_ROOT."""
    result = search_pdf_content_impl(keyword)
    return result.model_dump_json()


@mcp.tool
def list_all_files() -> str:
    """List all files under SEARCH_ROOT. Returns JSON only."""
    return list_all_files_impl().model_dump_json()


@mcp.tool
def read_pdf_content(file_path: str) -> str:
    """Read text content from a PDF file within SEARCH_ROOT. Returns JSON only."""
    result = read_pdf_content_impl(file_path)
    return result.model_dump_json()


def create_server() -> FastMCP:
    return mcp
