from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.ingestion import DocumentStatus, DocumentType, ImportStatus, SyncStatus


class ImportPreviewRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    source_id: int | None = None
    site_id: int | None = None
    delimiter: str | None = None


class ImportCommitRequest(BaseModel):
    mapping: dict[str, str] = Field(default_factory=dict)
    indicator_id: int | None = None
    site_id: int | None = None


class ImportJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    source_id: int | None
    site_id: int | None
    filename: str
    source_type: str
    status: ImportStatus
    row_count: int
    imported_count: int
    duration_ms: int
    mapping: dict[str, Any] | None = None
    preview_rows: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None
    created_by: int | None
    created_at: datetime


class DataMappingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_id: int | None = None
    target_model: str = Field(default="environmental_data", max_length=64)
    rules: dict[str, str] = Field(default_factory=dict)


class DataMappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    source_id: int | None
    name: str
    target_model: str
    rules: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class SyncScheduleRequest(BaseModel):
    source_id: int
    frequency: str = Field(default="daily", max_length=32)
    window_start: str | None = Field(default=None, max_length=8)
    window_end: str | None = Field(default=None, max_length=8)
    is_active: bool = True


class SyncScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    source_id: int
    frequency: str
    window_start: str | None
    window_end: str | None
    is_active: bool
    last_status: SyncStatus
    last_run_at: datetime | None
    last_message: str | None
    created_at: datetime


class DocumentCreateRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    raw_text: str = Field(min_length=1)
    site_id: int | None = None


class DocumentValidateRequest(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)
    indicator_id: int | None = None
    site_id: int | None = None
    create_environmental_entry: bool = True


class ExtractedDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    document_id: int
    fields: dict[str, Any]
    confidence: int
    created_at: datetime
    validated_at: datetime | None
    validated_by: int | None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    site_id: int | None
    filename: str
    document_type: DocumentType
    status: DocumentStatus
    raw_text: str
    extracted_data: dict[str, Any] | None = None
    created_by: int | None
    created_at: datetime
