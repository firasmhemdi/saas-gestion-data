from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.user import User
from app.schemas.auth import ChallengeResendRequest, OtpSettingsRequest, OtpVerifyRequest, TokenResponse, UserOut
from app.services import audit as audit_service
from app.services import auth as auth_service
from app.services import otp as otp_service

router = APIRouter(prefix="/auth/otp", tags=["otp"])


@router.post("/verify", response_model=TokenResponse)
def verify_otp(
    payload: OtpVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    try:
        user = otp_service.verify_code(db, payload.otp_token, payload.code)
    except otp_service.OtpExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except otp_service.OtpInvalidError as exc:
        audit_service.log(
            db,
            AuditAction.otp_verify_failed,
            ip_address=ip,
            user_agent=ua,
            details={"reason": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    tokens = auth_service._token_pair(db, user)
    audit_service.log(
        db,
        AuditAction.login,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=ip,
        user_agent=ua,
    )
    db.refresh(user)
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=tokens["expires_in"],
        user=user,
    )


@router.post("/resend")
def resend_otp(payload: ChallengeResendRequest, db: Session = Depends(get_db)):
    from app.models.otp import OtpPurpose

    try:
        return otp_service.resend_challenge(
            db,
            payload.challenge_token,
            purpose=OtpPurpose.login,
            token_type="otp",
        )
    except otp_service.OtpDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except otp_service.OtpInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/settings", response_model=UserOut)
def update_otp_settings(
    payload: OtpSettingsRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not auth_service.verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe incorrect.")

    current_user.otp_enabled = payload.enabled
    db.commit()
    db.refresh(current_user)

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    audit_service.log(
        db,
        AuditAction.otp_enabled if payload.enabled else AuditAction.otp_disabled,
        user_id=current_user.id,
        company_id=current_user.company_id,
        ip_address=ip,
        user_agent=ua,
    )
    return current_user
