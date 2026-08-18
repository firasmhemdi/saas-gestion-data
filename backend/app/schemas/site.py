from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SiteCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=255)


class SiteUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    location: str | None = Field(default=None, max_length=255)


class SiteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    name: str
    code: str | None
    location: str | None
    created_at: datetime
