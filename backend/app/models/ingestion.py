import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ImportStatus(str, enum.Enum):
    preview = "preview"
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class SyncStatus(str, enum.Enum):
    idle = "idle"
    success = "success"
    failed = "failed"


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    extracted = "extracted"
    validated = "validated"
    rejected = "rejected"


class DocumentType(str, enum.Enum):
    facture_energie = "facture_energie"
    bordereau_dechets = "bordereau_dechets"
    contrat = "contrat"
    attestation = "attestation"
    autre = "autre"


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("data_sources.id", ondelete="SET NULL"), index=True, nullable=True
    )
    site_id: Mapped[int | None] = mapped_column(
        ForeignKey("sites.id", ondelete="SET NULL"), index=True, nullable=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, name="import_status"), default=ImportStatus.preview, index=True, nullable=False
    )
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mapping: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    preview_rows: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "source_id": self.source_id,
            "site_id": self.site_id,
            "filename": self.filename,
            "source_type": self.source_type,
            "status": self.status.value,
            "row_count": self.row_count,
            "imported_count": self.imported_count,
            "duration_ms": self.duration_ms,
            "mapping": self.mapping,
            "preview_rows": self.preview_rows or [],
            "error_message": self.error_message,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


class DataMapping(Base):
    __tablename__ = "data_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_model: Mapped[str] = mapped_column(String(64), default="environmental_data", nullable=False)
    rules: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "source_id": self.source_id,
            "name": self.name,
            "target_model": self.target_model,
            "rules": self.rules,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class SyncSchedule(Base):
    __tablename__ = "sync_schedules"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("data_sources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    frequency: Mapped[str] = mapped_column(String(32), default="daily", nullable=False)
    window_start: Mapped[str | None] = mapped_column(String(8), nullable=True)
    window_end: Mapped[str | None] = mapped_column(String(8), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    last_status: Mapped[SyncStatus] = mapped_column(
        Enum(SyncStatus, name="sync_status"), default=SyncStatus.idle, nullable=False
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "source_id": self.source_id,
            "frequency": self.frequency,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "is_active": self.is_active,
            "last_status": self.last_status.value,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_message": self.last_message,
            "created_at": self.created_at.isoformat(),
        }


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    site_id: Mapped[int | None] = mapped_column(
        ForeignKey("sites.id", ondelete="SET NULL"), index=True, nullable=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type"), default=DocumentType.autre, index=True, nullable=False
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"), default=DocumentStatus.uploaded, index=True, nullable=False
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )

    def to_dict(self, extracted_data: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "site_id": self.site_id,
            "filename": self.filename,
            "document_type": self.document_type.value,
            "status": self.status.value,
            "raw_text": self.raw_text,
            "extracted_data": extracted_data,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
        }


class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    fields: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "document_id": self.document_id,
            "fields": self.fields,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "validated_by": self.validated_by,
        }
