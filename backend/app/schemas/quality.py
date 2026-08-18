from datetime import date
from typing import Literal

from pydantic import BaseModel


QualitySeverity = Literal["info", "warning", "critical"]
QualityIssueType = Literal["missing_reference", "negative_value", "unit_mismatch", "duplicate", "outlier"]


class QualityAlertOut(BaseModel):
    id: str
    data_id: int
    issue_type: QualityIssueType
    severity: QualitySeverity
    title: str
    message: str
    recommendation: str
    entry_date: date
    site_id: int | None
    indicator_id: int | None


class QualitySummaryOut(BaseModel):
    total_entries: int
    draft_entries: int
    valid_entries: int
    alerts: list[QualityAlertOut]
    quality_score: int


class NormalizedEntryOut(BaseModel):
    data_id: int
    original_value: float
    original_unit: str
    normalized_value: float
    normalized_unit: str
    changed: bool
