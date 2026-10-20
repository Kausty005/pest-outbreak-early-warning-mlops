"""Pydantic schemas for the 7-day multi-crop pest outbreak forecasting API."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator


VALID_CROP_PEST_PAIRS: dict[str, str] = {
    "maize": "Fall armyworm",
    "rice": "Brown planthopper",
    "cotton": "Pink bollworm",
    "wheat": "Aphids",
    "tomato": "Fruit borer",
    "chickpea": "Pod borer",
}


class PestForecastRequest(BaseModel):
    crop: str = Field(..., description="Target crop (Maize, Rice, Cotton, Wheat, Tomato, Chickpea)")
    pest: str = Field(..., description="Target pest species")
    district: str = Field(default="Davanagere", description="Agricultural district")
    growth_stage: str = Field(..., description="Crop phenological growth stage")

    # 7-day and 14-day antecedent weather metrics
    t7_mean_temp_c: float = Field(..., ge=-10.0, le=55.0, description="7-day rolling mean temperature (°C)")
    t7_min_temp_c: float = Field(..., ge=-15.0, le=50.0, description="7-day minimum temperature (°C)")
    t7_max_temp_c: float = Field(..., ge=-5.0, le=60.0, description="7-day maximum temperature (°C)")
    t7_mean_rh_pct: float = Field(..., ge=0.0, le=100.0, description="7-day rolling mean relative humidity (%)")
    t7_high_rh_days: int = Field(..., ge=0, le=7, description="Count of days in last week with RH >= 80%")
    t7_rainfall_mm: float = Field(..., ge=0.0, le=1000.0, description="7-day cumulative precipitation (mm)")
    t14_rainfall_mm: float = Field(..., ge=0.0, le=2000.0, description="14-day cumulative precipitation (mm)")

    # Current infestation features (required for 'full' model, optional for 'early_warning', ignored for 'weather_crop')
    current_incidence_pct_t0: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Current infested plant/foliage percentage at t0"
    )
    current_severity_pct_t0: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Current damage severity percentage at t0"
    )
    pest_present_t0: int | None = Field(
        default=None, ge=0, le=1, description="Binary indicator: 1 if pest/symptoms present at t0, else 0"
    )

    model_type: Literal["full", "weather_crop", "early_warning"] = Field(
        default="full",
        description="Forecasting model variant: 'full' (14 features), 'weather_crop' (11 macro features), 'early_warning' (12 features including binary trap presence)"
    )

    @model_validator(mode="after")
    def validate_physical_consistency(self) -> PestForecastRequest:
        if self.t7_min_temp_c > self.t7_max_temp_c:
            raise ValueError(
                f"t7_min_temp_c ({self.t7_min_temp_c}°C) cannot exceed t7_max_temp_c ({self.t7_max_temp_c}°C)."
            )
        if self.t14_rainfall_mm < self.t7_rainfall_mm - 1e-4:
            raise ValueError(
                f"14-day cumulative rainfall ({self.t14_rainfall_mm}mm) cannot be less than 7-day rainfall ({self.t7_rainfall_mm}mm)."
            )
        return self


class PestForecastResponse(BaseModel):
    crop: str
    target_pest: str
    forecast_horizon: str = "7 days"
    outbreak_probability: float
    outbreak_predicted: bool
    risk_level: str
    decision_threshold: float
    model_used: str
    model_label: str
    features_used: list[str]
    disclaimer: str
    input_summary: dict[str, Any]


class ModelInfoItem(BaseModel):
    model_type: str
    label: str
    description: str
    required_features: list[str]
    decision_threshold: float
    available: bool


class PestForecastCatalogInfo(BaseModel):
    available_models: list[ModelInfoItem]
    crop_pest_pairs: dict[str, str]
    growth_stages_by_crop: dict[str, list[str]]
    sample_districts: list[str]
    disclaimer: str
