"""
advisory_schema.py
──────────────────
Standardized schema for publicly accessible agricultural pest intelligence,
extension advisories, and agrometeorological warnings.

CRITICAL SCIENTIFIC DISTINCTION:
A published advisory is evidence that an institution issued an advisory or notice.
It is NEVER direct evidence that a specific farm or field experienced a verified
pest outbreak.

STRICT INVARIANTS:
1. Advisory records must NEVER be converted automatically into binary outbreak
   training labels (outbreak_within_7d = 1 or 0).
2. General advisory statements must be classified as GENERAL_PREVENTIVE_ADVISORY
   or REPORTED_PEST_ACTIVITY — never assumed to be FIELD_SURVEILLANCE_MEASUREMENT
   without documented sampling counts and field methods.
3. Unobserved fields must remain None / null. No inferring exact farm GPS coordinates,
   incidence percentages, or trap catches from qualitative prose.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class EvidenceType(str, Enum):
    """
    Epistemic evidence classification for public advisory content.
    Prevents mistaking routine seasonal advice for verified field outbreaks.
    """
    # Routine preventive guidance (e.g. "Install pheromone traps; inspect weekly")
    GENERAL_PREVENTIVE_ADVISORY = "GENERAL_PREVENTIVE_ADVISORY"
    # Qualitative report of pest presence (e.g. "Moths sighted in parts of district")
    REPORTED_PEST_ACTIVITY = "REPORTED_PEST_ACTIVITY"
    # Qualitative report of high/severe damage without rigorous plot sampling
    REPORTED_PEST_SEVERITY = "REPORTED_PEST_SEVERITY"
    # Quantitative field measurement with documented sampling units/methods
    FIELD_SURVEILLANCE_MEASUREMENT = "FIELD_SURVEILLANCE_MEASUREMENT"
    # Ambiguous or unclassifiable content
    UNKNOWN_EVIDENCE_TYPE = "UNKNOWN_EVIDENCE_TYPE"


class AdvisorySeverity(str, Enum):
    """Advisory urgency / warning level assigned by issuing authority or extracted."""
    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HumanReviewStatus(str, Enum):
    """Workflow state for human entomological / domain review."""
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED_ADVISORY = "VERIFIED_ADVISORY"
    REJECTED_EXTRACTION = "REJECTED_EXTRACTION"
    PROMOTED_FOR_SURVEILLANCE_CONSIDERATION = "PROMOTED_FOR_SURVEILLANCE_CONSIDERATION"


class HumanReviewAuditEntry(BaseModel):
    """Immutable audit trail entry recording a reviewer's decision or correction."""
    audit_id: str = Field(default_factory=lambda: f"AUD-{uuid4().hex[:8]}")
    advisory_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    reviewer_id: str
    action: str  # "APPROVE", "REJECT", "CORRECT_FIELDS", "FLAG_FOR_SURVEILLANCE"
    field_changes: dict[str, dict[str, Any]] = Field(default_factory=dict)
    justification: str

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class AdvisoryRecord(BaseModel):
    """
    Structured record representing an extracted public pest advisory.
    Maintains clean separation from field surveillance data.
    """
    # ── 1. Identification ──
    advisory_id: str = Field(description="Unique alphanumeric identifier for this advisory entry")
    publication_date: Optional[str] = Field(default=None, description="ISO 8601 publication date (YYYY-MM-DD)")
    observation_period_start: Optional[str] = Field(default=None, description="Start date of advisory validity period")
    observation_period_end: Optional[str] = Field(default=None, description="End date of advisory validity period")
    issuing_organization: str = Field(description="Organization that published the advisory (e.g. ICAR-CICR, CROPSAP)")
    issuing_office: Optional[str] = Field(default=None, description="Specific division, research station, or KVK office")
    source_document: str = Field(description="Filename, title, or reference of the source bulletin")
    source_url: Optional[str] = Field(default=None, description="Public URL from which document was accessed")

    # ── 2. Agricultural Information ──
    crop: Optional[str] = Field(default=None, description="Standardized crop name (e.g. cotton, soybean, rice, maize)")
    pest_common_name: Optional[str] = Field(default=None, description="Standardized common name of the pest")
    pest_scientific_name: Optional[str] = Field(default=None, description="Binomial Latin nomenclature if mentioned")
    district: Optional[str] = Field(default=None, description="Administrative district (e.g. Nagpur, Amravati, Yavatmal, Jalgaon)")
    taluka: Optional[str] = Field(default=None, description="Taluka or sub-district if localized")
    village: Optional[str] = Field(default=None, description="Village or cluster if explicitly identified")
    reported_pest_status: Optional[str] = Field(default=None, description="Prose describing observed pest status in document")
    advisory_severity: AdvisorySeverity = Field(default=AdvisorySeverity.INFORMATIONAL, description="Severity rating")
    evidence_type: EvidenceType = Field(default=EvidenceType.GENERAL_PREVENTIVE_ADVISORY, description="Evidence category")
    evidence_justification_quote: Optional[str] = Field(default=None, description="Verbatim source excerpt justifying evidence type")
    source_section: Optional[str] = Field(default=None, description="Section or paragraph reference in source document")

    # ── 3. Recommendations ──
    recommended_scouting_actions: Optional[str] = Field(default=None, description="Scouting guidance for farmers/scouts")
    recommended_management_actions: Optional[str] = Field(default=None, description="Recommended curative or IPM interventions")
    recommended_preventive_actions: Optional[str] = Field(default=None, description="Preventive, cultural, or biological steps")
    advisory_text: str = Field(description="Raw or cleaned text snippet extracted from source document")

    # ── 4. Multilingual & Translation ──
    original_language: str = Field(default="en", description="Original language ('en', 'mr', 'hi')")
    translated_text: Optional[str] = Field(default=None, description="English translation if original was Marathi/Hindi")
    translation_method: Optional[str] = Field(default=None, description="Method used ('manual_review', 'dictionary_assisted', etc.)")

    # ── 5. Provenance & Quality Assurance ──
    document_sha256: str = Field(description="Cryptographic SHA-256 hash of the source document")
    page_number: Optional[int] = Field(default=None, description="Page number where snippet appeared (for PDFs)")
    extraction_method: str = Field(default="automated_parser", description="Extraction tool or routine")
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score [0.0, 1.0]")
    extraction_flags: list[str] = Field(default_factory=list, description="Quality flags or ambiguities detected")
    human_review_status: HumanReviewStatus = Field(default=HumanReviewStatus.PENDING_REVIEW, description="Review status")
    human_reviewer_notes: Optional[str] = Field(default=None, description="Notes from human reviewer")
    reviewed_at: Optional[str] = Field(default=None, description="ISO timestamp of review")
    reviewed_by: Optional[str] = Field(default=None, description="Reviewer identifier")

    @field_validator("publication_date", "observation_period_start", "observation_period_end")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        # Must parse as YYYY-MM-DD
        try:
            datetime.strptime(v[:10], "%Y-%m-%d")
            return v[:10]
        except ValueError:
            raise ValueError(f"Invalid date format '{v}'. Expected ISO format YYYY-MM-DD.")

    def assert_not_supervised_label(self) -> None:
        """
        Safety barrier: explicitly disallows using an AdvisoryRecord as an ML label.
        Raises RuntimeError if invoked in a modeling context.
        """
        raise RuntimeError(
            f"AdvisoryRecord '{self.advisory_id}' is an advisory intelligence document, "
            f"NOT a verified field surveillance observation. "
            f"It must NEVER be used as a ground-truth label for supervised model training."
        )

    def to_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        data["advisory_severity"] = self.advisory_severity.value
        data["evidence_type"] = self.evidence_type.value
        data["human_review_status"] = self.human_review_status.value
        return data

