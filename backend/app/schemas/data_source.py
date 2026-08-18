from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.data_source import SourceType


class DataSourceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    site_id: int | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class DataSourceUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    site_id: int | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class DataSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    site_id: int | None
    name: str
    source_type: SourceType
    config: dict[str, Any] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
