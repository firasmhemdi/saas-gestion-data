import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.data_source import DataSource
from app.models.environmental_data import DataEntrySource, EnvironmentalData
from app.models.indicator import Indicator
from app.models.ingestion import ImportJob, ImportStatus
from app.models.site import Site
from app.models.user import Role, User
from app.schemas.ingestion import ImportCommitRequest, ImportJobOut, ImportPreviewRequest
from app.services import audit as audit_service
from app.services.ingestion import commit_rows, elapsed_ms, parse_tabular_content, suggest_mapping

router = APIRouter(prefix="/imports", tags=["imports"])

_WRITERS = (Role.admin, Role.responsable_environnement, Role.consultant)


def _check_site(db: Session, site_id: int | None, user: User) -> None:
    if site_id is None:
        return
    site = db.get(Site, site_id)
    if not site or site.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site invalide pour ce tenant.")


def _check_source(db: Session, source_id: int | None, user: User) -> DataSource | None:
    if source_id is None:
        return None
    source = db.get(DataSource, source_id)
    if not source or source.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Source invalide pour ce tenant.")
    return source


def _get_owned_job(db: Session, job_id: int, user: User) -> ImportJob:
    job = db.get(ImportJob, job_id)
    if not job or job.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import introuvable.")
    return job


@router.get("", response_model=list[ImportJobOut])
def list_imports(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(ImportJob)
        .where(ImportJob.company_id == current_user.company_id)
        .order_by(ImportJob.created_at.desc())
        .limit(100)
    )
    return [job.to_dict() for job in db.scalars(stmt).all()]


@router.post("/preview", response_model=ImportJobOut, status_code=status.HTTP_201_CREATED)
def preview_import(
    payload: ImportPreviewRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_WRITERS)),
    db: Session = Depends(get_db),
):
    _check_site(db, payload.site_id, current_user)
    source = _check_source(db, payload.source_id, current_user)
    started = time.perf_counter()
    try:
        columns, rows = parse_tabular_content(payload.filename, payload.content, payload.delimiter)
        mapping = suggest_mapping(columns)
        job = ImportJob(
            company_id=current_user.company_id,
            source_id=payload.source_id,
            site_id=payload.site_id,
            filename=payload.filename,
            source_type=source.source_type.value if source else "excel",
            status=ImportStatus.preview,
            row_count=len(rows),
            duration_ms=elapsed_ms(started),
            mapping=mapping,
            preview_rows=rows[:10],
            created_by=current_user.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception as exc:
        job = ImportJob(
            company_id=current_user.company_id,
            source_id=payload.source_id,
            site_id=payload.site_id,
            filename=payload.filename,
            source_type=source.source_type.value if source else "excel",
            status=ImportStatus.failed,
            duration_ms=elapsed_ms(started),
            error_message=str(exc),
            created_by=current_user.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Import illisible : {exc}") from exc

    _audit(db, request, current_user, AuditAction.import_previewed, {"import_id": job.id, "rows": job.row_count})
    return job.to_dict()


@router.post("/{job_id}/commit", response_model=ImportJobOut)
def commit_import(
    job_id: int,
    payload: ImportCommitRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_WRITERS)),
    db: Session = Depends(get_db),
):
    job = _get_owned_job(db, job_id, current_user)
    if job.status == ImportStatus.success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cet import est déjà intégré.")
    _check_site(db, payload.site_id or job.site_id, current_user)
    if payload.indicator_id is not None:
        indicator = db.get(Indicator, payload.indicator_id)
        if not indicator or indicator.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Indicateur invalide pour ce tenant.")

    started = time.perf_counter()
    job.status = ImportStatus.running
    rows = commit_rows(job.preview_rows or [], payload.mapping or job.mapping or {})
    source = DataEntrySource(job.source_type) if job.source_type in DataEntrySource.__members__ else DataEntrySource.excel
    for row in rows:
        db.add(
            EnvironmentalData(
                company_id=current_user.company_id,
                site_id=payload.site_id or job.site_id,
                indicator_id=payload.indicator_id,
                entry_date=row["entry_date"],
                value=row["value"],
                unit=row["unit"],
                source=source,
                entered_by=current_user.id,
            )
        )
    job.status = ImportStatus.success
    job.mapping = payload.mapping or job.mapping
    job.imported_count = len(rows)
    job.duration_ms = elapsed_ms(started)
    db.commit()
    db.refresh(job)

    _audit(db, request, current_user, AuditAction.import_committed, {"import_id": job.id, "created": job.imported_count})
    return job.to_dict()


def _audit(db: Session, request: Request, user: User, action: AuditAction, details: dict) -> None:
    ip = request.client.host if request.client else None
    audit_service.log(
        db,
        action,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        details=details,
    )
