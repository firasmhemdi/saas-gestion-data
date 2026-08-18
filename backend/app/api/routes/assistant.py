from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.ai_query import AIQuery
from app.models.environmental_data import EnvironmentalData
from app.models.indicator import Indicator
from app.models.site import Site
from app.models.user import Role, User
from app.schemas.assistant import AssistantAnswerOut, AssistantQuestionRequest

router = APIRouter(prefix="/assistant", tags=["assistant"])


def _site_name(sites: dict[int, Site], site_id: int | None) -> str:
    if site_id is None:
        return "Non affecté"
    return sites[site_id].name if site_id in sites else f"Site #{site_id}"


def _answer_question(question: str, entries: list[EnvironmentalData], indicators: dict[int, Indicator], sites: dict[int, Site]) -> tuple[str, list[dict]]:
    normalized_question = question.lower()
    sources: list[dict] = []
    if not entries:
        return "Aucune donnée environnementale n'est encore disponible pour répondre.", sources

    if any(word in normalized_question for word in ["plus élevée", "plus elevee", "maximum", "max", "highest"]):
        candidates = [
            entry
            for entry in entries
            if entry.indicator_id in indicators
            and indicators[entry.indicator_id].category.value in {"energie", "eau", "dechets", "emissions"}
        ]
        if candidates:
            best = max(candidates, key=lambda entry: entry.value)
            indicator = indicators[best.indicator_id] if best.indicator_id else None
            site = _site_name(sites, best.site_id)
            sources.append(
                {
                    "type": "donnée",
                    "data_id": best.id,
                    "site": site,
                    "indicator": indicator.name if indicator else None,
                    "period": best.entry_date.isoformat(),
                }
            )
            indicator_name = indicator.name if indicator else "l'indicateur renseigné"
            return (
                f"Le niveau le plus élevé est observé sur {site}: {best.value:g} {best.unit} "
                f"pour {indicator_name} au {best.entry_date.isoformat()}.",
                sources,
            )

    totals: dict[str, float] = {}
    for entry in entries:
        indicator = indicators.get(entry.indicator_id or -1)
        label = indicator.name if indicator else "Données non qualifiées"
        totals[label] = totals.get(label, 0) + entry.value
        if len(sources) < 4:
            sources.append(
                {
                    "type": "donnée",
                    "data_id": entry.id,
                    "site": _site_name(sites, entry.site_id),
                    "indicator": label,
                    "period": entry.entry_date.isoformat(),
                }
            )
    top = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:3]
    summary = ", ".join(f"{label}: {value:g}" for label, value in top)
    return f"Synthèse des principaux volumes disponibles: {summary}. La réponse s'appuie sur les données internes filtrées par tenant.", sources


@router.post("/query", response_model=AssistantAnswerOut, status_code=status.HTTP_201_CREATED)
def ask_assistant(
    payload: AssistantQuestionRequest,
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    entries = list(
        db.scalars(
            select(EnvironmentalData)
            .where(EnvironmentalData.company_id == current_user.company_id)
            .order_by(EnvironmentalData.entry_date.desc())
            .limit(200)
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
    answer, sources = _answer_question(payload.question.strip(), entries, indicators, sites)
    query = AIQuery(
        company_id=current_user.company_id,
        user_id=current_user.id,
        question=payload.question.strip(),
        answer=answer,
        sources=sources,
    )
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


@router.get("/history", response_model=list[AssistantAnswerOut])
def assistant_history(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    return list(
        db.scalars(
            select(AIQuery)
            .where(AIQuery.company_id == current_user.company_id)
            .order_by(AIQuery.created_at.desc())
            .limit(50)
        ).all()
    )
