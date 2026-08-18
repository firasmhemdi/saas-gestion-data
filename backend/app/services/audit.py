from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog


def log(
    db: Session,
    action: AuditAction,
    *,
    user_id: int | None = None,
    company_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    entry = AuditLog(
        action=action,
        user_id=user_id,
        company_id=company_id,
        ip_address=ip_address[:64] if ip_address else None,
        user_agent=user_agent[:255] if user_agent else None,
        details=details,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_for_company(db: Session, company_id: int, limit: int = 50, offset: int = 0) -> list[AuditLog]:
    stmt = (
        select(AuditLog)
        .where(AuditLog.company_id == company_id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
