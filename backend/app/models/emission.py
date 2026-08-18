import enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class EmissionScope(str, enum.Enum):
    scope_1 = "1"
    scope_2 = "2"
    scope_3 = "3"


class Emission(Base):
    """Référentiel des facteurs d'émission carbone."""

    __tablename__ = "emissions"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_emission_company_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[EmissionScope] = mapped_column(
        Enum(EmissionScope, name="emission_scope"), nullable=False
    )
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    factor: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "code": self.code,
            "name": self.name,
            "scope": self.scope.value,
            "source": self.source,
            "factor": self.factor,
            "unit": self.unit,
            "year": self.year,
            "created_at": self.created_at.isoformat(),
        }
