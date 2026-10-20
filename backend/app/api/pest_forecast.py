"""
backend/app/api/pest_forecast.py
─────────────────────────────────
Dedicated API router for the 7-day Multi-Crop Pest Outbreak Forecasting pipeline.
Provides model discovery and inference endpoints with strict validation.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from ..schemas.pest_forecast import (
    PestForecastCatalogInfo,
    PestForecastRequest,
    PestForecastResponse,
)
from ..services.pest_forecast_service import ModelLoadError, PestForecastService

router = APIRouter(prefix="/pest-forecast", tags=["pest outbreak forecasting"])


def _get_service(request: Request) -> PestForecastService:
    service = getattr(request.app.state, "pest_forecast_service", None)
    if service is None:
        # Fallback instantiator if not pre-bound
        service = PestForecastService()
        request.app.state.pest_forecast_service = service
    return service


@router.get("/info", response_model=PestForecastCatalogInfo)
def get_forecasting_catalog(request: Request):
    """Return supported crops, pests, phenology stages, model variants, and synthetic disclaimer."""
    service = _get_service(request)
    return service.get_catalog_info()


@router.get("/example")
def get_example_request() -> dict:
    """Return a verified sample request for testing and demonstration."""
    return {
        "crop": "Maize",
        "pest": "Fall armyworm",
        "district": "Davanagere",
        "growth_stage": "V5_V8_mid_whorl",
        "t7_mean_temp_c": 28.5,
        "t7_min_temp_c": 22.0,
        "t7_max_temp_c": 35.0,
        "t7_mean_rh_pct": 78.0,
        "t7_high_rh_days": 3,
        "t7_rainfall_mm": 35.0,
        "t14_rainfall_mm": 65.0,
        "current_incidence_pct_t0": 4.5,
        "current_severity_pct_t0": 2.1,
        "pest_present_t0": 1,
        "model_type": "full",
    }


@router.post("/predict", response_model=PestForecastResponse, status_code=status.HTTP_200_OK)
def predict_pest_outbreak(payload: PestForecastRequest, request: Request):
    """
    Generate 7-day forward pest outbreak forecast.
    Enforces model-specific feature requirements and applies validation-tuned decision thresholds.
    """
    service = _get_service(request)
    try:
        return service.predict(payload)
    except ModelLoadError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
