"""
surveillance_schema.py
──────────────────────
Standardized ground-truth surveillance schema for multi-crop agricultural
pest monitoring in Maharashtra and India.

Accommodates:
- Visual plant scouting (incidence %, severity %, plants affected/sampled)
- Trap monitoring (pheromone moth counts, light traps)
- Destructive boll/pod dissection
- Crop phenology tracking (sowing date, growth stage, days since sowing)
- Full institutional provenance and license tracking

STRICT SCIENTIFIC INVARIANT:
Fields that cannot be obtained MUST remain missing (None / NaN).
Never populate unobserved fields with arbitrary values or zeros.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# Geographic boundaries for Maharashtra State, India
MAHARASHTRA_BOUNDS = {
    "lat_min": 15.6,
    "lat_max": 22.1,
    "lon_min": 72.6,
    "lon_max": 80.9,
}

# Physical bounds for agricultural measurements
PHYSICAL_BOUNDS = {
    "incidence_min": 0.0,
    "incidence_max": 100.0,
    "severity_min": 0.0,
    "severity_max": 100.0,
    "trap_catch_min": 0.0,
    "trap_catch_max": 5000.0,
    "plants_sampled_min": 1,
    "plants_sampled_max": 1000,
    "dss_min": 0,
    "dss_max": 365,
}

# Biological crop-pest compatibility mapping
VALID_CROP_PEST_COMBINATIONS = {
    ("cotton", "pink_bollworm"),
    ("cotton", "american_bollworm"),
    ("cotton", "spotted_bollworm"),
    ("cotton", "whitefly"),
    ("cotton", "aphids"),
    ("cotton", "thrips"),
    ("cotton", "jassids"),
    ("soybean", "tobacco_caterpillar"),
    ("soybean", "girdle_beetle"),
    ("soybean", "semilooper"),
    ("rice", "brown_planthopper"),
    ("rice", "yellow_stem_borer"),
    ("rice", "leaf_folder"),
    ("maize", "fall_armyworm"),
    ("maize", "stem_borer"),
}

VALID_SAMPLING_METHODS = {
    "fixed_plot_scouting",
    "roving_survey",
    "pheromone_trap_monitoring",
    "light_trap_monitoring",
    "destructive_boll_dissection",
}

VALID_VERIFICATION_STATUSES = {
    "UNVERIFIED",
    "FIELD_SCOUT_VERIFIED",
    "KVK_EXPERT_VALIDATED",
    "ICAR_SCIENTIST_VALIDATED",
}

VALID_DATASET_CLASSIFICATIONS = frozenset({
    "HISTORICAL_RESEARCH_TRIAL",
    "PROSPECTIVE_SENTINEL_FIELD",
    "PUBLIC_ADVISORY",
    "ENVIRONMENTAL_COVARIATE",
})


def normalize_token(val: Optional[str]) -> str:
    """Normalize string to lowercase alphanumeric with underscores."""
    if not val:
        return ""
    return str(val).strip().lower().replace(" ", "_").replace("-", "_")


class SurveillanceRecord(BaseModel):
    """
    Standardized ground-truth surveillance observation record.
    """
    # ── 1. Identification ──
    observation_id: str = Field(description="Unique alphanumeric record identifier")
    observation_date: str = Field(description="ISO 8601 date (YYYY-MM-DD)")
    field_id: Optional[str] = Field(default=None, description="Pseudonymous sentinel field identifier (e.g. MAH-NGP-KAT-001)")
    farmer_id: Optional[str] = Field(default=None, description="Pseudonymous farmer identifier (e.g. FMR-NGP-9E2A8F)")
    observer_id: Optional[str] = Field(default=None, description="Pseudonymous field scout identifier (e.g. SCT-NGP-01)")
    photo_evidence_sha256: Optional[str] = Field(default=None, description="Cryptographic SHA-256 hash of geotagged field photograph")
    district: str = Field(description="Administrative district (e.g., Nagpur, Amravati, Yavatmal, Jalgaon)")
    taluka: Optional[str] = Field(default=None, description="Administrative sub-district / taluka")
    village: Optional[str] = Field(default=None, description="Village or gram panchayat name")
    latitude: float = Field(description="WGS84 latitude coordinate")
    longitude: float = Field(description="WGS84 longitude coordinate")
    crop: str = Field(description="Target crop name (e.g. cotton, soybean, rice, maize)")
    crop_variety: Optional[str] = Field(default=None, description="Cultivar or hybrid name (e.g. Bt Cotton BG-II)")
    pest_common_name: str = Field(description="Common name of target pest (e.g. Pink Bollworm)")
    pest_scientific_name: Optional[str] = Field(default=None, description="Binomial scientific nomenclature")

    # ── 2. Pest Surveillance Measurements ──
    pest_incidence_pct: Optional[float] = Field(
        default=None,
        description="Percentage of plants or organs infested with pest [0.0, 100.0]%"
    )
    pest_severity_pct: Optional[float] = Field(
        default=None,
        description="Degree of tissue damage or defoliation severity [0.0, 100.0]%"
    )
    trap_type: Optional[str] = Field(
        default=None,
        description="Pheromone trap or physical monitoring device type"
    )
    trap_catch_count: Optional[float] = Field(
        default=None,
        description="Number of adult insects trapped per trap (moths/trap/night or weekly catch)"
    )
    plants_sampled: Optional[int] = Field(
        default=None,
        description="Total number of plants or plant organs inspected in scouting sample"
    )
    plants_affected: Optional[int] = Field(
        default=None,
        description="Number of sampled plants showing live pest presence or diagnostic damage"
    )
    sampling_method: str = Field(
        default="fixed_plot_scouting",
        description="Field sampling methodology"
    )
    observation_frequency: str = Field(
        default="weekly",
        description="Monitoring frequency: daily, weekly, bi_weekly, irregular"
    )

    # ── 3. Crop Information ──
    sowing_date: Optional[str] = Field(default=None, description="Field planting/sowing date (YYYY-MM-DD)")
    crop_growth_stage: Optional[str] = Field(default=None, description="Agronomic growth stage name")
    days_since_sowing: Optional[int] = Field(default=None, description="Days elapsed since crop sowing")

    # ── 4. Provenance & Verification ──
    dataset_classification: str = Field(
        default="PROSPECTIVE_SENTINEL_FIELD",
        description="Dataset provenance tier: HISTORICAL_RESEARCH_TRIAL, PROSPECTIVE_SENTINEL_FIELD, PUBLIC_ADVISORY, ENVIRONMENTAL_COVARIATE",
    )
    source_organization: str = Field(description="Originating institution (e.g. CROPSAP-Maharashtra, ICAR-NCIPM)")
    source_document: Optional[str] = Field(default=None, description="Source file, survey bulletin, or export ref")
    source_record_id: Optional[str] = Field(default=None, description="Original record ID in source database")
    collection_method: str = Field(default="field_scouting_visual", description="Visual or mechanical collection")
    verification_status: str = Field(default="UNVERIFIED", description="Data validation audit status")
    data_license: str = Field(default="GOVERNMENT_RESTRICTED", description="Legal licensing terms")

    # ── Validators ──
    @field_validator("dataset_classification")
    @classmethod
    def validate_dataset_classification(cls, v: str) -> str:
        if v not in VALID_DATASET_CLASSIFICATIONS:
            raise ValueError(
                f"Invalid dataset_classification '{v}'. Must be one of {sorted(VALID_DATASET_CLASSIFICATIONS)}."
            )
        return v
    @field_validator("observation_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v[:10], "%Y-%m-%d")
        except Exception:
            raise ValueError(f"observation_date must be in YYYY-MM-DD format, got '{v}'")
        return v[:10]

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if v < MAHARASHTRA_BOUNDS["lat_min"] or v > MAHARASHTRA_BOUNDS["lat_max"]:
            raise ValueError(
                f"Latitude {v} is outside Maharashtra bounding box "
                f"[{MAHARASHTRA_BOUNDS['lat_min']}, {MAHARASHTRA_BOUNDS['lat_max']}]"
            )
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if v < MAHARASHTRA_BOUNDS["lon_min"] or v > MAHARASHTRA_BOUNDS["lon_max"]:
            raise ValueError(
                f"Longitude {v} is outside Maharashtra bounding box "
                f"[{MAHARASHTRA_BOUNDS['lon_min']}, {MAHARASHTRA_BOUNDS['lon_max']}]"
            )
        return v

    @field_validator("pest_incidence_pct")
    @classmethod
    def validate_incidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < PHYSICAL_BOUNDS["incidence_min"] or v > PHYSICAL_BOUNDS["incidence_max"]:
                raise ValueError(f"pest_incidence_pct must be between 0.0 and 100.0%, got {v}")
        return v

    @field_validator("pest_severity_pct")
    @classmethod
    def validate_severity(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < PHYSICAL_BOUNDS["severity_min"] or v > PHYSICAL_BOUNDS["severity_max"]:
                raise ValueError(f"pest_severity_pct must be between 0.0 and 100.0%, got {v}")
        return v

    @field_validator("trap_catch_count")
    @classmethod
    def validate_trap_catch(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            if v < 0.0:
                raise ValueError(f"trap_catch_count cannot be negative, got {v}")
        return v

    @model_validator(mode="after")
    def validate_relationships(self) -> SurveillanceRecord:
        # Check plants_affected <= plants_sampled
        if self.plants_affected is not None and self.plants_sampled is not None:
            if self.plants_affected > self.plants_sampled:
                raise ValueError(
                    f"plants_affected ({self.plants_affected}) cannot exceed plants_sampled ({self.plants_sampled})"
                )

        # Check biological crop-pest compatibility
        norm_c = normalize_token(self.crop)
        norm_p = normalize_token(self.pest_common_name)
        if (norm_c, norm_p) not in VALID_CROP_PEST_COMBINATIONS:
            # Check if partial match exists
            matched = any(c == norm_c and (p in norm_p or norm_p in p) for (c, p) in VALID_CROP_PEST_COMBINATIONS)
            if not matched:
                raise ValueError(
                    f"Biologically invalid or unmonitored crop-pest combination: crop='{self.crop}', pest='{self.pest_common_name}'"
                )

        # Ensure at least one primary quantitative measurement exists
        has_incidence = self.pest_incidence_pct is not None
        has_severity = self.pest_severity_pct is not None
        has_trap = self.trap_catch_count is not None
        has_counts = self.plants_affected is not None and self.plants_sampled is not None
        if not (has_incidence or has_severity or has_trap or has_counts):
            raise ValueError(
                "Surveillance record must contain at least one quantitative measurement: "
                "pest_incidence_pct, pest_severity_pct, trap_catch_count, or plants_affected/sampled"
            )

        return self

