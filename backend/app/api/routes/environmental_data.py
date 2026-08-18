from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.environmental_data import DataEntryStatus, EnvironmentalData
from app.models.indicator import Indicator
from app.models.site import Site
from app.models.user import Role, User
from app.schemas.environmental_data import (
    EnvironmentalDataCreateRequest,
    EnvironmentalDataOut,
    EnvironmentalDataUpdateRequest,
)
from app.services import audit as audit_service

router = APIRouter(prefix="/data", tags=["environmental-data"])

_WRITERS = (Role.admin, Role.responsable_environnement, Role.consultant)


def _get_owned(db: Session, data_id: int, user: User) -> EnvironmentalData:
    entry = db.get(EnvironmentalData, data_id)
    if not entry or entry.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donnée introuvable.")
    return entry


def _check_refs(db: Session, site_id: int | None, indicator_id: int | None, user: User) -> None:
    if site_id is not None:
        site = db.get(Site, site_id)
        if not site or site.company_id != user.company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site invalide pour ce tenant.")
    if indicator_id is not None:
        indicator = db.get(Indicator, indicator_id)
        if not indicator or indicator.company_id != user.company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Indicateur invalide pour ce tenant.")


@router.get("", response_model=list[EnvironmentalDataOut])
def list_entries(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(EnvironmentalData)
        .where(EnvironmentalData.company_id == current_user.company_id)
        .order_by(EnvironmentalData.entry_date.desc(), EnvironmentalData.id.desc())
        .limit(200)
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=EnvironmentalDataOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    payload: EnvironmentalDataCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_WRITERS)),
    db: Session = Depends(get_db),
):
    _check_refs(db, payload.site_id, payload.indicator_id, current_user)
    entry = EnvironmentalData(
        company_id=current_user.company_id,
        site_id=payload.site_id,
        indicator_id=payload.indicator_id,
        entry_date=payload.entry_date,
        value=payload.value,
        unit=payload.unit.strip(),
        source=payload.source,
        status=DataEntryStatus.brouillon,
        entered_by=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.data_created,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua,
        details={"data_id": entry.id, "value": entry.value, "unit": entry.unit, "date": entry.entry_date.isoformat()},
    )
    return entry


@router.get("/{data_id}", response_model=EnvironmentalDataOut)
def get_entry(
    data_id: int,
    current_user: User = Depends(require_roles(*_WRITERS, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    return _get_owned(db, data_id, current_user)


@router.patch("/{data_id}", response_model=EnvironmentalDataOut)
def update_entry(
    data_id: int,
    payload: EnvironmentalDataUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_WRITERS)),
    db: Session = Depends(get_db),
):
    entry = _get_owned(db, data_id, current_user)
    if entry.status == DataEntryStatus.valide:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Une donnée validée ne peut plus être modifiée.")

    if payload.site_id is not None:
        _check_refs(db, payload.site_id, None, current_user)
        entry.site_id = payload.site_id
    if payload.indicator_id is not None:
        _check_refs(db, None, payload.indicator_id, current_user)
        entry.indicator_id = payload.indicator_id
    if payload.entry_date is not None:
        entry.entry_date = payload.entry_date
    if payload.value is not None:
        entry.value = payload.value
    if payload.unit is not None:
        entry.unit = payload.unit.strip()
    db.commit()
    db.refresh(entry)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.data_updated,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua, details={"data_id": entry.id},
    )
    return entry


@router.post("/{data_id}/validate", response_model=EnvironmentalDataOut)
def validate_entry(
    data_id: int,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    entry = _get_owned(db, data_id, current_user)
    entry.status = DataEntryStatus.valide
    db.commit()
    db.refresh(entry)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.data_validated,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua, details={"data_id": entry.id},
    )
    return entry


@router.delete("/{data_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    data_id: int,
    current_user: User = Depends(require_roles(*_WRITERS)),
    db: Session = Depends(get_db),
):
    entry = _get_owned(db, data_id, current_user)
    db.delete(entry)
    db.commit()
