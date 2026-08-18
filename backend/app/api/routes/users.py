from fastapi import APIRouter, Depends, HTTPException, Request, status
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.security import hash_password
from app.models.audit_log import AuditAction
from app.models.user import Role, User
from app.schemas.auth import AuditLogOut, UserCreateRequest, UserOut, UserUpdateRequest
from app.services import audit as audit_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[UserOut])
def list_users(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    stmt = (
        select(User)
        .where(User.company_id == current_user.company_id)
        .order_by(User.id)
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    email = payload.email.lower()
    if db.scalar(select(User).where(User.company_id == current_user.company_id, User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Un utilisateur avec cet email existe déjà.")

    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=True,
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc),
        company_id=current_user.company_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db, AuditAction.user_role_change,
        user_id=current_user.id, company_id=current_user.company_id,
        ip_address=ip, user_agent=ua,
        details={"target_user_id": user.id, "role": payload.role.value},
    )
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user or user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user or user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable.")

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
        audit_service.log(
            db, AuditAction.password_change,
            user_id=current_user.id, company_id=current_user.company_id,
            ip_address=ip, user_agent=ua, details={"target_user_id": user.id},
        )
    if payload.role is not None:
        if user.id == current_user.id and payload.role != Role.admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Vous ne pouvez pas retirer votre propre rôle admin.",
            )
        old_role = user.role
        user.role = payload.role
        audit_service.log(
            db, AuditAction.user_role_change,
            user_id=current_user.id, company_id=current_user.company_id,
            ip_address=ip, user_agent=ua,
            details={"target_user_id": user.id, "old_role": old_role.value, "new_role": payload.role.value},
        )

    db.commit()
    db.refresh(user)
    return user


@router.get("/audit/logs", response_model=list[AuditLogOut])
def audit_logs(
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    return audit_service.list_for_company(db, current_user.company_id)
