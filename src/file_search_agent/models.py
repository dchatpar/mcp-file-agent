"""Pydantic models for local file search tool responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FileMatch(BaseModel):
    name: str
    path: str
    extension: str
    size_bytes: int
    created_at: str
    modified_at: str


class SearchFilesResult(BaseModel):
    matches: list[FileMatch] = Field(default_factory=list)
    total: int = 0
    query: dict[str, str | int | None] = Field(default_factory=dict)


class PdfContentMatch(BaseModel):
    file_path: str
    file_name: str
    page: int
    snippet: str


class SearchPdfContentResult(BaseModel):
    keyword: str
    matches: list[PdfContentMatch] = Field(default_factory=list)
    total: int = 0


class ErrorResult(BaseModel):
    error: str
