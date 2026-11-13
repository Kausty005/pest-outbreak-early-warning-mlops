"""
backend/app/schemas/pest_risk.py
────────────────────────────────
Pydantic schemas for the Experimental Environmental Pest Risk Assessment API.

IMPORTANT ARCHITECTURAL RULE:
This endpoint estimates biophysical environmental favorability.
It does NOT output calibrated outbreak probabilities or machine learning predictions.
Fields named 'outbreak_probability' are strictly forbidden.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator


class EnvironmentalAssessmentRequest(BaseModel):
    """Request payload for experimental pest favorability assessment."""
    crop: str = Field(description="Target crop (e.g. cotton, soybean, rice, maize)")
    district: str = Field(description="Target Maharashtra district (e.g. Nagpur, Amravati, Yavatmal, Jalgaon)")
    pest: Optional[str] = Field(default=None, description="Optional target pest name (e.g. pink_bollworm)")
    assessment_date: Optional[str] = Field(
        default=None,
        description="Reference assessment date (YYYY-MM-DD). Defaults to latest date in surveillance records.",
    )
    planting_date: Optional[str] = Field(
        default=None,
        description="Crop sowing/planting date (YYYY-MM-DD) for phenological susceptibility evaluation.",
    )
    fetch_live_forecast: bool = Field(
        default=False,
        description="Whether to query live Open-Meteo 7-day meteorological forecast.",
    )


class EnvironmentalObservationSummary(BaseModel):
    """Observed microclimatic conditions used in the assessment."""
    date: str
    temperature_mean_c: float
    temperature_min_c: Optional[float] = None
    temperature_max_c: Optional[float] = None
    relative_humidity_pct: float
    rainfall_mm: float
    soil_moisture_m3m3: Optional[float] = None
    antecedent_window_days: int
    antecedent_mean_temperature_c: float
    antecedent_mean_humidity_pct: float
    antecedent_accumulated_rainfall_mm: float


class DataQualitySummary(BaseModel):
    """Quality and completeness indicators for the underlying environmental records."""
    records_used: int
    data_source: str
    edaphic_data_available: bool
    phenology_data_available: bool
    missing_fields: list[str]
    data_notices: list[str]


class ForecastDayItem(BaseModel):
    """Forecast day breakdown."""
    date: str
    temperature_c: float
    humidity_pct: float
    rainfall_mm: float
    soil_moisture_m3m3: Optional[float] = None
    favorability_score: float
    risk_category: str


class ForecastSummary(BaseModel):
    """Summary of 7-day future meteorological projections."""
    forecast_available: bool
    forecast_source: str
    forecast_days_count: int
    forecast_mean_favorability: Optional[float] = None
    daily_projections: list[ForecastDayItem] = Field(default_factory=list)


class EnvironmentalAssessmentResponse(BaseModel):
    """Response payload for experimental pest favorability assessment."""
    assessment_type: str = "EXPERIMENTAL_ENVIRONMENTAL_FAVORABILITY_ASSESSMENT"
    crop: str
    pest: str
    scientific_name: str
    location: str
    assessment_date: str
    assessment_horizon_days: int = 7
    environmental_favorability_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Continuous biophysical suitability index [0.0, 1.0]",
    )
    risk_category: str = Field(description="Advisory categorization: LOW, MODERATE, or HIGH")
    risk_trend: str = Field(description="Anticipated 7-day trajectory: RISING, STABLE, DECLINING, or UNKNOWN")
    contributing_factors: dict[str, list[str]] = Field(
        description="Positive favorability drivers and limiting biological factors"
    )
    environmental_observations: EnvironmentalObservationSummary
    data_quality: DataQualitySummary
    forecast_available: bool
    forecast_summary: Optional[ForecastSummary] = None
    recommendations: list[str]
    limitations: list[str]
    references: list[dict[str, Any]]
    disclaimer: str

    @model_validator(mode="before")
    @classmethod
    def reject_probabilistic_claims(cls, data: Any) -> Any:
        if isinstance(data, dict) and "outbreak_probability" in data:
            raise ValueError(
                "Violation of biological safety protocol: 'outbreak_probability' must not be returned. "
                "This engine evaluates environmental favorability, not statistical outbreak likelihood."
            )
        return data


class SupportedProfilesResponse(BaseModel):
    """List of supported crops, pests, and available surveillance districts."""
    supported_crops: list[str]
    crop_pests_mapping: dict[str, list[dict[str, str]]]
    available_surveillance_districts: list[str]
    available_date_range: dict[str, str]

