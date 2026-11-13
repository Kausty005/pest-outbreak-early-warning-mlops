"""
backend/app/schemas/pest_surveillance.py
────────────────────────────────────────
Pydantic schemas for the genuine field pest surveillance data entry,
validation, CSV batch upload, and dashboard endpoints.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class SurveillanceObservationInput(BaseModel):
    """Input payload for recording a single field surveillance observation."""
    observation_id: Optional[str] = Field(default=None, description="Unique ID; auto-generated if omitted")
    observation_date: str = Field(description="Observation date (YYYY-MM-DD)")
    district: str = Field(description="Maharashtra district name (e.g. Nagpur, Amravati, Yavatmal, Jalgaon)")
    taluka: Optional[str] = Field(default=None, description="Sub-district / taluka")
    village: Optional[str] = Field(default=None, description="Village name")
    latitude: float = Field(description="Latitude (WGS84, 15.6 to 22.1 for Maharashtra)")
    longitude: float = Field(description="Longitude (WGS84, 72.6 to 80.9 for Maharashtra)")
    crop: str = Field(description="Crop (cotton, soybean, rice, maize)")
    crop_variety: Optional[str] = Field(default=None, description="Cultivar or hybrid name")
    pest_common_name: str = Field(description="Pest common name (e.g. Pink Bollworm)")
    pest_scientific_name: Optional[str] = Field(default=None, description="Scientific binomial nomenclature")
    pest_incidence_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Pest incidence percentage [0-100]")
    pest_severity_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Damage severity percentage [0-100]")
    trap_type: Optional[str] = Field(default=None, description="Pheromone trap or monitoring device type")
    trap_catch_count: Optional[float] = Field(default=None, ge=0.0, description="Moths or insects trapped per night/week")
    plants_sampled: Optional[int] = Field(default=None, ge=1, description="Number of plants or organs inspected")
    plants_affected: Optional[int] = Field(default=None, ge=0, description="Number of plants showing pest damage")
    sampling_method: str = Field(default="fixed_plot_scouting", description="Sampling path methodology")
    observation_frequency: str = Field(default="weekly", description="Frequency: daily, weekly, bi_weekly")
    sowing_date: Optional[str] = Field(default=None, description="Sowing date (YYYY-MM-DD)")
    crop_growth_stage: Optional[str] = Field(default=None, description="Agronomic growth stage")
    days_since_sowing: Optional[int] = Field(default=None, ge=0, le=365, description="Days elapsed since sowing")
    field_id: Optional[str] = Field(default=None, description="Pseudonymous sentinel field ID (e.g. MAH-NGP-KAT-001)")
    farmer_id: Optional[str] = Field(default=None, description="Pseudonymous farmer ID (e.g. FMR-NGP-9E2A8F)")
    observer_id: Optional[str] = Field(default=None, description="Pseudonymous observer / scout ID")
    photo_evidence_sha256: Optional[str] = Field(default=None, description="SHA-256 hash of geotagged field photograph")
    dataset_classification: str = Field(default="PROSPECTIVE_SENTINEL_FIELD", description="Dataset classification: HISTORICAL_RESEARCH_TRIAL, PROSPECTIVE_SENTINEL_FIELD, PUBLIC_ADVISORY, ENVIRONMENTAL_COVARIATE")
    source_organization: str = Field(default="AgriAdapt-Field-Pilot", description="Originating organization")
    verification_status: str = Field(default="UNVERIFIED", description="Verification state: UNVERIFIED, FIELD_SCOUT_VERIFIED, KVK_EXPERT_VALIDATED")
    is_draft: bool = Field(default=False, description="Flag indicating draft vs submitted record")


class SurveillanceObservationResponse(BaseModel):
    """Response returned upon creating or fetching an observation."""
    success: bool
    observation_id: str
    record: dict[str, Any]
    validation_status: str  # "VALID", "INVALID", "DRAFT"
    warnings: list[str] = []
    message: str


class SurveillanceDashboardResponse(BaseModel):
    """Metrics for the Data Acquisition Progress Dashboard."""
    total_records_received: int
    unique_fields_monitored: int
    verified_records_count: int
    unverified_records_count: int
    draft_records_count: int
    positive_outbreak_windows: int
    verified_negative_windows: int
    unobserved_future_windows: int
    districts_represented: list[str]
    crops_represented: list[str]
    pests_represented: list[str]
    sampling_methods_represented: list[str]
    duplicate_count: int
    institutional_access_status: dict[str, str]
    scientific_invariants: dict[str, Any]


class SurveillanceUploadResponse(BaseModel):
    """Response returned upon batch CSV upload and validation."""
    success: bool
    filename: str
    file_sha256: str
    total_rows_processed: int
    valid_rows_count: int
    invalid_rows_count: int
    duplicates_detected: int
    validation_passed: bool
    errors: list[dict[str, Any]]
    passed_checks: list[str]
    failed_checks: list[str]
    records_saved_count: int


class SurveillanceReviewRequest(BaseModel):
    """Request model for human review of a surveillance record."""
    observation_id: str
    reviewer_id: str
    action: str  # "APPROVE", "REJECT", "CORRECT_FIELDS"
    justification: str
    field_corrections: Optional[dict[str, Any]] = None


class SurveillanceReviewResponse(BaseModel):
    """Response model after human review decision."""
    success: bool
    observation_id: str
    new_status: str
    reviewed_by: str
    timestamp: str
    audit_id: str
    message: str

