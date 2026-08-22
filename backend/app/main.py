from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import analytics, assistant, auth, data_sources, documents, environmental_data, imports, mappings, otp, quality, reference, sites, users
from app.core.config import get_settings
from app.core.database import Base, engine

settings = get_settings()


def ensure_database_compatibility() -> None:
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as connection:
        connection.execute(text("ALTER TYPE otp_purpose ADD VALUE IF NOT EXISTS 'email_verification'"))
        connection.execute(text("ALTER TYPE otp_purpose ADD VALUE IF NOT EXISTS 'password_reset'"))
        connection.execute(text("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'csv'"))
        connection.execute(text("ALTER TYPE data_entry_source ADD VALUE IF NOT EXISTS 'csv'"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_database_compatibility()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.8.0",
    description="Sprints 1-8 - Authentification, référentiel, collecte, qualité, analytics ESG et assistant IA",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(otp.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(sites.router, prefix=settings.api_v1_prefix)
app.include_router(data_sources.router, prefix=settings.api_v1_prefix)
app.include_router(imports.router, prefix=settings.api_v1_prefix)
app.include_router(mappings.router, prefix=settings.api_v1_prefix)
app.include_router(documents.router, prefix=settings.api_v1_prefix)
app.include_router(quality.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(assistant.router, prefix=settings.api_v1_prefix)
app.include_router(reference.router, prefix=settings.api_v1_prefix)
app.include_router(environmental_data.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "app": settings.app_name}
