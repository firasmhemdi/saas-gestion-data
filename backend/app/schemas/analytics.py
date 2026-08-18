from pydantic import BaseModel


class MetricOut(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    trend: float


class CategoryTotalOut(BaseModel):
    category: str
    label: str
    value: float
    unit: str


class SitePerformanceOut(BaseModel):
    site_id: int | None
    site_name: str
    energy_kwh: float
    water_m3: float
    waste_tonnes: float
    emissions_kgco2e: float


class ScopeEmissionOut(BaseModel):
    scope: str
    value: float
    unit: str = "kgCO2e"


class AnalyticsSummaryOut(BaseModel):
    metrics: list[MetricOut]
    categories: list[CategoryTotalOut]
    site_performance: list[SitePerformanceOut]
    emissions_by_scope: list[ScopeEmissionOut]
