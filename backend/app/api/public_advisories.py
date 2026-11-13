"""
backend/app/api/public_advisories.py
────────────────────────────────────
FastAPI router for the Public Pest Advisory & Intelligence API.

EXPLICIT SCIENTIFIC INVARIANT:
Public advisories represent institutional recommendations, agrometeorological warnings,
and regional intelligence. They do NOT constitute verified field-level surveillance
observations or outbreak labels. They must NEVER be presented as calibrated
machine learning outbreak probabilities.
"""
from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.app.schemas.public_advisories import (
    ADVISORY_DISCLAIMER_TEXT,
    AdvisoriesSummaryResponse,
    HumanReviewRequest,
    HumanReviewResponse,
    PublicAdvisoriesListResponse,
    PublicAdvisoryItem,
)
from src.data_ingestion.public_advisories import (
    AdvisoryRecord,
    AdvisoryValidator,
    PublicAdvisoryIngestionPipeline,
    list_advisory_sources,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/public-advisories", tags=["public pest intelligence & advisories"])

PROCESSED_FILE_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "public_advisories"
    / "extracted_advisories.json"
)

# In-memory cached advisory store
_CACHED_ADVISORIES: Optional[list[AdvisoryRecord]] = None


def get_all_advisories(force_reload: bool = False) -> list[AdvisoryRecord]:
    """Retrieve all extracted advisory records from disk or memory."""
    global _CACHED_ADVISORIES
    if _CACHED_ADVISORIES is not None and not force_reload:
        return _CACHED_ADVISORIES

    if not PROCESSED_FILE_PATH.exists():
        # Run ingestion pipeline if processed file is not present
        LOGGER.info("Processed advisories not found on disk. Running ingestion pipeline...")
        pipeline = PublicAdvisoryIngestionPipeline()
        records, _ = pipeline.run_pipeline()
        _CACHED_ADVISORIES = records
        return _CACHED_ADVISORIES

    try:
        with open(PROCESSED_FILE_PATH, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
        records = [AdvisoryRecord(**item) for item in raw_list]
        _CACHED_ADVISORIES = records
        return _CACHED_ADVISORIES
    except Exception as e:
        LOGGER.error("Failed to load extracted advisories from %s: %s", PROCESSED_FILE_PATH, e)
        return []


def save_all_advisories(records: list[AdvisoryRecord]) -> None:
    """Save updated advisory records back to disk and update cache."""
    global _CACHED_ADVISORIES
    _CACHED_ADVISORIES = records
    PROCESSED_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(PROCESSED_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump([r.to_dict() for r in records], f, indent=2, ensure_ascii=False)
    except Exception as e:
        LOGGER.error("Failed to save updated advisories to %s: %s", PROCESSED_FILE_PATH, e)


@router.get("", response_model=PublicAdvisoriesListResponse)
def list_public_advisories(
    crop: Optional[str] = Query(None, description="Filter by crop (e.g. cotton, soybean, rice, maize)"),
    district: Optional[str] = Query(None, description="Filter by Maharashtra district (e.g. Nagpur, Amravati)"),
    pest: Optional[str] = Query(None, description="Filter by pest common name"),
    evidence_type: Optional[str] = Query(None, description="Filter by EvidenceType"),
    language: Optional[str] = Query(None, description="Filter by original language ('mr', 'en', 'hi')"),
    review_status: Optional[str] = Query(None, description="Filter by HumanReviewStatus"),
    search: Optional[str] = Query(None, description="Text search across advisory text"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Query extracted public agricultural pest advisories with filtering.
    Preserves strict separation from field-level surveillance ground-truth.
    """
    records = get_all_advisories()
    filtered = records

    if crop:
        norm_crop = crop.strip().lower()
        filtered = [r for r in filtered if r.crop and r.crop.lower() == norm_crop]

    if district:
        norm_dist = district.strip().lower()
        filtered = [r for r in filtered if r.district and norm_dist in r.district.lower()]

    if pest:
        norm_pest = pest.strip().lower()
        filtered = [r for r in filtered if r.pest_common_name and norm_pest in r.pest_common_name.lower()]

    if evidence_type:
        filtered = [r for r in filtered if r.evidence_type.value == evidence_type]

    if language:
        filtered = [r for r in filtered if r.original_language == language]

    if review_status:
        filtered = [r for r in filtered if r.human_review_status.value == review_status]

    if search:
        s_lower = search.strip().lower()
        filtered = [
            r for r in filtered
            if s_lower in r.advisory_text.lower()
            or (r.pest_common_name and s_lower in r.pest_common_name.lower())
            or (r.issuing_organization and s_lower in r.issuing_organization.lower())
        ]

    total_filtered = len(filtered)
    paginated = filtered[offset : offset + limit]

    items = [PublicAdvisoryItem(**r.to_dict()) for r in paginated]
    return PublicAdvisoriesListResponse(
        total_count=len(records),
        filtered_count=total_filtered,
        advisories=items,
        disclaimer=ADVISORY_DISCLAIMER_TEXT,
    )


@router.get("/summary", response_model=AdvisoriesSummaryResponse)
def get_advisories_summary():
    """Retrieve statistical summary of public pest intelligence repository."""
    records = get_all_advisories()

    ev_counts = Counter(r.evidence_type.value for r in records)
    crop_counts = Counter(r.crop for r in records if r.crop)
    dist_counts = Counter(r.district for r in records if r.district)
    lang_counts = Counter(r.original_language for r in records)
    rev_counts = Counter(r.human_review_status.value for r in records)
    docs = set(r.document_sha256 for r in records)

    return AdvisoriesSummaryResponse(
        total_documents=len(docs),
        total_advisories=len(records),
        evidence_type_counts=dict(ev_counts),
        crop_counts=dict(crop_counts),
        district_counts=dict(dist_counts),
        language_counts=dict(lang_counts),
        review_status_counts=dict(rev_counts),
        sources_count=len(list_advisory_sources()),
        disclaimer=ADVISORY_DISCLAIMER_TEXT,
    )


@router.get("/sources")
def get_verified_advisory_sources():
    """List all verified public advisory sources and their coverage profiles."""
    sources = list_advisory_sources()
    return [s.to_dict() for s in sources]


@router.get("/{advisory_id}", response_model=PublicAdvisoryItem)
def get_advisory_by_id(advisory_id: str):
    """Retrieve a single advisory record by its unique identifier."""
    records = get_all_advisories()
    for r in records:
        if r.advisory_id == advisory_id:
            return PublicAdvisoryItem(**r.to_dict())

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Advisory record '{advisory_id}' not found.",
    )


@router.post("/{advisory_id}/review", response_model=HumanReviewResponse)
def submit_human_review(advisory_id: str, payload: HumanReviewRequest):
    """
    Submit an authorized human review decision for an extracted advisory record.
    Maintains an audit trail and updates review status.
    """
    records = get_all_advisories()
    target_idx = None
    for idx, r in enumerate(records):
        if r.advisory_id == advisory_id:
            target_idx = idx
            break

    if target_idx is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Advisory record '{advisory_id}' not found.",
        )

    target_record = records[target_idx]
    try:
        updated_record, audit_entry = AdvisoryValidator.apply_human_review(
            record=target_record,
            reviewer_id=payload.reviewer_id,
            action=payload.action,
            field_updates=payload.field_updates,
            justification=payload.justification,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    records[target_idx] = updated_record
    save_all_advisories(records)

    return HumanReviewResponse(
        success=True,
        advisory_id=advisory_id,
        human_review_status=updated_record.human_review_status.value,
        audit_id=audit_entry.audit_id,
        message=f"Human review '{payload.action}' successfully applied to advisory {advisory_id}.",
    )

