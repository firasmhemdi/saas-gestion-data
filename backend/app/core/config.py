from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SaaS Gestion Data API"
    api_v1_prefix: str = "/api/v1"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    database_url: str = "postgresql+psycopg://saas:saas@localhost:5433/saas_gestion_data"
    db_echo: bool = False

    jwt_secret_key: str = "CHANGE_ME_dev_secret_key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    bcrypt_rounds: int = 12

    otp_enabled: bool = True
    otp_expire_minutes: int = 5
    otp_length: int = 6
    otp_max_attempts: int = 5
    email_verification_required: bool = True
    demo_mode: bool = True
    otp_expose_demo_code: bool = False
    email_provider: str = "smtp"
    resend_api_key: str | None = None
    resend_from_email: str | None = None
    mailjet_api_key: str | None = None
    mailjet_secret_key: str | None = None
    mailjet_from_email: str | None = None
    mailjet_from_name: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "no-reply@saas-gestion-data.local"
    smtp_from_name: str = "SaaS Gestion Data"
    smtp_use_tls: bool = True

    data_encryption_key: str = "CHANGE_ME_dev_encryption_key_at_least_32_chars"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
