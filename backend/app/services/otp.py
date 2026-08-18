import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_challenge_token, decode_token
from app.models.otp import OtpCode, OtpPurpose
from app.models.user import User
from app.services.email import EmailDeliveryError, send_email_verification_code, send_otp_code


class OtpError(Exception):
    pass


class OtpExpiredError(OtpError):
    pass


class OtpInvalidError(OtpError):
    pass


class OtpDeliveryError(OtpError):
    pass


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def generate_code() -> str:
    settings = get_settings()
    return f"{secrets.randbelow(10 ** settings.otp_length):0{settings.otp_length}d}"


def _issue_challenge(db: Session, user: User, *, purpose: OtpPurpose, token_type: str) -> dict:
    settings = get_settings()
    code = generate_code()
    db.add(
        OtpCode(
            user_id=user.id,
            purpose=purpose,
            code_hash=_hash(code),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.otp_expire_minutes),
        )
    )
    db.flush()
    otp_token = create_challenge_token(
        str(user.id),
        token_type,
        settings.otp_expire_minutes,
        {"role": user.role.value, "company_id": user.company_id},
    )

    if not (settings.demo_mode and settings.otp_expose_demo_code):
        try:
            if purpose == OtpPurpose.email_verification:
                send_email_verification_code(user, code, settings.otp_expire_minutes)
            else:
                send_otp_code(user, code, settings.otp_expire_minutes)
        except EmailDeliveryError as exc:
            db.rollback()
            raise OtpDeliveryError(str(exc)) from exc

    db.commit()
    if purpose == OtpPurpose.email_verification:
        result: dict = {
            "requires_email_verification": True,
            "verification_token": otp_token,
            "delivery_hint": "Un code de vérification a été envoyé à votre adresse e-mail.",
            "email": user.email,
        }
    else:
        result = {
            "requires_otp": True,
            "otp_token": otp_token,
            "delivery_hint": "Un code de sécurité a été envoyé à votre adresse e-mail.",
        }
    if settings.demo_mode and settings.otp_expose_demo_code:
        result["dev_otp"] = code
    return result


def issue_challenge(db: Session, user: User) -> dict:
    return _issue_challenge(db, user, purpose=OtpPurpose.login, token_type="otp")


def issue_email_verification(db: Session, user: User) -> dict:
    return _issue_challenge(db, user, purpose=OtpPurpose.email_verification, token_type="email_verification")


def resend_challenge(db: Session, challenge_token: str, *, purpose: OtpPurpose, token_type: str) -> dict:
    try:
        payload = decode_token(challenge_token)
    except Exception as exc:
        raise OtpInvalidError("Jeton de vérification invalide.") from exc

    if payload.get("type") != token_type:
        raise OtpInvalidError("Jeton de vérification invalide.")

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise OtpInvalidError("Utilisateur inconnu ou inactif.")

    return _issue_challenge(db, user, purpose=purpose, token_type=token_type)


def verify_code(db: Session, otp_token: str, code: str, *, purpose: OtpPurpose = OtpPurpose.login, token_type: str = "otp") -> User:
    settings = get_settings()
    try:
        payload = decode_token(otp_token)
    except Exception as exc:
        raise OtpInvalidError("Jeton de vérification OTP invalide.") from exc

    if payload.get("type") != token_type:
        raise OtpInvalidError("Jeton de vérification OTP invalide.")

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise OtpInvalidError("Utilisateur inconnu ou inactif.")

    otp = db.scalar(
        select(OtpCode)
        .where(
            OtpCode.user_id == user.id,
            OtpCode.purpose == purpose,
            OtpCode.consumed_at.is_(None),
        )
        .order_by(OtpCode.created_at.desc())
    )
    if not otp or otp.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise OtpExpiredError("Code OTP expiré. Veuillez vous reconnecter.")

    if otp.attempts >= settings.otp_max_attempts:
        otp.consumed_at = datetime.now(timezone.utc)
        db.commit()
        raise OtpExpiredError("Trop de tentatives. Veuillez vous reconnecter.")

    if not secrets.compare_digest(otp.code_hash, _hash(code)):
        otp.attempts += 1
        if otp.attempts >= settings.otp_max_attempts:
            otp.consumed_at = datetime.now(timezone.utc)
        db.commit()
        raise OtpInvalidError("Code OTP incorrect.")

    otp.consumed_at = datetime.now(timezone.utc)
    db.commit()
    return user
