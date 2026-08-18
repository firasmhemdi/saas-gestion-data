from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import Role


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    company_name: str = Field(min_length=1, max_length=255)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ChallengeResendRequest(BaseModel):
    challenge_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    email_verified: bool = False
    email_verified_at: datetime | None = None
    otp_enabled: bool = False
    company_id: int
    created_at: datetime


class OtpChallenge(BaseModel):
    requires_otp: bool = True
    otp_token: str
    delivery_hint: str | None = None
    dev_otp: str | None = None


class OtpVerifyRequest(BaseModel):
    otp_token: str
    code: str = Field(min_length=4, max_length=8)


class EmailVerificationChallenge(BaseModel):
    requires_email_verification: bool = True
    verification_token: str
    delivery_hint: str | None = None
    email: EmailStr
    dev_otp: str | None = None


class EmailVerificationRequest(BaseModel):
    verification_token: str
    code: str = Field(min_length=4, max_length=8)


class OtpSettingsRequest(BaseModel):
    enabled: bool
    password: str


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.lecture_seule


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: Role | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    action: str
    user_id: int | None
    company_id: int | None
    ip_address: str | None
    details: dict[str, Any] | None
    created_at: datetime
