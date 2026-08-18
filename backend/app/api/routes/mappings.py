import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.crypto import decrypt
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.data_source import DataSource, SourceType
from app.models.ingestion import DataMapping, ImportJob, ImportStatus, SyncSchedule, SyncStatus
from app.models.user import Role, User
from app.schemas.ingestion import DataMappingOut, DataMappingRequest, SyncScheduleOut, SyncScheduleRequest
from app.services import audit as audit_service

router = APIRouter(tags=["mapping-sync"])

_MANAGERS = (Role.admin, Role.responsable_environnement)


def _get_source(db: Session, source_id: int, user: User) -> DataSource:
    source = db.get(DataSource, source_id)
    if not source or source.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source de données introuvable.")
    return source


def _get_mapping(db: Session, mapping_id: int, user: User) -> DataMapping:
    mapping = db.get(DataMapping, mapping_id)
    if not mapping or mapping.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping introuvable.")
    return mapping


@router.get("/mappings", response_model=list[DataMappingOut])
def list_mappings(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    stmt = select(DataMapping).where(DataMapping.company_id == current_user.company_id).order_by(DataMapping.created_at.desc())
    return [mapping.to_dict() for mapping in db.scalars(stmt).all()]


@router.post("/mappings", response_model=DataMappingOut, status_code=status.HTTP_201_CREATED)
def create_mapping(
    payload: DataMappingRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_MANAGERS)),
    db: Session = Depends(get_db),
):
    if payload.source_id is not None:
        _get_source(db, payload.source_id, current_user)
    mapping = DataMapping(
        company_id=current_user.company_id,
        source_id=payload.source_id,
        name=payload.name.strip(),
        target_model=payload.target_model,
        rules=payload.rules,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    _audit(db, request, current_user, AuditAction.mapping_saved, {"mapping_id": mapping.id})
    return mapping.to_dict()


@router.patch("/mappings/{mapping_id}", response_model=DataMappingOut)
def update_mapping(
    mapping_id: int,
    payload: DataMappingRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_MANAGERS)),
    db: Session = Depends(get_db),
):
    mapping = _get_mapping(db, mapping_id, current_user)
    if payload.source_id is not None:
        _get_source(db, payload.source_id, current_user)
    mapping.name = payload.name.strip()
    mapping.source_id = payload.source_id
    mapping.target_model = payload.target_model
    mapping.rules = payload.rules
    db.commit()
    db.refresh(mapping)
    _audit(db, request, current_user, AuditAction.mapping_saved, {"mapping_id": mapping.id})
    return mapping.to_dict()


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(
    mapping_id: int,
    current_user: User = Depends(require_roles(*_MANAGERS)),
    db: Session = Depends(get_db),
):
    mapping = _get_mapping(db, mapping_id, current_user)
    db.delete(mapping)
    db.commit()


@router.get("/sync-schedules", response_model=list[SyncScheduleOut])
def list_schedules(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    stmt = select(SyncSchedule).where(SyncSchedule.company_id == current_user.company_id).order_by(SyncSchedule.created_at.desc())
    return [schedule.to_dict() for schedule in db.scalars(stmt).all()]


@router.post("/sync-schedules", response_model=SyncScheduleOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: SyncScheduleRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_MANAGERS)),
    db: Session = Depends(get_db),
):
    _get_source(db, payload.source_id, current_user)
    schedule = SyncSchedule(
        company_id=current_user.company_id,
        source_id=payload.source_id,
        frequency=payload.frequency,
        window_start=payload.window_start,
        window_end=payload.window_end,
        is_active=payload.is_active,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    _audit(db, request, current_user, AuditAction.sync_scheduled, {"schedule_id": schedule.id})
    return schedule.to_dict()


@router.post("/data-sources/{source_id}/sync", response_model=dict)
def run_source_sync(
    source_id: int,
    request: Request,
    current_user: User = Depends(require_roles(*_MANAGERS)),
    db: Session = Depends(get_db),
):
    source = _get_source(db, source_id, current_user)
    config = json.loads(decrypt(source.encrypted_config))
    if source.source_type not in (SourceType.api, SourceType.sql, SourceType.erp):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Synchronisation réservée aux sources API, SQL et ERP.")

    sample_records = config.get("sample_records") if isinstance(config, dict) else None
    records = sample_records if isinstance(sample_records, list) else []
    status_value = SyncStatus.success if records or config else SyncStatus.failed
    message = (
        f"{len(records)} enregistrement(s) lus en mode lecture seule."
        if status_value == SyncStatus.success
        else "Configuration insuffisante pour lancer la synchronisation."
    )
    job = ImportJob(
        company_id=current_user.company_id,
        source_id=source.id,
        site_id=source.site_id,
        filename=f"sync-{source.source_type.value}-{source.id}.json",
        source_type=source.source_type.value,
        status=ImportStatus.success if status_value == SyncStatus.success else ImportStatus.failed,
        row_count=len(records),
        imported_count=0,
        preview_rows=records[:10],
        error_message=None if status_value == SyncStatus.success else message,
        created_by=current_user.id,
    )
    db.add(job)
    for schedule in db.scalars(select(SyncSchedule).where(SyncSchedule.source_id == source.id)).all():
        schedule.last_status = status_value
        schedule.last_run_at = datetime.now(timezone.utc)
        schedule.last_message = message
    db.commit()
    db.refresh(job)
    _audit(db, request, current_user, AuditAction.sync_run, {"source_id": source.id, "import_id": job.id, "status": status_value.value})
    return {"ok": status_value == SyncStatus.success, "message": message, "import_id": job.id}


def _audit(db: Session, request: Request, user: User, action: AuditAction, details: dict) -> None:
    audit_service.log(
        db,
        action,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=details,
    )
