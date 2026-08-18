import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditAction(str, enum.Enum):
    register = "register"
    login = "login"
    login_failed = "login_failed"
    logout = "logout"
    refresh = "refresh"
    password_change = "password_change"
    user_role_change = "user_role_change"
    otp_sent = "otp_sent"
    otp_verify_failed = "otp_verify_failed"
    otp_enabled = "otp_enabled"
    otp_disabled = "otp_disabled"
    site_created = "site_created"
    site_updated = "site_updated"
    site_deleted = "site_deleted"
    data_source_created = "data_source_created"
    data_source_updated = "data_source_updated"
    data_source_deleted = "data_source_deleted"
    indicator_created = "indicator_created"
    data_created = "data_created"
    data_updated = "data_updated"
    data_validated = "data_validated"
    import_previewed = "import_previewed"
    import_committed = "import_committed"
    mapping_saved = "mapping_saved"
    sync_scheduled = "sync_scheduled"
    sync_run = "sync_run"
    document_extracted = "document_extracted"
    document_validated = "document_validated"


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action"), index=True, nullable=False
    )
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), index=True, nullable=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )
