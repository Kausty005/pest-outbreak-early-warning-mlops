from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

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

    try:
        raw_inputs = payload.model_dump(exclude={"farm_id"}, exclude_none=True)
        result = service.prediction(raw_inputs)
    except ModelUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error

    result["persistence_status"] = persist_fertilizer_prediction(
        request.app.state.database,
        result,
        raw_inputs,
        payload.farm_id,
    )
    return result
