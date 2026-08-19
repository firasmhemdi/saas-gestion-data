import hashlib
import re
import unicodedata
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.audit_log import AuditAction
from app.models.otp import OtpPurpose
from app.models.company import Company
from app.models.user import RefreshToken, Role, User
from app.schemas.auth import RegisterRequest
from app.services import audit as audit_service


class AuthError(Exception):
    pass


class InvalidCredentialsError(AuthError):
    pass


class InvalidRefreshTokenError(AuthError):
    pass


class OtpDeliveryUnavailableError(AuthError):
    pass


def _slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name.strip().lower())
    ascii_text = "".join(c for c in normalized if not unicodedata.combining(c))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug or "societe"


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _store_refresh_token(db: Session, user: User, token: str) -> None:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    db.add(
        RefreshToken(
            token_hash=_hash_token(token),
            user_id=user.id,
            expires_at=expires_at,
        )
    )


def _token_pair(db: Session, user: User) -> dict:
    settings = get_settings()
    claims = {"role": user.role.value, "company_id": user.company_id}
    access_token = create_access_token(str(user.id), claims)
    refresh_token = create_refresh_token(str(user.id), claims)
    _store_refresh_token(db, user, refresh_token)
    db.commit()
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


def register(
    db: Session,
    data: RegisterRequest,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    email = data.email.lower()
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise InvalidCredentialsError("Un compte existe déjà avec cet email.")

    slug = _slugify(data.company_name)
    base_slug = slug
    suffix = 2
    while db.scalar(select(Company).where(Company.slug == slug)):
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    company = Company(name=data.company_name.strip(), slug=slug)
    db.add(company)
    db.flush()

    user = User(
        email=email,
        full_name=data.full_name.strip(),
        password_hash=hash_password(data.password),
        role=Role.admin,
        is_active=True,
        email_verified=not get_settings().email_verification_required,
        email_verified_at=datetime.now(timezone.utc) if not get_settings().email_verification_required else None,
        company_id=company.id,
    )
    db.add(user)
    db.flush()

    if get_settings().email_verification_required:
        from app.services import otp as otp_service

        try:
            challenge = otp_service.issue_email_verification(db, user)
        except otp_service.OtpDeliveryError as exc:
            raise OtpDeliveryUnavailableError(str(exc)) from exc
        audit_service.log(
            db,
            AuditAction.register,
            user_id=user.id,
            company_id=company.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": email, "company": company.name, "email_verification": "sent"},
        )
        return challenge

    tokens = _token_pair(db, user)
    audit_service.log(
        db,
        AuditAction.register,
        user_id=user.id,
        company_id=company.id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"email": email, "company": company.name},
    )
    db.refresh(user)
    return {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"],
            "token_type": "bearer", "expires_in": tokens["expires_in"], "user": user}


def authenticate(
    db: Session,
    email: str,
    password: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        audit_service.log(
            db,
            AuditAction.login_failed,
            company_id=user.company_id if user else None,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": email.lower()},
        )
        raise InvalidCredentialsError("Email ou mot de passe incorrect.")

    from app.services import otp as otp_service

    if get_settings().email_verification_required and not user.email_verified:
        try:
            challenge = otp_service.issue_email_verification(db, user)
        except otp_service.OtpDeliveryError as exc:
            raise OtpDeliveryUnavailableError(str(exc)) from exc
        audit_service.log(
            db,
            AuditAction.otp_sent,
            user_id=user.id,
            company_id=user.company_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": email.lower(), "purpose": "email_verification"},
        )
        return challenge

    if get_settings().otp_enabled and user.otp_enabled:
        try:
            challenge = otp_service.issue_challenge(db, user)
        except otp_service.OtpDeliveryError as exc:
            raise OtpDeliveryUnavailableError(str(exc)) from exc
        audit_service.log(
            db,
            AuditAction.otp_sent,
            user_id=user.id,
            company_id=user.company_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"email": email.lower()},
        )
        return challenge

    tokens = _token_pair(db, user)
    audit_service.log(
        db,
        AuditAction.login,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.refresh(user)
    return {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"],
            "token_type": "bearer", "expires_in": tokens["expires_in"], "user": user}


def request_password_reset(
    db: Session,
    email: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    normalized_email = email.lower()
    user = db.scalar(select(User).where(User.email == normalized_email))
    if not user or not user.is_active:
        return {
            "requires_password_reset": True,
            "reset_token": None,
            "delivery_hint": "Si un compte existe avec cet e-mail, un code de réinitialisation sera envoyé.",
            "email": normalized_email,
        }

    from app.services import otp as otp_service

    try:
        challenge = otp_service.issue_password_reset(db, user)
    except otp_service.OtpDeliveryError as exc:
        raise OtpDeliveryUnavailableError(str(exc)) from exc

    audit_service.log(
        db,
        AuditAction.otp_sent,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"email": normalized_email, "purpose": "password_reset"},
    )
    return challenge


def reset_password(
    db: Session,
    reset_token: str,
    code: str,
    new_password: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    from app.services import otp as otp_service

    user = otp_service.verify_code(
        db,
        reset_token,
        code,
        purpose=OtpPurpose.password_reset,
        token_type="password_reset",
    )
    user.password_hash = hash_password(new_password)

    active_tokens = db.scalars(
        select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
    ).all()
    now = datetime.now(timezone.utc)
    for token in active_tokens:
        token.revoked_at = now

    audit_service.log(
        db,
        AuditAction.password_change,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details={"method": "password_reset"},
    )
    db.commit()


def refresh(
    db: Session,
    refresh_token: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        raise InvalidRefreshTokenError("Jeton de rafraîchissement invalide.") from exc

    if payload.get("type") != "refresh":
        raise InvalidRefreshTokenError("Jeton de rafraîchissement invalide.")

    token_hash = _hash_token(refresh_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if not stored or stored.revoked_at is not None:
        raise InvalidRefreshTokenError("Jeton de rafraîchissement révoqué ou inexistant.")
    if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise InvalidRefreshTokenError("Jeton de rafraîchissement expiré.")

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise InvalidRefreshTokenError("Utilisateur inconnu ou inactif.")

    stored.revoked_at = datetime.now(timezone.utc)
    tokens = _token_pair(db, user)
    audit_service.log(
        db,
        AuditAction.refresh,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return {"access_token": tokens["access_token"], "refresh_token": tokens["refresh_token"],
            "token_type": "bearer", "expires_in": tokens["expires_in"], "user": user}


def logout(db: Session, user: User, refresh_token: str | None = None, *, ip_address: str | None = None, user_agent: str | None = None) -> None:
    if refresh_token:
        stored = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == _hash_token(refresh_token),
                RefreshToken.user_id == user.id,
            )
        )
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            db.commit()
    audit_service.log(
        db,
        AuditAction.logout,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
