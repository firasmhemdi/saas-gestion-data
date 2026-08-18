from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.indicator import IndicatorCategory


class IndicatorCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    unit: str = Field(min_length=1, max_length=64)
    category: IndicatorCategory
    description: str | None = None


class IndicatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    code: str
    name: str
    unit: str
    category: IndicatorCategory
    description: str | None
    created_at: datetime


class EmissionCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    scope: str
    source: str | None = None
    factor: float
    unit: str = Field(min_length=1, max_length=64)
    year: int = Field(ge=1990, le=2100)


class EmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    code: str
    name: str
    scope: str
    source: str | None
    factor: float
    unit: str
    year: int
    created_at: datetime
