from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.site import Site
from app.models.user import Role, User
from app.schemas.site import SiteCreateRequest, SiteOut, SiteUpdateRequest
from app.services import audit as audit_service

router = APIRouter(prefix="/sites", tags=["sites"])


def _get_owned_site(db: Session, site_id: int, user: User) -> Site:
    site = db.get(Site, site_id)
    if not site or site.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site introuvable.")
    return site


@router.get("", response_model=list[SiteOut])
def list_sites(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Site)
        .where(Site.company_id == current_user.company_id)
        .order_by(Site.name)
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
def create_site(
    payload: SiteCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    name = payload.name.strip()
    if db.scalar(select(Site).where(Site.company_id == current_user.company_id, Site.name == name)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un site avec ce nom existe déjà.")

    site = Site(
        company_id=current_user.company_id,
        name=name,
        code=payload.code,
        location=payload.location,
    )
    db.add(site)
    db.commit()
    db.refresh(site)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.site_created,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua, details={"site_id": site.id, "name": site.name},
    )
    return site


@router.get("/{site_id}", response_model=SiteOut)
def get_site(
    site_id: int,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant)),
    db: Session = Depends(get_db),
):
    return _get_owned_site(db, site_id, current_user)


@router.patch("/{site_id}", response_model=SiteOut)
def update_site(
    site_id: int,
    payload: SiteUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    site = _get_owned_site(db, site_id, current_user)
    if payload.name is not None:
        name = payload.name.strip()
        duplicate = db.scalar(
            select(Site).where(
                Site.company_id == current_user.company_id,
                Site.name == name,
                Site.id != site_id,
            )
        )
        if duplicate:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un site avec ce nom existe déjà.")
        site.name = name
    if payload.code is not None:
        site.code = payload.code
    if payload.location is not None:
        site.location = payload.location
    db.commit()
    db.refresh(site)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.site_updated,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua, details={"site_id": site.id},
    )
    return site


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_site(
    site_id: int,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    site = _get_owned_site(db, site_id, current_user)
    db.delete(site)
    db.commit()

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.site_deleted,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua, details={"site_id": site_id},
    )
