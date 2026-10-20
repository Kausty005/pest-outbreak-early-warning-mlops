"""
AgriAdapt AI Integration Contracts:
Covers confirmed lifecycle handoff, nutrient/fertilizer integration, and pest early-warning surveillance.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class LifecycleHandoff(BaseModel):
    farm_id: str | None = Field(default=None, description="Optional; recommendation does not create a farm record")
    selected_crop: str
    planting_date: date | None = Field(default=None, description="Must be supplied after a farmer confirms planting")
    location: str | None = Field(default=None, description="Optional farm-provided location")
    model_version: str


class AdvisoryContext(BaseModel):
    crop: str
    lifecycle_stage: str | None = None
    weather_observations: dict[str, float] | None = None
    iot_measurements: dict[str, float] | None = None
    farmer_observations: dict[str, Any] | None = None


class PestAdvisoryContract(BaseModel):
    """
    Contract for Phase 2: Drift-Aware Pest Outbreak Early-Warning System.
    Connects weather observations, crop type, and location to estimate 7-day outbreak probability.
    """
    crop: str = Field(description="Target crop, e.g. Cotton, Rice, Maize")
    region: str = Field(description="District or agroclimatic territory, e.g. Vidarbha, Maharashtra")
    forecast_horizon_days: int = Field(default=7, description="Pest risk forecasting window in days")
    weather_summary: dict[str, float] = Field(description="Temperature, humidity, precipitation variables")
    historical_pest_records_available: bool = Field(default=True)
    outbreak_probability: float | None = Field(default=None, description="Outbreak probability [0.0, 1.0]")
    risk_category: str = Field(default="LOW", description="Risk tier: LOW, MODERATE, or HIGH")
    drift_status: str = Field(default="stable", description="Evidently data-drift monitoring status: stable, drift_detected, retrained")
