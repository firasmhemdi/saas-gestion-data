import os
import tempfile

_TEST_DB = os.path.join(tempfile.gettempdir(), "saas_gestion_data_test.db")
if os.path.exists(_TEST_DB):
    os.remove(_TEST_DB)

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_not_used_in_prod"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["DATA_ENCRYPTION_KEY"] = "test_encryption_key_0123456789_abcdef"
os.environ["EMAIL_VERIFICATION_REQUIRED"] = "false"
os.environ["DEMO_MODE"] = "true"
os.environ["OTP_EXPOSE_DEMO_CODE"] = "true"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
    from app.core.database import engine

    engine.dispose()
    if os.path.exists(_TEST_DB):
        try:
            os.remove(_TEST_DB)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def _clean_db() -> Generator[None, None, None]:
    yield
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM extracted_data"))
        db.execute(text("DELETE FROM documents"))
        db.execute(text("DELETE FROM sync_schedules"))
        db.execute(text("DELETE FROM data_mappings"))
        db.execute(text("DELETE FROM import_jobs"))
        db.execute(text("DELETE FROM data_sources"))
        db.execute(text("DELETE FROM ai_queries"))
        db.execute(text("DELETE FROM environmental_data"))
        db.execute(text("DELETE FROM emissions"))
        db.execute(text("DELETE FROM indicators"))
        db.execute(text("DELETE FROM sites"))
        db.execute(text("DELETE FROM otp_codes"))
        db.execute(text("DELETE FROM refresh_tokens"))
        db.execute(text("DELETE FROM audit_logs"))
        db.execute(text("DELETE FROM users"))
        db.execute(text("DELETE FROM companies"))
        db.commit()
    finally:
        db.close()
