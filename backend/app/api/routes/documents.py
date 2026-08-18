from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.environmental_data import DataEntrySource, EnvironmentalData
from app.models.indicator import Indicator
from app.models.ingestion import Document, DocumentStatus, ExtractedData
from app.models.site import Site
from app.models.user import Role, User
from app.schemas.ingestion import DocumentCreateRequest, DocumentOut, DocumentValidateRequest
from app.services import audit as audit_service
from app.services.ingestion import classify_document, extract_document_fields

router = APIRouter(prefix="/documents", tags=["documents"])

_WRITERS = (Role.admin, Role.responsable_environnement, Role.consultant)


def _check_site(db: Session, site_id: int | None, user: User) -> None:
    if site_id is None:
        return
    site = db.get(Site, site_id)
    if not site or site.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Site invalide pour ce tenant.")


def _get_document(db: Session, document_id: int, user: User) -> Document:
    document = db.get(Document, document_id)
    if not document or document.company_id != user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")
    return document


def _latest_extraction(db: Session, document_id: int) -> ExtractedData | None:
    stmt = select(ExtractedData).where(ExtractedData.document_id == document_id).order_by(ExtractedData.created_at.desc()).limit(1)
    return db.scalars(stmt).first()


@router.get("", response_model=list[DocumentOut])
def list_documents(
    current_user: User = Depends(require_roles(Role.admin, Role.responsable_environnement, Role.consultant, Role.lecture_seule)),
    db: Session = Depends(get_db),
):
    stmt = select(Document).where(Document.company_id == current_user.company_id).order_by(Document.created_at.desc()).limit(100)
    documents = []
    for document in db.scalars(stmt).all():
        extraction = _latest_extraction(db, document.id)
        documents.append(document.to_dict(extraction.to_dict() if extraction else None))
    return documents


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreateRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_WRITERS)),
    db: Session = Depends(get_db),
):
    _check_site(db, payload.site_id, current_user)
    document_type = classify_document(payload.raw_text, payload.filename)
    fields, confidence = extract_document_fields(payload.raw_text)
    document = Document(
        company_id=current_user.company_id,
        site_id=payload.site_id,
        filename=payload.filename.strip(),
        raw_text=payload.raw_text,
        document_type=document_type,
        status=DocumentStatus.extracted,
        created_by=current_user.id,
    )
    db.add(document)
    db.flush()
    extraction = ExtractedData(
        company_id=current_user.company_id,
        document_id=document.id,
        fields=fields,
        confidence=confidence,
    )
    db.add(extraction)
    db.commit()
    db.refresh(document)
    db.refresh(extraction)
    _audit(db, request, current_user, AuditAction.document_extracted, {"document_id": document.id, "type": document_type.value})
    return document.to_dict(extraction.to_dict())


@router.post("/{document_id}/validate", response_model=DocumentOut)
def validate_document(
    document_id: int,
    payload: DocumentValidateRequest,
    request: Request,
    current_user: User = Depends(require_roles(*_WRITERS)),
    db: Session = Depends(get_db),
):
    document = _get_document(db, document_id, current_user)
    _check_site(db, payload.site_id or document.site_id, current_user)
    if payload.indicator_id is not None:
        indicator = db.get(Indicator, payload.indicator_id)
        if not indicator or indicator.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Indicateur invalide pour ce tenant.")
    extraction = _latest_extraction(db, document.id)
    if extraction is None:
        extraction = ExtractedData(company_id=current_user.company_id, document_id=document.id, fields={}, confidence=60)
        db.add(extraction)

    fields = {**(extraction.fields or {}), **payload.fields}
    extraction.fields = fields
    extraction.validated_at = datetime.now(timezone.utc)
    extraction.validated_by = current_user.id
    document.status = DocumentStatus.validated

    if payload.create_environmental_entry:
        entry_date = _coerce_date(fields.get("document_date"))
        quantity = fields.get("quantity")
        unit = fields.get("unit")
        if entry_date and quantity is not None and unit:
            db.add(
                EnvironmentalData(
                    company_id=current_user.company_id,
                    site_id=payload.site_id or document.site_id,
                    indicator_id=payload.indicator_id,
                    entry_date=entry_date,
                    value=float(quantity),
                    unit=str(unit),
                    source=DataEntrySource.excel,
                    entered_by=current_user.id,
                )
            )
    db.commit()
    db.refresh(document)
    db.refresh(extraction)
    _audit(db, request, current_user, AuditAction.document_validated, {"document_id": document.id})
    return document.to_dict(extraction.to_dict())


def _coerce_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _audit(db: Session, request: Request, user: User, action: AuditAction, details: dict) -> None:
    audit_service.log(
        db,
        action,
        user_id=user.id,
        company_id=user.company_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details=details,
    )
