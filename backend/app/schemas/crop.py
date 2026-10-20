from __future__ import annotations

import math
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CropRecommendationRequest(BaseModel):
    """Physically bounded inputs; dataset-supported ranges are exposed separately."""

    model_config = ConfigDict(extra="forbid")

    N: Annotated[float, Field(ge=0, le=300, description="Soil nitrogen measurement; unit not verified by source CSV")]
    P: Annotated[float, Field(ge=0, le=300, description="Soil phosphorus measurement; unit not verified by source CSV")]
    K: Annotated[float, Field(ge=0, le=400, description="Soil potassium measurement; unit not verified by source CSV")]
    temperature: Annotated[float, Field(ge=-10, le=60, description="Temperature; source unit not verified")]
    humidity: Annotated[float, Field(ge=0, le=100, description="Relative humidity percentage")]
    ph: Annotated[float, Field(ge=0, le=14, description="Soil pH on the standard 0–14 scale")]
    rainfall: Annotated[float, Field(ge=0, le=1000, description="Rainfall; source aggregation period and unit not verified")]
    farm_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("N", "P", "K", "temperature", "humidity", "ph", "rainfall")
    @classmethod
    def finite_number(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("must be a finite number")
        return float(value)


class RecommendationCandidate(BaseModel):
    crop: str
    model_score: float = Field(ge=0, le=1)


class CropRecommendationResponse(BaseModel):
    prediction_id: str
    predicted_crop: str
    top_recommendations: list[RecommendationCandidate]
    model_version: str
    prediction_timestamp: datetime
    input_summary: dict[str, float]
    confidence_note: str
    disclaimer: str
    persistence_status: str


class HealthResponse(BaseModel):
    status: str
    model_available: bool
    model_version: str | None
    crop_model_available: bool = True
    crop_model_version: str | None = None
    fertilizer_model_available: bool = True
    fertilizer_model_version: str | None = None
    persistence_enabled: bool
    persistence_available: bool


class ModelInfoResponse(BaseModel):
    model_available: bool
    model_version: str | None
    selected_model: dict | None = None
    evaluation_metrics: dict | None = None
    dataset_checksum: str | None = None
    disclaimer: str
