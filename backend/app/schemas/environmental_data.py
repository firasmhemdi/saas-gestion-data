from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.environmental_data import DataEntrySource, DataEntryStatus


class EnvironmentalDataCreateRequest(BaseModel):
    site_id: int | None = None
    indicator_id: int | None = None
    entry_date: date
    value: float
    unit: str = Field(min_length=1, max_length=64)
    source: DataEntrySource = DataEntrySource.manuel


class EnvironmentalDataUpdateRequest(BaseModel):
    site_id: int | None = None
    indicator_id: int | None = None
    entry_date: date | None = None
    value: float | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=64)


class EnvironmentalDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int
    site_id: int | None
    indicator_id: int | None
    entry_date: date
    value: float
    unit: str
    source: DataEntrySource
    status: DataEntryStatus
    entered_by: int | None
    created_at: datetime
