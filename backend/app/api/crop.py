from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from ...ml.data_validation import FEATURE_COLUMNS
from ..schemas.crop import (
    CropRecommendationRequest,
    CropRecommendationResponse,
    ModelInfoResponse,
)
from ..services.model_service import ModelUnavailableError
from ..services.prediction_persistence import persist_prediction

router = APIRouter(prefix="/crop", tags=["crop recommendation"])


@router.get("/schema")
def crop_schema(request: Request) -> dict:
    """Client contract; observed ranges are training-data context, not suitability limits."""
    metadata = request.app.state.model_service.metadata or {}
    observed = (metadata.get("dataset") or {}).get("numeric_ranges", {})
    fields = {
        "N": {"type": "number", "unit": "not verified by source CSV", "valid_range": [0, 300]},
        "P": {"type": "number", "unit": "not verified by source CSV", "valid_range": [0, 300]},
        "K": {"type": "number", "unit": "not verified by source CSV", "valid_range": [0, 400]},
        "temperature": {"type": "number", "unit": "not verified by source CSV", "valid_range": [-10, 60]},
        "humidity": {"type": "number", "unit": "percent relative humidity (inferred; verify before field use)", "valid_range": [0, 100]},
        "ph": {"type": "number", "unit": "pH scale", "valid_range": [0, 14]},
        "rainfall": {"type": "number", "unit": "not verified by source CSV", "valid_range": [0, 1000]},
    }
    for feature in FEATURE_COLUMNS:
        fields[feature]["training_data_observed_range"] = observed.get(feature)
    return {
        "required_fields": fields,
        "additional_optional_fields": {"farm_id": {"type": "string", "description": "optional existing farm identifier"}},
        "notes": [
            "Validation bounds are input-sanity bounds, not agronomic suitability thresholds.",
            "Only pH has a generally identifiable scale; the CSV does not document the other measurement units or rainfall period.",
        ],
    }


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info(request: Request):
    return request.app.state.model_service.model_info()


@router.post("/recommend", response_model=CropRecommendationResponse, status_code=status.HTTP_200_OK)
def recommend_crop(payload: CropRecommendationRequest, request: Request):
    service = request.app.state.model_service
    try:
        values = payload.model_dump(exclude={"farm_id"})
        result = service.prediction(values)
    except ModelUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    result["persistence_status"] = persist_prediction(request.app.state.database, result, payload.farm_id)
    return result
