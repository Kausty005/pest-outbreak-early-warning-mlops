"""
backend/app/schemas/pest.py
───────────────────────────
Preliminary Data Contracts & Interface for Pest Outbreak Early-Warning System (Phase 2).
Provides standardized contracts for pest risk screening and upcoming time-series models.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class TargetPestInfo(BaseModel):
    common_name: str
    scientific_name: str
    economic_threshold: str


class PestOutbreakSpecification(BaseModel):
    canonical_id: str
    display_name: str
    category: str
    priority_tier: str
    target_pests: list[TargetPestInfo]
    historical_data_requirements: list[str]
    weather_feature_requirements: list[str]
    training_data_availability: str
    data_sources: list[str]


class PestRiskPreviewRequest(BaseModel):
    crop: str = Field(description="Target crop canonical ID, alias, or display name (e.g. 'cotton', 'rice', 'maize')")
    temperature: float = Field(ge=-10, le=60, description="Ambient temperature in °C")
    humidity: float = Field(ge=0, le=100, description="Relative humidity percentage")
    rainfall: float = Field(ge=0, le=1000, description="Precipitation in mm")
    state_name: str = Field(default="Maharashtra", description="Target agricultural state")
    district: str | None = Field(default=None, description="Optional target district (e.g. Nagpur, Amravati)")


class PestRiskPreviewResponse(BaseModel):
    crop_canonical_id: str
    crop_display_name: str
    primary_threat: str
    preliminary_risk_level: str
    environmental_factors: list[str]
    target_pests: list[TargetPestInfo]
    next_phase_note: str


class FuturePestModelInferenceContract(BaseModel):
    """
    Contract for the Phase 2 XGBoost Pest Early-Warning Classifier.
    Predicts 7-day infestation risk using regional historical surveillance + daily weather.
    """
    model_config = ConfigDict(extra="ignore")

    crop: str = Field(description="Canonical crop ID, e.g. cotton, rice, maize")
    region: str = Field(description="Target state / agroclimatic zone (e.g. Maharashtra, Vidarbha)")
    district: str = Field(description="District name")
    observation_date: date = Field(description="Date of advisory calculation")
    forecast_horizon_days: int = Field(default=7, description="Prediction window in days")

    # NASA POWER Daily Agroclimatology (7-day and 14-day rolling aggregates)
    temp_max_c: float = Field(ge=-10, le=60)
    temp_min_c: float = Field(ge=-10, le=60)
    relative_humidity_pct: float = Field(ge=0, le=100)
    cumulative_rainfall_mm: float = Field(ge=0, le=2000)
    solar_radiation_mj_m2: float | None = Field(default=None, ge=0)
    wind_speed_km_h: float | None = Field(default=None, ge=0)

    # Historical Surveillance Traps (ICAR-NBAIR / CROPSAP / Bhuvan ground truth)
    recent_trap_catch_avg: float | None = Field(default=None, ge=0, description="Moths / trap / night over last 7 days")
    larval_count_per_unit: float | None = Field(default=None, ge=0, description="Visual larval or nymph count")
    foliage_damage_pct: float | None = Field(default=None, ge=0, le=100, description="Field damage percentage")
