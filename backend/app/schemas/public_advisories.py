"""
backend/app/schemas/public_advisories.py
────────────────────────────────────────
Pydantic API schemas for the Public Pest Advisory & Intelligence API.

CRITICAL INVARIANT:
Public advisories represent institutional recommendations and regional intelligence.
They do NOT constitute verified field-level surveillance ground-truth observations
or outbreak labels. They must NEVER be presented as calibrated outbreak probabilities.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

ADVISORY_DISCLAIMER_TEXT = (
    "NOTICE: Public pest advisories reflect institutional alerts, farmer guidance bulletins, "
    "and agrometeorological warnings issued by ICAR institutes, agricultural universities, "
    "and the Maharashtra Department of Agriculture. They represent public extension intelligence, "
    "NOT verified field-level surveillance measurements or calibrated machine learning outbreak probabilities."
)


class PublicAdvisoryItem(BaseModel):
    """Schema representing an individual public pest advisory entry."""
    advisory_id: str
    publication_date: str | None = None
    observation_period_start: str | None = None
    observation_period_end: str | None = None
    issuing_organization: str
    issuing_office: str | None = None
    source_document: str
    source_url: str | None = None

    crop: str | None = None
    pest_common_name: str | None = None
    pest_scientific_name: str | None = None
    district: str | None = None
    taluka: str | None = None
    village: str | None = None
    reported_pest_status: str | None = None
    advisory_severity: str
    evidence_type: str
    evidence_justification_quote: str | None = None
    source_section: str | None = None

    recommended_scouting_actions: str | None = None
    recommended_management_actions: str | None = None
    recommended_preventive_actions: str | None = None
    advisory_text: str

    original_language: str
    translated_text: str | None = None
    translation_method: str | None = None

    document_sha256: str
    page_number: int | None = None
    extraction_method: str
    extraction_confidence: float
    extraction_flags: list[str] = []
    human_review_status: str
    human_reviewer_notes: str | None = None
    reviewed_at: str | None = None
    reviewed_by: str | None = None


class PublicAdvisoriesListResponse(BaseModel):
    """Paginated or filtered list of public advisories."""
    total_count: int
    filtered_count: int
    advisories: list[PublicAdvisoryItem]
    disclaimer: str = ADVISORY_DISCLAIMER_TEXT


class HumanReviewRequest(BaseModel):
    """Request payload for submitting a human review decision."""
    reviewer_id: str = Field(min_length=2, description="Identifier of the reviewer")
    action: str = Field(description="'APPROVE', 'REJECT', 'CORRECT_FIELDS', or 'FLAG_FOR_SURVEILLANCE'")
    field_updates: dict[str, Any] | None = Field(default=None, description="Optional field corrections")
    justification: str = Field(min_length=5, description="Entomological or procedural justification")


class HumanReviewResponse(BaseModel):
    """Response returned upon applying human review."""
    success: bool
    advisory_id: str
    human_review_status: str
    audit_id: str
    message: str


class AdvisoriesSummaryResponse(BaseModel):
    """Statistical breakdown of available public advisories."""
    total_documents: int
    total_advisories: int
    evidence_type_counts: dict[str, int]
    crop_counts: dict[str, int]
    district_counts: dict[str, int]
    language_counts: dict[str, int]
    review_status_counts: dict[str, int]
    sources_count: int
    disclaimer: str = ADVISORY_DISCLAIMER_TEXT

