import enum
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DataEntryStatus(str, enum.Enum):
    brouillon = "brouillon"
    valide = "valide"


class DataEntrySource(str, enum.Enum):
    manuel = "manuel"
    csv = "csv"
    excel = "excel"
    api = "api"
    sql = "sql"
    erp = "erp"
    iot = "iot"


class EnvironmentalData(Base):
    """Saisie manuelle de données environnementales dans le référentiel."""

    __tablename__ = "environmental_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    site_id: Mapped[int | None] = mapped_column(
        ForeignKey("sites.id", ondelete="SET NULL"), index=True, nullable=True
    )
    indicator_id: Mapped[int | None] = mapped_column(
        ForeignKey("indicators.id", ondelete="SET NULL"), index=True, nullable=True
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[DataEntrySource] = mapped_column(
        Enum(DataEntrySource, name="data_entry_source"), default=DataEntrySource.manuel, nullable=False
    )
    status: Mapped[DataEntryStatus] = mapped_column(
        Enum(DataEntryStatus, name="data_entry_status"), default=DataEntryStatus.brouillon, nullable=False
    )
    entered_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "site_id": self.site_id,
            "indicator_id": self.indicator_id,
            "entry_date": self.entry_date.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "source": self.source.value,
            "status": self.status.value,
            "entered_by": self.entered_by,
            "created_at": self.created_at.isoformat(),
        }
