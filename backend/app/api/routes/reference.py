from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.emission import Emission
from app.models.indicator import Indicator
from app.models.user import Role, User
from app.schemas.reference import (
    EmissionCreateRequest,
    EmissionOut,
    IndicatorCreateRequest,
    IndicatorOut,
)
from app.services import audit as audit_service

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/indicators", response_model=list[IndicatorOut])
def list_indicators(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Indicator)
        .where(Indicator.company_id == current_user.company_id)
        .order_by(Indicator.category, Indicator.code)
    )
    return list(db.scalars(stmt).all())


@router.post("/indicators", response_model=IndicatorOut, status_code=status.HTTP_201_CREATED)
def create_indicator(
    payload: IndicatorCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    code = payload.code.strip()
    duplicate = db.scalar(
        select(Indicator).where(
            Indicator.company_id == current_user.company_id,
            func.lower(Indicator.code) == code.lower(),
        )
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce code d'indicateur existe déjà.")

    indicator = Indicator(
        company_id=current_user.company_id,
        code=code,
        name=payload.name.strip(),
        unit=payload.unit.strip(),
        category=payload.category,
        description=payload.description,
    )
    db.add(indicator)
    db.commit()
    db.refresh(indicator)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.indicator_created,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua,
        details={"indicator_id": indicator.id, "code": indicator.code},
    )
    return indicator


@router.get("/emissions", response_model=list[EmissionOut])
def list_emissions(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Emission)
        .where(Emission.company_id == current_user.company_id)
        .order_by(Emission.scope, Emission.code)
    )
    return list(db.scalars(stmt).all())


@router.post("/emissions", response_model=EmissionOut, status_code=status.HTTP_201_CREATED)
def create_emission(
    payload: EmissionCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    code = payload.code.strip()
    duplicate = db.scalar(
        select(Emission).where(
            Emission.company_id == current_user.company_id,
            func.lower(Emission.code) == code.lower(),
        )
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce code de facteur d'émission existe déjà.")

    emission = Emission(
        company_id=current_user.company_id,
        code=code,
        name=payload.name.strip(),
        scope=payload.scope,
        source=payload.source,
        factor=payload.factor,
        unit=payload.unit.strip(),
        year=payload.year,
    )
    db.add(emission)
    db.commit()
    db.refresh(emission)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.indicator_created,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua,
        details={"emission_id": emission.id, "code": emission.code},
    )
    return emission
