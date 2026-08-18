from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.environmental_data import DataEntryStatus, EnvironmentalData
from app.models.indicator import Indicator
from app.models.user import Role, User
from app.schemas.environmental_data import EnvironmentalDataOut
from app.schemas.quality import NormalizedEntryOut, QualityAlertOut, QualitySummaryOut
from app.services import audit as audit_service

router = APIRouter(prefix="/quality", tags=["quality"])

_UNIT_CONVERSIONS: dict[tuple[str, str], float] = {
    ("mwh", "kwh"): 1000,
    ("kwh", "mwh"): 0.001,
    ("wh", "kwh"): 0.001,
    ("l", "m3"): 0.001,
    ("litre", "m3"): 0.001,
    ("litres", "m3"): 0.001,
    ("kg", "tonnes"): 0.001,
    ("tonne", "tonnes"): 1,
    ("t", "tonnes"): 1,
}


def _unit_key(unit: str) -> str:
    return unit.strip().lower().replace("³", "3")


def _convert(value: float, from_unit: str, to_unit: str) -> float | None:
    source = _unit_key(from_unit)
    target = _unit_key(to_unit)
    if source == target:
        return value
    factor = _UNIT_CONVERSIONS.get((source, target))
    if factor is None:
        return None
    return round(value * factor, 4)


def _load_context(db: Session, company_id: int) -> tuple[list[EnvironmentalData], dict[int, Indicator]]:
    entries = list(
        db.scalars(
            select(EnvironmentalData)
            .where(EnvironmentalData.company_id == company_id)
            .order_by(EnvironmentalData.entry_date.desc(), EnvironmentalData.id.desc())
        ).all()
    )
    indicator_ids = {entry.indicator_id for entry in entries if entry.indicator_id is not None}
    indicators = {}
    if indicator_ids:
        indicators = {
            indicator.id: indicator
            for indicator in db.scalars(select(Indicator).where(Indicator.id.in_(indicator_ids))).all()
        }
    return entries, indicators


def _build_alerts(entries: list[EnvironmentalData], indicators: dict[int, Indicator]) -> list[QualityAlertOut]:
    alerts: list[QualityAlertOut] = []
    seen: dict[tuple[int | None, int | None, object, float, str], int] = {}
    values_by_indicator: dict[int, list[float]] = defaultdict(list)
    for entry in entries:
        if entry.indicator_id is not None:
            values_by_indicator[entry.indicator_id].append(entry.value)

    for entry in entries:
        indicator = indicators.get(entry.indicator_id or -1)
        if entry.site_id is None or entry.indicator_id is None:
            alerts.append(
                QualityAlertOut(
                    id=f"{entry.id}-missing-reference",
                    data_id=entry.id,
                    issue_type="missing_reference",
                    severity="warning",
                    title="Référence incomplète",
                    message="La donnée n'est pas rattachée à un site ou à un indicateur.",
                    recommendation="Compléter le site et l'indicateur avant validation.",
                    entry_date=entry.entry_date,
                    site_id=entry.site_id,
                    indicator_id=entry.indicator_id,
                )
            )
        if entry.value < 0:
            alerts.append(
                QualityAlertOut(
                    id=f"{entry.id}-negative",
                    data_id=entry.id,
                    issue_type="negative_value",
                    severity="critical",
                    title="Valeur négative",
                    message="Une consommation ou une émission ne devrait pas être négative.",
                    recommendation="Corriger la valeur ou justifier l'avoir associé.",
                    entry_date=entry.entry_date,
                    site_id=entry.site_id,
                    indicator_id=entry.indicator_id,
                )
            )
        if indicator and _convert(entry.value, entry.unit, indicator.unit) is None:
            alerts.append(
                QualityAlertOut(
                    id=f"{entry.id}-unit",
                    data_id=entry.id,
                    issue_type="unit_mismatch",
                    severity="warning",
                    title="Unité non normalisée",
                    message=f"L'unité {entry.unit} ne correspond pas à l'unité attendue {indicator.unit}.",
                    recommendation="Normaliser l'unité ou ajuster le référentiel.",
                    entry_date=entry.entry_date,
                    site_id=entry.site_id,
                    indicator_id=entry.indicator_id,
                )
            )

        duplicate_key = (entry.site_id, entry.indicator_id, entry.entry_date, entry.value, _unit_key(entry.unit))
        previous = seen.get(duplicate_key)
        if previous is not None:
            alerts.append(
                QualityAlertOut(
                    id=f"{entry.id}-duplicate",
                    data_id=entry.id,
                    issue_type="duplicate",
                    severity="info",
                    title="Doublon probable",
                    message=f"Une donnée identique existe déjà dans la ligne #{previous}.",
                    recommendation="Comparer les deux lignes et supprimer le doublon si nécessaire.",
                    entry_date=entry.entry_date,
                    site_id=entry.site_id,
                    indicator_id=entry.indicator_id,
                )
            )
        else:
            seen[duplicate_key] = entry.id

        if entry.indicator_id is not None:
            values = values_by_indicator[entry.indicator_id]
            if len(values) >= 3:
                average = sum(values) / len(values)
                if average and entry.value > average * 3:
                    alerts.append(
                        QualityAlertOut(
                            id=f"{entry.id}-outlier",
                            data_id=entry.id,
                            issue_type="outlier",
                            severity="critical",
                            title="Valeur aberrante",
                            message="La valeur dépasse fortement la moyenne observée pour cet indicateur.",
                            recommendation="Vérifier la période, l'unité et la source de la donnée.",
                            entry_date=entry.entry_date,
                            site_id=entry.site_id,
                            indicator_id=entry.indicator_id,
                        )
                    )
    return alerts


