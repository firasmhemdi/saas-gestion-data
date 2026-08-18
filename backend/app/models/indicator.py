import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IndicatorCategory(str, enum.Enum):
    energie = "energie"
    eau = "eau"
    dechets = "dechets"
    emissions = "emissions"
    matieres = "matieres"


class Indicator(Base):
    __tablename__ = "indicators"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_indicator_company_code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[IndicatorCategory] = mapped_column(
        Enum(IndicatorCategory, name="indicator_category"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "code": self.code,
            "name": self.name,
            "unit": self.unit,
            "category": self.category.value,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }
