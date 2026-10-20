from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..schemas.crop import CropRecommendationRequest
from ..schemas.fertilizer import normalize_crop_name, VALID_CROPS
from ..services.model_service import ModelUnavailableError

router = APIRouter(prefix="/advisory", tags=["unified agricultural advisory"])


class UnifiedAdvisoryRequest(BaseModel):
    # Soil and agroclimatic readings
    N: float = Field(ge=0, le=300, description="Soil Nitrogen (ppm or kg/ha)")
    P: float = Field(ge=0, le=300, description="Soil Phosphorus (ppm or kg/ha)")
    K: float = Field(ge=0, le=400, description="Soil Potassium (ppm or kg/ha)")
    temperature: float = Field(ge=-10, le=60, description="Ambient temperature in °C")
    humidity: float = Field(ge=0, le=100, description="Relative humidity %")
    ph: float = Field(ge=0, le=14, description="Soil pH")
    rainfall: float = Field(ge=0, le=1000, description="Rainfall in mm")
    state_name: str = Field(default="Maharashtra", description="State or Union Territory")
    target_crop_override: str | None = Field(default=None, description="Optional override to force a specific crop")
    farm_id: str | None = None


def estimate_nutrient_index(value: float, low_thresh: float, high_thresh: float) -> float:
    """Map raw numeric soil measurement to Ramamoorthy & Bajaj Nutrient Index [1.0, 3.0]."""
    if value < low_thresh:
        # Scale between 1.0 and 1.66
        ratio = max(0.0, value / max(low_thresh, 1e-5))
        return round(1.0 + ratio * 0.66, 2)
    elif value <= high_thresh:
        # Scale between 1.67 and 2.33
        span = max(high_thresh - low_thresh, 1e-5)
        ratio = (value - low_thresh) / span
        return round(1.67 + ratio * 0.66, 2)
    else:
        # Scale between 2.34 and 3.0
        ratio = min(1.0, (value - high_thresh) / max(high_thresh, 1e-5))
        return round(2.34 + ratio * 0.66, 2)


def evaluate_pest_risk_preview(crop: str, temp: float, humidity: float, rainfall: float) -> dict[str, Any]:
    """
    Preliminary rule-based agroclimatic pest risk indicators.
    Serves as the foundation and bridge for the upcoming Drift-Aware Pest Outbreak Early-Warning ML Model.
    """
    from ..core.crop_catalog import get_crop_catalog

    catalog = get_crop_catalog()
    canonical = catalog.resolve_canonical_id(crop) or crop.strip().lower()
    c = canonical.lower()
    pest_target = "General Crop Pests"
    risk_level = "LOW"
    risk_factors = []

    if "cotton" in c:
        pest_target = "Pink Bollworm & American Bollworm (Helicoverpa armigera)"
        if 25 <= temp <= 34 and humidity > 70:
            risk_level = "HIGH"
            risk_factors.append("Warm temperatures (25-34°C) with elevated humidity (>70%) strongly accelerate bollworm egg incubation.")
        elif 22 <= temp <= 36 and humidity > 60:
            risk_level = "MODERATE"
            risk_factors.append("Conditions are moderately favorable for bollworm moth activity.")
        else:
            risk_factors.append("Current weather parameters are outside peak bollworm outbreak bounds.")
    elif "rice" in c or "paddy" in c:
        pest_target = "Yellow Stem Borer & Brown Planthopper (BPH)"
        if temp >= 28 and humidity > 80:
            risk_level = "HIGH"
            risk_factors.append("High humidity (>80%) and temperatures above 28°C favor brown planthopper population surges.")
        elif humidity > 70:
            risk_level = "MODERATE"
            risk_factors.append("Moderate humidity creates favorable microclimates for stem borers.")
        else:
            risk_factors.append("Low humidity suppresses rapid pest multiplication.")
    elif "maize" in c or "corn" in c:
        pest_target = "Fall Armyworm (Spodoptera frugiperda)"
        if 24 <= temp <= 32 and humidity > 65:
            risk_level = "HIGH"
            risk_factors.append("Ideal thermal-hygrometric window for Fall Armyworm oviposition.")
        else:
            risk_level = "LOW"
            risk_factors.append("Weather conditions are sub-optimal for armyworm escalation.")
    else:
        if humidity > 80 and temp > 25:
            risk_level = "MODERATE"
            risk_factors.append("Warm and humid conditions general pest multiplication watch.")

    return {
        "primary_threat": pest_target,
        "preliminary_risk_level": risk_level,
        "environmental_factors": risk_factors,
        "next_phase_note": "A drift-aware XGBoost pest early-warning model will provide time-series 7-day outbreak probabilities in Phase 2.",
    }


@router.post("/unified", status_code=status.HTTP_200_OK)
def unified_advisory(payload: UnifiedAdvisoryRequest, request: Request) -> dict[str, Any]:
    """
    Unified end-to-end advisory pipeline:
    1. Recommends optimal crops based on soil nutrients and weather readings.
    2. Maps the chosen crop to the ICAR-IISS fertilizer recommendation ensemble.
    3. Calculates elemental macronutrient dosages (N, P2O5, K2O) and commercial bags (Urea, DAP, MOP).
    4. Provides initial agroclimatic pest early-warning context for the selected crop.
    """
    crop_service = getattr(request.app.state, "model_service", None)
    fertilizer_service = getattr(request.app.state, "fertilizer_service", None)

    if crop_service is None or not crop_service.available:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Crop recommendation model is not available.")

    # 1. Predict Crop
    crop_inputs = {
        "N": payload.N,
        "P": payload.P,
        "K": payload.K,
        "temperature": payload.temperature,
        "humidity": payload.humidity,
        "ph": payload.ph,
        "rainfall": payload.rainfall,
    }
    crop_res = crop_service.prediction(crop_inputs)
    recommended_crop = crop_res["predicted_crop"]

    # Crop to evaluate
    selected_crop = payload.target_crop_override or recommended_crop
    normalized_crop = normalize_crop_name(selected_crop)

    # 2. Estimate Fertilizer if normalized crop is supported, otherwise fallback to Rice baseline
    fertilizer_result = None
    crop_for_fert = normalized_crop if normalized_crop in VALID_CROPS else "Rice"

    if fertilizer_service is not None and fertilizer_service.available:
        # Convert soil measurements to nutrient indices
        fert_inputs = {
            "crop": crop_for_fert,
            "state_name": payload.state_name,
            "nitrogen__nutrient_index": estimate_nutrient_index(payload.N, 50.0, 150.0),
            "phosphorus__nutrient_index": estimate_nutrient_index(payload.P, 30.0, 80.0),
            "potassium__nutrient_index": estimate_nutrient_index(payload.K, 40.0, 120.0),
            "soil_ph__nutrient_index": round(max(1.0, min(3.0, (payload.ph - 4.5) / 3.5 * 2.0 + 1.0)), 2),
            "organic_carbon__nutrient_index": 1.80,  # Standard medium organic carbon baseline
        }
        try:
            fertilizer_result = fertilizer_service.prediction(fert_inputs)
        except Exception:
            fertilizer_result = None

    # 3. Pest Outbreak Early-Warning Preview
    pest_preview = evaluate_pest_risk_preview(
        selected_crop,
        payload.temperature,
        payload.humidity,
        payload.rainfall,
    )

    return {
        "advisory_id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_summary": {
            **crop_inputs,
            "state_name": payload.state_name,
        },
        "crop_recommendation": {
            "primary_crop": recommended_crop,
            "selected_crop": selected_crop,
            "top_candidates": crop_res["top_recommendations"],
            "model_version": crop_res["model_version"],
        },
        "fertilizer_advisory": fertilizer_result,
        "pest_early_warning_preview": pest_preview,
        "field_guidance": [
            "Adjust baseline fertilizer dosages +/- 25% according to accredited soil health card ratings.",
            "Inspect field edges regularly when pest early-warning risk is MODERATE or HIGH.",
            "Verify all advisory suggestions with local agricultural extension officers.",
        ],
    }
