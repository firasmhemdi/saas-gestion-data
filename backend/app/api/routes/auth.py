from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
    ChallengeResendRequest,
    EmailVerificationRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_context(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return ip, ua


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    ip, ua = _client_context(request)
    try:
        result = auth_service.register(db, payload, ip_address=ip, user_agent=ua)
    except auth_service.OtpDeliveryUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if "access_token" in result:
        return TokenResponse(**result)
    return result


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip, ua = _client_context(request)
    try:
        result = auth_service.authenticate(db, payload.email, payload.password, ip_address=ip, user_agent=ua)
    except auth_service.OtpDeliveryUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return result


@router.post("/email/verify", response_model=TokenResponse)
def verify_email(payload: EmailVerificationRequest, request: Request, db: Session = Depends(get_db)):
    ip, ua = _client_context(request)
    from datetime import datetime, timezone

    from app.models.audit_log import AuditAction
    from app.models.otp import OtpPurpose
    from app.services import audit as audit_service
    from app.services import otp as otp_service

    try:
        user = otp_service.verify_code(
            db,
            payload.verification_token,
            payload.code,
            purpose=OtpPurpose.email_verification,
            token_type="email_verification",
        )
    except otp_service.OtpExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except otp_service.OtpInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user.email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    tokens = auth_service._token_pair(db, user)
    audit_service.log(
        db,
        AuditAction.login,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=ip,
        user_agent=ua,
        details={"email_verification": "verified"},
    )
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer",
        expires_in=tokens["expires_in"],
        user=user,
    )


@router.post("/email/resend")
def resend_email_verification(payload: ChallengeResendRequest, db: Session = Depends(get_db)):
    from app.models.otp import OtpPurpose
    from app.services import otp as otp_service

    try:
        return otp_service.resend_challenge(
            db,
            payload.challenge_token,
            purpose=OtpPurpose.email_verification,
            token_type="email_verification",
        )
    except otp_service.OtpDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except otp_service.OtpInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/password/forgot")
def forgot_password(payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)):
    ip, ua = _client_context(request)
    try:
        return auth_service.request_password_reset(db, payload.email, ip_address=ip, user_agent=ua)
    except auth_service.OtpDeliveryUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/password/reset", response_model=MessageResponse)
def reset_password(payload: PasswordResetConfirmRequest, request: Request, db: Session = Depends(get_db)):
    ip, ua = _client_context(request)
    from app.services import otp as otp_service

    try:
        auth_service.reset_password(
            db,
            payload.reset_token,
            payload.code,
            payload.new_password,
            ip_address=ip,
            user_agent=ua,
        )
    except otp_service.OtpExpiredError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except otp_service.OtpInvalidError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return MessageResponse(message="Mot de passe réinitialisé. Vous pouvez vous connecter.")


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    ip, ua = _client_context(request)
    try:
        result = auth_service.refresh(db, payload.refresh_token, ip_address=ip, user_agent=ua)
    except auth_service.InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return TokenResponse(**result)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    payload: RefreshRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ip, ua = _client_context(request)
    auth_service.logout(db, current_user, payload.refresh_token, ip_address=ip, user_agent=ua)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