@router.get("/summary", response_model=QualitySummaryOut)
def quality_summary(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    entries, indicators = _load_context(db, current_user.company_id)
    alerts = _build_alerts(entries, indicators)
    critical_count = sum(1 for alert in alerts if alert.severity == "critical")
    score = max(0, 100 - critical_count * 18 - (len(alerts) - critical_count) * 8)
    return QualitySummaryOut(
        total_entries=len(entries),
        draft_entries=sum(1 for entry in entries if entry.status == DataEntryStatus.brouillon),
        valid_entries=sum(1 for entry in entries if entry.status == DataEntryStatus.valide),
        alerts=alerts,
        quality_score=score,
    )


@router.post("/data/{data_id}/normalize", response_model=NormalizedEntryOut)
def normalize_entry(
    data_id: int,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant)),
    db: Session = Depends(get_db),
):
    entry = db.get(EnvironmentalData, data_id)
    if not entry or entry.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donnée introuvable.")
    if entry.status == DataEntryStatus.valide:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Une donnée validée ne peut pas être normalisée.")
    if entry.indicator_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Indicateur requis pour normaliser l'unité.")

    indicator = db.get(Indicator, entry.indicator_id)
    if not indicator or indicator.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Indicateur invalide.")

    normalized = _convert(entry.value, entry.unit, indicator.unit)
    if normalized is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Conversion d'unité non prise en charge.")

    original_value = entry.value
    original_unit = entry.unit
    entry.value = normalized
    entry.unit = indicator.unit
    db.commit()

    ip = request.client.host if request.client else None
    audit_service.log(
        db,
        AuditAction.data_updated,
        user_id=current_user.id,
        company_id=current_user.company_id,
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
        details={"data_id": entry.id, "normalized": True, "from": original_unit, "to": indicator.unit},
    )
    return NormalizedEntryOut(
        data_id=entry.id,
        original_value=original_value,
        original_unit=original_unit,
        normalized_value=entry.value,
        normalized_unit=entry.unit,
        changed=original_value != entry.value or original_unit != entry.unit,
    )


@router.post("/data/{data_id}/validate", response_model=EnvironmentalDataOut)
def validate_after_quality_check(
    data_id: int,
    request: Request,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement)),
    db: Session = Depends(get_db),
):
    entry = db.get(EnvironmentalData, data_id)
    if not entry or entry.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donnée introuvable.")
    if entry.site_id is None or entry.indicator_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site et indicateur requis avant validation.")
    if entry.value < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valeur négative à corriger avant validation.")

    entry.status = DataEntryStatus.valide
    db.commit()
    db.refresh(entry)
    audit_service.log(
        db,
        AuditAction.data_validated,
        user_id=current_user.id,
        company_id=current_user.company_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details={"data_id": entry.id, "quality_checked": True},
    )
    return entry
