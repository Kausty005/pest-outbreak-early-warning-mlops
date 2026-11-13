from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request, status

from ..core.metrics import (
    prediction_requests_total,
    prediction_errors_total,
    prediction_latency_seconds,
    input_feature_value,
)
from ..schemas.fertilizer import (
    FertilizerRecommendationRequest,
    FertilizerRecommendationResponse,
    FertilizerModelInfoResponse,
)
from ..services.model_service import ModelUnavailableError
from ..services.prediction_persistence import persist_fertilizer_prediction

router = APIRouter(prefix="/fertilizer", tags=["fertilizer recommendation"])


@router.get("/schema")
def fertilizer_schema(request: Request) -> dict:
    """Return feature schema, nutrient indices definitions, and valid boundaries."""
    service = getattr(request.app.state, "fertilizer_service", None)
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Fertilizer service not initialized")
    return service.schema()


@router.get("/model-info", response_model=FertilizerModelInfoResponse)
def fertilizer_model_info(request: Request):
    """Return active model version, ensemble composition, and metrics."""
    service = getattr(request.app.state, "fertilizer_service", None)
    if service is None:
        return {
            "model_available": False,
            "model_version": None,
            "disclaimer": "Fertilizer service not initialized",
        }
    return service.model_info()


@router.get("/example")
def fertilizer_example(request: Request) -> dict:
    """Return verified sample plot input (Maharashtra Rice)."""
    service = getattr(request.app.state, "fertilizer_service", None)
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Fertilizer service not initialized")
    return service.example()


@router.post("/recommend", response_model=FertilizerRecommendationResponse, status_code=status.HTTP_200_OK)
def recommend_fertilizer(payload: FertilizerRecommendationRequest, request: Request):
    """
    Predict elemental macronutrient dosages (N, P2O5, K2O in kg/ha)
    and commercial fertilizer bag equivalents (Urea, DAP, MOP) for the given plot.
    """
    service = getattr(request.app.state, "fertilizer_service", None)
    if service is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Fertilizer service not initialized")

    prediction_requests_total.labels(model="fertilizer", endpoint="/fertilizer/recommend").inc()
    start = time.time()
    try:
        raw_inputs = payload.model_dump(exclude={"farm_id"}, exclude_none=True)
        result = service.prediction(raw_inputs)
    except ModelUnavailableError as error:
        prediction_errors_total.labels(model="fertilizer", endpoint="/fertilizer/recommend").inc()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        prediction_errors_total.labels(model="fertilizer", endpoint="/fertilizer/recommend").inc()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    finally:
        prediction_latency_seconds.labels(model="fertilizer").observe(time.time() - start)

    # Record input feature histograms
    for feature in ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]:
        val = raw_inputs.get(feature)
        if val is not None:
            input_feature_value.labels(feature=feature, model="fertilizer").observe(float(val))

    result["persistence_status"] = persist_fertilizer_prediction(
        request.app.state.database,
        result,
        raw_inputs,
        payload.farm_id,
    )
    return result
