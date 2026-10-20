from __future__ import annotations

import math
from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

VALID_CROPS = {
    "Rice",
    "Wheat",
    "Sugarcane",
    "Kharif Maize",
    "Rabi Maize",
    "Kharif Rice",
    "Rice-Rabi",
}


def normalize_crop_name(name: str) -> str:
    """Normalize input crop name into valid fertilizer model crop vocabulary."""
    cleaned = name.strip()
    # Check direct match
    for valid in VALID_CROPS:
        if valid.lower() == cleaned.lower():
            return valid
    # Partial match heuristics
    low = cleaned.lower()
    if "wheat" in low:
        return "Wheat"
    if "sugarcane" in low:
        return "Sugarcane"
    if "maize" in low or "corn" in low:
        return "Kharif Maize"
    if "rice" in low or "paddy" in low:
        return "Rice"
    return cleaned


class NutrientDetail(BaseModel):
    value: float
    unit: str = "kg/ha"
    chemical_form: str


class RecommendationsBreakdown(BaseModel):
    nitrogen: NutrientDetail
    phosphorus: NutrientDetail
    potassium: NutrientDetail


class CommercialEquivalents(BaseModel):
    urea_46_pct_n_kg_ha: float
    dap_46_pct_p2o5_kg_ha: float
    mop_60_pct_k2o_kg_ha: float


class FertilizerRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    crop: str = Field(description="Target crop, e.g. Rice, Wheat, Sugarcane, Kharif Maize")
    state_name: str = Field(min_length=1, description="Indian State or Union Territory")
    crop_season: str | None = Field(default=None, description="Kharif, Rabi, or Annual (auto-inferred if omitted)")

    # Required soil nutrient indices: Ramamoorthy & Bajaj Nutrient Index scale [1.0, 3.0] (tolerance [0.8, 3.2])
    nitrogen__nutrient_index: Annotated[float, Field(ge=0.8, le=3.2, description="Soil Nitrogen Nutrient Index (1=Low, 2=Med, 3=High)")]
    phosphorus__nutrient_index: Annotated[float, Field(ge=0.8, le=3.2, description="Soil Phosphorus Nutrient Index (1=Low, 2=Med, 3=High)")]
    potassium__nutrient_index: Annotated[float, Field(ge=0.8, le=3.2, description="Soil Potassium Nutrient Index (1=Low, 2=Med, 3=High)")]
    soil_ph__nutrient_index: Annotated[float, Field(ge=0.8, le=3.2, description="Soil pH Nutrient Index (1=Acidic, 2=Neutral, 3=Alkaline)")]
    organic_carbon__nutrient_index: Annotated[float, Field(ge=0.8, le=3.2, description="Soil Organic Carbon Nutrient Index (1=Low, 2=Med, 3=High)")]

    # Optional percentage breakdowns [0.0, 100.0]
    nitrogen__pct_low: float | None = Field(default=None, ge=0.0, le=100.0)
    nitrogen__pct_medium: float | None = Field(default=None, ge=0.0, le=100.0)
    nitrogen__pct_high: float | None = Field(default=None, ge=0.0, le=100.0)

    phosphorus__pct_low: float | None = Field(default=None, ge=0.0, le=100.0)
    phosphorus__pct_medium: float | None = Field(default=None, ge=0.0, le=100.0)
    phosphorus__pct_high: float | None = Field(default=None, ge=0.0, le=100.0)

    potassium__pct_low: float | None = Field(default=None, ge=0.0, le=100.0)
    potassium__pct_medium: float | None = Field(default=None, ge=0.0, le=100.0)
    potassium__pct_high: float | None = Field(default=None, ge=0.0, le=100.0)

    soil_ph__pct_low: float | None = Field(default=None, ge=0.0, le=100.0)
    soil_ph__pct_medium: float | None = Field(default=None, ge=0.0, le=100.0)
    soil_ph__pct_high: float | None = Field(default=None, ge=0.0, le=100.0)

    organic_carbon__pct_low: float | None = Field(default=None, ge=0.0, le=100.0)
    organic_carbon__pct_medium: float | None = Field(default=None, ge=0.0, le=100.0)
    organic_carbon__pct_high: float | None = Field(default=None, ge=0.0, le=100.0)

    electrical_conductivity__nutrient_index: float | None = Field(default=None, ge=0.8, le=3.2)
    nitrogen__total_samples: int | None = Field(default=None, ge=0)
    farm_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator(
        "nitrogen__nutrient_index",
        "phosphorus__nutrient_index",
        "potassium__nutrient_index",
        "soil_ph__nutrient_index",
        "organic_carbon__nutrient_index",
    )
    @classmethod
    def check_finite(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("must be a finite numeric value")
        return float(v)

    @field_validator("crop")
    @classmethod
    def validate_crop(cls, v: str) -> str:
        norm = normalize_crop_name(v)
        if norm not in VALID_CROPS:
            raise ValueError(f"Unrecognized crop '{v}'. Supported crops are: {sorted(VALID_CROPS)}")
        return norm


class FertilizerRecommendationResponse(BaseModel):
    prediction_id: str
    crop: str
    state_name: str
    recommendations: RecommendationsBreakdown
    fertilizer_commercial_equivalent_approx: CommercialEquivalents
    model_version: str
    prediction_timestamp: datetime
    disclaimer: str
    persistence_status: str


class FertilizerModelInfoResponse(BaseModel):
    model_available: bool
    model_version: str | None
    model_name: str | None = None
    model_type: str | None = None
    crops_covered: list[str] | None = None
    framework: str | None = None
    validation_ensemble_weights: dict[str, Any] | None = None
    disclaimer: str
