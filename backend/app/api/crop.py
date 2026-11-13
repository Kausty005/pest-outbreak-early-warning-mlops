from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request, status

from ...ml.data_validation import FEATURE_COLUMNS
from ...ml.prediction_logger import log_prediction_input
from ..core.metrics import (
    prediction_requests_total,
    prediction_errors_total,
    prediction_latency_seconds,
    input_feature_value,
)
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
    prediction_requests_total.labels(model="crop", endpoint="/crop/recommend").inc()
    start = time.time()
    try:
        values = payload.model_dump(exclude={"farm_id"})
        result = service.prediction(values)
        log_prediction_input(values)
    except ModelUnavailableError as error:
        prediction_errors_total.labels(model="crop", endpoint="/crop/recommend").inc()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    finally:
        prediction_latency_seconds.labels(model="crop").observe(time.time() - start)

    # Record input feature histograms
    for feature in ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]:
        val = values.get(feature)
        if val is not None:
            input_feature_value.labels(feature=feature, model="crop").observe(float(val))

    result["persistence_status"] = persist_prediction(request.app.state.database, result, payload.farm_id)
    return result
