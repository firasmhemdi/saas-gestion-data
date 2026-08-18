from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.emission import Emission
from app.models.environmental_data import DataEntryStatus, EnvironmentalData
from app.models.indicator import Indicator
from app.models.site import Site
from app.models.user import Role, User
from app.schemas.analytics import AnalyticsSummaryOut, CategoryTotalOut, MetricOut, ScopeEmissionOut, SitePerformanceOut

router = APIRouter(prefix="/analytics", tags=["analytics"])

_CATEGORY_LABELS = {
    "energie": "Énergie",
    "eau": "Eau",
    "dechets": "Déchets",
    "emissions": "Émissions directes",
    "matieres": "Matières",
}


def _unit_key(unit: str) -> str:
    return unit.strip().lower().replace("³", "3")


def _convert(value: float, from_unit: str, to_unit: str) -> float | None:
    source = _unit_key(from_unit)
    target = _unit_key(to_unit)
    if source == target:
        return value
    conversions = {
        ("mwh", "kwh"): 1000,
        ("wh", "kwh"): 0.001,
        ("l", "m3"): 0.001,
        ("litre", "m3"): 0.001,
        ("litres", "m3"): 0.001,
        ("kg", "tonnes"): 0.001,
        ("t", "tonnes"): 1,
        ("tonne", "tonnes"): 1,
    }
    factor = conversions.get((source, target))
    return round(value * factor, 4) if factor is not None else None


def _factor_input_unit(unit: str) -> str | None:
    parts = unit.split("/")
    if len(parts) != 2:
        return None
    return parts[1].strip()


@router.get("/summary", response_model=AnalyticsSummaryOut)
def analytics_summary(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    entries = list(
        db.scalars(
            select(EnvironmentalData)
            .where(EnvironmentalData.company_id == current_user.company_id)
            .order_by(EnvironmentalData.entry_date)
        ).all()
    )
    indicators = {
        indicator.id: indicator
        for indicator in db.scalars(select(Indicator).where(Indicator.company_id == current_user.company_id)).all()
    }
    sites = {
        site.id: site
        for site in db.scalars(select(Site).where(Site.company_id == current_user.company_id)).all()
    }
    factors = list(db.scalars(select(Emission).where(Emission.company_id == current_user.company_id)).all())

    totals = defaultdict(float)
    site_rows: dict[int | None, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    emissions_by_scope = {"1": 0.0, "2": 0.0, "3": 0.0}
    valid_entries = [entry for entry in entries if entry.status == DataEntryStatus.valide]

    for entry in entries:
        indicator = indicators.get(entry.indicator_id or -1)
        if not indicator:
            continue
        category = indicator.category.value
        normalized = _convert(entry.value, entry.unit, indicator.unit)
        value = normalized if normalized is not None else entry.value
        totals[(category, indicator.unit)] += value

        row = site_rows[entry.site_id]
        if category == "energie":
            row["energy_kwh"] += _convert(value, indicator.unit, "kWh") or value
        elif category == "eau":
            row["water_m3"] += _convert(value, indicator.unit, "m3") or value
        elif category == "dechets":
            row["waste_tonnes"] += _convert(value, indicator.unit, "tonnes") or value

        for factor in factors:
            input_unit = _factor_input_unit(factor.unit)
            if input_unit and _convert(entry.value, entry.unit, input_unit) is not None:
                emissions_by_scope[factor.scope.value] += (_convert(entry.value, entry.unit, input_unit) or 0) * factor.factor
                row["emissions_kgco2e"] += (_convert(entry.value, entry.unit, input_unit) or 0) * factor.factor
                break

    energy = sum(value for (category, unit), value in totals.items() if category == "energie" and _unit_key(unit) == "kwh")
    water = sum(value for (category, unit), value in totals.items() if category == "eau" and _unit_key(unit) == "m3")
    waste = sum(value for (category, unit), value in totals.items() if category == "dechets" and _unit_key(unit) in {"tonnes", "t"})
    emissions = sum(emissions_by_scope.values())

    categories = [
        CategoryTotalOut(category=category, label=_CATEGORY_LABELS.get(category, category), value=round(value, 2), unit=unit)
        for (category, unit), value in sorted(totals.items())
    ]
    site_performance = [
        SitePerformanceOut(
            site_id=site_id,
            site_name=sites[site_id].name if site_id in sites else "Non affecté",
            energy_kwh=round(values.get("energy_kwh", 0), 2),
            water_m3=round(values.get("water_m3", 0), 2),
            waste_tonnes=round(values.get("waste_tonnes", 0), 2),
            emissions_kgco2e=round(values.get("emissions_kgco2e", 0), 2),
        )
        for site_id, values in site_rows.items()
    ]

    return AnalyticsSummaryOut(
        metrics=[
            MetricOut(key="energy", label="Énergie", value=round(energy, 2), unit="kWh", trend=4.2),
            MetricOut(key="water", label="Eau", value=round(water, 2), unit="m3", trend=-2.1),
            MetricOut(key="waste", label="Déchets", value=round(waste, 2), unit="t", trend=1.4),
            MetricOut(key="emissions", label="Carbone", value=round(emissions, 2), unit="kgCO2e", trend=3.8),
            MetricOut(key="validated", label="Données validées", value=len(valid_entries), unit="lignes", trend=0),
        ],
        categories=categories,
        site_performance=sorted(site_performance, key=lambda item: item.emissions_kgco2e, reverse=True),
        emissions_by_scope=[
            ScopeEmissionOut(scope=scope, value=round(value, 2))
            for scope, value in emissions_by_scope.items()
        ],
    )
