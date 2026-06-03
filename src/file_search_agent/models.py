"""Pydantic models for local file search tool responses."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_serializer


class FileMatch(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(serialization_alias="file_name")
    path: str = Field(serialization_alias="folder_path")
    extension: str
    size_bytes: int
    created_at: str
    modified_at: str

    @model_serializer(mode="wrap")
    def _serialize_with_assignment_keys(self, handler):
        data = handler(self)
        data["file_name"] = data["name"]
        data["folder_path"] = data["path"]
        return data


class SearchFilesResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    matches: list[FileMatch] = Field(default_factory=list, serialization_alias="files")
    total: int = Field(default=0, serialization_alias="total_found")
    query: dict[str, str | int | None] = Field(default_factory=dict)

    @model_serializer(mode="wrap")
    def _serialize_with_assignment_keys(self, handler):
        data = handler(self)
        data["files"] = data["matches"]
        data["total_found"] = data["total"]
        return data


class PdfContentMatch(BaseModel):
    file_path: str
    file_name: str
    page: int
    snippet: str


class SearchPdfContentResult(BaseModel):
    keyword: str
    matches: list[PdfContentMatch] = Field(default_factory=list)
    total: int = 0


class ReadPdfContentResult(BaseModel):
    file_path: str
    content: str


class ErrorResult(BaseModel):
    error: str
