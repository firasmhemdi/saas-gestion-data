import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.crypto import decrypt, encrypt
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.data_source import DataSource
from app.models.site import Site
from app.models.user import Role, User
from app.schemas.data_source import DataSourceCreateRequest, DataSourceOut, DataSourceUpdateRequest
from app.services import audit as audit_service

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


def _get_owned(db: Session, source_id: int, user: User) -> DataSource:
    source = db.get(DataSource, source_id)
    if not source or source.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source de données introuvable.")
    return source


def _check_site(db: Session, site_id: int | None, user: User) -> None:
    if site_id is None:
        return
    site = db.get(Site, site_id)
    if not site or site.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site invalide pour ce tenant.")


@router.get("", response_model=list[DataSourceOut])
def list_data_sources(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(DataSource)
        .where(DataSource.company_id == current_user.company_id)
        .order_by(DataSource.name)
    )
    return [s.to_dict() for s in db.scalars(stmt).all()]


@router.post("", response_model=DataSourceOut, status_code=status.HTTP_201_CREATED)
def create_data_source(
    payload: DataSourceCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    _check_site(db, payload.site_id, current_user)
    source = DataSource(
        company_id=current_user.company_id,
        site_id=payload.site_id,
        name=payload.name.strip(),
        source_type=payload.source_type,
        encrypted_config=encrypt(json.dumps(payload.config, ensure_ascii=False)),
        is_active=payload.is_active,
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.data_source_created,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua,
        details={"source_id": source.id, "name": source.name, "source_type": source.source_type.value},
    )
    return source.to_dict()


@router.get("/{source_id}", response_model=DataSourceOut)
def get_data_source(
    source_id: int,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant)),
    db: Session = Depends(get_db),
):
    return _get_owned(db, source_id, current_user).to_dict()


@router.patch("/{source_id}", response_model=DataSourceOut)
def update_data_source(
    source_id: int,
    payload: DataSourceUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    source = _get_owned(db, source_id, current_user)
    if payload.site_id is not None:
        _check_site(db, payload.site_id, current_user)
        source.site_id = payload.site_id
    if payload.name is not None:
        source.name = payload.name.strip()
    if payload.source_type is not None:
        source.source_type = payload.source_type
    if payload.config is not None:
        source.encrypted_config = encrypt(json.dumps(payload.config, ensure_ascii=False))
    if payload.is_active is not None:
        source.is_active = payload.is_active
    db.commit()
    db.refresh(source)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.data_source_updated,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua, details={"source_id": source.id},
    )
    return source.to_dict()


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data_source(
    source_id: int,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    source = _get_owned(db, source_id, current_user)
    db.delete(source)
    db.commit()

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.data_source_deleted,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua, details={"source_id": source_id},
    )


# Endpoint technique : vérifier que la config chiffrée est bien décryptable (AES-256 au repos)
@router.post("/{source_id}/test-connection", response_model=dict)
def test_connection(
    source_id: int,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    source = _get_owned(db, source_id, current_user)
    config = json.loads(decrypt(source.encrypted_config))
    return {"ok": True, "source_type": source.source_type.value, "config_keys": list(config.keys())}
